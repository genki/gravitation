# クラスタHO（FAST）— 1st ラウンド（2025-09-26 JST）

## 結果サマリ
- MACS J0416（FAST, perm=1200, block_pix=6）を実行：
  - ΔAICc(FDB−rot) = −3.26e4, ΔAICc(FDB−shift) = −2.36e3（達成）
  - S_shadow = 0.195, p_perm = 0.266（未達）
  - 角度核の単位平均正規化導入後、Sのスケールは安定化。ただしFAST帯域/PSF/マスク既定では有意化に至らず。
- Abell S1063（FAST, perm=1200, block_pix=6）をBG起動（進行中）。

## 生成物
- MACS J0416: `server/public/reports/cluster/MACSJ0416_holdout.{html,json}`
- 進捗ログ: `server/public/reports/cluster/MACSJ0416_progress.log`, `AbellS1063_progress.log`
- 実行ログ: `server/public/reports/logs/holdout_MACSJ0416_FAST_*.log`

## 次アクション
- MACS J0416（FAST）: mask-q=0.70/0.80/0.85 × band=8–16 × σPSF=1.0/1.5 の最小走査を増やす（現在の既定→拡張）。
- p̂<0.02 到達時に FULL（n_perm≥1e4, global+outer, bands=4–8/8–16, σ=1.0/1.5/2.0）へ昇格。
- Abell S1063 のFAST完了を待ち、S_shadowの回復度合いを評価。

実行時刻(JST): 2025-09-27 05:29:49 JST
