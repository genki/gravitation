# StageResume並列安全化＋A-3/A-4バッチスクリプト追加（実装メモ）

日時: 2025-09-29 07:42 JST

## 結果サマリ

- `StageResume` を**digest付きファイル名**へ移行（`{holdout}_{stage}_{digest[:8]}_*`）。
  旧形式（digestなし）は**後方互換で読み取り**、digest不一致時のみクリア。
- **環境変数オーバライド**を追加（A-3膝スキャン向け）:
  `BULLET_Q_KNEE, BULLET_P, BULLET_XI, BULLET_XI_SAT, BULLET_S_GATE, BULLET_TAU_Q, BULLET_DELTA_TAU_FRAC, BULLET_SE_TRANSFORM`。
- 研究A-3/A-4用の**非対話バッチ**を追加。
  - A-3: `scripts/jobs/batch_w_eff_knee.sh`（q_knee×p×xi_sat）
  - A-4: `scripts/jobs/batch_se_psf_grid.sh`（Σ変換×PSFσ×高通過σ）
- いずれも `dispatch_bg.sh` で**単一nohup内直列実行**、tmux非依存・ログ一元化。

## 生成物

- 変更: `scripts/reports/make_bullet_holdout.py`（StageResume/ENV Override）
- 新規: `scripts/jobs/batch_w_eff_knee.sh`, `scripts/jobs/batch_se_psf_grid.sh`
- メモ: このファイル（実装記録）

## 次アクション

- 現行A-2バッチ完走後、各HO単位でA-3→A-4を**直列投入**（同時多発は避ける）。
- 既存のレガシー`*_meta.json`/`*_values.jsonl`は、次走からdigest付きへ移行（自動）。
- WatcherにA-3/A-4の簡易ステータス集計を追加（任意）。

