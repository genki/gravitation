# メモ: バレットクラスタ（薄レンズFDB）最小核

目的: 遮蔽 W, 界面 S, 畳み込み核 K≈1/θ を実装し、2–3クラスタで α,β,C を同時
最小化して固定。バレットはホールドアウトに適用。

受け入れ条件(DoD)
- バレットで ΔAICc ≤ −10（FDBが優越）を満たす。
- κピーク位置・剪断位相・κ残差×Σe 相関の3指標が論述通りの整合。

実行手順
1) `scripts/cluster/fdb/make_S_W.py`, `kappa_fdb.py` を最小実装（FFT/FMM, 縁アポ）。
2) `scripts/cluster/fit/grid_search_abc.py` で α,β,C を学習→固定。
3) `make bullet-all` で前処理→学習→ホールドアウト→評価まで実行。

