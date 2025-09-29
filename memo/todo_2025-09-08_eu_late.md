# メモ: Early‑Universe（Late‑FDB本線）

目的: `mu_late(a,k)=1+ε(a)S(k)` を実装し、成長 D(a) 増幅→稀少尾倍率→CMB/BAO
整合の可視領域を図示。SOTA/論文に Early‑Universe 節を追記。

受け入れ条件(DoD)
- `scripts/eu/mu_late.py` 実装、`eu-figs` が図を生成。
- 稀少尾倍率曲線（z≈10–15, 倍率≥2–5）と CMB/BAO 1σ整合の共存領域図を公開。

実行手順
1) `mu=1+ε_max σ((a-a_on)/Δa) · k^2/(k^2+k_c^2)` を `scripts/eu/mu_late.py` に実装。
2) PS/ST を用いた稀少尾倍率計算を `scripts/plot_early_universe.py` に拡張。
3) `make eu-all` で SOTA に Early‑Universe 節と識別予測（21cm |∇Tb|×銀河）を反映。

