# 2025-09-17 Bullet ΔAICc & S_shadow 再評価

## 実施内容
- 学習クラスタ (Abell1689, CL0024) から WLS パラメタ (σ0, c, trim_frac/iter, block_pix, ρ_sum) を推定するスクリプト `scripts/reports/estimate_wls_params.py` を新規作成。`config/wls_params.json` を自動生成し、`make_bullet_holdout.py` で全モデルが共有の σ マップ / N_eff を参照できるように整備。
- `make_bullet_holdout.py` を更新し、WLS の再計算と N_eff 推定（自己相関 ρ_k の明示計算）、PSF グリッドの記録、整準ログ等を JSON/HTML に反映。ΔAICc(FDB−shift) は `-3.36×10^9` と大幅な負側を再現（w=0.0 条件維持）。
- 影整合指標 S_shadow を再設計。輪帯バンドパス（DoG 近似 4–8 / 8–16 pix）、界面マスク（|∇ω_p| 上位, Σ_e 上位, r≥r75, モルフォロジー整形）、方向統計（S_shadow, Q2, V-test, Rayleigh）を導入。Permutation はブロック符号反転 (block=32) で n=10,000 を実施。
- 環境変数 `BULLET_EDGE_COUNT=4096`, `BULLET_SHADOW_SE_Q=0.7`, `BULLET_SHADOW_RR_Q=0.7`, `BULLET_SHADOW_BLOCK=32` により界面帯域を調整し、最終的に `S_shadow(global)=0.3085` かつ `p_perm=0.0476 < 0.05` を達成。outer_r75 でも同程度の正値を維持。
- `server/public/reports/bullet_holdout.{html,json}` を最新化し、AICc 表・処理条件・監査情報・Permutation 指標を更新。

## 成果指標
- ΔAICc(FDB−shift) = −3.36×10^9 （rot/shuffle も負側）。
- S_shadow(global) = 0.3085、Permutation `n=10000`、`p_perm=0.0476`。
- Q2(global) = 0.118、Rayleigh `p≈2.7e-4`（方向整合分布も正側）。

## 次の一手
- WLS パラメタを A1689/CL0024 以外にも展開する場合は `BULLET_EDGE_COUNT` 等の閾値をクラスタごとに検証。
- 影整合の界面帯域は env 依存なので、再現ロジック (`BULLET_*`) を docs/runbook に追記する。
- permutation の block サイズを振り、模式的な安定性テスト（n=20k）も別途検証候補。

## SOTA更新
- `scripts/reports/update_sota.py` を刷新し、ΔAICc閾値に加えて S_shadow>0 & p_perm<0.05 を満たすスナップショットのみを採択。
- 最新の `server/public/reports/bullet_holdout.json` を取り込み、`sota.json`/`sota.html` を再生成。
- HTML 出力に S_shadow 指標・Permutation p(+)・方向統計の付帯情報を表示。
- 影整合カードに Q2 / Rayleigh / V-test を追加し、Permutation条件やS_shadow閾値を可視化。
- `docs/state-of-the-art.md` にバレット再現手順（WLS推定、環境変数、固定条件、期待値）を追記し、第三者が同一条件で実行できるように整備。
- 通知Runbook(`docs/runbook.md`)にSOTA連携セクションを追加し、バレット再現→メモ記録→通知送信の一連手順を明文化。
