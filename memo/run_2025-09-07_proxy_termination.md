# リバースプロキシでのSSLターミネーションと外部公開URL

## 結果サマリ
- SOTAサーバーはローカルでHTTP(`http://localhost:3131`)として稼働。
- 外部公開はリバースプロキシによりSSLターミネーションの上で提供。
- 公開URL（例）: 
  - https://agent-gate.s21g.com/moon/67279209d81d4e890c28cbd088d8cd58396dfbe1c729eea299acfa74b3661ffa/@localhost:3131/reports/bench_ngc3198.html

## 生成物
- 運用メモ: 本ファイル（SSL終端と公開経路の記録）

## 次アクション
- 必要に応じ `server/README.md` のURL表記に外部公開URLの注記を追加。
- 監視: `/healthz` の外形監視（ゲート越し）要否を検討。
