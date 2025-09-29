# 2025-09-17 Fig-EU1c CLASS 連携化

## 結果サマリ
- classy 3.3.2.0 を導入し、`scripts/eu/class_validate.py` を更新して CLASS 出力を実計算化。
- Fig‑EU1c（assets/figures/early_universe/Fig-EU1c_class_bao.png）と SOTA ページのカードが実データ表示になり、振幅比≈0.994 / Δk≈0.0 を出力。
- 公開用 `server/public/state_of_the_art/figs/fig_eu1c.png`・`data/fig_eu1c.json`・`data/fig_eu1c_class.ini` を生成。
- 再現ログ（command, CLASS version, shared_params_sha, cfg/class_ini の SHA）を SOTA ページ脚注および JSON に常設。

## 生成物
- assets/figures/early_universe/Fig-EU1c_class_bao.png
- server/public/state_of_the_art/figs/fig_eu1c.png
- server/public/state_of_the_art/data/fig_eu1c.json
- server/public/state_of_the_art/data/fig_eu1c_class.ini
- server/public/state_of_the_art/early_universe_class.json

## 次アクション
- classy バージョンアップ時の再生成手順を docs/state-of-the-art.md に追記検討。
- growth_solver / mu_late パラメタ探索の高速化（現状 z=0.57 固定）。
