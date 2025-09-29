# 2025-09-17 バレットS_shadow再計算・SOTA同期

## 結果サマリ
- `config/baseline_conditions.json` に shadow セクション（edge_count=4096, se_quantile=0.7, rr_quantile=0.7, perm_min=10000, block_size=32）を追加し、バレット評価の既定を統一。
- `scripts/reports/make_bullet_holdout.py` を baseline 値参照＋指標更新に対応し、環境変数なしで **S_shadow=0.309, p_perm=0.0476** を再現。カード文言も主要指標＋S_shadow表示に刷新。
- `scripts/benchmarks/run_ngc3198_fullbench.py` / `run_ngc2403_fullbench.py` / `scripts/build_state_of_the_art.py` を新パラカード仕様に更新し、再生成した HTML に θ_opt/θ_if/θ_aniso や CLASS 実行情報を反映。
- `scripts/qa/audit_shared_params.py` / `scripts/paper/generate_vars.py` に import パス補正を入れ、`data/shared_params.json` v2 から直接読み込むよう統一。

## 生成物
- config/baseline_conditions.json（shadow 定義追加）
- server/public/reports/bullet_holdout.{html,json}（S_shadow p_perm=0.0476）
- server/public/state_of_the_art/index.html（proxy 表現除去、CLASS 情報同期）
- server/public/reports/bench_ngc3198.html, bench_ngc2403.html（共有パラ詳細追加）

## 次アクション
- バレット界面マスク（q_edge, SN 閾, 形態整形）をさらに最適化し、S_shadow の信頼区間と境界検定を p<0.05 に収束させる。
- Fig‑EU1c の CI/差分表示と runbook の再現手順を整理し、CLASS 実行を CI に組み込む。
- 単一銀河テンプレ（外縁 1/r²/Hα/ω_cut）を他銀河へ展開し、A/B 表の集約カードを追加。
