#!/usr/bin/env bash
if [[ ${BASH_SOURCE[0]} != "$0" ]]; then
  echo "Do not source; run ./scripts/jobs/run_holdout_async.sh" >&2
  return 1 2>/dev/null || exit 1
fi
set -euo pipefail

if [ $# -lt 1 ]; then
  echo "Usage: $0 HOLDOUT [TRAIN_CLUSTERS]" >&2
  echo "  HOLDOUT: e.g. MACSJ0416 or AbellS1063" >&2
  echo "  TRAIN_CLUSTERS (optional, default Abell1689,CL0024)" >&2
  exit 2
fi

HOLDOUT="$1"
TRAIN="${2:-Abell1689,CL0024}"
REPO_ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
cd "$REPO_ROOT"

LOG_DIR="server/public/reports/logs"
PROGRESS_DIR="server/public/reports/cluster"
JOBS_DIR="tmp/jobs"
mkdir -p "$LOG_DIR" "$PROGRESS_DIR" "$JOBS_DIR"

TS="$(date +%Y%m%d_%H%M%S)"
LOG_FILE="$LOG_DIR/holdout_${HOLDOUT}_${TS}.log"
PROGRESS_LOG="$PROGRESS_DIR/${HOLDOUT}_progress.log"
META_FILE="$JOBS_DIR/holdout_${HOLDOUT}.json"

# Check existing job metadata
if [ -f "$META_FILE" ]; then
  OLD_PID=$(META_PATH="$META_FILE" python - <<'PY'
import json, os
from pathlib import Path
path = Path(os.environ['META_PATH'])
try:
    data = json.loads(path.read_text())
    pid = int(data.get('pid', 0))
except Exception:
    pid = 0
if pid > 0:
    try:
        os.kill(pid, 0)
    except OSError:
        pid = 0
print(pid)
PY
  )
  if [ -n "$OLD_PID" ] && [ "$OLD_PID" -gt 0 ]; then
    echo "Existing holdout job for $HOLDOUT appears to be running (pid=$OLD_PID)." >&2
    echo "Stop it or remove $META_FILE before starting a new one." >&2
    exit 1
  fi
fi

# NOTE: route via dispatcher for isolation (cgroup scope) and unified metadata
CMD_STR="./scripts/reports/make_bullet_holdout.py --train $TRAIN --holdout $HOLDOUT"
"$REPO_ROOT/scripts/jobs/dispatch_bg.sh" -n "holdout_${HOLDOUT}" --cwd "$REPO_ROOT" --meta "$META_FILE" --scope -- "$CMD_STR"
