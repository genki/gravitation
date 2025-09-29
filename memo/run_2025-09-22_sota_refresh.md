# run_2025-09-22_sota_refresh

## 結果サマリ
- `PYTHONPATH=. python scripts/build_state_of_the_art.py` を実行し、AbellS1063 の最新ホールドアウト結果（ΔAICc, S_shadow, N/N_eff など）を SOTA トップとカードへ反映した。
- SOTA カードのクラスタ欄が `ΔAICc(FDB−rot)=-1.36e+07`、`ΔAICc(FDB−shift)=-6.19e+05`、`S_shadow=0.055 (p=0.38)` を表示することを確認した。

## 生成物
- 更新: `server/public/state_of_the_art/index.html`
- ログ: `logs/auto_holdout_20250921.log`（参照用）

## 確認事項
- `rg AbellS1063 server/public/state_of_the_art/index.html` でカードとリストが更新されていることを確認。

## 次アクション
- S_shadow 有意化に向け、P0-B 指示どおり帯域・界面マスク・重みの再探索を設計し、AbellS1063 へ適用する。
