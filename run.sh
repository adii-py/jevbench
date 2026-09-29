#!/usr/bin/env bash
# run.sh — dashboard entrypoint. The eval itself is jevbench-public/run.sh,
# which executes run_jevbench_topics.py against the vendored public cases.

if [ -z "${STDBUF_APPLIED:-}" ] && command -v stdbuf >/dev/null 2>&1; then
    export STDBUF_APPLIED=1
    exec stdbuf -oL -eL bash "${BASH_SOURCE[0]}" "$@"
fi

set -uo pipefail
export PYTHONUNBUFFERED=1

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PUBLIC_RUN="${SCRIPT_DIR}/jevbench-public/run.sh"
log_info() { echo "[run][INFO]  $*"; }
log_ok()   { echo "[run][OK]    $*"; }
log_warn() { echo "[run][WARN]  $*" >&2; }
log_err()  { echo "[run][ERR]   $*" >&2; }
log_step() { echo; echo "===== $* ====="; }

ENV_API_KEY="${API_KEY:-}"
API_KEY=""
EVAL_RUN_ID=""
if [ -n "${1:-}" ] && [ "${1#--}" = "$1" ] && [ -n "${2:-}" ] && [ "${2#--}" = "$2" ]; then
    API_KEY="$1"
    EVAL_RUN_ID="$2"
    shift 2
elif [ -n "${1:-}" ] && [ "${1#--}" = "$1" ]; then
    EVAL_RUN_ID="$1"
    shift
else
    EVAL_RUN_ID="local_$(date +%Y%m%d_%H%M%S)"
fi
if [ -z "$API_KEY" ]; then
    API_KEY="${GRID_AI_API:-$ENV_API_KEY}"
fi
export API_KEY

MODEL="jev-latest"
ENDPOINT="https://api.typesafe.ai"
JEV_VERSION="v1.4.2.2"
TASK_RANGE=""
SPLIT=""

while [ $# -gt 0 ]; do
    case "$1" in
        --model)         MODEL="${2:-}"; shift 2 ;;
        --base-url)      ENDPOINT="${2:-}"; shift 2 ;;
        --endpoint)      ENDPOINT="${2:-}"; shift 2 ;;
        --jev-version)   JEV_VERSION="${2:-}"; shift 2 ;;
        --version)       JEV_VERSION="${2:-}"; shift 2 ;;
        --task-range)    TASK_RANGE="${2:-}"; shift 2 ;;
        --split)         SPLIT="${2:-}"; shift 2 ;;
        --*)
            if [ $# -ge 2 ] && [ -n "${2:-}" ] && [ "${2#--}" = "$2" ]; then
                log_warn "ignoring unknown flag $1"
                shift 2
            else
                log_warn "ignoring unknown flag $1"
                shift
            fi
            ;;
        *)
            log_warn "ignoring unexpected argument"
            shift
            ;;
    esac
done

if [ -n "$SPLIT" ]; then
    log_warn "split=${SPLIT} is ignored; ${JEV_VERSION} selects its own public cases"
fi

OUTPUT_ROOT="${EVAL_RUNNER_OUTPUT_DIR:-${SCRIPT_DIR}/output}"
mkdir -p "$OUTPUT_ROOT"
RESULTS_FILE="${OUTPUT_ROOT}/${EVAL_RUN_ID}_results.json"

if [ -n "${JEVBENCH_PRIVATE_ROOT:-}" ]; then
    PRIVATE_ROOT="$JEVBENCH_PRIVATE_ROOT"
elif [ -n "${EVAL_RUNNER_WORK_DIR:-}" ]; then
    PRIVATE_ROOT="$(cd "${EVAL_RUNNER_WORK_DIR}/.." && pwd)/jevbench-private"
else
    PRIVATE_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)/jevbench-private"
fi
TOPICS_OUT="${PRIVATE_ROOT}/${EVAL_RUN_ID}/topics"

write_fallback_results() {
    [ -f "$RESULTS_FILE" ] && return 0
    local reason="${1:-unknown}"
    python3 - "$RESULTS_FILE" "$reason" <<'PY'
import json, os, sys
path, reason = sys.argv[1], sys.argv[2]
doc = {"metrics": {
    "main": {"name": "Public Accuracy", "value": 0},
    "secondary": {"n_correct": 0, "n_attempted": 0, "n_planned": 0, "complete": 0},
    "additional": {"status": "no-results", "reason": reason, "protocol": "v1.4.2.2"},
}}
tmp = path + ".tmp"
with open(tmp, "w", encoding="utf-8") as fh:
    json.dump(doc, fh, indent=2)
    fh.write("\n")
os.replace(tmp, path)
PY
    log_warn "wrote fallback zero-metric results (${reason})"
}
on_exit() {
    local rc=$?
    write_fallback_results "exit ${rc}"
}
trap on_exit EXIT

if [ ! -x "$PUBLIC_RUN" ]; then
    log_err "missing ${PUBLIC_RUN}"
    exit 1
fi

LIMIT_ARGS=()
if [ -n "$TASK_RANGE" ]; then
    start="${TASK_RANGE%-*}"
    end="${TASK_RANGE#*-}"
    case "$start" in
        ''|*[!0-9]*) log_err "bad task_range ${TASK_RANGE}"; exit 1 ;;
    esac
    case "$end" in
        ''|*[!0-9]*) log_err "bad task_range ${TASK_RANGE}"; exit 1 ;;
    esac
    if [ "$start" != "0" ]; then
        log_err "jevbench-public only supports a prefix; task_range must start at 0 (got ${TASK_RANGE})"
        exit 1
    fi
    if [ "$end" -lt "$start" ]; then
        log_err "task_range ${TASK_RANGE} has start > end"
        exit 1
    fi
    limit=$((end + 1))
    LIMIT_ARGS=(--limit "$limit")
    log_info "task_range ${TASK_RANGE} -> --limit ${limit} (first ${limit} public cases)"
fi

if [ -z "$API_KEY" ]; then
    log_err "API_KEY is empty"
    exit 1
fi

log_step "Running jevbench-public"
log_info "command: jevbench-public/run.sh --endpoint ${ENDPOINT} --model ${MODEL} --version ${JEV_VERSION} --api-key-env API_KEY --out <private>"
# Child process only. Do not exec: this script still has to write the dashboard results file.
if [ "${#LIMIT_ARGS[@]}" -gt 0 ]; then
    "$PUBLIC_RUN" \
        --endpoint "$ENDPOINT" \
        --model "$MODEL" \
        --version "$JEV_VERSION" \
        --api-key-env API_KEY \
        --out "$TOPICS_OUT" \
        "${LIMIT_ARGS[@]}"
else
    "$PUBLIC_RUN" \
        --endpoint "$ENDPOINT" \
        --model "$MODEL" \
        --version "$JEV_VERSION" \
        --api-key-env API_KEY \
        --out "$TOPICS_OUT"
fi
HARNESS_RC=$?
log_info "jevbench-public/run.sh exit ${HARNESS_RC}"
if [ "$HARNESS_RC" -ne 0 ]; then
    exit "$HARNESS_RC"
fi

log_step "Writing results"
python3 - "$RESULTS_FILE" "$TOPICS_OUT/topic-report.json" <<'PY'
import json, os, sys
results_path, report_path = sys.argv[1:]
report = json.load(open(report_path, encoding="utf-8"))
whole = report["official_public_summary"]
prov = report["provenance"]
planned = whole["n_planned"]
attempted = whole["n_attempted"]
correct = whole["n_correct"]
accuracy = whole["accuracy"]
complete = attempted == planned and planned > 0 and accuracy is not None
observed = None if accuracy is None else accuracy * 100.0
main_value = observed if complete else 0.0
secondary = {
    "n_planned": planned,
    "n_attempted": attempted,
    "n_unattempted": planned - attempted,
    "n_correct": correct,
    "n_scorable": whole.get("n_scorable"),
    "complete": 1 if complete else 0,
}
if accuracy is not None:
    secondary["accuracy"] = accuracy
    secondary["observed_accuracy_pct"] = observed
doc = {"metrics": {
    "main": {"name": "Public Accuracy", "value": main_value},
    "secondary": secondary,
    "additional": {
        "status": "complete" if complete else "partial",
        "protocol": prov.get("requested_version"),
        "release_family": prov.get("release_family"),
        "public_tiers": prov.get("public_tiers"),
        "scope": prov.get("scope"),
        "model": prov.get("requested_model"),
        "endpoint": prov.get("endpoint"),
        "by_topic": report.get("by_topic"),
        "methodology": (
            "Scored by jevbench-public/run_jevbench_topics.py on the public cases "
            "for the requested release. This is not an official ranked JevBench Score."
        ),
    },
}}
tmp = results_path + ".tmp"
with open(tmp, "w", encoding="utf-8") as fh:
    json.dump(doc, fh, indent=2)
    fh.write("\n")
os.replace(tmp, results_path)
print(f"[run][OK]    Public Accuracy={main_value} correct={correct} attempted={attempted}/{planned}", flush=True)
PY
trap - EXIT
log_ok "results at $RESULTS_FILE"
exit 0
