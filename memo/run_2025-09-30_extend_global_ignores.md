## 結果サマリ
- __pycache__ 類似の一時/ビルド/キャッシュ系ディレクトリをグローバルおよびリポジトリの .gitignore に反映しました。
- 既に追跡されていた対象は index から除外（作業ツリーは保持）。

## 生成物
- ~/.gitignore_global（core.excludesFile へ登録）
- .gitignore（root-onlyの /public, docs/_build, _site を含む）

## 次アクション
- 他ツール固有のキャッシュで追加したいものがあれば指示ください。
