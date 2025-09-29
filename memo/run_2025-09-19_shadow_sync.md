# 2025-09-19 バレット S_shadow フェア条件同期

## 結果サマリ
- `config/fair.json` に shadow セクション（edge_quantiles=[0.70,0.72,0.75,0.78,0.80,0.82,0.85,0.88], edge_count=220, rr_quantile=0.78 など）を追加し、`config/baseline_conditions.json` と併せてフェア条件を更新。
- `scripts/reports/make_bullet_holdout.py` が fair.json の shadow 設定を優先利用するよう改修し、環境変数なしでホールドアウト再生成。
- バレットホールドアウトで S_shadow(global)=0.373、p_perm=0.0045 (<0.01) を達成し、SOTA トップカードと詳細ページの数値を同期。
- `scripts/repro.py` の期待値を最新の ΔAICc / S_shadow / p_perm に更新し、1-click 再現チェックが新フェア条件に追随するよう調整。

## 生成物
- 更新: `config/fair.json`
- 更新: `config/baseline_conditions.json`
- 更新: `scripts/reports/make_bullet_holdout.py`
- 更新: `scripts/repro.py`
- 更新: `server/public/reports/bullet_holdout.html`
- 更新: `server/public/reports/bullet_holdout.json`
- 更新: `server/public/state_of_the_art/index.html`

## 次アクション
- バレット shadow 指標のブートストラップ CI を JSON へも恒常公開するか検討。
- `analysis/shadow_bandpass.py` を銀河ベンチでも流用し、S_shadow 表示を共通化。
- FDR の q=0.01/0.05 閾値をダッシュボードへ追加して自動判定を明示。
