# ImageJevBench v0.1.3 candidate

This additive ImageJevBench revision replaces only the Imajev-4B row with the paid fast-serving remeasurement. The JevBench text result remains unchanged. The frozen ImageJevBench v0.1.x method, 228-public/456-sealed split, scorer and one-rotation setting are unchanged.

## Candidate row

- **Imajev-4B:** #1 of 49, score **76.39** (exact: `76.38798675595419`).
- Previous ImageJevBench v0.1.2 row: #11 of 49, `65.72451137285294`.
- Axes: Intelligence 73.77, Calibration 90.52, Speed 87.59, Cost 61.18.
- Track scores: all `76.38798675595419`, core `75.49047861959203`, everyday photo `77.89952209964332`.

## Serving and scoring

Adapter `mohit67890/imajev-4b@c9e5f132465da85d31735ec502d5557982671a7d`; server `mohit67890/imajev@8501f5c3b1ed8ef608744eabed40f22b70de4277`. PyTorch backend, one rotation, `calibration.json`, `--fast --merge-lora`; flash-linear-attention/fla-core 0.5.2, causal-conv1d 1.7.0, and build-essential were retained. CUDA graphs replayed on all six public smoke items. The six smoke answer indices matched the prior optimized run; maximum probability delta was 0.0473833420.

The RTX 5090 pod rate was USD 0.67/hour. Speed and cost use the published self-hosted adjustment unchanged. The frozen scorer was run twice; both passes match, and the separate aggregate recomputation passes. See `release-manifest.json` and `independent-recomputation.json`.

The aggregate row and verification receipt contain no item text, images, answer keys, or per-item predictions. The raw prediction file remains in the restricted sealed directory and is not part of this repository.
