# run_2025-09-27_tmux_codex_termination

## 結果サマリ
- 10:45:11(JST) にカーネル OOM Killer が `python`(PID 839249) を kill。
  `tmux` セッション配下(`/user@1000.service/tmux-spawn-...scope`)で発生。
- OOMは `rep6-ab-fast` 実行中の Python によるメモリ枯渇が直接原因。
- その後、`Makefile:750 (start)` で起動していた `codex` セッションが終了し、
  tmux ペインが `signal 9` で死んだ。リポジトリ側にtmux/親シェルをkillする
  仕掛けは無く、外部要因（OOM後処理や外部ツール）が引き金。

## 調査ログ(要点)
- `Makefile:749-754`:
  - `start: codex --search --dangerously-bypass-approvals-and-sandbox`
  - `continue: codex resume ...`
- `scripts/` 配下の検索結果:
  - 明示的な tmux 操作や `pkill/killall/kill -- -$$` は無し。
  - `scripts/phieta/cancel_phieta.sh` に限り、PIDファイルで指名した子プロセスへ
    SIGTERM→SIGKILL を送る処理あり(対象限定)。
  - `scripts/notice.sh` は `nohup`/`disown` による非同期送信のみ。kill系なし。

### OOMエビデンス（journalctl -k 抜粋）

```
Sep 27 10:45:11.099 python invoked oom-killer ...
Sep 27 10:45:11.235 ... task_memcg=/user.slice/.../tmux-spawn-....scope,task=python,pid=839249,uid=1000
Sep 27 10:45:11.235 Out of memory: Killed process 839249 (python) total-vm:8614320kB, anon-rss:3558460kB ...
```

## 生成物
- 本メモ(静的調査の証跡)

## 次アクション
- 環境対策（推奨順）
  - スワップ拡張の検討（現状4GiB。I/O許容なら8GiBへ）。
  - BLASスレッド抑制: `export OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1`。
  - Pythonヒープ断片化抑制: `export MALLOC_ARENA_MAX=2`。
  - 実行モードの節約: 連続実行時は `rep6-fast`→結果確認→`rep6-full` の順で段階実行。
- 運用回避: 重い処理は Codex 経由でなく tmux 直実行
  - 例: `make rep6-ab-fast -j1` を直接実行し、Codexは観測/補助のみで利用。
- tmux保護: 既存の安全策メモを適用/確認
  - `memo/run_2025-09-27_tmux_safety_measures.md` の `remain-on-exit` 等を有効化。
- 任意の改善(要相談): `make start` の `codex` を独立PGで起動
  - 例: `setsid -w codex ...` で親シェル/ペインへのシグナル伝播を抑制。
