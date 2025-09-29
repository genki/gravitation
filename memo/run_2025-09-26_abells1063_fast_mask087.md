# 2025-09-26 — AbellS1063 FAST mask=0.87 / edge=896 試行

## 結果サマリ
- Σ_e 上位87%・edge_count=896のFASTホールドアウトは S_shadow=0.19 (p_perm=0.32) と改善はしたものの閾値未達。
- ΔAICc(FDB−rot)=-1.11×10⁵, ΔAICc(FDB−shift)=-1.30×10⁴ は維持。

## 実施内容
- コマンド:
  ```bash
  PYTHONPATH=. ./.venv/bin/python scripts/reports/make_bullet_holdout.py \
    --train Abell1689,CL0024 --holdout AbellS1063 --fast \
    --sigma-psf 1.0,1.5 --sigma-highpass 0.8,1.0,1.2 \
    --roi-quantiles 0.82,0.87,0.92 --perm-n 1200 --perm-min 600 --perm-max 2000 \
    --perm-earlystop --block-pix 6
  ```
  環境変数: `BULLET_MASK_Q=0.87`, `BULLET_SHADOW_SE_Q=0.73`, `BULLET_SHADOW_EDGE_QS=0.73,0.81,0.89`, `BULLET_EDGE_COUNT=896`, `BULLET_WEIGHT_POWERS=0.0`。

## 生成物
- `server/public/reports/AbellS1063_holdout.html`
- `server/public/reports/cluster/AbellS1063_progress.log`

## 次アクション
- edge_count=768ベースで mask 0.83–0.88 を細分化し、outer p_perm<0.02 を狙う（weight=0 固定）。
- 有望設定が得られたら FULL（n_perm≥1e4, band 4–8/8–16, global+outer）で確証。
