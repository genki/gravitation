# data ディレクトリ目録（概要）

## sparc
- `MassModels_Lelli2016c.mrt` — SPARC 質量モデルカタログ（Lelli+2016）。
- `SPARC_Lelli2016c.mrt` — SPARC MRT 主ファイル。
- `sparc_database/` — 銀河ごとの rotmod データ（Rad, Vobs, errV, Vgas, Vdisk, Vbul, SBdisk, SBbul）。
  - 例: `NGC2403_rotmod.dat`, `NGC3198_rotmod.dat`, `NGC6503_rotmod.dat`, …（全175銀河）。
- `sets/` — サブセット定義テキスト
  - `all.txt`, `barset.txt`, `lsb.txt`, `hsb.txt`, `nearby.txt`, `ngc2403_only.txt`, `ngc3198_only.txt` など。
  - ブラックリスト／クリーンセット: `blacklist.txt`, `clean_for_fit.txt`, `clean_no_blacklist.txt` ほか。

## strong_lensing
- レンズカタログ CSV
  - `SLACS_table.cat`, `SLACS_sigSIE.csv`, `SLACS_sigSIE_clean.csv`
  - `BELLS_GALLERY_SL2S_table.csv`
  - `S4TM_table.csv`
  - `BOSS_full_table.csv`, `BOSS_LAE_table.csv`
  - `SNL_table.csv`
- ソースHTML（出典キャッシュ）
  - `sources/bells2012.html`, `bells_gallery2016.html`, `mnras2017.html`

## filaments（追加準備中）
- Tempel+2014 SDSS DR8 フィラメントカタログ: `data/filaments/dr8_filaments.fits` （53 MB）を収蔵済み。

## 備考
- `sparc_database.zip` — rotmod データのアーカイブ。
- `sets/_boot_tmp*.txt` — ブートストラップ用一時セット（生成物）。
