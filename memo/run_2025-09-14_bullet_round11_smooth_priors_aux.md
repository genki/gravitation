## Bullet 全球PASS — 滑らかさ先験＋補助評価拡張（Round‑11） — 2025-09-14

## 結果サマリ
- 学習に軽量な滑らかさ先験を追加（新自由度なし）: τ_q の中庸化(0.55付近)、βの過大抑制、ゲート疎度の目標化。AICcで制約管理。
- κ_tot（κ_GR+κ_FDB）の補助相関を恒常化し、専用ページを追加。
- 制約付き探索と本検定（Permutation 1024/4096, Bootstrap 1024/4096）でも、主KPIは ΔAICc維持・全球Spearmanは正側のまま。

## 生成物
- コード: `train_shared_params.py`（W_SMOOTH/W_GATE/W_BETA 正則化）
- レポート: `server/public/reports/bullet_holdout_tot.html`（補助評価ページ）, `server/public/reports/bullet_holdout.html` 更新

## 次アクション
- 角度核/界面幅の物理モデル化（先験をもう一段強化）と、補助評価の可視化整理（SOTAへのリンク追加）を検討。

