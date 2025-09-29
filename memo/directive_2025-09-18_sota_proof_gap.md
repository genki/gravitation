#!/usr/bin/env memo

# SOTA再評価と「証明」までのギャップを埋める研究指示 — 単一MD版
**版**: 2025-09-18 (JST)  
**対象**: SOTA 全体（単一銀河／クラスタ／初期宇宙）・再現性・データ在庫  
**このファイルが最新・唯一の研究指示書（更新時は全置換）**

---

## 1) 現況評価（一次情報の要点）
- **単一銀河ベンチ**  
  NGC 3198 で **AICc: GR=7051 / GR+DM=7056 / MOND=21665 / FDB=192**,  
  **rχ²: GR=167.8 / FDB=4.70** と大差で FDB が優位。NGC 2403 でも  
  **AICc: GR=81666 / GR+DM=81670 / MOND=48305 / FDB=498**,  
  **rχ²: GR=1134 / FDB=7.09**。いずれも **同一データ・同一誤差・同一ペナルティ**の  
  フェア比較での結果。 [oai_citation:0‡Agent Gate](https://agent-gate.s21g.com/moon/67279209d81d4e890c28cbd088d8cd58396dfbe1c729eea299acfa74b3661ffa/%40localhost%3A3131/reports/bench_ngc3198.html)
- **バレット・クラスタ（ホールドアウト）**  
  AICc では **FDB−rot, FDB−shift が大きく負**で優位。ただし **方向指標  
  S_shadow** は **SOTAトップ要約では 0.151（p_perm=0.002）**と有意だが、  
  **ホールドアウト詳細頁では 0.088（p_perm=0.094）**と **非有意**になっており  
  **数値不整合**が残存。 [oai_citation:1‡Agent Gate](https://agent-gate.s21g.com/moon/67279209d81d4e890c28cbd088d8cd58396dfbe1c729eea299acfa74b3661ffa/%40localhost%3A3131/state_of_the_art/index.html)
- **初期宇宙（BAO）**  
  **CLASS 3.3.2.0 連携**で z≈0.57 の **振幅比≈0.994, Δk≈0** を提示し、  
  **BAO 距離点の尤度**を **χ²=3.87 / dof=6, AICc=3.87, p=0.694** として掲示  
  （“壊さない”ことの定量確認）。 [oai_citation:2‡Agent Gate](https://agent-gate.s21g.com/moon/67279209d81d4e890c28cbd088d8cd58396dfbe1c729eea299acfa74b3661ffa/%40localhost%3A3131/state_of_the_art/index.html)
- **Solar 上限制約・公平条件**  
  Solar ペナルティは **status=pass**。AICc 判定は **fair.json** で **WLS σ,  
  N_eff, PSF/HP, マスク/ROI, 整準, rng** を共有化し、**主判定＝rot/shift、  
  shuffle＝位相破壊の補助対照**という運用が明記。 [oai_citation:3‡Agent Gate](https://agent-gate.s21g.com/moon/67279209d81d4e890c28cbd088d8cd58396dfbe1c729eea299acfa74b3661ffa/%40localhost%3A3131/state_of_the_art/index.html)

> **総評**: 銀河（×2）とクラスタ（×1）で **適合面の強い証拠**は確立。  
> **方向性の有意性（数値同期）**、**サンプル拡張**、**宇宙論の軽量尤度**、  
> **公開一発再現**を埋めれば「証明に準ずる」水準へ到達できる。

---

## 2) ギャップの明示
1. **S_shadow の数値不整合と再現性**：トップ要約と詳細頁で **p_perm が矛盾**  
   （0.002 vs 0.094）。評価設計（帯域・マスク・整準・公平設定）が一致していない  
   可能性。 [oai_citation:4‡Agent Gate](https://agent-gate.s21g.com/moon/67279209d81d4e890c28cbd088d8cd58396dfbe1c729eea299acfa74b3661ffa/%40localhost%3A3131/state_of_the_art/index.html)
2. **サンプル規模の不足**：**学習→凍結→新ホールドアウト**の鎖がクラスタで 1 系統のみ。  
   SOTA のクラスタ準備表では **A1689/CL0024=READY** だが、**新規 HO（例: 衝突  
   クラスタ）**が未着手。 [oai_citation:5‡Agent Gate](https://agent-gate.s21g.com/moon/67279209d81d4e890c28cbd088d8cd58396dfbe1c729eea299acfa74b3661ffa/%40localhost%3A3131/state_of_the_art/index.html)
3. **宇宙論の広帯域尤度が未統合**：BAO は実値で提示済みだが、**RSD(fσ₈)、弱レンズ 2PCF、  
   CMB TT/TE/EE（ピーク高さ/比）**が未接続。 [oai_citation:6‡Agent Gate](https://agent-gate.s21g.com/moon/67279209d81d4e890c28cbd088d8cd58396dfbe1c729eea299acfa74b3661ffa/%40localhost%3A3131/state_of_the_art/index.html)
4. **公開 1-Click 再現パス**：主要図表（3198/2403/バレット/BAO）の **Docker/conda＋seed固定 CI** が未完成。
5. **KPI/脚注の完全同期**：全ページで **(N, N_eff, k, χ², rχ²)** と **fair.json sha / shared_params sha / コマンド**の **表示・値**を統一。

---

## 3) 研究指示（P0: 今スプリントで完遂／P1: 次スプリント）

### P0-1) バレット：S_shadow を「余裕有意」かつ数値同期
- **設計固定**  
  - **輪帯 2 帯域**（実空間 **4–8 pix / 8–16 pix**）で \(R, \Sigma_e\) 共通バンドパス → 帯域別  
    **band-S_shadow** を算出・\(|∇\Sigma_e|\) 分位で重み合成。  
  - **界面マスク**：\(|∇\omega_p|\) 分位 \(q_{\rm edge}\in\{0.70,0.75,0.80\}\)＋露光/SN 閾、形態整形  
    （closing→opening）。  
  - **Permutation**：**n≥10,000**（空間ブロック対応、rng固定）、**Q2=⟨cos2θ⟩**を補助指標で併記。
- **公平条件の完全適用**  
  - **SOTAトップ記載の fair.json（sha=b0a8ad97）** と **shared_params（sha=aa694c7f）** を  
    **ホールドアウト生成にも強制適用**。差分があれば **詳細頁を再生成**してトップと**数値同期**。  
    [oai_citation:7‡Agent Gate](https://agent-gate.s21g.com/moon/67279209d81d4e890c28cbd088d8cd58396dfbe1c729eea299acfa74b3661ffa/%40localhost%3A3131/state_of_the_art/index.html)
- **合否（DoD）**  
  - **global 合成帯域で S_shadow>0, p_perm<0.01**。  
  - トップと詳細頁で **S_shadow / p_perm / (N, N_eff, k, χ²)** が一致。

### P0-2) AICc 判定と KPI の単一 JSON 化／恒常掲示
- `config/fair.json` に **WLS σ, N_eff, PSF/HP, マスク/ROI, 整準(Δx,Δy), wrap, rng** を一元化。  
- すべての AICc 表に **(N, N_eff, k, χ², rχ²)** を本文条件と **完全一致**で差し込み（sha と  
  実行コマンドを脚注常設）。 [oai_citation:8‡Agent Gate](https://agent-gate.s21g.com/moon/67279209d81d4e890c28cbd088d8cd58396dfbe1c729eea299acfa74b3661ffa/%40localhost%3A3131/state_of_the_art/index.html)

### P0-3) BAO：CLASS 実計算＋距離点尤度の常設
- Fig-EU1c を **CLASS 出力固定**（既に z≈0.57 の **Amp≈0.994 / Δk≈0** 表示を維持）。  
- `bao_points.yml` を読み込み **χ²/AICc** を図と同頁に恒常掲示（**classy 版／ini／sha**の脚注込み）。  
  目標は **ΛCDM 同等（ΔAICc≈0）**。 [oai_citation:9‡Agent Gate](https://agent-gate.s21g.com/moon/67279209d81d4e890c28cbd088d8cd58396dfbe1c729eea299acfa74b3661ffa/%40localhost%3A3131/state_of_the_art/index.html)

### P0-4) Solar 上限の本線統合（常時ペナルティ）
- 1 AU の追加加速度上限を **全フィットに常時適用**し、SOTA 本線に **式・数値・感度図**を固定表示  
  （現状 **status=pass** を維持）。 [oai_citation:10‡Agent Gate](https://agent-gate.s21g.com/moon/67279209d81d4e890c28cbd088d8cd58396dfbe1c729eea299acfa74b3661ffa/%40localhost%3A3131/state_of_the_art/index.html)

### P0-5) 1-Click 再現（公開 CI）
- `docker/` と `environment.yml` を整備し、`make repro` で **3198/2403/バレット/BAO** を再生成。  
- CI で **数値一致（許容差内）**と **リンク監査(used_ids/notifications→200)** を検証し、**緑安定**に。

### P1-1) サンプル拡張（学習→凍結→新ホールドアウト）
- **学習**：**Abell 1689 / CL0024（READY）** を用いて α/β/… を学習→**凍結**。  
  [oai_citation:11‡Agent Gate](https://agent-gate.s21g.com/moon/67279209d81d4e890c28cbd088d8cd58396dfbe1c729eea299acfa74b3661ffa/%40localhost%3A3131/state_of_the_art/index.html)  
- **予測**：新規 **衝突クラスタ×1** をホールドアウトに設定し、**ΔAICc(FDB−shift)≤−10** と  
  **S_shadow p<0.01** を再現。  
- **銀河**：ベンチのテンプレを流用し **新規 1 銀河**を追加、**A/B 公平**で **ΔAICc(FDB−shift) ≤ −10** を確認。

### P1-2) 宇宙論の軽量尤度拡張
- **RSD (fσ₈)**、**弱レンズ 2PCF**、**CMB TT/TE/EE（ピーク高さ/比）**の **ライトウェイト尤度**を段階導入し、  
  「壊さない」範囲を定量提示。

### P1-3) FDB 固有予測の多数天体統計（識別性）
- **幾何“陰影”**（棒/ディスク/殻の界面法線に沿う R の方向）、**外縁 1/r² 復帰半径–|∇ω_p| 分位の相関**、  
  **遮蔽非対称の左右差**の 3 指標のうち **2/3 で p<0.01** を目標。

---

## 4) 実行チェックリスト（DoD）
- [ ] **バレット**：band-S_shadow（2帯域）＋界面マスク＋Permutation n≥10,000（ブロック対応）→ **S_shadow>0, p_perm<0.01**。トップと詳細頁の**数値完全同期**。 [oai_citation:12‡Agent Gate](https://agent-gate.s21g.com/moon/67279209d81d4e890c28cbd088d8cd58396dfbe1c729eea299acfa74b3661ffa/%40localhost%3A3131/state_of_the_art/index.html)
- [ ] **AICc 公平**：`fair.json` 一元化、各表へ **(N, N_eff, k, χ², rχ²)** と **sha/コマンド**を恒常掲示。 [oai_citation:13‡Agent Gate](https://agent-gate.s21g.com/moon/67279209d81d4e890c28cbd088d8cd58396dfbe1c729eea299acfa74b3661ffa/%40localhost%3A3131/state_of_the_art/index.html)
- [ ] **BAO**：CLASS 実計算の図＋**χ²/AICc** を常設（version/ini/sha 付き）。 [oai_citation:14‡Agent Gate](https://agent-gate.s21g.com/moon/67279209d81d4e890c28cbd088d8cd58396dfbe1c729eea299acfa74b3661ffa/%40localhost%3A3131/state_of_the_art/index.html)
- [ ] **Solar**：常時ペナルティ適用・図表本線設置（**status=pass** 維持）。 [oai_citation:15‡Agent Gate](https://agent-gate.s21g.com/moon/67279209d81d4e890c28cbd088d8cd58396dfbe1c729eea299acfa74b3661ffa/%40localhost%3A3131/state_of_the_art/index.html)
- [ ] **CI 再現**：Docker/conda＋seed固定で 3198/2403/バレット/BAO を 1-Click 再現（CI 緑）。
- [ ] **サンプル拡張**：A1689/CL0024 学習→凍結→新 HO（衝突クラスタ×1）で **ΔAICc≤−10**, **p<0.01** 達成。 [oai_citation:16‡Agent Gate](https://agent-gate.s21g.com/moon/67279209d81d4e890c28cbd088d8cd58396dfbe1c729eea299acfa74b3661ffa/%40localhost%3A3131/state_of_the_art/index.html)
- [ ] **固有予測**：幾何／外縁／非対称の 2/3 指標で **p<0.01**。

---

## 5) リスクと対策
- **数値同期の揺れ**：トップと詳細の KPI 差異は **一次情報＝詳細頁**に統一し、自動同期スクリプトで上書き。 [oai_citation:17‡Agent Gate](https://agent-gate.s21g.com/moon/67279209d81d4e890c28cbd088d8cd58396dfbe1c729eea299acfa74b3661ffa/%40localhost%3A3131/state_of_the_art/index.html)
- **設計ドリフト**：**fair.json** と **shared_params.json** の **sha ピン止め**を脚注に常設。
- **外部データ遅延**：新 HO は **READY** のクラスタから選び、欠品の少ない対象を優先。 [oai_citation:18‡Agent Gate](https://agent-gate.s21g.com/moon/67279209d81d4e890c28cbd088d8cd58396dfbe1c729eea299acfa74b3661ffa/%40localhost%3A3131/state_of_the_art/index.html)

