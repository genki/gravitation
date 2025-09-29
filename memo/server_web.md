# 配信用Webサーバー運用メモ

- 目的: 進捗/成果をHTTPSで配信(開発用途)
- 実装: Python `http.server` + TLS, 静的配信
- 配信: `server/public/` をドキュメントルートとして配信

## 起動手順

1) 証明書生成(初回)
   - `bash scripts/gen_dev_cert.sh`
2) 起動
   - `bash scripts/start_web.sh`
3) アクセス
   - `https://localhost:3131` でアクセス
   - 0.0.0.0 は待受アドレス。URLには `localhost` を推奨。

## 設定

- バインド: `HOST=0.0.0.0`, `PORT=3131`
- 証明書: `server/certs/dev.crt`, `server/certs/dev.key`
- 入口: `server/public/index.html`
 - 図ギャラリー: `/figures` (ソース: `paper/figures`)

## 注意事項

- 自己署名のためブラウザ警告が出ます。開発・ローカル専用。
- 証明書SANは`localhost`と`127.0.0.1`を含みます。
- レポジトリ内の`memo/`, `data/`, `paper/`へ相対リンクで誘導。
 - 図は`paper/figures/`にPNG/JPEG/SVGを配置すると自動で表示。

## 2025-08-27 更新

- ルーティング拡張: `/memo/`, `/paper/`, `/data/` パスをrepo直下に
  プロキシ。`*.md`はサーバー側で簡易Markdown→HTML変換して配信、
  それ以外は静的ファイルとしてそのまま配信します。
  - 例: `/memo/foo.md` → `./memo/foo.md`
  - 例: `/paper/main.tex` → `./paper/main.tex`
