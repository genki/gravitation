#!/usr/bin/env bash
if [[ ${BASH_SOURCE[0]} != "$0" ]]; then
  echo "Do not source; run ./scripts/serve_site.sh" >&2
  return 1 2>/dev/null || exit 1
fi
set -euo pipefail

# ローカルサーバーで ./site を配信する簡易サーバー
# 使い方: bash scripts/serve_site.sh [port]

PORT=${1:-8000}
ROOT=site

if [[ ! -d "$ROOT" ]]; then
  echo "site/ が見つかりません。先に 'mkdocs build' してください" >&2
  exit 1
fi

echo "Serving $ROOT at http://127.0.0.1:$PORT/"
cd "$ROOT"
python3 -m http.server "$PORT"
