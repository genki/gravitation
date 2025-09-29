# Bullet符号反転タスク実装メモ（2025-09-16）

## 結果サマリ
- `MinKernelParams` の界面ゲート既定を multi-scale (σ=2,4,8 pix) へ更新し、Σ_e 変換に `identity/id` エイリアスを追加。
- `scripts/reports/make_bullet_holdout.py` を改修し、整準を Lanczos3 サブピクセルシフトへ変更、PSF/高通過/β 候補を網羅的に記録する処理メタデータを導入。
- 高通過ピーク距離の探索を σ∈{6,7,8,9,10} 等へ一般化し、最小距離候補を自動採択しつつ全候補値を JSON/HTML に掲示。
- 監査出力に処理候補一覧（PSF/高通過/β）と Lanczos3 整準記録を追記し、Permutation 標本数の追跡を厳密化。

## 生成物
- 更新: `scripts/cluster/min_kernel.py`, `scripts/reports/make_bullet_holdout.py`
- 派生: `server/public/reports/bullet_holdout.{html,json}`, 各図版（Lanczos整準パネル等）
- メタ: `bullet_holdout.json` に `processing.psf_grid/highpass_grid/beta_candidates` を追加

## 次アクション
- 監査指標 (Spearman/partial/S_shadow/Fisher) が KPI を満たすか、所定のグリッド（τ_q, δ_τ/τ, s_gate, q_knee, ξ/ξ_sat, p, β, σ_psf, σ_highpass）で本走査を実行。
- Permutation ≥5000 / ブロックBootstrap CI を FAST=0 で実走し、負側統計を確認。
- `scripts/cluster/fit/train_shared_params.py` 側の界面ゲートシグマ指定を directive の範囲に合わせて再確認（必要なら GRID_S_GATE を調整）。

## 2025-09-16 追加調査
- ランク/identity/log1p/asinh 各Σ_e変換で τ_q∈{0.70,0.75,0.80}, δτ/τ∈{0.10,0.15,0.20}, s_gate∈{16,24,32,40}, q_knee∈{0.80,0.85,0.90}, ξ∈{0.5,1.0,1.5} の共有パラ学習を再実行（各 dt で grid 432〜648 件、平均5分、ログ: server/public/reports/logs/train_*.log）。
- 標準化パラの代表ケース（rank, s_gate=24, τ_q=0.75, δτ/τ=0.15, ξ=6, q_knee=0.9）でホールドアウトを Permutation 6000 / Bootstrap 4096 で再評価（w=0 強制, レポート: server/public/reports/bullet_holdout_rank_w0.0_sgate24.json/html）。
- グローバル Spearman=-0.365 (p≈0)、partial r(global/core/outer) < 0 を確認、Permutation(6000) でも負側優勢 (p_perm≈0.031)。Bootstrap 95
## 2025-09-16 追加調査
- ランク/identity/log1p/asinh 各Σ_e変換で τ_q∈{0.70,0.75,0.80}, δτ/τ∈{0.10,0.15,0.20}, s_gate∈{16,24,32,40}, q_knee∈{0.80,0.85,0.90}, ξ∈{0.5,1.0,1.5} の共有パラ学習を再実行（各 dt で grid 432〜648 件、平均5分、ログ: server/public/reports/logs/train_*.log）。
- 標準化パラの代表ケース（rank, s_gate=24, τ_q=0.75, δτ/τ=0.15, ξ=6, q_knee=0.9）でホールドアウトを Permutation 6000 / Bootstrap 4096 で再評価（w=0 強制, レポート: server/public/reports/bullet_holdout_rank_w0.0_sgate24.json/html）。
- グローバル Spearman=-0.365 (p≈0)、partial r(global/core/outer) < 0 を確認、Permutation(6000) でも負側優勢 (p_perm≈0.031)。Bootstrap 95% CI [−0.466, −0.216]。
- ΔAICc(FDB−shift) は w=0 でも ≈−1.87 に留まり KPI-B未達。Beta sweep 上では β=0.4 で Δ≈−20 だが、レポート採択ロジックが w=0 かつ最小 score を選ぶため最終差分が小さくなる。
- S_shadow=+0.0063 だが p_perm(one-sided>0)=0.125（512 perm, FAST条件で fallback）で DoD-3未達。境界帯域検定も有効ピクセル不足で未実施。
- make_bullet_holdout.py を修正: 残差勾配 NaN を 0 埋め、S_shadow permutation 用に rr_clean を導入、BULLET_SHADOW_PERM_N/BULLET_SHADOW_PERM_MIN を追加し最低512サンプル確保。
- 低重み化 (w→0) および s_gate/tau/xi の追加スイープ（64通り, perm=256）でも ΔAICc≲−2 / S_shadow p≳0.12 は改善せず。残課題: ΔAICc ≤ −10 と S_shadow p<0.05 を同時満たす探索。

## 2025-09-17 指示対応ログ
- make_bullet_holdout.py を更新: Permutation/Bootstrap を n≥5000/4096 に固定、Scharr カーネル＋|∇Σ_e|重み付き S_shadow を導入、マスク頑健性・処理メタを脚注へ拡張。
- FAST=0・Permutation6000/Bootstrap4096 で rank/τ_q=0.75/δτ/τ=0.15/s_gate=24/q_knee=0.9 の標準構成を再評価。global Spearman=-0.365 (p≈0)、Permutation効果量d≈-1.76。Bootstrap 95%CI を global/core/outer に付与。
- β×PSF×高通過 グリッドと q_knee/ξ/s_gate/τ_q の広域探索 (FAST=1) を実施するも ΔAICc(FDB−shift) は最良で ≈−3.4。Δ≤−10 を満たす組合せは未発見。
- S_shadow（Scharr+重み）を実装したが、現行パラメタでは平均値≈0、Permutation 判定も n=0 fallback → DoD-3 未達。
- TODO に「ΔAICc と S_shadow を同時PASSさせる再調整」を追加済み。
