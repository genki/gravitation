# Hαマップ取得・校正・配線 — 最小パイプライン実装

## 結果サマリ
- 取得手順に基づき、`HA_SUB.fits`（SINGS/IRSA）を入力として面輝度 `Halpha_SB.fits`（erg s^-1 cm^-2 arcsec^-2）と EM `EM_pc_cm6.fits`（pc cm^-6）を生成するスクリプトを追加。
- NGC 3198 ベンチは Hα FITS 検出時に自動で等高線図を生成・掲載（重ね合わせは2D残差配線後に自動化）。
- 変換式・係数・補正（[NII]/減光）のメタデータを `Halpha_metadata.json` に記録。

## 生成物
- `scripts/halpha/ingest_halpha.py`（CPS→F_line→I_Hα→EM）
- `data/halpha/NGC3198/Halpha_SB.fits`, `EM_pc_cm6.fits`, `Halpha_metadata.json`
- `scripts/benchmarks/make_ngc3198_ha_overlay.py`（Hα等高線 PNG） → `server/public/reports/ngc3198_ha_contours.png`
- Makeエントリ: `make ha-ngc3198 IN=.../HA_SUB.fits [NII=...] [EBV=...] [KHA=...]`

## 次アクション
- Hα等高線の**面内残差ヒートマップ**への重ね合わせ（2D残差の自動生成配線）。
- 再投影/PSF統一・[NII]径依存モデル・前景/内部減光の拡張（メタデータに係数と根拠を追記）。
