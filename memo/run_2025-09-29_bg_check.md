# BGジョブ確認 — HO方向性バッチ進行状況（A系列）

日時: 2025-09-29 07:26 JST

## 結果サマリ

- 実行中: AbellS1063 shadow-perm（se=none, band=8–16, perm=6000）。
  進捗 3515/6000, 経過25.3m, ETA≈17.9m（ログ参照）。
- 実行形態: 4本を順次実行（同一nohup内で直列）
  1) AbellS1063 se=none → 2) AbellS1063 se=asinh →
  3) MACSJ0416 se=none → 4) MACSJ0416 se=asinh。
- リソース: OMP/MKL/OPENBLAS=1, MALLOC_ARENA_MAX=2。
  RSS≈1.5GiB, 空きRAM≈0.9GiB, Swap使用≈215MiB。OOMの兆候なし。
- 監視: `scripts/jobs/watch_and_notify.py` 稼働中。
  `state_of_the_art/jobs.html` が定期更新されている。

## 主要ログ/生成物

- 進捗ログ: `server/public/reports/logs/ho_dirsig_knee_batch_20250929_061814.log`
- Watcherログ: `server/public/reports/logs/job_watcher2_20250929_030135.log`
- 既存成果: `server/public/reports/AbellS1063_holdout.html`（FAST版既了行あり）

## 実行条件（抜粋）

- 学習: `Abell1689, CL0024` / ホールドアウト: `AbellS1063, MACSJ0416`
- ゲートS: `sigmas=2,4,8`, `RR_q=0.9`, `SE_q=0.75`
- 外側強調: `q_low=0.80, q_high=0.98`, `radial_exp=2`
- バンド: `8–16`、置換: `perm-n=6000 (min=5000,max=6000)`、`block-pix=6`
- Σ変換: `se-transform ∈ {none, asinh}`（順次）

## 次アクション

- A-2の完走を待ち、A-3（W_effの膝: `q_knee×p×ω比`）を単一HOずつ投入。
- StageResumeのファイル名衝突回避（digest付与）を実装し並列安全化。
- A-5の可視化（`S_shadow`/境界帯域検定）をHOページに恒常化。
- 実行時は引き続きスレッド1固定・ログ進捗をWatcherで配信。

