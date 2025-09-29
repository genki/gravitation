# SOTA 更新レビュー（2025-09-03）— フィッティング改善指示

> 現状は **FDB＝見かけの引力**を、共有パラメータ **μ(k) = 1 + ε / [1 + (k/k₀)^m]** で同時評価する設計に整理され、DoG/幾何ブースト不使用・`j_EM→ρ_b` の整合も明記済みで良い流れです。共有値は **(ε,k₀,m,gas)=(1.0, 0.05 kpc⁻¹, 2, 1.33)** で SOTA に表示されています。 [oai_citation:0‡Agent Gate](https://agent-gate.s21g.com/moon/67279209d81d4e890c28cbd088d8cd58396dfbe1c729eea299acfa74b3661ffa/%40localhost%3A3131/state_of_the_art/index.html)  
> 以下、**公平性の担保**と**適合精度・堅牢性の向上**を中心に、具体的な改善指示を提示します。

---

## A. 公平比較と指標の統一（最優先）

1. **集計 AICc の「同一データ n」統一**
   - **問題**：SOTA の集計では **GR/GR+DM/MOND が n=1884** に対し **FDB が n=2284** となっており、**土台が異なる**比較です（AICc の公平性を損なう）。 [oai_citation:1‡Agent Gate](https://agent-gate.s21g.com/moon/67279209d81d4e890c28cbd088d8cd58396dfbe1c729eea299acfa74b3661ffa/%40localhost%3A3131/state_of_the_art/index.html)
   - **対応**：SOTA 集計器を「観測データ由来の共通マスク（g_obs/eV 有効点）」に統一。GR/MOND/FDB/GR+DM すべて同一 n の共通点で集計するよう変更。
   - **受入基準**：「ベースライン比較（AICc, 集計）」の表で **すべてのモデルが同一 n** になっていること。 [oai_citation:2‡Agent Gate](https://agent-gate.s21g.com/moon/67279209d81d4e890c28cbd088d8cd58396dfbe1c729eea299acfa74b3661ffa/%40localhost%3A3131/state_of_the_art/index.html)

2. **reduced χ² の定義を SOTA 側も統一**
   - **現状**：**CV レポートは `rχ²=χ²/(N−k)`** で計算・表示済み。一方 SOTA は脚注で **`rχ²=χ²/N`** を記載。**不一致**です。 [oai_citation:3‡Agent Gate](https://agent-gate.s21g.com/moon/67279209d81d4e890c28cbd088d8cd58396dfbe1c729eea299acfa74b3661ffa/%40localhost%3A3131/reports/cv_shared.html)
   - **対応**：CV は rχ²=χ²/(N−k) で集計済み。SOTA も per-galaxy=χ²/(N−k_local), fold/全体は k_global=4 を加味して rχ² を表示。脚注を太字で更新。
   - **受入基準**：SOTA の脚注に **`rχ²=χ²/(N−k)`** と **(n,k) の数え方**が記載され、Worst/Median の rχ² が整合的な値に収束。 [oai_citation:4‡Agent Gate](https://agent-gate.s21g.com/moon/67279209d81d4e890c28cbd088d8cd58396dfbe1c729eea299acfa74b3661ffa/%40localhost%3A3131/state_of_the_art/index.html)

3. **ブラックリストの適用範囲を明確化**
   - **現状**：SOTA は「ブラックリスト考慮版」ですが、汎用 CV ページ（`cv_shared.html`）の対象 ID には **CamB, DDO168** など **ブラックリスト ID** が含まれています（noBL 版の LSB/HSB CV は別途 OK）。 [oai_citation:5‡Agent Gate](https://agent-gate.s21g.com/moon/67279209d81d4e890c28cbd088d8cd58396dfbe1c729eea299acfa74b3661ffa/%40localhost%3A3131/reports/cv_shared.html)
   - **対応**：cv_shared.html に対象集合ラベル（全サンプル/BL除外）を表示。LSB/HSB の noBL は「BL除外」と明記。SOTA は noBL を要約に採用。
   - **受入基準**：各 CV ページのタイトルに **対象集合**が明記され、SOTA に反映する集合が一意に分かる。 [oai_citation:6‡Agent Gate](https://agent-gate.s21g.com/moon/67279209d81d4e890c28cbd088d8cd58396dfbe1c729eea299acfa74b3661ffa/%40localhost%3A3131/reports/cv_shared_summary_lsb_noBL.html)

---

## B. フィッティング精度・堅牢性の強化

### B-1. 誤差モデル・外れ値耐性
- **対応**（第1弾・簡便法）：
  - compare_fit_multi.py に `--robust {none|huber|student}` を追加（IRLS簡易近似）。外れに対する重み低下で堅牢化。
  - `--floor-jitter-kms` で点毎誤差に微少jitterを加算し、各銀河の rχ² を ≈1 に整列（過学習回避のため上限付き）。
  - `--rho-block` で半径方向の相関を近似（誤差の有効膨張）。

### B-2. バリオンの前向きモデル
- **対応**（スコープ内での簡便対応）:
  - `--psf-sigma-kpc` を追加し、ULW加速度の半径方向スムージングを提供（簡易PSF）。
  - i, D の不確かさ/非円運動は次期対応（方針は記載済み）。

### B-3. Υ★（M/L）推定の安定化
- **表記と推定の整合**：M/L 一覧は現在も **レンジ表記（0.8–1.5 等）や降順レンジ、0 を含む不自然レンジ**が混在。**点推定±68%CI** に統一し、**降順や 0** は修正。 [oai_citation:8‡Agent Gate](https://agent-gate.s21g.com/moon/67279209d81d4e890c28cbd088d8cd58396dfbe1c729eea299acfa74b3661ffa/%40localhost%3A3131/state_of_the_art/table.html)
- **階層ベイズ（shrinking）**：`Υ★,disk`/`Υ★,bulge` に **共通のロジ正規ハイパー prior** を置き、極端値を自動的に抑制（色–SPS 由来の弱事前があれば併用）。
- **座標降下の解析ステップ**：`μ(k)` 固定のもと **Υ★ は解析解（L2）**で一発更新→ `μ(k)` 更新（準ニュートン）→ 反復、で最適化の安定性と速度を両立。

### B-4. 共有 μ(k) の群別最適化（LSB/HSB）
- **観測**：noBL CV では **HSB: k₀=0.02**、**LSB: k₀=0.05** が最良。**群差**の可能性。 [oai_citation:9‡Agent Gate](https://agent-gate.s21g.com/moon/67279209d81d4e890c28cbd088d8cd58396dfbe1c729eea299acfa74b3661ffa/%40localhost%3A3131/reports/cv_shared_summary_hsb_noBL.html)  
- **指示**：共有を **「全体」と「群別（LSB/HSB）」の2案**で比較し、**AICc×CV** でどちらが汎化するか評価。群別にすると自由度が増えるため **AICc/BIC** で厳しく判定。

### B-5. 予測の正則化と同定性
- **同定性監視**：`μ(k)` の ε と Υ★ が縮退しやすい。**ヤコビアンの条件数**を定期出力し、**プロファイル尤度**で Υ★ を消去した場合の ε 推定を併記。  
- **単調性制約（オプション）**：`μ(k)` は **高 k で 1 に単調収束**する約束を **スプライン+単調制約**で実装可能（現状の式を使い続けつつ検証用として）。

---

## C. クロスバリデーション・ダイアグノスティクス

1. **ブロック k‑fold（半径帯）**  
   - 点の独立性が弱いため、**半径帯ごとにブロック**して fold を作成。**リーク**を抑え、汎化の信頼度を高める。

2. **勝率定義の明文化と整合性**  
   - SOTA の勝率は「GR に勝った割合（χ², ΔAICc）」を掲示。**ΔAICc の符号と“勝ち”の定義**（ΔAICc<0）を **テーブル見出しに明記**。 [oai_citation:10‡Agent Gate](https://agent-gate.s21g.com/moon/67279209d81d4e890c28cbd088d8cd58396dfbe1c729eea299acfa74b3661ffa/%40localhost%3A3131/state_of_the_art/index.html)

3. **指標の追加**  
   - **WAIC/PSIS‑LOO** を補助指標として併記し、AICc と整合するかを確認（外れ値耐性や overfit の検知に有効）。

---

## D. 計算・実装の改善

- **前計算の徹底**：Σ★, Σ_g の 2D FFT から **加速度カーネル K★(k), K_g(k)** を前計算。`μ(k)` 更新時は単なる **積・逆 FFT** で評価し、グリッド探索を高速化。  
- **自動同期**：SOTA 見出しの共有 μ(k)、表の (n,k)、勝率等は **単一 JSON（CV の採択結果）**から**自動反映**。手入力や別計算を排除（現状、SOTA と CV で rχ² 定義が食い違い）。 [oai_citation:11‡Agent Gate](https://agent-gate.s21g.com/moon/67279209d81d4e890c28cbd088d8cd58396dfbe1c729eea299acfa74b3661ffa/%40localhost%3A3131/reports/cv_shared.html)

---

## E. 表示と再現性（短期で直せるもの）

- **M/L 表**を **点推定±68%CI** に刷新（レンジ表記・降順・0 を排除）。AICc の `(n,k)` を併記。 [oai_citation:12‡Agent Gate](https://agent-gate.s21g.com/moon/67279209d81d4e890c28cbd088d8cd58396dfbe1c729eea299acfa74b3661ffa/%40localhost%3A3131/state_of_the_art/table.html)  
- **代表比較図**に **GR+DM / MOND / FDB の 3 列パネル**を少なくとも 3 銀河分掲出（同一データ・同一誤差・同一ペナルティの注記）。 [oai_citation:13‡Agent Gate](https://agent-gate.s21g.com/moon/67279209d81d4e890c28cbd088d8cd58396dfbe1c729eea299acfa74b3661ffa/%40localhost%3A3131/state_of_the_art/index.html)  
- **使用 ID CSV** を CV ページからリンク（noBL/withBL の両方）し、**解析に用いた集合**をダウンロード可能にする（リンクは既設だが開通確認）。 [oai_citation:14‡Agent Gate](https://agent-gate.s21g.com/moon/67279209d81d4e890c28cbd088d8cd58396dfbe1c729eea299acfa74b3661ffa/%40localhost%3A3131/reports/cv_shared.html)

---

## 実装タスク（チェックリスト）

- [ ] **AICc の n 統一**：全モデルで共通 n に揃えて集計し直す（共通部分へダウンサンプリング）。 [oai_citation:15‡Agent Gate](https://agent-gate.s21g.com/moon/67279209d81d4e890c28cbd088d8cd58396dfbe1c729eea299acfa74b3661ffa/%40localhost%3A3131/state_of_the_art/index.html)  
- [ ] **SOTA の rχ² を `χ²/(N−k)` に変更**、脚注と (n,k) の表示を更新（CV と統一）。 [oai_citation:16‡Agent Gate](https://agent-gate.s21g.com/moon/67279209d81d4e890c28cbd088d8cd58396dfbe1c729eea299acfa74b3661ffa/%40localhost%3A3131/reports/cv_shared.html)  
- [ ] **誤差モデルの強化**：Student‑t/Huber のオプション追加、jitter で rχ²≈1 に調整。  
- [ ] **PSF 畳み込み・i/D 伝播** をモデル側に実装。  
- [ ] **階層ベイズ Υ★**（ハイパ prior）＋ **座標降下の解析ステップ**で安定化。  
- [ ] **群別 μ(k)（LSB/HSB）** 案の AICc×CV 比較（自由度ペナルティ込み）。 [oai_citation:17‡Agent Gate](https://agent-gate.s21g.com/moon/67279209d81d4e890c28cbd088d8cd58396dfbe1c729eea299acfa74b3661ffa/%40localhost%3A3131/reports/cv_shared_summary_hsb_noBL.html)  
- [ ] **ブロック k‑fold**（半径帯）へ切替、勝率の定義をテーブル見出しに明文化。 [oai_citation:18‡Agent Gate](https://agent-gate.s21g.com/moon/67279209d81d4e890c28cbd088d8cd58396dfbe1c729eea299acfa74b3661ffa/%40localhost%3A3131/state_of_the_art/index.html)  
- [ ] **M/L 表記の刷新**（点±68%CI に統一、レンジ/0 排除）。 [oai_citation:19‡Agent Gate](https://agent-gate.s21g.com/moon/67279209d81d4e890c28cbd088d8cd58396dfbe1c729eea299acfa74b3661ffa/%40localhost%3A3131/state_of_the_art/table.html)  
- [ ] **代表 3 列パネル**の掲出（GR+DM / MOND / FDB）。 [oai_citation:20‡Agent Gate](https://agent-gate.s21g.com/moon/67279209d81d4e890c28cbd088d8cd58396dfbe1c729eea299acfa74b3661ffa/%40localhost%3A3131/state_of_the_art/index.html)  
- [ ] **JSON 一元化で SOTA↔CV の数値自動同期**（共有 μ(k), (n,k), 勝率, rχ² 定義）。

---

## 参考（現状確認の根拠）

- 共有 μ(k): **(ε,k₀,m,gas)=(1.0, 0.05, 2, 1.33)**（SOTA 見出し）。 [oai_citation:21‡Agent Gate](https://agent-gate.s21g.com/moon/67279209d81d4e890c28cbd088d8cd58396dfbe1c729eea299acfa74b3661ffa/%40localhost%3A3131/state_of_the_art/index.html)  
- CV（5‑fold）：`rχ²=χ²/(N−k)`、最良 `(ε=1.0, k₀=0.05, m=2, gas=1.33)`。 [oai_citation:22‡Agent Gate](https://agent-gate.s21g.com/moon/67279209d81d4e890c28cbd088d8cd58396dfbe1c729eea299acfa74b3661ffa/%40localhost%3A3131/reports/cv_shared.html)  
- LSB noBL / HSB noBL の集計・最良 k₀（LSB:0.05, HSB:0.02）。 [oai_citation:23‡Agent Gate](https://agent-gate.s21g.com/moon/67279209d81d4e890c28cbd088d8cd58396dfbe1c729eea299acfa74b3661ffa/%40localhost%3A3131/reports/cv_shared_summary_lsb_noBL.html)  
- M/L 表のレンジ表記・体裁崩れ（例：0.8–1.5, 0.743–0.728, 0.8–0 等）。 [oai_citation:24‡Agent Gate](https://agent-gate.s21g.com/moon/67279209d81d4e890c28cbd088d8cd58396dfbe1c729eea299acfa74b3661ffa/%40localhost%3A3131/state_of_the_art/table.html)  
- 集計 AICc の n 不一致（GR/GR+DM/MOND=1884, FDB=2284）。 [oai_citation:25‡Agent Gate](https://agent-gate.s21g.com/moon/67279209d81d4e890c28cbd088d8cd58396dfbe1c729eea299acfa74b3661ffa/%40localhost%3A3131/state_of_the_art/index.html)  
- rχ² の定義が SOTA と CV で不一致（SOTA: χ²/N, CV: χ²/(N−k)）。 [oai_citation:26‡Agent Gate](https://agent-gate.s21g.com/moon/67279209d81d4e890c28cbd088d8cd58396dfbe1c729eea299acfa74b3661ffa/%40localhost%3A3131/state_of_the_art/index.html)
