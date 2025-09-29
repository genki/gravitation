# 2025-09-17 ベースライン同期(クラスタ) 初動

## 結果サマリ
- `config/baseline_conditions.json` を新設し、バレットクラスタの公平条件（WLS・PSF/HP・整準・ラップ・N/N_eff）を一元管理。
- `scripts/reports/make_bullet_holdout.py` がベースラインJSONを読み込むようリファクタ。PSF/高通過/マスク既定値やメタ情報に baseline_counts・baseline_alignment などを反映。
- `PYTHONPATH=. python scripts/reports/make_bullet_holdout.py` を再実行し、生成物 (`server/public/reports/bullet_holdout*.{html,json}`) に共通条件が出力されることを確認。

## 生成物
- config/baseline_conditions.json
- server/public/reports/bullet_holdout.json/.html（baseline メタ更新）

## 次アクション
- ベースラインJSONを bench/EU スクリプトからも参照させ、脚注・AICc 表を自動同期。
- CI 用の閾値チェックスクリプトを追加し、SOTA/ホールドアウトの値ズレを検出する。
- NGC3198/NGC2403 ベンチスクリプトにベースライン読込を接続し、監査カードへ Baseline (config/baseline_conditions.json) の N/k 情報を表記。
- HTML 出力を再生成して整合性を確認。
- FDB 新パラメタ移行の準備として `params/schema_v2.json` とマイグレーションスクリプト (`scripts/migrate_params_v1_to_v2.py`) を追加。
