# 実行メモ: ベースライン脚注・M/L表記統一・CI監査拡張（2025-09-08）

日時: 2025-09-08

## 結果サマリ

- ベースライン脚注テンプレ（assets/templates/baseline_notes.md）を作成し、NGC 3198/2403 ベンチページへ注入。
- M/L表記の統一注記（ASCII: ML_*／論文: \(\Upsilon_\*\)）を両ベンチに明記。
- CI監査（site-audit）を拡張し、rep6表（surface_vs_volumetric.html）の必須列（AICc/rχ²/ΔAICc）の存在を検証。

## 生成物

- テンプレ: assets/templates/baseline_notes.md
- 更新: scripts/benchmarks/run_ngc3198_fullbench.py, scripts/benchmarks/run_ngc2403_fullbench.py
- 監査: scripts/qa/run_site_audit.py（rep6 検証追加）

## 次アクション

- Hα 等高線オーバーレイの完全自動化確認（3198/2403）と脚注テンプレの微調整（c–M事前の有無をページ種別で切替）。
- CI: 合計χ²/(N,k)/AICc の単一ソース一致チェックを audit_consistency 側に拡張。

