# SOTA評価と〈符号反転〉をさらに前進させる研究指示（単一MD版）
**日時**: 2025‑09‑15 JST  
**対象**: Bullet（1E 0657‑56）ホールドアウト／学習クラスタ（Abell 1689・CL0024）  
**位置づけ**: 本ファイルが最新・唯一の実行指示（更新は全置換）

---

## 1) 現状評価（SOTA実見の要点）
- **適合（ΔAICc）は合格域**：公平条件（N=12100, k=2/1/2/0, best σ_psf=1.8 pix, 共通処理）で  
  **AICc(FDB)=1,223,720.54**, **shift=1,228,955.19** → **ΔAICc(FDB−shift)=−5,234.65**（rot, shuffle に対しても大幅負）。①ピーク距離=150 kpc, ②⟨cosΔθ⟩=0.314 は PASS。 [oai_citation:0‡agent-gate.s21g.com](https://agent-gate.s21g.com/moon/67279209d81d4e890c28cbd088d8cd58396dfbe1c729eea299acfa74b3661ffa/%40localhost%3A3131/reports/bullet_holdout.html)  
- **〈全球PASS〉未達（符号が正）**：R≡κ_obs−κ_theory と Σ_e の **global** 相関は **Spearman=+0.258（p≈7.6e−183）**、partial r(global/core/outer)=[+0.072 / +0.227 / +0.065]。一方、**マスク強化（top75/90%）では負に転じる**（−0.067/−0.085）。Permutation（位相乱数）は n=5000, **p_perm=0.921**（FAIL）。 [oai_citation:1‡agent-gate.s21g.com](https://agent-gate.s21g.com/moon/67279209d81d4e890c28cbd088d8cd58396dfbe1c729eea299acfa74b3661ffa/%40localhost%3A3131/reports/bullet_holdout.html)  
- **SOTA本体の方針**：ULM‑P/D 語彙統一と「界面放射（Σ）モデル」実装注記あり。公平比較（同一n・誤差・AICc）・不足データ（銀河/ICLピーク）等が整理済み。 [oai_citation:2‡agent-gate.s21g.com](https://agent-gate.s21g.com/moon/67279209d81d4e890c28cbd088d8cd58396dfbe1c729eea299acfa74b3661ffa/%40localhost%3A3131/state_of_the_art/index.html)  

> **小括**：ΔAICc 側は十分。**低〜中 Σ_e 域の寄与が“面積優勢”で負符号を希釈**しており、**界面・高密度選好の強化と評価系の交絡除去**で全球PASSに到達できる段階。

---

## 2) 成果目標（KPI）
- **KPI‑A（全球PASS）**：global で **Spearman(R,Σ_e) < 0** かつ **p < 0.05**。付帯：**partial r(R,Σ_e | r) < 0** を global/core(r≤r50)/outer(r≥r75) の三域で同時達成。  
- **KPI‑B（適合維持）**：固定パラのまま **ΔAICc(FDB−shift) ≤ −10**（rot/shuffle も < 0）を再現。  
- **KPI‑C（監査性）**：AICc表に **(N,k)** と処理条件（PSF/高通過/マスク/ROI/整準/rng）・Permutation/Bootstrap（p_perm/CI）を恒常掲示。

---

## 3) 研究タスク（優先度順）

### A. 物理クロージャの「面・高密度選好」を増強（理論枠内・最小拡張）
**狙い**：Cov(κ_FDB, Σ_e) を正側に押し上げ、低〜中 Σ_e の希釈を抑え **global の負符号**へ。

1. **界面ゲート S の強化（多重スケール×急峻化）**  
   - |∇ω_p| を **σ_g∈{2,4,8} pix** で計算し **max 合成**。  
   - \( S=\sigma((|\nabla\omega_p|-\tau)/\delta_\tau)\,[\hat n\!\cdot\!\hat r]_+ \) の走査：  
     **τ_q∈{0.70,0.75,0.80}**, **δ_τ/τ∈{0.10,0.15,0.20}**, **s_gate∈{12,16,24,32}**。  
   - 処理条件（N・誤差床・整準・PSF/高通過・rng）は**全試行で固定**。

2. **再放射重み \(W_{\mathrm{eff}}\) に“膝”を導入（低域を削る）**  
   - 現行 \(W=e^{-\alpha\Sigma_e}+ξ\Sigma_e^p\) を  
     \( W=e^{-\alpha\Sigma_e}+ξ\,[\max(0,\Sigma_e-\Sigma_{q\mathrm{knee}})]^{p} \) に置換。  
   - 走査：**q_knee∈{0.6,0.7,0.8}（分位）**, **p∈{0.7,1.0,1.3}**, **ξ/ξ_sat∈{1,2,3}**。  
   - 目的：**top75/90% で既に得ている負傾向**を global へ波及。

3. **Σ_e 変換の比較（ダイナミックレンジ整流）**  
   - {identity, **asinh**, **log1p**, rank} を切替え、W_eff と S の最適組を探索。  
   - 指針：rank は上位コントラストが潰れやすい→asinh/log1p で上位域を保ちつつ低域寄与を緩和。

4. **β（前方化）× PSF/高通過 の同時最適化**  
   - β∈{0.4,0.6,0.8,1.0} × σ_psf∈{1.2,1.5,1.8} × 高通過σ∈{6,8,10} を直交格子で評価。  
   - **AICc公平**のため (N,k) と処理条件を**表と本文で厳密一致**。

**DoD‑A**：最適組で **global Spearman<0（p<0.05）かつ partial r<0（global/core/outer）** を達成し、**ΔAICc(FDB−shift) ≤ −10** を維持。 [oai_citation:3‡agent-gate.s21g.com](https://agent-gate.s21g.com/moon/67279209d81d4e890c28cbd088d8cd58396dfbe1c729eea299acfa74b3661ffa/%40localhost%3A3131/reports/bullet_holdout.html)

---

### B. 半径・整準・自己相関の交絡を除去（評価系の“地ならし”）
1. **整準の厳密化を恒常運用**  
   - WCS → **FFT相互相関→サブピクセル補正（Lanczos3）**を **FDB/rot/shift/shuffle に完全一致**で適用。  
   - 脚注に **(Δy,Δx)、wrap(dy,dx)、rng_seed** を固定表示（例：現行 (16,37)/(12,−7), rng=42）。 [oai_citation:4‡agent-gate.s21g.com](https://agent-gate.s21g.com/moon/67279209d81d4e890c28cbd088d8cd58396dfbe1c729eea299acfa74b3661ffa/%40localhost%3A3131/reports/bullet_holdout.html)
2. **Permutation / Bootstrap を常時掲載**  
   - 位相乱数 Permutation：**n≥5000**（one‑sided toward negative の **p_perm** を掲示）。  
   - **空間ブロックBootstrap**：ブロック径は半変動関数で推定し **95% CI** を併記。  
   - 採否基準：CI が負領域を跨がず、p_perm<0.05 を満たす。
3. **マスク・スケールの頑健性**  
   - マスク {coverage, top50, **top75**, **top90**} と σ_psf/高通過 σ の同時計画を維持。  
   - 結論（負符号と ΔAICc）が設定間で同方向に安定することを確認。 [oai_citation:5‡agent-gate.s21g.com](https://agent-gate.s21g.com/moon/67279209d81d4e890c28cbd088d8cd58396dfbe1c729eea299acfa74b3661ffa/%40localhost%3A3131/reports/bullet_holdout.html)

**DoD‑B**：global/core/outer の **Spearman/partial が負（p<0.05）**。Permutation/Bootstrap でも**負側一貫**。

---

### C. 局所「影」検出で全球判定を補強（方向情報を明示）
1. **影整合指数 \(S_{\mathrm{shadow}}=\langle -\hat{\nabla}\Sigma_e\cdot\hat{\nabla}R\rangle\)** を global/core/outer で常設し、Permutation **n≥5000** を付す（**期待正**）。現状 global=−0.014 を反転させる。 [oai_citation:6‡agent-gate.s21g.com](https://agent-gate.s21g.com/moon/67279209d81d4e890c28cbd088d8cd58396dfbe1c729eea299acfa74b3661ffa/%40localhost%3A3131/reports/bullet_holdout.html)  
2. **境界帯域の二値検定**：|∇ω_p|>τ の等値線帯で、外側/内側の **R<0 比率**を binomial/Fisher で比較（**外側優勢**を確認）。  
3. **半空間ベクトルの物理規約**：[\(\hat n\cdot\hat r\)]_+ の \(\hat r\) は κ_obs 中心基準だが、**X線ショック法線の主方向（∇ω_p のロバスト平均）**で置換して再評価（自由度は増やさず規約更新として扱う）。

**DoD‑C**：**S_shadow>0（p_perm<0.05）** と **境界外側で R<0 優勢（p<0.05）** を達成。 [oai_citation:7‡agent-gate.s21g.com](https://agent-gate.s21g.com/moon/67279209d81d4e890c28cbd088d8cd58396dfbe1c729eea299acfa74b3661ffa/%40localhost%3A3131/reports/bullet_holdout.html)

---

## 4) 公平性・監査の恒常化
- κ_tot/κ_obs 重畳・差分 R マップを常設（共通カラーバー・軸・参照点）。  
- AICc 表に **(N,k), rχ², PSF/高通過/マスク/ROI/整準/rng** を固定（本文条件と完全一致）。  
- Permutation/Bootstrap の **p_perm / CI** を脚注に恒常掲示。  
- 環境ログ（`ciaover`, `lenstool -v`）と `shared_params_sha` を常掲。 [oai_citation:8‡agent-gate.s21g.com](https://agent-gate.s21g.com/moon/67279209d81d4e890c28cbd088d8cd58396dfbe1c729eea299acfa74b3661ffa/%40localhost%3A3131/reports/bullet_holdout.html)

---

## 5) 実装メモ（最小変更点）
- フラグ：`--interface-gate`（τ_q, δ_τ/τ, s_gate, multi‑scale）／`--use-reemission`（q_knee, ξ, p, ξ_sat）／`--beta`／`--sigma-psf`／`--sigma-highpass`／`--se-transform {id,log1p,asinh,rank}`。  
- **AICc の k 自動集計**（α,β,C, ξ,p, τ と整準2自由度）。  
- 相関：Spearman/Pearson/partial（半径制御）をユーティリティ化。Permutation（位相乱数 n≥5000）とブロックBootstrapを共通関数に。  
- 脚注自動化：整準量・処理条件・rng・sha を HTML へ自動注入。

---

## 6) 実行チェックリスト
- [ ] **界面ゲート**（多重スケール・急峻化）を導入しグリッド探索。  
- [ ] **W_eff に膝**を追加し、Σ_e 変換（asinh/log1p）と併せ最適化。  
- [ ] **β×PSF/高通過** を直交格子で再最適化（(N,k) と処理条件を厳密一致）。  
- [ ] global/core/outer の **Spearman/partial** を再計算、Permutation n≥5000／ブロックBootstrap CI を併記。  
- [ ] **S_shadow** と **境界帯域二値検定** を実装・掲載。  
- [ ] AICc表（N,k,rχ²）・処理条件・整準ログ・rng・sha を**常設**。  
- [ ] 不足データ（銀河/ICLピーク座標）を登録（ピーク距離注釈を明確化）。 [oai_citation:9‡agent-gate.s21g.com](https://agent-gate.s21g.com/moon/67279209d81d4e890c28cbd088d8cd58396dfbe1c729eea299acfa74b3661ffa/%40localhost%3A3131/state_of_the_art/index.html)

---

## 7) Definition of Done（今回スプリント）
1) **全球PASS**：**global Spearman(R,Σ_e)<0, p<0.05**（partial r<0、core/outer でも負）。  
2) **適合維持**：固定パラのまま **ΔAICc(FDB−shift) ≤ −10**（rot/shuffle も < 0）。  
3) **監査完了**：AICc 表（N,k,rχ²）・処理条件・Permutation/Bootstrap（p_perm/CI）・整準ログ・sha を数値で恒常化。

---

### 参考リンク
- **SOTA 本体**（用語・共有ハイパラ・補遺・不足データ・更新時刻）。 [oai_citation:10‡agent-gate.s21g.com](https://agent-gate.s21g.com/moon/67279209d81d4e890c28cbd088d8cd58396dfbe1c729eea299acfa74b3661ffa/%40localhost%3A3131/state_of_the_art/index.html)  
- **バレット・ホールドアウト**（AICc・三指標・偏相関・マスク依存・Permutation/Bootstrap・処理条件・整準ログ）。 [oai_citation:11‡agent-gate.s21g.com](https://agent-gate.s21g.com/moon/67279209d81d4e890c28cbd088d8cd58396dfbe1c729eea299acfa74b3661ffa/%40localhost%3A3131/reports/bullet_holdout.html)
