# 研究進捗配信用Webサーバー

本サーバーは開発用の自己署名証明書を使ってHTTPSで配信します。

- バインド: `0.0.0.0:3131` (アクセスは`https://localhost:3131`推奨)
- 配信ルート: `server/public/` (index), リポジトリの参照リンクあり

## 使い方

1) 証明書生成(初回のみ)

   `bash scripts/gen_dev_cert.sh`

2) 起動

   `bash scripts/start_web.sh`

3) アクセス

   ブラウザで `https://localhost:3131` を開きます。
   0.0.0.0は待受アドレスであり、URLとしての利用は推奨されません。

注意: 自己署名のためブラウザ警告が表示されます。開発用途限定です。

