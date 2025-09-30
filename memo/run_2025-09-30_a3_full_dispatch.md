# A-3（W_eff“膝”）FULL実行の投入（選抜構成）

版: 2025-09-30

## 結果サマリ
- AbellS1063 の A-3 FAST（3×3×3）結果を踏まえ、方向性S_shadowの改善を狙う上位寄り構成を4本選抜し、**FULL（perm=5000固定）** をバックグラウンド投入。
- HOLDOUTランごとに `holdout_runs/` へ **パラメタ付きのJSON/HTMLを保存** するようバッチを整備（FAST/FULL共通）。今後のランキング・可視化が容易に。
- MACSJ0416 の A-3 FAST は継続実行中。FASTスクリプトも per-config 保存に更新済み。

## 生成物
- ジョブ: `w_eff_knee_full_sel_AbellS1063_20250930_053004`（scope実行）
  - ログ: `server/public/reports/logs/w_eff_knee_full_sel_AbellS1063_20250930_053004.log`
  - メタ: `tmp/jobs/w_eff_knee_full_sel_AbellS1063_20250930_053004.json`
- スクリプト追加/更新:
  - 新規: `scripts/jobs/batch_w_eff_knee_full_select.sh`（FULL選抜実行＋成果保存）
  - 改修: `scripts/jobs/run_w_eff_knee_fast_seq.sh`（各構成のJSON/HTMLを `holdout_runs/` に保存）
- SOTA: `server/public/state_of_the_art/index.html` を再生成（更新時刻反映）

## 次アクション
- AbellS1063 FULLの収束を待ち、`holdout_runs/AbellS1063_*_full.json` から **S_shadow（global/core/outer）と p_perm**、ΔAICc(FDB−shift) を抜粋→ランキング表を作成しSOTAへ掲載。
- MACSJ0416 FAST完了後、同様に上位候補を2–4本選抜→FULL投入。
- A-4（Σ変換×g×PSF/高通過）FAST→FULLの順に実行し、Permutation≥5000/Bootstrap CIを常設。

