# run_2025-09-24_sota_tri_refresh

## 結果サマリ
- `scripts/run_shared_fit_filtered.py` をバックグラウンド実行（PID 577103, ログ `logs/multi_fit_all_noBL_20250924.log`）し、ブラックリスト除外セット100件を最新 shared_params で再フィット。`data/results/multi_fit_all_noBL.json` を 2025-09-24 02:16 JST 版に更新した。
- 新JSONでは `mu_k.shared=true` で ε=1.0, k0=0.05 kpc⁻¹ (λ≈20 kpc), m=2.0、λ 最良値=24.0, A=125.0, gas_scale=1.33 を記録。
- `PYTHONPATH=. python scripts/build_report.py` で HTML 群を更新後、`make sota-refresh`→`scripts/build_state_of_the_art.py` を再実行し、SOTA代表比較図が最新 multi_fit_all_noBL に基づくように同期。

## 生成物
- `data/results/multi_fit_all_noBL.json`（mtime 2025-09-24 02:16 JST）
- `server/public/reports/multi_fit_all_noBL.html`
- `paper/figures/tri_compare_*.svg`（該当銀河の代表比較図）
- ログ: `logs/multi_fit_all_noBL_20250924.log`

## 次アクション
1. 代表比較図が SOTA ページに正しく露出しているか手動確認し、必要なら `paper/figures/tri_compare_*.svg` の適用範囲を調整。
2. 共有 μ(k) の最新値が `shared_params_sha=aa694c7f…` と一致するか、スクリプト側でも監査ログを更新する。
3. AbellS1063 再走査完了後に再び `make sota-refresh` を実行し、クラスタ KPI を最新化する。
