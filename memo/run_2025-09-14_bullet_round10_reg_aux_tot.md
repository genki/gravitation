## Bullet 全球PASS — 正則化導入＋κ_tot補助評価（Round‑10） — 2025-09-14

## 結果サマリ
- 学習目的に軽量正則化を導入（新自由度なし）: gate疎度(≈1−τ_q)の目標化、βの大きさ罰、τ_qの中庸化（0.55付近）。
- 補助: κ_tot=κ_GR+κ_FDB の残差×Σ_e 相関を別ページに恒常化（global/top10%）。
- 制約付き探索・検定の結果、主KPIは変わらず（ΔAICc維持、全球Spearmanは正）。

## 生成物
- コード: `train_shared_params.py`（正則化）、`make_bullet_holdout_tot.py`（補助ページ）
- レポート: `server/public/reports/bullet_holdout_tot.html`（κ_tot 補助）、`bullet_holdout.html` 更新

## 次アクション
- 角度核/界面幅の物理的先験（滑らかさ項）の適用を検討（AICc管理下）。
- R_tot を主とする対照解析の拡張（参考として保持、主判定は現行KPI）。

