# 用語整理: ULW → ULM（Ultra‑Long electromagnetic Mode）

## 結果サマリ
- “ULW‑EM” を “ULM（Ultra‑Long electromagnetic Mode）” に改称。分枝は ULM‑P（ω>ω_cut; propagating）/ ULM‑D（ω<ω_cut; diffusive）。
- SOTA と論文テンプレの表記を更新し、初出に “formerly ULW‑EM” を明記。
- SOTAに用語カード（ULM/ULM‑P/ULM‑Dの定義）を常設。ULW‑h/l デモのラベルも ULM‑P/D に変更（互換リンクは維持）。

## 生成物
- 更新: `scripts/build_state_of_the_art.py`（用語カード・リンク文言）
- 更新: `paper/preamble.tex`（\ulm マクロ追加）、`paper/paper.qmd`（アブストラクト/理論節）
- 参考: `scripts/paper/generate_tex.py` の出力本文は次ビルドで反映（ULM/Negative‑control に整合）

## 次アクション
- 図凡例・色凡例の ULM‑P/D 置換（該当SVG/PNGに反映）。
- CLI表記のエイリアス（`--ulm {p|d}`）追加検討（実装は互換維持のため別PRに分離）。
