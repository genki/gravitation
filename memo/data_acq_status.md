# データ取得ステータス(Phase1・初回)

- 実行日時: 2025-08-26 UTC
- 実行者: Codex CLI

## 配置と取得結果

- SPARC: 取得済
  - `data/sparc/SPARC_Lelli2016c.mrt` (28 KB)
  - `data/sparc/MassModels_Lelli2016c.mrt` (263 KB)
- ALFALFA: 取得済
  - `data/alfalfa/a100.code12.table2.190808.csv` (~3.8 MB)
- MaNGA DR17(SPX 3.1.0): サンプル取得済
  - `data/manga/dr17/8485-1901/LOGCUBE/manga-8485-1901-LOGCUBE.fits.gz`
  - `data/manga/dr17/8485-1901/MAPS/manga-8485-1901-MAPS.fits.gz`
  - `data/manga/dr17/8077-12703/LOGCUBE/manga-8077-12703-LOGCUBE.fits.gz`
- THINGS: 大容量のため未取得(スクリプトに案内済)
- GALEX/WISE: 地域抽出が必要なため未取得(スクリプト整備予定)

## メモ/知見

- MaNGA DR17のDAPは`analysis/v3_1_1/3.1.0/SPX-...`の階層で、
  ファイル名にパイプライン名が含まれる。
- 既存スクリプトは旧パス想定だったため修正。現在はSPX系を取得。
- SPARCのCSVは提供されておらず、公式.mrtの取得が安定。
- ALFALFAの最終版カタログは`a100.code12.table2.190808.csv`。

## 次アクション案

- MaNGA: `data/manga/dr17/plateifu.txt`のターゲットを拡充しバッチ取得。
- GALEX/WISE: RA/Decリスト入力で円錐抽出する`fetch_galex.sh`/`fetch_wise.sh`
  を追加。まずはMaNGA `dapall`から座標抽出。
- 整合: 取得物のハッシュと件数を台帳化(JSON)し再取得も容易に。

