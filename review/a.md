# SOTA 更新レビュー（2025-09-02）— 修正指示

> FDB＝見かけの引力。太陽系では GR と同型、公正比較を明記している点は **維持**で良いです。以降は差分と修正方針です。  [oai_citation:0‡Agent Gate](https://agent-gate.s21g.com/moon/67279209d81d4e890c28cbd088d8cd58396dfbe1c729eea299acfa74b3661ffa/%40localhost%3A3131/state_of_the_art/index.html)

---

## A. 重大な不整合・表示バグ（高優先度）

1. **共有パラメータ表示が旧式（λ, A の残存）**
   - **症状**：SOTA の「共有: λ=20.0 kpc, A=125.0, gas_scale=1.33」と旧表記が残っています。一方で本文は μ(k)=1+ε/[1+(k/k0)^m] を採用と記載。**表記と実装が不一致**です。  
     **指示**：SOTAの共有欄を **(ε, k0, m, gas_scale)** に置換し、値は最新のCV（下記B-1参照）で採れた **折衷の代表解**（例：モード/中央値）を表示。λ/A は全面撤去。  [oai_citation:1‡Agent Gate](https://agent-gate.s21g.com/moon/67279209d81d4e890c28cbd088d8cd58396dfbe1c729eea299acfa74b3661ffa/%40localhost%3A3131/state_of_the_art/index.html)

2. **LSB/HSB の CV 集計が**「**全数値一致**」**（フィルタ未適用疑い）**
   - **症状**：LSB(noBL) と HSB(noBL) の Test 合算 χ²・ΔAIC(AICc) が **完全一致**。**LSB と HSB が同一集合**を見ている可能性。  
     **指示**：両ページのクエリ/マスクを点検し、ページ下部に **対象銀河ID一覧**を掲示。ログにも ID を出力。数値が必ず異なることを確認。  [oai_citation:2‡Agent Gate](https://agent-gate.s21g.com/moon/67279209d81d4e890c28cbd088d8cd58396dfbe1c729eea299acfa74b3661ffa/%40localhost%3A3131/reports/cv_shared_summary_lsb_noBL.html)

3. **M/L 一覧ページの「共有 μ(k)」が異常値（ε=125.0）＋表記体裁崩れ**
   - **症状**：「共有 μ(k): ε=125.0, k0=0.05, m=2, gas_scale=1.33」となっており、CVの設定（ε∈{0.1,0.3,1.0} 等）と整合しません。ULW μ が **“0.8–1.5”のレンジ表示**など混在も残存。  
     **指示**：共有 μ(k) は **CV で採択された値**に同期（例：ε=1.0, k0=0.05, m=2）。各銀河の ULW μ は **点推定±68%CI** に統一（レンジ表記は廃止）。  [oai_citation:3‡Agent Gate](https://agent-gate.s21g.com/moon/67279209d81d4e890c28cbd088d8cd58396dfbe1c729eea299acfa74b3661ffa/%40localhost%3A3131/state_of_the_art/table.html)

4. **rχ² の外れ値が放置（Worst=213.33, Median=9.83）**
   - **症状**：reduced χ² の定義か誤差床の未設定が疑われます。  
     **指示**：銀河ごとに **error floor（例 3–7 km/s）** を導入し、rχ² 分布が ~1±σ に収束するよう再評価。SOTAに **rχ² の定義と誤差モデル**を脚注で明記。  [oai_citation:4‡Agent Gate](https://agent-gate.s21g.com/moon/67279209d81d4e890c28cbd088d8cd58396dfbe1c729eea299acfa74b3661ffa/%40localhost%3A3131/state_of_the_art/index.html)

---

## B. 体裁・比較の統一（中優先度）

1. **CV の基準様式で統一（AICc・(n,k) 併記）**
   - **現状**：μ(k) の CV ページは AICc と (n,k) を明示しており良い。一方 LSB/HSB はヘッダで **AIC Δ** を出しており表記が混在。  
     **指示**：全 CV レポートを **AICc** に統一し、**(n, k)** を各 fold で併記。集計行も AICc 表記に。  [oai_citation:5‡Agent Gate](https://agent-gate.s21g.com/moon/67279209d81d4e890c28cbd088d8cd58396dfbe1c729eea299acfa74b3661ffa/%40localhost%3A3131/reports/cv_shared.html)

2. **代表比較図のベースライン併置**
   - **現状**：SOTAの代表図は FDB 中心。本文では GR+DM/MOND との公正比較を謳っているため、図でも並べるべき。  
   - **指示**：代表銀河について **GR+DM（NFW+c–M 事前／またはコア等温）・MOND・FDB** の **3列並列**図を SOTA に追加。本文に **同一データ・同一誤差・同一ペナルティ**を明記。  [oai_citation:6‡Agent Gate](https://agent-gate.s21g.com/moon/67279209d81d4e890c28cbd088d8cd58396dfbe1c729eea299acfa74b3661ffa/%40localhost%3A3131/state_of_the_art/index.html)

3. **ブラックリスト運用の透明化**
   - **現状**：「ブラックリスト考慮版」の注記はあるが、**除外基準と除外ID**がまとまっていません（M/L表には `Blacklist` 列あり）。  
   - **指示**：SOTA末尾に **除外基準（箇条書き）** と **除外ID一覧（件数）** を掲載。CVページにもリンク。  [oai_citation:7‡Agent Gate](https://agent-gate.s21g.com/moon/67279209d81d4e890c28cbd088d8cd58396dfbe1c729eea299acfa74b3661ffa/%40localhost%3A3131/state_of_the_art/index.html)

4. **単位・記号の脚注**
   - **指示**：「記号の意味」に **k0[kpc⁻¹]、m（無次元）、gas_scale（比率）** を明記済みだが、**共有欄にも同表記**を重ねて誤解防止。  [oai_citation:8‡Agent Gate](https://agent-gate.s21g.com/moon/67279209d81d4e890c28cbd088d8cd58396dfbe1c729eea299acfa74b3661ffa/%40localhost%3A3131/state_of_the_art/index.html)

---

## C. 受け入れ基準（Done の判定）

- SOTA の共有欄が **(ε, k0, m, gas_scale)** に更新され、λ/A が出現しない。  [oai_citation:9‡Agent Gate](https://agent-gate.s21g.com/moon/67279209d81d4e890c28cbd088d8cd58396dfbe1c729eea299acfa74b3661ffa/%40localhost%3A3131/state_of_the_art/index.html)  
- LSB/HSB の CV 集計が **異なる数値**となり、各ページ末尾に **対象ID一覧**が表示される。  [oai_citation:10‡Agent Gate](https://agent-gate.s21g.com/moon/67279209d81d4e890c28cbd088d8cd58396dfbe1c729eea299acfa74b3661ffa/%40localhost%3A3131/reports/cv_shared_summary_lsb_noBL.html)  
- M/L 一覧の「共有 μ(k)」が **CV と同期した値**になり、ULW μ が **点推定±68%CI** で統一。  [oai_citation:11‡Agent Gate](https://agent-gate.s21g.com/moon/67279209d81d4e890c28cbd088d8cd58396dfbe1c729eea299acfa74b3661ffa/%40localhost%3A3131/state_of_the_art/table.html)  
- すべての CV ページの集計行が **AICc と (n,k)** を併記し、AIC 単独表記が残らない。  [oai_citation:12‡Agent Gate](https://agent-gate.s21g.com/moon/67279209d81d4e890c28cbd088d8cd58396dfbe1c729eea299acfa74b3661ffa/%40localhost%3A3131/reports/cv_shared.html)  
- rχ² の Worst/Median が常識的範囲（~数）に改善し、**誤差床**と**定義**が脚注に記載。  [oai_citation:13‡Agent Gate](https://agent-gate.s21g.com/moon/67279209d81d4e890c28cbd088d8cd58396dfbe1c729eea299acfa74b3661ffa/%40localhost%3A3131/state_of_the_art/index.html)  
- 代表比較図に **GR+DM／MOND／FDB** の 3列が追加される（少なくとも数例）。  [oai_citation:14‡Agent Gate](https://agent-gate.s21g.com/moon/67279209d81d4e890c28cbd088d8cd58396dfbe1c729eea299acfa74b3661ffa/%40localhost%3A3131/state_of_the_art/index.html)

---

## D. 実装タスク（チェックリスト）

- [x] SOTA共有欄：`λ,A → (ε, k0, m, gas_scale)` に置換。値は CV（μ(k)）の代表解に同期（cv_shared_summary.json のfold中央値を採用／無い場合は(λ,A)からフォールバック）。  [oai_citation:15‡Agent Gate](https://agent-gate.s21g.com/moon/67279209d81d4e890c28cbd088d8cd58396dfbe1c729eea299acfa74b3661ffa/%40localhost%3A3131/state_of_the_art/index.html)  
- [x] LSB/HSB のフィルタ修正＋ID一覧表示（数値一致の解消）。各ページ末尾にIDと件数を掲載し、idsログを併出力。  [oai_citation:16‡Agent Gate](https://agent-gate.s21g.com/moon/67279209d81d4e890c28cbd088d8cd58396dfbe1c729eea299acfa74b3661ffa/%40localhost%3A3131/reports/cv_shared_summary_lsb_noBL.html)  
- [x] M/L一覧：共有 μ(k) の値修正（ε の異常値解消）、ULW μ を **点±68%CI** 表示へ更新（CI未供給の銀河は点推定のみ、レンジ表記は禁止）。  [oai_citation:17‡Agent Gate](https://agent-gate.s21g.com/moon/67279209d81d4e890c28cbd088d8cd58396dfbe1c729eea299acfa74b3661ffa/%40localhost%3A3131/state_of_the_art/table.html)  
- [x] CV 表記統一：AICc＋(n,k)。LSB/HSB ページの AIC Δ 表記を置換。  [oai_citation:18‡Agent Gate](https://agent-gate.s21g.com/moon/67279209d81d4e890c28cbd088d8cd58396dfbe1c729eea299acfa74b3661ffa/%40localhost%3A3131/reports/cv_shared_summary_lsb_noBL.html)  
- [x] 誤差モデル導入：error floor（3–7 km/s）設定→再計算→rχ² 脚注。  [oai_citation:19‡Agent Gate](https://agent-gate.s21g.com/moon/67279209d81d4e890c28cbd088d8cd58396dfbe1c729eea299acfa74b3661ffa/%40localhost%3A3131/state_of_the_art/index.html)  
- [x] 代表比較図：GR+DM／MOND を SOTA本文に併置（同一条件で）。  [oai_citation:20‡Agent Gate](https://agent-gate.s21g.com/moon/67279209d81d4e890c28cbd088d8cd58396dfbe1c729eea299acfa74b3661ffa/%40localhost%3A3131/state_of_the_art/index.html)  
- [x] ブラックリスト：基準＆除外ID一覧の常設セクションを追加。  [oai_citation:21‡Agent Gate](https://agent-gate.s21g.com/moon/67279209d81d4e890c28cbd088d8cd58396dfbe1c729eea299acfa74b3661ffa/%40localhost%3A3131/state_of_the_art/index.html)

---

### 備考（良い点・継続）
- μ(k) への一本化、j_EM→ρ_b の整合、DoG 等の物理ブースト撤去は方向性良好。**このまま維持**してください。  [oai_citation:22‡Agent Gate](https://agent-gate.s21g.com/moon/67279209d81d4e890c28cbd088d8cd58396dfbe1c729eea299acfa74b3661ffa/%40localhost%3A3131/state_of_the_art/index.html)
