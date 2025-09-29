## Bullet 全球PASS — 制約付き探索（Round‑3） — 2025-09-13

## 結果サマリ
- Round‑3 では探索空間を絞り（72候補）、ΔAICc(FDB−shift) ≤ −10 を満たすものから全球Spearman最小を選抜。
- 選抜結果: α=0.6, β=0.7, C=0.05, ξ=0.5, p=1.0, τ_q=0.6 に更新（sha付）。
- Bullet（Permutation n=8192）での検証: KPI‑2は引き続きPASS、全球Spearman=+0.287（p≪0.05）でKPI‑1は未達。

## 生成物
- 共有パラ: `data/cluster/params_cluster.json`（α=0.6, β=0.7, C=0.05, ξ=0.5, p=1.0, τ_q=0.6, sha）
- レポート/JSON: `server/public/reports/bullet_holdout.html`, `.../bullet_holdout.json`（n=8192）

## 次アクション
- さらなる負相関を狙い、ROI依存性低減のための `FAST_HOLDOUT` 併用スイープを継続（ξ上限0.6, p=1.0固定で τ_q を0.5–0.85 探索）。
- 並行してブロックBootstrap CI と partial r 図版の追加実装（検定の安定化）。

