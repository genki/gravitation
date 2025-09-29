# SOTAレビュー受領と着手内容（2025-09-07）

## 結果サマリ
- レビュー（2025‑09‑07）に基づく優先タスク群を受付。まずはクリティカル修正1件目の土台として **監査バッジ⇔CI連動**の仕組みを確認し、Makeターゲット `site-audit` を新設。
- `scripts/qa/run_site_audit.py` により `server/public/state_of_the_art/audit.json` を生成し、`scripts/build_state_of_the_art.py` がこれを読んで **「監査OK/要確認」** と **HTTP未達時の注記・リンク抑止** を反映する経路を確認。SOTA再生成 (`build-sota`) と連動。
- 通知ログはローカル（/notifications/）で200応答。リバースプロキシ（Agent Gate）越しの到達可否はCIの `BASE` 環境変数で検査できる状態を整備。

## 生成物
- Makefile: `site-audit`（新規） — `BASE=... make site-audit` で監査実行→SOTA再生成。
- 既存: `server/public/state_of_the_art/audit.json`（CI結果の格納先; builderが参照）。

## 次アクション
- [1-A] CIに `BASE` を設定して `make site-audit` を実行（ゲート越しの `notifications/` が非200なら SOTAに「要確認＋リンク一時非表示」反映）。
- [1-B] ゲート設定を確認し `/notifications/` が200を返すよう復旧（復旧まで SOTA では非表示と注記）。
- [2] 代表6（Surface vs Volumetric）の再計算: N・k・誤差床の完全一致を保証するスクリプト更新とmd5表記の常設化。
- [3] Prospectiveの指標再監査: 誤差床・(N,k)の一致を適用し、rχ²を現実レンジへ。本文に「診断用」注記を追記。

## 参考
- 外部公開URL（SSL終端）: Agent Gate 経由のproxy。BASE例: `https://agent-gate.s21g.com/moon/<token>/@localhost:3131`
