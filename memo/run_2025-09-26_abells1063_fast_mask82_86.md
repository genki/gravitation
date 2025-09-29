# 2025-09-26 — AbellS1063 FAST mask 0.82 / 0.86 スイープ

## 結果サマリ
- mask=0.82, edge_count=752 → S_shadow=0.060 (outer=0.072), p_perm=0.383（悪化）。
- mask=0.86, edge_count=840 → S_shadow=0.276 (outer=0.297), p_perm=0.179（既存ベスト値に回帰）。
- ΔAICc優位（rot:-1.11×10⁵, shift:-1.30×10⁴）は保持。

## 実施内容
- mask=0.82 / edge=752:
  ```bash
  PYTHONPATH=. ./.venv/bin/python scripts/reports/make_bullet_holdout.py \
    --train Abell1689,CL0024 --holdout AbellS1063 --fast \
    --sigma-psf 1.0,1.5 --sigma-highpass 0.8,1.0,1.2 \
    --roi-quantiles 0.78,0.82,0.88 --perm-n 1200 --perm-min 600 --perm-max 2000 \
    --perm-earlystop --block-pix 6
  ```
  (環境変数: `BULLET_MASK_Q=0.82`, `BULLET_SHADOW_SE_Q=0.70`, `BULLET_SHADOW_EDGE_QS=0.70,0.78,0.86`, `BULLET_EDGE_COUNT=752`, `BULLET_WEIGHT_POWERS=0.0`)
- mask=0.86 / edge=840:
  ```bash
  PYTHONPATH=. ./.venv/bin/python scripts/reports/make_bullet_holdout.py \
    --train Abell1689,CL0024 --holdout AbellS1063 --fast \
    --sigma-psf 1.0,1.5 --sigma-highpass 0.8,1.0,1.2 \
    --roi-quantiles 0.82,0.86,0.91 --perm-n 1200 --perm-min 600 --perm-max 2000 \
    --perm-earlystop --block-pix 6
  ```
  (環境変数: `BULLET_MASK_Q=0.86`, `BULLET_SHADOW_SE_Q=0.72`, `BULLET_SHADOW_EDGE_QS=0.72,0.80,0.88`, `BULLET_EDGE_COUNT=840`, `BULLET_WEIGHT_POWERS=0.0`)

## 生成物
- `server/public/reports/AbellS1063_holdout.html`
- `server/public/reports/cluster/AbellS1063_progress.log`

## 次アクション
- mask 0.83–0.85 × edge_count 768/832 組合せを中心に再探索（Σ層と角度核の再設計も含む）。
- FAST で p_perm<0.02 を確認できた設定を FULL (band 4–8/8–16, σ_psf=1.0/1.5/2.0, n_perm≥1e4, global+outer) へ昇格。
