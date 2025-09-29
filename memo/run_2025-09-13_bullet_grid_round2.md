## Bullet 全球PASS — 制約付き探索（Round‑2） — 2025-09-13

## 結果サマリ
- 学習候補(α,β,C,ξ,p,τ_q)を列挙し、各候補について Bullet で **ΔAICc(FDB−shift) ≤ −10** を満たすことを必須制約に採用。
- 制約を満たす集合から **全球Spearman(R,Σ_e)** を最小化する候補を選抜。
- 選抜結果: α=1.0, β=0.5, C=0.1, ξ=0.2, p=0.7, τ_q=0.7（sha付）に更新。
- 検証（Permutation n=4096）: KPI‑2は引き続きPASS、ただし **全球Spearman=+0.284 (>0)** でKPI‑1は未達。

## 生成物
- スクリプト: `scripts/cluster/fit/holdout_constrained_search.py`（制約付き探索）, `scripts/reports/make_bullet_holdout.py`（FAST/Permutationスキップ対応）
- パラ: `data/cluster/params_cluster.json`（α=1.0, β=0.5, C=0.1, ξ=0.2, p=0.7, τ_q=0.7, sha）
- レポート/JSON: `server/public/reports/bullet_holdout.html`, `.../bullet_holdout.json`

## 次アクション
- さらなる負相関化の指針:
  1) ξとpの上限側を拡張（例: ξ≤0.5, p∈{0.7,1.0}）。
  2) τ_q の上げ下げで界面を鋭化/緩和（0.5–0.85）。
  3) 必要に応じ β を微調整（0.3–0.8）。
- 実行例（計算量中）:
  `GRID_XI=0.1,0.2,0.3,0.4,0.5 GRID_P=0.7,1.0 GRID_TAUQ=0.5,0.6,0.7,0.8,0.85 GRID_ALPHA=0.6,1.0,1.5 GRID_BETA=0.3,0.5,0.7 \`
  `PYTHONPATH=. ./.venv/bin/python scripts/cluster/fit/holdout_constrained_search.py && BULLET_PERM_N=8192 PYTHONPATH=. ./.venv/bin/python scripts/reports/make_bullet_holdout.py`

