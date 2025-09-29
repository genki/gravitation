# 2025-09-19 P0タスク段取り・担当割りプラン

## 対象タスク
1. AICc 公平化（P0-2）
2. BAO χ²/AICc 常設（P0-3）
3. Solar ペナルティ本線統合（P0-4）
4. 1-Click 再現 CI（P0-5）

## 体制と担当
- **解析基盤チーム**: `scripts/build_state_of_the_art.py`, `config/fair.json`, `docs/state-of-the-art.md` の更新と監査ライン整備。
- **宇宙論チーム**: CLASS 連携・BAO YAML・Fig-EU1c を含む cosmology pipeline の維持。
- **インフラ/CI チーム**: Docker / conda / GitHub Actions (or equivalent) の整備、seed 固定検証、リンク監査。

## タイムライン（2025-09-19 開始想定）
| タスク | Owner | 期間 | マイルストーン |
| --- | --- | --- | --- |
| AICc 公平化 | 解析基盤 | 09-19〜09-20 | `config/fair.json` 一元化、各 AICc 表に (N,N_eff,k,χ²,rχ²) を脚注化、`scripts/qa/audit_shared_params.py` へチェック追加 |
| BAO 常設 | 宇宙論 | 09-19〜09-21 | Fig-EU1c データブロックに χ²/AICc/p 値＋dataset 注記、`docs/state-of-the-art.md` 同期、`bao_points.yml` バリデーション |
| Solar 統合 | 解析基盤 + 宇宙論 | 09-19〜09-21 | Solar ペナルティ式/感度図を `state_of_the_art` カードへ固定表示、`config/fair.json` に bound パラメタ追記、再現テスト |
| 1-Click 再現 | インフラ/CI | 09-20〜09-22 | `docker/` + `environment.yml` 更新、`scripts/repro.py` をCI化、used_ids/notifications リンク監査自動化、緑化報告 |

## 依存関係
- Solar 統合は AICc 公平化（fair.json sha 固定）完了後に実装。
- 1-Click 再現は AICc 公平化および Solar 統合済みのリポジトリ状態を前提。
- BAO 常設は cosmology リソースが CLASS 3.3.2.0 を呼び出せる環境（Docker/conda）整備と並行進行。

## 成果物テンプレ
- 各タスク完了時に `memo/run_2025-09-19_*` 形式で run memo を作成。
- `TODO.md` の該当行を消化後に削除し、通知には run memo 名を含める。

## リスク/フォロー
- フェア条件更新後は `scripts/repro.py` の閾値を即時更新し、CI で乖離検出。
- CLASS 計算が長時間化する場合は `docker` イメージに事前キャッシュを導入。
- 通知ポリシーに従い、各完了時に `make notify-done` を実行。
