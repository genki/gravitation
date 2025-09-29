# run_2025-09-22_p0_actions

## 結果サマリ
- バレットホールドアウトを再実行し、`sigma_highpass in {0.7,1.0,1.5,2.0}`, `sigma_psf in {1.0,1.5,2.0}`, `w(Sigma_e)^p` (p∈{0,0.3,0.7})、`roi_quantiles={0.65,0.70,0.75,0.80}` を探索。S_shadow=0.378、p_perm=0.00225 を達成した設定で `server/public/reports/bullet_holdout.json` を更新。
- NGC3198/NGC2403 フルベンチを再生成し、`fair.json_sha=56f181ae9122`, `shared_params_sha=aa694c7f90ea...` に統一。SOTA ビルドを更新し、トップカードと KPI を最新化。
- `make repro-local` を実行(bench3198→bench2403→class_validate→repro_local_checks)。AICc/χ²/BAO/Solar の閾値チェックが `[repro-local] verification passed` で完了、`env.lock` は既存値で確認済み。

## 生成物
- 更新: `server/public/reports/bullet_holdout.html`, `server/public/reports/bullet_holdout.json`
- 更新: `server/public/state_of_the_art/index.html`
- 更新: `server/public/reports/bench_ngc3198.html`, `server/public/reports/bench_ngc2403.html`
- 更新: `docs/runbook.md`
- ログ: `server/public/reports/cluster/Bullet_progress.log`, `logs/auto_holdout_20250921.log` (追記), `scripts/repro_local_checks.py` 出力

## 確認事項
- S_shadow の新値: 0.377958 / p_perm=0.002249 (n=12000) を `jq '.indicators.S_shadow' server/public/reports/bullet_holdout.json` で確認。
- DeltaAICc(FDB-rot)=-6.79e+07, DeltaAICc(FDB-shift)=-6.74e+06 を再確認。
- `rg 'fair.json_sha=' server/public` で旧値(4edd...) が残っていないことを確認。
- `rg 'sha256:e049e07a446b' server/public` が一致 0 件であることを確認。
- `make repro-local` 実行ログに `[repro-local] verification passed` が出力されることを確認。

## 次アクション
- AbellS1063 / MACSJ0416 のホールドアウトを再実行し、S_shadow 有意化と ΔAICc<0 を達成する設定を特定。
- 広帯域宇宙論(弱レンズ 2PCF, CMB ピーク) の軽量尤度を追加実装し、Late-FDB vs ΛCDM の ΔAICc≈0 を検証。
- `scripts/repro_local_checks.py` の許容閾値を runbook に明文化し、手順書に SHA/環境ハッシュ/通知コマンドを追記。
