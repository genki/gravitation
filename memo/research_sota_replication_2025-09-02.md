# research_sota_replication_2025-09-02

## 目的
- SOTA図表の再現性検証と信頼区間再計算を自動化し、更新フローに統合。

## 手順(案)
- `scripts/build_state_of_the_art.py`/`scripts/plot_sota_figs.py`の再現スクリプト化とシード固定。
- 依存データのバージョン固定、生成物のハッシュ検証。

## 成果物
- 自動再現ジョブ、更新ドキュメント、CI統合の提案。
