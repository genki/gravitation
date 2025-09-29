#!/usr/bin/env bash
if [[ ${BASH_SOURCE[0]} != "$0" ]]; then
  echo "Do not source; run ./scripts/notice_to_file.sh" >&2
  return 1 2>/dev/null || exit 1
fi
set -euo pipefail

usage(){ echo "usage: $0 -m MESSAGE -t TITLE [-S SUBTITLE]" >&2; exit 1; }

title="通知"; subtitle=""; message=""
while getopts m:t:S: opt; do
  case "$opt" in
    m) message="$OPTARG";;
    t) title="$OPTARG";;
    S) subtitle="$OPTARG";;
    *) usage;;
  esac
done
[ -n "$message" ] || usage

outd="server/public/notifications"
mkdir -p "$outd"
ts="$(date -u '+%Y-%m-%d %H:%M UTC')"
printf '{"ts":"%s","title":%s,"subtitle":%s,"message":%s}\n' \
  "$ts" \
  "$(jq -Rn --arg x "$title" '$x')" \
  "$(jq -Rn --arg x "$subtitle" '$x')" \
  "$(jq -Rn --arg x "$message" '$x')" >> "$outd/log.ndjson"

# Rebuild simple HTML
{
  echo "<!doctype html><html lang=\"ja-JP\"><head><meta charset=\"utf-8\"><meta name=\"viewport\" content=\"width=device-width,initial-scale=1\"><title>Notifications</title><link rel=\"stylesheet\" href=\"../styles.css\"></head><body>"
  echo "<header class=\"site-header\"><div class=\"wrap\"><div class=\"brand\">通知</div><nav class=\"nav\"><a href=\"../index.html\">ホーム</a></nav></div></header>"
  echo "<main class=\"wrap\"><h1>Notifications (file sink)</h1><div class=\"card\">通知はネットワーク未到達時にファイルへミラーされています。</div>"
  echo "<ul>"
  # Avoid SIGPIPE under pipefail: select last 50 then reverse for newest-first
  tail -n 50 "$outd/log.ndjson" | tac | while IFS= read -r line; do
    ts=$(jq -r '.ts' <<<"$line");
    ti=$(jq -r '.title' <<<"$line");
    st=$(jq -r '.subtitle' <<<"$line");
    ms=$(jq -r '.message' <<<"$line" | sed 's/\n/<br>/g');
    echo "<li><b>[$ts] $ti</b><br><em>$st</em><div style=\"white-space:normal\">$ms</div></li>"
  done
  echo "</ul></main><footer class=\"site-footer\"><div class=\"wrap\">ローカル配信</div></footer></body></html>"
} > "$outd/index.html"

echo "wrote file notification -> $outd/index.html"
