# TODOメモ — FDB-volume geometry catalog

## 背景
- 体積版FDBの前処理で、面輝度マップを3D発光率へリフトアップするためには、銀河ごとの傾斜(i)、位置角(PA)、ディスク厚み(h_z)が必須。
- 初期実装では NGC3198 / NGC2403 のみ値を暫定投入。その他の SPARC noBL サンプルは `TEMPLATE_FILL_ME` を削除しながら埋める必要がある。

## やること
1. SPARC / S4G / THINGS など一次情報を確認し、残り銀河の i/PA を geometry.yaml に追記。
2. h_z は photometric scale height 文献（S4G decompositions 等）から引用し、ソースを明記。
3. warp や flaring のある銀河は `notes` に区画化ルール（半径閾値）を記載。
4. 反映後は `scripts/fdb_volume/io.py`（未実装）で参照し、ログに geometry ソースを表示する。

## 成果物
- 更新: `config/fdb_volume/geometry.yaml`
- メモ: 本ファイル

## 次アクション
- geometry ローダ実装時に、欠損が残っていればログ WARN を出し `TODO` 行を再掲する。
