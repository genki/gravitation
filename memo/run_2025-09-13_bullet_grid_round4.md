## Bullet 全球PASS — 制約付き探索（Round‑4） — 2025-09-13

## 結果サマリ
- 重点探索: ξを0.4–0.6, p=1.0, τ_q=0.5–0.7、α∈{0.6,0.8,1.0}、β∈{0.5,0.7}、C=0.05 の計90候補で制約付き探索。
- 制約（ΔAICc(FDB−shift) ≤ −10）を満たす全候補から全球Spearman最小を選抜。
- 選抜結果: **α=0.6, β=0.7, C=0.05, ξ=0.6, p=1.0, τ_q=0.5**（sha付）に更新。
- Bullet検証（Permutation n=8192）: KPI‑2は継続PASS、全球Spearman=+0.287（p≪0.05）でKPI‑1は未達。

## 生成物
- 共有パラ: `data/cluster/params_cluster.json`（α=0.6, β=0.7, C=0.05, ξ=0.6, p=1.0, τ_q=0.5, sha）
- レポート/JSON: `server/public/reports/bullet_holdout.html`, `.../bullet_holdout.json`（n=8192）

## 次アクション
- グローバル負相関をさらに押し下げるため、以下を提案：
  1) ROI/マスクの高Σ_e側重み（top‑q>0.9）を目的関数に微混合（公平条件の範囲で）
  2) Σ_e 正規化（分位スケーリング）でクラスタ間のスケール差の干渉を低減
  3) ブロックBootstrap CI と partial r 図版の追加（検定の頑健化）

