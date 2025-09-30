# 2025-09-30 WL 2PCF 正式カードの n(z)畳み込み実装 + BG監視・環境ログ（JST）

## 結果サマリ
- 宇宙論(WL 2PCF 正式): tomo1-1 向けに **n(z) 畳み込みカーネル**を実装（単一z近似→分布畳み込みへ）。`make cosmo-formal` でカードとSOTAを再生成。
- 環境: `capture_env_logs.sh` を実行し **ciaover/lenstool -v** のログを `server/public/reports/` に常設。
- BG: AbellS1063 A-3 FULL は2本目 perm 進行中（shadow-perm ≈ 286/5000 → 進捗観測継続）。MACSJ0416 A-3 FULL は完了済。

## 生成物
- 更新: `scripts/reports/make_cosmo_formal.py`（`lensing_kernel_nz` と `compute_wl_predictions(..., nz_pair=...)` を追加）
- 出力: `server/public/state_of_the_art/wl_2pcf_formal.html`, `cmb_peaks_formal.html`, `cosmo_formal_summary.json`
- 更新: `server/public/state_of_the_art/index.html`（リンク・更新時刻）
- 環境ログ: `server/public/reports/env_logs.txt`, `server/public/reports/env_logs.json`

## 次アクション
- WL 2PCF: トモグラフィ各ビンへの一般化（n(z)×共分散ブロック対応）と IA/m 補正の導入、|ΔAICc|≤10 への収束確認。
- BG: AbellS1063 A-3 FULL 完了検出→A-4 FAST 自動投入（チェイン監視維持）→ 指標集計（S_shadow/p_perm/ΔAICc）→ SOTA更新。
