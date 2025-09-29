# rep6 図版の表示基準/体裁の完全統一（Total基準, テンプレv2）

## 結果サマリ
- 全6図を **Total基準**の単一テンプレで再生成し、**FDB追加線は薄破線**に格下げ（補助表示）。
- 図下の **脚注帯** に `(N,k,rχ²,AICc, ΔAICc vs W·S, σ_floor, rng, shared_sha)` を恒常表示。
- **凡例/配色/線種/順序** を統一（観測→GR→GR+DM→MOND→FDB‑W·S(Total)→FDB‑Φ·η(Total)→FDB追加）。
- **二段構成**（上: 速度Total, 下: 残差=観測−FDB‑W·S Total）を統一。
- 画像PNGに **XMP/iTXt** で `N,k,rchi2,AICc,seed,shared_sha` を埋め込み。
- `reports/ws_vs_phieta_rep6.html` に **2×3タイル**で6図を自動差し込み。

## 生成物
- 図: `assets/rep6/{galaxy}_rep6.png`（6枚）
- メタ: `assets/rep6/{galaxy}_rep6.json`
- HTML: `server/public/reports/ws_vs_phieta_rep6.html`（表直下に6図を挿入）
- スクリプト:
  - 新規 `scripts/figs/io_rep6.py`（観測/モデルの共通IO）
  - 新規 `scripts/figs/plot_rep6.py`（テンプレv2・Total基準の作図）
  - 新規 `scripts/reports/inject_rep6_figs.py`（HTML差し込み）
  - Makefile ターゲット `rep6`

## 次アクション
- ベンチ（NGC 3198/2403）の図脚注帯も同仕様で再生成（既存コマンド流用）。
- 必要に応じて SVG 出力と `<metadata>` 埋め込み版も追加（将来のdiff容易化）。
