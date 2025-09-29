# Directive 2025-09-22: SOTA再評価(2025-09-22 JST)と証明完了ラインまでの研究指示

> 評価前提: Tokyo (UTC+9) 時刻 2025-09-22 08:40 更新の SOTA を一次情報として参照。フェア条件は `config/fair.json (sha=56f181ae)`。 [oai_citation:0‡Agent Gate](https://agent-gate.s21g.com/moon/67279209d81d4e890c28cbd088d8cd58396dfbe1c729eea299acfa74b3661ffa/%40localhost%3A3131/state_of_the_art/index.html)

---

## 0) 現況スナップショット(一次情報)

- **宇宙論(Late-FDB 本線: 壊さない)**  
  BAO(BOSS DR12, CLASS 3.3.2.0) は `chi^2=3.87 / dof=6, AICc=3.87, p=0.694`。代表点 z~0.57 で振幅比~0.994, Delta k~0。RSD は `chi^2(Late-FDB)=3.79 / dof=3` で LambdaCDM との差は Delta chi^2=0.13。Solar 上限制約は pass。弱レンズ 2PCF(KiDS-450 tomo1-1) と CMB ピーク(Boomerang-2001: ell=212,544,843) は観測セット整備済、モデル照合は次フェーズ。 [oai_citation:1‡Agent Gate]

- **単一銀河ベンチ(同一 n・同一誤差・同一ペナルティ)**  
  NGC 3198: FDB AICc=192.227 (GR=7051, MOND=21665, GR+DM=7055), rchi^2=4.697 (GR=167.834)。脚注 `fair.json_sha=56f181ae`。 [oai_citation:2‡Agent Gate]  
  NGC 2403: FDB AICc=497.673 (GR=81666, MOND=48305, GR+DM=81670), rchi^2=7.088 (GR=1134.225)。脚注 `fair.json_sha=4edd92f...` (SOTAトップの 56f... と不一致)。 [oai_citation:3‡Agent Gate]

- **クラスタ(バレット: 学習->固定->HO)**  
  DeltaAICc(FDB-rot)=-1.364e7, DeltaAICc(FDB-shift)=-6.19e5 と主判定はクリア。ただし方向性 S_shadow=0.055 (p_perm=0.378, n=12000, block_pix=4) で有意未達。全球 Spearman(kappa 残差, Sigma_e)=-0.484 (p=0)。脚注には `fair.json_sha=56f181ae`, 実行コマンド, rng, (N, N_eff, k, chi^2, rchi^2) を明記。 [oai_citation:4‡Agent Gate]

- **準備状況と進捗ライト**  
  Abell1689 / CL0024 / Bullet / MACSJ0416 / AbellS1063 = READY。進捗率 86%。 [oai_citation:5‡Agent Gate]

- **表記・参照 SHA の揺らぎ**  
  SOTA 本文は `shared_params.json sha=aa694c7f...` を記載する一方、KPI セクションでは `sha=e049e07...` と混在。 [oai_citation:6‡Agent Gate]  
  NGC 2403 ベンチの `fair.json_sha=4edd...` はトップの 56f... と不一致。 [oai_citation:7‡Agent Gate]

> **総評**: 単一銀河は FDB が GR/MOND/GR+DM を AICc・rchi^2 で圧倒。宇宙論は BAO/RSD/Solar を壊さず維持。バレット HO は AICc で大幅リードだが S_shadow の有意化が未達。SHA 表記の統一も残課題。

---

## 1) 証明完了までのギャップ(必要条件)

1. **方向性の統計的有意化(バレット HO)**: S_shadow>0 かつ p_perm<0.01 (one-sided, 空間ブロック, rng固定) を現行設定で達成。現状 p=0.378。 [oai_citation:8‡Agent Gate]
2. **汎化の実証(別クラスタ HO)**: MACSJ0416 または AbellS1063 で DeltaAICc(FDB-rot/shift)<0 と方向指標の有意を、学習->固定->HO の鎖で再現。 [oai_citation:9‡Agent Gate]
3. **広帯域宇宙論の明示**: 弱レンズ 2PCF と CMB ピーク高さ/比で chi^2/AICc を掲示し、DeltaAICc≈0 を確認(BAO/RSD/Solar と整合)。 [oai_citation:10‡Agent Gate]
4. **フェア条件・共有パラの SHA 統一**: SOTAトップ・各ベンチ・HO の `fair.json_sha` と `shared_params_sha` を単一値に固定表示(一次 JSON から自動上書き)。 [oai_citation:11‡Agent Gate]

---

## 2) P0(今スプリント: 1-2週間) — 方向性の有意化 / 表示一元化 / ローカル再現

### P0-A バレット HO: S_shadow 有意化プロトコル
- 高通過フィルタ sigma in {0.7, 1.0, 1.5, 2.0} pix を走査し、band-S_shadow(4-8 / 8-16 pix) を global/core/outer で評価(one-sided permutation, n>=1e4, block_pix=4, rng固定)。 [oai_citation:12‡Agent Gate]
- 界面マスク: |grad omega_p| 分位 {65,70,75,80}% の境界帯を再設計し、ROI(core r<=r50 / outer r>=r75) と組み合わせて cos Delta theta・偏相関を改善。 [oai_citation:13‡Agent Gate]
- 重み関数 w(Sigma_e): {Sigma_e^0, Sigma_e^0.3, Sigma_e^0.7} を比較し境界強調とノイズ増幅のバランスを取る。 [oai_citation:14‡Agent Gate]
- PSF と整準: PSF sigma in {1.0, 1.5, 2.0} pix を同時走査。整準は FFT cross-correlation -> Lanczos3 を維持。 [oai_citation:15‡Agent Gate]
- 採否基準(本文へ掲示): 1) S_shadow>0 かつ p_perm<0.01 (global または合成帯域)、2) DeltaAICc(FDB-rot)<=-10 かつ DeltaAICc(FDB-shift)<=-10 (N, N_eff, k, chi^2, rchi^2 を併記)、3) Spearman(kappa 残差, Sigma_e)<0 (top10% でも負・p<0.05)、4) 高通過ピーク距離<=300 kpc (現状 FAIL を明記)。 [oai_citation:16‡Agent Gate]

> 実行コマンド: `PYTHONPATH=. python scripts/reports/make_bullet_holdout.py` (SOTA脚注の再現コマンドを踏襲し rng/sha を固定)。結果は一次 JSON -> HTML へ自動反映。

### P0-B SHA 統一と KPI 自動同期
- `fair.json_sha` を全ページで 56f181ae に統一(NGC 2403 ベンチの 4edd... を更新)。 [oai_citation:17‡Agent Gate]
- `shared_params_sha` を単一値に統一。暫定正準を aa694c7f... とし、KPI セクションの e049e07... を揃える(または逆に正準を e049e07... に決めてベンチ/HO を再実行)。 [oai_citation:18‡Agent Gate]
- トップ KPI を一次 JSON から自動上書きし、DeltaAICc・S_shadow・(N,N_eff,k,chi^2,rchi^2) の一致ログを runbook に保存。 [oai_citation:19‡Agent Gate]

### P0-C ローカル「1-Click」再現(CI なし)
- `make repro_local` に NGC 3198 -> NGC 2403 -> Bullet HO -> BAO を束ね、終了時に既掲値との閾値照合(AICc 差<=1e-3, p 値2-3桁一致)。 [oai_citation:20‡Agent Gate]
- 環境固定: venv または micromamba で env.lock(.yml) を保持。runbook に日時・sha・rng・実行コマンド・env.lock を記載。

**P0 DoD**  
- バレット HO で S_shadow 有意(p<0.01) かつ DeltaAICc(FDB-rot/shift)<0 を固定設定で達成し、一次 JSON と HTML を同期。 [oai_citation:21‡Agent Gate]  
- `fair.json_sha` と `shared_params_sha` が全ページで単一値。トップ KPI が一次 JSON と一致(同期ログ有)。 [oai_citation:22‡Agent Gate]  
- `make repro_local` の閾値一致ログと env.lock を runbook に保存。

---

## 3) P1(次スプリント: 1-2週間) — 汎化実証と広帯域宇宙論

### P1-A 別クラスタ HO(衝突系 >=1)
- 対象: MACSJ0416 または AbellS1063(SOTA READY)。WCS 整合と PIXKPC ヘッダをまず監査。 [oai_citation:23‡Agent Gate]
- 手順: `python scripts/cluster/run_holdout_pipeline.py --auto-train --auto-holdout` で学習->固定->HO を実施し、脚注に sha/rng/コマンドを固定表示。 [oai_citation:24‡Agent Gate]
- 採否: DeltaAICc(FDB-rot/shift)<=-10、S_shadow>0 かつ p_perm<0.01(n>=1e4, 空間ブロック, rng固定)。補助として cos Delta theta や 勾配整合 grad R dot grad Sigma_e / ||...|| も掲示(FDR 管理)。

### P1-B 広帯域宇宙論(壊さないの強化)
- 弱レンズ 2PCF(KiDS-450 tomo1-1) と CMB ピーク(Boomerang-2001) の軽量尤度を追加し、Late-FDB と LambdaCDM の chi^2/AICc を並記。DeltaAICc≈0 を提示(BAO/RSD/Solar は現数値維持)。 [oai_citation:25‡Agent Gate]

---

## 4) リスク管理とフォールバック

- 方向性が上がらない場合: sigma・マスク(|grad omega_p|分位)・重み w を同時走査。global が難しい場合は outer 帯域の S_shadow を主判定にし、合成 p(FDR q<=0.05) で採否。 [oai_citation:26‡Agent Gate]
- 設計ドリフト防止: 各ページ脚注に `fair.json_sha / shared_params_sha / rng / 実行cmd` を恒常表示。トップは一次 JSON -> 自動上書きで手編集を排除。 [oai_citation:27‡Agent Gate]
- データ欠品: SOTA READY 行から順次投入。最小セット(kappa_obs.fits / sigma_e.fits / omega_cut.fits) を先行し、細部は後追い。 [oai_citation:28‡Agent Gate]

---

## 5) 証明完了判定基準(公開ページで満たす)

- 単一銀河: NGC 3198 / NGC 2403 で FDB が AICc・rchi^2 で優位(既達)。 [oai_citation:29‡Agent Gate]
- クラスタ(汎化): Bullet + 衝突系>=1 の HO で DeltaAICc<0 (rot/shift) かつ S_shadow 有意(p<0.01) を本文で掲示。 [oai_citation:30‡Agent Gate]
- 宇宙論: BAO/RSD/Solar に加え、弱レンズ 2PCF と CMB ピークでも DeltaAICc≈0 を提示。 [oai_citation:31‡Agent Gate]

> P0->P1 を完了すると、銀河(適合) + クラスタ(汎化・方向) + 宇宙論(広帯域で壊さない) の三本柱が統計面・運用面で揃い、証明完了ラインに到達する見込み。
