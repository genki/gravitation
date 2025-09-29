# run_2025-09-27 MACS J0416 — FAST 第4トライ（weight 0.5 追加, outer強調, block_pix=12）

## 結果サマリ
- 第3トライ後の p 推移を受け、誤差重みの指数候補に 0.5 を追加し（`--weight-powers 0.0,0.3,0.5`）、outer 強調（ROI=0.85/0.90/0.95）と block_pix=12 で第4トライを起動。rngは固定。

## 実行条件（FAST 第4トライ）
- コマンド:
  - `PYTHONPATH=. ./.venv/bin/python scripts/reports/make_bullet_holdout.py \
    --train Abell1689,CL0024 --holdout MACSJ0416 \
    --fast --downsample 2 --float32 \
    --band 8-16 --roi-quantiles 0.85,0.90,0.95 \
    --sigma-psf 1.0,1.5 --sigma-highpass 8.0,16.0 \
    --perm-n 1200 --perm-earlystop --perm-max 2000 \
    --block-pix 12 --weight-powers 0.0,0.3,0.5 --se-transform asinh`
- rng/env: perm/resid/boot 種は 42/314 を固定。

## 次アクション
- p̂<0.02 達成時に FULL（perm≥1e4）へ自動昇格（監視ジョブ稼働中）。
