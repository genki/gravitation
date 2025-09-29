# run_2025-09-27 再開用メモ（現況・ETA・次アクション）

## 結果サマリ
- クラスターHO（MACSJ0416/AbellS1063）のFASTは複数設定を並列起動し、p̂<0.02 を検出次第 FULL（perm≥1e4）へ自動昇格する監視ジョブを稼働中。
- 代表比較（W·S vs Φ·η）は「公平スイープ（NGC3198/2403）」をBG実行中。A/B（FAST→FULL）は Φ·η FAST の終了待ちで待機。
- 進行中の全ジョブは server/public/reports/logs/ と server/public/reports/cluster/ の進捗ログから追跡可能。

## 現在の実行・監視
- MACSJ0416: FAST 2/3/4（outer強調・asinh・block_pix 8/10/12・weight 0.0/0.3/0.5）
  - 直近 p_perm ≈ 0.236（未達）
  - 監視: auto_full_MACSJ0416（p̂<0.02 で FULL perm=10000 を即起動）
- Abell S1063: FAST 1（outer 0.70/0.80/0.85）と FAST 2（outer厚め 0.75/0.85/0.90 + asinh）
  - 直近 p_perm ≈ 0.587（未達）
  - 監視: auto_full_AbellS1063（p̂<0.02 で FULL perm=10000 を即起動）
- 代表6（フェアスイープ）: rep6_phieta_fair（NGC3198/2403）をBG実行
- 代表6（A/B）: Φ·η FAST（rep6_ab_fast の中）が稼働中。完了→FULL→代表HTML生成→SOTA更新の順に自動実行。

## ETA（目安）
- 各FAST: 3–8分／設定（Permutation 2000 回 + バンド処理）
- FULL: 10–25分（perm=10000）+ HTML/JSON/SOTA更新: 2–5分
- 代表6フェアスイープ: 10–20分 + SOTA更新: 2–3分
- 代表6A/B（Φ·η FAST）: 1–2 時間（計算環境依存）

## 再開時の見所（ログと生成物）
- 進捗ログ: 
  - MACSJ0416: server/public/reports/cluster/MACSJ0416_progress.log
  - AbellS1063: server/public/reports/cluster/AbellS1063_progress.log
- 出力JSON/HTML（自動更新）: 
  - server/public/reports/MACSJ0416_holdout.json/.html
  - server/public/reports/AbellS1063_holdout.json/.html
  - server/public/reports/ws_vs_phieta_rep6.html

## 次アクション
- [自動] p̂<0.02 を検知 → FULL を自動起動 → SOTA再生成 → 通知（notify-done-site）。
- [手動/補助] p が停滞する場合、FASTの `--roi-quantiles` / `--block-pix` / `--weight-powers` を追加探索。
- [代表6] フェアスイープ完了後、DoD‑1（|Δ(ΔAICc)| ≤ 5）を表に表示済みか監査し、必要なら再ビルド。

## 再現情報（rng/sha/cmd）
- rng: 42（Permutation/Resid/Shadow の固定seedは 42/314）
- fair.json: sha12 は各ページ脚注に掲示（代表6・SOTA）。
- 起点コマンド例は研究指示メモ（memo/run_2025-09-27_research_directive.md）を参照。

## 連絡・通知
- 完了時は `make notify-done-site` により、直近メモからサマリを抽出して送信・サイト更新。
