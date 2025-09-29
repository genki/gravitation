#!/usr/bin/env bash
if [[ ${BASH_SOURCE[0]} != "$0" ]]; then
  echo "Do not source; run ./scripts/benches/run_benches_bg.sh" >&2
  return 1 2>/dev/null || exit 1
fi
set -euo pipefail

ROOT=$(git -C "$(dirname "$0")/../.." rev-parse --show-toplevel 2>/dev/null || pwd)
cd "$ROOT"

PY=./.venv/bin/python
LOGDIR=logs/benches
PIDDIR=data/pids
mkdir -p "$LOGDIR" "$PIDDIR" server/public/notifications

start_one() {
  local name=$1; shift
  local script=$1; shift
  local log="$LOGDIR/${name}.log"
  echo "[start] $name -> $log"
  nohup bash -lc "PYTHONPATH=. $PY $script >> '$log' 2>&1" &
  echo $! > "$PIDDIR/${name}.pid"
}

start_one bench_ngc3198 scripts/benchmarks/run_ngc3198_fullbench.py
start_one bench_ngc2403 scripts/benchmarks/run_ngc2403_fullbench.py

echo "PIDs:"
for n in bench_ngc3198 bench_ngc2403; do
  echo "  $n: $(cat "$PIDDIR/$n.pid")"
done
echo "logs in: $LOGDIR"

exit 0
