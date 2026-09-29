#!/usr/bin/env bash
# setup.sh — provisioning for JevBench on the xyne-eval-ops-dashboard.
# Runs as root inside the Debian eval-runner container. No args. cwd = repo root.
# Non-agentic API eval (Runbook A): no Docker, no Artifact Registry, no harness patch.

if [ -z "${STDBUF_APPLIED:-}" ] && command -v stdbuf >/dev/null 2>&1; then
    export STDBUF_APPLIED=1
    # bash setup.sh leaves $0 as a relative name, which stdbuf cannot exec.
    exec stdbuf -oL -eL bash "${BASH_SOURCE[0]}" "$@"
fi

set -u
export DEBIAN_FRONTEND=noninteractive
export TZ=Etc/UTC

log()  { echo "[setup] $*"; }
warn() { echo "[setup] WARNING: $*" >&2; }
die()  { echo "[setup] FATAL: $*" >&2; exit 1; }

SUDO=""
if [ "$(id -u)" -ne 0 ] && command -v sudo >/dev/null 2>&1; then SUDO="sudo"; fi

apt_get() { $SUDO apt-get "$@" -y -qq || warn "apt-get $* failed (continuing)"; }

if command -v apt-get >/dev/null 2>&1; then
    apt_get update
    apt_get install ca-certificates curl git jq python3
fi

log "uid=$(id -u) sudo=$(command -v sudo || echo absent)"
log "python=$(command -v python3 || echo MISSING) $(python3 -V 2>/dev/null || true)"

python3 -c 'import sys; raise SystemExit(0 if sys.version_info >= (3, 9) else 1)' \
    || die "python >= 3.9 required (jevbench uses Path.is_relative_to)"
python3 -c 'import jevbench.cli, jevbench.runner, jevbench.summarize' \
    || die "jevbench import failed; cwd must be the repo root"

log "docker skipped (non-agentic; no per-task images)"
log "setup complete"
