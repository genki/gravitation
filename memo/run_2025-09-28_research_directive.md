# 研究指示（単一MD）— 方向統計の立て直しと“壊さない”の可視化強化（2025‑09‑28 JST）

## 0. 目的（Definition of Done）
1. **汎化の確証**：以下の同時達成を **FULL** 設定で掲示  
   - **Abell S1063 または MACS J0416** の少なくとも一件で  
     **(i)** ΔAICc(FDB−rot) ≤ −10 **かつ** ΔAICc(FDB−shift) ≤ −10、  
     **(ii)** **S_shadow > 0 かつ p_perm < 0.01**（one‑sided, 空間ブロック, rng固定）。  
2. **宇宙論“壊さない”の可視化**：WL 2PCF（KiDS‑450 tomo1‑1）／CMBピーク（Boomerang‑2001）の図表を **ΔAICc≈0** と共に掲示（写像導入＋同一共分散）。  
3. **代表比較の完全整合**：代表6と“公平スイープ”の **k/誤差床/PSF/帯域/rng** を完全一致させ、脚注に **rng/sha/cmd/fair.json_sha** を固定表示。

---

## 1. 計算戦略（共通）：**FAST→FULL** の二段運用（計算量最適化）
- **FAST（探索）**  
  `--downsample 2 --float32`、**PSF σ={1.0,1.5}**、**高通過=8–16 px**、**‖∇ω_p‖分位={70,80,85}%**、**ROI=outer (r≥r75)** 優先。  
  **Permutation**：`n_perm=1200`＋**早期停止**（`p̂<0.02→FULL`／`p̂>0.20→他設定へ`／その他は最大2000）。  
  **重み試行**：`w(Σ_e)∈{Σ_e^0, Σ_e^0.3}`（shuffle優位の抑制）。  
  **キャッシュ**：∇ω_p・PSF畳込・WCSタイルを sha 鍵でディスク保存。
- **FULL（確証・公開）**  
  元解像度 `--float64`、**PSF σ={1.0,1.5,2.0}**、**帯域={4–8, 8–16}**、**ROI=global+outer**、`n_perm≥1e4`、rng固定。  
  **一次JSON→HTML** を自動上書きし、脚注に **(N,N_eff,k,χ²,rχ²,ΔAICc,S_shadow,p_perm,q_FDR,rng,sha,cmd)** を常設。

---

## 2. MACS J0416 — p_perm を 0.01 未満へ（現状: S_shadow=0.212, p=0.233）
**症状**：ΔAICc は達成済み、方向の有意化が未達。  
**仮説**：ROI/前処理の微差（PSF/誤差床/Σ_e 変換）が S_shadow を鈍化。

### 2.1 整合監査（順序厳守）
1) **WCS/回転・原点の一致** → 2) **PSF/ビームの対等化** → 3) **誤差床/外れ値clipの統一** → 4) **ROI/マスク（outer厚め）**。  
（ベースラインは SOTA の fair 設定に一致させる）

### 2.2 FAST 探索（対照も全く同一設定）
```bash
PYTHONPATH=. python scripts/cluster/run_holdout_pipeline.py \
  --target MACSJ0416 --fast --downsample 2 --float32 \
  --band 8-16 --mask-q 0.70 0.80 0.85 --psf-sigma 1.0 1.5 \
  --roi outer --perm-n 1200 --perm-earlystop --perm-max 2000 \
  --block-pix 6 --rng 42 --weight-exp 0.0 0.3
```
移行条件：outer で p̂<0.02 かつ ΔAICc(rot/shift)<0 → FULLへ。

### 2.3 FULL 確証
```bash
PYTHONPATH=. python scripts/cluster/run_holdout_pipeline.py \
  --target MACSJ0416 --full --bands 4-8 8-16 --psf-sigma 1.0 1.5 2.0 \
  --roi global outer --perm-n 10000 --rng 42
```
採択基準：S_shadow>0 & p_perm<0.01（outer主判定、global でも符号維持）。

---

## 3. Abell S1063 — 正側回復と p_perm の有意化（現状: S_shadow=−0.031, p=0.601）
**症状**：ΔAICc は達成だが、S_shadow が負側に後退。ページでは Σ_e変換=asinh が採用。  
**仮説**：Σ設計（界面放射）＋変換が方向核と噛み合わず、法線方向のコントラストが減衰。

### 3.1 Σ→遷移層 S(r) の再設計
- Hα/X線 → (n_e → ω_p → ω_cut) → 等値面上の外向きフラックス (J_out) を明示評価。  
- 薄層厚 (H_cut)・形状係数 (χ=ℓ^*/H_cut) をパラ化し、角度核 K(θ;χ) を **band‑S_shadow（4–8/8–16 px）**で最適化（過剰中心化は抑制）。  
- Σ_e変換のアブレーション：none / asinh / log1p を比較（まず none をベースに戻して符号回復を確認）。

### 3.2 FAST→FULL
```bash
# FAST
PYTHONPATH=. python scripts/cluster/run_holdout_pipeline.py \
  --target AbellS1063 --fast --downsample 2 --float32 \
  --band 8-16 --mask-q 0.70 0.80 0.85 --psf-sigma 1.0 1.5 \
  --roi outer --perm-n 1200 --perm-earlystop --perm-max 2000 \
  --block-pix 6 --rng 42 --sigma-e-transform none asinh

# FULL（候補のみ）
PYTHONPATH=. python scripts/cluster/run_holdout_pipeline.py \
  --target AbellS1063 --full --bands 4-8 8-16 --psf-sigma 1.0 1.5 2.0 \
  --roi global outer --perm-n 10000 --rng 42 --sigma-e-transform none
```
採択：outer で p_perm<0.01 を満たし ΔAICc(rot/shift)<0 を維持。

---

## 4. 代表比較（W·S vs Φ·η）— 条件の完全一致と脚注修正
- k=2（Υ★ と α(κ) の同時最小二乗）・誤差床・PSF/帯域・rng=42 を代表6／公平スイープ双方で完全一致。  
- 代表6ページ脚注の古い k=1 記述が残っていれば修正。  
- FULL 再計算後、各行末に “最良パラカード”（β, s[kpc], σ_k, rχ²）＋±σ帯/残差ミニ図を追記し、脚注に rng/sha/cmd/fair.json_sha を固定。

---

## 5. 宇宙論“壊さない”の可視化（軽→最終）
- 軽量カードは χ²(Late‑FDB)=χ²(ΛCDM) の ΔAICc≈0 を数値で確認済み。  
- 最終版では理論写像を導入し、同一共分散の下で ΔAICc≈0 を再掲。SOTA に図表＋脚注（出典・共分散・class_ini_sha）を追加。

---

## 6. 受入判定（DoD）
- Abell S1063 or MACS J0416：ΔAICc(rot/shift)≤−10 かつ S_shadow>0, p_perm<0.01（FULL）。  
- WL 2PCF/CMB：ΔAICc≈0 の最終図表を公開（写像・共分散・ハッシュ脚注）。  
- 代表比較の整合：代表6と公平スイープの条件一致・脚注固定（rng/sha/cmd/fair.json_sha）。  
- 一次JSON→HTML 自動上書き／脚注に N/N_eff/k/χ²/rχ²/ΔAICc/S_shadow/p_perm/q_FDR/rng/sha/cmd を恒常表示。

---

## 7. リスクとフォールバック
- FAST→FULL乖離：帯域を片側固定（4–8 or 8–16）し直交検証。核の近似次数差も監査。  
- shuffle優位：w(Σ_e)=Σ_e^0.3 で動的レンジを抑え、outer優先の ROI で角度整合を安定化。  
- 符号反転の再発：WCS/flip、法線向き（外向きを正）、mask被り、過強高通過を順に点検。
