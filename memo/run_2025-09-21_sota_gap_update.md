# run_2025-09-21_sota_gap_update

## 結果サマリ
- `memo/directive_2025-09-21_sota_gap.md` を再構成し、最新ステータスとギャップ解消マトリクスを明示したうえで、P0-A〜D に具体的な CLI 手順と公開更新フローを追加した。
- フェア条件脚注の統一手順（ベンチ再実行、ホールドアウト再生成、テンプレ確認）と `make repro_local` の検証ログ運用を文書化した。

## 生成物
- 更新: `memo/directive_2025-09-21_sota_gap.md`

## 確認事項
- `scripts/cluster/run_holdout_pipeline.py` と `config/cluster_holdouts.yml` を確認し、READY 判定と生成物パスを特定済み。
- `rg fair.json_sha` でベンチとクラスタ脚注の不一致箇所を把握（NGC2403, AbellS1063 が旧 sha 表記）。

## 次アクション
- 指示に沿って Bullet → MACSJ0416 → AbellS1063 の HO 実走と SOTA 反映を実行する（ΔAICc/FDB 判定・S_shadow 有意化）。
- `docs/runbook.md` に repro_local 手順と許容差を移植し、1-click 再現の手元運用を固める。
