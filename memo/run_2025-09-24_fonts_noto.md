# run_2025-09-24_fonts_noto

## 結果サマリ
- CJK文字が欠落していたため、`fonts-noto-cjk` と `fonts-noto-core`（依存で `fonts-noto-mono`）を apt 経由で導入し、`~/.cache/matplotlib` を削除してフォントキャッシュを再構築。
- `PYTHONPATH=. python scripts/build_report.py` と `scripts/build_state_of_the_art.py` を再実行し、レポート／SOTA の図版を新フォントで再生成。
- テストとして `tmp/test_font.png` を出力し、日本語・全角記号のレンダリングが成功することを確認。

## 生成物
- システムフォント: Noto Sans CJK/Mono/Core（`/usr/share/fonts/truetype/noto/`）
- キャッシュ再構築: `~/.cache/matplotlib`（再生成）
- テスト出力: `tmp/test_font.png`
- 更新: `server/public/reports/*`, `paper/figures/tri_compare_*.svg`, `server/public/state_of_the_art/index.html`

## 次アクション
1. 進行中の `make_bullet_holdout` 実行（AbellS1063 sweep）が完了したら、必要に応じて再実行し最終レポートを新フォントで上書きする。
2. 図中の文字化けが解消されたか目視確認し、必要なら追加の図版を個別に再生成する。
