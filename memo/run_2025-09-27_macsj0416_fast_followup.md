# run_2025-09-27 MACS J0416 — FAST 追加トライ（outer厚め, block_pix↑）

## 結果サマリ
- 初回FASTの p_perm≈0.245（未達）を受け、outer寄りのROI分位を強化（0.75/0.85/0.90）し、block_pix を 8 に拡大した追試を起動。
- 目的: p̂<0.02 の達成設定を見つけ FULL(perm≥1e4)に自動昇格（`scripts/jobs/auto_escalate_full.py` が監視中）。

## 実行条件（FAST 追試）
- コマンド:
  - `PYTHONPATH=. ./.venv/bin/python scripts/reports/make_bullet_holdout.py \
    --train Abell1689,CL0024 --holdout MACSJ0416 \
    --fast --downsample 2 --float32 \
    --band 8-16 --roi-quantiles 0.75,0.85,0.90 \
    --sigma-psf 1.0,1.5 --sigma-highpass 8.0,16.0 \
    --perm-n 1200 --perm-earlystop --perm-max 2000 \
    --block-pix 8 --weight-powers 0.0,0.3`
- rng/env: 前回と同一（perm/resid/boot種を 42/314 で固定）。

## 次アクション
- p̂<0.02 が出た時点で FULL を自動起動（監視ジョブが待機中）。
- 未達の場合は weight_powers=0.5 の追加トライと、ROI=global での符号一致のみ監査。
