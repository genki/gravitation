# β前方化の配線検証とユニットテスト追加（surfaceモード）

## 結果サマリ
- compare_fit_multi の surface 経路で β 前方化（角度カーネル + 半径重み）の実配線挙動を再現するテストを追加。
- 角度カーネル（Lambert前方化の近似）と radial_forwardize の併用で、外側半径の寄与が相対的に増加することを検証（合成データ）。
- 低レイヤ（irradiance_log_bias, radial_forwardize）のテストに加え、配線全体の意図が壊れていないことを確認。

## 生成物
- tests/test_compare_fit_beta_wiring.py（新規）: `compute_inv1_unit('fft', ...)` + `radial_forwardize` 構成で外/内比の増加を検証。
- テスト総数: 18件に増加（全通過）。

## 次アクション
- β 前方化のUI露出と使用例をドキュメントに追記（CLIヘルプ、SOTAページ内注記）。
- NGC3198 ベンチの残差×Hαオーバーレイ自動生成に着手（データ存在時のみ）。
- AIC→AICc表記の全面統一（SOTA/一覧ページの再生成）。

## 参考
- 実装参照: scripts/compare_fit_multi.py（surface 経路の β 前方化適用）。
- 既存テスト: tests/test_beta_forward.py, tests/test_beta_kernel_forward.py.
