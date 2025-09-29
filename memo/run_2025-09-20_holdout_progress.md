# 2025-09-20 ホールドアウト進捗・プログレス実装

## 結果サマリ
- `make_bullet_holdout.py` にプログレス表示とETA計算を追加し、進捗ログを `server/public/reports/cluster/<holdout>_progress.log` へ出力する仕組みを導入。
- MACSJ0416 のホールドアウト解析を完走（shadow permutation 3帯域×n=10,000, residual permutation n=5,000、全体所要 ≈27分）。
- AbellS1063 のホールドアウト解析を長時間ジョブ（n_perm=10,000×3）として実行。8hタイムアウトで中断したが、progressログによりETA確認が可能になった。
- バックグラウンド実行スクリプト `scripts/jobs/run_holdout_async.sh` を新設し、PID・標準ログ・progressログを自動記録する運用に切り替え。`tmp/jobs/holdout_*.json` でジョブ管理。
- AbellS1063 ホールドアウトを新スクリプト経由で再投入（PIDは progress log と meta に記録）。
- Chandra ACIS データ取得済みクラスタの `omega_cut/sigma_e/kappa_obs` を揃え、`run_holdout_pipeline.py --auto-train` で共有パラメタを再学習。

## 生成物
- `scripts/reports/make_bullet_holdout.py` 更新（プログレスクラス、ログ出力）。
- `scripts/fetch/fetch_cluster_cxo.py` 自動ダウンローダ。
- `data/cluster/MACSJ0416/` および `data/cluster/AbellS1063/` の `sigma_e.fits`, `omega_cut.fits`, `kappa_obs.fits`。
- `server/public/reports/cluster/MACSJ0416_progress.log`, `server/public/reports/cluster/AbellS1063_progress.log`。
- `server/public/reports/bullet_holdout.html`（MACSJ0416向け最新出力）。

## 次アクション
- AbellS1063 ホールドアウトの継続実行（再投入 or ステップ分割）と結果反映。
- 生成されたprogressログの監視基盤（通知/ダッシュボード反映）の検討。
- 共有パラメタ（`data/cluster/params_cluster.json`）のshaをSOTA脚注に同期。
- バックグラウンドジョブ監視スクリプト `scripts/jobs/status.py` をCI/監視に組み込み、完了後のメタ削除フローを定義。

## 2025-09-20 追加ログ
- `scripts/jobs/run_holdout_async.sh AbellS1063` で起動したジョブ (PID 328136) は
  `server/public/reports/cluster/AbellS1063_progress.log` へ進捗を継続吐き出し中。
  19:05 JST 時点で shadow permutation 1 周目が 9984/10000、次の帯域用ループが
  1/10000 まで進行しており、ETA ≈100 分/loop のペースを確認。
- `scripts/reports/make_bullet_holdout.py` に per-holdout コピー処理を追加。
  既存のバレット結果は `server/public/reports/cluster/Bullet_holdout.*` として退避。
- Frontier Fields Lenstool FITS を `scripts/fetch/fetch_frontier_lenstool.py`
  で取得し、tarball を `data/raw/frontier/{macs0416,abells1063}/...` に生成。
  `data/raw/lenstool/{macs0416,abells1063}.tar.gz` へシンボリックリンクを配置。
- `data/cluster/MACSJ0416` / `AbellS1063` の `omega_cut/sigma_e/kappa_obs` に
  `PIXKPC` が埋め込まれていることを確認（例: AbellS1063 σ_e/ω_cut は
  17.06 kpc/pix, κ_obs は 0.867 kpc/pix）。
- `scripts/repro.py` の期待値を最新バレットKPIに更新し、`check_bench` /
  `check_bullet_holdout` / `check_bao_and_solar` を単体実行して閾値一致を確認。
- GitHub Actions での再現ワークフロー案は利用予定がなくなったため撤回。
- `analysis/lightweight_likelihood.py` を新設し、RSD/弱レンズ/CMB ピーク用の
  雛形 (`analysis/rsd_likelihood.py`, `analysis/weak_lensing_likelihood.py`,
  `analysis/cmb_peak_likelihood.py`) を実装。将来の観測ベクトルを YAML で
  与えるだけで χ²/AICc を計算できる構成を整備した（現状は enabled=false の
  プレースホルダデータを配置）。
- RSD 向けに growth solver から fσ₈(z) を生成する `predict_fsigma8` を追加。
  `analysis/rsd_likelihood.evaluate_rsd_from_growth` で Late‑FDB/ΛCDM の比較が
  可能になった。
- 複数天体の指標を一括処理する `scripts/galaxies/run_signatures_batch.py`
  を追加し、P1-C の多数天体統計に備えた。
- `scripts/eu/class_validate.py` を拡張し、RSD 尤度を自動呼び出し
  （データ未整備時はスキップ）できる導線を追加。弱レンズや CMB ピークの
  ラッパは将来データ投入後に接続予定。
- RSD 観測ファイル `data/rsd/rsd_points.yml` を BOSS DR12 の fσ₈ 値で更新し、
  `evaluate_rsd_from_growth` により Late‑FDB χ²≈3.79、ΛCDM χ²≈3.66 (ndof=3) を
  評価。結果を `server/public/state_of_the_art/data/rsd_likelihood.json` に出力。
- `config/fdb_signatures_bullet.yml` を用いて Bullet クラスタの指標を
  バッチ計算し、`server/public/reports/cluster/Bullet_signatures*.json` を生成
  (S≈3.7×10⁻³, Q₂≈3.0×10⁻³, p_V≈7.7×10⁻⁴)。
- AbellS1063 ホールドアウトをバックグラウンド完走（残差Permutation 5,000×3）。
  出力を `server/public/reports/cluster/AbellS1063_holdout.{html,json}` として退避。
- KiDS-450 cosmic shear 2PCF (tomographic bin 1-1) のデータベクトルと
  18×18 共分散サブ行列を `data/weak_lensing/kids450_xi_tomo11.yml` に整備。
- BOOMERANG/Maxima の CMB ピーク位置・高さを `data/cmb/peak_ratios.yml` に整理
  （ピーク毎に ℓ と μK² のセット + 6×6 共分散）。
