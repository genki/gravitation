# Bullet質量分布データの在庫確認 — 2025-09-13

## 結果サマリ
- リポジトリにBullet(1E 0657-56)の質量分布関連データを確認。
- 弱レンズκマップ（Clowe+06 release1）とガス質量マップ、せん断/銀河カタログ、
  Chandra ACIS画像、内部派生の `sigma_e.fits` と `omega_cut.fits` を保持。
- Data Catalogに存在・サイズ・更新日時が反映（最終更新: 2025-09-11〜12 UTC）。

## 生成物
- 確認のみ（ファイル追加なし）。本メモを追加。

## 参照パス（主要）
- `data/cluster/Bullet/kappa_obs.fits`（κ; 1e0657.release1.kappa.fitsのコピー）
- `data/cluster/Bullet/kappa_wayback/1e0657.release1.kappa.fits`
- `data/cluster/Bullet/kappa_wayback/1e0657_central_gasmass_mod.fits`
- `data/cluster/Bullet/kappa_wayback/1e0657.release1.shear.dat`
- `data/cluster/Bullet/kappa_wayback/1e0657.release1.clustergal.dat`
- `data/cluster/Bullet/sigma_e.fits`, `data/cluster/Bullet/omega_cut.fits`
- `data/cluster/Bullet/cxo/*.fits.gz`（Chandra ACIS 画像）
- カタログ: `server/public/reports/data_catalog.html`（Bullet項）

## 次アクション
- 必要ならKS等でκの再構成を実施: `make reconstruct-ks`（要: せん断カタログ指定）。
- HST/ACS画像が未整備なら取得: `bash scripts/fetch/fetch_hst_bullet.sh`。
- 解析再現: `make bullet-holdout`（固定パラのホールドアウト検証）。

