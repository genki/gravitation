# FASTスイープ（ラウンド2）— von Mises角度核の適用（2025-09-27 JST）

## 結果サマリ（暫定）
- 角度核を von Mises（κ×χスケール）に変更し、outer重視のFAST探索を実施。
- MACS J0416（perm=1200, earlystop）: S_shadow(outer)=+0.316, p=0.509（未達、増幅はあるが有意化せず）。
- Abell S1063（perm=1200, earlystop）: S_shadow(outer)=+0.440, p=0.240（未達、符号は正に回復）。
- 角度核の単位平均正規化により、Sのスケールは安定（>1逸脱なし）。

## 生成物
- 更新: `server/public/reports/cluster/MACSJ0416_holdout.{html,json}`
- 更新: `server/public/reports/cluster/AbellS1063_holdout.{html,json}`
- 進捗/実行ログ: `server/public/reports/cluster/*_progress.log`, `server/public/reports/logs/holdout_*_FAST_*.log`

## 次アクション（ラウンド3, FAST）
- 外縁重視の更なる絞り込み（outer r≥r75）:
  - rr_quantile: 0.80→0.90 を追加（高エッジ選好を強化）
  - ROI: q=0.85 を追加
  - block_pix: 6→8 を試行（N_effに合わせたブロック拡大）
  - band: 4–8 / 8–16 を並行
- 目標: FAST で p̂<0.02 を検出次第、自動で FULL (n_perm=1e4) にエスカレーション。


実行時刻(JST): 2025-09-27 06:13:43 JST
