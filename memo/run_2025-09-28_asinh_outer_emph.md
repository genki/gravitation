# asinh外側強調バッチの投入（scope分離）

## 結果サマリ
- AbellS1063 FULL 再開は `resid_perm` が 5.2k/10k まで進行中（ETA ≈ 86 分）。
- FAST 欠番の asinh×外側強調を 4 コンボ（MACS:4–8/8–16, Abell:4–8/8–16）で逐次投入。
- dispatcher `--scope` + メモリ制限環境で実行。tmux巻き添え・OOM再発の抑制を継続。

## 生成物
- ジョブ: `asinh_outer_emph_batch`
- ログ: `server/public/reports/logs/asinh_outer_emph_batch_*.log`
- メタ: `tmp/jobs/asinh_outer_emph_batch_*.json`

## 次アクション
- 完了後に `*_holdout.json` の p を確認し、p<0.02 があれば FULL 昇格。
- AbellS1063 FULL の完了時点で `*_holdout.json` の `shadow/resid` 双方を再点検。
- 追加候補: rr_q=0.88/0.92 と block_pix=6/8 の比較、必要に応じて投入。
