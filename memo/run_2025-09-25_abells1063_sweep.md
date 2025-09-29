# run_2025-09-25_abells1063_sweep

## 結果サマリ
- `make_bullet_holdout.py` を AbellS1063 向けに再実行し、`BULLET_PERM_N/SHADOW_PERM_N` を 256〜12000 に切替えながら σ_psf∈{1.0,1.5,2.0}, 高通過σ∈{0.7,1.0,1.5,2.0}, mask_q∈{0.65,0.70,0.75,0.80}, weight_power∈{0,0.3,0.7}, edge_q∈{0.75,0.80,0.85} をスイープ。S_shadow(global) は最大でも ~0.055（p≈0.43）で、有意化には至らなかった。
- StageResume により permutation/residual 256 件体制でのスイープは 5〜9 分/ケース、12,000 件体制は >150 分となることを確認。探索フェーズでは perm=256 で候補を絞り、最終候補に対してのみ perm≥12,000 を適用する方針を整理。
- `tmp/sweep/abells1063_fast.jsonl` に FAST_HOLDOUT=1 でのパラメータログを生成（S_shadow=NaN のため評価指標としては未使用）。出力 JSON に `metadata.command` や env overrides を含めることで再現性を追跡できる状態を確保した。

## 生成物
- 更新: `server/public/reports/cluster/AbellS1063_holdout.json`, `server/public/reports/AbellS1063_holdout.html`
- 追加ログ: `tmp/sweep/abells1063_fast.jsonl`
- メモ: 本ファイル

## 次アクション
1. `edge_count` を 512/1024 に固定、`edge_q` を 0.90 以上へ引き上げつつ、`BULLET_SHADOW_SE_Q` を 0.6/0.8 と切替える小規模スイープを継続し、S_shadow>0.1 の候補を探索する。
2. 有望な候補が見つかったら perm/resid を ≥12,000 に戻し、p_perm<0.01 を満たすまで StageResume を許容して本番実行する。
3. `sweep_bullet_shadow.py` に FAST モードでも S_shadow を記録できるよう改修（NaN 回避）し、探索ログを定量化する。
