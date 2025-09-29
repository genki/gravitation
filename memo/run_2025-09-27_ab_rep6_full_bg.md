# run_2025-09-27 A/B代表比較（FULL）自動実行スケジュール

## 結果サマリ
- FAST完了検知後に、同一条件（rng=42, k=2, hipass=4–8/8–16, psf=1.0/1.5/2.0, errfloor=0.03,3,7, float64）でFULLを実行するBGジョブを登録しました。
- 実行順: WS → Φ·η → 代表6HTML生成 → SOTA再生成。ログは server/public/reports/logs/ に保存します。

## 生成物（完了時）
- data/results/rep6_ws_full.json, data/results/rep6_phieta_full.json
- server/public/reports/ws_vs_phieta_rep6.html（脚注: rng/sha/cmd 固定、ΔAICc整合チェック内蔵）

## 次アクション
- NGC 3198 の Φ·η best（β=0.30, s=0.40, σ_k=0.80）で ΔAICc≈−10.6 の再現を確認（|Δ(ΔAICc)|≤5, 符号一致）。
- 代表6の表における各銀河の ΔAICc 整合（公平スイープ基準）を監査。
- PSF畳込み/高通過の実装を核計算に反映（現状は条件固定・脚注提示）。
