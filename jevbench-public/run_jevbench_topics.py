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


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--endpoint", help="System One API base URL")
    parser.add_argument("--model", help="model value sent to the endpoint")
    parser.add_argument("--api-key-env", default="SYSTEMONE_BENCH_API_KEY", help="environment variable containing the bearer key")
    parser.add_argument("--out", type=Path, help="new output directory")
    parser.add_argument("--topic", action="append", help="run only this topic key; repeatable")
    parser.add_argument("--limit", type=int, help="first N selected cases (smoke test)")
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
    if args.limit is not None:
        if args.limit < 1:
            parser.error("--limit must be positive")
        tasks = tasks[:args.limit]
    if args.results and (args.topic or args.limit):
        parser.error("--results expects the full public results; omit --topic and --limit")
    endpoint = (args.endpoint or "").rstrip("/")
    if endpoint.endswith("/v1/systemone"):
        endpoint = endpoint.removesuffix("/v1/systemone")
    out = args.out or ROOT / "runs" / f"jevbench-{profile.requested}-topics-{dt.datetime.now().strftime('%Y%m%d-%H%M%S')}"
    out = out.resolve()
    out.mkdir(parents=True, exist_ok=False)
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
            "--manifest", str(out / "run-manifest.json"),
        ]
        print(f"Running {len(tasks)} public JevBench cases against {endpoint} -> {out}", flush=True)
        subprocess.run(command, env=env, check=True)
        records = [json.loads(line) for line in (out / "results.jsonl").read_text().splitlines() if line.strip()]
    result = report(topic_data, tasks, records)
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
    print(f"Public overall: {whole['n_correct']}/{whole['n_scorable']} = {whole['accuracy']:.2%}; report: {out / 'topic-report.json'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
