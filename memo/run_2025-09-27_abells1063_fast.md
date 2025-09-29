# run_2025-09-27 Abell S1063 — FAST（outer優先, rng固定）

## 結果サマリ
- Abell S1063 のホールドアウトFASTを、整合条件（WCS/PSF/誤差床/ROI/バンド）と固定rngでバックグラウンド起動。
- 目的: p̂<0.02 の設定を抽出し、FULL(perm≥1e4)へ自動エスカレート。

## 実行条件（FAST）
- コマンド:
  - `PYTHONPATH=. ./.venv/bin/python scripts/reports/make_bullet_holdout.py \
    --train Abell1689,CL0024 --holdout AbellS1063 \
    --fast --downsample 2 --float32 \
    --band 8-16 --roi-quantiles 0.70,0.80,0.85 \
    --sigma-psf 1.0,1.5 --sigma-highpass 8.0,16.0 \
    --perm-n 1200 --perm-earlystop --perm-max 2000 \
    --block-pix 6 --weight-powers 0.0,0.3`
- rng/env: `BULLET_PERM_SEED=42 BULLET_BOOT_SEED=314 BULLET_SHADOW_PERM_SEED=42 BULLET_SHADOW_BOOT_SEED=314 BULLET_RESID_PERM_SEED=42 BULLET_RESID_BOOT_SEED=42`
- MEMSAFE: `OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 NUMEXPR_MAX_THREADS=1 MALLOC_ARENA_MAX=2`

## 次アクション
- p̂<0.02 を満たす設定が出たら、同条件でFULLに移行（auto_escalate_fullの対象に追加予定）。
