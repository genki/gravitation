# run_2025-09-24_sota_representative_fix

## 結果サマリ
- SOTA 代表比較図が空欄になる原因を調査したところ、`build_state_of_the_art.py` 内で JSON の `names` リストが別セクション処理で空にされた後に参照されていた。
- `names` を読み込んだ直後にキャッシュ (`names_cache`) を保持し、代表図生成では常にキャッシュを優先して利用するよう修正。
- 実行後 `make sota-refresh` により `server/public/state_of_the_art/index.html` を再生成し、6枚の tri-compare 図（GR+DM / MOND / FDB）が表示されていることを確認。

## 生成物
- 更新: `scripts/build_state_of_the_art.py`
- 更新: `server/public/state_of_the_art/index.html`

## 次アクション
1. 代表比較図のキャッシュロジックが他セクションに影響しないか、後続ビルドでも監視を継続する。
2. 今後 JSON 形式を変更する場合は `names_cache` の作成箇所を併せて更新する。
