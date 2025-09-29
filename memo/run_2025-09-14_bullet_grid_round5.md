## Bullet 全球PASS — 制約付き探索（Round‑5, 狭域） — 2025-09-14

## 結果サマリ
- 狭域グリッド（36候補）で制約付き探索（ΔAICc(FDB−shift) ≤ −10 を必須）を実施。
- 選抜パラ: α=0.8, β=0.7, C=0.05, ξ=0.7, p=1.0, τ_q=0.5（sha付）。
- 検証（Permutation n=8192, Block Bootstrap n=2048）:
  - ΔAICcは引き続き強い負差で PASS（shift 対照に対し ≪ −10）。
  - 全球 Spearman(R,Σ_e)=+0.287（p≪0.05）で未達。partial r(global)≈+0.074。Bootstrap 95% CI ≈ [0.167, 0.402]。

## 生成物
- パラ更新: `data/cluster/params_cluster.json`
- レポート/JSON: `server/public/reports/bullet_holdout.html`, `.../bullet_holdout.json`
- ページ強化（前回実装）: AICc+(N,k)+χ²/rχ² 表、κ_tot 可視化、Permutation/Bootstrap 情報の併記

## 次アクション
- 指示Aに沿い、目的関数へ高Σ_e層の −Spearman を微混合（5–10%）した学習を導入（ΔAICc制約は維持）。
- Σ_e 分位正規化（クラスタ間スケール差の干渉低減）の導入可否を検討。
- 検定の頑健化を継続（Permutation≥8192、Bootstrap≥4096）。

