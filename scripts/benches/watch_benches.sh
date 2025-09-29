#!/usr/bin/env bash
if [[ ${BASH_SOURCE[0]} != "$0" ]]; then
  echo "Do not source; run ./scripts/benches/watch_benches.sh" >&2
  return 1 2>/dev/null || exit 1
fi
set -euo pipefail
ROOT=$(git -C "$(dirname "$0")/../.." rev-parse --show-toplevel 2>/dev/null || pwd)
cd "$ROOT"
PIDDIR=data/pids
PY=./.venv/bin/python

is_alive(){ local pid=$1; kill -0 "$pid" 2>/dev/null; }

read_pid(){ [ -f "$PIDDIR/$1.pid" ] && cat "$PIDDIR/$1.pid" || echo 0; }

P1=$(read_pid bench_ngc3198)
P2=$(read_pid bench_ngc2403)
if [ "$P1" = "0" ] || [ "$P2" = "0" ]; then
  echo "[watch] missing PID files; start benches first (scripts/benches/run_benches_bg.sh)" >&2
  exit 1
fi

echo "[watch] waiting for benches to finish..."
while true; do
  a=0; b=0
  is_alive "$P1" || a=1
  is_alive "$P2" || b=1
  if [ "$a" = "1" ] && [ "$b" = "1" ]; then
    break
  fi
  sleep 30
done

echo "[watch] benches finished; rebuilding SOTA and sending notification"
PYTHONPATH=. $PY scripts/build_state_of_the_art.py || true
make notify-done-site || true
echo "[watch] done"
