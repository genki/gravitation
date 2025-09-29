# サイト内リンクを相対パスへ統一

- 実行時刻: 2025-09-02 06:22 UTC

## 結果サマリ
- 生成スクリプトのテンプレートを修正して、CSS/JS/ナビ/画像/内部ページを相対リンク化
- 既存の静的HTML（通知/一部CVレポート）も相対リンクに修正
- 再生成後、`server/public/` 配下に絶対パス参照が残っていないことを確認（主要ページ）

## 生成物
- 更新: `scripts/build_state_of_the_art.py`, `scripts/build_galaxy_profiles_page.py`, `scripts/build_report.py`
- 更新: `scripts/cross_validate_shared.py`, `scripts/notice_to_file.sh`
- 既存HTMLを修正: `server/public/notifications/index.html`, `server/public/reports/cv_shared.html`

## 次アクション
- レポート群の残差チェック（追加で絶対参照が見つかれば同様に修正）
- MkDocs側も相対URL化が必要なら `mkdocs-relative-urls` の導入を検討
