# SOTA進捗レビュー（text版）＋「証明完了」ギャップ解消の研究指示（単一Markdown）

**版:** 2025‑09‑29  
**対象:** SOTA（State of the Art）サイト全体の**前回からの進展評価**と、**証明完了（Definition of Done; DoD）**に到達するための**実行可能な研究指示**

---

## 0) エグゼクティブサマリー

- 代表比較図（rep6）の体裁統一と“Total基準”化が完了。先頭2図の形式差も解消し、FDBは“合成（Total）”を太線、追加は補助破線として明確化。AICcと(N,k)、誤差床、rngが脚注に常設され、監査性が向上。([Agent Gate][1])
- 代表6の結果: Phi·eta（情報流）は6銀河中1勝、中央値ΔAICc=+278.63（Phi·eta−W·S）。一方、公平スイープ（3198/2403）では銀河依存の反転が明示（3198はW・S優位、2403はPhi・eta優位）。([Agent Gate][1])
- 単一銀河ベンチは統計が整理され、FDBがAICc/χ²で圧倒的改善（例: NGC 3198: AICc≈192 vs GR≈7051 / GR+DM≈7056、NGC 2403: AICc≈498 vs GR≈81666 / GR+DM≈81670）。([Agent Gate][2])
- クラスタ・ホールドアウト: BulletはΔAICcで大勝かつS_shadow>0, p_perm≈0.002を達成。Abell S1063 / MACS J0416はΔAICcは達成しつつ、方向性（S_shadowの有意）が未達。([Agent Gate][3])
- 宇宙論カード（WL 2PCF / CMBピーク）は軽量尤度で「壊さない（ΔAICc≈0）」確認まで到達。正式の理論写像・同一共分散での提示は未達。([Agent Gate][4])
- 環境・データ: Lenstool/CIAOは検出済だが、Python lenstoolsは未導入。また、A1689/CL0024 の κ_obs 整備が必要と明記。サイトは 2025‑09‑29 05:27 時点で更新。([Agent Gate][5])

---

## 1) 前回からの具体的進展（差分ログ的レビュー）

1. 用語と物理設計の統一: 「ULW → ULM」へ語彙統一、帯域はULM‑P/Dで明確化。共有ハイパラ（ε=1, k0=0.2, m=2, gas_scale=1.33）をサイト横断で固定。合計χ²（GR vs ULM）も掲出。([Agent Gate][5])
2. 代表比較図（rep6）の再計算と体裁統一: 「テンプレv2／Total基準」への移行、勝率やΔAICcの中央値・IQR・効果量dの併記、(N,k)・誤差床・rngの固定表示を実装。([Agent Gate][1])
3. A/B公平スイープの公開: 3198/2403でk=2（Υ★, α(κ)）を同時最小二乗、同一N/誤差床・AICcでのΔAICcとrχ²を明示。銀河依存の優劣反転が可視化。([Agent Gate][6])
4. 単一銀河ベンチの監査性向上: 3198/2403にて横並び統計（AICc/χ²/rχ², (N,k)）と外縁1/r²の傾き、残差×Hα等高線、幾何系統の可視化を整備。([Agent Gate][2])
5. クラスタ・ホールドアウトの前進: BulletでΔAICc大勝＋方向性S_shadowの有意達成（Permutation/Bootstrapの指標掲示含む）。Abell S1063/MACS J0416はΔAICc達成だが方向性未達と原因・再走計画を明記。([Agent Gate][3])
6. 宇宙論（軽量版）の導入: WL 2PCF と CMBピークでΔAICc≈0を確認（同一予測）。最終版への移行方針を注記。([Agent Gate][4])
7. 運用・不足データ・環境の明文化: κ_obs の入手・PIXKPC要件、lenstools 導入要請、環境ログの指示をSOTAに常掲。更新タイムスタンプを明示。([Agent Gate][5])

---

## 2) 「証明完了（DoD）」に対する現存ギャップ

**DoD想定（4本柱）**  
P1: 銀河回転曲線（代表ベンチ/代表6）での公平条件下ΔAICc<0の再現と残差・外縁指標の整合  
P2: クラスタHO（Bullet, Abell S1063, MACS J0416）でΔAICc達成＋方向性有意（S_shadow>0, p_perm<0.05）  
P3: 宇宙論（CMBピーク/WL 2PCF）で正式写像＋同一共分散下のΔAICc≈0の提示  
P4: 太陽系整合・環境ログ・再現手順の恒常化

- P2: Abell S1063（S_shadow=0.646, p≈0.15）、MACS J0416（S_shadow=0.217, p≈0.34）→ 方向性未達（WCS/PSF/ROI/マスク・ゲート設定の再最適化が必要）。([Agent Gate][7])
- P3: WL/CMBは軽量尤度段階で「壊さない」確認のみ。CLASS等での正式写像・共分散同一化が未了。([Agent Gate][4])
- P4: lenstools未導入、A1689/CL0024のκ_obs整備・`ciaover`欠落表示など環境/データの穴が残存。([Agent Gate][5])

---

## 3) 研究指示（ギャップを埋めるための具体作業）

### A. クラスタHOの方向性（影）を有意化（Abell S1063 / MACS J0416）
目標: **global Spearman(R,Σ_e)<0, p<0.05** と **S_shadow>0（p_perm<0.05）** を、**ΔAICc達成を保ったまま**満たす。

1) 整準・処理の完全統一（恒常化）  
- **WCS → FFT相互相関 → サブピクセル補正（Lanczos3）**を**FDB/rot/shift/shuffle**全てに共通適用（脚注に (Δy,Δx)、wrap(dy,dx)、rng=42 を表示）。([Agent Gate][3])  
- Acceptance: ページ脚注で**整準ログ**が**全方式一致**。

2) 界面ゲートSの多重スケール×急峻化  
- `|∇ω_p|` を **σ_g∈{2,4,8}** で計算し **max合成**。`τ_q∈{0.70,0.75,0.80}`, `η∈{0.10,0.15,0.20}`, `s_gate∈{12,16,24,32}` を格子探索。([Agent Gate][8])  
- Acceptance: **global/core/outer の Spearman と partial** が**負**、**p<0.05**。

3) 再放射重み（W_eff）への膝導入  
- `q_knee∈{0.6,0.7,0.8}`, `p∈{0.7,1.0,1.3}`, `ω₀/(1−ω₀)∈{1,2,3}` を直交探索（既定 q_knee=0.8 から上限側を強化）。([Agent Gate][8])  
- Acceptance: **ΔAICc(FDB−shift)≤−10**を維持しつつ**S_shadow>0（p_perm<0.05）**。

4) Σ_e 変換× g × PSF/高通過 の直交格子  
- 変換 `{identity, asinh, log1p, rank}` × `g∈{0.29,0.38,0.44,0.50}` × `σ_psf∈{1.2,1.5,1.8}` × `σ_highpass∈{6,8,10}`。([Agent Gate][8])  
- Acceptance: **負符号**と**ΔAICcの結論**が設定間で**同方向**。Permutation **n≥5000**／ブロックBootstrap **CI**を併記。

5) 方向性可視化の常設（S_shadow / 境界帯域検定）  
- `S_shadow=⟨−ĵ∇Σ_e·ĵ∇R⟩` を global/core/outer で算出、Permutation **n≥5000** を併記。**境界帯域（二値）**は `|∇ω_p|>τ` 外側での **R<0比率>0.5** を検定。([Agent Gate][3])  
- Acceptance: **S_shadow>0（p_perm<0.05）** と **帯域外優勢（p<0.05）**。

### B. 銀河（代表6／ベンチ）の公平性と解釈性の仕上げ
1) rep6の“Total基準”と脚注統一の維持（テンプレv2）  
- **Total=太線／追加=薄破線**、**(N,k)/AICc/rχ²/誤差床/rng**を**全図で常設**。([Agent Gate][1])  
- Acceptance: rep6の6図すべてが**同一テンプレ**・**脚注一致**（AICc表と数値同一）。

2) A/B公平スイープの再走（3198/2403）  
- **同一N/誤差床/ペナルティ（k=2）**で**Υ★とα(κ)**を同時最適化、**ΔAICcとrχ²**を再掲。**銀河依存の反転**の要因（幾何・Hα分布・外縁1/r²）を補助図でリンク。([Agent Gate][6])  
- Acceptance: **ΔAICc数値とrχ²**が**A/Bページとrep6**で**整合**。

3) 外縁1/r²と残差×Hαの恒常化  
- **上位30%半径での g(R)R² 傾き±95%CI**、**残差ヒート×Hα等高線**を全ベンチで常設。([Agent Gate][2])  
- Acceptance: 各ベンチで**傾きとCI**、**残差×Hα**が表示。

### C. 宇宙論カードの正式化（軽量→正式）
1) CLASS連携（例: 3.3.2 系）による Late‑FDB 写像の実装  
- **同一共分散**下で **ΛCDM と Late‑FDB**の**ΔAICc≈0**を提示。現行の軽量版（同一予測）の置換。([Agent Gate][4])  
- Acceptance: WL 2PCF / CMB ピークとも**正式カード**で**ΔAICc≈0**を掲示。

2) ページ脚注の統一  
- (N,k)、誤差床の定義、共分散の出所、CLASSの**バージョン/ini/sha**を明記。

### D. データ・環境の整備
1) κ_obs（A1689/CL0024）の受領→展開→FITS化→PIXKPC付与  
- Lenstool公式モデルtarballの導線に従う。**必須FITS**は `omega_cut.fits, sigma_e.fits, kappa_obs.fits`。([Agent Gate][5])  
- Acceptance: SOTA「必要データ」欄から**sha付き**で参照可能。

2) lenstools の導入  
- `pip install lenstools`、環境表に**導入済**へ更新。`lenstool -v`, `ciaover` のログを**各カード脚注**へ常設。([Agent Gate][5])  
- Acceptance: SOTA環境表で**未導入→導入済**、各ページ脚注から**実行ログ**へ到達可。

3) サイト更新ルールの継続  
- **更新時刻**・**shared_params.sha**・**監査OK表示**（HTTP 200）を維持。([Agent Gate][5])

---

## 4) 受け入れ基準（Definition of Done; 最終版）
- **P1（銀河）:** rep6/ベンチの**Total基準**・**統一脚注**完了。A/B公平スイープの**ΔAICc/rχ²**整合。  
- **P2（クラスタ）:** Bulletに続き、**Abell S1063 / MACS J0416**で**S_shadow>0（p_perm<0.05）**かつ**ΔAICc(FDB−shift)≤−10**を達成。([Agent Gate][7])  
- **P3（宇宙論）:** WL 2PCF / CMB ピークで**正式写像＋同一共分散**の**ΔAICc≈0**を掲示。([Agent Gate][4])  
- **P4（環境・再現性）:** **κ_obs整備・lenstools導入・環境ログ常設**を完了。([Agent Gate][5])

---

## 5) 進捗KPI（現状値の引用）
- **KPI‑1（A/B NGC3198）:** ΔAICc=63.14（k=2）。([Agent Gate][5])
- **KPI‑2（銀河確定版）:** 3198/2403 の外縁1/r²・Hα・ω_cut掲示。([Agent Gate][5])
- **KPI‑3（対照検証）:** rotate n=300 d=0.00 / translate n=200 d=0.02 / shuffle n=2000 d=0.60。([Agent Gate][5])
- **KPI‑4（代表6）:** 表を再計算して更新済み（テンプレv2/Total基準）。([Agent Gate][1])

---

## 6) 実行チェックリスト
- [ ] **HO方向性:** 整準統一／S多重スケール×急峻化／W_eff膝／Σ変換×g×PSF×高通過格子／Permutation≥5000／ブロックBootstrap CI／S_shadow・境界帯域検定の**常設**。([Agent Gate][3])
- [ ] **rep6/ベンチ:** **Total基準**・**脚注帯**の完全統一、A/Bとrep6の**数値整合**。([Agent Gate][1])
- [ ] **宇宙論正式化:** CLASS連携・同一共分散で**ΔAICc≈0**の**正式カード**。([Agent Gate][4])
- [ ] **環境/データ:** κ_obs整備、**lenstools導入**、`lenstool -v`/`ciaover`の**脚注常設**。([Agent Gate][5])

---

## 7) 参考（主要ソース）
- **SOTAトップ**（更新時刻、共有ハイパラ、KPI、環境・不足データ、リンク集）。([Agent Gate][5])  
- **代表6（rep6）**（テンプレv2/Total基準、勝率・中央値・IQR・効果量）。([Agent Gate][1])  
- **A/B公平スイープ**（3198/2403、ΔAICcとrχ²）。([Agent Gate][6])  
- **単一銀河ベンチ**（3198/2403、横並び統計・外縁1/r²・残差×Hα等高線）。([Agent Gate][2])  
- **Bullet HO**（ΔAICc優位、S_shadow有意、Permutation/Bootstrap常設）。([Agent Gate][3])  
- **Abell S1063 / MACS J0416 HO**（ΔAICc達成・方向性未達の現状）。([Agent Gate][7])  
- **WL 2PCF / CMBピーク（軽量）**（ΔAICc≈0の“壊さない”確認）。([Agent Gate][4])

---

### 付: 通知抽出用（運用都合の要約）

## 結果サマリ
- rep6の体裁統一とTotal基準化が完了。ベンチ2頁も脚注帯を統一。
- Bulletは方向性有意達成。Abell S1063/MACS J0416は方向性未達で再最適化を指示。
- 宇宙論カードは軽量版でΔAICc≈0。正式写像＋同一共分散への移行が必要。

## 生成物
- 本メモ: `memo/run_2025-09-29_sota_text_review_and_research_directive.md`
- rep6ページ: `server/public/reports/ws_vs_phieta_rep6.html`
- SOTAトップ: `server/public/state_of_the_art/index.html`

## 次アクション
- HO方向性の有意化（多重スケールS・W_eff膝・Σ変換×g×PSF/高通過格子・Permutation≥5000）。
- A/B公平スイープの再走（3198/2403）とrep6数値の整合。
- 宇宙論カードの正式化（CLASS連携・同一共分散）。
- κ_obs整備・lenstools導入・環境ログの常設。

[1]: https://agent-gate.s21g.com/moon/67279209d81d4e890c28cbd088d8cd58396dfbe1c729eea299acfa74b3661ffa/%40localhost%3A3131/reports/ws_vs_phieta_rep6.html
[2]: https://agent-gate.s21g.com/moon/67279209d81d4e890c28cbd088d8cd58396dfbe1c729eea299acfa74b3661ffa/%40localhost%3A3131/reports/bench_ngc3198.html
[3]: https://agent-gate.s21g.com/moon/67279209d81d4e890c28cbd088d8cd58396dfbe1c729eea299acfa74b3661ffa/%40localhost%3A3131/reports/bullet_holdout.html
[4]: https://agent-gate.s21g.com/moon/67279209d81d4e890c28cbd088d8cd58396dfbe1c729eea299acfa74b3661ffa/%40localhost%3A3131/state_of_the_art/wl_2pcf.html
[5]: https://agent-gate.s21g.com/moon/67279209d81d4e890c28cbd088d8cd58396dfbe1c729eea299acfa74b3661ffa/%40localhost%3A3131/state_of_the_art/index.html
[6]: https://agent-gate.s21g.com/moon/67279209d81d4e890c28cbd088d8cd58396dfbe1c729eea299acfa74b3661ffa/%40localhost%3A3131/reports/ws_vs_phieta_fair.html
[7]: https://agent-gate.s21g.com/moon/67279209d81d4e890c28cbd088d8cd58396dfbe1c729eea299acfa74b3661ffa/%40localhost%3A3131/reports/cluster/AbellS1063_holdout.html
[8]: https://agent-gate.s21g.com/moon/67279209d81d4e890c28cbd088d8cd58396dfbe1c729eea299acfa74b3661ffa/%40localhost%3A3131/state_of_the_art/bullet_exec.html
