## 結果サマリ
- 開発環境全体で一時ディレクトリ（`__pycache__`, `.pytest_cache` など）を無条件で無視するため、`~/.gitignore_global` を設定しました。
- リポジトリの `.gitignore` でもアンカー無しパターンを確認/補完し、全階層で適用されるようにしました。

## 生成物
- `~/.gitignore_global`（core.excludesFile に登録）
- `.gitignore` 更新（必要箇所のみ）

## 次アクション
- チームメンバーにも `core.excludesFile` 設定の共有を推奨します。
