## 結果サマリ
- `server/public/reports` をリポジトリに追加しました（HTML/PNG/SVG/JSON 含む）。
- 大きなデータに配慮し、reports配下の `*.json` は Git LFS でトラッキング。
- 大量小ファイルの `logs/` と `cluster/` は除外し、`archives/*.tar.gz`（LFS）にスナップショット化済み。

## 生成物
- コミット: Add server/public/reports; LFS-track JSON; logs/cluster は archives に集約

## 次アクション
- 追加で LFS 化が必要な拡張子/パスがあれば指示ください（例: *.csv 大容量など）。
