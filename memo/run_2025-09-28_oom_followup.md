# OOMフォローアップ（FULL再開とメモリ緩和）

## 結果サマリ
- 2025-09-28 18:59:48 に kernel OOM が発生し、`python` が kill されました（journal: "Out of memory: Killed process 852596 (python)"）。
- 該当ジョブは `abell_full_48_none`（AbellS1063, band=4–8, perm_n=10000）。`shadow_perm` は 3917/12000 まで進行後に中断。
- メモリ要因は FFT ベースのバンドパス計算の一時メモリ増大（アリーナ膨張含む）と推定。並列度は既に 1 に制御済み。
- 対応: `MALLOC_ARENA_MAX=2 PYTHONMALLOC=malloc` を付与し BG 再開。`StageResume` により 3917 から再開を確認。
- 予防: 将来の FULL 自動昇格でも `MALLOC_ARENA_MAX=2` を既定適用（`scripts/jobs/auto_escalate_full.py`を更新）。

## 生成物
- パッチ: `scripts/jobs/auto_escalate_full.py`（BLAS制御に加え `MALLOC_ARENA_MAX=2` を既定化）
- 再開ログ: `server/public/reports/logs/abell_full_48_none_resume_20250928_191838.log`
- 進捗ファイル: `server/public/reports/cluster/AbellS1063_shadow_perm_meta.json`（iterations=3917→継続）

## 次アクション
- 監視: この再開ジョブの完了までログと `*_shadow_perm_meta.json` を確認（OOM再発時は `--float32` への切替を検討）。
- 改善候補: FULL 昇格の既定に `--float32` を追加する是非を要検討（数値安定性と再現性の影響をレビュー）。
- 併走制御: FULL の同時実行数を 1 に制限する簡易ロック導入（`tmp/locks/full.lock` 等）を検討。

