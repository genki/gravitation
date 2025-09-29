# 代表比較図(MOND)の診断オプション追加とS_shadow正規化 — 実装/再描画（2025-09-26 JST）

## 結果サマリ
- `analysis/shadow_bandpass.py` に角度核(von Mises)の**単位平均正規化**と **[-1,1] クリップ**を追加し、S_shadowの値域逸脱（>1）を抑止。
- 代表比較図スクリプト `scripts/benchmarks/plot_rep_fig.py` に MOND 診断オプションを追加：
  - `--mond-mu-source {gr,fixed,refit}`、`--mond-mu-fixed`、`--mu-max`、`--fit-uses-floor`、`--no-meta`。
  - メタ出力 `tmp/rep_fig/rep_meta_<name>.json`（μやg_N統計）を保存。
- NGC3198/2403 を**再描画**し、MOND 曲線が他モデルと同オーダーで表示されることを確認。

## 生成物
- 更新: `analysis/shadow_bandpass.py`（正規化とクリップ）
- 更新: `scripts/benchmarks/plot_rep_fig.py`（診断オプション・メタ出力）
- 図: `server/public/reports/figs/rep_ngc3198.png`, `rep_ngc2403.png`
- メタ: `tmp/rep_fig/rep_meta_ngc3198.json`, `rep_meta_ngc2403.json`

## 実行ログ（主要コマンド）
```sh
PYTHONPATH=. python scripts/benchmarks/plot_rep_fig.py \
  --name NGC3198 --name NGC2403 \
  --no-run-fdb --psf-sigma-kpc 0.0 --fit-uses-floor --mu-max 3.0 --mond-mu-source gr
make sota-refresh
```

## 次アクション
- [FAST] MACS J0416 / Abell S1063 の再走査（mask-q:0.70/0.80/0.85, band:8–16, σPSF:1.0/1.5, block:6, rng固定）。
- `analysis/shadow_bandpass.py` の正規化導入後、Bullet/追加HOのS_shadow・p_permが安定化するか確認（FULL基準: n_perm≥1e4）。
- MOND図の比較用に `--mond-mu-source refit` での参考曲線も内部ログに保存し、影響範囲を評価。

実行時刻(JST): 2025-09-27 05:20:10 JST
