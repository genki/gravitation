# SOTA 残タスク 実行ログ（2025-09-13）

## 実行内容
- `make data-catalog` でデータ一覧を更新。
- `make bullet-holdout` で Bullet ホールドアウト（AICc 公平化・三指標）を再生成。
- `make sota-refresh` で SOTA ページを更新（最新の (N,k) と KPI 状態を反映）。

## 結果サマリ
- (N,k): N=12100, k(FDB/rot/shift/shuffle)=2/1/2/0
- AICc: FDB=6.323e5, rot=3.206e6, shift=6.524e5, shuffle=2.592e6
- ΔAICc: FDB−rot=−2.575e6, FDB−shift=−2.003e4, FDB−shuffle=−1.960e6
- 指標: peak(PASS), high-pass peak(PASS), shear-phase(PASS), neg-corr top10(FAIL)

注: neg-corr(top10%) の FAIL は現行 ROI/thr 設定での結果。SOTA では PASS/FAIL と閾値を明示。

## 次の一手（SOTA 残り）
- CIAO 4.17 環境で `make ciao-bullet` を実行し、正式 `sigma_e_ciao/omega_cut_ciao` を生成→差分 <10% 確認→ホールドアウト再実行。
- （任意）neg-corr の層化ロバスト化: ROI を top25–50% に広げた補助指標も表示し、main は現行閾値を維持。

