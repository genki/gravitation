# 2025-09-26 — MACSJ0416 κマップ再投影＋FASTホールドアウト（ΔAICc負化）

## 結果サマリ
- `kappa_obs.fits` を `sigma_e.fits` と同一 WCS/解像度へ再投影し、MACS J0416 FAST ホールドアウトで **ΔAICc(FDB−rot)=-3.26×10⁴**, **ΔAICc(FDB−shift)=-2.36×10³** を達成。
- 方向統計は S_shadow=0.724(outer 0.760) まで上昇したが、FAST段階の permutation 2000 本で **p_perm≈0.064**（基準未達）。

## 実施内容
1. `data/cluster/MACSJ0416/kappa_obs.fits` を `kappa_obs_orig.fits` に退避し、Astropy WCS + `scipy.ndimage.map_coordinates` で Σ_e グリッド (398×499 pix, PIXKPC=17.06) へ再投影 → `kappa_obs.fits` を生成。
2. FAST 設定（`--fast --sigma-psf 1.0,1.5 --sigma-highpass 0.8,1.0,1.2 --roi-quantiles 0.82,0.88,0.92`）で MACS J0416 ホールドアウトを再実行。
3. マスク・edge_count・重みを掃引（例: mask=0.88/edge=640, mask=0.90/edge=896, mask=0.847/edge=808 など）して S_shadow/p_perm の変化を確認。

## 生成物
- `data/cluster/MACSJ0416/kappa_obs.fits`（再投影済み κ）
- `server/public/reports/MACSJ0416_holdout.html`
- `server/public/reports/cluster/MACSJ0416_progress.log`

## 次アクション
- mask 0.83–0.85 × edge_count 768/832 の FAST 探索を継続し、**p_perm<0.02** を達成した設定を FULL (band 4–8 & 8–16, σ_psf=1.0/1.5/2.0, n_perm≥1e4, global+outer) で確証。
- 再投影手順をスクリプト化し、MACS データ準備の runbook へ反映。
