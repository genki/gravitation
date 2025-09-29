# 2025-09-18 公平条件(fair.json) 実装と参照統一

## 結果サマリ
- `config/fair.json` を新設し、Bullet ホールドアウトおよび単一銀河ベンチ共通の公平条件（WLS σマップ、N_eff、PSF/高通過、マスク/ROI、整準、wrap、rng、k_map）を一元管理。
- `scripts/reports/make_bullet_holdout.py` が `fair.json` を参照するよう再構成し、メタデータ・HTML・JSON 出力に fair.json の SHA/パスを埋め込み。AICc 表／カードは公平カウントを明示し、`processing_meta` に fair_counts/fair_k_map を追加。
- NGC 3198 / 2403 ベンチスクリプトを `scripts/config/fair.py` 経由へ移行し、カード表示に fair.json の SHA を追記。baseline_conditions.json のベンチマーク節は fair.json 参照メモへ更新。

## 生成物
- config/fair.json（公平条件定義）
- scripts/config/fair.py（ロード／SHA 取得ユーティリティ）
- scripts/reports/make_bullet_holdout.py（fair.json 連携、再現フッタ更新）
- scripts/benchmarks/run_ngc3198_fullbench.py（公平条件参照更新）
- scripts/benchmarks/run_ngc2403_fullbench.py（同上）
- config/baseline_conditions.json（ベンチマーク節のメモ追記）
- memo/run_2025-09-18_fair_json_sync.md（本メモ）

## 次アクション
- Bullet ホールドアウト JSON/HTML の diff をレビューし、ダッシュボード側の公平表示（表記「Fairness」）を確認。
- CI/ダッシュボードで fair.json の SHA を監査ログ（used_ids 等）へ取り込み、ズレ検知を自動化。
- bench/cluster 以外のスクリプト（例: progress dashboard）での公平条件参照箇所を巡回し、`fair.json` への差し替え漏れが無いか確認。
