# Portable public JevBench

Requires Python 3.10+ and a reachable System One `POST /v1/systemone` endpoint.
No installation, model weights, or network download is needed for the runner.

```sh
./run.sh --list-versions
./run.sh --endpoint http://127.0.0.1:49003 --model xor-1.2 \
  --version v1.2 --out runs/xor-1.2-v1.2
```

Use a new `--out` directory for each run. For authenticated endpoints, export
the bearer key and add `--api-key-env NAME_OF_VARIABLE`. The report is
`topic-report.json`; `results.jsonl`, `ledger.jsonl`, and `raw/` preserve
per-case results and traces. `--topic KEY` selects one topic (repeatable), and
`--limit N` makes a smoke run. `--results PATH` summarizes an existing full
public run without contacting the endpoint.

Public task counts: v1.0 = 72, v1.1 = 120, v1.2-v1.4 = 231. Patch versions use
their release family's same published public cases. Private leaderboard cases
are not included, so these are public-subset scores, not official ranks.
v1.5 public task text is not in the upstream repository and is unavailable here.
The runner and tasks come from JevBench commit
`1bcc55eb6c8cffde2306b3db03ede39b61c6152a`; its LICENSE is included.
