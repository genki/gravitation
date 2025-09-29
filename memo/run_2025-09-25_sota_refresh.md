# run_2025-09-25_sota_refresh

## 結果サマリ
- `make sota-refresh` を実行し、SOTA トップページと進捗ダッシュボードを再生成。`server/public/state_of_the_art/index.html` と `server/public/reports/progress_card.html` が最新状態になったことを確認。
- ビルドコマンドは `scripts/build_state_of_the_art.py`（PYTHONPATH=.）および `scripts/reports/make_progress_dashboard.py` が自動で走行。

## 生成物
- 更新: `server/public/state_of_the_art/index.html`
- 更新: `server/public/reports/progress_card.html`, `server/public/reports/progress.html`

## 次アクション
1. 公開サイト側に反映されたカード／代表図の内容をブラウザでスポットチェックし、統計の齟齬がないか確認。
