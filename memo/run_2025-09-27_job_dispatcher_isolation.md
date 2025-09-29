# 重いジョブの独立実行ディスパッチャ導入

## 結果サマリ
- codex/tmuxからのシグナル伝播を避けるため、独立セッションで実行するディスパッチャを追加。
- 新ターゲット: `rep6-ab-fast-bg`, `rep6-ab-full-bg`, `jobs-run`, `jobs-status`, `jobs-cancel`。
- メタ情報は `tmp/jobs/*.json`、ログは `server/public/reports/logs/*.log` に保存。
- 重要: 重いスクリプトは起動ガードを実装。`GRAV_BG_JOB=1` が未設定の場合、
  「dispatcher経由で実行してください」と表示して `exit 1`。

## 生成物
- `scripts/jobs/dispatch_bg.sh` — setsid+nohupで新セッション起動、PID/PGIDとログ/メタ書き出し。
- `scripts/jobs/cancel_job.sh` — メタからPGIDを取得し、安全にSIGTERM→SIGKILL。
- `Makefile` — -bgターゲットと汎用 `jobs-*` を追加、`MEMSAFE_ENV`と併用。
- 起動ガード追加（`GRAV_BG_JOB`）: 
  - `scripts/ab_comp/run_rep6_ws.py`
  - `scripts/ab_comp/run_rep6_phieta.py`
  - `scripts/reports/build_ws_vs_phieta_rep6.py`
  - `scripts/cross_validate_shared.py`
  - `scripts/build_state_of_the_art.py`

## 次アクション
- 運用移行: A/B再計算は `make rep6-ab-fast-bg` で起動し、`make jobs-status` で監視。
- 必要時は `make jobs-cancel NAME=rep6_ab_fast` で直近ジョブを停止。
- 拡張案: systemd-run --user --scope でのcgroup隔離/MemoryHigh設定の導入（任意）。
