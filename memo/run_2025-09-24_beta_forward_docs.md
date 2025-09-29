# run_2025-09-24_beta_forward_docs

## 結果サマリ
- TODO「CLIオプション --beta-forward の利用ガイド追加」を消化し、`docs/benchmarks/NGC3198_procedure.md` のステップ4を前方化βの説明付きで拡充。
- `--beta-forward` の役割（Lambert→前方化、ウエイト式）、`--aniso-angle`/`--auto-geo` との連携、β=0/0.3 を比較する例コマンドを追加。
- 実行結果を記録する際の `meta.beta_forward` ログ化を明示し、再現者への利用ガイドラインを確立。

## 生成物
- 更新: `docs/benchmarks/NGC3198_procedure.md`
- メモ: `memo/todo_2025-09-07_beta_docs.md`

## 次アクション
1. 今後のベンチ作業では β=0 ↔ β>0 の比較ログを `memo/run_*.md` に記述し、ΔAICc/ELPD 差分を共有する。
2. `docs/state-of-the-art.md` のクラスタ／銀河カードに `meta.beta_forward` 表記を追加する予定があれば、SOTA更新の際に追記する。
