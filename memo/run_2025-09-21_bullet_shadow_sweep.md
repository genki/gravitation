# Run 2025-09-21: Bullet Shadow Sweep (初期探索)

## 結果サマリ
- `scripts/reports/sweep_bullet_shadow.py` を実装し、PSFσ∈{1.0,1.5}, HPσ∈{1.0,1.5}, w∈{0,0.3,0.7}, mask_q∈{0.70,0.75}, edge_q∈{0.70,0.75} の 48 通りを perm=256（resid perm=128）で試行
- **PSFσ=1.5, HPσ=1.0〜1.5, w=0, mask_q=0.70–0.75, edge_q=0.70–0.75** で **S_shadow≈0.198, p_perm≈3.9×10⁻³**, ΔAICc(FDB−rot)≈−6.79×10⁷, ΔAICc(FDB−shift)≈−6.74×10⁶（良好）
- 重み指数 w>0 では ΔAICc が正転するケースが多く、方向性は同等でも採用不可

## 生成物
- スイープスクリプト: `scripts/reports/sweep_bullet_shadow.py`
- 走査ログ: `tmp/sweep/bullet_shadow_sweep_20250921T172745Z.jsonl`

## 次アクション
- 有望設定 (PSFσ=1.5, HPσ≈1.0, w=0, mask_q=0.70–0.75, edge_q=0.70–0.75) で perm≥10⁴ の本番実行を準備
- 追加ハイパーパラメータ（SN quantile, block size, Σ_e quantile）も含めた絞り込みと方向一致統計の再検証

### 2025-09-21 18:12Z 追加: 本番パラメータ試行
- 設定: PSFσ=1.5, HPσ=1.0, weight_power=0, mask_q=0.70, edge_q=0.70, perm_shadow=12,000, perm_resid=10,000
- 結果: S_shadow=0.378、p_perm=1.75×10⁻³、ΔAICc(FDB−rot)=−6.79×10⁷、ΔAICc(FDB−shift)=−6.74×10⁶、Spearman(top10)=-0.229 (p≈7.1×10⁻¹⁶)
- `server/public/reports/bullet_holdout.json` と progress ログに反映済み（Checkpoint meta 更新済み）
### 2025-09-21 18:30Z 追記: SN分位スイープ
- PSFσ=1.5, HPσ=1.0, weight=0 固定で SN 分位 {0.85,0.90,0.95} を perm=512 で比較
- SN≥0.90 で S_shadow≈0.378 (p_perm≈1.95×10⁻³) を維持、SN=0.85 では S_shadow≈0.360 (p_perm≈3.9×10⁻³)
- outer 帯域がより安定（S_shadow_outer≈0.37〜0.40）となり、SN=0.90 を既定値維持のまま採用予定
### 2025-09-21 19:00Z 追記: 公正条件反映確認
- `config/fair.json` を 2025-09-21 版に更新（PSFσ=1.5, HPσ=1.0, mask_q=0.70, shadow edge_count=256, sn_q=0.9, perm_min=12k, block_size=28）
- 公正設定のみで `make_bullet_holdout.py` を再実行し、S_shadow=0.378, p_perm=2.25×10⁻³, ΔAICc(FDB−rot)=−6.79×10⁷, ΔAICc(FDB−shift)=−6.74×10⁶ を再現
- シード固定とチェックポイントリセットで安定化を確認済み
### 2025-09-21 20:50Z 追記: SOTA刷新
- 新 fair.json (2025-09-21) 反映後に `scripts/build_state_of_the_art.py` を実行し、SOTA トップを更新
- Bullet セクションは S_shadow p≈2.25×10⁻³ の再計算値で同期済み
