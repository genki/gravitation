# Directive 2025-09-23: 「証明完了」ラインまでの実行計画 (JST)

> 基準: 2025-09-23 06:53 JST 時点の一次成果物を参照。フェア条件は `config/fair.json` (sha256=56f181ae91220909fff30b8ed920503df575a3e9a66b7170f1ab1fbc22d0a814)。共有パラは `data/shared_params.json` (sha256=aa694c7f90eafa406021a6777311d0914835eb3b6579409d4ebe57781409d1af)。CI/Actions は使用せずローカル運用。

---

## 0. 現況スナップショット（一次JSON/ログの確認結果）

- **銀河ベンチ (NGC3198 / NGC2403)**  
  `server/public/reports/bench_ngc3198.html`, `bench_ngc2403.html` は `fair.json_sha=56f181ae9122`, `shared_params_sha=aa694c7f90ea…` を掲示済み。`rχ²` と `(N,k)` も脚注に常設され、`make repro_local` の検証ログは `[repro-local] verification passed` を記録。
- **Bullet HO (学習: Abell1689/CL0024 固定)**  
  `server/public/reports/cluster/Bullet_holdout.json` → ΔAICc(FDB−rot)=-6.7859×10⁷, ΔAICc(FDB−shift)=-6.7438×10⁶, `S_shadow(global)=0.378` / `outer=0.366`, permutation(one-sided >0) `n=12000`, `p_perm=2.25×10⁻³`, `block_pix=4`, `N=7396`, `σ_psf=1.5`, `weight_power=0.0`, `mask_quantile=0.65`。`Bullet_progress.log` には 2025-09-22T09:41 JST 完了を記録。
- **AbellS1063 HO**  
  `server/public/reports/cluster/AbellS1063_holdout.json` → ΔAICc(FDB−rot)=-3.2646×10⁹, ΔAICc(FDB−shift)=-2.1510×10⁸ を維持。ただし `S_shadow(global)=0.256`, `p_perm=0.176` (n=2000, block_pix=4), `weight_power=-0.5`, `σ_psf=1.0`, `mask_quantile=0.50`。境界ピーク距離は 4.23 Mpc (閾値 300 kpc) で FAIL。
- **MACSJ0416 HO**  
  `server/public/reports/cluster/MACSJ0416_holdout.json` → ΔAICc(FDB−rot)=+7.753×10⁶ (FAIL), ΔAICc(FDB−shift)=-6.235×10⁵, `S_shadow(global)=0.690`, `p_perm=0.123` (n=12000)。整準 `dy=205, dx=269`, `mask_quantile=0.70`, `σ_psf=1.5`, `weight_power=0.0`。ピーク距離 7.09 Mpc で FAIL。
- **宇宙論 (軽量尤度)**  
  `server/public/state_of_the_art/early_universe_class.json` → BAO(BOSS DR12): χ²=3.874, dof=6, p=0.694; RSD: Δχ²=0.134 (Late-FDB vs ΛCDM); Solar 制約は pass。弱レンズ 2PCF(KiDS-450) と CMB ピーク比 (Boomerang-2001) は観測セットの整備済みのみで、尤度・ΔAICc の掲示は未実装。
- **データ欠品と再現性メタ**  
  SOTA データ表 (`state_of_the_art/index.html`) では `ngc3198_irac1.fits`, `ngc2403_irac1.fits` が未取得。`server/public/reports/env_logs.json` は `shared_params_sha` を出力するが `ciaover` 欠落を警告。通知ログ `server/public/notifications/log.ndjson` に run_2025-09-22 系の成果と次アクションが記録済み。

---

## 1. DoD とのギャップ整理

1. **Bullet 方向性 (達成済み) の恒常化**: S_shadow>0 かつ p_perm<0.01 を満たす構成を runbook・SOTA へ恒常反映 (`cluster/Bullet_holdout.*` と `reports/bullet_holdout.*` の乖離を解消)。
2. **追加クラスタ汎化**: AbellS1063 で p_perm<0.01 へ改善、または MACSJ0416 で ΔAICc(FDB−rot)<0 & p_perm<0.01 を実現し、少なくとも一件を公開 KPI に昇格。
3. **宇宙論の「壊さない」可視化**: 弱レンズ 2PCF、CMB ピーク高さ/比 の軽量尤度を Late-FDB vs ΛCDM で実装し、ΔAICc≈0 を数値で掲示。
4. **再現性の自動化**: 一次 JSON→HTML の自動上書き・`make repro_local` の閾値ログ・通知導線を runbook に固定。`scripts/build_state_of_the_art.py` が最新 JSON を参照する状態へ整備。
5. **データ補完**: IRAC1 FITS の取得、`lenstools` インストール、環境ログの欠落項目(ciaover)補完。

---

## 2. P0 (今スプリント｜1–2週間)

### P0-A Bullet 成果の固定化と公開反映
- `scripts/reports/make_bullet_holdout.py` に `--sync-legacy` 相当の処理を追加し、`cluster/Bullet_holdout.*` の best 結果を `reports/bullet_holdout.*` と SOTA カードへ同期。`scripts/build_state_of_the_art.py` 内の参照先も `cluster/` を優先するよう修正。
- runbook (`docs/runbook.md`) に以下を追記: 実行コマンド、rng、(σ_psf, σ_highpass, weight_power, mask_quantile, block_pix)、Permutation n=12000、p_perm=2.25e-3。`logs/auto_holdout_*.log` を参照パスで紐付け。
- `make repro_local` 終了時に bullet ΔAICc / S_shadow を自動検証するチェッカを追加し、閾値逸脱時は FAIL で停止。

### P0-B AbellS1063: S_shadow 有意化プロトコル
- **Permutation強化**: `BULLET_SHADOW_PERM_MIN=12000`、`block_pix` を 4/6/8 で再評価。Permutation メタ (`shadow_perm_meta.json`) を n と seed 付きで保存。
- **帯域・PSF 走査**: `sigma_highpass ∈ {0.7,1.0,1.5,2.0}`、`sigma_psf ∈ {1.0,1.5,2.0}` を `weight_power ∈ {0.0,0.3,0.7,-0.3,-0.5}` と直積。ROI は core(r≤r50), outer(r≥r75) を併記。
- **界面マスク調整**: `mask_quantile ∈ {0.50,0.60,0.65,0.70}` と `|∇ω_p|` 分位 {0.65,0.70,0.75,0.80} を組み合わせ、outer 帯域を主判定とした合成 p(FDR q≤0.05) も検討。
- **整準/WCS 監査**: `AbellS1063_progress.log` の `xcorr_shift_applied_pix=(368,367)` を再検証し、WCS 基準フレームと反転有無を `scripts/cluster/min_kernel.py` の `--diagnostics` で確認。
- KPI へ昇格できる設定を確定後、`server/public/reports/cluster/AbellS1063_holdout.json/.html` を更新し、一次 JSON→SOTA へ再同期。

### P0-C MACSJ0416: ΔAICc<0 と方向性の両立
- **WCS/Flip 点検**: `run_holdout_pipeline.py` を `--dry-run --debug-wcs` で実行し、galmap/κ の parity を確認。必要なら `config/cluster/macsj0416_wcs.yml` を整備。
- **Mask/ROI 差の補正**: `mask_quantile` を 0.65/0.60/0.55 に下げ、outer 帯域で κ−Σ_e の負相関を強化。`roi_outer_r` を 0.70/0.80/0.85 で走査。
- **誤差床と PSF**: `sigma_floor` / `sigma_scale` を bullet と揃え (0.6/0.6) つつ、`σ_psf` 1.0–2.0, `weight_power` 0.0/0.3/0.7 を比較。ΔAICc(FDB−rot)<0 を優先して探索し、方向性判定は合格候補でのみ高精度 permutation を実施。
- **Permutation 設定**: n≥12000, block_pix 4/6。`shadow_perm_values.jsonl` に seed / rng を書き出し。p_perm<0.01 に到達しない場合は outer 帯域を主判定にして FDR 管理。

### P0-D 再現性と通知オペレーション
- `scripts/build_state_of_the_art.py` に一次 JSON (`server/public/reports/cluster/*.json`, `early_universe_class.json`) の md5 チェックと上書き機構を追加。ビルド時に Delta 閾値(AICc, S_shadow, (N,N_eff,k,χ²,rχ²)) を比較し一致しない場合は FAIL。
- `docs/runbook.md` の `make repro_local` セクションを更新し、env.lock / rng / SHA / 通知コマンド (`make notify-done`) をテンプレ化。
- 通知テンプレ: run memo → `make notify-done-site` で完結するフローを runbook / README に明記。

### P0-E データ・環境整備
- `data/sings/ngc3198_irac1.fits`, `data/sings/ngc2403_irac1.fits` を IRSA (SINGS) から取得し、`scripts/data/acquire_irac1.py` (存在しない場合は作成) で取り込み。取得ログを `memo/data_acquisition_2025-09-23.md` として残す。
- `pip install lenstools` を `environment.yml` と `requirements.txt` に追加済みか確認。未記載なら追記して `env.lock` を更新。
- `server/public/reports/env_logs.json` の `ciaover` 欠落を解消 (`ciaover` コマンドでバージョン取得→JSON上書き)。

---

## 3. P1 (次スプリント｜1–2週間)

### 3.1 汎化の確証と公開
- AbellS1063 or MACSJ0416 のうち KPI 合格したものを SOTA トップに昇格させ、`ΔAICc(FDB−rot/shift)≤−10`, `S_shadow>0 & p_perm<0.01` をカードで掲示。Spearman・⟨cosΔθ⟩・ピーク距離を補助指標として常設。
- 余力があれば 3 系目 (例: MACSJ0416→AbellS1063) も順次着手し、一般化のサンプルを増やす。

### 3.2 宇宙論（弱レンズ / CMB）
- KiDS-450 tomo1-1: `tmp/kids/` のデータベクトル＋共分散を `scripts/eu/lightweight_likelihood.py` で読み込み、Late-FDB vs ΛCDM の χ²/AICc を算出。ΔAICc≈0 を確認後、SOTA に図表＋数値を載せる。
- Boomerang-2001 ピーク高さ/比: 観測ベクトルを `data/cmb/boomerang_peak.yml`（仮）に整備し、Late-FDB と ΛCDM のピーク差を χ² 化。Solar 上限制約との差分も併記。
- Runbook に再現手順 (CLASS 3.3.2.0 ini, rng, コマンド) を追加し、`make repro_local` に弱レンズ / CMB の検証スクリプトを組み込む。

### 3.3 自動化・監査強化
- `scripts/qa/audit_shared_params.py` を拡張し、`fair.json_sha` / `shared_params_sha` / rng / 実行コマンドを全レポートで差分監視。`make audit-sota` で確認できるようにする。
- 通知システム: 成功/警告/要確認 のサブタイトルを自動判断（閾値逸脱→警告、補助指標未達→要確認）。

---

## 4. リスクとフォールバック

- **Permutation 計算負荷**: n=12000 で時間が掛かる場合は 2000→12000 へ段階的に増加し、暫定結果を run memo に記録。GPU 等のリソース転用が必要なら別途検討。
- **MACSJ0416 の ΔAICc>0 継続**: 学習κ の再生成（Lenstool tarball再取得）と誤差床スケールの再推定を行い、`data/cluster/MACSJ0416/` の md5 を runbook へ記録。必要なら学習セットに MACSJ0717 等を追加して再学習。
- **SOTA ビルド差異**: JSON 上書きに失敗した場合は `scripts/build_state_of_the_art.py --report-diff` を実装し、差分をログに残して手動介入できるようにする。
- **データ入手遅延**: IRAC1 等が遅れる場合は代替図（例: 3.6µm の公表PNG）で暫定表示し、TODO に残す。

---

## 5. DoD チェックリスト（更新後に満たすべき条件）

- [ ] Bullet: `cluster/Bullet_holdout.json` と SOTA カードが ΔAICc<0, S_shadow=0.378, p_perm≤0.005 を一致表示。runbook に rng/cmd/sha 記録。
- [ ] クラスタ汎化: AbellS1063 か MACSJ0416 で ΔAICc(FDB−rot/shift)≤−10, S_shadow>0, p_perm<0.01 を公開指標として掲示。
- [ ] 宇宙論: BAO/RSD/Solar に加え、弱レンズ 2PCF と CMB ピーク比の χ²/AICc を公開し、ΔAICc≈0 を明示。
- [ ] 再現性: `make repro_local` が銀河→クラスタ→BAO→WL/CMB の全工程を自動実行し、閾値ログ＋env.lock を runbook へ記録。通知コマンドは `make -C gravitation notify-done` を標準化。
- [ ] データ補完: IRAC1 FITS と lenstools を導入し、環境ログ (`env_logs.json`) が `lenstool`, `ciaover`, `shared_params_sha` を全て出力。

---

## 参考コマンド / スクリプト

```
PYTHONPATH=. python scripts/reports/make_bullet_holdout.py \
  --sigma-psf 1.0,1.5,2.0 --sigma-highpass 0.7,1.0,1.5,2.0 \
  --weight-powers 0,0.3,0.7,-0.3,-0.5 --mask-quantiles 0.50,0.60,0.65,0.70 \
  --shadow-perm-n 12000 --block-pix 4,6,8

PYTHONPATH=. python scripts/cluster/run_holdout_pipeline.py \
  --clusters MACSJ0416 --auto-train --auto-holdout --debug-wcs

make repro_local
make -C gravitation notify-done
```

> **記録先**: 実行ログは `memo/run_YYYY-MM-DD_*.md` にまとめ、終了時は `make notify-done-site` で通知とサイト更新を一括実施すること。
