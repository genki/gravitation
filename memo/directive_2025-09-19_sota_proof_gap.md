#!/usr/bin/env memo

# SOTA再評価と「証明（=100）」までのギャップを埋める研究指示 — 単一MD版
**日付**: 2025-09-19 (JST)  
**対象**: SOTA 全体（単一銀河ベンチ／クラスタ・ホールドアウト／初期宇宙ブロック）、再現性、データ在庫  
**このファイルが最新・唯一の研究指示書（更新時は全置換）**

---

## 1) 現況評価（一次情報の要点）

- **初期宇宙（BAO / Solar / 公平条件）**  
  - BAO は **CLASS 3.3.2.0** で実計算・尤度化済み（BOSS DR12: χ²=3.87 / dof=6, AICc=3.87, p=0.694）。z≈0.57 で **振幅比≈0.994**, **Δk≈0**。Solar 追加加速度は **status=pass**（1 AU 上限内）。フェア条件は `config/fair.json` で **WLS σ・整準・wrap・PSF・高通過・マスク/ROI・rng** を共通化し、**主判定=AICc(FDB−rot/shift)**、shuffle は位相破壊の補助対照として扱う方針が明示。  [oai_citation:0‡Agent Gate](https://agent-gate.s21g.com/moon/67279209d81d4e890c28cbd088d8cd58396dfbe1c729eea299acfa74b3661ffa/%40localhost%3A3131/state_of_the_art/index.html)
- **単一銀河ベンチ**  
  - **NGC 3198**: AICc（GR 7051 / MOND 21665 / GR+DM 7056 / **FDB 192**）、rχ²（GR 167.8 / **FDB 4.70**）。N・N_eff・誤差・ペナルティはモデル間で公正化。  [oai_citation:1‡Agent Gate](https://agent-gate.s21g.com/moon/67279209d81d4e890c28cbd088d8cd58396dfbe1c729eea299acfa74b3661ffa/%40localhost%3A3131/reports/bench_ngc3198.html)  
  - **NGC 2403**: AICc（GR 81666 / MOND 48305 / GR+DM 81670 / **FDB 498**）、rχ²（GR 1134 / **FDB 7.09**）。  [oai_citation:2‡Agent Gate](https://agent-gate.s21g.com/moon/67279209d81d4e890c28cbd088d8cd58396dfbe1c729eea299acfa74b3661ffa/%40localhost%3A3131/reports/bench_ngc2403.html)
- **クラスタ・ホールドアウト（バレット）**  
  - 公平条件下で **ΔAICc(FDB−rot)=−6.77×10⁷**, **ΔAICc(FDB−shift)=−6.72×10⁶**（大きく負）。方向性は **S_shadow=0.373**, **p_perm≈0.004**（one‑sided, n=10,000, q_FDR≈0.040）。R–Σ_e の全球相関は **Spearman=−0.440**（負が期待）。再現コマンド・(N,N_eff,k,χ²)・rng が脚注に固定。  [oai_citation:3‡Agent Gate](https://agent-gate.s21g.com/moon/67279209d81d4e890c28cbd088d8cd58396dfbe1c729eea299acfa74b3661ffa/%40localhost%3A3131/reports/bullet_holdout.html)

> **総評**: 銀河（×2）とクラスタ（×1）で**適合と方向性の強い証拠**が整いつつある。残課題は **(i) マルチ・クラスタへの汎化、(ii) 方向指標の余裕有意と報告同期、(iii) 宇宙論の広帯域尤度拡張、(iv) 公開1‑Click再現の恒常化、(v) 記号／設定の完全同期**。

---

## 2) ギャップ（不足点）の明示

1. **汎化不足（学習→凍結→新ホールドアウトの複線化）**  
   - クラスタはバレット1系統のみ。SOTAには **A1689/CL0024: READY**、他2系（MACSJ0416, Abell S1063）は FITS 欠品。  [oai_citation:4‡Agent Gate](https://agent-gate.s21g.com/moon/67279209d81d4e890c28cbd088d8cd58396dfbe1c729eea299acfa74b3661ffa/%40localhost%3A3131/state_of_the_art/index.html)
2. **方向性の“余裕有意”と報告同期**  
   - バレット S_shadow は **有意（p≈0.004）**だが、core/outer の詳細や設計（帯域・マスク）最適化の余地と、トップ↔詳細の**数値完全同期**が必要。  [oai_citation:5‡Agent Gate](https://agent-gate.s21g.com/moon/67279209d81d4e890c28cbd088d8cd58396dfbe1c729eea299acfa74b3661ffa/%40localhost%3A3131/reports/bullet_holdout.html)
3. **宇宙論の広帯域尤度が未接続**  
   - BAO は実装済みだが、**RSD(fσ₈), 弱レンズ2PCF, CMB(TT/TE/EEピーク高さ・比)**の軽量尤度が未統合。  [oai_citation:6‡Agent Gate](https://agent-gate.s21g.com/moon/67279209d81d4e890c28cbd088d8cd58396dfbe1c729eea299acfa74b3661ffa/%40localhost%3A3131/state_of_the_art/index.html)
4. **公開 1‑Click 再現**  
   - 再現スクリプトは頁脚注にあるが、**Docker/conda＋seed固定**の CI で主要図表・数値を**閾値一致**させる「公開一発」経路の恒常化が必要。  [oai_citation:7‡Agent Gate](https://agent-gate.s21g.com/moon/67279209d81d4e890c28cbd088d8cd58396dfbe1c729eea299acfa74b3661ffa/%40localhost%3A3131/reports/bench_ngc3198.html)
5. **表記／設定の完全同期**  
   - SOTAトップは新パック（τ₀, ω₀, g, η…）だが、バレット頁は一部に旧記号（α,β,ξ…）が残る。`fair.json` の **sha** もページ間で異なる箇所があり、**単一の sha** へ統一して再生成が必要。  [oai_citation:8‡Agent Gate](https://agent-gate.s21g.com/moon/67279209d81d4e890c28cbd088d8cd58396dfbe1c729eea299acfa74b3661ffa/%40localhost%3A3131/state_of_the_art/index.html)

---

## 3) 研究指示（P0: 直近スプリント／P1: 次スプリント）

### P0（今スプリントで完遂）

**P0‑1｜クラスタ：方向性の余裕有意化＋報告同期（バレット）**  
- **帯域固定**: 実空間 **4–8 pix / 8–16 pix** の輪帯で \(R,\Sigma_e\) を共通バンドパス化し、帯域別 **band‑S_shadow** を算出→\(|∇\Sigma_e|\) 分位で重み付け合成。  
- **界面マスク**: \(|∇\omega_p|\) 分位 \(q_{\rm edge}\in\{0.70,0.75,0.80\}\) ＋露光/SN 閾、**closing→opening** で形態整形。  
- **検定**: Permutation **n≥10,000**（空間ブロック、rng固定）、**Q2=⟨cos2θ⟩** を補助指標として併記。  
- **DoD**: **S_shadow>0 & p_perm<0.01**（global 合成帯域）。トップと詳細頁の **S_shadow / p_perm / (N,N_eff,k,χ²)** を**完全一致**に更新。  [oai_citation:9‡Agent Gate](https://agent-gate.s21g.com/moon/67279209d81d4e890c28cbd088d8cd58396dfbe1c729eea299acfa74b3661ffa/%40localhost%3A3131/reports/bullet_holdout.html)

**P0‑2｜AICc 公平条件の単一 JSON 化・sha 固定**  
- `config/fair.json` を**唯一の参照**として sha をトップと一致（SOTA 表示の sha に統一）→ **FDB/rot/shift/shuffle の全ランが同一設定**で走るよう保証。  
- すべての AICc 表に **(N, N_eff, k, χ², rχ²)** を本文条件そのまま自動差し込み（sha と実行コマンドを脚注常設）。  [oai_citation:10‡Agent Gate](https://agent-gate.s21g.com/moon/67279209d81d4e890c28cbd088d8cd58396dfbe1c729eea299acfa74b3661ffa/%40localhost%3A3131/state_of_the_art/index.html)

**P0‑3｜BAO 図の恒常化（既存）＋“広帯域”準備**  
- Fig‑EU1c は **CLASS 実計算＋尤度**を維持（version/ini/sha を脚注継続）。  
- 後続の RSD / 弱レンズ / CMB 用に **軽量尤度ラッパ**（データ→ベクトル化→χ²）を雛形作成。  [oai_citation:11‡Agent Gate](https://agent-gate.s21g.com/moon/67279209d81d4e890c28cbd088d8cd58396dfbe1c729eea299acfa74b3661ffa/%40localhost%3A3131/state_of_the_art/index.html)

**P0‑4｜公開 1‑Click 再現（CI）**  
- `docker/` と `environment.yml` を整備して `make repro` で **3198/2403/バレット/BAO** を再生成。  
- CI で **数値閾値一致**（AICc, S_shadow, 相関, BAO χ²）と **リンク監査（used_ids/notifications→200）** を通し、ステータスを**緑安定**に。  [oai_citation:12‡Agent Gate](https://agent-gate.s21g.com/moon/67279209d81d4e890c28cbd088d8cd58396dfbe1c729eea299acfa74b3661ffa/%40localhost%3A3131/reports/bench_ngc3198.html)

**P0‑5｜記号／共有パラの完全同期**  
- 全ページを **τ₀, ω₀, g, η, q_knee** に統一（旧→新換算の脚注を常設）。  
- `shared_params.json` の **sha** をトップ・ベンチ・バレットで一致させ、数値・脚注・表を同時更新。  [oai_citation:13‡Agent Gate](https://agent-gate.s21g.com/moon/67279209d81d4e890c28cbd088d8cd58396dfbe1c729eea299acfa74b3661ffa/%40localhost%3A3131/state_of_the_art/index.html)

---

### P1（次スプリントで完遂）

**P1‑1｜サンプル拡張（学習→凍結→新ホールドアウト）**  
- **学習**: **Abell 1689 / CL0024** を `run_holdout_pipeline.py --auto-train` で学習→**凍結**。  
- **新ホールドアウト**: **衝突クラスタ×1**（例: MACSJ0416 or Abell S1063）を対象に、欠品 FITS（omega_cut/sigma_e/kappa_obs）を整備（ヘッダに `PIXKPC` 必須）。  
- **DoD**: **ΔAICc(FDB−shift)≤−10**（公平条件）と **S_shadow p_perm<0.01** を再現。  [oai_citation:14‡Agent Gate](https://agent-gate.s21g.com/moon/67279209d81d4e890c28cbd088d8cd58396dfbe1c729eea299acfa74b3661ffa/%40localhost%3A3131/state_of_the_art/index.html)

**P1‑2｜宇宙論の広帯域尤度の段階導入**  
- **RSD (fσ₈)**、**弱レンズ2PCF**、**CMB(TT/TE/EEピーク高さ・比)** の**軽量尤度**を順次追加し、「**壊さない**」範囲を定量化（ΔAICc≈0 目標）。  [oai_citation:15‡Agent Gate](https://agent-gate.s21g.com/moon/67279209d81d4e890c28cbd088d8cd58396dfbe1c729eea299acfa74b3661ffa/%40localhost%3A3131/state_of_the_art/index.html)

**P1‑3｜FDB固有予測の多数天体統計（識別性）**  
- 棒/ディスク/殻の **“陰影方向”**、外縁 **1/r² 復帰半径**と \(|∇\omega_p|\) 分位の相関、**遮蔽非対称**の左右差のうち **2/3 指標で p<0.01** を目標に多数天体で検定（ベンチUIをテンプレ化して横展開）。  [oai_citation:16‡Agent Gate](https://agent-gate.s21g.com/moon/67279209d81d4e890c28cbd088d8cd58396dfbe1c729eea299acfa74b3661ffa/%40localhost%3A3131/state_of_the_art/index.html)

---

## 4) データ入手・作業レシピ（抜粋）

- **Hα（IRSA/SINGS）**: `ngc3198_HA_SUB_dr4.fits` / `ngc2403_HA_dr4.fits + R` を取得→ `scripts/halpha/ingest_halpha.py` で取り込み。  [oai_citation:17‡Agent Gate](https://agent-gate.s21g.com/moon/67279209d81d4e890c28cbd088d8cd58396dfbe1c729eea299acfa74b3661ffa/%40localhost%3A3131/state_of_the_art/index.html)  
- **H I 21 cm（HALOGAS/Zenodo）**: `NGC3198-HR-cube.fits` / `NGC2403-HR-cube.fits` 等を取得→ moment‑1 生成または同梱の `*_mom1m.fits` 利用。  [oai_citation:18‡Agent Gate](https://agent-gate.s21g.com/moon/67279209d81d4e890c28cbd088d8cd58396dfbe1c729eea299acfa74b3661ffa/%40localhost%3A3131/state_of_the_art/index.html)  
- **クラスタ**: A1689 / CL0024 / Bullet の `omega_cut.fits, sigma_e.fits, kappa_obs.fits` を整備（ヘッダに `PIXKPC`）。Lenstool 公式 tarball（a1689.tar.gz / cl0024.tar.gz）を受領→展開→κ 作成→配置。  [oai_citation:19‡Agent Gate](https://agent-gate.s21g.com/moon/67279209d81d4e890c28cbd088d8cd58396dfbe1c729eea299acfa74b3661ffa/%40localhost%3A3131/state_of_the_art/index.html)

> いずれも **SOTA の「不足データ／入手手順」ブロック**と **クラスタ・ホールドアウト準備表**に沿って実施。  [oai_citation:20‡Agent Gate](https://agent-gate.s21g.com/moon/67279209d81d4e890c28cbd088d8cd58396dfbe1c729eea299acfa74b3661ffa/%40localhost%3A3131/state_of_the_art/index.html)

---

## 5) Definition of Done（今回=P0）

1. **方向性**: バレットで **S_shadow>0 & p_perm<0.01**（設計固定・ブロックPermutation・rng固定）。トップ↔詳細の数値が**完全一致**。  [oai_citation:21‡Agent Gate](https://agent-gate.s21g.com/moon/67279209d81d4e890c28cbd088d8cd58396dfbe1c729eea299acfa74b3661ffa/%40localhost%3A3131/reports/bullet_holdout.html)  
2. **適合**: 公平条件（単一 `fair.json`）下で **ΔAICc(FDB−shift)≤−10** を恒常化（rot も負、shuffle は補助欄）。  [oai_citation:22‡Agent Gate](https://agent-gate.s21g.com/moon/67279209d81d4e890c28cbd088d8cd58396dfbe1c729eea299acfa74b3661ffa/%40localhost%3A3131/state_of_the_art/index.html)  
3. **BAO**: Fig‑EU1c を **CLASS 実計算＋尤度**で固定（version/ini/sha 表示継続）。  [oai_citation:23‡Agent Gate](https://agent-gate.s21g.com/moon/67279209d81d4e890c28cbd088d8cd58396dfbe1c729eea299acfa74b3661ffa/%40localhost%3A3131/state_of_the_art/index.html)  
4. **再現**: Docker/conda＋seed固定の `make repro` で **3198/2403/バレット/BAO** が 1‑Click 再現、CI 緑安定。  [oai_citation:24‡Agent Gate](https://agent-gate.s21g.com/moon/67279209d81d4e890c28cbd088d8cd58396dfbe1c729eea299acfa74b3661ffa/%40localhost%3A3131/reports/bench_ngc3198.html)  
5. **同期**: 記号（τ₀, ω₀, g, η…）、`shared_params.json` / `fair.json` の **sha**、表の **(N,N_eff,k,χ²,rχ²)**、脚注の **コマンド**が**全ページ一致**。  [oai_citation:25‡Agent Gate](https://agent-gate.s21g.com/moon/67279209d81d4e890c28cbd088d8cd58396dfbe1c729eea299acfa74b3661ffa/%40localhost%3A3131/state_of_the_art/index.html)

---

## 6) リスクと対策

- **設計ドリフト**: `fair.json` / `shared_params.json` の **sha ピン止め**を頁脚注に常設し、自動同期スクリプトでトップを上書き。  [oai_citation:26‡Agent Gate](https://agent-gate.s21g.com/moon/67279209d81d4e890c28cbd088d8cd58396dfbe1c729eea299acfa74b3661ffa/%40localhost%3A3131/state_of_the_art/index.html)  
- **クラスタ欠品**: MACSJ0416 / Abell S1063 は FITS 欠品。最小限 **omega_cut/sigma_e/kappa_obs + PIXKPC** を優先調達（WCS/視野の厳密整合を先に実施）。  [oai_citation:27‡Agent Gate](https://agent-gate.s21g.com/moon/67279209d81d4e890c28cbd088d8cd58396dfbe1c729eea299acfa74b3661ffa/%40localhost%3A3131/state_of_the_art/index.html)  
- **方向性の不安定**: 帯域・マスク・Permutation を固定プロトコル化（rng/ブロック径を明記）して“p値ハンティング”を防止。  [oai_citation:28‡Agent Gate](https://agent-gate.s21g.com/moon/67279209d81d4e890c28cbd088d8cd58396dfbe1c729eea299acfa74b3661ffa/%40localhost%3A3131/reports/bullet_holdout.html)

---

### 付記（運用メモ）
- 3198/2403 の **UI/脚注テンプレ**（外縁1/r²、Hα等高線、ω_cut 誤差伝播、A/B 公平表）は、このまま**多数銀河へ横展開**できる構成になっている。  [oai_citation:29‡Agent Gate](https://agent-gate.s21g.com/moon/67279209d81d4e890c28cbd088d8cd58396dfbe1c729eea299acfa74b3661ffa/%40localhost%3A3131/reports/bench_ngc3198.html)

