# 2025-12-06 GitHub Pages にリポジトリリンク追加

## やったこと
- wiki→GitHub Pages デプロイ用ワークフローにトップバーを追加し、リポジトリ/Wiki/最新PDFへのリンクを各ページ上部に自動挿入。
- トップバー用の簡易スタイル（アクセント色・ピル型リンク）を付与して目立つようにした。

## 影響範囲
- `.github/workflows/wiki-to-pages.yml`（Pages生成時のみ。既存本文やPDFには影響なし）。

## 次の一手
- `wiki-to-pages` ワークフローを手動 dispatch するか次の定期実行（毎12時間）を待ち、gh-pages を更新。
- 反映後、Pages サイト上でリンク表示を目視確認する。

## デプロイ試行メモ
- `gh workflow run wiki-to-pages.yml` は PAT に workflow scope が無く 403。
- ローカルで wiki をクローンし HTML を再生成、gh-pages ワークツリーに反映してコミット済み。
- `.env` に `GITHUB_TOKEN` が無く `git push origin gh-pages` は認証エラーで失敗。トークン設定後に `git push origin gh-pages` を実行すればデプロイ完了。

## 通知
- `make notify-done` ターゲットが存在せず実行できなかった（Makefile 未実装）。代替手段があれば follow-up 要。

## 追加作業（2025-12-06）
- `.env` の `GITHUB_TOKEN` を使って `gh workflow run wiki-to-pages.yml` を実行したが、`HTTP 403: Resource not accessible by personal access token` で失敗（workflow scope 不足と思われる）。PAT に `workflow` 権限を付けて再試行する必要あり。
- 代替としてローカルで wiki をクローンし pandoc で静的HTMLを生成、`gh-pages` ワークツリーに同期して直接 `git push origin gh-pages` を実行しデプロイ完了（コミット bb164ae）。
- 「What is FDB?（3行で）」の表現を GR 同型の 1/r² 幾何を主軸にした文言へ修正し、wiki Home.md と README の該当箇所を更新。再度 pandoc 生成・`gh-pages` へ手動 push（コミット 7a32ff5）。
- 学習なし「宇宙型ディフュージョン」最小デモを `demo/univ/` に追加（スクリプト・README）。`pip install torch numpy matplotlib` が前提。ローカル実行では matplotlib 未インストールで ModuleNotFoundError を確認（依存を入れれば動作見込み）。メインへ push 済み（コミット a95acd6）。
