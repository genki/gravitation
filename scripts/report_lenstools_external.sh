#!/usr/bin/env bash
if [[ ${BASH_SOURCE[0]} != "$0" ]]; then
  echo "Do not source; run ./scripts/report_lenstools_external.sh" >&2
  return 1 2>/dev/null || exit 1
fi
set -euo pipefail

# Usage:
#   LENSTOOLS_VERSION=0.8.2 PY_VERSION=3.9.18 NUMPY_VERSION=1.21.6 PLATFORM="ubuntu20.04-conda" \
#   NOTES="built in podman container" ./scripts/report_lenstools_external.sh

ROOT_DIR=$(cd "$(dirname "$0")/.." && pwd)
OUT_DIR="$ROOT_DIR/server/public/reports/env"
mkdir -p "$OUT_DIR"

ts=$(date -u +%Y-%m-%dT%H:%M:%SZ)
jfile="$OUT_DIR/lenstools_info.json"

lenstools_ver="${LENSTOOLS_VERSION:-}"
py_ver="${PY_VERSION:-}"
np_ver="${NUMPY_VERSION:-}"
plat="${PLATFORM:-}"
notes="${NOTES:-}"

if [ -z "$lenstools_ver" ] || [ -z "$py_ver" ] || [ -z "$np_ver" ]; then
  echo "Please set LENSTOOLS_VERSION, PY_VERSION, NUMPY_VERSION (and optionally PLATFORM, NOTES)" >&2
  exit 2
fi

cat >"$jfile" <<JSON
{
  "timestamp": "$ts",
  "lenstools": "$lenstools_ver",
  "python": "$py_ver",
  "numpy": "$np_ver",
  "platform": "$plat",
  "notes": "$notes"
}
JSON

echo "wrote $jfile"

