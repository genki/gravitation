# run_2025-09-27 Abell S1063 — FAST 追試（outer厚め, asinh, block_pix=8）

## 結果サマリ
- 初回FASTの p を受け、ROI分位を outer 寄り（0.75/0.85/0.90）に強化、`--se-transform asinh` と block_pix=8 を導入した追試を起動。

## 実行条件（FAST 追試）
- コマンド:
  - `PYTHONPATH=. ./.venv/bin/python scripts/reports/make_bullet_holdout.py \
    --train Abell1689,CL0024 --holdout AbellS1063 \
    --fast --downsample 2 --float32 \
    --band 8-16 --roi-quantiles 0.75,0.85,0.90 \
    --sigma-psf 1.0,1.5 --sigma-highpass 8.0,16.0 \
    --perm-n 1200 --perm-earlystop --perm-max 2000 \
    --block-pix 8 --weight-powers 0.0,0.3 --se-transform asinh`

## 次アクション
- p̂<0.02 達成で FULL（perm≥1e4）に自動移行（監視ジョブは起動済み）。
