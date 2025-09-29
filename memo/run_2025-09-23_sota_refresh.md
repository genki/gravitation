# run_2025-09-23_sota_refresh

## 結果サマリ
- `nohup make sota-refresh` をバックグラウンド（PID 560763, 約1分以内）で実行し、progress ダッシュボードと SOTA 一覧を再生成した。
- `server/public/state_of_the_art/index.html` と `server/public/reports/progress{,_card}.html` の更新時刻が 2025-09-24 00:27 JST を指すことを確認し、最新ホールドアウト指標が反映済みであることをチェックした。

## 生成物
- 更新: `server/public/state_of_the_art/index.html`
- 更新: `server/public/reports/progress.html`
- 更新: `server/public/reports/progress_card.html`
- ログ: `logs/sota_refresh_20250923.log`

## 確認事項
- ログにエラーは無く、`scripts/build_state_of_the_art.py` が正常終了。
- 既存のベンチ/ホールドアウトページは大規模リジェネにより一括更新待ちのため、差分管理に注意。

## 次アクション
1. 追加ホールドアウト（AbellS1063/MACSJ0416）の p 値改善後に、再度 `make sota-refresh` で SOTA KPI を更新する。
2. KPI バンドル再生成 (`make kpi-sprint`) のタイミングを Runbook に沿って調整する。
