# ベンチ図のSVG出力追加とSOTA更新

## 結果サマリ
- ベンチ図（NGC 3198/2403）に SVG 出力とメタ埋込を追加（seed/shared_sha）。
- PNG には iTXt で同等メタを埋め込み（監査性の統一）。
- SOTA を再生成して反映（rep6統一・フォント適用・ベンチ図更新を含む）。

## 生成物
- `server/public/reports/figs/rep_ngc3198.(png|svg)`
- `server/public/reports/figs/rep_ngc2403.(png|svg)`
- `server/public/state_of_the_art/index.html`（再生成）

## 次アクション
- 必要に応じてベンチHTML内の図リンクに SVG 版を追加（軽量テキスト差分向け）。
