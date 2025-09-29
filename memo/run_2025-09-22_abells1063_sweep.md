# run_2025-09-22_abells1063_sweep

## 結果サマリ
- AbellS1063 ホールドアウトで `sigma_highpass`・`sigma_psf`・`mask_quantile`・重み指数を調整。`BULLET_MASK_Q=0.5` / `sigma_psf=1.0` / `sigma_highpass=0.7` / `weight_power=0` で ΔAICc(FDB−rot)=-1.36e7, ΔAICc(FDB−shift)=-6.19e5 を維持しつつ **S_shadow=0.256 (p_perm≈0.18, n=2000)** まで改善（初期値 0.055→0.256）。citeserver/public/reports/cluster/AbellS1063_holdout.json:1server/public/reports/cluster/AbellS1063_holdout.json:28server/public/reports/cluster/AbellS1063_holdout.json:820
- `BULLET_MASK_Q` や `BULLET_SHADOW_EDGE_QS` を変えた他パターン（mask=0.6, edge_q=0.85 等）も検証したが、S_shadow の統計的有意性 (p<0.01) には到達せず。citelogs/abells1063_holdout_20250922.logserver/public/reports/cluster/AbellS1063_holdout.json:820

## 生成物
- 更新: `server/public/reports/cluster/AbellS1063_holdout.json`, `server/public/reports/cluster/AbellS1063_holdout.html`
- ログ: `logs/abells1063_holdout_20250922.log`

## 確認事項
- ΔAICc(FDB−rot) と ΔAICc(FDB−shift) は負側を維持。citeserver/public/reports/cluster/AbellS1063_holdout.json:28
- S_shadow の p 値は 0.18 前後であり、有意水準 (p<0.01) に届いていない。citeserver/public/reports/cluster/AbellS1063_holdout.json:820

## 次アクション
- `BULLET_SHADOW_EDGE_QS` を複数候補 (0.3–0.9) で再走査し、外縁ROIの S_shadow を強化できる設定を特定する。
- Align offsets (`BULLET_ALIGN_OFFSETS`) や重み指数 (負値含む) を系統的に走査し、Spearman/Permutation の効果が最大となる組み合わせを抽出する。
- 有望設定に対し `BULLET_SHADOW_PERM_MIN=12000` で本番評価し、p_perm<0.01 を満たすか再確認する。
