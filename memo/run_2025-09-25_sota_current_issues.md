# 2025-09-25 — SOTA 現在の課題カード再生成

## 結果サマリ
- SOTAトップに「現在の課題」カードが残っていることを確認し、Abell S1063 / MACS J0416 の未達状況を明示。

## 実施内容
- `scripts/build_state_of_the_art.py` の現在の課題集計ロジック（Abell S1063・MACS J0416・宇宙論pending）を確認。
- `make sota-refresh` を実行し、最新の holdout JSON をもとに SOTA HTML を再生成。
- 出力 HTML にカードが期待どおり表示されるか `grep` で検証。

## 生成物
- `server/public/state_of_the_art/index.html`

## 次アクション
- Abell S1063: Σモデル再設計＋FAST→FULL 検証で S_shadow>0, p_perm<0.01 を目指す。
- MACS J0416: WCS/PSF/ROI の監査後、ΔAICc/ S_shadow 判定を再実行。
