# 銀河系データ収集計画

本計画は研究再現性と保守性を重視し、必要最小限から拡張可能な
段階的収集を行う。既存`scripts/`を活用しつつ、データ配置規約と
メタデータ統合方針を統一する。

## 目的と対象

- 目的: 銀河内部運動とバリオン物理の検証。回転曲線、星質量、
  ガス質量、SFR、幾何学(傾斜角PA)を共通IDで統合。
- スコープ: 近傍(z≲0.05)の銀河。空間分解分光と多波長撮像の併用。

## フェーズ構成(最小可用セット→拡張)

1) 重要コア(Phase1)
   - SDSS‑MaNGA DR17: IFU分光(DAP/DRP派生量, NSA)
   - SPARC: 高品質回転曲線(光学/赤外幾何)
   - GALEX: UV(SFR指標)
   - WISE/AllWISE: 中赤外(星質量指標)
   - ALFALFA: HIガス質量

2) 追加拡張(Phase2)
   - 2MASS XSC: 近赤外光度
   - S4G: 3.6/4.5μm構造
   - SDSS撮像/LegacySurvey: 光学形態補助

## ディレクトリとバージョン規約

```
data/
  raw/<dataset>/<version>/           # 配布の原本
  interim/<dataset>/<version>/       # 中間生成物
  processed/<release_tag>/           # 解析入力の統合体
  external/                          # 再配布不可の派生
```

- 命名: `<dataset>`は`manga`, `sparc`, `galex`, `wise`, `alfalfa`。
- バージョン例: `dr17`, `v1.0`, `2023-12-01`等。
- 原本は不可変。更新は新バージョンとして併置し差分管理。

## 識別子と照合キー

- 主キー順序: `NSAID`(MaNGA同梱)→天球座標(RA,Dec,epochJ2000)。
- MaNGA: `plateifu`, `mangaid`, `NSAID`。解析では`NSAID`を優先。
- SPARC: `name`と座標。座標半径一致で`NSAID`へ帰属。
- 他カタログ: 座標一致(半径3″基準, 拡張5–10″再試行)。
- 一致実装指針: `astropy.coordinates`と球面kd木による高速照合。

## 収集対象と入手先(Phase1)

1) SDSS‑MaNGA DR17
   - 入手: SDSS SAS `dr17/manga/`配下。
   - 必須: `drpall`(v3_1_1), DAP MAPS,CUBE,NSA抜粋。
   - 参考: plateifu一覧は`data/manga/dr17/plateifu.txt`に存在。
   - 目安容量: 100–300GB(全量)。本研究は`DAP MAPS`の要約で軽量化。

2) SPARC
   - 入手: https://astroweb.cwru.edu/SPARC/ 公式配布。
   - 必須: 回転曲線表, 幾何量(incl,PA), 光度尺度。
   - 容量: 数十MB。

3) GALEX(AIS/MIS)
   - 入手: MAST。公開テーブルとイメージを選択取得。
   - 必須: FUV/NUV等級, 有効半径内光度, 測光フラグ。
   - 容量: 数百MB(テーブル主体)。

4) WISE(AllWISE/NEOWISE)
   - 入手: IRSA。AllWISEソースカタログ。
   - 必須: W1/W2測光, 品質フラグ, 拡張源指標。
   - 容量: 数百MB(抽出)。

5) ALFALFA
   - 入手: Arecibo Legacy ALFALFAカタログ。
   - 必須: HI線幅, 系外速度, 秤量距離, logMHI。
   - 容量: 数十MB。

## 取得オーケストレーション

- 既存スクリプト活用:
  - `scripts/download_manga_dr17.sh`: MaNGA原本の同期。
  - `scripts/fetch_sparc.sh`: SPARC取得。
  - `scripts/fetch_things.sh`: 汎用フェッチ下地。
- 追加予定:
  - `scripts/fetch_galex.sh`, `scripts/fetch_wise.sh`,
    `scripts/fetch_alfalfa.sh`(将来追加)。
- 将来のMake統合:
  - `make setup`: 依存ツール導入(curl,wget,astropy環境等)。
  - `make fetch`: Phase1全取得を順序実行。
  - `make refresh`: 差分更新と整合性検査。

## 中間生成と統合スキーマ

- 中間形式: Parquet/CSV(UTF‑8, 行指向はCSV, 列指向はParquet)。
- 共通列案:
  - `nsaid`, `mangaid`, `plateifu`, `ra`, `dec`, `z`, `dist_mpc`
  - `logmstar`, `sfr`, `av`, `incl`, `pa`, `r25_arcsec`
  - `logmhi`, `w50`, `vrot_max`, `flag_quality`, `dataset_mask`
- FITS要約:
  - DAP MAPSから速度場, 乱流速度, S/Nの統計量を抽出。
  - マスクビットを尊重し外れ値を除去。

## 整合性検査と品質管理

- 完全性: 期待件数との差分を台帳化(JSON/CSV)。
- 同一性: ハッシュ(SHA256)とサイズ記録。再取得時に照合。
- 統計監査: 基本統計(件数, 欠損率, 主要量の分布)を保存。
- 位置照合検証: 無相関領域での偽一致率を推定(シフト法)。

## ライセンスと謝辞

- 各配布の再配布方針を尊重。原本は`data/raw/`に保持し再配布しない。
- 論文内謝辞テンプレートを`docs/`に用意し、引用を明記する。

## スケジュール(目安)

- W1: 既存スクリプト検証, MaNGA plateifu台帳確定, SPARC取得。
- W2: GALEX/WISE/ALFALFAのテーブル抽出と座標一致基盤実装。
- W3: DAP要約生成, 共通スキーマ統合v0リリース。
- W4: QA/監査, 安定化, `processed/v0.1`固定。

## リスクと回避

- サーバ仕様変更: フォールバックURLとミラーを定義。
- 取得量過多: MaNGAは要約生成を優先し原本全量は後回し。
- レート制限: バックオフと再試行、夜間ジョブ。

## 実行手順(初期)

1) SPARC取得: `scripts/fetch_sparc.sh`を実行し`data/raw/sparc/`へ。
2) MaNGA台帳: `data/manga/dr17/plateifu.txt`を基に対象抽出。
3) MaNGA要約: DAP MAPSから速度統計の最小要約CSVを作成。
4) 一致基盤: `NSAID`優先, 座標半径3″で補助一致を実装。
5) 統合v0: `processed/v0.1/galaxies.parquet`を生成。

## 追跡メトリクス

- 取得成功率(%), 欠損率(%), 偽一致率(%), 再現ジョブ時間(min)。

## 参考

- SDSS MaNGA DR17: https://www.sdss.org/dr17/manga/
- SPARC: https://astroweb.cwru.edu/SPARC/
- GALEX(MAST): https://mast.stsci.edu
- WISE(IRSA): https://irsa.ipac.caltech.edu
- ALFALFA: https://egg.astro.cornell.edu/alfalfa/data/

