# run_2025-09-27 MACS J0416 — FAST 第3トライ（asinh圧縮, outer強調, block_pix=10）

## 結果サマリ
- 2nd FAST 追試に続き、Σ_e の動的レンジ圧縮（`--se-transform asinh`）と outer 強調（ROI=0.80/0.90/0.95）、block_pix=10 を適用した第3トライを起動。
- 目的: p̂<0.02 を達成し FULL（perm≥1e4）へ自動昇格（監視ジョブ稼働中）。

## 実行条件（FAST 第3トライ）
- コマンド:
  - `PYTHONPATH=. ./.venv/bin/python scripts/reports/make_bullet_holdout.py \
    --train Abell1689,CL0024 --holdout MACSJ0416 \
    --fast --downsample 2 --float32 \
    --band 8-16 --roi-quantiles 0.80,0.90,0.95 \
    --sigma-psf 1.0,1.5 --sigma-highpass 8.0,16.0 \
    --perm-n 1200 --perm-earlystop --perm-max 2000 \
    --block-pix 10 --weight-powers 0.0,0.3 \
    --se-transform asinh`
- rng/env: perm/resid/boot 種は 42/314 を固定（前回同様）。

## 次アクション
- p̂<0.02 が出たら FULL に自動移行。未達の場合は `--weight-powers 0.0,0.3,0.5` を追加して第4トライを検討。
