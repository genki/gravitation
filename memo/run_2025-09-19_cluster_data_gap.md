# 2025-09-19 MACSJ0416/AbellS1063 データ評価

## 結果サマリ
- Frontier Fields Lenstool v4 FITS は取得済み。`kappa_obs.fits` を CATS v4 κ から配置し、PIXKPC を付与済み。
- Chandra ACIS ObsID (MACSJ0416: 16235/16236/16522/16545, AbellS1063: 3591/6108/6110/6111/6112) の `full_img2` / `cntr_img2` を `scripts/fetch/fetch_cluster_cxo.py` で取得。
- `scripts/cluster/make_sigma_wcut_from_cxo.py` を用い、両クラスターの `sigma_e.fits` / `omega_cut.fits` を生成。
- 要求データ（kappa/sigma_e/omega_cut）が `data/cluster/MACSJ0416`, `data/cluster/AbellS1063` に揃い、ホールドアウトパイプラインを進められる状態になった。

## 不足項目
- 追加の X 線モザイク（複数ObsID合成）や正式PIXKPC計算が必要な場合は再処理を検討。
- Lenstool κ のバージョン差異検証（CATS vs Sharon）を行う余地あり。

## 推奨アクション
1. 生成した `sigma_e/omega_cut` の品質確認（SNマスクやスムージング）を追跡。
2. Lenstool κ の別バリアント（Sharon v4 等）も取得して比較検証を準備。
3. ホールドアウトパイプライン (`scripts/cluster/run_holdout_pipeline.py --auto-train`) で MACSJ0416 / AbellS1063 を実行し、SOTA カードの MISSING 状態を解消。
4. 取得・生成手順を `memo/run_2025-09-19_data_request_plan.md` に追記し、再現ログを整理。

## 次アクション
- ObsID ごとのデータ取得 scripts（CIAO 導入判断含む）を検討。
- Lenstool κ → `kappa_obs.fits` コピー処理を準備。
