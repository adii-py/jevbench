# Dashboard input parameters

Copy the JSON object in [`input_param.json`](../input_param.json) into the eval **Input Config (JSON)** field (`fields` array; each field needs `name`, `label`, and `type`).

The API key is **not** in this JSON. The runner passes it as the first argument to `run.sh` (env `API_KEY` / `GRID_AI_API`).

## Field reference

| Field | `run.sh` flag | Used? | Notes |
|--------|----------------|-------|--------|
| `model` | `--model` | No (Validate only) | Dashboard binds a Grid **chat** alias so Validate passes. Jev is not a chat model; this value is logged and ignored. |
| `model_alpha` | `--model-alpha` | **Yes** | System One model id sent in the `/v1/systemone` body (e.g. `jev-latest`). This is the model being scored. |
| `base_url` | `--base-url` | **Yes** | Host only; runner posts to `{base_url}/v1/systemone`. Trailing `/v1` or `/v1/systemone` is stripped. Default Grid: `https://grid.ai.juspay.net`. |
| `jev_version` | `--jev-version` | **Yes** | Public case profile (default `v1.4.2.2` → 231 cases). |
| `task_range` | `--task-range` | **Yes** | Inclusive `start-end` on the fixed 231-case list. Smoke: `0-9`. Empty / omit: all 231. Index map: easy `0-47`, original `48-119`, hard `120-230`. |
| `delay_s` | `--delay-s` | **Yes** | Seconds between serial requests (default `0.5`; helps stay under ~150 rpm). |
| `split` | `--split` | No | Documented for operators; ignored (version defines the full public set). |
| `cap_usd` | — | No | Ignored (public runner uses its own cap). |
| `input_token_price` | — | No | Ignored. |
| `output_token_price` | — | No | Ignored. |
| `request_options` | — | No | Ignored (System One adapter, not chat completions). |

## Example run values (smoke)

These are **run-time** parameters, not the Input Config schema:

```json
{
  "model": "open-large",
  "model_alpha": "jev-latest",
  "base_url": "https://grid.ai.juspay.net",
  "jev_version": "v1.4.2.2",
  "task_range": "0-9",
  "delay_s": 0.5
}
```

Use any Grid chat alias you need for `model`; only `model_alpha` affects JevBench scoring.

## Example run values (full public set)

Omit `task_range` or set it to an empty string:

```json
{
  "model_alpha": "jev-latest",
  "base_url": "https://grid.ai.juspay.net",
  "jev_version": "v1.4.2.2",
  "delay_s": 0.5
}
```

Machine type: **`n2-standard-2`**. Headline metric: **Public Accuracy** over attempted cases (not the official ranked JevBench Score).
