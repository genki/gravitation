# 通知talker(@localhost:8082) 起動ガイド（ドラフト）

## 概要
- 目的: `scripts/notice.sh` の送信先 `talker/notice` をローカルで受信し、デスクトップ通知/ログ出力する。
- 既定送信先:
  - agent-gate経由: `https://agent-gate.s21g.com/moon/$AGENT_TOKEN/@localhost:8082/notice`
  - 直接モード: `NOTICE_DIRECT=1` で `http://127.0.0.1:8082/notice`

## 手順（例: Node/Express 簡易受信）
- `npm init -y && npm i express`
- `server.js`:
  ```js
  const express = require('express');
  const app = express();
  app.use(express.json());
  app.post('/notice', (req,res)=>{ console.log('notice:', req.body); res.sendStatus(204); });
  app.listen(8082, ()=>console.log('talker on 8082'));
  ```
- 起動: `node server.js`
- 送信テスト:
  ```sh
  NOTICE_DIRECT=1 ./scripts/notice.sh -m "hello" -t "test"
  ```

## Makefile との連携
- `make notify-test` は直接・同期モードで疎通チェックします。
- タイムアウトは `NOTICE_CONNECT_TIMEOUT`/`NOTICE_MAX_TIME` で短縮可能。

## 運用Tips
- 定常運用時は `systemd --user` や `pm2` で自動起動を推奨。
- Slack連携は `.env` に `SLACK_WEBHOOK_URL` を設定。
- ネット未到達時も `server/public/notifications/` にミラーされます。
