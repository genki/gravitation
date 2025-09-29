# 論文作成ガイド (arXiv)

本ディレクトリは arXiv 投稿用の論文スケルトンです。本文は原則英語で記述します（希望があれば日本語クラスへの変更も可能）。

## 使い方
- 章ごとに `sections/*.tex` を編集し、`main.tex` で結合します。
- 図は `figures/` に配置し、`\includegraphics{figures/<name>.pdf}` で参照します。
- 参考文献は `references.bib` に BibTeX 形式で追加します。

## ビルド
- `make pdf`: `latexmk` があれば自動で PDF 化。なければ `pdflatex + bibtex` にフォールバック。
- `make clean`: 中間生成物を削除。
- `make arxiv`: arXiv 提出用 zip を `dist/arxiv.zip` に作成（`.bbl` を同梱）。

## 執筆の移行
- `memo/theory.md` を `sections/theory.tex` に反映。
- `memo/project.md` の「データ取得/前処理/モデル/結果」を Data/Methods/Models/Results へ移行。

## 注意
- arXiv は標準 TeX パッケージのみ。特殊クラスや外部フォントは避けてください。
- 画像は PDF/EPS/PNG を推奨（ベクタは PDF が望ましい）。
