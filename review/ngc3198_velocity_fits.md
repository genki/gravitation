# NGC 3198 速度場（moment‑1）FITS 入手と前処理ガイド

目的:
- HALOGAS の深い HI 速度場（moment‑1）を主採用。必要に応じて THINGS の高解像 HI を補完。
- Hα 面輝度（SINGS/IRSA の HA_SUB）を n_e プロキシに変換し、残差オーバーレイを自動生成。

受入パス（このリポジトリの規約）:
- HI 速度場: `data/vel/NGC3198/velocity.fits`（moment‑1、BUNIT=km/s）
- Hα 面輝度: `data/halpha/NGC3198/Halpha_SB.fits`（erg s^-1 cm^-2 arcsec^-2）

---

## 1) HALOGAS（推奨）
- データ: HALOGAS Data Release 1（Zenodo）。NGC 3198 の HR/LR プロダクトに `*_mom1m.fits`（moment‑1）が含まれます。
  - 推奨: `NGC3198-HR_mom1m.fits`（~15" ビーム）
  - 参考: `NGC3198-LR_mom1m.fits`（~30" ビーム）
- 手順:
  1. ダウンロード後、MD5 を記録（任意）し、FITS ヘッダで以下を確認: `BUNIT=='km/s'`, `WCS`（CTYPE/CDELT/CD/PC）, ビーム `BMAJ/BMIN/BPA`。
  2. 本リポの標準配置へコピー:
     - `make vres-ngc3198 IN=/path/to/NGC3198-HR_mom1m.fits`
     - これにより `data/vel/NGC3198/velocity.fits` として取り込み、リング中央値差し引き残差×Hα 等高線の図を `server/public/reports/ngc3198_vfield_residual_ha.png` に生成します（Hα が未配置なら残差のみ）。

QC ポイント:
- 電波速度の基準系（LSR/ヘリオ）と符号規約（Doppler 定義）を確認。moment‑1 の単位は km/s であること。
- 異波長の重ね合わせを行う場合、最悪解像度（HALOGAS LR 等）に合わせてコンボリューションするのが安全です（本ベンチでは図示のみのため厳密 PSF 合致は要求しません）。

参考:
- 解析の背景や厚い HI 層のラグ等は Gentile et al. 2013（A&A）を参照。

---

## 2) THINGS（補完）
THINGS のキューブから moment‑1 を自作する想定です（既製の教育用 mom1 が入手できる場合はそれを流用可）。

Python 例（SpectralCube）:

```python
from spectral_cube import SpectralCube
from astropy.io import fits
from astropy import units as u

cube = SpectralCube.read("NGC3198_THINGS_cube.fits")
vc = cube.with_spectral_unit(u.km/u.s)
line = vc.spectral_slab(-350*u.km/u.s, 350*u.km/u.s)  # 必要に応じ調整
# S/N マスクやフラグを適用してから計算するのが推奨
mom1 = line.moment(order=1)  # km/s の平均速度（moment‑1）
hdu = fits.PrimaryHDU(mom1.value, header=mom1.header)
hdu.header['BUNIT'] = 'km/s'
hdu.writeto('NGC3198_THINGS_mom1.fits', overwrite=True)
```

取り込みは HALOGAS と同じ: `make vres-ngc3198 IN=NGC3198_THINGS_mom1.fits`

---

## 3) Hα → EM → n_e（プロキシ）
IRSA/SINGS の `HA_SUB` を取り込み、[N II] 除去と減光補正を任意で適用後、Rayleigh→EM へ変換します。

- 実行:
  - `make ha-ngc3198 IN=/path/to/HA_SUB.fits NII=0.3 EBV=0.02 KHA=2.53`
  - 出力: `data/halpha/NGC3198/Halpha_SB.fits`, `EM_pc_cm6.fits`, メタデータ JSON。

---

## 4) 残差オーバーレイと確認
- 速度場のリング中央値残差 × Hα 等高線: `make vres-ngc3198 IN=/path/to/velocity.fits [SIGMA=1.0]`
  - 生成物: `server/public/reports/ngc3198_vfield_residual_ha.png`
- 2D 近似残差（|g_ULW|）× Hα 等高線: `scripts/benchmarks/make_ngc3198_residual_overlay.py`（Hα があれば自動実行）

---

## 5) ベンチページへの反映
`make bench-ngc3198` を実行すると、以下が `server/public/reports/bench_ngc3198.html` に揃います。
- AICc と (N,k)、rχ² の明記（GR / MOND / GR+DM / FDB）。
- 外縁 1/r² 復帰の簡易図（g(R)·R² と外縁線形近似）。
- 太陽系 Null のログ（μ0(k→∞)→1 の数値偏差）。
- 残差×Hα のオーバーレイ（データが揃っていれば）。

備考:
- 本単一銀河ベンチでは NFW の c–M 事前は掛けません（粗グリッド）。SOTA 集計側では ln c のガウス事前（σ≈0.35）を併記しています。

