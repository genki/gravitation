# 実行メモ: CI数値監査拡張・環境定義・論文ビルド・バレット最小核（2025-09-08）

日時: 2025-09-08

## 結果サマリ

- CI監査強化: `audit_consistency.py` に AICc と rχ² の自己整合チェック（AIC→AICc補正/χ²→rχ²）を追加し、`site-audit` で検証（ok=true）。
- 環境定義: `environment.yml` と `Dockerfile` を追加（再現ビルド/配布の足場）。
- 論文ビルド: `make paper-all` 実行。Quarto/Pandoc 非導入のためPDFはスキップ、HTML/変数/図収集/アーカイブは生成。
- バレット最小核: `make bullet-all` 実行（準備済みスタブ入力で流通）。`bullet_metrics.json` を生成し、SOTA連携の下地を確認。

## 生成物

- 監査: `scripts/qa/audit_consistency.py`（numericセクション追加）
- 環境: `environment.yml`, `Dockerfile`
- 論文: `paper/_variables.yml`, `paper/paper.tex`, `paper/dist/arxiv-src.zip`
- バレット: `server/public/reports/cluster/bullet_metrics.json`, `server/public/reports/cluster/bullet_overview.html`

## 次アクション

- Quarto/Pandoc の導入後に `make paper-all` を再実行しPDF生成を確認。
- バレットの実観測マップを配置して再学習→ホールドアウト評価（ΔAICc ≤ −10 目標）。

