"""Pinned public JevBench task profiles, separate from official ranked scores.

Later releases reuse the public v1.2 task files while changing private
populations and composite scoring. A local public run is never an official
leaderboard result. The v1.5 public corpus has not been published in the
upstream repository, so it must not silently fall back to v1.2 tasks.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


PUBLIC_SHA256 = {
    "easy": "231df3c2c8e88a1a8c137ebe85de96ba70fabd330849098ac7b3c52c70b7172b",
    "original": "5c2414edb3006b8bfcb70fda433f0f9ca015759433849f8d3104328a1f7c4180",
    "hard": "89e9e6becb33ed88c1de7d42dcc87531b2fb64cfaef4e1986faf7c37b3f80ebb",
}
PUBLIC_COUNTS = {"easy": 48, "original": 72, "hard": 111}


@dataclass(frozen=True)
class JevVersion:
    requested: str
    family: str
    tiers: tuple[str, ...]
    public_records: int
    availability: str

    def paths(self, repo: Path) -> tuple[Path, ...]:
        return tuple(repo / "datasets" / "public" / f"{tier}.jsonl" for tier in self.tiers)


ALIASES = {
    "v1.0": ("original",),
    "v1.1": ("easy", "original"),
    **{f"v1.1.{patch}": ("easy", "original") for patch in range(1, 4)},
    "v1.2": ("easy", "original", "hard"),
    **{f"v1.2.{patch}": ("easy", "original", "hard") for patch in range(1, 17)},
    "v1.3": ("easy", "original", "hard"),
    "v1.3.0": ("easy", "original", "hard"),
    "v1.4": ("easy", "original", "hard"),
    "v1.4.0": ("easy", "original", "hard"),
    "v1.4.1": ("easy", "original", "hard"),
    "v1.4.2": ("easy", "original", "hard"),
    "v1.4.2.1": ("easy", "original", "hard"),
    "v1.4.2.2": ("easy", "original", "hard"),
    "v1.5": (),
    "v1.5.0": (),
}


def resolve_version(name: str) -> JevVersion:
    key = name.strip().lower()
    if key and key[0].isdigit():
        key = "v" + key
    if key not in ALIASES:
        raise ValueError(f"Unknown JevBench release {name!r}; use --list-jev-versions")
    tiers = ALIASES[key]
    family = ".".join(key.split(".")[:2])
    availability = "public_subset" if tiers else "external_tasks_required"
    return JevVersion(key, family, tiers, sum(PUBLIC_COUNTS[t] for t in tiers), availability)


def listed_families() -> list[dict]:
    return [
        {"version": name, "public_records": resolve_version(name).public_records,
         "status": resolve_version(name).availability}
        for name in ("v1.0", "v1.1", "v1.2", "v1.3", "v1.4", "v1.5")
    ]
