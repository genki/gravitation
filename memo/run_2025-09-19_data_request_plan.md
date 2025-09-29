# 2025-09-19 MACSJ0416/AbellS1063 データ調達計画

## 目的
- P1-1 サンプル拡張に必要な MACSJ0416 / AbellS1063 の `omega_cut.fits`, `sigma_e.fits`, `kappa_obs.fits` を準備するため、入手先と手順を明文化する。

## 手順案
1. 既存 Lenstool 公式リポジトリへのアクセス元を確認し、`data/raw/lenstool/` 配下に `macsj0416.tar.gz`, `abells1063.tar.gz` を配置依頼する。
2. 受領後、`scripts/cluster/prep/reproject_all.py` を用いて WCS と視野を A1689/CL0024/Bullet と一致させる。
3. `scripts/cluster/maps/make_sigma_e.py`・`make_omega_cut.py`（必要な場合）で薄層マップを生成し、ヘッダに `PIXKPC` を記入する。
4. 作成した FITS を `data/cluster/<name>/` へ配置し、`run_holdout_pipeline.py --auto-train --auto-holdout` を再実行してパラメタ凍結→ホールドアウト適用を行う。

## 状況
- 2025-09-19 時点で `data/cluster/MACSJ0416` / `data/cluster/AbellS1063` は存在せず、`config/cluster_holdouts.yml` では MISSING 状態。

## TODO 更新
- `TODO.md` の P1-1 項目に「tarball 受領（macsj0416, abells1063）」を追記済み（別タスク）。

