# tmuxセッション保護の安全策実装

## 結果サマリ
- 誤って`source`された際に`errexit/pipefail`が親シェルへ残留しないよう、実行用スクリプト全体に「誤source防止ガード」を導入。
- `batch/_common.sh` は他スクリプトからの `source` 前提のため、厳格モードをこのファイル内では有効化しない方針へ変更（呼び出し元で厳格モード有効）。
- `~/.tmux.conf` を新規作成し、`remain-on-exit on`・`detach-on-destroy off`・`exit-empty off` を設定。SHELLOPTS/BASH_ENV/ENV を tmux 環境から明示的に除去。
- 運用ドキュメント(AGENTS.md)に「スクリプトは実行専用・source禁止」を追記。

## 主要変更点（抜粋）
- 誤source防止ガードを追加（例、scripts/notice.sh 冒頭）:
  - `if [[ ${BASH_SOURCE[0]} != "$0" ]]; then echo 'Do not source...' >&2; return 1 2>/dev/null || exit 1; fi`
  - 対象: `scripts/` 配下ほぼ全て, `batch/` の実行スクリプト, `bin/lenstool`（計40+ファイル）。
- `batch/_common.sh`: 厳格モード行を削除し、コメントで方針明記。
- `~/.tmux.conf` 新規:
  - `set -g remain-on-exit on`
  - `set -g detach-on-destroy off`
  - `set -g exit-empty off`
  - `setenv -gu SHELLOPTS; setenv -gu BASH_ENV; setenv -gu ENV`
- `AGENTS.md`: 「Bashスクリプトは実行専用（source禁止）」追記。

## 次アクション
- 反映: 稼働中の tmux で `tmux source-file ~/.tmux.conf` を実行（または次回の tmux 起動から有効）。
- TIPS: もし対話シェルが落ちやすいと感じた場合、`set +e; set +o pipefail` で一時的に解除可能。
- 運用共有: 「スクリプトは source しない」方針をチームへ周知。

