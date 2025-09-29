# Matplotlib CJKフォント整備（Noto Sans CJK JP 導入）

## 結果サマリ
- `NotoSansCJKjp-Regular.otf` を `assets/fonts/` に配置し、`scripts/utils/mpl_fonts.py` で優先使用されるよう登録。
- 記号フォント `NotoSansSymbols2-Regular.ttf` と `NotoSansMath-Regular.ttf` も同ディレクトリに配置（既存実装と整合）。
- 主要図版スクリプトが `use_jp_font()` を呼ぶよう調整（`plot_rep6.py`, `plot_rep_fig.py`, `make_bullet_holdout.py` 等）。
- 代表図/ベンチ/ホールドアウトの CJK グリフ欠落警告が解消されることを確認。

## 生成物
- フォント設置スクリプト: `scripts/setup_fonts.sh`（再実行可）
- フォント: `assets/fonts/NotoSansCJKjp-Regular.otf` 他
- スクリプト更新: `scripts/reports/make_bullet_holdout.py`（フォント既定の適用）

## 次アクション
- SVG の `svg.fonttype` を将来的に `none` に移行し、Webフォント(woff2)同梱を検討（別タスク）。
