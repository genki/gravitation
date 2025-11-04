# State of the Art（SOTA）
Last updated: 2025-11-04 15:52 +0900

注: 本リポジトリで用いる FDB は Future Decoherence Bias の略称です。
ULM（旧称 ULW‑EM）の将来デコヒーレンスに起因する見かけの引力（見かけの加速度）を指し、FDB3 は
その3パラメータ型モデル、FDBL は3D拡張型モデルを表します。


本ページはSPARC銀河に対するGR(noDM)とFDB3の比較結果を集約し、
SOTAを可視化するダッシュボード的サマリです。図は`make all`または
`make figs`で再生成され、本ページには`make docs`で反映されます。

## 最新状況（2025-11-04）

- **FULL再実行**: 2025-11-03 13:40 JST に AbellS1063 a4_full（band=8–16, block_pix=6, perm=10, early-stop）を完了。`check_preproc_repro.py` の整備により FAST↔FULL の前処理差分は `fast_mode` のみ、`S_shadow`/Spearman 差分は 0.0000。MACSJ0416 も同条件で再実行済み（aligned JSON を `holdout_runs/MACSJ0416_ps1p5_hp6_{fast,full}_aligned.json` に保存）。
- **Gate逐次Permutation**: ジョブディスパッチャ（`scripts/jobs/dispatch_bg.sh`）経由で Gate 2.0 FULL を再開。影／残差 permutation は 5000 ステップの途中から再開し、直近の run では残り十数秒で完了。今後は perm=2000→5000 の段階的停止ルール（CI上限U≤0.05 / 下限L≥0.35）を適用し PASS率回復を狙う。
- **KPIモニタリング**: `make kpi-weekly` で `gate_kpi.json`（dispatch 316, FULL PASS率0%, 平均perm AbellS1063 ≈707 / MACSJ0416 ≈790）と `nbody_kpi.json`（missing_required=0）を同時更新。anytime-fail ログは依然 0 件で推移。
- **N体HTTP公開**: `plot_s0_diagnostics.py` の改修により `m_mode_power` から `m2_heatmap.png` を生成できるようにし、S0 ラン（dev_alpha/dev_dir_test/dev_test/dev_test_qalog/mid_combo）の欠品を解消。`metrics.csv` も DoD スキーマで整備し、SOTA から HTTP 200 で取得可能。
- **次手優先度**: Gate 推薦上位70%の FULL PASS率≥40% 達成に向けて perm=2000→5000 機構を本稼働、FAST 側は膝 + Skeleton 指標の上位設定追加。N体は S0 スイープの Gate 条件（dA2/dt>0 連続＋pitch判定）を実装し、B-3 の Gate 昇格へ進む。WL 正式版は n(z)/m/IA/TATT の整合と ΔAICc|≤10 を週次に確認する。

## 統計サマリ

![Improvement Histogram](img/sota_improvement_hist.png)

![redχ² Scatter](img/sota_redchi2_scatter.png)

- 改善倍率(中央値): ×19.64（175銀河, 2025-08-31）
- 共同フィット(共有a,b,c): 合成redχ² GR=195.82 → FDB3=25.90（×7.56）

## 代表VR図

![VR Panel](img/sota_vr_panel.png)

### 共有パラメータによる比較

- DDO154（共有a,b,c）

![DDO154 shared](img/compare_fit_DDO154_shared.png)

- DDO161（共有a,b,c）

![DDO161 shared](img/compare_fit_DDO161_shared.png)

## 反映・更新手順

1. 解析と図生成
   - `make all`（取得→当てはめ→共同フィット→図出力）
   - 図のみ更新は `make figs`
2. ドキュメントへ反映
   - `make docs`（docs/imgへ同期し本ページに反映）
3. LaTeX論文へ反映（任意）
   - `bash scripts/sync_figs_to_paper.sh`
   - `make -C paper pdf`（LaTeX環境がある場合）

---

注意: 図は`assets/figures`がソースで、`docs/img`と`paper/figures`に
同期されます。詳細は`Makefile`と`scripts/`を参照してください。

## バレット・ホールドアウト（1E 0657‑56）再現手順

最新の SOTA 指標では、バレット・ホールドアウトが ΔAICc と方向統計（S_shadow）の
両方で KPI を満たしています。以下の手順で再現してください。

### 1. WLS パラメタの推定（初回のみ）

```sh
python scripts/reports/estimate_wls_params.py --out config/wls_params.json
```

学習クラスタ（Abell 1689 / CL0024）から `σ0=0.6`, `c=0.6`, `trim_frac=0.09`,
`trim_iter=2`, `block_pix=4`, `N_eff=487` を推定し、全モデルで共有する σ マップを生成します。

### 2. 環境変数（界面マスクとPermutation）の固定

```sh
export BULLET_PERM_N=10000
export BULLET_SHADOW_PERM_MIN=10000
export BULLET_EDGE_COUNT=4096
export BULLET_SHADOW_SE_Q=0.7
export BULLET_SHADOW_RR_Q=0.7
export BULLET_SHADOW_BLOCK=32
```

### 3. ホールドアウト再計算

```sh
python scripts/reports/make_bullet_holdout.py \
  --beta-sweep 0.4,0.6,0.8,1.0 \
  --sigma-psf 1.2,1.5,1.8 \
  --sigma-highpass 6,8,10
```

固定条件（SOTA準拠）:

- **PSF σ = 1.80 pix**, **高通過 σ = 8 pix**（最良点）
- **マスク = Σ_e 上位 75%**, **ROI = core(r≤r50) / outer(r≥r75)**
- **整準 = FFT相互相関 → Lanczos3**, 整準結果 (dy,dx) = (27, 48)
- **wrap(dy,dx) = (12, −7)**、**rng = 42**
- **Gate**: τ_q = 0.75, δ_τ/τ = 0.15, s_gate = 24, gate_sigmas = [2,4,8]
- **W_eff**: Σ_e 変換 = rank, q_knee = 0.9, ξ_sat = 0.5（shared_params sha: f4fd655f）
- **誤差モデル**: σ²(x,y) = σ0² + c·Σ_e(x,y) with σ0 = 0.6, c = 0.6
- **(N, N_eff, block_pix) = (7396, 487, 4)**
- **AICc の自由度 k**: FDB/rot/shift/shuffle = 2 / 1 / 2 / 0

### 4. SOTA サマリの更新

```sh
python scripts/reports/update_sota.py
```

`server/public/reports/sota.json` / `sota.html` に最新結果が反映されます。

### 5. 期待される指標（2025‑09‑17 時点）

- ΔAICc(FDB−shift) ≈ **−3.364×10⁹**（rot/shuffle も負側）
- S_shadow(global) ≈ **0.3085**、Permutation(one-sided >0) p ≈ **0.0476**
- Rayleigh p ≈ 3.8×10⁻²⁷、V-test p ≈ 1.4×10⁻²⁶
- `server/public/reports/bullet_holdout.json/.html` 内の AICc 表に (N, N_eff, k, χ², rχ²)
  が恒常掲示され、影整合カードに Q2 / Rayleigh / V-test が表示されます。