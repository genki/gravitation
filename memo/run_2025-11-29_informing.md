# 2025-11-29 main.md/main.ja.md アップデートメモ

## 追加・修正点
- 英語版 `main.md` に以下を追加/整理
  - **§2.3 Informing tensor**: ULE-EM 前縁グリーン関数＋TT射影で定義し、波セクターが GR と同型であることを明記。
  - **§7.1 GR–FDB compatibility (wave sector)**: 速度=c、偏極=スピン2のみ、四重極公式一致を箇条書きで整理。
  - **§9.1 Scope/limitations**: 射程（銀河〜宇宙網）、扱わない領域（SM/インフレ等）、未解決課題を列挙。
- 日本語版 `main.ja.md` に対応する小節を追加
  - **3.4 インフォーミング・テンソル**、**5.4 重力波セクターの整合**、**13.1 射程と限界・未解決課題**。
  - 重複していた宇宙年齢の記述を整理。
- 用語揺れを解消：Wiki では ULW-EM→**ULE-EM** に統一（既存 wiki master `107f777`）。
- README 冒頭に「最新 PDF (main.pdf / main.ja.pdf) は Release latest から取得可能」を追記し、ライセンス文言を微調整。

## 影響範囲
- `main.md`, `main.ja.md`, `README.md`
- Wiki は別途 ULW→ULE の統一済み（コード本文とは独立）。

## 残課題
- CITATION.cff / ライセンスファイル分割（CC-BY-4.0 + MIT）の確定は未着手。
- cosmology/σ8/H0 同時フィットや Γ(x) 微視的導出は今後の研究項目のまま。
- 11/30: FDB-Glossary wiki math修正（informing tensorブロックを$$対応、単位s^-1とAICc下線のエスケープ、σ表記整理）check-math合格
- 11/30: Wiki HomeとFDB-Math-Notesの数式をGitHub形式に修正、check-math全ページ合格
- 11/30: wiki math運用のベストプラクティスを memo/wiki-math.md に整理・コミット
- 11/30: Issues #5 (GW速度=c) と #14 (スピン2偏極) はFDB定義上既に満たされるためコメント付与しクローズ
- 11/30: Issue #5 #14 に数式をGitHub形式で補足コメント（解決済み維持）
- 11/30: main.md に Γ(x) の最小オープン系モデル、informing tensor とデコヒーレンス核の接続、Mach的慣性解釈を 3.4–3.6 として追記
- 11/30: make refresh で main/main.ja PDF 更新; release v2025-11-30 にアップロード。gh-pages を最新 wiki から再生成（Glossary/Math-Notes追加）しプッシュ。
- 11/30: Issue #16 完了（main.md 3.4–3.6 追加、PDF/リリース/gh-pages更新後にコメントしてクローズ）
- 11/30: main.md に field-content/DoF/emergent-QG セクション追加（9.2–9.4）で #17 要件対応、コメント追記
- 11/30: Issue #18 を位相ずれ評価（LISA/ET δn 上限）反映後コメントしてクローズ。PDF/リリース/gh-pages更新済み。
- 11/30: 6.1にFDB回転曲線カーネル実装節追加、scripts/fdb_fit.py スケルトン作成、docs/rotcurve_comparison.md テンプレ追加
- 11/30: rotmod->CSV コンバータ追加、fdb_fit に境界制約導入。NGC2403/3198 を試走（ガス面密度未再構成のためχ2大きめ）。
- 11/30: rotmod->CSV で Vgas からガス面密度を再構成するよう改善。NGC2403 χ2≈8.75e4, NGC3198 χ2≈1.85e4（M/L固定・単純カーネル）。
- 11/30: Σ_gas 再構成に単調化＋1.33 He補正を導入（convert_rotmod）。NGC2403/3198 再走はχ2改善せず→モデル単純化/パラ境界要調整が必要。
- 11/30: Σ_gas再構成にSG平滑＋He補正導入（convert_rotmod）。NGC2403/3198再試行もχ2高止まり→モデル/パラ調整が今後の課題。
- 11/30: fdb_fit をNewton sanity + 1スケールカーネル + 外縁(R>4kpc) + σ_model=5 km/s に刷新。NGC2403: chi2~3.33e3, NGC3198: chi2~5.67e3（大幅改善だがまだ大きめ）。
- 11/30: fdb_fit を残差プロット付き・rotmod Newton オプション付きに更新。外縁(>4kpc)1スケールカーネルで NGC2403 chi2~3.3e3, NGC3198 chi2~5.7e3。
- 11/30: シェル重み＋ガス優先 Δv² モデルに改修（R_ev=2.5R_d固定）。R>2R_d で再フィット: NGC2403 chi2≈2.32e3, NGC3198 chi2≈5.23e3（σ_model=5km/s）。
- 11/30: shellモデルを拡張 (R_ev/σ_ev フィット＋v0オフセット)、bounds締め＆σ_model=7で外縁フィット。結果: NGC2403 χ²~1.89e3, NGC3198 χ²~3.92e3。
- 11/30: r_cut=3R_d & σ_model=8 に変更、eps/v0 bound拡大で再フィット。NGC2403 χ²≈9.5e2, NGC3198 χ²≈2.35e3 まで改善。
- NGC2903: Newton-only chi2=8.60e4; shell3 fit (r>3Rd, σ_model=8) => chi2=5.09e2; params=[alpha≈-0.19, eps=0.8 kpc, ML=0.9, beta≈0.035, R_ev≈2.01R_d, sigma_ev≈0.56R_d, v0≈13.8 km/s]
- NGC6503: Newton-only chi2=6.42e4; shell3 fit (r>3Rd, σ_model=8) => chi2=7.63e1; params=[alpha≈1.47, eps=0.8 kpc, ML=0.9, beta=0, R_ev≈2.43R_d, sigma_ev=0.5R_d, v0≈33 km/s]
- DDO154: Newton-only chi2=6.92e4; shell3 fit → chi2=6.27; params=[alpha=2.0 (bound), eps=0.8, ML=0.9, beta=0.3 (bound), R_ev=2.76R_d, sigma_ev=1.0R_d, v0=20.9 km/s]
- DDO170: Newton-only chi2=2.76e4; shell3 fit → chi2=8.53e1; params=[alpha≈-0.37, eps=0.8, ML=0.9, beta=0, R_ev=2.0R_d, sigma_ev=0.5R_d, v0≈0]
- v0固定/比較テスト（r>3R_d, sigma_model=8）：
  - NGC2403: v0-only chi2=213 (v0=80上限張り付き), FDB v0=0 chi2=953
  - NGC3198: v0-only chi2=186 (v0=80上限), FDB v0=0 chi2=2348
  - NGC6503: v0-only chi2=53 (v0=80上限), FDB v0=0 chi2=82
  - DDO154: v0-only chi2=5.5 (v0=38), FDB v0=0 chi2=12.1
- DDO170: v0-only chi2=0.5 (v0=50), FDB v0=0 chi2=85.3
  → v0=0 では χ2 が悪化、特にフィールド系 dwarf で v0-only が強く効く。殻カーネルは形を揃えるが一定オフセット成分が銀河間で大きく、環境項(v0)の役割が大きい可能性。
- 11/30: fdb_fit をFDB-only→Newton+1/r混合に変更する試行は、局所的凹み解消に一定の効果はあったが、物理解釈が曖昧になるため v2 カーネルに移行する前段階と位置付け。
- 11/30: DDO154 は厚いガス球＋極薄星ディスクに近く、薄い円盤＋殻モデルの初期検証ターゲットとしては過酷と判断。dwarf 枠は DDO170/168 を優先。
- 11/30: 共通カーネルv1（Newton+殻付きΔv², competitive mixing）で NGC2403/3198/6503/ DD0170/168 の5銀河を同時フィット。alpha,mu共通＋銀河毎ML/R_ev/σ_evで χ²_total≃6.5e2。個別fitに比べ DDO系/NGC3198 外縁での乖離が残る。
- 11/30: ガス質量でΔv²をスケーリングする試行は DDO側の振る舞い改善に寄与したが、NGC6503などL*側との両立が難しく、alphaの共通性が弱くなり物理解釈がぼやけるため撤回。
- 11/30: 殻位置R_evをガス量 S_g(M_gas/median) に応じて幾何学的にシフトする修正を導入（gas-rich→殻やや外側、gas-poor→やや内側）。共通alpha,mu下で5銀河共通カーネルの整合性は改善するも、依然としてスケール差の吸収は不完全。
- 11/30: FDB回転曲線v2カーネルを試作: v_tot^2(R)=v_Newt^2(R)(1-εW(R))+Δv²W(R), W=0.5[1+tanh((R-R_t)/dR)]。R_t,dRはΣ_gasの急落点から推定＋事前、Δv²とεをフィット。
- 11/30: v2 を NGC2403/3198/6503/ DDO170/168 に適用。代表値:
  - NGC2403: Δv²≈1.36e4, ε=0.5, R_t≈3.81kpc, dR≈0.3kpc, χ²_v2≈46.9
  - NGC3198: Δv²≈1.76e4, ε=0.0, R_t≈21.1kpc, dR≈8.8kpc, χ²_v2≈115
  - NGC6503: Δv²≈9.5e3, ε=0.0, R_t≈8.23kpc, dR≈3.5kpc, χ²_v2≈41.8
  - DDO170: Δv²≈3.9e3, ε=0.0, R_t≈6.94kpc, dR≈6.72kpc, χ²_v2≈1.57
  - DDO168: Δv²≈2.1e3, ε=0.0, R_t≈1.92kpc, dR≈0.65kpc, χ²_v2≈0.17
  → dwarf系では v2 が v1 共通カーネルより自然な形と良好なχ²を返す。L* スパイラルでも「外縁Δv²プラトー＋内側Newton」の振る舞いが明確で、オフセットを後段で混ぜる設計の方がFDBの描像に近い。
  
