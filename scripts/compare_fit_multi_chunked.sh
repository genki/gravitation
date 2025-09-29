#!/usr/bin/env bash
if [[ ${BASH_SOURCE[0]} != "$0" ]]; then
  echo "Do not source; run ./scripts/compare_fit_multi_chunked.sh" >&2
  return 1 2>/dev/null || exit 1
fi
set -euo pipefail

# Wrapper for scripts/compare_fit_multi.py that enforces chunked execution.
# Each invocation of the Python script is capped by MAX_MINUTES (default 55).
# The wrapper loops until the progress file reports completion.

PY_CMD=${PY:-.venv/bin/python}
SCRIPT_PATH=${SCRIPT_PATH:-scripts/compare_fit_multi.py}
MAX_MINUTES=${MAX_MINUTES:-55}
CHUNK_SIZE=${CHUNK_SIZE:-0}
RESET_PROGRESS=${RESET_PROGRESS:-0}

ARGS=()
while (($#)); do
  ARGS+=("$1")
  shift
done

# Determine output path (--out) to derive progress file name.
OUT_PATH=""
for ((i=0; i<${#ARGS[@]}; i++)); do
  if [[ "${ARGS[$i]}" == "--out" ]] && (( i + 1 < ${#ARGS[@]} )); then
    OUT_PATH="${ARGS[$((i+1))]}"
  fi
done
if [[ -z "${OUT_PATH}" ]]; then
  OUT_PATH="data/results/multi_fit.json"
fi

PROGRESS_PATH="${OUT_PATH}.progress.json"

first_run=1
while true; do
  extra=()
  if [[ "${CHUNK_SIZE}" != "0" ]]; then
    extra+=("--chunk-size" "${CHUNK_SIZE}")
  fi
  if [[ "${MAX_MINUTES}" != "0" ]]; then
    extra+=("--max-minutes" "${MAX_MINUTES}")
  fi
  if (( first_run )) && [[ "${RESET_PROGRESS}" == "1" ]]; then
    extra+=("--reset-progress")
  fi

  PYTHONPATH=. "${PY_CMD}" "${SCRIPT_PATH}" "${ARGS[@]}" "${extra[@]}"
  status=$?
  if [[ ${status} -ne 0 ]]; then
    exit ${status}
  fi

  complete_flag="1"
  if [[ -f "${PROGRESS_PATH}" ]]; then
    complete_flag=$(python - <<'PY'
import json, sys
from pathlib import Path

path = Path(sys.argv[1])
try:
    data = json.loads(path.read_text(encoding='utf-8'))
except Exception:
    print('1')
    raise SystemExit(0)
print('1' if data.get('complete') else '0')
PY
"${PROGRESS_PATH}" 2>/dev/null || echo "1")
  fi

  if [[ "${complete_flag}" == "1" ]]; then
    break
  fi
  echo "[chunk] Saved progress -> continuing next chunk"
  first_run=0
done

echo "[chunk] compare_fit_multi completed"
