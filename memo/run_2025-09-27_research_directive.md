# 研究指示（2025-09-27） — 汎化確証／“壊さない”可視化／代表比較の完全整合

## 結果サマリ
- Abell S1063/MACS J0416 のホールドアウトで p_perm を 0.01 未満へ下げるための整合監査→FAST→FULL確証の手順を定義。
- WL 2PCF（KiDS‑450 tomo1‑1）/CMBピーク（Boomerang‑2001）の軽量尤度を ΔAICc≈0 で図表化し、既掲載の BAO/RSD と整合する方針を明文化。
- 代表6（W·S vs Φ·η）と“公平スイープ”の生成条件・k・rng・核・誤差床を完全一致させ、脚注に rng/sha/cmd/fair.json_sha を恒常表示する再計算計画を確定。

## 生成物
- この指示書（単一Markdown）: `memo/run_2025-09-27_research_directive.md`
- 実行テンプレ（FAST/FULL）: 本文のコマンド例（codex向け）

## 次アクション
- A: MACS J0416 の p_perm を <0.01 へ（整合監査→FAST→FULL）。
- B: Abell S1063 の方向統計を閾値内へ（Σ→薄層S(r)再設計→FAST→FULL）。
- C: 代表6と公平スイープの完全整合（FAST→FULL再計算、脚注固定、KPI更新）。
- D: WL 2PCF/CMBピークの軽量尤度を ΔAICc≈0 で図表化し SOTA 掲示。

---

## 目的（Definition of Done）
1. 汎化の確証（クラスターHO）
   - 少なくとも Abell S1063 または MACS J0416 の一件で、FULLにて同時達成し SOTA 掲示:
     - (i) ΔAICc(FDB−rot) ≤ −10 かつ ΔAICc(FDB−shift) ≤ −10
     - (ii) S_shadow > 0 かつ p_perm < 0.01（one‑sided, 空間ブロック, rng固定）
   - 現状: AICc差は両団体で達成、p は Abell≈0.17 / MACS≈0.23（未達）。
2. “壊さない”の可視化（宇宙論の軽量尤度）
   - WL 2PCF（KiDS‑450 tomo1‑1）/CMBピーク（Boomerang‑2001）で ΔAICc≈0 を図表として掲載（既掲載の BAO/RSD と整合）。
3. 代表比較の完全整合（銀河A/B）
   - 代表6と“公平スイープ”の生成条件・k・rng・核・誤差床を完全一致。脚注に rng/sha/cmd/fair.json_sha を固定表示。
   - 現状: 代表6は Φ·η 1/6 勝、スイープ要約は NGC 3198 のみ整合。脚注の k 表記に更新漏れ。

---

## 優先タスクA：MACS J0416 の p_perm を 0.01 未満へ
- 背景: ΔAICc は達成（rot/shift とも負側）。S_shadow=0.422, p=0.23（未達）。
1. 整合監査（順序厳守）
   - WCS/座標原点/回転の一致 → PSF/ビーム対等化 → 誤差床・外れ値clipの統一 → ROI/マスク再定義（outer 厚め）。
2. FAST 探索（全方式で同一設定）
   - `--downsample 2 --float32 --band 8-16 --mask-q 0.70 0.80 0.85 --psf-sigma 1.0 1.5 --roi outer --perm-n 1200 --perm-earlystop --perm-max 2000 --block-pix 6 --rng 42`
   - Σ_e の動的レンジ圧縮を併走（w(Σ_e)=Σ_e^0, Σ_e^0.3）して shuffle 優位のリスクを抑制。
   - 早期停止: `p̂<0.02 → FULL`／`p̂>0.20 → 他設定へ切替`。
3. FULL 確証
   - `--bands 4-8 8-16 --psf-sigma 1.0 1.5 2.0 --roi global outer --perm-n 10000 --rng 42`
   - 採択基準: outer で S_shadow>0 & p_perm<0.01 を満たし、global でも符号一致。

---

## 優先タスクB：Abell S1063 の方向統計を閾値内へ
- 背景: AICc差は達成、S_shadow=0.635, p=0.17（未達）。Σ（界面放射）モデルの再設計が推奨。
1. Σ→遷移層 S(r) 再設計
   - Hα/X線 → n_e → ω_p → ω_cut → 等値面上の外向きフラックス \(J_{\rm out}\) を再評価。
   - 薄層厚 \(H_{\rm cut}\) と形状係数 \(\chi = \ell^*/H_{\rm cut}\) を明示して薄層 S(r) を生成。
   - 角度核 \(K(\theta;\chi)\) を band‑S_shadow（4–8/8–16 px）に整合（過剰中心化は抑制）。
2. FAST → FULL（設定はAと同一）
   - FAST で outer 優先に `p̂<0.02` を確保 → FULL で `n_perm≥1e4` に拡張し global/複数帯域で確証。
3. 負符号再発の切り分け
   - WCS 符号/flip、法線向き（外向きを正）、mask 被り、過強な高通過（過大 d）を順に点検。

---

## タスクC：代表比較（W·S vs Φ·η）の完全整合と脚注修正
1. 生成条件の完全一致
   - **k=2（Υ★ と α(κ) の同時最小二乗）**を代表6・公平スイープの双方で固定。脚注の “k=1: Υ★” は修正。
   - PSF（σ={1.0,1.5,2.0} in FULL / {1.0,1.5} in FAST）、高通過（4–8, 8–16 in FULL / 8–16 in FAST）、誤差床、rng を完全一致。
2. 再計算（FAST→FULL）
   - FAST: 代表6の両方式に同一設定で一括再生成。
   - FULL: 公開用。代表表の各行末に **“最良パラカード”（β, s[kpc], σ_k, rχ²）**と ±σ帯/残差の小型図を追加。
3. 脚注・再現性
   - 代表6ページに rng/sha/cmd/fair.json_sha/shared_params_sha を恒常表示。
   - SOTA本体の KPI‑4（代表表再計算済み）に、**整合済み（|Δ(ΔAICc)| ≤ 5）**の注記を追記。

---

## タスクD：“壊さない”の可視化（軽量尤度→最終図）
1. FAST: KiDS‑450 tomo1‑1（WL 2PCF）／Boomerang‑2001（CMBピーク）の観測ベクトル＋固定共分散で低次元近似 χ² を先行作成し ΔAICc≈0 を確認。
2. FULL: Late‑FDB と ΛCDM を並記した図表を作成し、データ出典・共分散ソース・class_ini_sha を脚注固定のうえ SOTA 掲示。

---

## 実行テンプレ（codex向け）
```bash
# MACS J0416 — FAST（outer 優先）
PYTHONPATH=. python scripts/cluster/run_holdout_pipeline.py \
  --target MACSJ0416 --fast --downsample 2 --float32 \
  --band 8-16 --mask-q 0.70 0.80 0.85 --psf-sigma 1.0 1.5 \
  --roi outer --perm-n 1200 --perm-earlystop --perm-max 2000 \
  --block-pix 6 --rng 42 --weight-exp 0.0 0.3

# MACS J0416 — FULL（確証）
PYTHONPATH=. python scripts/cluster/run_holdout_pipeline.py \
  --target MACSJ0416 --full --bands 4-8 8-16 --psf-sigma 1.0 1.5 2.0 \
  --roi global outer --perm-n 10000 --rng 42

# 代表6 — FULL（W·S と Φ·η を同条件で）
PYTHONPATH=. python scripts/ab_comp/run_rep6_ws.py \
  --full --float64 --psf-sigma 1.0 1.5 2.0 --hipass 4-8 8-16 \
  --errfloor 0.03,3,7 --k 2 --rng 42

PYTHONPATH=. python scripts/ab_comp/run_rep6_phieta.py \
  --full --float64 --psf-sigma 1.0 1.5 2.0 --hipass 4-8 8-16 \
  --errfloor 0.03,3,7 --k 2 --rng 42 \
  --beta 0.0 0.3 --s 0.4 0.6 1.0 --sigk 0.5 0.8 1.2
```

---

## リスク管理
- FAST/FULL 乖離: FASTで達成→FULLで不一致の場合、帯域（4–8/8–16）を片側固定で再検証。核の近似次数差も監査。
- shuffle 優位: Σ_e の動的レンジ圧縮（指数0.3）や outer 優先の ROI で再評価。
- 脚注の更新漏れ: 代表6の k 表記・rng・コマンドは必ず脚注固定。

---

## 受入チェック（DoD）
- Abell S1063 or MACS J0416 で ΔAICc(rot/shift)≤−10 かつ S_shadow>0, p_perm<0.01（FULL）。
- WL 2PCF/CMBピークで ΔAICc≈0 を図表で提示（出典・共分散・ハッシュ脚注）。
- 代表6 vs 公平スイープの完全整合（|Δ(ΔAICc)| ≤ 5）・脚注固定（rng/sha/cmd/fair.json_sha）。
- SOTA の KPI/課題欄に達成状況を反映（日時付き）。

---

## 参照箇所（現版SOTA）
- 更新時刻・KPI・不足データ・環境、追加HO（Abell S1063/MACS J0416）、代表6・公平スイープ、単一銀河ベンチ。

