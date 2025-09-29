# 追加データ収集メモ(軽量カタログ中心)

更新: 2025-08-27

## 収集済み/利用中
- 画像: LegacySurveys(光学), GALEX(FUV/NUV), unWISE(W1/W2)
- スペクトル立方体: MaNGA(DR17) 一部サンプル
- 回転曲線: SPARC(MassModels/Param), ALFALFA表
- LSS: 2MRS(Table 3)

## 今回追加
- SDSS DR17 カットアウト `sdss_dr17.jpg`
- Pan-STARRS(PS1) カットアウト `ps1_{g,r,i}.jpg`
- 実行: `make imaging-extra`
  - 入力: `data/imaging/targets.txt`
  - 出力: `data/imaging/<name>/manifest.json`

## 追加(カタログ/メタデータ)
- VizieR RC3 (VII/155/rc3) の取得を追加。
  - 実行: `make catalogs-vizier`
  - 出力: `data/catalogs/vizier/VII_155_rc3/`
    にターゲット別TSVと`combined.tsv`

## 次に候補(軽量/表中心)
- xGASS/xCOLDGASS: HI/CO質量カタログ(CSV)。BTFR/RAR検証に有用。
- PHANGS-ALMA: マスター表(銀河物理量/距離/傾斜)。COマップ本体は大。
- S4G: 3.6μmフォトメトリ(P4)表。バリオン分布の補助に有用。
- HyperLEDA: 距離/傾斜/系外塵減光などの集約表。名前解決にも。
- RCSEDv2(軽量派生表): 距離/光度/色指数の統合。全体は巨大。

## 実装方針
- まずはメタデータ(CSV/TSV)のみ取得するfetchスクリプトを作成。
- 公開の安定URLのみを使用(失敗時はスキップ/再試行)。
- 取得結果は `data/<source>/` に保存し、`manifest.json`で記録。

## 注意
- 大容量の立方体/モザイクは対象を絞る(プレースホルダで可)。
- API/TOS遵守。間隔を空け、失敗は穏当リトライに留める。

## 追加済(2025-08-27)
- VizieRバンドル: `make catalogs-bundle`
  - 対象: RC3, S4G(P4), xGASS, xCOLDGASS, (暫定)PHANGS表
  - 出力: `data/catalogs/vizier/<catalog_id_sanitized>/`
