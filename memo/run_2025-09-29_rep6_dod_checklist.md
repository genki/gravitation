# rep6 DoD 達成確認チェックリスト

## 結果サマリ
- 6図を同一テンプレ（Total基準, 追加は薄破線）で再生成し、`assets/rep6/*_rep6.(png|svg)` を出力。
- 各図に脚注帯（N,k,rχ²,AICc,ΔAICc,σ_floor,rng,shared_sha）を表示。
- `reports/ws_vs_phieta_rep6.html` は表＋図の一体ページで、表の公平条件（誤差床含む）と図脚注が一致。
- ベンチ2頁（NGC 3198/2403）の代表比較図をSVG/PNGで埋め込み、脚注帯仕様をrep6に揃えた（外縁1/r²の定義も文言一致）。

## 生成物
- rep6: `assets/rep6/*_rep6.(png|svg)`, `server/public/reports/ws_vs_phieta_rep6.html`
- ベンチ: `server/public/reports/figs/rep_ngc3198.(png|svg)`, `server/public/reports/figs/rep_ngc2403.(png|svg)`, `server/public/reports/bench_*.html`

## 次アクション
- rep6/ベンチのSVGをSOTAからも直接参照できる導線を追加（任意）。
