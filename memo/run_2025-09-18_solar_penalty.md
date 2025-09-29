# 2025-09-18 Solarペナルティ導入

## 結果サマリ
- `analysis/solar_penalty.py` を新設し、Late‑FDB パラメタ (eps_max, a_on, da, k_c) から μ(1AU) とΔa(1AU)を算出する関数 `compute_solar_penalty` を実装。閾値は Δa≤1×10⁻¹³ m s⁻² とした。
- `scripts/eu/class_validate.py` で Solar ペナルティを計算し、`server/public/state_of_the_art/data/fig_eu1c.json` と `early_universe_class.json` に `solar_penalty` ブロックを追加。
- `scripts/build_state_of_the_art.py` を更新し、SOTA Early-Universe カードに Solar ペナルティ列（μ(1AU), Δa, 比, PASS/FAIL）を恒常表示。現在の設定では `status=fail` が明示される。

## 生成物
- 新規: `analysis/solar_penalty.py`
- 更新: `scripts/eu/class_validate.py`
- 更新: `scripts/build_state_of_the_art.py`
- 更新: `assets/figures/early_universe/Fig-EU1c_class_bao.png`（再生成）
- 更新: `server/public/state_of_the_art/data/fig_eu1c.json`
- 更新: `server/public/state_of_the_art/early_universe_class.json`
- 更新: `server/public/state_of_the_art/index.html`

## 次アクション
- Solar ペナルティを BAO χ² 等と併せて CI テストに追加し、Δa>閾値でビルド失敗とするガードを整備。
- Solar ペナルティを銀河/クラスタ（κ,C）系のパラ推定にも接続し、AICc へ加点する仕組みを設計。
