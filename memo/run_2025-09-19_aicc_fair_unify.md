# 2025-09-19 AICc公平化と表示統一

## 結果サマリ
- `config/fair.json` に単一銀河ベンチ用の counts/k/commands セクションを追加し、N・N_eff・k をフェア条件として一元管理。
- `scripts/benchmarks/run_ngc3198_fullbench.py` / `run_ngc2403_fullbench.py` を更新し、AICc テーブルを (model, N, N_eff, k, AICc, χ², rχ²) 形式で表示、fair.json の sha と実行コマンドを脚注化。
- ベンチレポートを再生成し、SOTA ページも再構築して KPI 表示を最新化（バレット含む）。

## 生成物
- 更新: `config/fair.json`
- 更新: `scripts/benchmarks/run_ngc3198_fullbench.py`
- 更新: `scripts/benchmarks/run_ngc2403_fullbench.py`
- 再生成: `server/public/reports/bench_ngc3198.html`
- 再生成: `server/public/reports/bench_ngc2403.html`
- 再生成: `server/public/state_of_the_art/index.html`

## 次アクション
- ベンチ以外の AICc 表（代表6, 対照検証集計など）にも同形式のテーブルを展開する計画を整理。
- CI 用 `scripts/repro.py` がベンチの新AICcに追随しているか確認し、必要なら追加チェックを導入。
