# メモ: 代表6（Σ vs 体積）— 実測再計算

目的: 各銀河の AICc/(N,k)/rχ²/ΔAICc（Surface−Volumetric）/勝率/md5 を実測に
基づき再出力し、表と脚注（誤差床/マスク/seed/データ版）を恒常化。

受け入れ条件(DoD)
- `server/public/reports/rep6_table.html` が生成・公開される。
- ΔAICc と勝率の定義が本文/脚注に一致（勝率=ΔAICc<0）。
- md5 と (N,k) が再現性監査（CI）で照合される。

実行手順
1) `scripts/reports/make_rep6_table.py` を追加（csv+html出力）。
2) 生成に `data/used_ids.csv` と `shared_params.json` を単一ソースで参照。
3) `make rep6-recalc` ターゲットを追加し、SOTAとリンク。

