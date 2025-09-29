# Directive 2025-09-21: SOTA再評価（2025-09-21 JST）と証明完了ラインまでの研究指示

> **評価前提**：Tokyo (UTC+9) の更新時刻 *2025-09-21 20:49* 掲載の SOTA を一次情報として参照。SOTAトップには **Late-FDB 本線**・**共有ハイパー**・**BAO/RSD/Solar**・**フェア条件**・**READY 状況**・**不足データ**が明記されている。 [oai_citation:0‡Agent Gate](https://agent-gate.s21g.com/moon/67279209d81d4e890c28cbd088d8cd58396dfbe1c729eea299acfa74b3661ffa/%40localhost%3A3131/state_of_the_art/index.html)

---

## 現況スナップショット（一次情報の要点）

### 直近ステータス（2025-09-21 20:49 JST 時点）

- **銀河（証拠充足）** — NGC 3198 / NGC 2403 で FDB が GR・MOND・GR+DM を AICc / rχ² で圧倒。差分は `server/public/reports/bench_*.html` と `scripts/repro_local_checks.py` の検証閾値に一致（詳細: [NGC 3198ベンチ](https://agent-gate.s21g.com/moon/67279209d81d4e890c28cbd088d8cd58396dfbe1c729eea299acfa74b3661ffa/%40localhost%3A3131/reports/bench_ngc3198.html), [NGC 2403ベンチ](https://agent-gate.s21g.com/moon/67279209d81d4e890c28cbd088d8cd58396dfbe1c729eea299acfa74b3661ffa/%40localhost%3A3131/reports/bench_ngc2403.html)).
- **クラスタ（要ホールドアウト公開）** — `server/public/state_of_the_art/holdout_status.json` は Bullet / MACSJ0416 / AbellS1063 を READY と報告。ただし公開 SOTA ページでは Bullet のみ指標掲示。MACSJ0416 以降の ΔAICc / S_shadow 値は未掲示（詳細: [SOTAトップ](https://agent-gate.s21g.com/moon/67279209d81d4e890c28cbd088d8cd58396dfbe1c729eea299acfa74b3661ffa/%40localhost%3A3131/state_of_the_art/index.html)).
- **宇宙論（壊さない証明の一部完了）** — BAO / RSD / Solar penalty は CLASS 3.3.2.0 連携で ΔAICc≈0 を保持。弱レンズ 2PCF と CMB ピークは観測セット準備済みで、尤度掲載が未完（詳細: [SOTAトップ](https://agent-gate.s21g.com/moon/67279209d81d4e890c28cbd088d8cd58396dfbe1c729eea299acfa74b3661ffa/%40localhost%3A3131/state_of_the_art/index.html)).

### ギャップ→達成条件マトリクス

| ギャップ | 現状 | 必要アウトカム | 優先度 |
|---|---|---|---|
| クラスタ汎化 | Bullet 指標のみ公開 | Bullet + 衝突系 ≥1 の ΔAICc(FDB−rot/shift)≤−10、S_shadow>0・p_perm<0.01 を HTML/JSON に掲示 | **P0** |
| 広帯域宇宙論 | BAO/RSD/Solar のみ掲示 | KiDS-450 tomo1-1 / Boomerang-2001 の χ²・ΔAICc≈0 を Late-FDB vs ΛCDM で併記 | **P1** |
| フェア条件脚注 | SOTAトップ `fair.json_sha=56f181ae`、一部ベンチは旧 sha 表記 | 全ページ脚注を 56f181ae に統一。生成スクリプトとテンプレの sha 埋め込みを更新 | **P0** |
| ローカル再現フロー | `make repro_local` / `scripts/repro_local_checks.py` あり。runbook への手順集約が未整備 | runbook に 1-click 実行→閾値照合→通知までの手順と許容差を明記 | **P0** |

---

## 詳細スナップショット（一次情報の要点）

- **宇宙論の整合（Late-FDB）**  
  BAO（BOSS DR12）を **CLASS 3.3.2.0** 連携で評価：z≈0.57 の振幅比≈0.994、Δk≈0、尤度 **χ²=3.87 / dof=6（AICc=3.87, p=0.694）**。RSD は **Late-FDB χ²=3.79 / dof=3**（ΛCDMとの差 Δχ²=0.13）。Solar 追加加速度のペナルティは **pass**。フェア条件は `config/fair.json (sha=56f181ae)` と明記。 [oai_citation:1‡Agent Gate](https://agent-gate.s21g.com/moon/67279209d81d4e890c28cbd088d8cd58396dfbe1c729eea299acfa74b3661ffa/%40localhost%3A3131/state_of_the_art/index.html)

- **共有ハイパーと方針**  
  共有 μ(k) の採択値は **ε=1, k0=0.2 kpc⁻¹, m=2, gas_scale=1.33**。用語は **ULM-P/D**（旧 h/l）で統一し、宇宙では P が遠達・D は近傍で P に転化して総量を底上げする、という運用想定を掲示。 [oai_citation:2‡Agent Gate](https://agent-gate.s21g.com/moon/67279209d81d4e890c28cbd088d8cd58396dfbe1c729eea299acfa74b3661ffa/%40localhost%3A3131/state_of_the_art/index.html)

- **単一銀河ベンチ（フェア比較：同一n・同一誤差・同一ペナルティ）**  
  **NGC 3198**：AICc **FDB=192.227**（GR=7051, MOND=21665, GR+DM=7055）、rχ² **FDB=4.697**（GR=167.834）。 [oai_citation:3‡Agent Gate](https://agent-gate.s21g.com/moon/67279209d81d4e890c28cbd088d8cd58396dfbe1c729eea299acfa74b3661ffa/%40localhost%3A3131/reports/bench_ngc3198.html)  
  **NGC 2403**：AICc **FDB=497.673**（GR=81666, MOND=48305, GR+DM=81670）、rχ² **FDB=7.088**（GR=1134.225）。 [oai_citation:4‡Agent Gate](https://agent-gate.s21g.com/moon/67279209d81d4e890c28cbd088d8cd58396dfbe1c729eea299acfa74b3661ffa/%40localhost%3A3131/reports/bench_ngc2403.html)

- **クラスタ：ホールドアウト準備状況**  
  **Abell1689 / CL0024 / Bullet / MACSJ0416 / AbellS1063 = READY**。HO パイプラインのワンライナーが明示されている（`--auto-train --auto-holdout`）。 [oai_citation:5‡Agent Gate](https://agent-gate.s21g.com/moon/67279209d81d4e890c28cbd088d8cd58396dfbe1c729eea299acfa74b3661ffa/%40localhost%3A3131/state_of_the_art/index.html)

- **不足データ（抜粋）**  
  Bullet の「銀河/ICLピーク」は任意。Hα（IRSA/SINGS）や 21 cm（HALOGAS/Zenodo）の直リンクと取り込みコマンドが提供済み。 [oai_citation:6‡Agent Gate](https://agent-gate.s21g.com/moon/67279209d81d4e890c28cbd088d8cd58396dfbe1c729eea299acfa74b3661ffa/%40localhost%3A3131/state_of_the_art/index.html)

> **総評**：単一銀河では FDB が GR/MOND/GR+DM を AICc・rχ²で大差リード。BAO/RSD と Solar は「壊さない」ことを明示。クラスタ HO の**準備**は整備済みで、公開ページから HO 結果の数値掲示が未確認のため（リンク未発見）、**HO 実行とページ反映**が直近の優先タスク。 [oai_citation:7‡Agent Gate](https://agent-gate.s21g.com/moon/67279209d81d4e890c28cbd088d8cd58396dfbe1c729eea299acfa74b3661ffa/%40localhost%3A3131/state_of_the_art/index.html)

---

## 1) 「証明完了」に必要な残差（ギャップ）の明示

1. **クラスタ汎化の実証**：学習→固定→**新規ホールドアウト（衝突系）**で **ΔAICc(FDB−rot/shift)<0** を再現し、**方向性指標（S_shadow など）の有意化**を提示。SOTA上は HO 準備まで確認できるが、**結果ページの数値掲示が未確認**。 [oai_citation:8‡Agent Gate](https://agent-gate.s21g.com/moon/67279209d81d4e890c28cbd088d8cd58396dfbe1c729eea299acfa74b3661ffa/%40localhost%3A3131/state_of_the_art/index.html)
2. **宇宙論の広帯域「壊さない」提示**：BAO/RSDに加え、**弱レンズ 2PCF**・**CMB ピーク高さ/比**の軽量尤度で **ΔAICc≈0** を図表で併記（SOTAは観測セット整備済み・モデル照合は次段と記載）。 [oai_citation:9‡Agent Gate](https://agent-gate.s21g.com/moon/67279209d81d4e890c28cbd088d8cd58396dfbe1c729eea299acfa74b3661ffa/%40localhost%3A3131/state_of_the_art/index.html)
3. **フェア条件の脚注一元化**：SOTAトップの `fair.json` sha（56f181ae）と各ベンチ脚注の sha（例：4edd92f…）の表記差を吸収し、**現行 sha を全ページ脚注へ統一**。 [oai_citation:10‡Agent Gate](https://agent-gate.s21g.com/moon/67279209d81d4e890c28cbd088d8cd58396dfbe1c729eea299acfa74b3661ffa/%40localhost%3A3131/state_of_the_art/index.html)
4. **ローカル再現（CIなし）の恒常運用**：一次 JSON → SOTAトップ **自動上書き**・数値照合ログ・環境ロックを runbook に残し、常に“人手 Green”で再現可能にする（SOTAはリンク監査200確認と記載）。 [oai_citation:11‡Agent Gate](https://agent-gate.s21g.com/moon/67279209d81d4e890c28cbd088d8cd58396dfbe1c729eea299acfa74b3661ffa/%40localhost%3A3131/state_of_the_art/index.html)

---

## 2) P0（1–2週間）— **HO 実行・方向性の有意化・表示の一元化**

### P0-A｜クラスタ HO 実行と公開（Bullet → MACSJ0416/AbellS1063）
- **前提チェック**：`python scripts/cluster/run_holdout_pipeline.py` をオプション無しで実行し、`server/public/state_of_the_art/holdout_status.json` に missing が無いことを確認。Lenstool tarball と `data/cluster/<name>/{omega_cut,sigma_e,kappa_obs}.fits` の三点セットが揃っていなければ補完する。 [oai_citation:12‡Agent Gate]
- **本番コマンド**：
  ```sh
  PYTHONPATH=. python scripts/cluster/run_holdout_pipeline.py --auto-train
  PYTHONPATH=. python scripts/cluster/run_holdout_pipeline.py --auto-holdout
  ```
  1本目で Abell1689 / CL0024 の共有パラメタを再学習・固定し、2本目で Bullet → MACSJ0416 → AbellS1063 へ順に適用。ログは `logs/holdout/`、成果物は `server/public/reports/<cluster>_holdout_*.html/json` に生成。
- **公開と監査**：`python scripts/build_state_of_the_art.py` を再実行し、必要に応じて `mkdocs build`。SOTAトップと `table.html` に ΔAICc・S_shadow・(N,N_eff,k,χ²) が反映されているかを確認し、`memo/run_YYYY-MM-DD_*.md` へ結果と RNG/sha を記録。
- **採否基準**：
  1. ΔAICc(FDB−rot) ≤ −10、ΔAICc(FDB−shift) ≤ −10。
  2. S_shadow > 0 かつ p_perm < 0.01（one-sided／FDR q≤0.05）。
  3. Spearman(κ残差, Σ_e) < 0（p<0.05）。

### P0-B｜方向性のブースト（最小改修のみ）
- **帯域最適化**：高通過 σ ∈ {0.7, 1.0, 1.5, 2.0} pix を走査し、band-S_shadow（4–8 / 8–16 pix）を global/core/outer で評価。
- **界面マスク**：‖∇ω_p‖ 分位 {65, 70, 75, 80}% で ROI を再設計（core=r≤r50 / outer=r≥r75）。
- **重み w(Σ_e)**：{Σ_e^0, Σ_e^0.3, Σ_e^0.7} の走査で最良帯域を選択。

### P0-C｜フェア条件の脚注一元化と KPI 同期
- `python scripts/benchmarks/run_ngc3198_fullbench.py` と `python scripts/benchmarks/run_ngc2403_fullbench.py` を最新 `config/fair.json`（sha=56f181ae）で再実行し、HTML 内脚注を同期。
- `python scripts/reports/make_bullet_holdout.py --train Abell1689,CL0024 --holdout Bullet` など個別実行でクラスタ系の脚注を更新。テンプレを生成する `scripts/reports/_shared.py` 側の `fair_sha` 埋め込みも確認。
- `python scripts/build_state_of_the_art.py`（内部で `once_json→HTML` 更新）を通し、ΔAICc・S_shadow・(N,N_eff,k,χ²) が JSON / HTML間で一致するか `logs/build_state_of_the_art.log` に記録。必要に応じ `make repro_local` → `scripts/repro_local_checks.py` で KPI 整合を最終確認。

### P0-D｜ローカル 1-Click 再現（CI なし）
- `make repro_local`（`Makefile` 168 行付近）で NGC3198 → NGC2403 → Bullet HO → BAO を一括再計算し、終了時の `scripts/repro_local_checks.py` が AICc差≤1e-3・p値2–3桁一致を保証するか確認。
- 実行時の sha (`git rev-parse HEAD`)、`env.lock` ハッシュ、RNG シード、閾値チェック結果を `docs/runbook.md` または `memo/run_YYYY-MM-DD_repro_local.md` に追記し、人手で再現できるよう段階を明文化。
- 必要であれば `make repro_local LOG=1` などログ保存オプションを検討し、逸脱時は `logs/repro_local/*.log` を添付して通知に反映。

**P0 DoD**：Bullet などで採否基準を満たし、脚注統一＋KPI同期ログ＋runbook を整備。

---

## 3) P1（次の1–2週間）— **汎化＋広帯域宇宙論の定量**

### P1-A｜別クラスタ HO（衝突系×1 以上）
- 対象：MACSJ0416 or AbellS1063（SOTA READY）。WCS 整合と `PIXKPC` ヘッダを監査。
- 採否：ΔAICc(FDB−rot/shift) ≤ −10、S_shadow > 0 & p_perm < 0.01 を再現。

### P1-B｜弱レンズ 2PCF／CMB ピークの軽量尤度提示
- KiDS-450 tomo1-1 と Boomerang-2001 の χ²/AICc を算出し ΔAICc≈0 を提示。

---

## 4) データ補完と最小要件
- 銀河用 Hα・21cm データの再取得・取り込みコマンドは SOTA に記載。
- クラスタ HO 用は `kappa_obs.fits / sigma_e.fits / omega_cut.fits` が必須。

---

## 5) リスクとフォールバック
- 方向性が閾値に届かない場合は帯域×マスク×重みを同時探索し、outer 帯域の合成 p（FDR管理）も検討。
- 設計ドリフト防止：`fair.json_sha / shared_params_sha / rng / 実行cmd` を脚注に固定。
- 再現性：runbook に日時・環境・sha・rng・コマンド・照合結果を残し、“人手 Green” を維持。

---

### 証明完了条件のまとめ
- 単一銀河：3198/2403 で FDB が AICc・rχ² で優位（現状達成）。
- クラスタ：Bullet + 衝突系×1 以上の HO で ΔAICc<0 と S_shadow 有意を公開。
- 宇宙論：BAO/RSD/Solar に加え、弱レンズ 2PCF／CMB ピークでも ΔAICc≈0 を提示。

> P0→P1 を完了すれば、銀河（適合）＋クラスタ（汎化・方向）＋宇宙論（広帯域で壊さない）の三本柱が揃い、証明完了ラインに到達できる。
