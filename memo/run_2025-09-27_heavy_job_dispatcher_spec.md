# 重いジョブ実行の標準仕様（dispatcher必須・隔離実行）

## 結果サマリ
- OOM/シグナル伝播によるtmux異常終了に対処するため、重い処理は必ずdispatcher経由で独立セッションに実行する。
- dispatcherは `GRAV_BG_JOB=1` を付与し、setsid+nohupで新PG/新セッションに起動。ログ/メタを保存。
- 対象スクリプトは起動ガードを実装。`GRAV_BG_JOB` 未設定時は警告を出して `exit 1`。
- Makeに -bg ターゲットと汎用 `jobs-*` を追加。MEMSAFE_ENV と swap拡張(8GiB)でメモリ対策も併用。

## 目的/背景
- 2025-09-27 10:45:11(JST) にカーネル OOM Killer が python(PID 839249) を kill（tmux配下）。以降の巻き添えでcodex/tmuxが終了。
- 以後、重い処理は親セッションから隔離し、OOM/シグナル伝播の影響を受けにくくする。

## 対象（重いスクリプト）
- `scripts/ab_comp/run_rep6_ws.py`
- `scripts/ab_comp/run_rep6_phieta.py`
- `scripts/reports/build_ws_vs_phieta_rep6.py`
- `scripts/cross_validate_shared.py`
- `scripts/build_state_of_the_art.py`

## 必須仕様（ガード）
- これらのスクリプトは起動時に `GRAV_BG_JOB=1` を検査。
  - 未設定の場合: 標準エラーに「dispatcher経由で実行してください」を出力し、`exit 1`。
  - 設定されている場合のみ実行を継続。

## 実装（ディスパッチャ）
- `scripts/jobs/dispatch_bg.sh`
  - 起動: `setsid` + `nohup` で新しいセッション/PGに実行。
  - 付与: `export GRAV_BG_JOB=1`（必須印）。必要に応じ `--env "K=V ..."` で追加入力。
  - ログ: `server/public/reports/logs/NAME_YYYYmmdd_HHMMSS.log`
  - メタ: `tmp/jobs/NAME_YYYYmmdd_HHMMSS.json`（pid/pgid/cmd/env/startedなど）
- 取消: `scripts/jobs/cancel_job.sh`（PGIDへSIGTERM→SIGKILL）

## Makeターゲット（運用）
- A/B代表:
  - `make rep6-ab-fast-bg`
  - `make rep6-ab-full-bg`
- 進捗+SOTA（背景実行）:
  - `make progress-bg RATE=50 NOTE="途中経過"`
- 任意実行/管理:
  - `make jobs-run NAME=my_job CMD='PYTHONPATH=. ./.venv/bin/python ...'`
  - `make jobs-status`
  - `make jobs-cancel NAME=my_job`

## メモリ/安定化
- MEMSAFE_ENV 既定（Makefile）:
  - `OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 NUMEXPR_MAX_THREADS=1 MALLOC_ARENA_MAX=2`
- スワップ拡張: `/swap.img` を 8GiB（`scripts/swap_extend.sh -s 8G`）。`/etc/fstab` 登録済。
- codex起動の分離: `make start/continue` は `setsid -w codex ...`（存在時）。

## ログと監視
- ログ: `server/public/reports/logs/*.log` をtailして監視。
- 状況: `make jobs-status`（`tmp/jobs/*.json` を集計）。

## 失敗時の扱い
- ガード違反（GRAV_BG_JOB 未設定）: スクリプトは即時終了（exit 1）。
- ジョブ停止: `make jobs-cancel NAME=...` で直近メタのPGIDに停止シグナルを送付。
- OOMが再発する場合: swapの拡張やコマンド分割、メモリプロファイルの確認を実施。

## 生成物
- 主要ファイル/変更点:
  - `scripts/jobs/dispatch_bg.sh`, `scripts/jobs/cancel_job.sh`（新規）
  - `scripts/ab_comp/run_rep6_ws.py`, `scripts/ab_comp/run_rep6_phieta.py`,
    `scripts/reports/build_ws_vs_phieta_rep6.py`, `scripts/cross_validate_shared.py`,
    `scripts/build_state_of_the_art.py`（ガード追加）
  - `Makefile`（MEMSAFE_ENV、-bgターゲット、jobs-ターゲット、setsid化、progress-bg）
  - `scripts/swap_extend.sh`（スワップ拡張ユーティリティ）
  - `.env.example`（推奨メモリ環境変数のコメント例）

## 次アクション
- 必要に応じて、他の重い処理にもガードと-bgターゲットを展開。
- `systemd-run --user --scope` を用いたcgroup隔離（MemoryHigh等）の導入検討。

