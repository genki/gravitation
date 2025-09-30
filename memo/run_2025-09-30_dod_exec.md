# 証明完了（DoD）に向けた実行計画の着手と進捗

版: 2025-09-30

## 結果サマリ
- 実行計画（P1–P4, A/B/C/D）の骨子をSOTA運用に反映。A系列（クラスタ方向性）を優先着手。
- A-3（W_eff“膝”）のFASTグリッドを **MACSJ0416** でバックグラウンド起動。ログとPIDを記録（dispatcher経由、OOM分離）。
- **UGC06787** ベンチの追加調査として「外縁1/r²の安定性（Jackknife/Bootstrap）」ページを生成し、SOTAに反映。
- SOTA（index/HO進捗/リンク群）をビルドし直し、rep6統一テンプレ/Total基準と各リンクの健全性を再確認。

## 生成物
- server/public/reports/ugc06787_outer_slope_stability.html（図: ugc06787_outer_slope_stability.png）
- server/public/reports/bench_ugc06787.html / .png / .svg / .json（既存を活用）
- サイト更新: server/public/state_of_the_art/index.html（更新時刻更新）
- BGジョブ（A-3 FAST, MACSJ0416）
  - メタ: tmp/jobs/run_knee_fast_MACSJ0416_20250930_052228.json
  - ログ: server/public/reports/logs/run_knee_fast_MACSJ0416_20250930_052228.log

## 次アクション
- A-3（MACSJ0416 FAST）完了後、S_shadow>0 かつ p_perm<0.05 に寄与する構成を選抜し、FULL（perm=5000固定）へ昇格。
- A-3（Abell S1063）: FAST結果の上位構成を **FULL（perm=5000）** で再評価（ΔAICc維持+方向性有意）。
- A-4（Σ_e変換×g×PSF/高通過）: 直交格子をFAST→FULLの順で実行。Permutation≥5000／ブロックBootstrapCIを併記。
- B-系: rep6/ベンチのリンク整備（UGC06787を含む）と数値整合の点検を継続。
- C-1: CLASS 連携（同一共分散）カードの雛形実装と動作確認。

---

## 参考: 実行コマンド・設定
- UGC06787 外縁安定性: `PYTHONPATH=. ./.venv/bin/python scripts/reports/make_outer_slope_stability.py --name UGC06787`
- SOTA再生成: `PYTHONPATH=. ./.venv/bin/python scripts/build_state_of_the_art.py`
- A-3 FAST（MACSJ0416, bg）: `scripts/jobs/dispatch_bg.sh -n run_knee_fast_MACSJ0416 --scope -- "bash scripts/jobs/run_w_eff_knee_fast_seq.sh MACSJ0416"`

## 備考（フェア条件）
- 全比較で (N,k)・誤差床 clip(0.03×V_obs, 3..7) km/s・AICc を統一。rng=42 を明示固定。脚注帯/メタへ反映。

