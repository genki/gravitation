# SOTAレビュー対応（第1弾）— 通知リンク撤去・代表6再計算・Prospective注記・ロバスト性数値化

## 結果サマリ
- SOTAから「通知ログ」リンクと監査依存を撤去。監査カードは used_ids 等のリンク到達性のみ評価に変更。
- 代表6（Σ vs 体積版）を同一誤差モデル・同一 (N,k) で再計算。表に N・k・ΔAICc（S−V）・script md5 を併記し体裁統一。
- Prospectiveページに「診断用（フェア比較からは除外）」の注記を追加（rχ²が極小の場合に自動警告）。
- n_e撹乱ヌルテストと誤差床/H_cut感度ページに数値要約を追記（|F|の各ケース、ΔAICc≤2の許容域）。

## 主要変更点
- 更新: `scripts/build_state_of_the_art.py`（通知リンク除去、監査文言/判定の更新）
- 更新: `scripts/qa/audit_links.py`, `scripts/qa/audit_http.py`（通知関連の監査対象から除外）
- 更新: `scripts/reports/compare_surface_vs_volumetric.py`（誤差床とN,k整合、表にN/k/ΔAICc説明、md5脚注）
- 更新: `scripts/prospective_eval.py`（極小rχ²時の診断注記）
- 更新: `scripts/reports/make_ne_perturbation_report.py`（|F|数値要約）
- 更新: `scripts/reports/make_sensitivity_radar.py`（最適域=ΔAICc≤2の列挙、最良組の明示）
- 生成: `server/public/reports/surface_vs_volumetric.html`, `server/public/reports/prospective.html`（再出力）

## 次アクション
- 代表6の名称セット/マスク定義をREADMEに明記（rep6.txt）。
- Prospectiveのrχ²が過小となる要因分析（誤差相関・外縁マスク・モデル拘束の見直し）を別メモで実施。
- NGC2403 の Hα 等高線オーバーレイ（FITS入手後に自動生成）を確認。

## 参照
- SOTA: `server/public/state_of_the_art/index.html`
- 比較: `server/public/reports/surface_vs_volumetric.html`
- Prospective: `server/public/reports/prospective.html`
- ロバスト性: `server/public/reports/ne_null_ngc3198.html`, `server/public/reports/sensitivity_ngc3198.html`
