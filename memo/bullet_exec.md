# 符号反転（全球）をさらに前進させる研究指示（単一MD版）
**版**: 2025‑09‑15 JST  
**対象**: Bullet（1E 0657‑56）ホールドアウト／学習クラスタ（Abell 1689・CL0024）  
**位置づけ**: 本ファイルが最新・唯一の実行指示（更新は全置換）

> **記号対応（v2 パラメタ）**: θ_opt = {τ₀, ω₀, p}, θ_if = {η, s_gate, q_knee}, θ_aniso = {g}。旧表記との換算は τ₀ = α·Σ_ref (Σ_ref=1), ω₀ = ξ/(1+ξ), g = β/(1+β), η = δ_τ/τ。

---

## 0) 目的・KPI・採否基準
- **目的**: 残差 `R≡κ_obs−κ_theory` と `Σ_e` の **全球負相関**（“レンズ影”）を実現。
- **KPI‑A（符号）**: global **Spearman(R,Σ_e) < 0** かつ **p < 0.05**。付帯: **partial r(R,Σ_e|r) < 0** を **global / core(r≤r50) / outer(r≥r75)** の三域で達成。  
- **KPI‑B（適合）**: **固定パラ**のまま **ΔAICc(FDB−shift) ≤ −10**（rot/shuffle も < 0）を維持。  
- **KPI‑C（監査）**: AICc 表に **(N,k)** と **処理条件（PSF/高通過/マスク/ROI/整準/rng）**、Permutation/Bootstrap（**p_perm/CI**）を恒常掲示。  
- **採否**: KPI‑A〜C を全て満たした構成を採択。数値はバレット・ホールドアウトページに常設。  
  _根拠（現状）_: ΔAICc は合格域、全球符号は正、top75/90% で負転の芽を確認。  [oai_citation:5‡Agent Gate](https://agent-gate.s21g.com/moon/67279209d81d4e890c28cbd088d8cd58396dfbe1c729eea299acfa74b3661ffa/%40localhost%3A3131/reports/bullet_holdout.html)

---

## 1) 物理クロージャの「面・高密度選好」を増強（理論枠内・最小拡張）
**狙い**: Cov(κ_FDB, Σ_e) を正へ押し上げ、低〜中 Σ_e の“面積優勢”を抑え、**global の負符号**を実現。

### 1‑A. 界面ゲート S の強化（多重スケール×急峻化）
- **実装**: 勾配 `|∇ω_p|` を **σ_g∈{2,4,8} pix** で計算し **max 合成**。  
- **ゲート**: `S = σ((|∇ω_p|−τ)/δ_τ)·[n·r]_+`（δ_τ = η·τ）。  
  **走査**: `τ_q∈{0.70,0.75,0.80}`, `η∈{0.10,0.15,0.20}`, `s_gate∈{12,16,24,32}`。  
- **規約**: (N・誤差床・整準・PSF/高通過・rng) は**全候補で固定**。  
- **期待**: outer 域の負化を安定化し、global への波及を促進。  
  _根拠_: 現行 top75/90% で負転の芽を確認（global は正）。  [oai_citation:6‡Agent Gate](https://agent-gate.s21g.com/moon/67279209d81d4e890c28cbd088d8cd58396dfbe1c729eea299acfa74b3661ffa/%40localhost%3A3131/reports/bullet_holdout.html)

- **置換**: `W = exp(-τ₀ Σ_e) + \\frac{ω₀}{1-ω₀} \,[max(0, Σ_e - Σ_{q_\text{knee}})]^p`  
- **走査**: `q_knee∈{0.6,0.7,0.8}`, `p∈{0.7,1.0,1.3}`, `ω₀/(1-ω₀) ∈ {1,2,3}`（legacy ξ と同値）。  
- **目的**: 低〜中 Σ_e 域の寄与を切り落とし、**高密度・界面主導**へ。  
  _注_: q_knee は現状 0.8 既採用。上限側の最適化と ξ_sat の再調整で global 反転を狙う。  [oai_citation:7‡Agent Gate](https://agent-gate.s21g.com/moon/67279209d81d4e890c28cbd088d8cd58396dfbe1c729eea299acfa74b3661ffa/%40localhost%3A3131/reports/bullet_holdout.html)

### 1‑C. Σ_e 変換の比較（ダイナミックレンジ整流）
- **候補**: `{identity, asinh, log1p, rank}`（現行 log1p）。  
- **指針**: rank は上位コントラストを潰しやすい → **asinh/log1p** を第一候補に、**低域の影響を弱めつつ上位域のコントラスト保持**。

### 1‑D. g（前方化）× PSF/高通過 の同時最適化
- **格子**: `g∈{0.29,0.38,0.44,0.50}`（legacy β={0.4,0.6,0.8,1.0} に対応）× `σ_psf∈{1.2,1.5,1.8}` × `σ_highpass∈{6,8,10}`。  
- **公平**: (N,k) と処理条件を**本文と表で完全一致**。θ_aniso の自由度 g は AICc の k に計上。  
- **補足**: 現行スイープでは g≈0.29（β≈0.4）付近が最良傾向。  [oai_citation:8‡Agent Gate](https://agent-gate.s21g.com/moon/67279209d81d4e890c28cbd088d8cd58396dfbe1c729eea299acfa74b3661ffa/%40localhost%3A3131/reports/bullet_holdout.html)

---

## 2) 評価系の“地ならし”（交絡除去と検定力の底上げ）
**狙い**: 半径・整準・自己相関による擬相関を排除し、**符号判定を堅牢化**。

### 2‑A. 整準の厳密化を恒常運用
- WCS → **FFT相互相関→サブピクセル補正（Lanczos3）** を **FDB/rot/shift/shuffle に完全一致**で適用。  
- 脚注へ **(Δy,Δx)、wrap(dy,dx)、rng_seed** を恒常掲示（現行 (16,37)/(12,−7), rng=42）。  [oai_citation:9‡Agent Gate](https://agent-gate.s21g.com/moon/67279209d81d4e890c28cbd088d8cd58396dfbe1c729eea299acfa74b3661ffa/%40localhost%3A3131/reports/bullet_holdout.html)

### 2‑B. Permutation / Bootstrap を常時掲載
- 位相乱数 Permutation: **n≥5000**（one‑sided toward negative の **p_perm** を掲載）。  
- **空間ブロック Bootstrap**: ブロック径は半変動関数で推定し **95% CI** を併記。  
- **採否**: **p_perm<0.05** かつ CI が負領域を跨がない構成を採択。  
  _根拠_: 現状 **p_perm=0.92**、CI は正側 → 反転が必要。  [oai_citation:10‡Agent Gate](https://agent-gate.s21g.com/moon/67279209d81d4e890c28cbd088d8cd58396dfbe1c729eea299acfa74b3661ffa/%40localhost%3A3131/reports/bullet_holdout.html)

### 2‑C. マスク・スケール頑健性
- マスク `{coverage, top50, top75, top90}` と σ_psf/高通過 σ を**同条件で再評価**。  
- **採否**: 負符号と ΔAICc の結論が**設定間で同方向**なら合格。  
  _根拠_: 現行 **top75/90% で負転**を確認済（global は正）。  [oai_citation:11‡Agent Gate](https://agent-gate.s21g.com/moon/67279209d81d4e890c28cbd088d8cd58396dfbe1c729eea299acfa74b3661ffa/%40localhost%3A3131/reports/bullet_holdout.html)

---

## 3) 局所「影」指標で全球判定を補強（方向情報の明示）
**狙い**: ∇場の向き整合で“影”を直接測り、全球 Spearman の判断を補強。

### 3‑A. 影整合指数 `S_shadow`
- **定義**: `S_shadow = ⟨ − ȷ∇Σ_e · ȷ∇R ⟩`（単位ベクトルの内積の負平均）。  
- **要件**: global/core/outer で算出、Permutation **n≥5000** で **p_perm** 掲示。  
- **目標**: **S_shadow>0（p_perm<0.05）**。  
  _現状_: global=−0.014（未計算扱い）→ 反転必須。  [oai_citation:12‡Agent Gate](https://agent-gate.s21g.com/moon/67279209d81d4e890c28cbd088d8cd58396dfbe1c729eea299acfa74b3661ffa/%40localhost%3A3131/reports/bullet_holdout.html)

### 3‑B. 境界帯域の二値検定
- **手順**: `|∇ω_p|>τ` 等値線帯で内外を分け、**外側の R<0 比率が 0.5 を超えるか**を binomial/Fisher で検定。  
- **目標**: **外側優勢（p<0.05）**。界面ゲートの物理的一貫性を提示。

---

## 4) ページ恒常化（第三者がページ単体で判定できる状態へ）
- κ_tot/κ_obs 重畳・差分 R マップを常設（**共通カラーバー・軸・参照点**を明記）。  
- AICc 表に **(N,k), rχ², PSF/高通過/マスク/ROI/整準/rng** を**本文条件と完全一致**で固定。  
- Permutation/Bootstrap の **p_perm / CI** を脚注に恒常掲示。  
- 環境ログ（`lenstool -v`, `ciaover`）と `shared_params_sha` を常掲（`ciaover` 欠落表示は修正）。  [oai_citation:13‡Agent Gate](https://agent-gate.s21g.com/moon/67279209d81d4e890c28cbd088d8cd58396dfbe1c729eea299acfa74b3661ffa/%40localhost%3A3131/reports/bullet_holdout.html)

---

## 5) 実装メモ（最小変更点）
- フラグ: `--interface-gate`（`τ_q, δ_τ/τ, s_gate, multi-scale`）／`--use-reemission`（`q_knee, ξ, p, ξ_sat`）／`--beta`／`--sigma-psf`／`--sigma-highpass`／`--se-transform {id,log1p,asinh,rank}`。  
- **AICc の k 自動集計**（τ₀, g, C, ω₀/(1-ω₀), p, η と整準2自由度）。  
- 相関: Spearman/Pearson/partial（半径制御）をユーティリティ化。Permutation（位相乱数 n≥5000）とブロックBootstrapを共通関数に。  
- 脚注自動化: 整準量・処理条件・rng・sha を HTML に自動注入。

---

## 6) 実行チェックリスト
- [ ] **界面ゲート強化**（多重スケール・急峻化）のグリッド探索（1‑A）。  
- [ ] **W_eff に膝**を導入し（既存 0.8 を基点に）ξ/ξ_sat・p を最適化（1‑B）。  
- [ ] **Σ_e 変換**（asinh/log1p ほか）× **g×PSF/高通過** を直交格子で評価（1‑C/D）。  
- [ ] global/core/outer の **Spearman/partial** を再計算、Permutation **n≥5000**／ブロックBootstrap **CI** を併記（2‑B）。  
- [ ] **S_shadow** と **境界帯域二値検定** を実装・掲載（3‑A/B）。  
- [ ] AICc表（N,k,rχ²）・処理条件・整準ログ・rng・sha を**常設**（4）。

---

## 7) Definition of Done（今回スプリント）
1) **全球PASS**: **global Spearman(R,Σ_e)<0, p<0.05**（partial r<0、core/outer でも負）。  
2) **適合維持**: 固定パラのまま **ΔAICc(FDB−shift) ≤ −10**（rot/shuffle も < 0）。  
3) **監査完了**: AICc 表（N,k,rχ²）・処理条件・Permutation/Bootstrap（p_perm/CI）・整準ログ・sha を数値で恒常化。

---
**根拠ページ**: SOTA トップ（更新・共有ハイパラ・方針・バレット要約）と、バレット・ホールドアウト（ΔAICc・三指標・マスク依存・partial/Permutation/Bootstrap・処理条件）。  [oai_citation:14‡Agent Gate](https://agent-gate.s21g.com/moon/67279209d81d4e890c28cbd088d8cd58396dfbe1c729eea299acfa74b3661ffa/%40localhost%3A3131/state_of_the_art/index.html)
