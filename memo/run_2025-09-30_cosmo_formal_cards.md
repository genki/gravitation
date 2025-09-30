# 宇宙論カード（WL 2PCF / CMBピーク）正式版の生成

## 結果サマリ
- CLASS (classy) を用いて **KiDS-450 tomo1-1** の ξ± を計算し、Late‑FDB の μ(a,k) に基づくスケール依存成長を適用。ΛCDM vs Late‑FDB の χ²/AICc を算出した正式カードを作成。
- CMB TT スペクトルの第1/第2ピークを CLASS から抽出し、正式カードとして整備（Late‑FDB との差分は再結合期では極小であることを示記）。
- 生成物: `server/public/state_of_the_art/wl_2pcf_formal.html`, `server/public/state_of_the_art/cmb_peaks_formal.html`, `server/public/state_of_the_art/cosmo_formal_summary.json`。
- SOTA のクイックリンクを正式版カードへ差し替え。

## 実装ポイント
- 新規スクリプト `scripts/reports/make_cosmo_formal.py` を追加。
  - CLASS から Pδ(k,z) を取得（`class_baseline`）。
  - Late‑FDB では `apply_mu_growth` によりスケール依存成長を適用。
  - 単一ソース面 (z≈0.9) 近似の Limber 積分を実装し ξ± を評価。
  - CMB は lensed Cl を用いて ΔT²(ℓ₁/ℓ₂) を出力。
- 結果の χ²/AICc を JSON と HTML へ出力。
- `scripts/build_state_of_the_art.py` を更新し、正式カードへのリンクを自動反映（フォールバックで軽量版を表示）。

## 次アクション
- KiDS / Planck 等の実測値・共分散を整備し、カード内の χ² を実データで再評価。
- Late‑FDB→CMB の補正（再結合期でのμ効果）を hi_class 等で検証。
- ΔAICc のサマリを SOTA トップの KPI セクションに追記。

