# run_2025-09-25_mond_curve_fix

## 結果サマリ
- 代表比較図で MOND 曲線が発散していた原因は、`scripts/benchmarks/plot_rep_fig.py` の単位換算が m→km 方向で逆に設定され、`a0` が ≈3.7×10³ ではなく ≈3.7×10¹⁵ (km² s⁻²/kpc) と誤計算されていたため。`M_PER_KM=10^3` を用いた適正換算に修正。
- MOND アダプタ (`src/models/adapter.py`) の既定 `a0` も SI 単位のまま流れていたため、10⁻¹⁰ 未満なら自動的に (km² s⁻²)/kpc へ変換するロジックを追加。SOTA 集計器 (`scripts/build_state_of_the_art.py`) も同じ換算関数 `_a0_si_to_kpc` を通し、MOND の AICc が正しいスケールで集計されるよう統一。
- `plot_rep_fig.py` で NGC3198/NGC2403 の比較図を再生成 (`--no-run-fdb`) し、`make sota-refresh` を実行。MOND 曲線は他モデルと同じオーダーに収まり、SOTA 代表比較図に反映されたことを確認。

## 生成物
- 更新: `scripts/benchmarks/plot_rep_fig.py`, `src/models/adapter.py`, `scripts/build_state_of_the_art.py`
- 再生成: `server/public/reports/figs/rep_ngc3198.png`, `server/public/reports/figs/rep_ngc2403.png`
- 再生成: `server/public/state_of_the_art/index.html`

## 次アクション
1. MOND 曲線の再生成が必要な他銀河（Worst/Median など tri_compare SVG）の差し替え手順を整備する（必要なら自動化スクリプト化）。
2. `scripts/build_state_of_the_art.py` の MOND 集計で最適化された a0 値（≃3.7×10³）をページ脚注に明記し、比較条件が読者に伝わるよう整理する。
3. ベクタ図版（tri_compare SVG）の MOND ラベルも同じ単位表記に統一し、今後の出力で齟齬が出ないか確認する。
