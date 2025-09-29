# TODOメモ — Matplotlib CJK フォント整備

## 背景
- `make_bullet_holdout.py` 実行時に CJK グリフ（例: 固定, 測, パラ）のレンダリング警告が多数発生。現在のフォント優先リストに Noto Sans Symbols2 は登録済みだが、CJK 本体 (Noto Sans CJK JP) がランタイム環境に存在しない可能性が高い。
- 図版に含まれる日本語文言、カタカナ、全角括弧がアウトライン化されず、PNG 出力で欠落するリスクがある。

## 対応方針
1. Noto Sans CJK JP の OTF を `assets/fonts/` に同梱し、`scripts/utils/mpl_fonts.py` で `addfont` 登録する。
2. `matplotlib.font_manager` のキャッシュを再生成し、`font.sans-serif` 優先順位を `Noto Sans CJK JP` → `Noto Sans Symbols2` → fallback の順に整理。
3. ビルド後に `grep 'Glyph ... missing'` で警告が消えることを確認し、SOTA など主要レポートを再生成。

## 参照
- 発生ログ: `server/public/reports/Bullet_holdout.html` 生成時の stdout、`run_2025-09-25_fdb_volume_prep.md`

## 次アクション
- フォント同梱後、既存 PNG/SVG を再生成し、差分をレビューする。
