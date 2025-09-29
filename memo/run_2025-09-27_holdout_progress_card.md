# run_2025-09-27 ホールドアウト進捗カード（MACSJ0416 / AbellS1063）

## 結果サマリ
- HO進捗（AICc, ΔAICc, S_shadow, p_perm, n）を一望できる軽量カードを作成し、SOTAからの導線を追加。
- 進捗は既存の `server/public/reports/cluster/*_holdout.json` を参照して自動更新される（再生成時）。

## 生成物
- server/public/state_of_the_art/holdout_progress.html（表: AICc・Δ・S_shadow・p_perm・n）
- SOTAトップのクイックリンク「HO進捗」を追加

## 次アクション
- FULL完了後の値（perm≥1e4）を自動反映。達成（p_perm<0.01, S_shadow>0）時はSOTA要約に“汎化確証”を追加。
