# run_2025-09-22_sota_directive

## 結果サマリ
- 2025-09-22 08:40 JST 時点の SOTA をもとに、新指示書 `memo/directive_2025-09-22_sota_gap.md` を作成し、宇宙論・銀河ベンチ・クラスタ HO・SHA 揺らぎ・P0/P1 アクションを更新した。
- P0 の重点(バレット S_shadow 改善、SHA 統一、repro_local 運用)と P1 の汎化・広帯域宇宙論タスクを再整理した。

## 生成物
- 新規: `memo/directive_2025-09-22_sota_gap.md`

## 確認事項
- `server/public/state_of_the_art/index.html` と `server/public/reports/cluster/AbellS1063_holdout.json` を参照し、数値(DeltaAICc, S_shadow, p値, READY 状態)を照合済み。

## 次アクション
- P0-A 記載の S_shadow 走査プロトコル(帯域・マスク・重み・PSF)を実行し、p_perm<0.01 を満たす設定を特定する。
- P0-B のとおり `fair.json_sha` と `shared_params_sha` を統一し、JSON→HTML 同期ログを runbook に追加する。
