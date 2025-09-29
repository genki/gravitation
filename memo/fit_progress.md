# 初期フィット進捗(ULW-EM Yukawa, SPARC)

手法(最小版)
- 入力: SPARC MassModels (Lelli+2016c) の半径プロファイル
  `R[kpc]`, `Vobs`, `e_Vobs`, `Vgas`, `Vdisk`, `Vbul`, `SBdisk`。
- 軸対称近似: `SBdisk(R)`から2D軸対称の`j_EM(r)`画像を生成(最大1に
  正規化)。
- 有効場: `(∇^2-λ^{-2})φ = β j_eff` をFFTで解き、`g = -η∇φ`を算出。
- 置換モデル(FDB): `g`はFDB単体で重力を与える(内部にGR同型成分を含む)
  ため、`g_GR`との和は取らない。`Vmod = sqrt(R g)`。
- フィット: `(λ, A=βη)` のグリッド探索で赤χ²最小(誤差は`e_Vobs`)。

セットアップ/実行
- 依存導入: `make setup`
- 実行例: `make fit-sparc` (サンプル: DDO154)
- 出力図: `paper/figures/sparc_fit_<name>.svg`

結果(サンプル)
- DDO154: 最小 (粗グリッド)
  - 最良: `λ ≈ 12 kpc`, `A ≈ 1e2`, `χ² ≈ 2.23e2`
  - 図: `paper/figures/sparc_fit_DDO154.svg`

現状の制約/注意
- 近似: 軸対称、M/L=1固定、粗いグリッド(λ∈{2,3,5,8,12}kpc,
  A∈logspace[1e-2..1e2])。
- 次段: 連続最適化(単純Nelder-Mead)、M/L共変、銀河ごとの
  `(λ, A)`階層化(固定/共有の比較)。
- 妥当性: RAR/BTFRを包括する全銀河同時評価の設計が必要。

TODO
- 2–3銀河(例: DDO161, D631-7)で同様にフィットし挙動確認。
- M/Lの自由度(ディスク/バルジ)を1–2次元で同時最適化。
- λの事前分布(1–10kpc)とAの物理スケール合わせを検討。
