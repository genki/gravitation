# SOTA代表図にブラックリスト混入の修正

- 実行時刻: 2025-09-02 07:49 UTC

## 結果サマリ
- SOTA代表図の選定で `data['names']` から先頭を採っていたため、BL対象が混入するケースがあった
- `scripts/build_state_of_the_art.py` を修正し、代表図候補 `names` からブラックリストを除外
- 再生成後、CamB などBL対象が代表図から除外されていることを確認

## 生成物
- 更新: `scripts/build_state_of_the_art.py`

## 次アクション
- 将来的に結果JSONの生成時にもBL反映を徹底（重複防止の二重ガード）
