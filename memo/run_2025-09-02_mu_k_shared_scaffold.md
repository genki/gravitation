# μ(k) 共有推定の枠組み（第1弾）

- 実行時刻: 2025-09-02 18:15 UTC

## 結果サマリ
- compare_fit_multi.py に μ(k) 共有パラメータ（ε,k0,m）の粗格子を追加し、lam,Aに整合する格子点を暫定選択
- 結果JSONに `mu_k: {eps,k0,m,shared:true}` を保存し、SOTAに表示
- 次段で μ(k) を実際のモデルへ組込み（推定・最適化）予定

## 生成物
- 更新: scripts/compare_fit_multi.py（--mu-eps-grid/--mu-k0-grid/--mu-m-grid）
- 更新: scripts/build_state_of_the_art.py（共有μ(k)の表示）

## 次アクション
- μ(k) の実適用（周波数空間倍率の導入）と格子→局所最適化
- AICc/(n,k) の全面表示とCV中央値の整備
