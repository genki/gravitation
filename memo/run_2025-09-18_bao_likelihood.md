# 2025-09-18 BAO 尤度評価メモ

## 結果サマリ
- SDSS-III BOSS DR12 合意値 (z = 0.38 / 0.51 / 0.61) を `data/bao/bao_points.yml` として整理し、CLASS 3.3.2.0 の LCDM 基準に対する FDB (成長補正) 予測と同時評価した。
- 観測 (D_M, H) とモデルの差分で χ² = 3.87, 自由度 = 6, p = 0.694。AICc = 3.87 で、ΛCDM との差分は 0（背景自由度を追加していないため）。
- 個々の残差は |pull| ≤ 1.46 (最大は z=0.61 の H)。ΔD_M は |Δ| ≲ 20 Mpc、ΔH は ±3.6 km s⁻¹ Mpc⁻¹ 以内に収束。
- `server/public/state_of_the_art/data/fig_eu1c.json` と `.../early_universe_class.json` に BAO 尤度ブロックを追記。SOTA ページで χ²/AICc を掲示できる状態になった。

## 生成物
- 新規: `data/bao/bao_points.yml`
- 新規: `analysis/bao_likelihood.py`
- 更新: `scripts/eu/class_validate.py`
- 更新: `server/public/state_of_the_art/data/fig_eu1c.json`
- 更新: `server/public/state_of_the_art/early_universe_class.json`

## 手順メモ
1. CobayaSampler/bao_data の `sdss_DR12Consensus_bao.dat` と `BAO_consensus_covtot_dM_Hz.txt` から (D_M, H) 観測値と 6×6 共分散を引用。観測は D_M [Mpc], H [km s⁻¹ Mpc⁻¹] で整理。
2. `analysis/bao_likelihood.py` で YAML をロードし、CLASS で得た D_M=(1+z)D_A, H(z), r_d を用いてモデルベクトルを生成。共分散の逆行列から χ²・pull を計算。
3. `scripts/eu/class_validate.py` から当該ロジックを呼び出し、Fig-EU1c の JSON/メタに BAO ブロックを挿入。実行ログ: `PYTHONPATH=. python scripts/eu/class_validate.py`。
4. 結果は χ²/ndof=3.87/6, ΔAICc=0, BAO likelihood の p=0.694。図版および JSON に χ²・p・参照ファイルハッシュを付記。

## 次アクション
- SOTA ページ本文／カードで BAO χ²/AICc を掲示し、文言「壊さない」を定量値に差し替える。
- DESI/eBOSS など追加サンプルを `bao_points.yml` に拡張し、FDB 拡張版との整合を検証。
- BAO 用 CI（`make repro`）に `analysis/bao_likelihood.py` を組み込み、差分監視を自動化。
