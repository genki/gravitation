# クラスタHO方向性の有意化（多重スケールS・外側強調・perm≥6k）BG投入

## 結果サマリ
- AbellS1063/MACSJ0416 に対し、界面ゲートSの多重スケール(σ_g=2,4,8)・外側強調(radial_exp=2)・RR閾(0.9)・外側帯域(q=[0.80,0.98])を適用し、Permutation n≥6000 で再評価をBG投入しました。
- Σ_e 変換として identity/asinh の直交2条件を band=8–16 で逐次実行。
- 実行は systemd scope 分離＋メモリ/スレッド制限で安定化。

## 生成物
- BGジョブ: `ho_dirsig_knee_batch`（逐次4本）
- ログ: `server/public/reports/logs/ho_dirsig_knee_batch_*.log`
- 進捗: `server/public/reports/cluster/*_progress.log`（Permutation 進行表示）

## 次アクション
- 完了後、`*_holdout.json` の `S_shadow.perm.p_perm_one_sided_pos` を確認（p<0.05 目標）。
- 必要に応じて PSF σ・高通過σ・g の格子（指示A-4）を追加入力。
