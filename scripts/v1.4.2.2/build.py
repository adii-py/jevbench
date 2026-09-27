"""Build the Imajev-4B addition on the exact v1.4.2.1 result artifact."""

from __future__ import annotations

import copy
import datetime as dt
import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DATA = ROOT / "results" / "v1.4.2.2"
BASE = DATA / "base-live-v1.4.2.1-results.json"
BASE_FAMILIES = DATA / "base-live-v1.4.2.1-family-supplement.json"
SOURCE = DATA / "source" / "imajev_4b-ROW-v1.4.2.1.json"
OUTPUT = DATA / "jevbench-v1.4.2.2-results.json"
FAMILIES_OUTPUT = DATA / "jevbench-v1.4.2.2-family-supplement.json"

BASE_SHA256 = "e4c5ec1b510212e29cba130a7a861096623c484dab9f5ecf9893360c1e993166"
BASE_FAMILIES_SHA256 = "968b7e6ce30e539328e42b24d1b1379f3214675b966dd3cf814dff3a74770814"
SOURCE_SHA256 = "c26650b9bedc52445d693d2d8d67f047c5a21e40c3a2abd294c5c13b6424bb61"
HANDOFF_SHA256 = "51584c82047bf4392d5b05be1334775d6bfb51b2074cca682a87b1e7cdcaebf5"
SCORER_SHA256 = "33177d06eab9f78667972ec3b20997344f70a78e16b05326453a2c31200cac79"
EXPECTED_TOP5 = ["imajev_4b", "plumb-4b", "decider-4b-v2", "jev-1.13.0", "jevk5-v02"]

sys.path.insert(0, str(ROOT))
from jevbench import composite_v13 as old_score  # noqa: E402
from jevbench import composite_v14 as score  # noqa: E402


def read(path: Path):
    return json.loads(path.read_text())


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def make_row(source: dict, axes: dict, composite: float) -> dict:
    measurements = source["measurements"]
    speed_source = measurements["old_speed"]
    cost_source = measurements["cost"]
    sealed = copy.deepcopy(source["sealed"])
    sealed.pop("results_location", None)

    return {
        "key": source["key"],
        "display": source["display"],
        "author": source["author"],
        "repo": source["repo"],
        "class": source["class"],
        "licence": source["licence"],
        "open": "yes",
        "underlying": None,
        "has_distribution": True,
        "probability_source": "author server class probabilities",
        "endpoint_condition": (
            "Evaluator-owned Lium GPU pod; network-disabled, read-only container; "
            "the author's reviewed server ran on loopback."
        ),
        "endpoint_kind": "gpu",
        "partial": False,
        "ranked": True,
        "listing": "ranked",
        "not_ranked_because": None,
        "tiers": copy.deepcopy(source["v14"]["tiers"]),
        "speed": {
            "p50_s_raw": speed_source["p50_raw_s"],
            "p95_s_raw": speed_source["p95_raw_s"],
            "p50_s_adjusted": speed_source["p50_adjusted_s"],
            "p95_s_adjusted": speed_source["p95_adjusted_s"],
            "adjustment": "x2 + 0.15 s (assumption, not measured)",
            "run": "serial standard+judge requests; 242 decisions",
            "hardware": "evaluator-owned Lium GPU; exact model recorded in the run receipt",
            "measured_where": speed_source["basis"],
            "hard_tier_p50_s": None,
            "hard_tier_p95_s": None,
        },
        "cost": {
            "kind": "estimate",
            "usd_per_1000": cost_source["usd_per_1000_estimate"],
            "basis": cost_source["basis"],
            "usd_per_1000_v11_tiers": None,
            "usd_per_1000_hard": None,
            "self_host_sensitivity": None,
            "previous_price_basis": None,
        },
        "calibration": {"score": axes["calibration"], "note": None},
        "hard": None,
        "release_evidence": {
            "raw_results_sha256": source["raw_results_sha256"],
            "input_sha256": source["input_sha256"],
            "scope_counts": copy.deepcopy(measurements["scope_counts"]),
            "source_row_sha256": SOURCE_SHA256,
            "result_rows_handoff_sha256": HANDOFF_SHA256,
        },
        "new_in": "v1.4.2.2",
        "source_round": "v1.4.2.2 fast-lane addition (official Imajev-4B v1.4 protocol measurement; one rotation)",
        "api_flag": source["api_flag"],
        "api_exposure_note": None,
        "public_accuracy": source["public_acc"],
        "sealed_accuracy": source["sealed_acc"],
        "public_minus_sealed_gap_pp": (source["public_acc"] - source["sealed_acc"]) * 100,
        "sealed_aggregate": sealed,
        "v130_comparison_rank": source["v130"]["rank"],
        "v130_comparison_score": source["v130"]["score"],
        "axes": axes,
        "jevbench_score": composite,
        "presets": {
            name: score.harmonic(axes, dict(zip(old_score.AXES, weights)))
            for name, weights in old_score.PRESETS.items()
        },
        "scoring_note": source["note_v14"],
        "pricing_change_note": None,
        "rank": None,
        "rank_under": {},
    }


def build() -> dict:
    if sha256(BASE) != BASE_SHA256:
        raise ValueError("base artifact differs from the live v1.4.2.1 result")
    if sha256(BASE_FAMILIES) != BASE_FAMILIES_SHA256:
        raise ValueError("v1.4.2.1 family supplement differs from its release hash")
    if sha256(SOURCE) != SOURCE_SHA256:
        raise ValueError("Imajev-4B source row differs from the verified handoff row")
    if hashlib.sha256(Path(score.__file__).read_bytes()).hexdigest() != SCORER_SHA256:
        raise ValueError("scoring module differs from the live v1.4.2 scorer")

    base = read(BASE)
    source = read(SOURCE)
    if base.get("revision") != "v1.4.2.1" or len(base.get("systems", [])) != 94:
        raise ValueError("unexpected live v1.4.2.1 baseline")
    if source.get("key") != "imajev_4b" or not source.get("status", "").startswith("CANDIDATE"):
        raise ValueError("expected the verified Imajev-4B candidate row")
    if source.get("release_score", {}).get("scoring_module_sha256") != SCORER_SHA256:
        raise ValueError("candidate row does not bind the live v1.4 scorer")
    if any(item.get("key") == source["key"] for item in base["systems"]):
        raise ValueError("Imajev-4B already exists in the live v1.4.2.1 baseline")

    axes, composite = score.score_from_comparison(source)
    recorded = source["release_score"]
    if composite != recorded["score"] or axes != recorded["axes"]:
        raise ValueError("exact v1.4.2 recomputation did not reproduce the Imajev source row")

    row = make_row(source, axes, composite)
    artifact = copy.deepcopy(base)
    footnotes = copy.deepcopy(base.get("footnotes", {}))
    footnotes["imajev_4b"] = (
        "Imajev-4B: requested adapter c9e5f132465da85d31735ec502d5557982671a7d and server "
        "a0134749e0900189c129cd6bb5000969f3b64bb5; one rotation with calibration.json. "
        "The optimized image included flash-linear-attention/fla-core 0.5.2 and causal-conv1d 1.7.0; "
        "CUDA profiling confirmed the pinned kernels ran. Cost is an estimate using the public "
        "DeepInfra Qwen/Qwen3.5-4B base-model reference price ($0.03/M input, $0.15/M output), "
        "with no generated output tokens; it is not a GPU bill."
    )
    artifact.update(
        revision="v1.4.2.2",
        status="final",
        generated_utc=dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"),
        revision_note=(
            "v1.4.2.2 adds the verified Imajev-4B row to v1.4.2.1 using the exact live v1.4.2 "
            "scoring code. Earlier measurements and score fields are unchanged; only ranks and "
            "preset ranks move where the new row changes the ordering."
        ),
        top_five_note=(
            "Imajev-4B leads the JevBench Score at 67.37, ahead of Plumb-4B (65.84). "
            "The v1.4.2 scoring code and earlier measurement rows are unchanged."
        ),
        footnotes=footnotes,
        systems=artifact["systems"] + [row],
        revision_log=base["revision_log"] + [
            {
                "revision": "v1.4.2.2",
                "date": "2026-09-27",
                "note": (
                    "Added Imajev-4B, measured on the full v1.4 protocol with one rotation and "
                    "calibration.json. The v1.4.2 scorer is unchanged; earlier rows are unchanged."
                ),
            }
        ],
    )

    ranked = [item for item in artifact["systems"] if item.get("ranked") is True]
    unranked = [item for item in artifact["systems"] if item.get("ranked") is not True]
    ranked.sort(key=lambda item: (-item["jevbench_score"], item["display"].casefold()))
    for rank, item in enumerate(ranked, 1):
        item["rank"] = rank
        item["rank_under"] = {}
    for item in unranked:
        item["rank"] = None
        item["rank_under"] = {}
    for preset in old_score.PRESETS:
        ordered = sorted(ranked, key=lambda item: (-(item["presets"].get(preset) or 0), item["display"].casefold()))
        for rank, item in enumerate(ordered, 1):
            item["rank_under"][preset] = rank
    artifact["systems"] = ranked + unranked

    top5 = [item["key"] for item in ranked[:5]]
    if top5 != EXPECTED_TOP5:
        raise ValueError(f"unexpected top five: {top5}")
    if len(artifact["systems"]) != 95 or len(ranked) != 91:
        raise ValueError("unexpected v1.4.2.2 row counts")
    if ranked[0]["key"] != "imajev_4b" or ranked[1]["key"] != "plumb-4b":
        raise ValueError("unexpected new leader or Plumb rank")

    old_by_key = {item["key"]: item for item in base["systems"]}
    for item in artifact["systems"]:
        if item["key"] == source["key"]:
            continue
        old = copy.deepcopy(old_by_key[item["key"]])
        current = copy.deepcopy(item)
        for value in (old, current):
            value.pop("rank", None)
            value.pop("rank_under", None)
        if current != old:
            raise ValueError(f"existing non-rank fields changed for {item['key']}")

    OUTPUT.write_text(json.dumps(artifact, indent=1, ensure_ascii=False, allow_nan=False) + "\n")
    families = read(BASE_FAMILIES)
    if families.get("revision") != "v1.4.2.1" or families.get("kind") != "family-supplement":
        raise ValueError("unexpected v1.4.2.1 family supplement")
    families.update(
        revision="v1.4.2.2",
        created_utc=artifact["generated_utc"],
        base_artifact_sha256=BASE_SHA256,
        note=(
            "Carries forward the v1.4.2.1 hard-family aggregates unchanged. Imajev-4B's "
            "aggregate sealed-family counts are in the main result artifact."
        ),
    )
    FAMILIES_OUTPUT.write_text(json.dumps(families, indent=2, ensure_ascii=False, allow_nan=False) + "\n")
    print(f"Built {len(artifact['systems'])} systems; {len(ranked)} ranked")
    print("Top five:", ", ".join(f"{item['display']} {item['jevbench_score']:.2f}" for item in ranked[:5]))
    print(f"Imajev-4B exact v1.4.2 score: {composite:.14f}; scorer SHA-256 {SCORER_SHA256}")
    print(f"Imajev rank #{ranked[0]['rank']}; Plumb rank #{ranked[1]['rank']}")
    return artifact


if __name__ == "__main__":
    build()
