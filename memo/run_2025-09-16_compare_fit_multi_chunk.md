# compare_fit_multi 分割実行対応 — 2025-09-16

## 結果サマリ
- `scripts/compare_fit_multi.py` に進捗ファイルベースの分割実行機能を追加し、`--chunk-size` / `--max-minutes` / `--progress-file` / `--reset-progress` を実装。
- 進捗ファイルは `--out` に `.progress.json` を付与したパスへ保存し、時間超過時は途中終了して次回再開可能にした。
- `scripts/compare_fit_multi_chunked.sh` を新設し、最大実行時間を 55 分(既定)に制限したチャンクを連続投入できるラッパーを用意。
- `scripts/fit_all.sh` の共有フィット呼び出しをラッパー経由へ置換し、`FIT_ALL_MAX_MINUTES` / `FIT_ALL_CHUNK_SIZE` / `FIT_ALL_RESET_PROGRESS` で制御できるようにした。

## 生成物
- 既存更新: `scripts/compare_fit_multi.py`, `scripts/fit_all.sh`
- 新規: `scripts/compare_fit_multi_chunked.sh`
- 進捗ファイル: `data/results/multi_fit_clean.json.progress.json`（実行時に自動生成）

## 次アクション
- 必要に応じて `FIT_ALL_CHUNK_SIZE` を設定し、組み合わせ数ベースでもチャンク上限を調整する。
- 既存の進捗ファイルが残っている場合は `RESET_PROGRESS=1` もしくは `--reset-progress` を付与して初回実行前にクリアする。
- 実際の長時間ジョブで分割完了までの挙動を確認し、通知・レポートフローに影響が無いかをレビューする。
