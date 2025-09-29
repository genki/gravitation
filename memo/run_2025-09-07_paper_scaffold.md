# 論文化（arXiv/HTML単一ソース）スキャフォールド構築

## 結果サマリ
- Quarto/Pandocベースの単一ソース構成を整備。`paper/paper.qmd`（本文）から **HTML** と **PDF** をビルドできる構成（Pandoc/LaTeX未導入環境ではスキップし通知）。
- SOTAの数値（共有 μ(k), ΔAICc, N, k, 指紋）を `scripts/paper/generate_vars.py` で集約し、`paper/_variables.yml` に出力し本文へ自動流し込み。
- Makeターゲット: `paper-vars`, `paper-html`, `paper-pdf`, `arxiv-pack`, `paper-all` を追加。

## 生成物
- paper/quarto.yml, paper/preamble.tex, paper/paper.qmd, paper/refs.bib
- scripts/paper/generate_vars.py
- Makefile: 上記 paper-* ターゲット
- 出力例（環境にPandoc/Quarto未導入のためスキップメッセージで保留）: paper/dist/arxiv-src.zip（雛形同梱）

## 次アクション
- ビルド環境に Quarto または Pandoc+LaTeX を導入（ローカル/CI）。
- 図表: 代表図・ベンチ・ヌル/感度のPNG/SVGを適宜差し替え（paper/figures を共用）。
- 章立て本文の肉付け（qmd内の各セクションにドラフト移植）。

## 備考
- 変数は `data/shared_params.json` と `data/results/cv_shared_summary.json` から自動抽出。fingerprintとしてsha12を本文に記載し再現性を担保。
