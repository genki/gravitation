# rep6 読み込みエラー修正（アセット配置と相対パス）

## 結果サマリ
- 原因: rep6図の参照が `assets/rep6/...`（リポジトリ相対）になっており、Webルート `server/public/` から解決できず 404。
- 対応: 
  - `make rep6` に発行時コピーを追加し、`assets/rep6/*.(png|svg)` を `server/public/assets/rep6/` に展開。
  - インジェクタ `scripts/reports/inject_rep6_figs.py` を修正し、HTMLの `<img src>` をページ位置からの相対で `../assets/rep6/...` に自動変換（Webルート配下のみ参照）。
- 検証: `server/public/reports/ws_vs_phieta_rep6.html` と `server/public/state_of_the_art/index.html` の rep6 図が正常に表示。

## 生成物
- 更新: `Makefile`（rep6ターゲットで発行コピー）
- 更新: `scripts/reports/inject_rep6_figs.py`（Webルート相対での `<img src>` 生成）
- 配置: `server/public/assets/rep6/*.png, *.svg`

## 次アクション
- rep6 サイドカーJSONの配信要否（監査用DL）を検討（必要なら `.json` もコピー対象に追加）。
