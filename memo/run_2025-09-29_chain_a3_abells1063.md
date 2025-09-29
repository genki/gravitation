# A-2完走後の自動キック: A-3(膝グリッド) — AbellS1063

日時: 2025-09-29 07:55 JST

## 結果サマリ

- `chain_after_ho_dirsig.sh` を追加し、A-2(ho_dirsig knee batch) 完了を待って
  **AbellS1063 の A-3 (W_eff 膝: q_knee×p×xi_sat)** を自動投入するチェインを作成。
- 実行は `dispatch_bg.sh` 経由（tmux非依存、スレッド=1固定）。

## 生成物

- スクリプト: `scripts/jobs/chain_after_ho_dirsig.sh`
- 依存スクリプト: `scripts/jobs/batch_w_eff_knee.sh`（A-3実行本体）

## 次アクション

- チェインを起動してA-2→A-3の自動連結を確立。
- AbellS1063のA‑3が完了し次第、MACSJ0416も同様にチェイン投入（状況によりA‑4を続けて計画）。

