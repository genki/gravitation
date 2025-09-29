# SOTA追加指示(2025-09-06) 対応ログ（第1弾）

## 結果サマリ
- β（前方化）の配線: surfaceモードのラジアル近似を実装（`radial_forwardize`）。既定OFFで、自由度には不算入。
- NGC3198: 外縁1/r²に外挙動域の線形近似（傾き表示）を重ね描き。MOND/GR+DMの脚注強化。固定εの採用を明示。
- 共有JSONの指紋(sha256短縮)をSOTA/ベンチ両方に表示。
- CV: 重複fold行の除外とrχ²注記、監査カードを追加。
- SOTA: 監査OKバッジ、二層モデル図解の常設、W=1（環境依存OFF）明記。
- Prospective: AICc/(N,k)/rχ²を併記し、前提を明示。

## 生成物
- コード: `src/fdb/angle_kernels.py(radial_forwardize)`, `scripts/compare_fit_multi.py`（β配線）, `tests/test_beta_forward.py`
- ページ: `server/public/reports/bench_ngc3198.html`, `server/public/state_of_the_art/index.html`, `server/public/reports/cv_shared_summary.html`, `server/public/reports/prospective.html`

## 次アクション
- βの角度核（Lambert→前方化）の完全配線（ULW/Σで角度依存を反映）と人工面源のユニテスト。
- HALOGAS外挙動半径の厳密化（データがあれば自動選択）と注釈の強化。
- 通知ログ/used_ids.csvのリンク健全化をCI/Lintで常時検証。欠落時は非表示。
