# 2025-09-26 — SOTA 更新（MACS J0416 ΔAICc 負化を反映）

## 結果サマリ
- `make sota-refresh` により SOTA カードを更新し、MACS J0416 が **ΔAICc(FDB−rot)=-3.26×10⁴**, **S_shadow=0.724 (p=0.064)** の最新FAST結果に差し替わったことを確認。

## 実施内容
- MACS J0416 κマップの再投影後、FASTホールドアウト結果を元に SOTA を再生成。
- HTML の「現在の課題」カードを確認し、MACS 項目が ΔAICc 負化と p 値の改善を反映していることを確認。

## 生成物
- `server/public/state_of_the_art/index.html`
- `server/public/reports/progress_card.html`

## 次アクション
- MACS J0416 FAST 設定で p_perm<0.02 を満たす探索を継続し、達成次第 FULL (n_perm≥1e4, global+outer, band 4–8/8–16) で確証。
- Abell S1063 Σ層の再設計と FAST→FULL 移行を進める。
