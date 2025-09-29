# run_2025-09-28 Slack通知実験（webhook同報の確認）

## 結果サマリ
- Slack Webhook を `.env` に設定し、通知スクリプト経由の同報を実験。
- 直接通知（make notify）と、BGジョブ完了検知（watcher）双方で Slack 同報が動作することを検証。

## 生成物
- BGジョブ: tmp/jobs/slack_test_*.json（メタ）、server/public/reports/logs/slack_test_*.log（ログ）

## 次アクション
- 本番通知（完了/サイト更新）や BG 完了通知は Slack にも同報されます。運用時は `.env` の Webhook を維持してください。
