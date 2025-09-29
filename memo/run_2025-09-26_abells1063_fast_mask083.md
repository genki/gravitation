# 2025-09-26 — AbellS1063 FAST mask=0.83 / edge=768 試行

## 結果サマリ
- mask=0.83, edge_count=768 の FAST ホールドアウトで S_shadow=0.276 (outer=0.297)・p_perm=0.179 を維持。目標の p<0.02 には未達。
- ΔAICc 優位（rot: -1.11×10⁵, shift: -1.30×10⁴）は変わらず。

## 実施内容
- コマンド:
  ```bash
  PYTHONPATH=. ./.venv/bin/python scripts/reports/make_bullet_holdout.py \
    --train Abell1689,CL0024 --holdout AbellS1063 --fast \
    --sigma-psf 1.0,1.5 --sigma-highpass 0.8,1.0,1.2 \
    --roi-quantiles 0.78,0.83,0.88 --perm-n 1200 --perm-min 600 --perm-max 2000 \
    --perm-earlystop --block-pix 6
  ```
  環境変数: `BULLET_MASK_Q=0.83`, `BULLET_SHADOW_SE_Q=0.72`, `BULLET_SHADOW_EDGE_QS=0.72,0.80,0.88`, `BULLET_EDGE_COUNT=768`, `BULLET_WEIGHT_POWERS=0.0`。

## 生成物
- `server/public/reports/AbellS1063_holdout.html`
- `server/public/reports/cluster/AbellS1063_progress.log`

## 次アクション
- mask 0.83–0.85 で edge_count 768/832 を組み合わせ、outer p_perm<0.02 を目指す微調整を継続。
- FAST で候補を得たら FULL (band 4–8/8–16, σ_psf=1.0/1.5/2.0, n_perm≥1e4, global+outer) に昇格して確証。
