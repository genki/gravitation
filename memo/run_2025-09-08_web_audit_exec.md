# 実行メモ: WEB-AUDIT 実行と監査バッジ同期（2025-09-08）

日時: 2025-09-08

## 結果サマリ

- ローカルHTTPサーバを起動（3131）し、`BASE=http://localhost:3131 make site-audit` を実行。
- 監査は `ok=true`。`used_ids.csv` / `cv_shared_summary.html` / `notifications/` が HTTP 200 到達、`shared_params` 単一ソースも整合。
- SOTAトップを再生成し、監査バッジと実体リンクの一致を確認（自動反映）。

## 生成物

- 監査レポート: `server/public/state_of_the_art/audit.json`（ok=true; http200=all true）。
- SOTA更新: `server/public/state_of_the_art/index.html`（監査ステータス反映）。
- サーバ: `scripts/start_web.sh` 経由で http://localhost:3131 を起動（ログ: PID表示）。

## 次アクション

- 指標の恒常化（AICc/(N,k)/rχ²、誤差床脚注）を適用し、代表6の再計算と対照検証へ接続。
- 用語同期の残差（ULW表記が残るコードコメント/生成物）は表示層のみULMに統一し、データキーは互換維持。

