# 単一銀河ベンチ（NGC 3198）— 共有JSON・監査・可視化の仕上げ

## 結果サマリ
- 共有μ(k)/gas_scaleを単一JSON `data/shared_params.json` に集約し、ベンチページに明示（ε=1, k0=0.2, m=2, gas_scale=1.33）。
- (N,k)の整合監査を追加し、N一致=OKをページに表示（単一銀河のためused_idsはSOTA側に集約）。
- 外縁1/r²復帰の図をPNGで追加（`ngc3198_outer_gravity.png`）し、CSVと併記。
- Solar Nullの高k極限の数値偏差（μ0→1）を計算し、ベンチページに表示。
- Hα残差図はデータ未入手のためスキップ表示（自動生成のフックを配置）。

## 生成物
- server/public/reports/bench_ngc3198.html（カード3種: 共有JSON/監査/外縁図 + Null偏差表示）
- server/public/reports/ngc3198_outer_gravity.png, .csv
- data/shared_params.json（単一ソース）

## 次アクション
- Hαマップの配置規約を決め、`data/imaging/NGC3198_Halpha.(fits|png)` が存在すれば残差×等高線を自動生成。
- 共有JSONをSOTA/表側に読み込ませ、表記（AIC→AICc）を全面統一。
- （再掲）β前方化の配線とユニットテスト。
