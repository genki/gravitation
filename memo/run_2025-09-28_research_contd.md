# 研究継続（FAST: outer強調の欠番補完 + 安全運用）

## 結果サマリ
- 直近FASTの p 値を確認: AbellS1063 p≈0.45, MACSJ0416 p≈0.33（有意水準未到達）。
- 欠番の外側強調コンボを2件投入（単一BGジョブ内で逐次実行し、メモリ安全性を優先）。
- dispatcher を `--scope` 付きで使用し、tmux 巻き添えと OOM リスクを低減。

## 生成物
- 投入ジョブ（逐次）: `outer_emph_gap_fill`
  - MACSJ0416 FAST band=4–8, block_pix=6, rr_q=0.9, radial_exp=2, ROI=[0.80,0.85], w∈{0,0.3}
  - AbellS1063 FAST band=8–16, block_pix=6, rr_q=0.9, radial_exp=2, ROI=[0.80,0.85], w∈{0,0.3}
- ログ: `server/public/reports/logs/outer_emph_gap_fill_*.log`
- 進捗: `server/public/reports/cluster/*_progress.log`（各ホールドアウトで自動追記）
- 実行環境: OMP/MKL/OPENBLAS/NUMEXPR=1, `MALLOC_ARENA_MAX=2`, `PYTHONMALLOC=malloc`, scope分離。

## 次アクション
- 完了後、`*_holdout.json` の `S_shadow.perm.p_perm_one_sided_pos` を再評価。
- 有意 (p<0.02) が出た場合は FULL（n_perm=1e4, bands=4–8/8–16, σ_psf=1.0/1.5/2.0）へ昇格。
- 追加検証候補（必要に応じて）:
  - asinh 変換の外側強調（MACSJ0416/AbellS1063 両方, band=4–8 と 8–16）。
  - rr_quantile の微調整（0.88/0.92）と block_pix の比較（6/8）。

## 監視/自動昇格
- BG監視(通知): `scripts/jobs/watch_and_notify.py --interval 20` を scope 分離で起動。
- 自動昇格: `scripts/jobs/auto_escalate_full.py --holdouts MACSJ0416,AbellS1063 --interval 20 --timeout 7200` を scope 分離で起動。
- 実行メタ: `tmp/jobs/job_watcher_*.json`, `tmp/jobs/auto_escalate_full_watch_*.json`
