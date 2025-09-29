# run_2025-09-25_mond_recheck

## 結果サマリ
- `scripts/benchmarks/plot_rep_fig.py` の MOND 計算を再確認し、a0 の単位換算が (km^2 s^-2)/kpc ≈ 3.70×10^3 で正しく設定されていることを数値検証（定数 `A0_KPC=3702.8`）で確認。
- 最新の `multi_fit_all_noBL.json` を用い、各銀河で MOND が生成する速度の最大値を走査したところ、最大でも ≈3.5×10^2 km/s に収まり、桁違いに発散するケースは再現せず。
- 代表比較図（`rep_ngc3198.png`, `rep_ngc2403.png`）を `PYTHONPATH=. python scripts/benchmarks/plot_rep_fig.py --no-run-fdb` で再生成後、`make sota-refresh` を実施。SOTA ページの MOND 曲線が他モデルと同オーダーで描画されることを確認。

## 実行ログ
- `PYTHONPATH=. python scripts/benchmarks/plot_rep_fig.py --name NGC3198 --name NGC2403 --no-run-fdb`
- `make sota-refresh`
- 検証スニペット: `data/results/multi_fit_all_noBL.json` を読み込み MOND 速度分布を走査（Pythonワンライナー）

## 次アクション
1. ユーザ報告と比較できる図版（問題再現時の旧PNGなど）が残っていないかログを照会し、必要なら before/after を差分保存する。
2. `plot_rep_fig.py` で GR+DM 側の `g_gas` 正規化（現在 base=1.0, GR=1.33）にズレがないか再検討し、必要ならパラメタ表記を明示。
3. Worst/Median 用 tri_compare SVG も順次 PNG 化し、MOND 表示の一貫性を高める。
