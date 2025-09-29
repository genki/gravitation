# run_2025-09-23_bg_job_eta

- 2025-09-23T02:23:19 JST 時点で `python scripts/reports/make_bullet_holdout.py --train Abell1689,CL0024 --holdout AbellS1063 --sigma-highpass 0.7 --sigma-psf 1.5 --weight-powers 0` が稼働中 (PID 445873)。
- `server/public/reports/cluster/AbellS1063_progress.log` 最新行: `[holdout:AbellS1063-shadow-perm] 1,243/2,000` (進捗約 62.2%)、経過 11.92 分、推定残り 7.31 分 → 完了予想 2025-09-23T02:30 頃。
- 停止再開後の StageResume でも `shadow_perm` の進捗が 1,243/2,000 (62.2%)。完了済みステージ (resid_perm 5,000/5,000、shadow_boot 400/400) を含む全工程ベースでは 6,643 / 7,400 ステップ ≒ 89.8% が完了。
- 前回 run より `sigma-psf` が 1.0 → 1.5 へ変更されており、perm 周回も再スタートしている。

## 生成物
- `server/public/reports/cluster/AbellS1063_progress.log` に最新 perm 周回の進捗が追記中。

## 次アクション
- 進捗ログが 2000/2000 へ到達したら生成物 (perm メタ/values jsonl) を確認。
- `sigma-psf` 変更理由を確認し、KPI への影響があれば別途メモ化する。
