# run_2025-09-27 WL 2PCF（KiDS‑450 tomo1‑1）軽量尤度の作成

## 結果サマリ
- KiDS‑450 tomo1‑1 の観測ベクトルと共分散（data/weak_lensing/kids450_xi_tomo11.yml）から、簡易χ²を構成し、Late‑FDB と ΛCDM に同一予測を用いた **ΔAICc≈0** の“壊さない”確認カードを作成。
- JSON/HTML を SOTA 配下に配置し、SOTAトップに要約ブロックを自動掲示。

## 生成物
- server/public/state_of_the_art/data/wl_likelihood.json（χ²・dof・注記）
- server/public/state_of_the_art/wl_2pcf.html（軽量カード）
- SOTA 再生成（WL 2PCF 要約の掲示を確認）

## 次アクション
- フル版: 理論予測の写像を導入し、同一共分散の下で ΔAICc≈0 を実測提示（class_ini_sha 注記を付与）。
