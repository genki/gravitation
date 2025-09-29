# 2025-09-26 — AbellS1063 FAST mask=0.845 / edge=832 試行

## 結果サマリ
- mask=0.845, edge_count=832 の FAST 再実行は S_shadow=0.276 (outer=0.297)、p_perm=0.179 と変化なし（閾値未達）。
- ΔAICc 優位は維持（rot:-1.11×10⁵, shift:-1.30×10⁴）。

## 実施内容
- コマンド:
  ```bash
  PYTHONPATH=. ./.venv/bin/python scripts/reports/make_bullet_holdout.py \
    --train Abell1689,CL0024 --holdout AbellS1063 --fast \
    --sigma-psf 1.0,1.5 --sigma-highpass 0.8,1.0,1.2 \
    --roi-quantiles 0.80,0.845,0.90 --perm-n 1200 --perm-min 600 --perm-max 2000 \
    --perm-earlystop --block-pix 6
  ```
  環境変数: `BULLET_MASK_Q=0.845`, `BULLET_SHADOW_SE_Q=0.72`, `BULLET_SHADOW_EDGE_QS=0.72,0.80,0.88`, `BULLET_EDGE_COUNT=832`, `BULLET_WEIGHT_POWERS=0.0`。

## 生成物
- `server/public/reports/AbellS1063_holdout.html`
- `server/public/reports/cluster/AbellS1063_progress.log`

## 次アクション
- mask 0.83–0.85 と edge_count 768/800/832 を継続スイープし、FAST で p_perm<0.02 を狙う。
- 有望設定を確保できたら FULL (band 4–8/8–16, σ_psf=1.0/1.5/2.0, n_perm≥1e4, global+outer) に昇格して確証。
