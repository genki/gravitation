# SOTAサーバー常駐化と自動起動設定

## 結果サマリ
- `server/server.py` を systemd 管理下で常時稼働化。HTTPS(自己署名)で `0.0.0.0:3131` にバインド。
- OS起動時の自動起動を有効化（`gravitation-sota.service`）。ヘルスチェック `/healthz` で稼働確認。
- 初回起動時は自己署名証明書を自動生成（存在しなければ `scripts/gen_dev_cert.sh` を実行）。

## 生成物
- systemd ユニット: `/etc/systemd/system/gravitation-sota.service`
- 証明書: `server/certs/dev.crt`, `server/certs/dev.key`
- ログ: `journalctl -u gravitation-sota`（journald、必要に応じてファイル出力へ変更可）

## 次アクション
- ファイアウォール環境下での外部アクセス要否に応じ `3131/tcp` を開放（不要ならローカルのみの利用で可）。
- 本番相当の証明書を使う場合は `USE_TLS=1` のまま `dev.crt/dev.key` を差し替え。
- サーバ表示のAIC→AICc表記統一（SOTA/一覧ページの再生成）に着手。

## 参考
- 手動操作例:
  - 起動状態: `systemctl status gravitation-sota`
  - 再起動: `sudo systemctl restart gravitation-sota`
  - ログ: `journalctl -u gravitation-sota -f`
