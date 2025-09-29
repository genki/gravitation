# 2025-09-02 TODO 実行ログ（第2便）

実行時刻(UTC): 2025-09-02 20:35–20:45

対応内容:
- SOTA: CVテンプレ置換漏れの修正（`LAM_GRID`等のテンプレがそのまま出ていた問題）
  - `scripts/cross_validate_shared.py` のHTML生成を f-string 化。
  - 既存の `server/public/reports/*.html` 内の該当箇所を実際のグリッド配列に修正。
- LSB/HSB フィルタ: ID差分ログ出力を追加
  - `scripts/make_subsets.py` に、前回の `lsb.txt`/`hsb.txt` と比較した追加/削除IDのログ出力機能を実装。
  - 出力先: `server/public/reports/lsb_hsb_diff_YYYYMMDDTHHMMSSZ.txt`
- M/L 表: 推定値±区間の表示に対応
  - `scripts/build_state_of_the_art.py` の CSV ローダを拡張。
  - `ml_disk_map, ml_disk_p16, ml_disk_p84`（および bulge の同等列）が存在する場合は `MAP ± (p84-p16)/2` を表示。
  - 既存の `ml_disk, ml_bul` のみでも後方互換で値を表示。
- 用語統一（“gravity”不使用・表記整理、SOTA関連の表現を調整）
  - `docs/state-of-the-art.md` の「見かけ重力」を「見かけの引力（見かけの加速度）」へ。
  - `src/models/fdbl.py` 冒頭説明も同様の語彙へ更新。

備考:
- M/L の区間はCSVに p16/p84 が存在する場合のみ反映（無い場合は点推定のまま）。
- CVレポートのプレースホルダは生成スクリプト修正済み。新規再生成で恒久対応となる。

関連ファイル:
- scripts/cross_validate_shared.py
- scripts/make_subsets.py
- scripts/build_state_of_the_art.py
- server/public/reports/cv_shared*.html
- docs/state-of-the-art.md, src/models/fdbl.py

