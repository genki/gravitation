#!/usr/bin/env bash
if [[ ${BASH_SOURCE[0]} != "$0" ]]; then
  echo "Do not source; run ./scripts/capture_env_logs.sh" >&2
  return 1 2>/dev/null || exit 1
fi
set -euo pipefail

ROOT_DIR=$(cd "$(dirname "$0")/.." && pwd)
OUT_DIR="$ROOT_DIR/server/public/reports"
mkdir -p "$OUT_DIR"

ts=$(date -u +%Y-%m-%dT%H:%M:%SZ)
log_txt="$OUT_DIR/env_logs.txt"
log_json="$OUT_DIR/env_logs.json"

ciao_v=""
lenstool_v=""

if command -v ciaover >/dev/null 2>&1; then
  ciao_v=$(ciaover 2>&1 || true)
else
  ciao_v="(ciaover not found)"
fi

if command -v lenstool >/dev/null 2>&1; then
  lenstool_v=$(lenstool -v 2>&1 || true)
else
  lenstool_v="(lenstool not found)"
fi

sha_params=""
if [ -f "$ROOT_DIR/data/cluster/params_cluster.json" ]; then
  sha_params=$(jq -r '.sha256 // empty' "$ROOT_DIR/data/cluster/params_cluster.json" || true)
fi

{
  echo "[#] env logs at $ts"
  echo
  echo "[ciaover]"; echo "$ciao_v"; echo
  echo "[lenstool -v]"; echo "$lenstool_v"; echo
  echo "[shared params sha]"; echo "${sha_params:-"(none)"}"
} >"$log_txt"

jq -n \
  --arg ts "$ts" \
  --arg ciao "$ciao_v" \
  --arg lens "$lenstool_v" \
  --arg sha "$sha_params" \
  '{timestamp:$ts, ciaover:$ciao, lenstool:$lens, shared_params_sha:($sha//"")}' \
  >"$log_json"

echo "wrote $log_txt and $log_json"
