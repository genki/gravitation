# 2025-09-30 SOTA環境ログリンク追加＋BG監視継続（JST）

## 結果サマリ
- SOTAの「環境とツール」に **env_logs.txt/json（ciaover/lenstool -v）へのリンク**を追加。監査性を強化。
- 宇宙論（WL 2PCF 正式）は **n(z) 畳み込み**対応済（tomo1-1）。カード・サマリ・SOTAを再生成済。
- BG: AbellS1063 A-3 FULL は resid-perm 進行中（ETA 17:10±10分）。MACSJ0416 A-3 FULL は完了済。

## 生成物
- 更新: `scripts/build_state_of_the_art.py`（環境ログの行を追加）
- 出力: `server/public/state_of_the_art/index.html`（環境ログリンクを掲示）
- 参考: `server/public/reports/env_logs.txt`, `server/public/reports/env_logs.json`

## 次アクション
- AbellS1063 FULLの完了検出→A-4 FAST 自動投入→ S_shadow/p_perm/ΔAICc 集計→ SOTA更新。
- WL 2PCF: トモグラフィ全ビン＋共分散ブロック対応・IA/m補正の導入を継続。
