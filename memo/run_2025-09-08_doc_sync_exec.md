# 実行メモ: 用語同期（ULM/対照検証）適用（2025-09-08）

日時: 2025-09-08

## 結果サマリ

- 表示層の用語を ULW→ULM（P/D; 旧称併記）へ統一。ヌルテスト→対照検証の方針に沿う文言整理。
- docs/ と SOTA 部分テンプレを更新し、ビルドを反映。データキーや内部統計の互換は維持（ULW キーはそのまま）。

## 生成物

- 更新: `docs/volumetric_fdb/README.md`, `docs/state-of-the-art.md`,
  `docs/sota/partials/ulw_lh_glossary.html`, `docs/sota/partials/whats_new_2025Q3.html`
- SOTA: `server/public/state_of_the_art/index.html`（用語脚注を維持; 初出で旧称併記）

## 次アクション

- 細部（図ラベル/凡例）の残差確認。必要なら `assets/templates/footnotes.md` を導入し脚注を単一化。
- 指標の恒常化を代表6/対照検証の表作成と合わせて適用。

