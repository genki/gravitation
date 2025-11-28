# 2025-11-28 GitHub Wiki 数式レンダリング対応メモ

## やったこと
- FDB-chi ウィキページの数式表記を GitHub Wiki 制約に合わせて再整形し、未レンダリング箇所を解消。
- `check-math.js` を強化し、`mathcolor="red"` で表示される MathML エラーを検出・スニペット表示できるようにした（`math-renderer` 内の `<template>` も走査）。
- 未検出だった `\sigmav` 表記を `$\\langle\sigma v\\rangle$` に修正し、Wiki を更新。

## GitHub Wiki 数式ルール（再確認）
- インライン: `$...$` 内部・外部ともに空白なし（`$ \alpha $` は不可）。
- ブロック: `$$` は単独行、前後に空行を置く。1 行に収めると崩れにくい。
- KaTeX 置換後でも `mathcolor="red"` が残る場合は未解釈 LaTeX の可能性大。

## チェック方法
- `node scripts/check-math.js <url>`  
  - 未レンダリングの `$`, `$$`, `\\frac`, `\\(...\\)` を検出。
  - `mathcolor="red"` を含む MathML を抽出し、問題スニペットを表示。
- 実行結果（最新）：`https://github.com/genki/gravitation/wiki/FDB-chi` で未レンダリング・赤表示とも検出なし。

## 変更点
- Main repo: `scripts/check-math.js` を改修（コミット `cf0ee42` 済）。
- Wiki repo: `FDB-chi` の `\langle\sigmav\rangle` を `\langle\sigma v\rangle` に修正（コミット `a6149a4` 済）。

## 今後の運用
- Wiki 数式修正後は必ず `check-math.js` を回し、`mathcolor="red"` が 0 件になることを確認。
- 新規数式追加時は上記ルールを徹底し、外部ツール貼り付け時は空白混入・ハイフン直前の `$` に注意。
