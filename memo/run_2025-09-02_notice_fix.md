# 通知未達の調査と対処

- 実行日: 2025-09-02
- 症状: `make notify(-done)` 実行で"通知を送信しました(非同期)"が出るが、受信側に出ない。
- 原因推定:
  - scripts/notice.sh の既定転送先は agent-gate 経由で `@localhost:8082/notice` (talker/notice)だが、この環境に8082の受信サービスがない。
  - 非同期送信のためHTTPの成否を保持せず、失敗に気づきにくい。
- 対処:
  1) ファイルシンクの追加: `scripts/notice_to_file.sh` を導入し、常に `server/public/notifications/` にミラー保存。
  2) Makefileを更新し、`notify`/`notify-done`で`notice.sh`失敗時にもファイルシンクへフォールバック、成功時も常にミラーしてローカル可視化。
  3) `notify-test` は従来通り（直接/同期）で疎通確認可。
- 確認: `/notifications/` ページに最新が表示される。
- 次アクション: 実運用先(例: Slack)のWebhook設定時は二重配信だが、意図通りの冗長化。必要に応じてミラー抑制フラグを導入。
