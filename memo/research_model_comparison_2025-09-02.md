# 質量分布モデル比較の計画と初期設計

- 目的: NFW/等温コア/MOND相当(phenomenological) を共通の指標(AIC/AICc)で比較。
- 現状: ULW(FDB)とGR(noDM)の枠組みは実装済。NFW/ISO/MOND相当は雛形未実装。

## 設計
- 入力: SPARC MassModels (既存)
- 追加モデル:
  - NFW: V^2 = V_baryon^2 + V_NFW^2(c, V200)
  - 等温(コア): V^2 = V_baryon^2 + V_ISO^2(ρ0, r_c)
  - MOND相当: V^2 = V_baryon^2 + V_MOND^2(a0, ν)（単純な補正関数で代用）
- 推定: 各銀河で最小二乗→AIC/AICc集計、共有/独立の2モード
- 出力: data/results/model_comp_*.json, reports/model_comp.html

## TODO(実装タスク)
- [ ] NFW/ISO/MOND相当の速度関数の実装 (src/fdb/models_ext.py)
- [ ] compare_fit_multi.py にモデル切替フラグを追加
- [ ] 結果レポーター scripts/build_model_comp_report.py の追加

