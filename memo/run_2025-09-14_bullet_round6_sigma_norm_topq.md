## Bullet 全球PASS — Top‑q相関混合 + Σ_e分位正規化（Round‑6） — 2025-09-14

## 結果サマリ
- 目的関数に **高Σ_e層(top‑q, 既定q=0.9)の −Spearman** を小比率（w_corr=0.1）で混合（ΔAICc制約は維持）。
- Σ_e を **q=0.9 分位で正規化**（W_eff へ入力前にスケール統一）。
- 制約付き探索を再実行（fast holdoutはtop‑10% Spearmanを採用）→ 最良: α=0.8, β=0.7, C=0.05, ξ=0.7, p=1.0, τ_q=0.6。
- 検証（Permutation n=4096, Block Bootstrap n=4096）: KPI‑B維持、全球Spearmanは依然正側（~+0.287）。

## 生成物
- コード: `scripts/cluster/min_kernel.py`（Σ_e分位正規化）, `scripts/cluster/fit/train_shared_params.py`（top‑q Spearman混合）, `scripts/cluster/fit/holdout_constrained_search.py`（top‑10%重視）, `scripts/reports/make_bullet_holdout.py`（partial r 図/表 維持）。
- パラ/レポート: `data/cluster/params_cluster.json`, `server/public/reports/bullet_holdout.html` / `.json`

## 次アクション
- 指示Aの範囲内で追加探索（ξ上限0.8, τ_q∈[0.45,0.7], β∈{0.5,0.7,0.8}）と、ROI加重（top‑15%）の試験。
- 図版の監査情報（PSF/高通過/マスク/ROI/整準rng）を脚注で更に固定表示。

