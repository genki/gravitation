#!/usr/bin/env bash
# Guard to avoid leaking strict mode when sourced accidentally
if [[ ${BASH_SOURCE[0]} != "$0" ]]; then
  echo "Do not source; run ./scripts/start_web.sh" >&2
  return 1 2>/dev/null || exit 1
fi
set -euo pipefail

# HTTP/HTTPS 開発サーバーの起動ヘルパー（常駐・ヘルスチェック付き）

ROOT_DIR=$(cd "$(dirname "$0")/.." && pwd)
LOG="$ROOT_DIR/server/web.log"
PIDF="$ROOT_DIR/server/web.pid"

export HOST="${HOST:-0.0.0.0}"
export PORT="${PORT:-3131}"
export USE_TLS="${USE_TLS:-1}"

# 既存停止
if [[ -f "$PIDF" ]] && ps -p "$(cat "$PIDF" 2>/dev/null || echo)" >/dev/null 2>&1; then
  kill "$(cat "$PIDF")" || true
  sleep 1
fi

# 証明書の用意は TLS 利用時のみ
if [[ "$USE_TLS" != "0" ]]; then
  if [[ ! -f $ROOT_DIR/server/certs/dev.crt || ! -f $ROOT_DIR/server/certs/dev.key ]]; then
    echo "[start_web] 自己署名証明書を生成します..."
    bash "$ROOT_DIR/scripts/gen_dev_cert.sh"
  fi
fi

if [[ "$USE_TLS" == "0" ]]; then
  echo "[start_web] サーバー起動(HTTP): http://localhost:${PORT}"
  NO_TLS=1 nohup python3 "$ROOT_DIR/server/server.py" >"$LOG" 2>&1 & echo $! >"$PIDF"
else
  echo "[start_web] サーバー起動(HTTPS): https://localhost:${PORT}"
  nohup python3 "$ROOT_DIR/server/server.py" >"$LOG" 2>&1 & echo $! >"$PIDF"
fi
sleep 1

# ヘルスチェック（最大5秒）
for i in {1..10}; do
  if curl -sk "https://localhost:${PORT}/healthz" >/dev/null 2>&1 || curl -s "http://localhost:${PORT}/healthz" >/dev/null 2>&1; then
    echo "[start_web] 起動OK (pid $(cat "$PIDF"))"
    exit 0
  fi
  sleep 0.5
done

echo "[start_web] 起動に失敗しました。直近のログ:"
tail -n 80 "$LOG" || true
exit 1
