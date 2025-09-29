# run_2025-09-22_sota_refresh_b

## 結果サマリ
- `scripts/build_state_of_the_art.py` を再実行し、AbellS1063 ホールドアウトの最新値 (ΔAICc(FDB−rot)=-3.26e9, ΔAICc(FDB−shift)=-2.15e8, S_shadow=0.256/p=0.18) を SOTA カードへ反映した。
- 共有パラメータ表記 (sha256:aa694c7f90ea) と KPI 表記の整合を確認。

## 生成物
- 更新: `server/public/state_of_the_art/index.html`

## 確認事項
- `rg AbellS1063 server/public/state_of_the_art/index.html` でカードに新しい ΔAICc / S_shadow が掲載されていることを確認。
- `server/public/reports/cluster/AbellS1063_holdout.json` の数値と一致していることを `jq` で確認。

## 次アクション
- AbellS1063 S_shadow の有意化 (p<0.01) を目指し、edge_quantiles や align offset の探索を継続する。
- MACSJ0416 の ΔAICc(FDB−rot) を負側へ改善するための再学習・調整プランを立案する。
