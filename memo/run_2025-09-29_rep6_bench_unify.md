# ベンチ図（NGC 3198/2403）の脚注帯をrep6様式へ統一

## 結果サマリ
- ベンチ図 `rep_ngc3198.png`, `rep_ngc2403.png` に rep6 と同一仕様の脚注帯を追加（N,k, rχ², AICc, ΔAICc, σ_floor, rng, shared_sha）。
- 配色と凡例を rep6 のテンプレv2に合わせて統一（GR=灰, GR+DM=紫, MOND=緑, FDB=赤）。
- 画像PNGへ軽量メタ（iTXt）を埋め込み（seed, shared_sha）。

## 生成物
- `server/public/reports/figs/rep_ngc3198.png`
- `server/public/reports/figs/rep_ngc2403.png`
- 更新スクリプト: `scripts/benchmarks/plot_rep_fig.py`

## 次アクション
- 必要に応じて SVG 出力＋メタ埋め込みも追加（差分監査の容易化）。
- ベンチindexからの導線を確認し、SOTAトップのshaと一致表示を継続監視。
