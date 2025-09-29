# run_2025-09-23_abells1063_search

## 結果サマリ
- AbellS1063 ホールドアウトを軽量設定 (n_perm=2000) で複数回再実行し、マスク分位と重み指数の影響を確認したが、S_shadow(global) は 0.05 前後、p_perm≈0.36–0.45 で有意水準に到達せず。
- `scripts/reports/make_bullet_holdout.py` に per-cluster 出力分離ロジックを導入済みの状態で再実行しても、AICc 差 (ΔAICc(FDB−rot)≈-3.26e9, ΔAICc(FDB−shift)≈-2.15e8) は維持されることを確認。
- 既存アルゴリズムは AICc 最優先で候補を選択するため、S_shadow を最大化するパラメタ探索には個別設定で再実行する必要があると判明 (ROI/mask を単一値に固定し直す必要あり)。

## 生成物
- 更新: `scripts/reports/make_bullet_holdout.py`
- 更新: `server/public/reports/AbellS1063_holdout.html`, `server/public/reports/AbellS1063_holdout.json`
- 更新: `server/public/state_of_the_art/index.html` (間接影響なし)

## 確認事項
- 最新 `server/public/reports/AbellS1063_holdout.json` で `mask_quantile=0.70`, `S_shadow(global)=0.055`, `p_perm=0.364` を確認。外縁 ROI でも p_perm≒0.36 で未達。
- `cluster/AbellS1063_shadow_perm_meta.json` の digest が更新され、n=2000 の permutation が再実行済みであることを確認。

## 次アクション
- マスク分位ごとに単一設定 (σ_psf, weight_power, σ_highpass) を固定して S_shadow を比較し、高値を示す組み合わせを特定する。
- 有望設定について n_perm=12000, block_pix∈{4,6,8} を実行し、p_perm<0.01 を達成できるか検証する。
- S_shadow の候補選択を S/FDR 優先に切り替えるオプションを実装し、AICc優先による方向性低下を回避する方法を検討する。
