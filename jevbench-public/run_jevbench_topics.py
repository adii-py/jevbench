#!/usr/bin/env python3
"""Run JevBench's public cases and report accuracy by official subject topic.

The topic labels are metadata, not a separate dataset. This script uses the
vendored upstream JevBench runner/scorer and joins its per-item results to
datasets/topics.json. Held-out cases cannot be reproduced from the public repo.
"""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys

from systemone_bench.jev_versions import listed_families, resolve_version


ROOT = Path(__file__).resolve().parent
UPSTREAM = ROOT / "systemone_bench/vendor/jevbench-src"
DATASETS = UPSTREAM / "datasets"
TOPICS = DATASETS / "topics.json"

sys.path.insert(0, str(UPSTREAM))
from jevbench.summarize import metric, summarize  # noqa: E402
from jevbench.tasks import dataset_hash, load_jsonl  # noqa: E402


def write_json(path: Path, value: object) -> None:
    path.write_text(json.dumps(value, indent=2, sort_keys=True, ensure_ascii=False) + "\n")


def load_inputs(version="v1.2"):
    profile = resolve_version(version)
    if not profile.tiers:
        raise ValueError(f"{profile.requested} public cases are not published in the upstream repository")
    topic_data = json.loads(TOPICS.read_text())
    tasks = [task for path in profile.paths(UPSTREAM) for task in load_jsonl(str(path))]
    ids = [task.id for task in tasks]
    if len(ids) != len(set(ids)):
        raise ValueError("Duplicate public JevBench task IDs")
    if not set(ids) <= set(topic_data["public"]):
        raise ValueError("topics.json lacks labels for selected JevBench public tasks")
    if profile.family in ("v1.2", "v1.3", "v1.4") and set(ids) != set(topic_data["public"]):
        raise ValueError("topics.json public IDs differ from the 231-case profile")
    keys = {topic["key"] for topic in topic_data["topics"]}
    if set(topic_data["public"].values()) - keys:
        raise ValueError("topics.json contains unknown topic keys")
    return topic_data, tasks, profile


def report(topic_data, tasks, records):
    selected_ids = {task.id for task in tasks}
    if len({row["task_id"] for row in records}) != len(records):
        raise ValueError("Duplicate result task IDs")
    if {row["task_id"] for row in records} - selected_ids:
        raise ValueError("Results contain IDs outside selected tasks")
    whole = summarize(tasks, records)
    rows = []
    for topic in topic_data["topics"]:
        subset = [task for task in tasks if topic_data["public"][task.id] == topic["key"]]
        stats = metric(subset, records)
        rows.append({
            "topic": topic["key"], "label": topic["label"],
            "planned": stats["n_planned"], "attempted": stats["n_attempted"],
            "correct": stats["n_correct"], "accuracy": stats["accuracy"],
            "brier": stats["brier_mean"], "ece": stats["ece"],
            "schema_validity": stats["schema_validity"],
        })
    assert sum(row["planned"] for row in rows) == len(tasks)
    assert sum(row["attempted"] for row in rows) == len(records)
    return {"official_public_summary": whole, "by_topic": rows}


def read_records(path: Path) -> list:
    """Per-item rows the harness fsynced so far; a torn final line is skipped."""
    if not path.exists():
        return []
    records = []
    for line in path.read_text().splitlines():
        if line.strip():
            try:
                records.append(json.loads(line))
            except json.JSONDecodeError:
                print(f"WARNING: skipped unreadable results line: {line[:80]!r}", flush=True)
    return records


def termination(records, planned, harness_rc):
    """Why the run ended. The harness stops on HTTP 401/403/429 or on 3 consecutive
    request errors and leaves the remaining cases unattempted."""
    failed = [
        {"task_id": r["task_id"], "status_code": r.get("status_code"), "error": (r.get("error") or "")[:300]}
        for r in records if not r.get("ok")
    ]
    info = {"harness_exit_code": harness_rc, "attempted": len(records), "planned": planned,
            "n_failed_requests": len(failed), "last_errors": failed[-3:]}
    if harness_rc == 0 and len(records) == planned:
        return {"status": "complete", "reason": None, **info}
    last = records[-1] if records else None
    if last is not None and last.get("status_code") in (401, 403, 429):
        reason = f"stopped on HTTP {last['status_code']} (access or rate limit) at case {len(records)}/{planned}"
    elif len(records) >= 3 and not any(r.get("ok") or r.get("status_code") == 422 for r in records[-3:]):
        reason = f"stopped after 3 consecutive request errors at case {len(records)}/{planned}"
    elif harness_rc != 0:
        reason = f"harness exited with code {harness_rc} after {len(records)}/{planned} cases"
    else:
        reason = f"harness finished after {len(records)}/{planned} cases"
    return {"status": "ended_abruptly", "reason": reason, **info}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--endpoint", help="System One API base URL")
    parser.add_argument("--model", help="model value sent to the endpoint")
    parser.add_argument("--api-key-env", default="SYSTEMONE_BENCH_API_KEY", help="environment variable containing the bearer key")
    parser.add_argument("--out", type=Path, help="new output directory")
    parser.add_argument("--topic", action="append", help="run only this topic key; repeatable")
    parser.add_argument("--start", type=int, default=0, help="0-based index of the first selected case to run")
    parser.add_argument("--limit", type=int, help="run N cases from --start (smoke test)")
    parser.add_argument("--delay-s", type=float, default=0.0, help="pause between requests (rate limits)")
    parser.add_argument("--results", type=Path, help="summarize an existing JevBench results.jsonl instead of running")
    parser.add_argument("--version", default="v1.2", help="public JevBench release profile; default v1.2")
    parser.add_argument("--list-versions", action="store_true", help="show available public JevBench profiles")
    args = parser.parse_args()
    if args.list_versions:
        print(json.dumps(listed_families(), indent=2))
        return 0
    if not args.results and (not args.endpoint or not args.model):
        parser.error("--endpoint and --model are required when running requests")
    try:
        topic_data, tasks, profile = load_inputs(args.version)
    except ValueError as exc:
        parser.error(str(exc))
    allowed = {item["key"] for item in topic_data["topics"]}
    if args.topic:
        unknown = set(args.topic) - allowed
        if unknown:
            parser.error(f"unknown topic(s): {', '.join(sorted(unknown))}")
        tasks = [task for task in tasks if topic_data["public"][task.id] in args.topic]
    if args.start < 0:
        parser.error("--start must be >= 0")
    if args.start >= len(tasks):
        parser.error(f"--start {args.start} is past the last selected case (index {len(tasks) - 1})")
    tasks = tasks[args.start:]
    if args.limit is not None:
        if args.limit < 1:
            parser.error("--limit must be positive")
        tasks = tasks[:args.limit]
    if args.results and (args.topic or args.limit or args.start):
        parser.error("--results expects the full public results; omit --topic, --start and --limit")
    if args.delay_s < 0:
        parser.error("--delay-s must be >= 0")
    endpoint = (args.endpoint or "").rstrip("/")
    # The adapter appends /v1/systemone itself; accept a bare host, a /v1 base, or the full route.
    for suffix in ("/v1/systemone", "/v1"):
        endpoint = endpoint.removesuffix(suffix)
    out = args.out or ROOT / "runs" / f"jevbench-{profile.requested}-topics-{dt.datetime.now().strftime('%Y%m%d-%H%M%S')}"
    out = out.resolve()
    out.mkdir(parents=True, exist_ok=False)
    harness_rc = 0
    if args.results:
        records = [json.loads(line) for line in args.results.read_text().splitlines() if line.strip()]
    else:
        selected = out / "selected-tasks.jsonl"
        # Preserve the canonical task records and JevBench scoring semantics.
        by_id = {json.loads(line)["id"]: line for path in profile.paths(UPSTREAM) for line in path.read_text().splitlines() if line}
        selected.write_text("\n".join(by_id[task.id] for task in tasks) + "\n")
        env = os.environ.copy()
        env["PYTHONPATH"] = str(UPSTREAM) + os.pathsep + env.get("PYTHONPATH", "")
        env[args.api_key_env] = env.get(args.api_key_env) or "local"
        command = [
            sys.executable, "-m", "jevbench.cli", "run", "--tasks", str(selected),
            "--adapter", "typesafe", "--endpoint", endpoint, "--model", args.model,
            "--key-env", args.api_key_env, "--results", str(out / "results.jsonl"),
            "--ledger", str(out / "ledger.jsonl"), "--raw-dir", str(out / "raw"),
            "--reserve-usd", "0", "--cap-usd", "1000", "--cost-basis", "local_endpoint",
            "--manifest", str(out / "run-manifest.json"), "--delay-s", str(args.delay_s),
        ]
        print(f"Running {len(tasks)} public JevBench cases against {endpoint} -> {out}", flush=True)
        # cwd=UPSTREAM: `-m` puts the cwd first on sys.path, so launching from a checkout
        # that has its own jevbench/ package would silently run that copy, not the vendored one.
        # check=False: an early stop must still yield a report over the cases already scored.
        harness_rc = subprocess.run(command, env=env, cwd=str(UPSTREAM), check=False).returncode
        records = read_records(out / "results.jsonl")
    end = termination(records, len(tasks), harness_rc)
    if end["status"] != "complete":
        print(f"EVAL ENDED ABRUPTLY: {end['reason']}", flush=True)
        for err in end["last_errors"]:
            print(f"  last error: {err['task_id']} HTTP {err['status_code']}: {err['error']}", flush=True)
    result = report(topic_data, tasks, records)
    result["termination"] = end
    result["provenance"] = {
        "scope": "public JevBench task subset only; not an official ranked score",
        "requested_version": profile.requested,
        "release_family": profile.family,
        "public_tiers": list(profile.tiers),
        "topic_label_source": "v1.2.15 topics.json applied to the selected public cases",
        "topic_revision": topic_data["revision"],
        "topics_sha256": hashlib.sha256(TOPICS.read_bytes()).hexdigest(),
        "task_dataset_hash": dataset_hash(tasks),
        "endpoint": endpoint, "requested_model": args.model,
        "attempted": len(records), "planned": len(tasks),
    }
    write_json(out / "topic-report.json", result)
    for row in result["by_topic"]:
        accuracy = f"{row['accuracy']:.1%}" if row["accuracy"] is not None else "—"
        print(f"{row['label']:<24} {row['correct']:>3}/{row['attempted']:<3} {accuracy}")
    whole = result["official_public_summary"]
    accuracy = f"{whole['accuracy']:.2%}" if whole["accuracy"] is not None else "—"
    print(f"Public overall: {whole['n_correct']}/{whole['n_scorable']} = {accuracy} "
          f"({whole['n_attempted']}/{whole['n_planned']} attempted); report: {out / 'topic-report.json'}", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
