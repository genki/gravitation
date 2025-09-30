# A-4（Σ_e 変換 × g × PSF/高通過）FASTバッチ雛形の追加と自動選抜系の整備

## 結果サマリ
- A-4 用の **FAST** バッチスクリプトを追加（`batch_se_psf_grid_fast.sh`）。--fastで軽量にランキング用の結果を得る。
- FAST結果からFULL候補を自動選抜し、選抜バッチへ渡すユーティリティを整備。
  - 追加: `scripts/jobs/select_top_from_fast.py`（q_knee:p:xi_satの上位抽出）
  - 追加: `scripts/jobs/dispatch_full_from_fast.sh`（自動選抜→FULL選抜バッチをscopeで起動）
- 既存の A-4 FULL 一括（`batch_se_psf_grid.sh`）は据え置き（必要時のみ使用）。

## 生成物
- スクリプト:
  - `scripts/jobs/batch_se_psf_grid_fast.sh`
  - `scripts/jobs/select_top_from_fast.py`
  - `scripts/jobs/dispatch_full_from_fast.sh`

## 次アクション
- 現在は A-3（FAST/FULL）が稼働中のため **未起動**。A-3の収束を待ち、負荷を見て A-4 FAST を順次投入。
- A-3 FAST完了後は `dispatch_full_from_fast.sh MACSJ0416` でFULL候補を自動投入可能。

