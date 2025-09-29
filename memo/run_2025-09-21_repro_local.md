# 2025-09-21 ローカル再現環境整備と AbellS1063 再訓練

## 実施日時
- 2025-09-21 JST

## 実施内容
- AbellS1063 用 Chandra ObsID (4966/18611/18818) を取得し、`make_sigma_wcut_from_cxo.py` で `sigma_e/omega_cut` を再生成。
- `run_holdout_async.sh AbellS1063` で整準をやり直したホールドアウトをバックグラウンド再投入。
- `scripts/repro_local_checks.py` を新設し、ベンチAICc/バレットΔAICc・S_shadow/BAO χ² を即‐確認できる仕組みを追加。
- `make repro-local` ターゲットを Makefile に追加（bench×2, BAO 再計算, 軽量検証スクリプト呼び出し）。
- `pip freeze > env.lock` を実行し、ローカル 1-click 再現用の環境ロックファイルを設置。

## 生成物
- `data/cluster/AbellS1063/sigma_e.fits`, `omega_cut.fits`（再生成）
- `server/public/reports/logs/holdout_AbellS1063_20250921_095836.log`（進行中ジョブ）
- `scripts/repro_local_checks.py`（新規）
- `Makefile:repro-local`（ターゲット追加）
- `env.lock`

## 次アクション
- バックグラウンドジョブ完了後、`server/public/reports/cluster/AbellS1063_holdout.json` の ΔAICc / S_shadow を確認し、SOTAを再同期。
- `make repro-local` をフル実行してログ化（timeout を緩めて再試行）。
- 弱レンズ2PCF・CMBピークの軽量尤度（Late‑FDB vs ΛCDM）を算出し、SOTAへ数値掲載。
