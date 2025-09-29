# run_2025-09-08_ulm_metrics_ci

## 結果サマリ
- 用語刷新: 表示文言を ULW→ULM に統一（CV/ SOTA/ ベンチ残差図のラベル）。
- メトリクス恒常化: 単一ベンチ（NGC 3198/2403）に rχ² 行を追加（AICc/(N,k) 併記を維持）。
- 監査/CI: 共有JSONの sha 指紋一致チェックを追加し、リンク存在監査と合わせて CI で強制。
- リンク健全化ポリシー: SOTAの監査バナーを HTTP 200 完了時のみ自動表示（未復旧時は非表示）。

## 生成物
- 変更: `scripts/cross_validate_shared.py`（表示ラベル ULM、ヘッダ更新）、`scripts/build_state_of_the_art.py`（ULM表記・監査バナー制御強化）
- 変更: `scripts/benchmarks/run_ngc3198_fullbench.py`, `scripts/benchmarks/run_ngc2403_fullbench.py`（rχ² 追加／ULM表記）
- 変更: `scripts/benchmarks/make_ngc3198_residual_overlay.py`, `scripts/benchmarks/make_ngc2403_residual_overlay.py`（図ラベル |g_ULM|）
- 追加: `scripts/qa/audit_shared_sha.py`（shared_params.json の sha 一致検証）
- 追加: `.github/workflows/ci.yml`（リンク監査＋sha検証）
- 追加: `data_links.json`（HI/Hα 直リンクのレジストリ雛形）
- 更新: `TODO.md`（D+2 フォローアップを追記）

## 次アクション
- 表示文言の残差（紙面/図キャプション/既存HTML）を一括再生成してULM統一を完了。
- CI拡張: 合計χ²一致、Solar Null、代表6再計算表の存在チェックを加え、落ちたら公開停止へ。
- `data_links.json` を取得スクリプトに配線し、H I/Hα 取込を半自動化。

