# メモ: 対照検証（Negative-control）の定量公開

目的: 回転/平行移動/等値面シャッフル対照を自動実行し、ΔAICc（control−original）
の中央値[IQR]・効果量d・試行数nを図表で公開。

受け入れ条件(DoD)
- `server/public/reports/controls_summary.{svg,png,html}` が生成・公開。
- 本文に2行の定義（偽データで幾何依存を検証…）が章頭に固定表示。

実行手順
1) `scripts/controls/run_all_controls.py`（n既定=200, seed固定）を追加。
2) `scripts/controls/summary_plot.py` でΔAICc分布と効果量を図化。
3) `make ctrl-tests`（新規）で全体を再生成しSOTAにリンク。

