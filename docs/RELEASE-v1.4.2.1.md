# JevBench v1.4.2.1 release

Released 27 September 2026. This additive revision starts from the exact live v1.4.2 artifact and adds the officially measured Plumb-4B row. All earlier measurement, score, cost and display fields remain unchanged; only overall and preset ranks move where Plumb changes the order.

## Current top five

| Rank | System | JevBench Score |
|---:|---|---:|
| 1 | Plumb-4B (crh225, JevK5 v0.2 + LoRA) | 65.84 |
| 2 | decider-4b v2 (Mapika) | 64.13 |
| 3 | Jev 1.13.0 (TypeSafe AI) | 63.29 |
| 4 | JevK5 v0.2.0 | 62.04 |
| 5 | Cygnet (blockbrain, frozen Gemma-4-12B-it) | 61.76 |

## Score and provenance

- Plumb's composite is `65.84344821613185`; Intelligence 52.9789266844, Calibration 75.4854439416, Speed 93.4904047993, Cost 55.7697791406.
- The score was recomputed with the exact v1.4.2 tag module `jevbench/composite_v14.py`, SHA-256 `33177d06eab9f78667972ec3b20997344f70a78e16b05326453a2c31200cac79`.
- The input is the latest Plumb run-14 aggregate row. The current bookable EmpirioLabs Qwen3.5-4B input rate is $0.04/M. This replaces a retired $0.03/M reference; the resulting estimate is $0.0298085393258427 per 1,000 decisions. This estimates API-equivalent usage and is not a GPU bill.
- Request issue #84 pins `crh225/plumb-4b` revision `55de037801a8a9b9de3db5c0e16cef86210c2186` and the author's `crh225/plumb` serving path with JevK5 v0.2.0. The runtime tag resolves to `85238d7be5527370c43206fe54cd752eb3134c1b`. Recorded source review is PASS.
- Plumb ran all 842 decisions using the evaluator-owned offline, read-only GPU path. The artifact contains aggregate sealed statistics only; it does not include item text, answers or per-item predictions.

## Integrity receipts

- Exact live v1.4.2 base SHA-256: `fb81f4e774e7a965eff7b5bed641cff62c7e51c9b28464dca83d5d7725990fcd`.
- Source measurement row SHA-256: `0fe248c8e2c1f267951c8d8c0fd3a480baea1cbf725caacd2911c087facda709`.
- Plumb aggregate-source SHA-256: `aade49ff5c86936b14ed287d6a503d3c1ba2884eb2b9f745cc8f0e4b73296165`; corrected public row input: [`results/v1.4.2.1/source/plumb-4b-latest-v1.4.3-public-row.json`](../results/v1.4.2.1/source/plumb-4b-latest-v1.4.3-public-row.json); original aggregate and release footnote are preserved beside it.
- Result SHA-256: `e4c5ec1b510212e29cba130a7a861096623c484dab9f5ecf9893360c1e993166` at [`results/v1.4.2.1/jevbench-v1.4.2.1-results.json`](../results/v1.4.2.1/jevbench-v1.4.2.1-results.json). Family-supplement SHA-256: `968b7e6ce30e539328e42b24d1b1379f3214675b966dd3cf814dff3a74770814` at [`results/v1.4.2.1/jevbench-v1.4.2.1-family-supplement.json`](../results/v1.4.2.1/jevbench-v1.4.2.1-family-supplement.json). The supplement carries forward v1.4.2 family aggregates; no Plumb hard-tier family breakdown was available. Reproduction uses [`scripts/v1.4.2.1/build.py`](../scripts/v1.4.2.1/build.py).

This revision does not include ImageJevBench or other fast-lane rows. Rows held for customer confirmation or still in measurement will be handled in a later revision.
