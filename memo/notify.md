# 通知運用ガイド（再構築可能版）

最終更新: 2025-09-29

## 目的

タスク完了時に、ダッシュボード（talker/notice）および Slack へ同報するための
標準手順を、環境再構築できる粒度でまとめます。

## 前提

- `.env` に機密 `AGENT_TOKEN` を設定（必須）。Slack連携は `SLACK_WEBHOOK_URL` を追加（任意）。
- `.env.example` から複製: `cp gravitation/.env.example gravitation/.env`
- 置換: `sed -i 's/^AGENT_TOKEN=.*/AGENT_TOKEN=<提供トークン>/' gravitation/.env`

## コマンド

- 既定: `make notify`（簡易送信）
- 完了時: `make notify-done`（直近の `memo/run_*.md` を自動要約）
- サイト更新も同時: `make notify-done-site`

いずれも `.env` を自動読込し、`scripts/notice.sh` を介して送信します。

## 送信内容（自動抽出）

- タイトル: `作業完了: run_YYYY-MM-DD_*`
- 本文: 直近の `memo/run_*.md` から以下の見出しを抽出
  - `## 結果サマリ`
  - `## 生成物`
  - `## 次アクション`

`memo` に上記見出しを含めれば、通知本文が自動で充足します。

## スクリプト直叩き

最小例:

```sh
./scripts/notice.sh -m "ジョブ完了" -t "テスト更新"
```

Slack同期（同期応答待ち）:

```sh
NOTICE_SLACK_SYNC=1 ./scripts/notice.sh -m "再起動しますか" -t "メンテ" \
  -S "返答を選択してください" -a "OK,キャンセル"
```

## Slack設定

- `.env` に `SLACK_WEBHOOK_URL=https://hooks.slack.com/services/...` を設定
- 実行時ログは `server/public/reports/logs/notice_slack_*.log` に保存

## ダッシュボードへの反映

- すべての通知は `server/public/notifications/index.html` にミラー
- 受信先が落ちていてもダッシュボードで参照可能

## 運用ルール（要点）

- 各タスク終了時に1回送信（標準は `make notify-done-site`）
- 長時間ジョブはバックグラウンド実行＋進捗ログを残す
- `memo/run_*.md` に要点を必ず記録（通知の元データ）

