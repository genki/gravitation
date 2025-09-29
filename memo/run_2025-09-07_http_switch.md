# SOTAサーバー: HTTPS→HTTPへ切替

## 結果サマリ
- 運用プロトコルを HTTPS(自己署名) から HTTP へ変更。
- systemd ユニットを更新し `NO_TLS=1` で常時HTTP起動。証明書生成は抑止。
- ヘルスチェック: `curl http://localhost:3131/healthz` が 200 OK を返却。

## 生成物
- `/etc/systemd/system/gravitation-sota.service`（HTTP版に更新）
- リポジトリ控え: `server/gravitation-sota.service`

## 次アクション
- 外部向け公開が不要であればFWは現状維持。公開する場合は `3131/tcp` を開放。
- ドキュメントのURL表記（READMEほか）を http://localhost:3131 に統一。

## 備考
- いつでも HTTPS に戻す場合は unit の `NO_TLS=1` を外し、`USE_TLS=1` に戻して再起動。
