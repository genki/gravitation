# ブラックリスト考慮版 5-fold 交差検証

- 実行日: 2025-09-02
- 目的: BL対象外のみで共有(λ,A,gas)の汎化性能を検証。

## 実行
- 入力: `data/sparc/sets/clean_no_blacklist.txt`
- グリッド: λ={18,20,22,24}, A={100,112,125}, gas={1.0,1.33}
- コマンド: `PYTHONPATH=. .venv/bin/python scripts/cross_validate_shared.py --names-file data/sparc/sets/clean_no_blacklist.txt`

## 結果サマリ
- 合計Test χ²: GR≈2.02e4 / ULW≈5.00e3（改善×4.04）
- ΔAICc≈−1.52e4（ULW有利）

## 生成物
- JSON: `data/results/cv_shared_summary.json`
- HTML: `server/public/reports/cv_shared.html`

## 次アクション
- BL考慮版の要約をSOTAに固定表示（現状注記あり）。
- グループ別（LSB/HSB）でのCVもBL考慮版で実施（任意）。
