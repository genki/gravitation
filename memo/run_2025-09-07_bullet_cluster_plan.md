# バレットクラスタ（1E 0657-56）— FDB(ULM) 薄レンズ検証の実装開始

## 結果サマリ
- 薄レンズ近似の最小実装を追加（共有パラ α,β,C + S(界面)/W(遮蔽) + κ_FDB 畳み込み）。
- パイプラインMakeを追加：`bullet-prep → bullet-sigma → bullet-fit-train → bullet-apply-holdout → bullet-metrics`。
- 共有学習（簡易グリッド）→ホールドアウト適用（バレット）までの雛形を整備。

## 生成物
- scripts/cluster/prep/reproject_all.py（マニフェスト作成）
- scripts/cluster/maps/make_sigma_e.py（X線→Σ_e）
- scripts/cluster/fdb/make_S_W.py（S,Wの生成）
- scripts/cluster/fdb/kappa_fdb.py（κ_FDBのFFT畳み込み）
- scripts/cluster/fit/global_fit.py（α,β,C の粗探索）
- scripts/cluster/fit/apply_holdout.py（共有固定でバレットへ適用）
- scripts/cluster/eval/metrics.py（ピークオフセット等の簡易指標）
- Makefile: bullet-* ターゲット一式

## 次アクション
- データ投入（κ, X線, 温度, ICL）とWCS/PSF整合（prepの拡張）。
- κ_GR(baryon)の実装（星＋ガスの推定と投影）。
- 強レンズ拘束（多重像）の取り込みと評価関数の拡張。
- 対照検証（回転/平行移動/等値面シャッフル）のクラスタ版追加。
