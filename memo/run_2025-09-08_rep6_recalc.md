# 実行メモ: 代表6（Σ vs 体積）— 実測再計算・公開

日時: 2025-09-08

## 結果サマリ

- 代表6（DDO154, DDO161, NGC2403, NGC3198, NGC7331, UGC06787）について、同一誤差モデル・同一 (N,k) で **Σ（界面） vs 体積版（ULM）** を再計算し、表を公開。
- 勝率（定義: ΔAICc<0 を Surface 勝ち）: Surface=2 / Volumetric=4（勝率=0.33）。
- ΔAICc(S−V) の要約: 中央値=133.1, IQR=1556.3（本日の実行出力）。
- 表には per‑galaxy の AICc, rχ², (N,k), ΔAICc, ΔELPD を併記。脚注に **names md5** と **結果JSON md5** を追記し、再現性を補強。

## 生成物

- ページ: `server/public/reports/surface_vs_volumetric.html`
- 結果JSON: `data/results/rep6_surface.json`, `data/results/rep6_volumetric.json`
- スクリプト更新: `scripts/reports/compare_surface_vs_volumetric.py`（ULM表記・勝率/中央値/IQR追加・md5脚注）

## 次アクション

- [検証] DDO161, NGC7331 で Surface 側の AICc が極端に大きい件を点検（誤差床・line_eps・正則化の適正を再確認）。
- [整備] SOTA本文に代表6の定義と勝率の定義（ΔAICc<0）を固定表示（現状カードリンクあり）。
- [公開] 代表6のスナップショットを paper 図版に反映（簡易表 or 参照リンク）。

