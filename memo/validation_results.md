# 比較検証ログ: GR(no DM) vs ULW-EM(FDB)

注: FDB = Future Decoherence Bias（ULW-EM に由来する見かけ重力）。

方法(概要)
- SPARC MassModels(Lelli+2016c)の1銀河に対し、加速度空間で比較。
- 観測: g_obs = Vobs^2/R, 誤差 eg ≈ 2 Vobs eV / R。
- モデル:
  - GR(no DM): g = g_gas + mu g_star (muは[3.6]のM/Lに相当)
- ULW-EM(FDB): g = g_gas + mu g_star + g_ulw(λ,A)
- 手順: (λ,A)を粗グリッドで探索。各点でmuは解析的最小二乗解。
  図は速度空間で重ね描き(観測/GR/ULW)。

実行コマンド
- `make compare-sparc` → DDO154の比較図を生成。
  出力: `paper/figures/compare_fit_DDO154.svg`

初期結果(粗グリッド)
- DDO154
  - GR: mu≈4.75, χ²≈2.35e4, AIC≈93.98
  - ULW: λ≈12 kpc, A≈100, mu≈4.53, χ²≈2.23e4, AIC≈99.80
  - コメント: χ²は僅差でULWが良いが、パラメータ数(3)の罰則を入れた
    AICではGRが有利。粗モデル/誤差扱い/軸対称近似の影響が大。

追加結果(構造ブースト: α=0.5, σをλに連動)
- DDO154: ULW(λ≈12kpc, A≈0.01, mu≈4.75) → χ²≈2.35e4, AIC≈100.39
  - ブーストは本対象では実質無効(最適Aが縮退)。
- NGC2403: GR(mu≈1.08) χ²≈9.13e4, AIC≈523.61 / ULW(λ≈12kpc, A≈0.01,
  mu≈1.08) χ²≈9.16e4, AIC≈529.89 → GR優位。
- NGC3198: GR(mu≈1.06) χ²≈7.71e3, AIC≈226.12 / ULW(λ≈12kpc, A≈100,
  mu≈1.01) χ²≈2.57e3, AIC≈185.02 → ULWが有意に優位。

注意点・今後
- 誤差: egの近似は単純。系統(傾斜/距離/非円運動)のマージン未導入。
- 星M/L: 単一mu(ディスク+バルジ共通)。分離/制約の導入を検討。
- g_ulw: いまは一定λのYukawa。今後はλのスケール依存やw(λ)の
  改良を検討して再比較する。
- 銀河拡張: NGC2403/3198等で同様に比較して挙動を評価。
