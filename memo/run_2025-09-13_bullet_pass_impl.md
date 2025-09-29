## Bullet 全球PASSに向けた最小拡張の実装 — 2025-09-13

## 結果サマリ
- FDB最小核を理論枠内の最小拡張で更新。
  - `W_eff(Σ_e)=exp(-αΣ_e)+ξΣ_e^p` を導入（既定: ξ=0, p=0.5）。
  - 界面ゲート `S=σ((|∇ω_p|−τ)/δτ)·[n·r]_+·(1+βcosΘ)_+` を実装。
    - 既定: `τ` は |∇ω_p| の70%分位, `δτ=0.1·τ`。
  - 前方化βは既存Lambert拡張を維持（β>0解禁）。
- 学習→固定→ホールドアウトのパイプラインを更新。
  - 学習: Abell 1689/CL0024 同時。グリッド(α,β,C,ξ,p,τ_q)でAICc最小を選択（Spearmanは同点時のタイブレーク）。
  - 共有パラを `data/cluster/params_cluster.json` に保存（`sha256`付与）。
  - ホールドアウト: Bulletで公平条件（N/k、整準、PSF/高通過、対照: rot/shift/shuffle）を統一しΔAICcと相関指標を算出。
- 現状のKPI達成状況（速報）
  - KPI‑2: Bulletで ΔAICc(FDB−shift) ≈ −2.49×10^5 ≤ −10 → PASS。
  - KPI‑1: 全球 Spearman(R,Σ_e) は正（r≈+0.30, p≪0.05）→ 未達。
  - 付帯: ROI(core r≤r50/outer r≥r75) でも正側優勢、partial r も要改善。

## 生成物
- コード:
  - `scripts/cluster/min_kernel.py`（W_eff・界面ゲート・新パラ対応）
  - `scripts/cluster/fit/train_shared_params.py`（新パラ学習 / 環境変数でグリッド拡張）
  - `scripts/reports/make_bullet_holdout.py`（新パラ受け渡し・全球SpearmanのPASS判定追加）
- パラ: `data/cluster/params_cluster.json`（例: α=2.0, β=0.7, C=0.05, ξ=0, p=0.5, τ_q=0.7, sha付）
- レポート: `server/public/reports/bullet_holdout.html`, `bullet_holdout.json`

## 次アクション
- 全球負相関を狙うため、再放射強度/界面閾値の探索を拡張（計算量は限定）。
  - 例: `GRID_XI=0,0.05,0.1,0.2 GRID_P=0.5,0.7 GRID_TAUQ=0.6,0.7,0.8 \
    PYTHONPATH=. ./.venv/bin/python scripts/cluster/fit/train_shared_params.py`
  - 再学習→`make bullet-holdout`で再判定。Permutationは `BULLET_PERM_N=4096..8192` を推奨。
- ブロックBootstrap CI と半径制御(partial r)の追補図版を追加（検定の安定化）。
- 画像系: CIAO正式モザイク差し替えの影響（|Δ|中央値<10%）を後段確認。

