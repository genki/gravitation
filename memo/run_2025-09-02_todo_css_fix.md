# TODOページの相対リンク/スタイル修正

- 実行時刻: 2025-09-02 07:27 UTC

## 結果サマリ
- `server/server.py` のHTMLテンプレート出力を修正し、引用符エスケープ不備を解消
- `_root_prefix()` をディレクトリ深さベースに変更し、`/TODO.md` などルート直下の相対リンクを正しく出力
- TODOページを含むMarkdown配信のCSS/ナビリンクが有効化

## 生成物
- 更新: `server/server.py`

## 次アクション
- 他のMarkdownパス（`/memo/*.md`）の表示も外部ゲート越しに確認
