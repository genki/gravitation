## SOTA評価(2025-09-13) 指示反映とページ強化 — 2025-09-13

## 結果サマリ
- 指示書（単一MD版）A–Dに沿ってホールドアウト評価系を強化。
  - A: `W_eff=exp(-αΣ_e)+ξΣ_e^p`・界面ゲートS・β>0は既実装を維持（学習/固定は既レール）。
  - B: 相関検定を拡充。Permutationはn可変（≥5000推奨）に加え、空間ブロックBootstrap CIを追加（JSONに`bootstrap:{n,ci95,block_pix}`）。
  - C: AICc表を恒常化し、(N,k)とχ²/rχ²を同一表で提示。処理条件の脚注も明示を拡充。
  - 図版: κ_FDBパネルに加え、κ_tot=κ_GR+κ_FDB と κ_obs の重畳・差分（R_tot）を追加（可視化のみ）。
- レポート/JSONは `server/public/reports/bullet_holdout.html` / `.../bullet_holdout.json` に反映。

## 生成物
- コード更新: `scripts/reports/make_bullet_holdout.py`（κ_tot図、χ²/rχ²算出、AICc表、Bootstrap CI）
- レポート更新: `bullet_holdout.html`（AICc+(N,k)+rχ² 表、κ_tot 図、Permutation/Bootstrap情報追記）

## 次アクション
- KPI‑A 達成に向けたモデル側の継続（ξ,p,τ_q,β の制約付き探索）と、partial r を主判定に掲示強化。
- 監査強化: ページ脚注に PSF/高通過/マスク/ROI/整準rng の固定表示を追加整備。
- D項: 銀河/ICLピーク座標（任意）の登録と環境ログ（ciaover/lenstool）の収集→脚注掲示。

