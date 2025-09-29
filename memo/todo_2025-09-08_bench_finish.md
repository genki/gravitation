# メモ: 銀河ベンチ仕上げ（NGC3198/2403）

目的: 外縁1/r²の定量（g(R)·R² の線形フィット）と95%CI、Hα等高線オーバー
レイの自動化、ベースライン脚注テンプレの統一。

受け入れ条件(DoD)
- HALOGAS/THINGS到達半径までの傾き・95%CIを図注に明示。
- Hα 等高線が残差図に自動重畳（データ未入手時は明示的プレースホルダ）。
- 脚注テンプレ: MOND(a0/μ), GR+DM(NFW c–M事前/探索域/seed/M/L) を共通化。

実行手順
1) `scripts/benchmarks/fit_outer_inverse_square.py` を追加し傾きを bootstrap で推定。
2) `scripts/halpha/ingest_halpha.py` の出力を等高線関数に接続し overlay を自動化。
3) 図注テンプレを `assets/templates/baseline_notes.md` から注入し統一。
4) `make bench-ngc3198 bench-ngc2403` を再実行して確認。

