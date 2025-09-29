# 2025-09-02 TODO 実行ログ（最終便）

実行時刻(UTC): 2025-09-02 20:55–21:05

## 対応内容
- モデルの3クラス化とAdapter層の導入
  - `src/models/adapter.py` を新設。`GRBaryonModel`, `FDB3Model`, `MONDModel` と共通IFを定義。
  - 既存関数を安全にラップし、段階的移行が可能な設計。
- 再走用スクリプトの追加
  - `scripts/fit_all.sh`: サブセット作成→共有フィット→CV→SOTA再生成→E2Eの一括実行。
  - `Makefile` に `fit-all` / `artifacts` を追加。
- 解析ログのartifact化
  - `scripts/artifacts.py` を追加。`compare_fit_multi.py` 終了時に実行の文脈（引数・選択結果・データセット・メトリクス等）を `data/artifacts/` にJSON保存。
- TODOの完了処理
  - `TODO.md` と `server/public/TODO.md` を空バックログに整理。
  - `memo/sota_rewrite_plan.md` の該当チェックを [x] に更新。

## 生成物
- `src/models/adapter.py`
- `scripts/fit_all.sh`
- `scripts/artifacts.py`
- `data/artifacts/*.json`（以後の実行時に蓄積）
- `Makefile` ターゲット: `fit-all`, `artifacts`

## 次アクション案
- `compare_fit_sparc.py` など既存スクリプトをAdapter経由に段階移行（動作同値性を確認しつつ）。
- MOND/NFW等のパラ範囲・事前の明文化とAdapter対応（別メモへ）。

