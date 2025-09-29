# ブラックリスト反映・共有パラメータ再フィット（更新）

- 実行日: 2025-09-02
- 目的: ブラックリスト（不規則含む）を反映し、共有(λ,A,gas)を再同定。

## 実行
- セット: `data/sparc/sets/clean_no_blacklist.txt`（対象 100 銀河）
- コマンド: `PYTHONPATH=. .venv/bin/python scripts/run_shared_fit_filtered.py`

## 結果サマリ
- 最良: λ≈20.0 kpc, A≈125.0, gas_scale≈1.33
- 合計χ²: GR≈2.02e+04 → ULW≈4.96e+03（改善倍率×4.08）

## 生成物
- JSON: `data/results/multi_fit_all_noBL.json`
- HTML: `server/public/reports/multi_fit_all_noBL.html`
- セット: `data/sparc/sets/clean_no_blacklist.txt`

## 次アクション
- BL反映版でCV/ブートストラップを再実施→SOTAへ要約追加。
