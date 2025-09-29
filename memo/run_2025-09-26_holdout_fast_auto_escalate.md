# FAST→FULL自動エスカレーション監視の導入（2025-09-26 JST）

## 結果サマリ
- FASTホールドアウト（MACS J0416/Abell S1063）の **p<0.02** を自動監視し、到達時に **FULL (n_perm=1e4, bands=4–8/8–16, σ=1.0/1.5/2.0, roi-q=0.70/0.80/0.85)** を起動する監視スクリプトを追加。
- 監視はBG実行（20s間隔, timeout=20min）。ログは reports/logs/ に保存。

## 生成物
- 新規: `scripts/jobs/auto_escalate_full.py`（監視＋エスカレーション）
- 起動: `nohup PYTHONPATH=. scripts/jobs/auto_escalate_full.py --holdouts MACSJ0416,AbellS1063 --interval 20 --timeout 1200 &`
- 依存ログ: `server/public/reports/cluster/*_holdout.json`（p値参照）、`server/public/reports/logs/holdout_*_FULL_*.log`（FULL実行ログ）

## 次アクション
- 監視によりFULLが起動されたら、完了後に `make sota-refresh` を実施し、SOTAへ反映＋通知。
- pが閾値未達の場合、FAST探索の帯域/マスク/σPSFの組み合わせを追加スイープ（outer強化→global 追加）

実行時刻(JST): 2025-09-27 06:02:26 JST
