# run_2025-09-24_rep_figure_fairness

## 結果サマリ
- 代表比較図を公平化するためのスクリプト `scripts/benchmarks/plot_rep_fig.py` を新規作成。観測半径 R_i に限定したプロット、±σ帯、残差段、共通線幅・凡例、GR+DM の c–M 事前オン/オフ線、k/N/AICc/rχ² 注記を含む 2段構成の図を生成。
- NGC3198 / NGC2403 の図を `server/public/reports/figs/rep_*.png` として再生成。PSF σ の共通適用（既定 0）をコード化し、Matplotlib の日本語フォントに Noto Sans を適用。
- SOTA (`scripts/build_state_of_the_art.py`) を更新し、存在すれば新しい `rep_*.png` を優先的に読み込み。fallback として従来の tri_compare SVG を保持し、Worst/Median でも同様に PNG を優先するロジックを追加。
- `make sota-refresh` でトップページを再構築し、代表比較図セクションに NGC3198/NGC2403 の新図が表示されることを確認。

## 生成物
- `scripts/benchmarks/plot_rep_fig.py`
- `server/public/reports/figs/rep_ngc3198.png`
- `server/public/reports/figs/rep_ngc2403.png`
- 更新: `scripts/build_state_of_the_art.py`
- 更新: `server/public/state_of_the_art/index.html`

## 次アクション
1. GR/GR+DM/MOND/FDB の rχ²/AICc が図中値とベンチ表で一致するか再確認し、乖離があれば数値算出部を調整する。
2. 他の代表銀河（ESO079-G014 など）についても `plot_rep_fig.py` を実行し、新仕様へ順次移行する。
3. フォント環境の違いを吸収するため、TeX 数式で使用した文字がすべて描画されるか追加確認する。
