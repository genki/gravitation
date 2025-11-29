# 2025-11-29 main.md/main.ja.md アップデートメモ

## 追加・修正点
- 英語版 `main.md` に以下を追加/整理
  - **§2.3 Informing tensor**: ULE-EM 前縁グリーン関数＋TT射影で定義し、波セクターが GR と同型であることを明記。
  - **§7.1 GR–FDB compatibility (wave sector)**: 速度=c、偏極=スピン2のみ、四重極公式一致を箇条書きで整理。
  - **§9.1 Scope/limitations**: 射程（銀河〜宇宙網）、扱わない領域（SM/インフレ等）、未解決課題を列挙。
- 日本語版 `main.ja.md` に対応する小節を追加
  - **3.4 インフォーミング・テンソル**、**5.4 重力波セクターの整合**、**13.1 射程と限界・未解決課題**。
  - 重複していた宇宙年齢の記述を整理。
- 用語揺れを解消：Wiki では ULW-EM→**ULE-EM** に統一（既存 wiki master `107f777`）。
- README 冒頭に「最新 PDF (main.pdf / main.ja.pdf) は Release latest から取得可能」を追記し、ライセンス文言を微調整。

## 影響範囲
- `main.md`, `main.ja.md`, `README.md`
- Wiki は別途 ULW→ULE の統一済み（コード本文とは独立）。

## 残課題
- CITATION.cff / ライセンスファイル分割（CC-BY-4.0 + MIT）の確定は未着手。
- cosmology/σ8/H0 同時フィットや Γ(x) 微視的導出は今後の研究項目のまま。
- 11/30: FDB-Glossary wiki math修正（informing tensorブロックを$$対応、単位s^-1とAICc下線のエスケープ、σ表記整理）check-math合格
- 11/30: Wiki HomeとFDB-Math-Notesの数式をGitHub形式に修正、check-math全ページ合格
- 11/30: wiki math運用のベストプラクティスを memo/wiki-math.md に整理・コミット
- 11/30: Issues #5 (GW速度=c) と #14 (スピン2偏極) はFDB定義上既に満たされるためコメント付与しクローズ
