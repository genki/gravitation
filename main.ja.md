# 将来決定バイアス (Future Determination Bias; FDB) 解説書

**原著**: Genki Takiuchi  
**日本語版**: Gravitation チーム  
**最終更新**: 2025-11-24  

---

## 0. まえがき

本ドキュメントは、英語論文 “Future Determination Bias as Emergent Gravity: Waveguide Confinement, 1/r Drift, and Instant Validation via Strong-Lensing Ratio Test” を、物理学部卒程度の知識を背景に**自学しやすい形で構造化した日本語版**である。専門的な箇所は丁寧に言い換え、式が出てくるたびに背景を補足している。以下の読者をおもな対象とする。

1. **重力レンズ・銀河回転曲線に興味のある学生**。暗黒物質を前提としない枠組みを学びたい人。  
2. **情報流に基づく重力描像に関心がある研究者**。英語原文を読む前のイントロとして。  
3. **再現実験を行いたい開発者**。リポジトリ構造とスクリプトの使い方も含む。  

英語版と章構成を対応させつつ、「なぜその式になるのか」「測定手順はどうなっているか」を詳細に説明し、紙幅制限なしで背景解説を盛り込んでいる。

---

## 1. 背景: なぜ FDB を導入するのか

### 1.1 ΛCDM の長所と短所

- **長所**: 宇宙マイクロ波背景、銀河団分布、バリオン音響振動など、大局的な観測とよく合う。  
- **短所 (銀河スケール)**:  
  1. 平坦回転曲線 (外縁で速度が一定)。  
  2. バリオン Tully–Fisher 関係 (BTFR) の非常に小さな散布 (<0.1 dex)。  
  3. 強重力レンズで得られる質量と運動学的質量のズレ。  

ΛCDM では「ハロー濃度」「異方性」「サブハロー配置」など銀河ごとに別パラメータを調整する必要があり、観測的に“即時で検証”する手段がない。

### 1.2 既存の代替案

- **MOND**: 低加速度領域で Newton 則を修正するが、閾値 \(a_0\) や外場効果など複数の入力が要る。  
- **Emergent Gravity**: エントロピーや情報から重力を導く理論（例: Verlinde 2017）。BTFR を再現するが、強レンズとの接続や即時検定は提示されていない。  

### 1.3 FDB が狙うもの

Future Determination Bias (FDB) は、**情報フラックス**を用いたゼロ自由度の等式を中心に構成される:

- **理論定数**: 強レンズでは 
  \[
  R \equiv \frac{\theta_E' c^2}{2\pi v_c^2} = 1,
  \]
  であり、ここにはデータごとの自由パラメータは存在しない。  
- **観測的価値**: 比を計算して中央値・散布を見るだけで合否が分かる。MCMC やハイパワー計算が不要。  
- **銀河スケールへの波及**: 情報流の幾何が 1/r 力を生み、BTFR と平坦回転曲線を同時に説明する。

---

## 2. Proca 電磁場とプラズマ

### 2.1 Proca 場の基本

Maxwell 方程式にフォトン質量項を加えた理論で、ラグランジアンは
\[
\mathcal{L} = -\frac{1}{4}F_{\mu\nu}F^{\mu\nu} + \frac{1}{2}\mu_\gamma^2 A_\mu A^\mu - J_\mu A^\mu,
\]
となる。ここで \(\mu_\gamma = m_\gamma c/\hbar\) はフォトン質量を表す。質量を持つ場合、静電ポテンシャルは Yukawa 型 \(\propto e^{-r/\lambda_C}/r\) になり、\(\lambda_C = \hbar/(m_\gamma c)\) が Compton 長さである。

### 2.2 プラズマ中の波動

電子密度 \(n_e\) を持つプラズマにおける分散関係は
\[
k^2(\omega) = \frac{1}{c^2}\left[\omega^2 - \omega_p^2(n_e) - \mu_\gamma^2 c^4/\hbar^2\right],
\]
で記述される。ここで \(\omega_p^2 = n_e e^2/(\varepsilon_0 m_e)\) はプラズマ周波数。 \(k^2>0\) なら伝搬、<0 なら指数減衰 (エバネッセント)。

- **ボイド側 (低密度)**: 低周波でも \(k^2>0\) が可能。  
- **銀河側 (高密度)**: 同じ周波数で \(k^2<0\) となり、界面に沿った導波が起こり得る。  

FDB はこの差を利用して“波導”を実現する。

---

## 3. 界面波導と 1/r フラックス

### 3.1 波導条件

界面を伝わる TE モードの反射係数は
\[
R = \frac{k_{z,1} - k_{z,2}}{k_{z,1} + k_{z,2}}, \quad
k_{z,i} = \sqrt{\frac{\omega^2 - \omega_{p,i}^2 - \mu_\gamma^2 c^2}{c^2} - k_\parallel^2}.
\]

ここで 1 をボイド側、2 を銀河側とすると、\(k_{z,1}^2>0\)・\(k_{z,2}^2 < 0\) となる周波数帯で高反射 (|R| 1) が実現する。実効遮蔽長 \(\delta = 1/|\mathrm{Im}\,k_{z,2}|\) は 10–30 kpc 程度で、銀河スケールより短い。

### 3.2 幾何学的帰結

波が界面に沿って伝わると、球面幾何から円筒幾何に変わり、エネルギーフラックス保存は
\[
2\pi r I(r) = \text{const} \Rightarrow I(r) \propto \frac{1}{r}
\]
となる。情報フラックス \(I(r)\) が 1/r で減衰すると、後述する確率ドリフトを通じて**有効力も 1/r** になる。

---

## 4. 情報フラックスと確率ドリフト

### 4.1 Lindblad 形式の導入

連続測位を表す Lindblad 方程式
\[
\frac{d\rho}{dt} = -\frac{i}{\hbar}[H, \rho] + \frac{\Gamma}{2}\left(2L\rho L^\dagger - \{L^\dagger L, \rho\}\right)
\]
を Wigner 表現で展開すると、Fokker–Planck 方程式
\[
\frac{\partial f}{\partial t} = -\partial_x (A f) + \frac{1}{2}\partial_x^2(D f)
\]
に写る。ここでドリフト係数 \(A\) は \(\Gamma(x)\) の勾配に比例する。界面で \(\Gamma \propto I(r) \propto 1/r\) ならば \(A \propto -1/r\)、つまり有効力も 1/r になる。

### 4.2 有効ポテンシャル

FDB の有効ポテンシャルを
\[
\Phi_{\rm FDB}(r) = v_c^2 \ln r
\]
とすると、Newton 力学の等温球と同形になり、**強重力レンズの公式とも一致**する。

---

## 5. 観測検証

<a id="sec6"></a>

### 5.1 強レンズ一次検定 (H1)

- **比の定義**: \(R \equiv \theta_E' c^2 / (2\pi v_c^2)\)（\(v_c = \sqrt{2}\sigma_{\rm SIS}\)）。
- **計算手順**:
  1. \(\theta_E\) を弧度法に変換し、角径距離比 \(D_s/D_{ls}\) で正規化。
  2. 速度分散は \(\sigma_{\rm SIS}\) を優先。無い場合は \(\sigma_e = \sigma_{\rm ap}(R_{\rm ap}/R_e)^{-0.066}\)。
  3. 各レンズで \(R_i\) を計算し、\(m_R = \mathrm{median}(\log_{10} R_i)\)、\(s_R = 1.4826\,\mathrm{MAD}\) を求める。
- **PASS 窓**: \(|m_R|\le 0.03\) dex かつ \(s_R\le 0.10\) dex。
- **結果**: SDSS および BELLS は PASS。BOSS は \(m_R=+0.0846\) dex, \(s_R=0.1497\) dex で補助 QC 扱い。

### 5.2 回転曲線 (SPARC)

- **データ**: SPARC MRT (品質=1、傾斜>30°, R_out>3R_d)。
- **モデル**: FDB は一定 \(V_0\)、NFW は \(c=10\) 固定 (k=1) とし、\(\Delta\mathrm{AICc}=\mathrm{AICc}_{\rm FDB}-\mathrm{AICc}_{\rm NFW}\) を評価。
- **感度試験**: 誤差床 5/3/2 km s⁻¹ と M/L が 0.5/0.7 または二値トグル。full-radius では中央値が正 (FDB 不利) になるが、outer-only (r≥2.5R_d) では負 (FDB 有利) になる。

### 5.3 BTFR

- **プロット法**: \(x = \log_{10} M_{\rm bar}[M_\odot]\)、\(y = \log_{10} v_{\rm flat}^4[(\mathrm{km\,s^{-1}})^4]\)。傾き 1 を固定し、切片 \(b = \mathrm{median}(y-x) = -1.69\) dex。
- **図**: 実線は \(y = x + b\)、破線は ±0.1 dex。散布の小ささが FDB の 1/r ドリフトと整合。

---

## 6. 再現性ガイド

1. リポジトリをクローン: `git clone https://github.com/genki/gravitation` (commit `32304c6` で検証)。
2. 依存ソフト: Pandoc + XeLaTeX。Linux 環境なら `make pdf` で `build/main.pdf` が再生成される。
3. H1 比テスト: `src/analysis/h1_ratio_test.py` を実行すると Table 1 と Figure 2 が再計算される。
4. SPARC 解析: `src/scripts/sparc_sweep.py` が Table 2 と BTFR 図を再出力。入力は `data/sparc/` 以下の MRT ファイル。
5. すべての中間結果 (CSV) は `build/` に保存される。

---

## 7. 制限と今後

- **等価原理**: \(L_0\) を環境依存と見ることで、試験体質量に依存しない。太陽系では情報勾配が小さく追加力は無視できる。
- **強重力**: 近接ブラックホール周りでは波導条件が破れ、3D 逆二乗に戻る。GR との厳密整合は今後の課題。
- **決定的テスト**: 同じ銀河で \(\theta_E\) と \(v_c\) を同時測定し、\(R=1\) から 0.03 dex 以上ずれれば FDB は即棄却できる。

---

<a id="refs-ja"></a>
## 参考文献（抄訳）

- McGaugh, Lelli & Schombert 2016, AJ, 152, 157 — SPARC カタログ。  
- Narayan & Bartelmann 1997 — SIS レンズ公式の古典的レビュー。  
- Sugiura 1978, Hurvich & Tsai 1989 — AICc の導入論文。  
- Shu et al. 2016/2017 — BELLS, S4TM のレンズカタログ。  
- Particle Data Group 2024 — フォトン質量上限。  
- そのほか英語版 `refs.bib` に列挙された文献。

---

<a id="appendixA"></a>
## 付録 A: 用語と式まとめ

| 用語 | 意味 |
|---|---|
| ULE-EM | 超低エネルギーの Proca 電磁場。フォトン質量は \(m_\gamma\sim3.9\times10^{-65}\,\mathrm{kg}\)。|
| \(v_c\) | 円速度。観測される 1 次元速度分散 \(\sigma\) から \(v_c=\sqrt{2}\sigma\)。|
| H1 比 | \(R=\theta_E' c^2/(2\pi v_c^2)\)。SIS と完全一致する定数関係。|
| PASS 窓 | \(|m_R|\le0.03\) dex, \(s_R\le0.10\) dex。|
| ΔAICc | \(\mathrm{AICc}_{\rm FDB}-\mathrm{AICc}_{\rm NFW}\)。負なら FDB 有利。|

数式の詳細は英語版 (main.md) および `appendix_f_h1.md` を参照。

---

## データとコードの公開

- GitHub: <https://github.com/genki/gravitation>  
- 強レンズ: `src/analysis/h1_ratio_test.py` ＋ `data/strong_lensing/`  
- SPARC: `src/analysis/sparc_fit_light.py`, `src/scripts/sparc_sweep.py`, 入力は `data/sparc/`  
- 中間結果: `build/` ディレクトリ  
- ビルド: `make pdf` で `build/main.pdf` と `build/main.ja.pdf`（Pandoc で `main.ja.md` を指定）もし生成可能。

---

以上。
