# 2025-09-26 — AbellS1063 FAST 外側重点マスク試行

## 結果サマリ
- Σ_e 上位 85% 領域に限定し、edge_count=768 / Σ量子 0.72 を採用した FAST ホールドアウトで **S_shadow=0.276 (outer=0.297)** に上昇。
- permutation を 2000 本まで回しても **p_perm=0.179**（基準未達）。Rayleigh 検定は p=5.0×10⁻⁴、V-test は p=1.4×10⁻² まで改善。
- AICc 差は維持（ΔAICc(FDB−rot)=-1.11×10⁵, ΔAICc(FDB−shift)=-1.30×10⁴）。

## 実施内容
- マスクを `BULLET_MASK_Q=0.85` で固定し、`BULLET_SHADOW_SE_Q=0.72`、`BULLET_SHADOW_EDGE_QS=0.72,0.80,0.88`、`BULLET_EDGE_COUNT=768` を指定。
- 高通過 σ を 0.8/1.0/1.2 pix でスイープ、重み指数は `w=Σ_e^0` のみに制限。
- コマンド:
  ```bash
  PYTHONPATH=. ./.venv/bin/python scripts/reports/make_bullet_holdout.py \
    --train Abell1689,CL0024 --holdout AbellS1063 --fast \
    --sigma-psf 1.0,1.5 --sigma-highpass 0.8,1.0,1.2 \
    --roi-quantiles 0.80,0.85,0.90 --perm-n 1200 --perm-min 600 --perm-max 2000 \
    --perm-earlystop --block-pix 6
  ```

## 生成物
- `server/public/reports/AbellS1063_holdout.html`
- `server/public/reports/cluster/AbellS1063_progress.log`

## 次アクション
- outer での S_shadow 増強が確認できたため、Σ層の角度核（K(θ;χ)) と edge_count を微調整して **p_perm<0.02** を狙う（例: edge_count=896, Σ_e^0.1, mask 0.83–0.88）。
- 有望設定が得られた際は FAST→FULL（band 4–8/8–16, n_perm≥1e4）へ昇格し、SOTA へ反映する。
