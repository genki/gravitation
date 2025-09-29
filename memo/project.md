# プロジェクト研究ログ: ULW-EM / FDB 仮説の実証

注: FDB = Future Decoherence Bias（ULW-EM に由来する見かけ重力）。

## 基本仮説
- **ULW-EM (Ultra Long Wavelength Electromagnetism)** が「見かけの重力」として作用する。
- GR (no DM) は ULW-EM の波数空間における **直流成分 (λ→∞)** と対応する。
- それ以外の有限 λ 成分が GR との差分 (FDB) を与える。
- 星系スケールでは直流成分のみ → GR と同じに見える。
- 銀河スケールでは低周波成分が寄与して差が顕著になる。

---

## データ取得
- **MaNGA (SDSS DR17/18)**: LOGCUBE, MAPS をダウンロード。  
  - `download_manga_dr17.sh` により自動取得可能。
  - `plateifu.txt` に Plate-IFU を列挙。
- **SPARC**: rotation curve catalog (700+ galaxies) を利用。
- **THINGS**: HI 21cm 観測で高解像度データ。

---

## 前処理
- `manga_3d_mass_from_maps.py`:
  - LOGCUBE + MAPS を統合し、3D 質量分布と rotation curve を推定。
  - 出力:
    - `manga3d_meta.json`
    - `manga3d_rotationcurve.csv`
    - `manga3d_quicklook.png`

- 正規化: rotation curve に `Vobs_kms`, `eVobs_kms` を整備。
  - `normalize_rotcurve.py` → `*_rotationcurve_norm.csv`

---

## FDB モデル（Future Decoherence Bias）
### FDB1
- 単一パラメータ θ
- 加速度:  
  \[
  g = g_{\text{GR}} \cdot (1 + \theta^2)
  \]

### FDB2
- パラメータ a, b
- 加速度:  
  \[
  g = g_{\text{GR}} + a \cdot \tanh\!\left(\frac{r}{b}\right)
  \]

### FDB3
- パラメータ a, b, c
- 加速度:  
  \[
  g = g_{\text{GR}} + a \cdot \left(1 - e^{-r/b}\right)^c
  \]

### FDBL (linear octree 3D)
- 3D 質量分布を octree で解釈。
- 各 depth が λ に対応。
- バンドごとに重みを設定し、合成して全体の加速度場を計算。

---

## グローバルフィット結果
- 42 銀河 (SPARC サンプル) を用いて全銀河同時フィット。
- **結果 (redχ²)**:
  - FDB1 ≈ 412
  - FDB2 ≈ 240
  - FDB3 ≈ 121
- **モデル選択 (AIC/BIC)** → FDB3 が最有力。

---

## ULW-EM スペクトル重み付け
- ULW-EM は電磁波であるため、放射源温度に基づく黒体放射スペクトルの超低周波部分に従う。
- 温度 T=20K を仮定し、Rayleigh–Jeans 近似で重みを算定。
- 例: λ = {1e6, 5e3, 5e2} pc → weights ≈ {2.5e-7, 0.0099, 0.9901}.

---

## 現在の課題
1. **GR(no DM) が obs とフィットしすぎる問題**:
   - 出力 CSV 内で `Vgr_nodm` に誤って `Vobs` が書かれている可能性。
   - 単位 (km/s vs m/s, kpc vs arcsec) の不一致も疑われる。
   - → CSV のカラム (`Vobs`, `Vgr`) を要確認。

2. **FDBL 3D 実装**:
   - Octree の depth ごとに λ を割り当てて加速度場を構築。
   - タイムラグ効果をどう組み込むか検討中。

3. **正則化ルール**:
   - λ 成分の自由度が大きすぎると過剰フィット。
   - → ウェーブレット係数のような制約、RJ スペクトル比による拘束を導入。

---

## 今後のステップ
- [ ] SPARC/THINGS の rotation curve を用いた FDB3 vs FDBL3D の直接比較。
- [ ] RJ スペクトルに基づく全銀河同時フィット。
- [ ] GR(no DM) カラムの中身を精査し、真の差分を確認。
- [ ] タイムラグ (λ/c) 効果を実装。
- [ ] 他銀河系への拡張 (NGC3198, NGC2403 など高解像度サンプル)。

---
