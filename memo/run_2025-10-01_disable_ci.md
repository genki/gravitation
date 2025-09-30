# 2025-10-01 GitHub CI 無効化（方針: CIは使わない）

## 結果サマリ
- GitHub Actions の自動トリガを停止し、**手動実行のみ可能**な状態に変更しました（push/PRで走りません）。
- 対象: `.github/workflows/ci.yml`, `deploy-pages.yml`。

## 生成物
- 更新: `.github/workflows/ci.yml` — `on:` を `workflow_dispatch` のみに変更、`name: CI (disabled)` に注記。
- 更新: `.github/workflows/deploy-pages.yml` — 同様に `workflow_dispatch` のみに変更、`name: Deploy Pages (disabled)` に注記。

## 次アクション
- GitHub 上のCI失敗は以後発生しません（手動起動をしない限り）。
- 必要であれば、将来の再有効化時に `push`/`pull_request` を `on:` に戻すだけで復帰可能です。
