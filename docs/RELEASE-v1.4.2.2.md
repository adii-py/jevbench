# JevBench v1.4.2.2 release

Prepared for publication on 27 September 2026. This additive revision starts from the exact v1.4.2.1 artifact and adds the requested one-rotation Imajev-4B measurement. The v1.4.2 scoring module is unchanged. Existing measurements and score fields remain unchanged; only overall and preset ranks move where Imajev changes the order.

## Current top five

| Rank | System | JevBench Score |
|---:|---|---:|
| 1 | Imajev-4B | 67.37 |
| 2 | Plumb-4B (crh225, JevK5 v0.2 + LoRA) | 65.84 |
| 3 | decider-4b v2 (Mapika) | 64.13 |
| 4 | Jev 1.13.0 (TypeSafe AI) | 63.29 |
| 5 | JevK5 v0.2.0 | 62.04 |

## Score and provenance

- Imajev-4B's JevBench Score is `67.36821557095253`; Intelligence, Calibration, Speed, and Cost are recomputed from its candidate row using the exact live v1.4.2 `jevbench/composite_v14.py`, SHA-256 `33177d06eab9f78667972ec3b20997344f70a78e16b05326453a2c31200cac79`.
- The source row records adapter `mohit67890/imajev-4b@c9e5f132465da85d31735ec502d5557982671a7d`, server `mohit67890/imajev@a0134749e0900189c129cd6bb5000969f3b64bb5`, one rotation, and `calibration.json`. The optional `flash-linear-attention`/`fla-core` 0.5.2 and `causal-conv1d` 1.7.0 kernels were installed and profiled in the measured run.
- Estimated Cost uses the public DeepInfra Qwen/Qwen3.5-4B reference price ($0.03/M input, $0.15/M output) and the measured input tokens with zero generated output tokens. It is a public-price estimate, not a GPU bill.
- The exact aggregate-only result handoff is `RESULT-ROWS.json`, SHA-256 `51584c82047bf4392d5b05be1334775d6bfb51b2074cca682a87b1e7cdcaebf5`; the candidate source row is included under `results/v1.4.2.2/source/`.

## Integrity receipts

- Exact live v1.4.2.1 base SHA-256: `e4c5ec1b510212e29cba130a7a861096623c484dab9f5ecf9893360c1e993166`.
- v1.4.2.1 family supplement SHA-256: `968b7e6ce30e539328e42b24d1b1379f3214675b966dd3cf814dff3a74770814`.
- Imajev source-row SHA-256: `c26650b9bedc52445d693d2d8d67f047c5a21e40c3a2abd294c5c13b6424bb61`.
- v1.4.2.2 result SHA-256: `f0dfdd8f1601cadb16864061413e6e43c8b2dfa07b10ffd0716c67fc3c4b9952` at [`results/v1.4.2.2/jevbench-v1.4.2.2-results.json`](../results/v1.4.2.2/jevbench-v1.4.2.2-results.json).
- Family supplement SHA-256: `df41a1152f32b9f32448ae0da2ea3a304d84727254650a01ab540b3a5284a078` at [`results/v1.4.2.2/jevbench-v1.4.2.2-family-supplement.json`](../results/v1.4.2.2/jevbench-v1.4.2.2-family-supplement.json).
- Reproduction uses [`scripts/v1.4.2.2/build.py`](../scripts/v1.4.2.2/build.py). The builder's integrity assertions passed when producing this candidate; no local test suite was run.

This revision contains 95 systems, 91 ranked. It adds Imajev-4B to the already live Plumb-4B revision. Laya Vision remains out of this candidate under its separate author confirmation hold and may be handled by a later additive revision if that hold is lifted.
