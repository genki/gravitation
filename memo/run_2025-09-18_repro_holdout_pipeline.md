# 2025-09-18 再現パイプライン整備とホールドアウト拡張

## 結果サマリ
- Solar ペナルティを高波数抑制 (`k_sup`,`n_sup`) で実装し、Fig-EU1c の `solar_penalty.status` が `pass` となるよう Late‑FDB を調整。
- `scripts/repro.py` と `make repro` を追加し、ベンチ2件・バレットホールドアウト・CLASS/BAO・SOTA 再生成を一括実行後、主要値（AICc、S_shadow、BAO χ²、Solar）を検証する 1-click 再現フローを整備。Docker イメージ（`docker/Dockerfile`）と README を添付。
- `scripts/cluster/run_holdout_pipeline.py` と `config/cluster_holdouts.yml` を追加し、Abell1689/CL0024 の学習データ状態と新規ホールドアウト候補（MACSJ0416, AbellS1063）の欠品ファイルを自動棚卸 → `holdout_status.json`/SOTAカードで公開。
- `scripts/galaxies/compute_fdb_signatures.py` を作成し、残差×Σ_e 方向統計（S_shadow/Q2/Rayleigh/V-test）を任意銀河に対して計算できる CLI を提供。

## 生成物
- 更新: `cfg/early_fdb.json`, `src/cosmo/mu_late.py`, `src/cosmo/growth_solver.py`, `analysis/solar_penalty.py`, `scripts/eu/class_validate.py`, `scripts/build_state_of_the_art.py`
- 新規: `scripts/repro.py`, `docker/Dockerfile`, `docker/README.md`, `scripts/cluster/run_holdout_pipeline.py`, `config/cluster_holdouts.yml`, `scripts/galaxies/compute_fdb_signatures.py`
- 更新: `Makefile`（`repro` ターゲット）, `requirements.txt`, `environment.yml`
- JSON/HTML: `server/public/state_of_the_art/data/fig_eu1c.json`, `server/public/state_of_the_art/early_universe_class.json`, `server/public/state_of_the_art/index.html`, `server/public/state_of_the_art/holdout_status.json`

## 次アクション
- Docker イメージを CI から利用できるよう GitHub Actions (or agent-gate job) で `make repro` を実行し、閾値逸脱時に失敗させる。
- Lenstool 公式 tarball を取得し、`scripts/cluster/run_holdout_pipeline.py --auto-train --auto-holdout` を実走させて MACSJ0416 / AbellS1063 の ΔAICc≤−10, S_shadow 有意を確認。
- `scripts/galaxies/compute_fdb_signatures.py` を銀河一括処理用の `scripts/galaxies/run_signatures_batch.py` へ拡張し、棒/ディスク/殻の固有予測 (方向・1/r²復帰・左右差) を統計化。
