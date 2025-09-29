# 環境内の通知手段サーベイ（Ubuntu24.04）

- ホスト: Ubuntu24.04, カーネル6.8系（headless）
- GUI: DISPLAY未設定。ユーザーDBusは稼働（userバス有）
- ログイン中TTY: `pts/0, pts/1, pts/2`（ユーザーvagrant）
- cron: `enabled/active`
- journald: 利用可（`logger`, `journalctl`）

## 利用可能なコマンド

- `wall`: 端末に対する一斉通知
- `write`: 特定TTYへのダイレクト通知
- `mesg`: 端末への書込許可切替（`y/n`）
- `logger`: syslog/journal通知
- `notify-send`: コマンドは在るが通知デーモン不在で実用不可
- `systemd-notify`: systemd向け通知（ユーザー通知用途ではない）
- `crontab`: 定期通知のトリガーに利用可
- `tmux`, `screen`: インストール済。稼働セッションは検出無し

## 未導入/非推奨の手段

- ローカルメール: `mail/mailx/sendmail`系なし。MTA未導入
- `at`系: `at/atq/atrm`なし

## 実用パターンと例

### 1) 端末一斉通知（現在ログイン中に即時）

- 全TTYへ:
  ```sh
  wall "[通知] バックアップ完了 21:00"
  ```

- 注意: 各TTYが`mesg y`である必要。

### 2) 特定ユーザー/TTYへ通知

- 接続中TTYを確認:
  ```sh
  who
  # 例: vagrant  pts/2  ...
  ```
- 個別送信:
  ```sh
  printf "デプロイ完了\n" | write vagrant pts/2
  ```

### 3) システムログを通知チャネルとして使う

- 書込みと閲覧:
  ```sh
  logger -t deploy "本番デプロイ成功"
  journalctl -t deploy -f
  ```

- 用途: バックグラウンド処理の進捗や失敗検知に有効。

### 4) cronで定期通知/遅延通知

- 例: 毎時ジョブの終了を通知
  ```sh
  # エディタで設定
  crontab -e
  # またはワンライナーで設定
  (crontab -l 2>/dev/null; \
   echo "0 * * * * /usr/bin/wall '毎時ジョブ完了'" ) | crontab -
  ```

### 5) tmux/screen内の通知（セッション稼働時）

- tmux:
  ```sh
  tmux display-message "ビルド完了"   # 5秒表示は -d 5000
  ```
- screen:
  ```sh
  screen -X wall "ビルド完了"
  ```

## デスクトップ通知（notify-send）について

- 現状: `notify-send 0.8.3`は在るが通知デーモンが稼働していない。
- サーバー環境のためDISPLAY未設定。表示先がなく実用不可。
- もし必要なら、軽量通知デーモン導入と環境設定が必要。
  例: `notification-daemon`をユーザーサービスで起動し、
  `DISPLAY`と`DBUS_SESSION_BUS_ADDRESS`を整える。

## ローカルメール通知を使いたい場合

- MTA未導入のため、そのままでは送信不可。
- 簡易構成例:
  - 送信専用: `msmtp-mta` + `bsd-mailx`/`s-nail`
  - 本格MTA: `postfix`（ローカル配送/リレー設定要）
- 導入しない限り`mail`/`mailx`は利用不可。

## 端末ベル（簡易アラート）

- 端末にベルを鳴らす:
  ```sh
  printf "\a"   # 端末設定に依存
  ```

## 推奨方針（この環境）

- 即時・確実: `wall` または `write`（TTY在席時に強い）
- バックグラウンド追跡: `logger` + `journalctl`
- 定期/遅延: `cron` + 上記の`wall`/`logger`
- GUI前提の`notify-send`は現状は非推奨（無効）
- ローカルメールは未構成のため不可。必要なら軽量MTA導入を検討

## 検出結果（抜粋）

- コマンド: `wall, write, mesg, notify-send, logger, crontab` は存在
- MTA系: `sendmail, mail, mailx, msmtp` は未導入
- systemdユーザー: `dbus.service`のみ稼働、通知デーモン無し
- ログインTTY: `pts/0, pts/1, pts/2` に`vagrant`

