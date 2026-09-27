"""Build v1.4.2.1 by adding an aggregate-only row to the exact live v1.4.2 artifact."""

from __future__ import annotations

import copy
import datetime as dt
import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DATA = ROOT / "results" / "v1.4.2.1"
BASE = DATA / "base-live-v1.4.2-results.json"
SOURCE = DATA / "source" / "plumb-4b-ROW-v1.4.3.json"
PRICED_ROW = DATA / "source" / "plumb-4b-latest-v1.4.3-public-row.json"
AGGREGATE_SOURCE = DATA / "source" / "plumb-4b-AGGREGATE-SOURCE-v1.4.3.json"
FOOTNOTE_SOURCE = DATA / "source" / "plumb-4b-footnote.txt"
OUTPUT = DATA / "jevbench-v1.4.2.1-results.json"
BASE_FAMILIES = DATA / "base-live-v1.4.2-family-supplement.json"
FAMILIES_OUTPUT = DATA / "jevbench-v1.4.2.1-family-supplement.json"
BASE_SHA256 = "fb81f4e774e7a965eff7b5bed641cff62c7e51c9b28464dca83d5d7725990fcd"
SCORER_SHA256 = "33177d06eab9f78667972ec3b20997344f70a78e16b05326453a2c31200cac79"
EXPECTED_TOP5 = ["plumb-4b", "decider-4b-v2", "jev-1.13.0", "jevk5-v02", "cygnet"]

sys.path.insert(0, str(ROOT))
from jevbench import composite_v13 as old_score  # noqa: E402
from jevbench import composite_v14 as score  # noqa: E402


def read(path: Path):
    return json.loads(path.read_text())


def build() -> dict:
    base_bytes = BASE.read_bytes()
    if hashlib.sha256(base_bytes).hexdigest() != BASE_SHA256:
        raise ValueError("base artifact differs from the exact live v1.4.2 response")
    if hashlib.sha256(Path(score.__file__).read_bytes()).hexdigest() != SCORER_SHA256:
        raise ValueError("scoring module differs from the v1.4.2 tag")

    base = json.loads(base_bytes)
    source = read(SOURCE)
    priced = read(PRICED_ROW)
    aggregate_bytes = AGGREGATE_SOURCE.read_bytes()
    if base.get("revision") != "v1.4.2" or len(base.get("systems", [])) != 93:
        raise ValueError("unexpected live v1.4.2 baseline")
    if source.get("key") != "plumb-4b" or priced.get("key") != "plumb-4b":
        raise ValueError("expected the Plumb-4B measurement and price-corrected row")
    expected_aggregate_sha = priced["release_evidence"]["aggregate_source_sha256"]
    if hashlib.sha256(aggregate_bytes).hexdigest() != expected_aggregate_sha:
        raise ValueError("Plumb aggregate source does not match the priced public-row receipt")
    if any(row.get("key") == "plumb-4b" for row in base["systems"]):
        raise ValueError("Plumb-4B already exists in the live baseline")

    # The original measurement receipt used a retired $0.03/M basis. The latest
    # v1.4.3 row records the bookable exact-base $0.04/M basis; feed its resulting
    # Cost axis to the unchanged v1.4.2 comparison scorer.
    source = copy.deepcopy(source)
    source["v130"]["axes"]["cost"] = priced["axes"]["cost"]
    source["note_v14"] = priced["scoring_note"]
    axes, composite = score.score_from_comparison(source)
    if composite != priced["jevbench_score"] or axes != priced["axes"]:
        raise ValueError("exact v1.4.2 recomputation did not reproduce the corrected source row")

    row = copy.deepcopy(priced)
    row.update(
        new_in="v1.4.2.1",
        axes=axes,
        jevbench_score=composite,
        rank=None,
        rank_under={},
        presets={
            name: score.harmonic(axes, dict(zip(old_score.AXES, weights)))
            for name, weights in old_score.PRESETS.items()
        },
        calibration={"score": axes["calibration"], "note": None},
        source_round="v1.4.2.1 fast-lane addition (official Plumb-4B v1.4 protocol measurement)",
    )

    artifact = copy.deepcopy(base)
    footnotes = copy.deepcopy(base.get("footnotes", {}))
    footnotes["plumb-4b"] = FOOTNOTE_SOURCE.read_text().strip()
    artifact.update(
        revision="v1.4.2.1",
        status="final",
        generated_utc=dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"),
        revision_note=(
            "v1.4.2.1 adds Plumb-4B to the exact live v1.4.2 board. Existing measurement, "
            "score, cost and display fields are unchanged; ranks and preset ranks move only "
            "where the new row changes the ordering. Scoring formulas and v1.4.2 measurements are unchanged."
        ),
        top_five_note=(
            "Plumb-4B leads the equal-weight JevBench Score at 65.84, ahead of decider-4b v2 (64.13). "
            "Jev 1.13.0 remains ahead of decider-4b v2 on Intelligence and Calibration; decider-4b v2 "
            "leads on Speed and Cost. Sort by Intelligence to compare raw reasoning."
        ),
        footnotes=footnotes,
        systems=artifact["systems"] + [row],
        revision_log=base["revision_log"] + [
            {
                "revision": "v1.4.2.1",
                "date": "2026-09-27",
                "note": (
                    "Added Plumb-4B, measured on the full v1.4 protocol. The v1.4.2 scorer is "
                    "unchanged. Its estimated Cost uses the bookable EmpirioLabs exact-base "
                    "Qwen3.5-4B input price of $0.04/M; prior v1.4.2 rows are unchanged."
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
    if len(artifact["systems"]) != 94 or len(ranked) != 90:
        raise ValueError("unexpected v1.4.2.1 row counts")

    old_by_key = {item["key"]: item for item in base["systems"]}
    for item in artifact["systems"]:
        if item["key"] == "plumb-4b":
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
    if families.get("revision") != "v1.4.2" or families.get("kind") != "family-supplement":
        raise ValueError("unexpected live v1.4.2 family supplement")
    families.update(
        revision="v1.4.2.1",
        created_utc=artifact["generated_utc"],
        base_artifact_sha256=BASE_SHA256,
        note=(
            "Carries forward the v1.4.2 hard-family aggregates unchanged. Plumb-4B's sealed "
            "family aggregates are in the main result artifact; no per-family 220-item hard-tier "
            "breakdown was available for the Plumb row."
        ),
    )
    FAMILIES_OUTPUT.write_text(json.dumps(families, indent=1, ensure_ascii=False, allow_nan=False) + "\n")
    print(f"Built {len(artifact['systems'])} systems; {len(ranked)} ranked")
    print("Top five:", ", ".join(f"{item['display']} {item['jevbench_score']:.2f}" for item in ranked[:5]))
    print(f"Plumb exact v1.4.2 score: {composite:.14f}; scorer SHA-256 {SCORER_SHA256}")
    return artifact


if __name__ == "__main__":
    build()
