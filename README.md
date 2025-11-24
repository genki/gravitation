# Gravitation Research Repository

このリポジトリは「Future Determination Bias (FDB)」仮説を中心にした重力研究用の単一ソース・ペーパー一式を収めています。pandoc で Markdown→LaTeX/PDF にビルドし、図・計算スクリプト・入力データをすべて同一ディレクトリツリーで完結させました。公開後は https://github.com/genki/gravitation から取得できます。

## ディレクトリ構成

| パス | 内容 |
|------|------|
| `main.md` | 論文本文（pandoc/LaTeX 変換用 Markdown）。 |
| `figures/` | 掲載図 (`.png`)。 |
| `build/` | `make pdf`/`make tex` の出力（PDF/TeX/CSV）。 |
| `src/analysis/` | 再現スクリプト（例: `h1_ratio_test.py`, `sparc_fit_light.py`）。 |
| `src/scripts/` | 解析ラッパー（例: `sparc_sweep.py`）。 |
| `data/strong_lensing/` | SLACS/BELLS/S4TM/BOSS などの機械可読レンズ表。 |
| `data/sparc/` | SPARC MRT・rotmod データ。 |
| `table2_aicc.md`, `appendix_f_h1.md` | 表・付録の補助 Markdown。 |
| `memo/` | 作業メモ（旧ドラフトディレクトリの経緯・手順を含む）。 |

## ビルド方法

```bash
python3 -m venv .venv
. .venv/bin/activate
pip install -r requirements.txt  # pandoc/xelatexは別途インストール
make pdf   # build/main.pdf を生成
make tex   # build/main.tex を生成
```

`make pdf` は pandoc + xelatex を使用するので、TeX Live (>=2023) を推奨します。

## 再現手順（概要）

- **強レンズ H1 比テスト**  
  `src/analysis/h1_ratio_test.py` が `data/strong_lensing/` の CSV を読み込み、Table 1 と Figure 2 を再生成します。  

- **SPARC 回転曲線 & BTFR**  
  `src/scripts/sparc_sweep.py` → `src/analysis/sparc_fit_light.py` で Table 2・Figure 3–4 を再計算 (`build/sparc_aicc.csv` へ書き出し)。

- **補助ファイル**  
  `appendix_f_h1.md` や `table2_aicc.md` などの Markdown 片は pandoc が自動で本文に組み込みます。

詳細なコマンド列は Appendix G と “Data and code availability” 節、ならびに `memo/*.md` を参照してください。

## ライセンス / 引用

論文テキストと図は CC-BY-4.0 を予定。コードとスクリプトは MIT 互換ライセンスを想定しています。利用時は ``main.md`` の引用規定と refs.bib に記載した一次文献に従ってください。
