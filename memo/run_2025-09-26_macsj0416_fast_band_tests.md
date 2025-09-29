# 2025-09-26 — MACS J0416 FAST パラメータ追加探索

## 結果サマリ
- band を `4–8,8–16` に拡張した FAST 設定は S_shadow=0.149 (outer=0.345), p_perm=0.344 と劣化。ΔAICc 優位は維持。
- mask/edge/weight の追加スイープでも p_perm を 0.02 未満に下げられず、現状ベストは S_shadow=0.724 (p=0.064)。

## 実施内容
- `--band 4-8,8-16` を指定し、mask=0.88 / edge_count=640 / σ_psf=1.0,1.5 / 高通過0.8,1.0,1.2 / ROI 0.82,0.88,0.92 で FAST 再実行。
- その他の組み合わせ（mask=0.88 で weight ±0.3, block_pix=8 など）も試行し、結果を `MACSJ0416_holdout.json` で確認。

## 生成物
- `server/public/reports/MACSJ0416_holdout.html`
- `server/public/reports/cluster/MACSJ0416_progress.log`

## 次アクション
- Σ 層／角度核の再設計に着手し、mask 0.83–0.85 × edge_count 768/832 を中心とした FAST 探索を継続。
- 有望設定が得られたら FULL (band 4–8/8–16, σ_psf 1.0/1.5/2.0, n_perm≥1e4, global+outer) で確証し、SOTA へ反映。
