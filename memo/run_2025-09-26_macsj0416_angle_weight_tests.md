# 2025-09-26 — MACS J0416 S_shadow 角度核/重みシェーピング試行（FAST）

## 結果サマリ
- `ShadowBandpassEvaluator` に `angle_gamma` / `weight_exp` を追加し、角度核 K(θ;γ)=sign(-dot)|-dot|^γ と重み w=|∇Σ_e|^p を導入。
- γ=1.3, p=0.7 → S_shadow=0.672 (outer=0.715), p≈0.0625（僅かな改善）。
- γ=2.0, p=0.5 → S_shadow=0.594 (outer=0.629), p≈0.0660（悪化）。
- ベース設定（γ=1, p=1）に対し有意な p 値改善には至らず、現状ベストは S_shadow≈0.724（outer 0.760, p≈0.064）。

## 実施内容
- `analysis/shadow_bandpass.py`：`angle_gamma` と `weight_exp` を評価器に実装。
- `scripts/reports/make_bullet_holdout.py`：環境変数 `BULLET_SHADOW_ANGLE_GAMMA` / `BULLET_SHADOW_WEIGHT_EXP` を評価器に受け渡し。
- MACS J0416 で γ, p を掃引し FAST で再評価。

## 生成物
- `analysis/shadow_bandpass.py`, `scripts/reports/make_bullet_holdout.py`
- `server/public/reports/MACSJ0416_holdout.html`

## 次アクション
- Σ層（遷移厚 H_cut, 形状係数 χ）と角度核 K(θ;χ) の物理整合な再設計に着手し、outer 指標を強化。
- 再設計後に FAST（mask 0.83–0.85 × edge 768/832 × weight 0/0.3）で p_perm<0.02 を狙い、達成時に FULL で確証へ。
