## 結果サマリ
- 大きなメディア/アセット（>5MB）は Git LFS で保存するよう .gitattributes を拡張し、既存の大容量ファイルをステージしました。
- 一般的にgitに入れるべきコアファイル（<100件）を追加（README/要件/Dockerfile/エントリHTML/一部docs/workflows）。

## 生成物
- コミット: 「LFS: extend media asset patterns; add large media assets; add core configs and entry pages (<100 files).」
- 更新: .gitattributes（mp4/webm/mp3/wav/ogg/flac/tiff/bmp/pdf 等）

## 次アクション
- 追加でLFS対象にしたい拡張子があれば指示ください（例: *.pdf 全域などの範囲変更）。
