# メモ: WEB-AUDIT（リンク健全化と監査バッジ連動）

目的: notifications/・used_ids.csv・主要レポートがHTTP 200で到達。非到達時は
SOTAの監査バッジ/リンクを自動でOFFにし、復旧後に自動ON。

受け入れ条件(DoD)
- `make site-audit-ci BASE=http://localhost:3131` がゼロ終了。
- `server/public/state_of_the_art/audit.json` の http.200 が all true。
- SOTAトップの監査バッジが audit.json に追随（到達不可時は非表示）。

実行手順
1) `make site-audit BASE=http://localhost:3131`
2) 落ちたリンクを `data_links.json` や `scripts/qa/run_site_audit.py` の例外設定
   で修復。直アクセスで 200 を確認。
3) `make build-sota`（バッジが自動反映されることを確認）。

補足: 受信サービスが停止していても `server/public/notifications/` のファイル
ミラーで参照可能（通知ポリシー）。

