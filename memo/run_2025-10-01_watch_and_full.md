# 2025-10-01 A-4集計ウォッチャ投入＋FULL昇格準備（JST）

## 結果サマリ
- A-4 FAST（AbellS1063）用に **集計ウォッチャ**をBG起動（60秒毎にサマリ更新）。
- **FULL昇格スクリプト**（A-4スナップショット→上位選抜→FULLディスパッチ）を追加し、集計完了後に投入可能な状態に。

## 生成物
- 追加: `scripts/jobs/watch_collect_a4.sh`（A-4スナップショットの定期集計）
- 追加: `scripts/jobs/dispatch_full_from_a4.py`（上位構成のFULL昇格ディスパッチ）
- ログ: `server/public/reports/logs/watch_collect_a4_AbellS1063_*.log`

## 次アクション
- スナップショット蓄積→サマリ更新を待ち、`dispatch_full_from_a4.py --holdout AbellS1063 --top 1..2` を実行。
- FULL完了後、`S_shadow/p_perm/ΔAICc` をSOTA反映、通知。
