# dispatcher拡張（systemd scope）とガード導入

## 結果サマリ
- `dispatch_bg.sh` に `--scope` と `--meta` を追加。`--scope` 指定時は `systemd-run --user --scope` を用いて別 cgroup に起動し、OOM 時の tmux 巻き添えを抑止。
- `run_holdout_async.sh` を dispatcher 経由に統一（メタは従来の `tmp/jobs/holdout_*.json` に書込）。
- 重量級エントリ `scripts/reports/make_bullet_holdout.py` にディスパッチャ未経由の警告を追加（`GRAV_BG_JOB!=1` かつ tmux 検出時に stderr へ注意喚起）。

## 生成物
- 更新: `scripts/jobs/dispatch_bg.sh`（`--scope/--meta`、scope 実行時は unit 名もメタに記録）
- 更新: `scripts/jobs/run_holdout_async.sh`（dispatcher 呼び出しへ置換）
- 更新: `scripts/reports/make_bullet_holdout.py`（dispatcher ガード警告）

## 次アクション
- 任意: 他の重量級スクリプト（`ab_comp/*`, `build_state_of_the_art.py` 等）にも同警告を展開。
- 任意: `watch_and_notify.py` を unit 監視にも対応させ、scope 実行時の終了検出を PID 以外でも補完。
- 任意: `dispatch_bg.sh` に `--memory-max` 等の resource hints を追加検討。
