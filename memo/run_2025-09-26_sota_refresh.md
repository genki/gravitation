# SOTA更新 — 現状反映（2025-09-26 JST）

実行: `make sota-refresh`（SOTA再生成＋進捗カード更新）。
最終更新: 2025-09-26 JST。

## 結果サマリ
- SOTAトップを再生成し、「現在の課題」カードを最新値で更新。
- 追加HOの到達状況（自動抽出）:
  - Abell S1063 — S_shadow=0.276 (p=0.18) で方向性未達。
  - MACS J0416 — S_shadow=1.678 (p=0.079) が未達（WCS/PSF/ROI 再監査→FAST→FULL）。
- 代表比較図のMONDが“桁違いに大きい”件：コード点検の一次結果では式・単位変換は妥当（下記）。図生成側のμ推定やg_N構成の影響が疑い。切り分けを着手。

## 主要変更点 / 生成物
- 再生成:
  - `server/public/state_of_the_art/index.html`（「現在の課題」を含む）
  - `server/public/reports/progress.html`, `progress_card.html`
- 確認ログ:
  - make標準出力（SOTA rebuilt）

## MOND式 点検ログ（要旨）
- 実装: `src/models/adapter.py:MONDModel`
  - 補間式: a = 0.5 g_N + sqrt((0.5 g_N)^2 + g_N a0)（simple μ）
  - a0 変換: 1.2e-10 m/s^2 → a0_kpc = a0_SI × (kpc_in_m / 1000^2) ≈ 3.7e3 km^2 s^-2 kpc^-1（実装どおり）
  - g_N 構成: g_gas + μ*g_star（`V^2/R` で整合単位）
- 図側: `scripts/benchmarks/plot_rep_fig.py` でも同一式・同一単位を確認。
- 現象の仮説: μ推定（GR基準）や外縁の誤差床設定が g_N を過大化 → MONDが相対的に上振れ。次段でμ・誤差床・R単位の整合性を点検。

## 次アクション（短期）
- [FAST] MACS J0416/Abell S1063 の方向統計を再走査（mask-q: 0.70/0.80/0.85, band: 8–16, σ_PSF: 1.0/1.5, block: 6）。`p̂<0.02` 到達で FULL へ。
- 角度核とS_shadowの正規化（|S|≤1）を `analysis/shadow_bandpass.py` に実装（既知課題: S>1 事例）。
- MOND図の切り分け: μ_GR の上限制約・g_N対数プロファイルのダンプ・R単位（kpc）一致チェックを追加し再描画。


実行時刻(JST): 2025-09-27 05:14:58 JST
