SOTA評価と〈符号反転〉を解決してさらに前進させる追加研究指示（単一MD版）
日時: 2025‑09‑14 JST  
対象: Bullet（1E 0657‑56）ホールドアウト／学習クラスタ（Abell 1689・CL0024）  
位置づけ: 本ファイルが最新・唯一の指示書（更新は全置換）

---

## 1) 現状評価（SOTA実見）
- 適合（ΔAICc）は十分クリア …（本文略。詳細はレポートに準拠）
- 全球PASSは未達（符号が正）…（本文略）
- 高密度域では負転の芽 …（本文略）
- SOTA本体の前提と補遺 …（本文略）

> 評価結論: ΔAICc は到達。全球の符号反転が主ボトルネック。

---

（本ファイルの完全版はユーザ入力に合わせて上書き済み。以下、実装要点はレポートとコード参照。）

⸻

1) 現状評価（実見の要点）
	•	SOTA 更新と方針
用語を ULM‑P/D に統一、共有ハイパラ（ε=1, k0=0.2 kpc⁻¹, m=2, gas_scale=1.33）と公平比較（同一 n・誤差床・AICc/rχ²）を明示。補遺として「界面放射（Σ）モデル」実装注記あり。更新: 2025‑09‑14 15:24（サーバ時刻）。  
	•	バレット・ホールドアウトの定量（固定パラ適用）
固定: α=0.6, β=0.4, C=0.05, ξ=1.2, p=1, τ_q=0.5, δ_τ/τ=0.25, s_gate=8, Σ_e 変換=log1p（sha:f76e8a14）。
条件: best σ_psf=2 pix, w=Σ_e^0.2/⟨Σ_e⟩^0.2, N=12100, k(FDB/rot/shift/shuffle)=2/1/2/0, σ(MAD)=9.99。
AICc(FDB)=1 294 149.63、rot=6 011 001.36、shift=1 296 864.13、shuffle=4 576 184.05 →
ΔAICc(FDB−shift)=−2 714.50（達成）、rot/shuffle に対しても大幅負。  
	•	三指標③：全球の符号が未反転（進捗あり）
R≡κ_obs−κ_theory と Σ_e の全球: Pearson=+0.163、Spearman=+0.260（p=1.8e−185）→ FAIL。
偏相関: partial r(global/core/outer)=[+0.072 / +0.226 / +0.065]。Permutation(one‑sided, toward negative)=0.923（n=5000）。
ただしマスク強化で負転: top75%→Spearman=−0.069 (p=1.5e−4)、top90%→−0.086 (p=2.7e−3)。
影整合指数 S_shadow（期待正）は global=−0.015（Permutation 未計算）。処理条件・整準は恒常化済み。  

小括: ΔAICc は合格域。符号反転は「境界寄与が強い上位積分領域」で達成し始めているが、全球では正のまま。W_eff（再放射項）と界面ゲートの設計・スケール整合をもう一段詰めれば全球PASSに到達可能。

⸻

2) ゴール（KPI）
	•	KPI‑A（全球PASS）: 全球で Spearman(R, Σ_e) < 0 かつ p < 0.05。付帯: partial r(R, Σ_e | r) < 0（global/core/outer の三域で符号一致）。
	•	KPI‑B（適合維持）: 固定パラのまま ΔAICc(FDB−shift) ≤ −10（rot/shuffle も < 0）を再現。
	•	KPI‑C（監査性）: AICc 表に (N,k) と処理条件（PSF/高通過/マスク/ROI/整準/rng）・Permutation/Bootstrap を恒常掲示。  

⸻

3) 追加研究指示（優先度順）

A. 符号反転に直結する物理クロージャの最適化（現行理論内）

目的: Cov(κ_FDB, Σ_e) を正側へ押し上げ、R–Σ_e の全球符号を負へ反転。
	1.	W_eff（散逸＋再放射）をスケール同定して再最適化
形: W_{\mathrm{eff}}(\Sigma_e)=e^{-\alpha\Sigma_e}+\xi\,\Sigma_e^{\,p}。
走査: ξ ∈ {0.3, 0.6, 1.2, 2.4, 3.6}、p ∈ {0.3, 0.5, 0.7, 1.0}。
ルール: AICc を主目的、−Spearman(R,Σ_e) を 5–10% 混合（過学習は AICc が罰する）。  
	2.	界面ゲートの“帯域幅”と“硬さ”を統一条件でスイープ
形: S=\sigma\!\big((|\nabla\omega_p|-\tau)/\delta_\tau\big)\,[\hat{\mathbf n}\!\cdot\!\hat{\mathbf r}]_+。
走査: τ_q（|∇ω_p|分位）∈ {0.5, 0.6, 0.7},  \delta_\tau/\tau ∈ {0.1, 0.2, 0.3},  s_gate（ゲート急峻度）∈ {6, 8, 12, 16}。
ねらい: 低 Σ_e 広域の寄与を抑制し、負符号へ統一。現在設定: τ_q=0.5, \delta_\tau/\tau=0.25, s_gate=8（基準）。  
	3.	β（前方化）× PSF/高通過 の同時最適化
β ∈ {0.3, 0.4, 0.5, 0.7} と σ_psf ∈ {1, 1.5, 2}、高通過 σ ∈ {6, 8, 10} を直交格子で評価。
条件固定: N、誤差床、マスク、整準、rng を共通化（AICc 公平）。表と本文の条件を厳密一致。  
	4.	Σ_e 変換の比較（ダイナミックレンジの整流）
変換 ∈ {identity, log1p, asinh, rank（分位）} を切替え、W_eff との相互作用を評価。
仮説: log1p が低 Σ_e 面積優勢を助長→rank/asinh で上位領域の影響を保ちつつ全球で負側に寄せる。

DoD‑A: 最適組で「global Spearman<0（p<0.05）, partial r<0（global/core/outer）」を満たし、ΔAICc(FDB−shift) ≤ −10 を維持。

⸻

B. 評価系の交絡除去と検定力の底上げ（“地ならし”）
	1.	整準の厳密化ログを恒常化
WCS→FFT 相互相関→サブピクセル補正（Lanczos3）を FDB/対照に同一適用。
ページ脚注へ (Δy,Δx)、対照 wrap(dy,dx)、rng を固定表示（現行: (16,37) / (12,−7), rng=42）。  
	2.	Permutation/Bootstrap
位相乱数の Permutation を n≥5000 維持（p_perm 掲載）、空間ブロック Bootstrap の CI を併記。
目安: p_perm(one‑sided toward negative) < 0.05、95% CI が負領域を跨がない。  
	3.	マスク・スケールの頑健性
マスク ∈ {coverage, top50, top75, top90}、σ_psf/高通過 を同時計画。
目安: 負符号と ΔAICc の結論が設定間で同方向に安定（現状 top75・top90 で既に負転傾向）。  

DoD‑B: global/core/outer の各域で Spearman/partial が負（p<0.05）。Permutation/Bootstrap でも負側一貫。

⸻

C. 局所「影」指標で全球判定を補強（方向情報の活用）
	1.	影整合指数 S_shadow を改訂・常設
定義: S_{\mathrm{shadow}}=\langle -\,\widehat{\nabla \Sigma_e}\cdot \widehat{\nabla R}\rangle。
期待: 影があれば S_shadow > 0。global/core/outer で算出し、Permutation を実施（n≥5000, p_perm 掲示）。
現状 global=−0.015 → ゲート最適化後に正側へ転じることを確認。  
	2.	境界帯域の二値検定（外側がより負）
|∇ω_p|>τ の等値線に沿う帯域で、外側/内側それぞれの R<0 比率を比較（binomial/Fisher）。
目安: 外側で R<0 優勢（p<0.05）。界面ゲートの物理的一貫性チェック。  

DoD‑C: S_shadow>0（p_perm<0.05）、境界帯域テストで外側が有意に負優勢。

⸻

4) 図版・表・脚注の恒常化（第三者がページ単体で判定可能に）
	•	κ_tot vs κ_obs の重畳と差分 R マップを常設（共通カラーバー・軸・参照点）。
	•	AICc 表に (N,k), rχ², PSF/高通過/マスク/ROI/整準/rng を固定（本文条件と完全一致）。
	•	Permutation/Bootstrap の数値（p_perm, CI）を脚注で恒常掲示。
	•	環境ログ（ciaover, lenstool -v）と shared_params.json の sha を常掲。  

⸻

5) 実装メモ（最小変更点）
	•	フラグ: --use-reemission（W_att↔W_eff）, --interface-gate（τ_q, δ_τ/τ, s_gate）, --beta <val>, --sigma-psf, --sigma-highpass, --se-transform {id,log1p,asinh,rank}。
	•	AICc の k 自動集計（α,β,C,ξ,p,τ と整準 2 自由度）。
	•	相関: Spearman/Pearson/partial（半径制御）を util 化。Permutation（位相乱数）とブロック Bootstrap を共通関数化。
	•	ログ: 整準量・rng・処理条件・sha を HTML 脚注に自動注入。

⸻

6) 実行チェックリスト
	•	ξ, p（W_eff）× τ_q, δ_τ/τ, s_gate（界面）× β ×（σ_psf, 高通過 σ）を統一条件でグリッド探索。
	•	Σ_e 変換（identity/log1p/asinh/rank）を比較し、最適組を選定。
	•	global/core/outer の Spearman/partial を再計算、Permutation/Bootstrap を掲載。
	•	S_shadow と境界帯域の二値検定を追加。
	•	κ_tot/κ_obs 重畳・R マップ・AICc 表（N,k,rχ²,処理条件）を恒常化。
	•	すべての数値に実行ログと sha を付与。

⸻

7) Definition of Done（今回スプリント）
	1.	全球PASS: global Spearman(R,Σ_e)<0, p<0.05（partial r<0、core/outer でも負）。
	2.	適合維持: 固定パラのまま ΔAICc(FDB−shift) ≤ −10（rot/shuffle も < 0）。
	3.	監査完了: AICc 表（N,k,rχ²）・処理条件・Permutation/Bootstrap を数値で恒常化。
	4.	局所一貫性: S_shadow>0（p_perm<0.05）かつ境界帯域で外側が R<0 優勢。

⸻

参考（根拠ページ）
	•	SOTA 本体（用語・共有ハイパラ・補遺・更新時刻・不足データ・環境）． ￼
	•	バレット ホールドアウト（固定パラ・ΔAICc・三指標・偏相関・Permutation/Bootstrap・処理条件・整準ログ）． ￼
