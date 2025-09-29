#!/usr/bin/env bash
if [[ ${BASH_SOURCE[0]} != "$0" ]]; then
  echo "Do not source; run $0" >&2
  return 1 2>/dev/null || exit 1
fi
set -euo pipefail

usage(){
  echo "Usage: $0 -n NAME | -f META.json" >&2
}

NAME=""; META=""
while getopts n:f:h opt; do
  case "$opt" in
    n) NAME="$OPTARG" ;;
    f) META="$OPTARG" ;;
    h) usage; exit 0 ;;
    *) usage; exit 2 ;;
  esac
done

REPO_ROOT=$(cd "$(dirname "$0")/../.." && pwd)
JOBS_DIR="$REPO_ROOT/tmp/jobs"

if [ -z "$META" ]; then
  [ -n "$NAME" ] || { usage; exit 2; }
  META=$(ls -t "$JOBS_DIR/${NAME}_"*.json 2>/dev/null | head -n1 || true)
  [ -n "$META" ] || { echo "No metadata for $NAME" >&2; exit 1; }
fi

PID=$(jq -r '.pid // empty' "$META" 2>/dev/null || true)
PGID=$(jq -r '.pgid // empty' "$META" 2>/dev/null || true)
NAME_F=$(jq -r '.name // empty' "$META" 2>/dev/null || true)

if [ -n "$PGID" ]; then
  echo "[jobs] sending SIGTERM to process group $PGID ($NAME_F)" >&2
  kill -- -"$PGID" 2>/dev/null || true
  sleep 1
  if ps -o pgid= -p "$PID" 2>/dev/null | grep -q "$PGID"; then
    echo "[jobs] still running; sending SIGKILL to group $PGID" >&2
    kill -9 -- -"$PGID" 2>/dev/null || true
  fi
elif [ -n "$PID" ]; then
  echo "[jobs] sending SIGTERM to $PID ($NAME_F)" >&2
  kill "$PID" 2>/dev/null || true
  sleep 1
  if kill -0 "$PID" 2>/dev/null; then
    echo "[jobs] still running; sending SIGKILL to $PID" >&2
    kill -9 "$PID" 2>/dev/null || true
  fi
else
  echo "[jobs] no pid in $META" >&2
fi

echo "[jobs] cancelled: $NAME_F ($META)"
