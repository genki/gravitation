## Bullet 全球PASS — 重み強化(W_CORR/W_ROI)＋τ_q狭域（Round‑8） — 2025-09-14

## 結果サマリ
- 目的関数の相関重みを強化（W_CORR=0.15, W_ROI=0.10）し、τ_q∈[0.40,0.55], β=0.8, ξ∈[0.6,0.8] に絞って制約付き探索。
- 選抜: α=0.6, β=0.8, C=0.05, ξ=0.6, p=1.0, τ_q=0.55（sigma_norm_q=0.9）。
- 検証（Permutation n=4096, Bootstrap n=4096）: KPI‑B維持。全球Spearman≈+0.286、top‑10%≈+0.095、partial r(global)≈+0.074 → なお正側。

## 生成物
- パラ/レポート更新: `data/cluster/params_cluster.json`, `server/public/reports/bullet_holdout.html` / `.json`

## 次アクション
- 更にモデル側の構造（Sの角度核や界面幅の正則化、PSF/高通過の同時最適化）を検討しつつ、ΔAICc制約維持での負相関追求を継続。

