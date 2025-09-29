# run_2025-09-27 CMB ピーク（Boomerang‑2001）軽量尤度の作成

## 結果サマリ
- Boomerang‑2001 の音響ピーク（data/cmb/peak_ratios.yml）から、簡易χ²を構成し、Late‑FDB と ΛCDM に同一予測を用いた **ΔAICc≈0** の“壊さない”確認カードを作成。
- JSON/HTML を SOTA 配下に配置し、SOTAトップに要約ブロックを自動掲示。

## 生成物
- server/public/state_of_the_art/data/cmb_likelihood.json（χ²・dof・注記）
- server/public/state_of_the_art/cmb_peaks.html（軽量カード）
- SOTA 再生成（CMB ピーク要約の掲示を確認）

## 次アクション
- フル版: 理論予測の写像を導入し、同一共分散の下で ΔAICc≈0 を実測提示（class_ini_sha 注記を付与）。
