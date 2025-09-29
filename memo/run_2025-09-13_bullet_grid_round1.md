## Bullet 全球PASSに向けた共有パラ再学習（Round‑1） — 2025-09-13

## 結果サマリ
- 指示に従い、(α,β,C,ξ,p,τ_q) のグリッドを拡張し、Spearman負相関を小比率で混合した目的関数（w_corr=0.12）で再学習。
- 学習最良は「ξ=0」を選択。共有パラは α=2.0, β=0.7, C=0.05, τ_q=0.6（sha更新）。
- Bulletホールドアウト（Permutation n=4096）では ΔAICc(FDB−shift)=−2.49×10^5 でKPI‑2は引き続きPASS。ただし全球Spearman(R,Σ_e)=+0.30（p≪0.05）でKPI‑1は未達。

## 生成物
- 共有パラ: `data/cluster/params_cluster.json`（sha再生成）
- レポート/JSON: `server/public/reports/bullet_holdout.html`, `.../bullet_holdout.json`（Permutation n=4096）

## 次アクション
- 「ΔAICc(FDB−shift) ≤ −10 を満たす候補に限定」した上で、全球Spearmanが最も負になる(ξ,p,τ_q,α,β)を選ぶ制約付き探索へ変更。
  - 実装案: 学習スクリプトで AICc による足切り（閾値 −10 相当を近似）→ 残りで mean Spearman を最小化。
- 追加のグリッド例（計算量中）：`GRID_XI=0.05,0.1,0.2 GRID_P=0.5,0.7 GRID_TAUQ=0.6,0.7,0.8 GRID_ALPHA=0.6,1.0,1.5,2.0 GRID_BETA=0.3,0.5,0.7`。
- 監査強化: ブロックBootstrap CI と partial r の図版を追補。

