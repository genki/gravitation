# 2025-09-26 — MACS J0416 FAST mask/edge/se グリッドスイープ

## 結果サマリ
- mask ∈ {0.82, 0.845, 0.865} と edge_count ∈ {512, 704}, Σ閾値 se_q ∈ {0.72, 0.76} を FAST で一括探索したが、すべて **S_shadow=0.724 (outer=0.760, p_perm=0.064)** に収束（現ベスト値から改善なし）。
- band を `4–8,8–16` や `4–8` 単独に変更すると S_shadow が 0.05–0.34 付近まで低下し、p_perm>0.3 に悪化。

## 実施内容
- Python スクリプトで mask / edge / se_q のグリッドを走査し、各設定で `scripts/reports/make_bullet_holdout.py --fast` を実行。結果を `MACSJ0416_holdout.json` から収集。
- band オプション（`--band 4-8,8-16`）や weight ±0.3, block_pix=8 なども試行したが p_perm を 0.02 未満に下げられず。

## 生成物
- `server/public/reports/MACSJ0416_holdout.html`
- `server/public/reports/cluster/MACSJ0416_progress.log`
- `scripts/cluster/prep/reproject_kappa.py`（再投影スクリプト）

## 次アクション
- Σ層/角度核を再設計し、outer 指標がより鋭敏になるよう界面厚・形状係数を調整したうえで FAST 探索を再開。
- FAST で **p_perm<0.02** を達成した設定を FULL (band 4–8/8–16, σ_psf=1.0/1.5/2.0, n_perm≥1e4, global+outer) に昇格し、ΔAICc と S_shadow を確証。
