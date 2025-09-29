#!/usr/bin/env bash
# Guard: prevent accidental 'source' which would leak strict-mode to parent shell
if [[ ${BASH_SOURCE[0]} != "$0" ]]; then
  echo "Do not source this file; execute it (./scripts/notice.sh)." >&2
  return 1 2>/dev/null || exit 1
fi
# talker/notice を使って通知を送信するスクリプト
# -S でサブタイトルを指定可能
# -a でアクションボタンをカンマ区切りで指定できる
# -F で画像などのファイルを添付できる
# 環境変数 SLACK_WEBHOOK_URL があれば Slack にも同じ内容を投稿
# アクション指定時はデタッチせず通知完了まで待機する

set -euo pipefail
[ "${NOTICE_DEBUG_SLACK:-0}" = "1" ] && set -x || true

usage() {
  echo "使い方: $0 -m メッセージ [-t タイトル] [-S サブタイトル] \" >&2
  echo "  [-s サウンド] [-T 秒数] [-a action1,action2,...] [-f from] \" >&2
  echo "  [-F ファイル]" >&2
  echo "サウンドを省略すると Tink が使用されます" >&2
  echo "-T で通知表示時間を秒単位で指定します (既定値: 300)" >&2
  echo "-a でアクションボタンをカンマ区切りで指定します" >&2
  echo "  サブタイトル未指定時は '返答を選択してください' を自動設定" >&2
  exit 1
}

# 動作モード: agent-gate(既定) / direct(local)
direct_mode=${NOTICE_DIRECT:-0}
base_url_override=${NOTICE_BASE_URL:-}
sync_mode=${NOTICE_SYNC:-0}
# タイムアウト/スキップ制御（無指定時は短めの安全値）
connect_timeout=${NOTICE_CONNECT_TIMEOUT:-2}
max_time=${NOTICE_MAX_TIME:-6}

# 各種オプション初期値
title="通知"
sound="Tink"
timeout=300
message=""
actions=""
subtitle=""
file=""
repo_dir=$(git -C "$(dirname "$0")/.." \
  rev-parse --show-toplevel 2>/dev/null || echo '')
from=galaxy

# Fallback: mirror notification to local file sink
mirror_to_file() {
  if [ -n "$repo_dir" ] && [ -x "$repo_dir/scripts/notice_to_file.sh" ]; then
    "$repo_dir/scripts/notice_to_file.sh" -m "$message" -t "$title" ${subtitle:+-S "$subtitle"}
  else
    echo "[notice] file mirror skipped (missing scripts/notice_to_file.sh)" >&2
  fi
}

# オプション解析
while getopts m:t:S:s:T:a:f:F:du: opt; do
  case "$opt" in
    m) message="$OPTARG" ;;
    t) title="$OPTARG" ;;
    S) subtitle="$OPTARG" ;;
    s) sound="$OPTARG" ;;
    T) timeout="$OPTARG" ;;
    a) actions="$OPTARG" ;;
    f) from="$OPTARG" ;;
    F) file="$OPTARG" ;;
    d) direct_mode=1 ;;
    u) base_url_override="$OPTARG" ;;
    *) usage ;;
  esac
done

# アクション指定時にサブタイトルが無ければ既定文を設定
if [ -n "$actions" ] && [ -z "$subtitle" ]; then
  subtitle="返答を選択してください"
fi

[ -n "$message" ] || usage

# JST 時刻をタイトル先頭へ付与
prefix="$(TZ=Asia/Tokyo date '+%H:%M ')"
title="${prefix}${title}"

# jq を用いて JSON ペイロードを生成
json=$(jq -n \
  --arg title "$title" \
  --arg message "$message" \
  --arg subtitle "$subtitle" \
  --arg sound "$sound" \
  --arg timeout "$timeout" \
  --arg actions "$actions" \
  --arg file "$file" \
  --arg from "$from" \
  '
    {title:$title,message:$message,from:$from} +
    (if $subtitle != "" then {subtitle:$subtitle} else {} end) +
    (if $sound != "" then {sound:$sound} else {} end) +
    (if $timeout != "" then {timeout:($timeout|tonumber)} else {} end) +
    (if $actions != "" then {actions:($actions|split(","))} else {} end) +
    (if $file != "" then {file:$file} else {} end)
  ')

# 非デバッグ時はペイロードを表示しない（静粛運転）
[ -n "${NOTICE_DEBUG:-}" ] && echo "$json"

# Slack Webhook の後読み（未設定なら .env を読んで補完）
if [ -z "${SLACK_WEBHOOK_URL:-}" ] && [ -n "$repo_dir" ] && [ -f "$repo_dir/.env" ]; then
  set -a; . "$repo_dir/.env"; set +a || true
fi

# URLの決定
if [ -n "${NOTICE_SKIP_NET:-}" ]; then
  url=""  # ネット送信をスキップ
elif [ "$direct_mode" = "1" ]; then
  base="${base_url_override:-http://127.0.0.1:8082}"
  url="$base/notice"
else
  # AGENT_TOKEN は agent-gate 利用時のみ必須
  if [ -z "${AGENT_TOKEN:-}" ]; then
    echo "AGENT_TOKEN が未設定です (agent-gate 経由)。ネット送信をスキップし、ファイルミラー/Slackのみ試行します" >&2
    url=""  # ゲート送信は行わない
    mirror_to_file || true
  else
    base="https://agent-gate.s21g.com/moon/$AGENT_TOKEN"
    # 既定の転送先はローカル8082。必要に応じて NOTICE_TARGET を上書き可
    target="${NOTICE_TARGET:-@localhost:8082}"
    url="$base/$target/notice"
  fi
fi

send_async() { nohup "$@" >/dev/null 2>&1 & disown || true; }

ASYNC_MODE=0
[ -z "$actions" ] && [ "$sync_mode" != "1" ] && ASYNC_MODE=1

# 共通 curl オプション（短めのタイムアウトで素早くフォールバック）
curl_common=( -fsS --connect-timeout "$connect_timeout" --max-time "$max_time" )

if [ -n "$file" ]; then
  form_args=(
    -F "message=$message" -F "title=$title" -F "from=$from"
  )
  [ -n "$subtitle" ] && form_args+=( -F "subtitle=$subtitle" )
  [ -n "$sound" ] && form_args+=( -F "sound=$sound" )
  [ -n "$timeout" ] && form_args+=( -F "timeout=$timeout" )
  [ -n "$actions" ] && form_args+=( -F "actions=$actions" )
  form_args+=( -F "file=@$file" )

  if [ -n "$url" ]; then
    if [ "$ASYNC_MODE" = "1" ]; then
      send_async curl "${curl_common[@]}" -X POST "${form_args[@]}" "$url" || true
      echo "通知を送信しました (非同期)"
      mirror_to_file
    else
      if ! curl "${curl_common[@]}" -X POST "${form_args[@]}" "$url"; then
        echo "[notice] ネット送信に失敗しました（$url）。ファイルミラーへフォールバックします" >&2
        mirror_to_file
      fi
    fi
  else
    echo "[notice] NOTICE_SKIP_NET=1 のためネット送信をスキップしました" >&2
    mirror_to_file
  fi
else
  if [ -n "$url" ]; then
    if [ "$ASYNC_MODE" = "1" ]; then
      send_async curl "${curl_common[@]}" -X POST \
        -H 'Content-Type: application/json' -d "$json" "$url" || true
      echo "通知を送信しました (非同期)"
      mirror_to_file
    else
      if ! curl "${curl_common[@]}" -X POST \
        -H 'Content-Type: application/json' -d "$json" "$url"; then
        echo "[notice] ネット送信に失敗しました（$url）。ファイルミラーへフォールバックします" >&2
        mirror_to_file
      fi
    fi
  else
    echo "[notice] NOTICE_SKIP_NET=1 のためネット送信をスキップしました" >&2
    mirror_to_file
  fi
fi

# Slack設定状況を標準エラーに表示（可視化）
[ "${NOTICE_DEBUG_SLACK:-0}" = "1" ] && echo "[dbg] notice.sh: entering Slack section" >&2 || true
if [ -n "${SLACK_WEBHOOK_URL:-}" ]; then
  [ "${NOTICE_SLACK_VERBOSE:-1}" = "1" ] && echo "[notice] Slack: webhook is SET" >&2
  [ "${NOTICE_DEBUG_SLACK:-0}" = "1" ] && echo "[dbg] notice.sh: SLACK_WEBHOOK_URL detected" >&2 || true
else
  [ "${NOTICE_SLACK_VERBOSE:-1}" = "1" ] && echo "[notice] Slack: webhook is NOT set; skipping Slack post" >&2
  [ "${NOTICE_DEBUG_SLACK:-0}" = "1" ] && echo "[dbg] notice.sh: SLACK_WEBHOOK_URL missing" >&2 || true
fi

# Slack への通知は常に試行（Webhook設定時）。メイン送信成否に関わらず実行。
if [ -n "${SLACK_WEBHOOK_URL:-}" ]; then
  [ "${NOTICE_SLACK_VERBOSE:-1}" = "1" ] && echo "[notice] Slack: webhook configured; attempting post" >&2
  text="$title"
  [ -n "$subtitle" ] && text+=$'\n'"$subtitle"
  text+=$'\n'"$message"
  slack_payload=$(jq -n --arg text "$text" '{text:$text}')
  # ログ出力先（SOTA配下）
  logdir="server/public/reports/logs"; mkdir -p "$logdir" || true
  ts="$(date +%Y%m%d_%H%M%S)"
  slog="$logdir/notice_slack_${ts}.log"
  # NOTICE_SLACK_SYNC=1（既定）で同期送信し、結果をログへ記録
  if [ "${NOTICE_SLACK_SYNC:-1}" = "1" ]; then
    {
      echo "[payload]"; echo "$slack_payload"
      echo "[curl]";
      echo "$slack_payload" | curl -sS --connect-timeout "$connect_timeout" --max-time "$max_time" \
        -D - -o /tmp/slack_body_$$.txt \
        -X POST -H 'Content-Type: application/json' -d @- "$SLACK_WEBHOOK_URL"; rc=$?; echo "RC=$rc";
      echo "[body]"; cat /tmp/slack_body_$$.txt 2>/dev/null; rm -f /tmp/slack_body_$$.txt 2>/dev/null || true
    } >"$slog" 2>&1 || true
    [ "${NOTICE_SLACK_VERBOSE:-1}" = "1" ] && echo "[notice] Slack: sync post finished, log=$slog" >&2
    [ "${NOTICE_SLACK_STDOUT:-0}" = "1" ] && echo "Slack: sync ok -> $slog"
    [ "${NOTICE_DEBUG_SLACK:-0}" = "1" ] && echo "[dbg] notice.sh: wrote Slack log $slog" >&2 || true
  else
    (
      echo "$slack_payload" | \
      curl -fsS --connect-timeout "$connect_timeout" --max-time "$max_time" \
        -X POST -H 'Content-Type: application/json' -d @- "$SLACK_WEBHOOK_URL" \
        >/dev/null 2>&1 || true
    ) &
    [ "${NOTICE_SLACK_VERBOSE:-1}" = "1" ] && echo "[notice] Slack: async post dispatched" >&2
    [ "${NOTICE_SLACK_STDOUT:-0}" = "1" ] && echo "Slack: async dispatched"
  fi
fi
