# run_2025-09-23_gap_to_proof_plan

## 結果サマリ
- Bullet ホールドアウトの最新 JSON (`server/public/reports/cluster/Bullet_holdout.json`) を確認し、ΔAICc(FDB−rot)=-6.79e7, S_shadow(global)=0.378, p_perm=2.25e-3 (n=12000) が成立していることを整理した。
- AbellS1063 / MACSJ0416 ホールドアウトの一次データを精査し、未達指標（S_shadow の p 値、ΔAICc>0、ピーク距離 FAIL）の具体値と調整すべきハイパラを特定した。
- 上記ギャップと再現性・宇宙論・データ補完タスクを統合した新ディレクティブ `memo/directive_2025-09-23_gap_to_proof.md` を作成し、P0/P1 の実行計画と DoD チェックリストを更新した。
- `scripts/reports/make_bullet_holdout.py` をホールドアウト名ごとのファイルに分離し、Bullet 以外の run が `server/public/reports/bullet_holdout.*` を上書きしないよう修正。既存の Bullet 結果を `server/public/reports/Bullet_holdout.*` / `bullet_holdout.*` に同期した上で SOTA を再ビルドし、バレット KPI カードを ΔAICc<0・S_shadow=0.378 (p_perm=0.0022) 表示へ更新。

## 生成物
- 新規: `memo/directive_2025-09-23_gap_to_proof.md`
- 更新: `TODO.md`（2025-09-23 の追記事項を追加）
- 更新: `scripts/reports/make_bullet_holdout.py`
- 更新: `server/public/reports/Bullet_holdout.html`, `server/public/reports/Bullet_holdout.json`, `server/public/reports/bullet_holdout.html`, `server/public/reports/bullet_holdout.json`
- 更新: `server/public/state_of_the_art/index.html`

## 確認事項
- Bullet/AbellS1063/MACSJ0416 の各 `*_holdout.json` / `*_progress.log` を参照し、Permutation 設定・mask/PSF/weight の現状値を記録。
- `server/public/state_of_the_art/early_universe_class.json` で BAO/RSD/Solar の χ²/AICc が ΔAICc≈0 を維持していることを確認。

## 次アクション
- P0-A/B/C/E のタスク（Bullet legacy同期、AbellS1063 permutation拡張、MACSJ0416 WCS補正、IRAC1取得・lenstools導入等）を順次実装し、runbook と通知フローを更新する。
- P1 の弱レンズ/CMB 軽量尤度実装に向け、KiDS-450 / Boomerang データセットの整形スクリプトを準備する。
