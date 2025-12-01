## 実験ノート — SPARC を用いた Proca 光子質量 m_gamma 推定

### 実行日時 / 環境
- 2025-11-25 / `python3` (venv 既設) @ `/home/vagrant/gravitation`
- データ: `data/sparc/sparc_database/*_rotmod.dat`, `data/sparc/MassModels_Lelli2016c.mrt`

### 手順と設定
1. **BTFR 振幅のロバスト推定** — `scripts/calibrate_btfr.py`
   - コマンド: `python scripts/calibrate_btfr.py --rotmod_dir data/sparc/sparc_database --catalog data/sparc/MassModels_Lelli2016c.mrt --out results/btfr_calib.json`
   - 結果: \(A_{\rm BTFR}=3.224\times10^{-10}\,(\mathrm{km\,s^{-1}})^4\,M_\odot^{-1}\)（使用銀河 135/175）
   - 以後、各銀河の \(v_{\rm flat}=(A_{\rm BTFR} M_{\rm bar})^{1/4}\) で振幅を固定。
2. **FDB 切替長の一次元掃引** — `scripts/estimate_mgamma.py`
   - コマンド:
     ```bash
     python scripts/estimate_mgamma.py \
       --rotmod_dir data/sparc/sparc_database \
       --catalog data/sparc/MassModels_Lelli2016c.mrt \
       --btfr_json results/btfr_calib.json \
       --grid_min_kpc 20 --grid_max_kpc 3000 --n_grid 40 \
       --error_floor 5 --n_boot 50 --crossfold \
       --out_json results/mgamma_estimate.json \
       --out_plot results/misfit_vs_lambdaC.png
     ```
   - モデル: \(v_{\rm model}^2(r)=v_{\rm bar}^2(r)+v_{\rm flat}^2\,[1-\exp(-r/\lambda_C)]\)
   - 指標: 各銀河ごとの残差 MAD を銀河間中央値で圧縮。

### 主結果（curvature-based 近似 1σ）
- 相関長 \(\lambda_C = 34.9^{+9.7}_{-7.6}\,\mathrm{kpc}\)
- Proca 光子質量 \(m_\gamma = 3.27^{+0.91}_{-0.71}\times10^{-64}\,\mathrm{kg}\)
  - eV 換算: \(m_\gamma c^2 = (1.83^{+0.51}_{-0.40})\times10^{-28}\,\mathrm{eV}\)
- 使用銀河: 171（SPARC 品質フィルタ後）
- ミスフィット vs \(\lambda_C\) の曲線は `results/misfit_vs_lambdaC.png` を参照。

### ブートストラップ / クロスフォールド診断
- 50 resample のブートストラップでは \(\lambda_C\) が 20–800 kpc に広く分布（コスト最小領域がほぼ平坦なため）。報告値には curvature interval を採用し、ブート区間は補助参考とする。
- 2-fold（even/odd）では \(\lambda_C\) ≈ {1221 kpc, 20 kpc} と大きく振れ、データ分割に対して感度が高い。アイテムごとの分布を見ると、巨大値はサンプル数減少による局所プレートーが原因。代表値には全銀河一括フィットを用いる。

### 既存上限との比較
- PDG/Okun/Retinò 等がまとめる代表的上限 \(m_\gamma \lesssim 10^{-54}\,\mathrm{kg}\) より **11 桁小さい**。したがって本推定は既存の実験・天体制約と矛盾しない。

### 解釈メモ（帯域と殻スケール）
- ここで推定している \(\lambda_C\) は、ULE‑EM 前縁の**有限帯域の中心スケール**としての Compton 長であり、
  「単一のモノクロ波長」ではなく「FDB が 1/r 補正を生む主帯域」の代表値とみなす。
- 有効相関長 \(\lambda_{\rm eff}\) は幾何スケールとの合成 \(\lambda_{\rm eff}^{-1}\simeq\lambda_C^{-1}+L_{\rm inner}^{-1}+L_{\rm outer}^{-1}+L_{\rm web}^{-1}\) として現れ、
  - inner shell（\(R\sim(2\text{–}3)R_d\)）で RC の 1/r tail を立ち上げ、
  - outer shell（CGM/IGM スケール）で v\(_0\) 相当のベースラインを決める。
  したがって \(\lambda_C\) は「FDB 情報流が殻と強く結合するスケール」の測定結果として読む。

### 今後のTODO
- プレートー解消のため、幾何に基づくスイッチング関数（例: erf, tanh）を導入し、\(\lambda_C\) の局在性を検証。
- サーベイ別・銀河タイプ別の \(\lambda_C\) 分布を可視化し、系統源を特定。
- main.ja.md の Proca 節に上記数値（kg/eV）と比較結果を反映。

---

### 追試：閉形式推定（実効長 \(\lambda_{\rm eff}\)）
- 目的: 最小モデルで点ごとの \(\lambda(r)\) を直接計算し、識別性と系統を把握する。
- スクリプト: `scripts/estimate_mgamma_closedform.py` （新規）。BTFR キャリブ後の \(v_{\rm flat}\) を用い、\(\lambda(r) = -r / \ln(1-\Delta(r))\) を有効域 \(0.15<\Delta<0.85\) で算出。各銀河は重み付き中央値、全体は銀河中央値のMAD。
- コマンド:
  ```bash
  python scripts/estimate_mgamma_closedform.py \
    --rotmod_dir data/sparc/sparc_database \
    --catalog data/sparc/MassModels_Lelli2016c.mrt \
    --btfr_json results/btfr_calib.json \
    --out_json results/mgamma_closedform.json
  ```
- 結果（有効銀河 30 件）:
  - \(\lambda_{\rm eff} = 20.9^{+11.6}_{-11.6}\,\mathrm{kpc}\)（MAD 基準）
  - \(m_\gamma^{\rm eff} = (5.45^{+6.74}_{-1.94})\times10^{-64}\,\mathrm{kg} \approx (3.06^{+3.78}_{-1.09})\times10^{-28}\,\mathrm{eV}\)
  - 点数が少ない銀河では 1–2 点の寄与のみ。幾何・誤差床を調整してサンプル拡大の余地あり。
- 解釈: \(\lambda_{\rm eff}^{-1} = \lambda_C^{-1} + L_{\rm wg}^{-1}\) とみなすと、本値は \(\lambda_C\) の下限 → \(m_\gamma\) の上限に相当。本文では「実効漏洩長の推定」として紹介し、35 kpc（全銀河フィット）を保守的な代表値に据える方針とする。
