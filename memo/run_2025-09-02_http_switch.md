# サイト配信をHTTPS→HTTPへ切替

- 実行時刻: 2025-09-02 06:15 UTC

## 結果サマリ
- `Makefile`の `web-restart`/`web-deploy` で `USE_TLS=0` を明示
- `scripts/start_web.sh` を修正し、HTTP時は証明書生成をスキップ
- `server/server.py` を修正し、HTTP時は証明書不要・フッター表示をHTTPに切替

## 生成物
- 更新: `Makefile`, `scripts/start_web.sh`, `server/server.py`
- ドキュメント更新: `docs/runbook.md`

## 次アクション
- ブラウザから `http://localhost:3131` で表示を確認
- 必要あれば `USE_TLS=1` で一時的にTLSへ戻せます（Makefile変更済）
