# サイト運用Runbook（./site サーバー）

日付: 2025-08-31

## 目的
- 本研究の進捗を静的サイト`./site`で公開する。
- 図・SOTAページ・論文図の更新を自動化し、更新漏れを防ぐ。

## ディレクトリ
- ソース: `docs/`（Markdown, 画像は`docs/img/`）
- 生成物: `site/`（静的サイトの公開ルート）
- 図の生成源: `assets/figures/`

## よく使うコマンド
- 一括生成＋反映（推奨）
  - `make publish-site`
    - 図生成→SOTA最終更新の自動更新→画像同期→mkdocs build
    - 出力は`./site`に配置

- SOTAページだけ更新
  - `make figs`（図の再生成）
  - `make docs`（最終更新更新＋docs/img同期）
  - `make site`（mkdocs build）

- ローカル配信（プレビュー）
  - `make serve` → http://127.0.0.1:8000/

## スクリプト概要
- `scripts/update_sota_lastmod.py`:
  - `docs/state-of-the-art.md`見出し直下の"Last updated"を
    `YYYY-MM-DD`で自動更新。
- `scripts/plot_sota_figs.py`:
  - 改善ヒスト、redχ²散布、代表VRパネルの生成。
- `scripts/plot_compare_shared.py`:
  - 共有(a,b,c)適用の比較図（例: DDO154/161）。
- `scripts/sync_figs_to_docs.sh`:
  - `assets/figures`→`docs/img`へ同期。
- `scripts/serve_site.sh`:
  - `./site`を簡易HTTPサーバーで配信（既定:8000）。
- `scripts/update_and_build_site.sh`:
  - 図生成→SOTA同期→mkdocs build を一括実行。

## 運用手順（進捗が出たら）
1) 解析・実装を進める（図やCSVが`assets/`に出力）。
2) `make publish-site`を実行。
3) `make serve`でローカル確認。
4) 公開が必要なら、任意:
   - GitHub Pages: mainにpush（`.github/workflows/deploy-pages.yml`）
   - 任意サーバー: `scripts/deploy_rsync.sh` を環境に合わせ実行

## 注意事項
- 画像は`assets/figures`がソース。docs/paperへは同期で反映。
- `site/`は生成物につき直接編集しない。
- `mkdocs.yml`のnavにSOTAページを登録済み。

