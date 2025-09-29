# α_line 撤去（第1弾）とSOTA表示の更新

- 実行時刻: 2025-09-02 17:00 UTC

## 結果サマリ
- スクリプト側で α_line を不使用化し、出力・レポートから表示を撤去（μ(k)統合へ移行準備）
- SOTA冒頭に公平比較・物理一貫性・再現性の方針を追記、太陽系Nullテストを明記
- 代表図: BL除外・銀河名→プロファイルリンク化を完了

## 生成物
- 更新: scripts/compare_fit_sparc.py（α_line=0固定、1パラWLS化）
- 更新: scripts/compare_fit_multi.py（α_line推定を撤去、出力から除去）
- 更新: scripts/build_report.py（α_line表示を撤去）
- 更新: scripts/build_state_of_the_art.py（方針宣言、μ(k)記述、Nullテスト、α_line表示撤去）
- メモ: memo/sota_rewrite_plan.md（残タスク定義）

## 次アクション
- 第2弾: μ(k)共有推定の導入（ε,k0,m）とAICc/(n,k)/error floorの一貫化
