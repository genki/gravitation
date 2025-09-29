## Bullet 全球PASS — 重み増強＋τ_q 0.40–0.55 集中（Round‑9） — 2025-09-14

## 結果サマリ
- 相関重みを更に増強（W_CORR=0.18, W_ROI=0.12）し、τ_q を 0.40–0.55 に集中。β=0.8 固定、ξ=0.6–0.8。
- 選抜: α=0.6, β=0.8, C=0.05, ξ=0.6, p=1.0, τ_q=0.40（sigma_norm_q=0.9）。
- 検証（Permutation n=4096, Bootstrap n=4096）: KPI‑B 維持。全球 Spearman ≈ +0.286、top‑10% ≈ +0.095、partial r(global) ≈ +0.074 → 依然正側。

## 生成物
- パラ/レポート: `data/cluster/params_cluster.json`, `server/public/reports/bullet_holdout.html` / `.json`

## 所感と次アクション
- 目的関数の相関重みを引き上げても、ΔAICc 制約の下では全球符号は正に残存。モデル側の核（角度項/界面幅）の正則化や、κ_tot（GR+FDB）整合ベースの追加評価を並走することを提案。

