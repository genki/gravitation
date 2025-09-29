# 実行メモ: 代表6再計算と対照検証（2025-09-08）

日時: 2025-09-08

## 結果サマリ

- 代表6（Σ vs 体積）を同一誤差・同一 (N,k) で再計算し、AICc/(N,k)/rχ²/ΔAICc/勝率・md5 を表に集約。
- 対照検証（回転/平行移動＋Hα派生）は要約統計（ΔAICc中央値[IQR], 効果量d, 試行数）を図表化。
- SOTAトップにリンク（代表6・対照）を掲出し、共有ハイパーの単一ソースと整合。

## 生成物

- 表: `server/public/reports/surface_vs_volumetric.html`（rep6; AICc/(N,k)/rχ²/ΔAICc/勝率/md5）
- 対照: `server/public/reports/control_tests.html`, `control_tests_box.png`,
  `server/public/reports/control_halpha_tests.html`
- Make: `rep6-recalc`, `controls`（別名: `ctrl-tests`）ターゲットを追加。

## 次アクション

- 代表6の名称セット/マスク定義を本文脚注に明記（rep6.txt の md5 を併記）。
- Prospective/CV/ベンチの rχ² ラベルを横断で点検（UI残差を除去）。

