# DoD（理論の証明完了）ギャップ解消計画
**版:** 2025-11-XX  
**目的:** (i) P2「方向性」Gateの安定有意化と FULL パス率の回復、(ii) N体形態KPIの自動生成・HTTP 200 公開で「渦の一次判定」に到達、(iii) WL“正式”の同化（|ΔAICc|≤10）

---

## 0) Definition of Done（受け入れ基準）
- **P2（S1063/J0416）**  
  1) ΔAICc(FDB−shift) ≤ −10 を維持  
  2) **S_shadow>0 & p_perm<0.05**（global/core/outer の 3 帯同時）  
  3) **Spearman(resid, Σ|r)<0**（global/core/outer 各 one-sided p<0.05）  
  *Permutation n≥5000、ブロックBootstrap 95%CI 併記*
- **N体（S0: 2D/PM-FFT）**  
  **m=2 持続 ≥0.5–1.0 Gyr**, **ピッチ角 15–25°**, **RC 逸脱 <10%（3–15 kpc）**, **|ΔE/E| ≤ 1e−4**  
  *`metrics.csv` を SOTA から **HTTP 200** で取得可能（CORS/MIME 設定済）*
- **WL（P3）**  
  “正式”で **公式 n(z)/m/IA/θ/共分散**に整合、**|ΔAICc(FDB−ΛCDM)| ≤ 10**, **rχ²≲O(1)**

---

## A. P2「方向性」— Gate 2.0 + 前処理完全共通化（最優先）
### A-1 前処理の完全共通化（再現ズレを 0.02 以内に）
- 整準: `WCS→FFT相互相関→サブピクセル(Lanczos3)` を **FDB/rot/shift/shuffle** で完全一致  
- フィルタ: `σ_psf∈{1.2,1.5,1.8}`, `σ_hp∈{6,8,10}` を **両マップ同一適用**  
- ROI/mask: 事前登録（固定）＋**STAMP（設定ハッシュ）**を図脚注に自動出力  
- **検証:** FAST 再走で `S_shadow/Spearman` 再現ズレ **SD ≤ 0.02**

### A-2 Gate 2.0（偽陰性を減らす昇格ロジック）
- **主判定:** `S_shadow_global>0` かつ `Spearman<0`（[global, core, outer] の **2/3** で one-sided p<0.1）  
- **補助（OR）:** (A) 境界帯の外側優勢（Fisher p<0.05）; (B) 配向序数 `S2>0` & Rayleigh/V-test p<0.1  
- **昇格:** 主 or 補助成立 **かつ** 学習 `p̂_pass≥0.35` を **FULL(n=5000)** へ  
- **逐次Permutation:** 400→2000→5000（CI上限 U≤0.05 でPASS / 下限 L≥0.35 で打切り）  
- **KPI:** 推薦上位70% の **FULL PASS≥40%**, **平均perm≤2300**

### A-3 形状知覚 × “膝”で信号濃縮
- `|∇Σ|` を骨格化 → **法線ストリップ**で局所 `S_t,S2_t` を算出 → **相関補正 Stouffer Z** で統合  
- **W_eff “膝”** の直交格子: `q_knee∈{0.6,0.7,0.8}`, `p∈{0.7,1.0,1.3}`, `ω0/(1−ω0)∈{1,2,3}`  
- **受け入れ:** 各クラスタで **Spearman<0（p<0.05）** を満たす FAST 設定 **≥3 件**

### A-4 Σ変換×g×PSF×高通過 — HALVING + Thompson 70/30
- 初期格子 `{se∈[id,asinh,log1p,rank]} × {g∈[0.29,0.38,0.44,0.50]} × {σ_psf∈[1.2,1.5,1.8]} × {σ_hp∈[6,8,10]}` を FAST  
- **Successive Halving** で **上位 16** を残し、**Thompson 70%（搾取） + ε-greedy 30%（探索）**で FULL を配分

---

## B. N体（銀河渦）— 形態KPIの自動生成・HTTP公開（S0）
### B-1 「必須 4 図」の常設
1) **m=2/3 パワー（R×t ヒートマップ）**  
2) **ピッチ角の時系列（中央値+IQR）**  
3) **パターン速度 Ωₚ(t)**（位相ドリフト法、半径平均）  
4) **回転曲線（FDB有無の重ね／相対逸脱％）**  
図脚注に `(N, Nx, Lbox, dt, α, β, a2, a4, kmin, kmax, |ΔE/E|, seed, STAMP)` を自動埋め込み

### B-2 `metrics.csv` スキーマ固定と配信修復
- カラム：`time_Myr,A2_global,A2_3_6kpc,A2_6_10kpc,pitch_med_deg,pitch_iqr_deg,Omega_p_kms_kpc,RC_maxdev_frac_3_15kpc,dE_over_E,Lz_drift_frac,Nx,Lbox_kpc,alpha,beta,a2_kpc2,a4_kpc4,kmin,kmax,seed,STAMP`  
- **配信:** SOTA から **HTTP 200**で取得可能に（静的パス配置＋CORS/MIME 修正）  
- **KPI:** ΔE/E **中央値 ≤1e−4**, `metrics.csv` **生成率 100%**

### B-3 S0 スイープと Gate（S0）
- **固定:** `Lbox=100 kpc, Nx=1024, N=2e6, Q=1.2, dt=0.5 Myr, t_end=2.0 Gyr`  
- **スイープ:** `α∈{0.0,0.2,0.35,0.5} × a4∈{0.0,0.2} × β∈{0.0,0.1,0.2}`（24 本）  
- **Gate（0–0.4 Gyr）:** `dA2/dt>0` を 3 連続窓 ∧ `pitch∈[10°,30°]` ∨ `|ΔE/E|<5e−5` → **FULL（2.0 Gyr）**

### B-4 S1（3D/TreePM）導線
- PM 側へ `Φ_k += α Ktilde(k) ρ_k` を追加（IR/UV カット共有）、ε=50–100 pc / 適応 dt  
- 薄盤 Σ から **−∇ψ(Σ)** を z にソフト化（保存則厳守）

---

## C. WL（P3）— “厳密”→“正式”の同化
- **ベース固定（厳密）**：θレンジ=線形域・共分散=公式・自由度=k=0/1。rχ² と ΔAICc をカード化  
- **正式移行**：photo-z PDF で **n(z)** 再構成、**m** 適用、**IA=NLA→TATT**；**θビン/共分散**は公式仕様に完全整合  
- **受け入れ:** **rχ²≲O(1)** かつ **|ΔAICc(FDB−ΛCDM)| ≤ 10**

---

## D. 公平比較・監査の恒常化
- 図/カード脚注へ **(N,k,AICc,rχ²,誤差床,rng,PSF/HP,ROI,STAMP)** を恒常表示  
- 週次で **Gate→FULL PASS率**, **平均 perm**, **N体 metrics 200 応答率**をダッシュボード監査  
- “A-3/A-4”バッチを CI の**必須ジョブ**に昇格（候補 FAST→自動 FULL）

---

## 実行順とKPI（週次）
1) **A-1/A-2**（前処理共通化＋Gate 2.0）→ **A-3/A-4**（骨格ストリップ＋“膝”＋HALVING）  
2) **B-1/B-2/B-3**（N体KPI生成・200公開）→ **B-4**（S1準備）  
3) **C**（WL“正式”の同化）  
**KPI:** Gate→FULL **PASS≥40%**, **平均 perm ≤2300** / N体 **m=2持続≥0.5–1.0 Gyr, ピッチ15–25°, RC逸脱<10%, ΔE/E≤1e−4, metrics 200** / WL“正式” **|ΔAICc|≤10, rχ²≲O(1)**
