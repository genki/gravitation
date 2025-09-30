# 2025-10-01 並行タスク: WLトモグラフィ preview 作成（JST）

## 結果サマリ
- KiDS‑450 の各トモグラフィビンの n(z) を用いて ξ± を算出する **preview** を作成（ΛCDM / Late‑FDB）。
- SOTAの宇宙論リンク群に **WL tomo(preview)** を追加（正式カード整備までの橋渡し）。

## 生成物
- 追加: `scripts/reports/make_wl_tomo_preview.py`
- 出力: `server/public/state_of_the_art/wl_2pcf_tomo_preview.html`（図: `wl_tomo_preview_bin*.png`）
- 更新: `scripts/build_state_of_the_art.py`（リンク追加）

## 次アクション
- 共分散ブロック・IA/m補正を導入した **正式トモグラフィ**へ移行。
- 収束確認: |ΔAICc|≤10（ΛCDM同等）をKPIに継続評価。
