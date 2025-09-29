# 通知のタイムアウト短縮とフォールバック強化

- 実行時刻: 2025-09-02 05:50 UTC
- 目的: 通知未達時に処理が長時間ブロックされる問題の緩和と、明示ログの追加

## 結果サマリ
- `scripts/notice.sh` に短い `curl` タイムアウトとスキップ機能を追加
- ネット未到達時は速やかにファイルミラーへフォールバックしつつ警告出力
- 既存の `notify`/`notify-done` は挙動そのまま、体感応答性が向上

## 生成物
- 更新: `scripts/notice.sh`（`NOTICE_CONNECT_TIMEOUT`/`NOTICE_MAX_TIME`/`NOTICE_SKIP_NET`を追加）
- メモ: `memo/run_2025-09-02_notice_timeout_fallback.md`（本ファイル）

## 次アクション
- talker(@localhost:8082) の起動手順を整備し、手元でエンドツーエンド疎通確認（`memo/notice_talker_setup.md`）
- 必要に応じ `NOTICE_TARGET` を運用先に合わせて設定
