# run_2025-09-23_notify_dup

## 結果サマリ
- `scripts/notice.sh` の `curl_common` から `--retry 2 --retry-all-errors` を削除し、通知送信が単発で行われるよう修正した。
- `make notify-done` 実行時に同一通知が最大3通届く現象を確認。原因は `scripts/notice.sh` が `curl --retry 2 --retry-all-errors` を非同期実行していたため、一度の送信で最大3回 POST が発火する設計にあった。
- デフォルトの `connect_timeout=2` 秒・`max_time=6` 秒が短いため、ゲート応答がわずかに遅れるだけで `curl` がエラー扱いとなりリトライ→重複通知になる。

## 詳細調査
- `scripts/notice.sh:125` で `curl_common=( -fsS --retry 2 --retry-all-errors --connect-timeout "$connect_timeout" --max-time "$max_time" )` を定義。非同期モード (`ASYNC_MODE=1`) では `send_async curl ...` が実行される (`scripts/notice.sh:156-159`)。
- `--retry-all-errors` によりタイムアウト・TLS交渉失敗などあらゆるエラーで POST を再送。POST は冪等でないため、 gate 側が毎回通知を発火すると同一メッセージが最大3通生成される。
- `connect_timeout=2` / `max_time=6` は `NOTICE_CONNECT_TIMEOUT` / `NOTICE_MAX_TIME` 未設定時の既定 (scripts/notice.sh:27-28)。処理が6秒を超えると失敗扱い→再送。
- `mirror_to_file` は常時呼び出し (`scripts/notice.sh:158-160`) されるが、これはローカル記録用で重複送信問題に直接は関与しない。
- 2025-09-23 に `curl_common` からリトライ指定を除去し、`bash -n scripts/notice.sh` で構文チェック済み。

## 対策案
1. **送信挙動の監視**: 本修正後の通知重複が解消されるか確認し、必要に応じて `NOTICE_CONNECT_TIMEOUT` / `NOTICE_MAX_TIME` を調整。
2. **冪等化検討**: 受信側での `X-Notice-Id` 等による重複排除は別タスクで検討。

## 次アクション
- 修正後の通知ログを観測し、必要に応じて `NOTICE_CONNECT_TIMEOUT` / `NOTICE_MAX_TIME` を調整。
- 受信側仕様を確認し、`X-Notice-Id` 等による重複排除の可否を検討。
