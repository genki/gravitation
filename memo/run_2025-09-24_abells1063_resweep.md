# run_2025-09-24_abells1063_resweep

## 結果サマリ
- Bullet HO の固定化状況を確認し、S_shadow=0.378, p_perm=0.00225, ΔAICc(rot/shift)=(-6.79e7, -6.74e6) など指示基準を満たしていることを再確認した。
- AbellS1063 の前回ホールドアウト結果を整理し、StageResumeメタ (`shadow_perm/resid_perm`) をクリアして再走査の準備を整えた。
- `BULLET_PERM_N=12000` 等を指定し、mask_q∈{0.70,0.75,0.80}, σ_highpass∈{0.7,1.0,1.5,2.0}, σ_psf∈{1.0,1.5,2.0}, w∈{0,0.3,0.7} の sweep をバックグラウンド実行開始（PID 570170, ログ `logs/abells1063_scan_mask70.log`）。shadow permutation は n=12,000, block_pix=6 で進行中。

## 生成物
- ログ: `logs/abells1063_scan_mask70.log`
- 更新: `server/public/reports/cluster/AbellS1063_holdout.json`（再生成後に確認予定）
- メモ: 本ファイル

## 次アクション
1. バックグラウンドジョブの進捗を定期確認し、完了後に S_shadow と p_perm, ΔAICc を再評価。
2. 必要に応じて mask 分位 0.80 や block_pix=8 等の追加組み合わせを投入し、有意性確保を優先。
3. 成果が得られた時点で `make sota-refresh` を実施し、SOTA/KPI へ同期。
