# 2025-09-18 バンドパス影指標モジュール化

## 結果サマリ
- `analysis/shadow_bandpass.py` を新設し、輪帯 FFT・Scharr 勾配・ブロック統計・Benjamini-Hochberg を含む S_shadow/Q2 の汎用評価クラス `ShadowBandpassEvaluator` を実装。
- `scripts/reports/make_bullet_holdout.py` から帯域処理ロジックを同モジュールへ委譲し、フェア条件に沿った FDR(q) 自動計算とブロック・ブートストラップの再利用性を改善。
- 既存フローでの core/outer マスク評価・Permutation/Bootstrap の呼び出しを新クラスに合わせて更新し、py_compile で構文検証を実施。

## 生成物
- analysis/shadow_bandpass.py（帯域 S_shadow/Q2 評価モジュール）
- scripts/reports/make_bullet_holdout.py（ShadowBandpassEvaluator 利用、FDR 処理刷新）

## 次アクション
- `ShadowBandpassEvaluator` を単一銀河ベンチ / CI でも再利用し、指標表示を SOTA ページに統一。
- core/outer 用マスクの自動生成ルールを `analysis/shadow_bandpass.py` 内に抽象化し、将来的なマスク設計比較に備える。
- FDR q=0.01 / 0.05 の閾値レポートを JSON 出力に追加し、ダッシュボードの自動色分けに組み込む。
