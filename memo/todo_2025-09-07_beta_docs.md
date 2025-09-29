# todo_2025-09-07_beta_docs — CLI `--beta-forward` 利用ガイド整備

## 背景
- FDBの薄層（surface）/体積（ULM）比較で、`scripts/compare_fit_multi.py` に導入された `--beta-forward` が文書化されていない。
- β>0 により界面照度項 `irradiance_log_bias` と 1/r 加速度 `line_bias_accel` へ前方化ウエイトが掛かり、外縁や棒方向を強調できる。

## 目的
- 既存の手順書（特に `docs/benchmarks/NGC3198_procedure.md`）へ `--beta-forward` の意味・推奨値・角度指定との関係を追記し、再現者が設定意図を把握できるようにする。
- 例コマンドを掲載し、Lambert(β=0)との差分検証方法を示す。

## 実装タスク
- 手順書ステップ4（角度核アブレーション）を拡充し、βの範囲、`--aniso-angle` / `--auto-geo` との連携、`--fdb-mode` との組合せを説明する。
- 具体的な CLI 例（Lambert基準 vs β=0.3 の比較）を記述。
- 必要に応じて `docs/state-of-the-art.md` の関連節にも出力反映の旨を追加。

## メモ
- コード参照: `src/models/fdbl.py::irradiance_log_bias`, `src/fdb/angle_kernels.py::radial_forwardize`。
- 角度は `--aniso-angle` 又は `--auto-geo` の銀河位置角を流用。
- βは 0..1 の正規化で、先行ベンチでは β≈0.3 が外縁残差を改善。
