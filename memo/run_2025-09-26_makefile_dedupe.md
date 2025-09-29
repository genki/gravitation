# Makefile 重複ターゲットの解消（警告対処）

## 結果サマリ
- `bench-ngc3198`/`bench-ngc2403` の重複レシピを削除し、包括的な旧定義を採用した
- `ha-ngc3198`/`ha-ngc2403` は改良版（後方の定義）のみ残し、旧定義を削除した
- 先頭TAB欠落に伴う `missing separator` を修正し、`make -n` 実行で警告ゼロを確認

## 生成物
- Makefile（重複レシピの整理・整形）
- 検証ログ（`make -n bench-ngc3198`, `make -n bench-ngc2403` で警告なし）

## 次アクション
- 他ターゲットの重複有無を継続監視（追加警告が出た場合は同様に集約）
- `ha-*` 系の引数仕様を README/Runbook に反映（IN/IN_HA/IN_R の使い分け）
