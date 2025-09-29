# 実行メモ: Quick Wins（用語刷新・リンク監査・Prospective整備）

日時: 2025-09-08

## 結果サマリ

- リンク監査を実行し、`used_ids.csv` / `cv_shared_summary.html` / `notifications/` のHTTP 200到達を確認。SOTAに監査OKバッジを再掲（自動判定）。
- 用語刷新（サイト表示）: ULW→ULM、ヌル→対照検証。Prospective/太陽系節の見出し・本文を更新。
- Prospective ページを再生成し、AICc/(N,k)/rχ² を恒常表示。誤差床の式 `clip(0.03×Vobs, 3..7 km/s)` を明記。極小 rχ² 時は「診断用」注記を自動付与。

## 生成物

- ページ: `server/public/state_of_the_art/index.html`（監査OKバッジ/見出し更新）
- ページ: `server/public/reports/prospective.html`（ULM表記・AICc/(N,k)/rχ²・誤差床注記）
- 監査: `server/public/state_of_the_art/audit.json`（ok=true; http 200=all true）
- スクリプト更新: `scripts/prospective_eval.py`, `scripts/build_state_of_the_art.py`

## 次アクション

- 代表6（Σ vs 体積）の実測再計算を着手（AICc/(N,k)/rχ²/ΔAICc/勝率/md5を整備）。
- SOTA本文に「勝率＝ΔAICc<0」の定義とベースライン脚注テンプレを恒常化。
- Hα 等高線の自動オーバーレイを NGC 3198/2403 に適用し、外縁 1/r² の傾き＋95%CI を脚注化。

