## Bullet 全球PASS — ROI加重(15%)＋拡張グリッド（Round‑7） — 2025-09-14

## 結果サマリ
- 目的関数に **top‑15% Σ_e の −Spearman**（W_ROI=0.06）を追加混合（主はAICc; ΔAICc制約あり）。
- 分位正規化(sigma_norm_q=0.9)を維持したまま **拡張グリッド**（ξ≤0.8, τ_q∈[0.45,0.7], β∈{0.5,0.7,0.8}）で制約付き探索。
- 選抜パラ: α=1.0, β=0.8, C=0.05, ξ=0.7, p=1.0, τ_q=0.45。
- 検証（Permutation n=8192, Bootstrap n=4096）: KPI‑B維持。全球Spearman≈+0.286、top‑10%≈+0.095、partial r(global)≈+0.075 → 符号は依然正側。

## 生成物
- コード: `train_shared_params.py`（ROI加重mix）, `min_kernel.py`（Σ分位正規化）, `holdout_constrained_search.py`（top‑q優先）, `make_bullet_holdout.py`（Bootstrap/partial図/脚注）
- パラ/レポート: `data/cluster/params_cluster.json`, `server/public/reports/bullet_holdout.html` / `.json`

## 次アクション（提案）
- 目的関数の重みを微増（W_ROI=0.1, W_CORR=0.15 目安）して更に負側を探索（ΔAICc制約は維持）。
- τ_q を 0.4–0.55 に集中させ、β=0.8 固定で ξ∈[0.6,0.8] を掃引（高速FAST→本検証）。
- ページ脚注へ PSF/高通過/マスク/ROI/整準rng の固定表示は実装済み。必要に応じ SOTAへも同様の脚注を展開。

