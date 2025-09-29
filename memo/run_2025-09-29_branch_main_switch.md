## 結果サマリ
- メインブランチを `main` に統一しました（ローカルを `main` へリネーム、upstream 設定）。
- `git config init.defaultBranch main` を設定し、今後の `git init` 初期ブランチも `main` になります。
- リモート `origin` へ `main` を push（必要に応じて master は削除）。

## 生成物
- ブランチ: main（upstream=origin/main）

## 次アクション
- 既存のCI/デプロイ設定でブランチ名が `master` の参照があれば `main` に更新してください。
