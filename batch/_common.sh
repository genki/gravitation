#!/usr/bin/env bash
# Note: Do not enable strict-mode here to avoid leaking options into callers' shells
# when sourced in interactive contexts. Callers (batch scripts) enable strict-mode.

# Root of repo
REPO_ROOT=$(cd "$(dirname "$0")/.." && pwd)

# Ensure venv
if [[ ! -d "$REPO_ROOT/.venv" ]]; then
  echo "[common] Python venv .venv not found under $REPO_ROOT; please create it first." 1>&2
  echo "          e.g., python3 -m venv .venv && source .venv/bin/activate && pip install -U pip numpy scipy astropy matplotlib" 1>&2
  exit 2
fi

source "$REPO_ROOT/.venv/bin/activate"
export PYTHONPATH="$REPO_ROOT:${PYTHONPATH:-}"

# Logs dir
LOG_DIR="$REPO_ROOT/server/public/reports/logs"
mkdir -p "$LOG_DIR"
