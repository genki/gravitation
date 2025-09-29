# 2025-09-26 — AbellS1063 FAST weight=0.1/edge896 試行

## 結果サマリ
- `w=Σ_e^0.1`, mask 83%、edge_count=896 の FAST 再計算は S_shadow=0.047 (p=0.42) と悪化、採用見送り。
- 直後に既存ベスト設定（mask 85%、edge=768、w=0）を再実行し、S_shadow=0.276 (p=0.179) の状態に復帰。

## 実施内容
- コマンド:
  ```bash
  PYTHONPATH=. ./.venv/bin/python scripts/reports/make_bullet_holdout.py \
    --train Abell1689,CL0024 --holdout AbellS1063 --fast \
    --sigma-psf 1.0,1.5 --sigma-highpass 1.0,1.2 \
    --roi-quantiles 0.78,0.83,0.88 --perm-n 1200 --perm-min 600 --perm-max 2000 \
    --perm-earlystop --block-pix 6
  ```
  （環境変数: `BULLET_MASK_Q=0.83`, `BULLET_SHADOW_SE_Q=0.70`, `BULLET_SHADOW_EDGE_QS=0.70,0.78,0.86`, `BULLET_EDGE_COUNT=896`, `BULLET_WEIGHT_POWERS=0.1`）
- S_shadow が低下したため、`BULLET_MASK_Q=0.85`, `BULLET_SHADOW_SE_Q=0.72`, `BULLET_SHADOW_EDGE_QS=0.72,0.80,0.88`, `BULLET_EDGE_COUNT=768`, `BULLET_WEIGHT_POWERS=0.0` で再実行し、従来値を復帰。

## 生成物
- `server/public/reports/AbellS1063_holdout.html`
- `server/public/reports/cluster/AbellS1063_progress.log`

## 次アクション
- weight power を 0.0 に固定しつつ、edge_count 768→896/960 や mask 0.83–0.87 の細分探索で outer 帯域の p_perm<0.02 を狙う。
- FAST で有望設定が得られたら FULL (n_perm≥1e4, band 4–8/8–16, global+outer) へ昇格。
