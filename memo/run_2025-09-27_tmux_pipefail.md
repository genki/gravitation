# tmux セッション終了の原因調査（pipefail影響）

## 結果サマリ
- dotfiles（~/.profile, ~/.bashrc）に `set -o pipefail` / `set -e` の恒常設定は無し。`gravitation/tools/profile.d/gravitation-paths.sh` でも該当設定はコメントアウト済み（安全）。
- tmux 側の環境伝播も問題なし。`tmux show -g update-environment` に `SHELLOPTS` は含まれず、`tmux show-environment` でも `SHELLOPTS/BASH_ENV/ENV` は未設定（環境からの強制継承は起きていない）。
- リポジトリ内の多数のスクリプトは `set -euo pipefail`（厳格モード）で開始するが、いずれも「実行」前提で設計されており、dotfiles等から「source」される設計ではない。
- 最も起こり得る原因は「厳格モードのスクリプトを誤って source した」ケース。これにより現在の対話シェルに `errexit/pipefail` が残留 → 些細な失敗でシェル自体が終了 → tmux ペイン/セッションが閉じる、という事象と整合する。

## 主要調査ログ（抜粋）
- ~/.profile: 行11–17で ~/.bashrc を取り込み。独自の `set -o` 設定なし。
- ~/.bashrc: 行5–9で非対話シェルを return。`set -o pipefail`/`set -e` 設定なし。行127で `tools/profile.d/gravitation-paths.sh` を source（同ファイル6行目は `#set -euo pipefail` とコメントアウト）。
- tmux: `tmux show -g update-environment` は既定の DISPLAY/SSH_* 等のみ。`tmux show-environment` に `SHELLOPTS/BASH_ENV/ENV` なし。
- 本リポジトリ: `scripts/*.sh`, `batch/*.sh`, `bin/lenstool` 等が `set -euo pipefail` を使用（「実行」前提）。Makefile のレシピ内も `set -euo pipefail` を明示（レシピ用サブシェル内のみ有効）。

## 原因の推定（静的解析による結論）
- 恒常設定・tmuxグローバル環境・BASH_ENV/ENV による継承は見当たらず、外部セッションへ自動伝播する経路は確認できない。
- 一方、厳格モードのスクリプトを対話シェルで `source`（または `.`）してしまうと、`SHELLOPTS` 経由で現在のシェルに `errexit/pipefail/nounset` が有効化されたまま残留する。以降に実行した通常コマンド（例: パイプラインや補助コマンド）が非ゼロ終了すると対話シェルが終了し、tmux ペイン/セッションが突然閉じる。
- よって「誤 source に起因する厳格モードの残留」が最も整合的な根本原因。

### 参考（再現条件の一例）
1) tmux 内で `source scripts/notice.sh` のように誤って source する。
2) その後、プロンプト更新やパイプラインを含む小コマンドが失敗（例: `cmd1 | cmd2` の一部が未存在）
3) `errexit+pipefail` により対話シェルが終了 → ペインやセッションが閉じる。

## 生成物
- 本メモ（原因、根拠、対処案の整理）

## 次アクション
- スクリプトの「誤 source」防止ガードを追加（例）:
  - 各 `scripts/*.sh` 冒頭に次を入れる: `[[ ${BASH_SOURCE[0]} != "$0" ]] && { echo 'Do not source; run this script.' >&2; return 1; }`
  - あるいは `main()` 内に `set -euo pipefail` を閉じ込め、ファイル末尾で `main "$@"` を呼ぶ（source されても親シェルへ副作用を残さない）。
- tmux 側の安全策（任意）:
  - `~/.tmux.conf` に `set -g remain-on-exit on` と `set -g detach-on-destroy off` を設定し、プロセス終了時の即時クローズを避ける。
  - 念のため `setenv -gu SHELLOPTS; setenv -gu BASH_ENV; setenv -gu ENV` を追記し、環境継承を明示的に遮断。
- 運用ガイド追記: スクリプトは必ず「実行」(`./scripts/xxx.sh`) し、「source しない」旨を `README`/`AGENTS.md` に明記。

