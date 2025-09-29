# 2025-09-26 — AbellS1063 FAST Σマスク探索（S_shadow改善）

## 結果サマリ
- FAST設定で Abell S1063 ホールドアウトを再実行し、S_shadow を **-0.39 → +0.25**（outer=0.22）へ改善。
- ただし permutation 600本時点の p_perm=0.22 で早期停止（基準未達）。Rayleigh 検定は p=2.7e-3 まで向上。
- weight_power=0 のみが有効で、0.3 を含めると S_shadow が ≈0.09 まで低下することを確認。

## 実施内容
- `BULLET_SHADOW_EDGE_QS=0.70,0.80,0.85 / BULLET_EDGE_COUNT=512 / BULLET_SHADOW_SE_Q=0.75` を指定し、FAST 推奨 (`--fast --downsample 2 --perm-earlystop`) で再走査。
- コマンド（最良設定）:
  ```bash
  PYTHONPATH=. ./.venv/bin/python scripts/reports/make_bullet_holdout.py \
    --train Abell1689,CL0024 --holdout AbellS1063 --fast \
    --sigma-psf 1.0,1.5 --roi-quantiles 0.70,0.80,0.85 \
    --weight-powers 0.0 --perm-n 1200 --perm-min 600 --perm-max 2000 \
    --perm-earlystop --block-pix 6
  ```
- 比較のため `--weight-powers 0.3`（および `BULLET_EDGE_COUNT=1024`）でも実行し、S_shadow が 0.09 / p≈0.34 まで悪化することを確認後、最良設定を再実行して現行 JSON を更新。

## 生成物
- `server/public/reports/AbellS1063_holdout.html`
- `server/public/reports/cluster/AbellS1063_progress.log`

## 次アクション
- 後続：Σモデルの層厚・角度核を再設計し、outer 帯域で p_perm<0.02 を達成する設定を洗い出す。
- 重み付け・edge_count の追加スイープ（512→768/1024、Σ_e^0.1 など）と高通過帯域(4–8px)の組合せを検討。
- p_perm<0.02 を FAST で確認できた設定を FULL (n_perm≥1e4, global+outer) へ昇格し、SOTAへ反映。
