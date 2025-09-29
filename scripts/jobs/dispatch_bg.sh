#!/usr/bin/env bash
if [[ ${BASH_SOURCE[0]} != "$0" ]]; then
  echo "Do not source; run $0" >&2
  return 1 2>/dev/null || exit 1
fi
set -euo pipefail

usage(){
  cat >&2 <<'USAGE'
Usage: scripts/jobs/dispatch_bg.sh -n NAME [--cwd DIR] [--env "K=V ..."] [--meta FILE] [--scope] -- CMD...

Runs CMD as an isolated background job:
 - starts a new session (setsid) to avoid parent signal propagation
 - logs to server/public/reports/logs/NAME_YYYYmmdd_HHMMSS.log
 - writes metadata to tmp/jobs/NAME_YYYYmmdd_HHMMSS.json
  - with --scope and systemd available, runs within a user scope (separate cgroup)

Options:
  -n NAME        Job name (identifier)
  --cwd DIR      Working directory (default: repo root)
  --env STR      Extra environment variables (e.g., "OMP_NUM_THREADS=1 ...")
  --meta FILE    Write metadata JSON to a specific path (default auto)
  --scope        Use systemd-run --user --scope for stronger isolation if available

Examples:
  scripts/jobs/dispatch_bg.sh -n rep6_ab_fast -- \
    "set -e; PYTHONPATH=. ./.venv/bin/python scripts/ab_comp/run_rep6_ws.py --fast && echo done"
USAGE
}

NAME=""
CWD=""
EXTRA_ENV=""
META_FILE_OVERRIDE=""
USE_SCOPE=0

while (( "$#" )); do
  case "${1}" in
    -n) NAME="$2"; shift 2;;
    --cwd) CWD="$2"; shift 2;;
    --env) EXTRA_ENV="$2"; shift 2;;
    --meta) META_FILE_OVERRIDE="$2"; shift 2;;
    --scope) USE_SCOPE=1; shift 1;;
    --) shift; break;;
    -h|--help) usage; exit 0;;
    *) echo "Unknown arg: $1" >&2; usage; exit 2;;
  esac
done

[ -n "$NAME" ] || { echo "-n NAME is required" >&2; exit 2; }

REPO_ROOT=$(cd "$(dirname "$0")/../.." && pwd)
[ -n "$CWD" ] || CWD="$REPO_ROOT"
LOG_DIR="$REPO_ROOT/server/public/reports/logs"
JOBS_DIR="$REPO_ROOT/tmp/jobs"
mkdir -p "$LOG_DIR" "$JOBS_DIR"

TS=$(date +%Y%m%d_%H%M%S)
LOG_FILE="$LOG_DIR/${NAME}_${TS}.log"
PID_FILE="$JOBS_DIR/${NAME}_${TS}.pid"
if [ -n "$META_FILE_OVERRIDE" ]; then
  META_FILE="$META_FILE_OVERRIDE"
else
  META_FILE="$JOBS_DIR/${NAME}_${TS}.json"
fi

CMD_STR="$*"
[ -n "$CMD_STR" ] || { echo "CMD is required after --" >&2; exit 2; }

# Start new session and background, optionally via systemd user scope
cd "$CWD"
UNIT_NAME="grav-${NAME}_${TS}.scope"
if [ "$USE_SCOPE" -eq 1 ] && command -v systemd-run >/dev/null 2>&1; then
  # Run inside a user scope to isolate from tmux/user session cgroups.
  # We still background the scope runner and capture the child PID via a pidfile.
  # shellcheck disable=SC2086
  nohup systemd-run --user --scope \
    --unit="$UNIT_NAME" \
    -p KillMode=process -p OOMPolicy=continue -p MemoryAccounting=yes \
    bash -lc "export GRAV_BG_JOB=1; ${EXTRA_ENV:+export ${EXTRA_ENV}; } nohup bash -lc '${CMD_STR//'/"'}' >>'$LOG_FILE' 2>&1 & echo \$! > '$PID_FILE'; wait" \
    >/dev/null 2>&1 &
  # Wait briefly for pidfile to appear
  for _i in $(seq 1 50); do
    [ -s "$PID_FILE" ] && break
    sleep 0.1
  done
  if [ -s "$PID_FILE" ]; then
    PID=$(cat "$PID_FILE" 2>/dev/null || echo 0)
  else
    # Fallback: we couldn't capture child pid; use the systemd-run shim pid (less ideal)
    PID=$!
  fi
else
  if command -v setsid >/dev/null 2>&1; then
    # shellcheck disable=SC2086
    nohup setsid bash -lc "export GRAV_BG_JOB=1; ${EXTRA_ENV:+export ${EXTRA_ENV}; }${CMD_STR}" >>"$LOG_FILE" 2>&1 &
  else
    # shellcheck disable=SC2086
    nohup bash -lc "export GRAV_BG_JOB=1; ${EXTRA_ENV:+export ${EXTRA_ENV}; }${CMD_STR}" >>"$LOG_FILE" 2>&1 &
  fi
  PID=$!
fi
sleep 0.05 || true
PGID=$(ps -o pgid= -p "$PID" 2>/dev/null | tr -d ' ' || echo "$PID")

# Write metadata
export PID PGID NAME LOG_FILE CWD CMD_STR META_FILE EXTRA_ENV UNIT_NAME
python3 - <<PY || true
import json, os, datetime, pathlib
meta = {
  "pid": int(os.environ["PID"]),
  "pgid": int(os.environ["PGID"]),
  "name": os.environ["NAME"],
  "started": datetime.datetime.now().isoformat(),
  "log_file": os.environ["LOG_FILE"],
  "workdir": os.environ["CWD"],
  "command": os.environ["CMD_STR"],
  "env": os.environ.get("EXTRA_ENV",""),
  "unit": os.environ.get("UNIT_NAME",""),
}
pathlib.Path(os.environ["META_FILE"]).write_text(json.dumps(meta, indent=2))
print("Wrote", os.environ["META_FILE"])
PY

cat <<INFO
Dispatched job: $NAME
  PID      : $PID (PGID $PGID)
  Log file : $LOG_FILE
  Meta     : $META_FILE
  Workdir  : $CWD
  Scope    : $( [ "$USE_SCOPE" -eq 1 ] && echo "$UNIT_NAME" || echo "(none)" )
INFO
