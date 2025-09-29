# 2025-09-18 パラメタ記号統一（θ_opt/θ_if/θ_aniso）

## 結果サマリ
- Bullet 指示書 `memo/bullet_exec.md` を v2 記号（τ₀, ω₀, η, g）へ移行し、旧表記との換算式を冒頭に追記。Σ_e 再放射式や β グリッドを新記号にあわせて更新した。
- `scripts/build_state_of_the_art.py` を再実行し、公開版 `server/public/state_of_the_art/bullet_exec.html` にも新記号と換算注記が反映された。

## 生成物
- 更新: `memo/bullet_exec.md`
- 更新: `server/public/state_of_the_art/bullet_exec.html`

## 次アクション
- 旧記号を使用しているクラスタ用スクリプト（train_shared_params など）にも新記号レイヤーを設け、UI 表示とログが v2 記号で統一されるよう順次改修する。
