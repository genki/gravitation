# run_2025-09-23_abells1063_mask065_sigma07

## 結果サマリ
- AbellS1063 ホールドアウトを σ_highpass=0.7 pix, mask_q=0.65, w(Σ_e)=Σ_e^0, σ_psf=1.0 で実行し permutation n=5,000/block=4 を完走。
- S_shadow(global)=0.0565, outer=0.148 と正値だが p_perm_one_sided_pos=0.453 で成功条件 (p<0.01) 未達。
- ΔAICc(FDB−rot)=-1.36×10^7, ΔAICc(FDB−shift)=-6.19×10^5 と AICc 条件は満たしている。

## 生成物
- server/public/reports/AbellS1063_holdout.json
- server/public/reports/AbellS1063_holdout.html
- logs/abells1063_mask075.log

## 次アクション
1. マスク分位 0.70/0.75/0.80 と高通過帯域の組合せを再走査し、outer 主判定での有意性向上を検証。
2. 重み指数 0.3/0.7 や σ_psf=1.5 を併用した再実行で S_shadow の改善を試みる。
3. permutation block_pix を 6–8 に変更して空間相関の影響と p 値の変動を確認。

## 詳細
### 実行パラメータ
- コマンド: `PYTHONPATH=. python scripts/reports/make_bullet_holdout.py --holdout AbellS1063 --sigma-psf 1.0 --sigma-highpass 0.7 --weight-powers 0`
- block_pix=4, rng_seed=42, permutation n=5,000, mask_quantile=0.65。

### 指標メモ
- S_shadow: global=0.0565, outer_r75=0.1477, core_r50=NaN。
- permutation: p_perm_one_sided_pos=0.4528, p_fdr=0.478; perm_test(effect_d=-2.03, p_perm_one_sided_neg=0.0152)。
- ΔAICc: FDB−rot=-1.3641050×10^7, FDB−shift=-6.191655×10^5, FDB−shuffle=2.0622489×10^7。
- alignment: FFT相互相関後 dx=367, dy=368 (Lanczos3)、fair_wrap=(-7, 12)。
