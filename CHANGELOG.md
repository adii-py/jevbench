# Changelog

## v1.4.2.2 — 2026-09-27

- Added Imajev-4B (#1, 67.37) to the exact live v1.4.2.1 result using the unchanged v1.4.2 scorer.
- Preserved all prior measurement and score fields; only score-dependent ranks changed.
- The one-rotation run used the author's pinned adapter/server, `calibration.json`, and the pinned optimized kernels.
- 28 Sep text-only correction: the Imajev-4B cost basis now reflects the single pinned server pass. No score, axis, rank, eligibility, or numeric value changed.


## v1.4.2.1 — 2026-09-27

- Added Plumb-4B as the new #1 (65.84) on the live v1.4.2 base, using the exact v1.4.2 scoring code.
- Repriced Plumb's estimated input cost at the bookable EmpirioLabs Qwen3.5-4B rate ($0.04/M); the earlier $0.03/M reference was retired.
- Existing v1.4.2 measurements and display fields are unchanged; only score-dependent ranks move.

## v1.4.2 — 2026-09-25

- Added eleven newly measured systems and completed swanOne's sealed run; all rows use the full 842-decision protocol.
- New #1: decider-4b v2 (64.13), after an independent verification of its cost basis, generalization gap, overlap and score. Jev 1.13.0 out-reasons it (Intelligence 53.1 vs 49.4); decider-4b v2 leads on speed and cost.
- Systems without a public, bookable price carry a labelled estimate from their base model's public price.
- Kept the v1.4 scoring formula and every v1.4.1 measurement unchanged.

## v1.4.1 — 2026-09-23

- Added six systems omitted from the frozen v1.4.0 board, each with a completed 308-item sealed measurement.
- Kept the v1.4 scoring formula and all 76 v1.4.0 scores unchanged; the approved top five remains unchanged.
- Published aggregate accuracy and calibration data only. The six new rows have no API exposure flag because their sealed items were evaluated offline.

## v1.4.0 — 2026-09-23

- Added 308 fresh sealed decisions. Only aggregate results are published; task text and answers remain sealed.
- Set sealed Intelligence weight to 20% and blended Calibration by `0.2 / 0.35` toward the sealed-inclusive candidate axis.
- Added a generalization penalty for a public-to-sealed accuracy gap above 25 percentage points.
- Replaced the geometric composite with an equal-weight harmonic mean; retained the low-Intelligence penalty and added separate Speed and Cost gates below 50.
- Kept v1.3.0 Speed and Cost axes and the frozen v1.2 item measurements.
- Added API exposure flags and preserved contributor development and measurement disclosures.
- Added round 4, round 5 and GPT-6 Luna measurements. swanOne has no rank pending its sealed measurement.
