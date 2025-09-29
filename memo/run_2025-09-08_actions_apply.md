# 実行メモ: 追加研究指示（2025-09-08）の即応実装

日時: 2025-09-08

## 結果サマリ

- 公開品質: rep6表の存在/必須列を site-audit に組み込み、用語ULMと対照定義の章頭固定を適用。
- ベンチ: ベースライン脚注テンプレ導入（MOND/GR+DM/FDBの共通脚注）、M/L表記の統一注記を各ベンチに追加。
- 代表6: Σ層の定義（ω_cut, H_cut, 法線）を節頭に追加し、再現メタ（names/used_ids の md5、seed）を脚注化。
- 対照検証: 回転/平行移動/等値面シャッフルの3対照を実装し、ΔAICcの中央値[IQR]と効果量dをHTML/JSONに出力。

## 生成物

- ページ: `server/public/reports/surface_vs_volumetric.html`（定義/再現メタ追加）
- ページ: `server/public/reports/control_tests.html`（二行定義、効果量d、要約）
- JSON: `server/public/reports/control_tests_summary.json`（rotate/translate/shuffle 各統計）
- テンプレ: `assets/templates/baseline_notes.md`
- 監査: `scripts/qa/run_site_audit.py`（rep6 検証拡張）

## 次アクション

- Prospective/CV/付録でも AICc/(N,k)/rχ² の行を点検し不足箇所を補強。
- 非円運動の系統補正図を別図で切り出すスクリプトを追加（棒/渦腕/ワープ/アウトフロー）。

