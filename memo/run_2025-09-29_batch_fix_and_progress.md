# バッチ投入の修正と進捗更新（scope分離）

## 結果サマリ
- dispatcher へのコマンド引き渡しで先頭に `--` が混入していたため、二つの逐次バッチが no-op となっていた問題を修正。
- 正しい形式で再投入: `outer_emph_gap_fill2`, `asinh_outer_emph_batch2`（どちらも scope 分離 + メモリ安全環境）。
- AbellS1063 FULL(4–8, n_perm=10k) は `resid_perm` が進行中。直近ETA ≈ 21分。

## 生成物
- ジョブ: `outer_emph_gap_fill2`, `asinh_outer_emph_batch2`
- ログ: `server/public/reports/logs/outer_emph_gap_fill2_*.log`, `server/public/reports/logs/asinh_outer_emph_batch2_*.log`
- メタ: `tmp/jobs/*_20250929_*.json`
- スクリプト修正: `scripts/jobs/run_holdout_async.sh`（dispatcher 呼び出しの `--` 重複を除去）

## 次アクション
- 逐次バッチ完了後、`*_holdout.json` で p を評価し、有意 (p<0.02) なら FULL を投入（auto-escalate も稼働中）。
- AbellS1063 FULL 完了後、影・残差双方の指標を確認し、必要なら追加の FULL（8–16 帯）を検討。
