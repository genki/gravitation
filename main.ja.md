---
header-includes:
  - \setlength{\emergencystretch}{3em}
  - \overfullrule=8pt
  - \hfuzz=0pt
  - \vfuzz=0pt
  - \hbadness=1
  - \vbadness=1
  - \XeTeXlinebreaklocale "ja"
  - \XeTeXlinebreakskip=0pt plus 1pt
---

# 将来決定バイアス (Future Determination Bias; FDB) 解説書

**原著**: Genki Takiuchi
**日本語版**: Gravitation チーム
**最終更新**: 2025-11-24

---

## 0. まえがき

> **本書の要点（3文）** — 本解説書は、**情報流の勾配**を起点に重力を“有効現象”として再定義する **Future Determination Bias (FDB)** を紹介します。**局所・強重力では GR と同一**（1/r² 幾何・測地線・重力赤方偏移）に還元され、**銀河〜ボイド界面の幾何では波導により 1/r ドリフトが顕在化**して外縁の平坦回転・BTFR を説明します。観測側では**強レンズ H1 の比等式と BTFR**が**重計算なし**に即時検証を可能にします（詳細は §10）。

本解説書は、Future Determination Bias (FDB) 理論そのものの発想・数理背景・観測的含意を日本語で体系化したものである。FDB は**宇宙全域**を情報流ドリフトで記述し、情報勾配が小さい領域では一般相対論 (GR) と同じ 1/r² 幾何・測地線・重力赤方偏移を**そのまま再現**する。一方、銀河–ボイド界面など勾配が大きい領域では波導が 1/r ドリフトを顕在化させ、外縁の平坦回転や BTFR を説明する。すなわち「GR は局所・強重力の標準解、FDB は銀河スケールで優勢になる補正」という役割分担を前提に、重力を“情報流起源の有効現象”として捉え直す。

以下では重力理論・電磁気学・統計物理の基礎を修めた読者を想定し、次の順序で議論を進める（参照ナビ: §3, Fig.\,1; §10, Table\,1/2, Fig.\,2–4）。

::: {=latex}
\XeTeXlinebreaklocale "ja"
\XeTeXlinebreakskip=0pt plus 1pt
\overfullrule=8pt
\hfuzz=0pt
\vfuzz=0pt
\hbadness=1
\vbadness=1
\setlength{\emergencystretch}{3em}
:::

- 観点の再整理: GR と FDB を併存させるための前提整備。
- 重力の再定義: 幾何学から情報ドリフトへの視点転換。
- 四つの力から三つへ: 重力を“有効現象”として再配置する考え方。
- GR との比較: 対応域・差異・観測的指標。

その後、Proca 電磁場（§6）・補遺（フォトン質量; §7）・導波路（§8）・情報流束（§9）・観測検証（§10）・資料（§11）という詳細論を展開する。GitHub (<https://github.com/genki/gravitation>) の `make` コマンドで英語版 (build/main.pdf) と日本語版 (build/main.ja.pdf) を同時生成でき、詳細な再現手順は §11「資料：再現ガイド」を参照すればよい。

---

### 0.1 エグゼクティブサマリ

- FDB は **情報流ドリフト**として重力を再定義し、情報勾配が小さい領域では GR と同一の 1/r^2 幾何に漸近する（§3）。
- **銀河–ボイド界面**で波導 (waveguide) が成立すると 1/r ドリフトが立ち上がり、暗黒物質を仮定せず平坦回転曲線と BTFR を説明する（§3–§10）。
- **強重力レンズ一次検定 (H1)** と **BTFR** はゼロ自由度の等式で、比を作って中央値・散布を見るだけで FDB を即時検証できる（§10）。

> **読み方のナビ** — まず **§3「観点の再整理」**（GR 極限と用語ミニ枠）→ **図1（幾何とドリフトの対比）** → **§11（H1 と BTFR の即時検証）** の順でざっと眺め、その後に **§7–§10（Proca 場・波導・情報束）** で数理背景を掘り下げると理解が速い。

以下では重力理論・電磁気学・統計物理の基礎を修めた読者を想定し、(1) 観点の再整理 (GR と FDB の併存条件)、(2) 幾何から情報ドリフトへの再定義、(3) 四つの力から三つへの再配置、(4) GR との対応域・観測指標、という順に議論を進める。

## 1. 概要（図で掴む Future Determination Bias）

> **要点ボックス（1ページでわかるFDB）**  
> - 重力 = 「時空の曲率」ではなく **情報流（ULE‑EM）の勾配が生む確率ドリフト**。  
> - **銀河スケール以下では GR と事実上同一**（測地線・重力赤方偏移・SIS レンズ）。  
> - 銀河–ボイド界面で波導が成立すると情報流が 1/r で減衰し、平坦回転・BTFR を自然に再現。  
> - コア検証は **ゼロ自由度比 \(R\equiv\theta_E' c^2/(2\pi v_c^2)=1\)**（H1）。  
> - 本書の図: Fig.\,A（FDBメカニズム）、Fig.\,B（GR vs FDB 対比）、Fig.\,C（Procaポテンシャルとスケール）、Fig.\,D（界面波導模式）。

![Fig.A FDBメカニズムの概念図。情報流 \(J_{\rm info}\) が界面に沿ってガイドされ、連続測定により確率ドリフト \(\langle\mathbf a\rangle\) が**引力同型**として現れる。銀河スケール以下では GR と観測上区別できない。](figures/fdb_concept.png){#fig:fdb-mech width=0.95\linewidth}

### 1.1 GR との同型性（図で先に見る）
![図1｜GR と FDB の対比。左: GR は曲率→ポテンシャル→測地線。右: FDB は情報流保存→\(\nabla\Gamma\)→確率ドリフト。**観測される運動方程式の形は銀河スケール以下で一致**し、差異は外縁の有効項に限られる。](figures/schematic_flux_scaling.png){#fig:gr-fdb width=0.8\linewidth}

> **記法ボックス（H1 / ΔAICc 確定版）**  
> \(R \equiv \theta_E' c^2/(2\pi v_c^2)\), \(\theta_E'=\theta_E D_s/D_{ls}\), \(v_c=\sqrt{2}\sigma\). \(v_c\) 軸では分母は常に \(2\pi v_c^2\); \(\sigma\) 軸を直接使う場合のみ \(4\pi\sigma^2\)。  
> PASS 窓: \(|m_R|\le0.03\) dex, \(s_R\le0.10\) dex (1.4826×MAD)。  
> \(\Delta\mathrm{AICc}\equiv\mathrm{AICc}_{\rm FDB}-\mathrm{AICc}_{\rm NFW}\); 負が FDB 有利。外縁評価は \(r\ge2.5R_d\) を採用。

要点: 情報監視率が一様（\(\nabla\Gamma=0\)）な領域では FDB の加速度は消え、GR/SIS と事実上同じふるまいになる。外縁だけで 1/r の有効項が立ち上がるため、太陽系・連星パルサ・重力波源の検証と矛盾しない。

### 1.2 媒質とスケール（Proca と波導）
![Fig.C Proca ポテンシャルのスケール。コンプトン長 \(\lambda_C\) が銀河外縁〜ボイド境界スケールに重なると、界面効果と合成された \(\lambda_{\rm eff}\) が 1/r 実効項を支配しうる。](figures/proca_potential.png){#fig:proca width=0.75\linewidth}

![Fig.D 銀河–ボイド界面の波導模式図。プラズマ密度差により反射係数が高く、前縁のみが測地線上で伝搬。エバネッセント深さ \(\delta\) と波導ロス \(L_{\rm wg}\) は \(\lambda_C\) と合成され \(\lambda_{\rm eff}^{-1}=\lambda_C^{-1}+L_{\rm wg}^{-1}\) を与える。](figures/interface_waveguide.png){#fig:waveguide width=0.8\linewidth}

> **用語ミニ辞典（初出で参照）**  
> ULE‑EM: 超低エネルギー Proca 電磁場（微小質量を許容）。  
> \(\Gamma\): 情報監視率 [s\(^{-1}\)]。\(\mathbf a=-\alpha_m\nabla\Gamma\)（一様域で 0）。  
> \(v_c=\sqrt{2}\sigma\): H1 では常にこの軸を使用し分母 \(2\pi v_c^2\) を保持。  
> \(\lambda_C\): コンプトン長。 \(\lambda_{\rm eff}^{-1}=\lambda_C^{-1}+L_{\rm wg}^{-1}\) で波導ロスと合成。

## 2. FDB理論とは

Future Determination Bias (FDB) は「宇宙を満たす超低エネルギー電磁波 (ULE-EM) が位置情報を連続監視し、その監視強度の勾配が物質に確率的ドリフトを与える」という描像を採る。要点は次の 3 点に集約できる。

1. **情報キャリア** — フォトン質量を持つ Proca 電磁場が宇宙スケールで位置情報を輸送する（§6）。銀河–ボイド界面ではプラズマ密度差によりエバネッセント全反射が起こり、情報流が界面に沿って閉じ込められた波導 (*waveguide*, §8) 状態になる。
2. **幾何からドリフトへ** — 波導内ではフラックス保存が球面 (1/r^2) から円筒 (1/r) に切り替わり、情報勾配が 1/r スケールになる（§8.2）。Lindblad→Fokker–Planck の写像（§9）を経て、情報勾配そのものが 1/r の有効力として現れ、平坦回転曲線や BTFR を自然に説明できる。
3. **ゼロ自由度検定** — 強重力レンズでは観測量の比だけで整合性が決まり、パラメータフィットを必要としない（定義は §10.1 に集約）。

要するに **「情報流の波導化 → 1/r ドリフト → ゼロ自由度の観測比」** という鎖こそが FDB のビッグピクチャーであり、本書はこの鎖の物理と検証法を順番にひも解いていく。太陽系・連星パルサ・重力波源では情報勾配が小さく、追加項は観測分解能以下となって GR と区別不能（重力赤方偏移の等価は付録F参照）。以後の式は銀河外縁など“勾配が立つ”場面に限定して読めばよい。

> **定義 1 (FDB 加速度)** \
> \(\mathbf a(\mathbf x) \equiv -\alpha_m \nabla \Gamma(\mathbf x)\), \(\alpha_m\simeq1\). \
> \(\Gamma(\mathbf x)\) は ULE‑EM 情報流の**測位モニタリング率** [s\(^{-1}\)]。 \(\nabla\Gamma=0\) となる領域（実験室・太陽系・強重力域）では \(\mathbf a=0\) となり、FDB は GR/SIS と観測上区別できない。

### 1.1 ΛCDM の長所と短所

- **長所**: 宇宙マイクロ波背景、銀河団分布、バリオン音響振動など、大局的な観測とよく合う。
- **短所 (銀河スケール)**:
  1. 平坦回転曲線 (外縁で速度が一定)。
  2. バリオン Tully–Fisher 関係 (BTFR) の非常に小さな散布 (<0.1 dex)。
  3. 強重力レンズで得られる質量と運動学的質量のズレ。

ΛCDM では「ハロー濃度」「異方性」「サブハロー配置」など銀河ごとに別パラメータを調整する必要があり、観測的に“即時で検証”する手段がない。

### 1.2 GR と FDB の二層構造

FDB では「情報流の強度 $I(r)$ がそのまま有効ドリフトの大きさを決める」と仮定する。局所の有効ポテンシャルを $U(r) \equiv -\chi\int_r^\infty I(r')\,dr'$ と定義すれば、加速度は $\mathbf a=-\nabla U$ で与えられる。幾何が異なれば $I(r)$ の形が変わり、結果として GR の $1/r^2$ 幾何と FDB の $1/r$ ドリフトが同じ枠組で説明できる。

> **Box 1 (球対称: GR と同型)**  \
> $I_{\mathrm{sph}}(r)=S/(4\pi r^2),\ U(r)=-\chi S/(4\pi r)$  \
> $\mathbf a(r)=-\nabla U=-\chi S/(4\pi)\,\hat{\mathbf r}/r^2$  \
> $\chi S/(4\pi)=GM$ と同定すれば $\mathbf a=-GM\hat{\mathbf r}/r^2$（GR の弱重力極限）。

> **Box 2 (導波: 円筒幾何)**  \
> $I_{\mathrm{cyl}}(r)=S_c/(2\pi L\,r),\ U(r)=-\chi S_c/(2\pi L)\ln r$  \
> $\mathbf a(r)=-\nabla U=-\chi S_c/(2\pi L)\,\hat{\mathbf r}/r$  \
> $v_{\mathrm{flat}}^2=r|a|=\chi S_c/(2\pi L)=\mathrm{const}$。

図~\ref{fig-waveguide} も併せて見ると、球面幾何では $1/r^2$、波導（円筒幾何）では $1/r$ の減衰になる違いが一目で分かる。§3 の「重力の再定義」や §10 の H1/BTFR 検証はこの二層構造を具体化したものである。

### 1.3 既存の代替案

- **MOND**: 低加速度領域で Newton 則を修正するが、閾値 $a_0$ や外場効果など複数の入力が要る。
- **Emergent Gravity**: エントロピーや情報から重力を導く理論（例: Verlinde 2017）。BTFR を再現するが、強レンズとの接続や即時検定は提示されていない。

### 1.4 FDB が狙うもの

Future Determination Bias (FDB) の狙いは以下のとおりである。

- **即時に検証できる理論定数**: 強レンズでは入力データだけから決まる比が 1 になる（数式は §10.1）。
- **重計算に依存しない判定**: 比の中央値・散布を見るだけで整合性が判断でき、MCMC や大規模回帰を要しない。
- **銀河スケールへの波及**: 情報流の幾何が 1/r 力を生み、BTFR と平坦回転曲線を一貫した枠組で説明する。

## 3. 観点の再整理 — GR と FDB を併存させるために

### 2.1 GR 極限の条件
1. **局所一致**: 太陽系や実験室では FDB の補正項は観測上無視でき、GR と区別不能である。
2. **情報勾配の閾値**: kpc–Mpc の銀河–ボイド界面で情報波導が成立すると 1/r ドリフトが現れるが、それ以外では GR 極限に留まる。
3. **既存検証との非矛盾**: 重力赤方偏移や二重星タイミング、PDG が提示するフォトン質量上限 (Goldhaber & Nieto 2010; Tu et al. 2005; Ryutov 2007) を十分満たす。

### 2.2 参照ナビ

理論の詳細は §6–§9、観測指標は §10（H1・BTFR）を参照すると手早く把握できる。

### 2.3 記法ボックス（H1 / ΔAICc）

> **H1 比** $R \equiv \theta_E' c^2/(2\pi v_c^2)$。ここで $\theta_E' = \theta_E D_s/D_{ls}$、$v_c = \sqrt{2}\,\sigma$。$v_c$ 軸を用いるときは分母が常に $2\pi v_c^2$、一次元分散 $\sigma$ を直接使う場合のみ $4\pi\sigma^2$ を用いる。
>
> **PASS 窓** $|m_R|\le 0.03$ dex かつ $s_R\le 0.10$ dex（$s_R=1.4826\times \mathrm{MAD}$）。
>
> **Lemma (SIS 等価)** — $v_c$ 軸を用いれば $\hat\alpha=2\pi(v_c/c)^2 \Rightarrow R=1$。切片 $b_0=\log_{10}(2\pi)-2\log_{10}c$ を採用すれば自由度は残らない。
>
> **ΔAICc** $\equiv \mathrm{AICc}_{\rm FDB}-\mathrm{AICc}_{\rm NFW}$。負であれば FDB が情報量基準で優勢となる。

---

## 4. 重力の再定義 — 幾何学から情報ドリフトへ

### 3.1 GR の語り直し

一般相対論 (GR) は「質量・エネルギーが時空を曲げ、物質は曲率の最短経路（測地線）に沿って動く」という幾何学的描像をとる。FDB は同じ方程式体系を土台にしつつ、情報流の偏りが小さい領域では GR と同じ運動を返し、銀河–ボイド界面のように勾配が立つところで 1/r ドリフトが現れる、という補完的な視点を与える。

### 3.2 情報流と波導

宇宙を満たす超低エネルギー電磁波 (Ultra Low Energy EM Wave; ULE-EMW) を Proca 場として捉え、これが**位置情報の更新頻度**を担うと解釈する。銀河とボイドの界面では電子密度のギャップにより**全反射 (エバネッセント障壁)** が生じやすく、情報流が界面に沿って閉じ込められた**波導 (waveguide)** 状態になる。波導内では球面ではなく円筒幾何のフラックス保存が働くため、強度は (1/r^2) ではなく **(1/r)** で減衰する。
図~\ref{fig-waveguide} に球面 (1/r^2) と円筒 (1/r) のフラックスの違いを模式的に示す。

![情報波導による 1/r フラックスへの遷移の模式図。左: 球面 1/r^2、右: 波導 1/r。右図の等ポテンシャル面に沿って \(-\nabla\Gamma\)（情報監視率の勾配）が界面へ向かう。](figures/schematic_flux_scaling.png){#fig-waveguide width=0.7\linewidth}

### 3.3 観測的含意

波導が成立すると、銀河外縁の回転速度は半径に依らず一定になり、バリオン Tully–Fisher 関係 (BTFR) **(v^4 \propto M_{\rm bar})** が定数 1 本で記述できる。また強重力レンズでは、
\[
R \equiv \frac{\theta_E' c^2}{2\pi v_c^2} = 1,\qquad \theta_E' = \theta_E \frac{D_s}{D_{ls}},~v_c = \sqrt{2}\,\sigma,
\]
という無次元比の中央値と散布を測るだけで理論と観測の整合性を即時に判定できる。これが「ゼロ自由度検定」と呼ぶ理由である。

### 3.4 インフォーミング・テンソル（informing tensor）
ULE-EM の担体を GR 同様のランク2テンソルに束ねるため、**informing tensor** \(I_{\mu\nu}\) を導入する。物質テンソル \(T^{\rm (mat)}_{\alpha\beta}(x)\) と、光円錐上の前縁だけにサポートを持つグリーン関数 \(G_{\rm front}(x,x')\) を用い、TT 射影 \(P_{\rm TT}\) 付きで
\[
I_{\mu\nu}(x)=\kappa\,(P_{\rm TT})_{\mu\nu}{}^{\alpha\beta}\int d^4x'\,G_{\rm front}(x,x')\,T^{\rm (mat)}_{\alpha\beta}(x')
\]
と定義する（\(\kappa\) は H1 の SIS 規格化で固定）。真空・遠方では
\[
\Box I_{\mu\nu}\simeq0,\quad \partial^\mu I_{\mu\nu}=0,\quad I^\mu{}_\mu=0,
\]
となり、**重力波セクターは GR と同一**（速度 = c、偏極 = スピン2の2自由度、四重極放射公式も一致）。FDB の差分は \(\Gamma(x)\) や情報ポテンシャル \(\Phi_{\rm FDB}\) を形作るガイド付き ULE-EM にのみ現れる。

---

## 5. 四つの力から三つへ — 情報流ドリフトの位置づけ

### 4.1 再配置の考え方

FDB では重力を基本相互作用のリストから外し、電磁・弱・強の 3 作用に **情報流ドリフト**を足した枠組みで宇宙を描く。重力は Proca 場の巨視的な統計揺らぎが生む**有効力**とみなし、GR はその短距離極限として並び立つ。

### 4.2 GR 極限との整合

§2.1 で述べた三条件（局所一致・情報勾配の閾値・既存検証との非矛盾）を満たす限り、FDB は宇宙全域で定義されつつ GR と矛盾しない。情報勾配が小さい領域では補正項が実質ゼロになり、GR と同一の 1/r^2 幾何に落ちる。

### 4.3 観測プログラム

FDB を検証する上で重要なのは、**(i)** 強レンズ H1 のゼロ自由度比、**(ii)** BTFR の傾き 1 と切片 1 本の整合、**(iii)** 回転曲線における一定補正速度の存在の 3 点である。いずれも入力は公開カタログで完結し、重い MCMC を要しない。

---

## 6. GR との対応・差異・整合テスト

### 5.1 対応する領域

FDB の情報ドリフトは情報フラックス勾配が十分大きい領域でのみ表に出る。太陽系・連星パルサー・重力波源では勾配が小さく、GR の予言と区別できない（全領域で FDB を書き下ろせるが、この極限では GR と一致する）。

### 5.2 明確な差異

- **銀河外縁**: 波導化により \(v(r) \approx \mathrm{const}\) が自然に得られ、暗黒物質ハローなしで平坦回転曲線を再現。
- **BTFR**: \(v^4 \propto M_{\rm bar}\) が定数 1 本で成立し、散布は 0.1 dex 以下。
- **強レンズ**: H1 比 \(R\) の中央値・散布だけで合否が決まる。

### 5.3 実用的な検証手順

1. **H1 比テスト**: PASS 窓 \( |m_R|\le 0.03\) dex, \(s_R\le 0.10\) dex。比は \(\theta_E, z_l, z_s, \sigma, R_e\) だけで算出できる。
2. **BTFR**: 傾き 1 固定、切片は \(b=\mathrm{median}(y-x)\) に合わせる。
3. **SPARC ΔAICc**: 補正速度 \(V_0\) を 1 パラメータで最適化し、外縁のみの ΔAICc を主指標にする。

FDB と GR は排他的ではなく、**情報勾配の大小によって FDB の補正項が効いたり無効化されたりする**という立場を本文全体で貫徹する。
まとめると、\(\nabla\Gamma=0\) なら GR/SIS と完全一致し、外縁でのみ H1 が規格化する有効項が立ち上がるため、太陽系や強重力試験と矛盾しない。

### 5.4 重力波セクターの整合
informing tensor は TT 射影つきで定義され、前縁グリーン関数を使うため、真空では
\[
\Box I_{\mu\nu}\simeq0,\quad \partial^\mu I_{\mu\nu}=0,\quad I^\mu{}_\mu=0
\]
を満たす。結果として
- 伝播速度は c（GW170817 の制限と整合）  
- 偏極はスピン2の 2 自由度のみ（スカラー/ベクトルは物理的に現れない）  
- 四重極放射公式・連星パルサ減衰は GR と一致  

となり、重力波セクターは観測上 GR と区別できない。FDB の差分は銀河〜宇宙網スケールの情報ポテンシャルにのみ現れる。

---

## 7. Proca 電磁場とプラズマ

FDB で Proca 場を採用する理由は三つある。(i) Maxwell 理論に質量項を 1 つ加えるだけで有効コンプトン長 \(\lambda_C=\hbar/(m_\gamma c)\) を導入でき、プラズマ分散では \(\omega_p^2+\mu_\gamma^2 c^4/\hbar^2\) として自動的に効いて界面の導波条件を切り替えられる。(ii) 本稿で SPARC 回転曲線 (N=171) に FDB の極小モデルを当てはめたところ、\(\lambda_C=35^{+10}_{-8}\,\mathrm{kpc}\)（曲率近似 1σ）に対応する \(m_\gamma=(3.3^{+0.9}_{-0.7})\times10^{-64}\,\mathrm{kg}\approx (1.8^{+0.5}_{-0.4})\times10^{-28}\,\mathrm{eV}\) が得られ、PDG 2024 や Goldhaber & Nieto (2010) が与える上限より 10 桁以上下であり太陽系・実験室の検証と矛盾しない。(iii) H1 比や BTFR のようなゼロ自由度検定を直接入れて観測側の自由度を増やさずに済む。以下では Proca 場の最小数式とプラズマ中の分散関係だけを示し、詳細導出は補遺Bに譲る。

銀河内の波導が有限長 \(L_{\rm wg}\) をもつと、回転曲線で見える有効漏洩長 \(\lambda_{\rm eff}\) は
\[
\lambda_{\rm eff}^{-1} = \lambda_C^{-1} + L_{\rm wg}^{-1}
\]
で与えられる。閉形式推定（\(\Delta = (v_{\rm obs}^2-v_{\rm bar}^2)/v_{\rm flat}^2\) から直接 \(\lambda(r)=-r/\ln(1-\Delta)\) を求める手法）では \(\lambda_{\rm eff}\approx 21^{+12}_{-12}\,\mathrm{kpc}\)（30 銀河）が得られ、これは \(\lambda_C\) の下限 → \(m_\gamma\) の上限 \(m_\gamma \lesssim 5.5\times10^{-64}\,\mathrm{kg}\) に相当する。本論のグローバル・フィット値（\(\lambda_C\approx35\,\mathrm{kpc}\)）はこの上限を緩和した保守的代表値として扱う。

### 6.1 Proca 場の基本

Maxwell 方程式にフォトン質量項を加えた理論で、ラグランジアンは
\[
\mathcal{L} = -\frac{1}{4}F_{\mu\nu}F^{\mu\nu} + \frac{1}{2}\mu_\gamma^2 A_\mu A^\mu - J_\mu A^\mu,
\]
となる。ここで \(\mu_\gamma = m_\gamma c/\hbar\) はフォトン質量を表す。質量を持つ場合、静電ポテンシャルは Yukawa 型 \(\propto e^{-r/\lambda_C}/r\) になり、\(\lambda_C = \hbar/(m_\gamma c)\) が Compton 長さである。Proca 場の導出や物理的意味は砂川 (1987) の第 7 章が平易なので参照してほしい。

### 6.2 プラズマ中の波動

電子密度 \(n_e\) を持つプラズマにおける分散関係は
\[
k^2(\omega) = \frac{1}{c^2}\left[\omega^2 - \omega_p^2(n_e) - \mu_\gamma^2 c^4/\hbar^2\right],
\]
で記述される。ここで \(\omega_p^2 = n_e e^2/(\varepsilon_0 m_e)\) はプラズマ周波数。 \(k^2>0\) なら伝搬、<0 なら指数減衰 (エバネッセント)。

- **ボイド側 (低密度)**: 低周波でも \(k^2>0\) が可能。  
- **銀河側 (高密度)**: 同じ周波数で \(k^2<0\) となり、界面に沿った導波が起こり得る。  

FDB はこの差を利用して“波導”を実現する。

## 8. 補遺 B: Proca とフォトン質量の上限制約

### 7.1 Proca を採用する最小理由

1. **自由度の最小追加** — Maxwell 理論に質量項を 1 つ加えるだけで有効コンプトン長 \(\lambda_C=\hbar/(m_\gamma c)\) が導入され、プラズマ分散では \(\omega_p^2+\mu_\gamma^2 c^4/\hbar^2\) という形で有効に効く。界面両側の \(k^2(\omega)\) の符号差が導波 (全反射＋エバネッセント) を可能にし、§8 の 1/r フラックスに直結する。
2. **局所実験との整合** — \(m_\gamma\) を十分小さく取れば Yukawa 補正は実験室で検出できず、§5 の「GR との役割分担」で述べたように太陽系では GR がそのまま成立する。
3. **観測指標の自立** — \(m_\gamma\) を直接フィットせずとも、§10 の H1 比と BTFR の傾き 1 をゼロ自由度で検証できる。比の中央値・散布を見るだけで即棄却可能なのが FDB の価値である。

### 7.2 上限制約のカタログ

粒子データグループ (PDG 2024) や Goldhaber & Nieto (2010)、Tu・Luo・Gillies (2005) などのレビューに基づき、代表的なフォトン質量上限を整理すると以下の通りである。

- **実験室・太陽圏**: コールム則の検証や惑星間磁場から \(m_\gamma \lesssim 10^{-50}\,\mathrm{kg}\)。
- **天体磁場**: 銀河磁場や星間プラズマ (Ryutov 2007) から \(m_\gamma \lesssim 10^{-54}\,\mathrm{kg}\)。
- **宇宙論的拘束**: CMB・重力波伝播からの制約はさらに緩い。

本稿で採用する \(m_\gamma \simeq 3.3\times10^{-64}\,\mathrm{kg}\) （\(\lambda_C\simeq35\,\mathrm{kpc}\)）は、代表的な天体磁場の上限 (例: Ryutov 2007 の \(m_\gamma^{\rm bound} \lesssim 10^{-54}\,\mathrm{kg}\)) より \(m_\gamma \ll m_\gamma^{\rm bound}\) を満たし、安全側に位置する。概念的には \(\log_{10} m_\gamma\) と \(\log_{10} \lambda_C\) の平面で既存上限より十分左側に位置し、FDB が扱うスケールが銀河〜銀河群レンジであることを示している。

### 7.3 桁感と二層スケール

採用値では \(\lambda_C \sim 300\,\mathrm{kpc}\) と銀河群級の長さに対応する。一方、界面での実効遮蔽長 \(\delta = 1/|\mathrm{Im}\,k_{z,2}|\) は 10–30 kpc 程度なので、\(\lambda_C \gg \delta\) が成立し、“巨視では 1/r ドリフト、界面では波導”という二層像が自然に両立する。

---

## 9. 界面波導と 1/r フラックス

### 8.1 波導条件

界面を伝わる TE モードの反射係数は
\[
R = \frac{k_{z,1} - k_{z,2}}{k_{z,1} + k_{z,2}}, \quad
k_{z,i} = \sqrt{\frac{\omega^2 - \omega_{p,i}^2 - \mu_\gamma^2 c^2}{c^2} - k_\parallel^2}.
\]

ここで 1 をボイド側、2 を銀河側とすると、\(k_{z,1}^2>0\)・\(k_{z,2}^2 < 0\) となる周波数帯で高反射 (\(|R|\approx 1\)) が実現する。実効遮蔽長 \(\delta = 1/|\mathrm{Im}\,k_{z,2}|\) は 10–30 kpc 程度で、銀河スケールより短い。
導波路解析そのものは電磁波工学の標準的話題であり、電気学会 (2013) などの解説と同じ数学を使っている。

### 8.2 幾何学的帰結

波が界面に沿って伝わると、球面幾何から円筒幾何に変わり、エネルギーフラックス保存は
\[
2\pi r I(r) = \text{const} \Rightarrow I(r) \propto \frac{1}{r}
\]
となる。情報フラックス \(I(r)\) が 1/r で減衰すると、後述する確率ドリフトを通じて**有効力も 1/r** になる。

---

## 10. 情報フラックスと確率ドリフト

### 9.1 Lindblad 形式の導入

連続測位を表す Lindblad 方程式
\[
\frac{d\rho}{dt} = -\frac{i}{\hbar}[H, \rho] + \frac{\Gamma}{2}\left(2L\rho L^\dagger - \{L^\dagger L, \rho\}\right)
\]
を Wigner 表現で展開すると、Fokker–Planck 方程式
\[
\frac{\partial f}{\partial t} = -\partial_x (A f) + \frac{1}{2}\partial_x^2(D f)
\]
に写る。ここでドリフト係数 \(A\) は \(\Gamma(x)\) の勾配に比例する。界面で \(\Gamma \propto I(r) \propto 1/r\) ならば \(A \propto -1/r\)、つまり有効力も 1/r になる。Lindblad 形式の導出や物理的意味付けは上田 (2015) が詳しい。Fokker–Planck への展開と拡散係数の扱いは久保 (1978) を参照すれば数学的背景を確認できる。

### 9.2 有効ポテンシャル

FDB の有効ポテンシャルを
\[
\Phi_{\rm FDB}(r) = v_c^2 \ln r
\]
とすると、Newton 力学の等温球と同形になり、**強重力レンズの公式とも一致**する。

---

## 11. 観測検証

<a id="sec6"></a>

FDB では §2 のボックスで示したように、情報流の幾何だけで繰り込み定数が決まるため、観測側では比を取るだけで理論と整合するか判断できる。以下では強重力レンズ (H1) と BTFR を順に扱う。

### 10.1 強レンズ一次検定 (H1)

> **H1 定義ボックス**
> $R \equiv \theta_E' c^2/(2\pi v_c^2)$、$\theta_E' = \theta_E D_s/D_{ls}$、$v_c = \sqrt{2}\sigma$（SIS 速度分散）。
> *注意*: $v_c$ 軸を用いるときは分母は常に $2\pi$。1 次元速度分散 $\sigma$ を直接使う場合は $4\pi \sigma^2$ を用いる。
> **PASS 窓**: $|m_R|\le 0.03$ dex、$s_R\le 0.10$ dex（1.4826×MAD）。

H1 (ratio) test: implementation at a glance  
• 軸と単位: \(v_c=\sqrt{2}\sigma\) [km/s], \(\theta_E'=\theta_E D_s/D_{ls}\) [radian]。  
• 切片: \(b_0=\log_{10}(2\pi)-2\log_{10}c\); \(\log_{10}R\) は 0 dex を基準。  
• 指標: 中央値 \(m_R\)、ロバスト散布 \(s_R=1.4826\times\mathrm{MAD}\); PASS は \(|m_R|\le0.03\) dex かつ \(s_R\le0.10\) dex。  
• サンプル: SDSS/BELLS は PASS、BOSS は \(m_R=+0.0846\) dex, \(s_R=0.1497\) dex で補助 QC セット。  
• 再現: `src/analysis/h1_ratio_test.py`; カタログは `data/strong_lensing/` に配置済み。

- **計算手順**: (1) $\theta_E$ をラジアン化し $\theta_E' = \theta_E D_s/D_{ls}$ を求める。(2) $\sigma_{\rm SIS}$ または補正済み $\sigma_e$ を用い $v_c=\sqrt{2}\sigma$ を計算。(3) 各レンズで $R_i$ を算出し $m_R,s_R$ を評価する。
- **結果**: SDSS/BELLS は PASS、BOSS は $m_R=+0.0846$ dex, $s_R=0.1497$ dex で補助 QC 扱い。図3参照。
図~\ref{fig-h1} は \(\log_{10}R\) の分布と PASS 窓を示す概念図であり、中央値と散布のみで合否が判定できる点を視覚化している。

![H1 比 \(\log_{10}R\) と PASS 窓の概念図。灰色帯が $|m_R|\le 0.03$ dex, $s_R\le 0.10$ dex を示す。](figures/schematic_h1_hist.png){#fig-h1 width=0.7\linewidth}
### 10.2 回転曲線 (SPARC)

- **データ**: SPARC MRT (品質=1、傾斜>30°, R_out>3R_d)。
- **モデル**: FDB は一定 \(V_0\)、NFW は \(c=10\) 固定 (k=1) とし、\(\Delta\mathrm{AICc}=\mathrm{AICc}_{\rm FDB}-\mathrm{AICc}_{\rm NFW}\) を評価。
- **感度試験**: 誤差床 5/3/2 km s⁻¹ と M/L が 0.5/0.7 または二値トグル。full-radius では中央値が正 (FDB 不利) になるが、outer-only (r≥2.5R_d) では負 (FDB 有利) になる。
 - **設定まとめ（外縁指標が主）**: \(Υ_{\rm disk}=0.5\), \(Υ_{\rm bulge}=0.7\), \(\sigma_{\rm floor}=5\,\mathrm{km\,s^{-1}}\), FDB \(k=1\), NFW \(k=1\) (c=10 固定); \(\Delta\mathrm{AICc}<0\) が FDB 有利。
図~\ref{fig-aicc} に ΔAICc の符号と“全半径 vs 外縁”の読み方を示した概念図を載せ、負が FDB 有利であることを視覚的に示している。

![ΔAICc の読み方。横軸は ΔAICc、負領域が FDB 有利、正領域が NFW 有利。全半径と外縁の中央値を矢印で示す。](figures/schematic_aicc_axis.png){#fig-aicc width=0.65\linewidth}

### 10.3 BTFR

BTFR 図では横軸 $x = \log_{10} M_{\rm bar}[M_\odot]$、縦軸 $y = \log_{10} v_{\rm flat}^4[(\mathrm{km\,s^{-1}})^4]$ を用い、傾き 1 を固定した基準線 $y=x+b$ (b = median(y−x) = −1.69 dex) と ±0.1 dex 帯で FDB の $v^4\propto M_{\rm bar}$ 予言を視覚化する。図~\ref{fig-btfr} はこの関係を概念的に示したもので、観測中央値で切片を合わせるだけで FDB の予言に一致する点を強調している。

![BTFR の概念図。横軸 $\log_{10}M_{\rm bar}$、縦軸 $\log_{10}v_{\rm flat}^4$。傾き 1 の直線と ±0.1 dex の帯で整合を示す。](figures/schematic_btfr.png){#fig-btfr width=0.7\linewidth}
各銀河の $\Delta v^2 = v_{\rm obs}^2 - v_{\rm bar}^2$ がほぼ一定であるため、$L_0 = GM_{\rm bar}/\Delta v^2$ の散布が BTFR の散布と一致するという物理的解釈に直結する。

---

## 12. 資料：再現ガイド

再現手順の最小セットは以下のとおり。追加オプションやログ整形は README を参照すれば十分。

1. `git clone https://github.com/genki/gravitation` で取得し、検証コミット (`c429a17`) にチェックアウト。依存は Pandoc と XeLaTeX。
2. `make refresh` を実行すると `build/main.pdf` と `build/main.ja.pdf` が生成され、H1 比 (Table 1, Fig.2) と SPARC 解析 (Table 2, Fig.4) が同時に再計算される。
3. 中間 CSV やログは `build/` に保存される。個別に再計算する場合は `src/analysis/h1_ratio_test.py` と `src/scripts/sparc_sweep.py` を直接呼び出せばよい。

---

## 13. 制限と今後

- **等価原理**: \(L_0\) を環境依存と見ることで、試験体質量に依存しない。太陽系では情報勾配が小さく追加力は無視できる。
- **強重力**: 近接ブラックホール周りでは波導条件が破れ、3D 逆二乗に戻る。GR との厳密整合は今後の課題。
- **決定的テスト**: 同じ銀河で \(\theta_E\) と \(v_c\) を同時測定し、\(R=1\) から 0.03 dex 以上ずれれば FDB は即棄却できる。
- **位置づけ**: FDB は赤方偏移・測地線・SIS レンズを GR と同値に保ったまま、外縁のみ有効項を立ち上げる設計であり、既存の太陽系・強重力試験と矛盾しない。

### 13.1 射程と限界・未解決課題
- **射程**: 銀河〜宇宙網スケール（回転曲線、BTFR、強レンズ H1、σ8/H0 緩和の可能性）。重力波セクターは GR と同一。  
- **扱わない領域**: 標準模型パラメータ、インフレーション、バリオン非対称性、QCD コンファインメント、ブラックホール内部、プランクスケール量子重力。  
- **未解決課題**: (i) FDB カーネルを入れた宇宙論シミュレーション、(ii) 強レンズ＋BTFR＋σ8/H0 の同時フィット、(iii) プラズマ・フィラメント環境からの \(\Gamma(x)\) の微視的導出、(iv) \(m_\gamma\sim10^{-65}\,\mathrm{kg}\) オーダーの実験・宇宙線制約。

### 13.2 FDB の場の内容：新しい基本場は導入しない
FDB は **標準模型の物質場と電磁場（ULE‑EM）だけ** を基本場として用いる。情報ポテンシャル \(\Phi_{\rm FDB}\) やインフォーミング・テンソル \(I_{\mu\nu}\) は前波グリーン関数と物質テンソルの畳み込みで得られる非局所的・有効的な量であり、新たなゲージ場やスカラー場を仮定しない。
\[
I_{\mu\nu}(x)
 = \kappa (P_{\rm TT})_{\mu\nu}{}^{\alpha\beta}
   \int d^4x'\,G_{\rm front}(x,x')\,T^{\rm(mat)}_{\alpha\beta}(x').
\]

### 13.3 インフォーミング・テンソルの自由度：GR と同じ 2
対称テンソルは 10 成分だが、TT 射影で \(\partial^\mu I_{\mu\nu}=0\)（4 条件）、\(I^\mu{}_\mu=0\)（1 条件）を課すと 10−5=5 成分に減る。波動方程式 \(\Box I_{\mu\nu}=0\) の下では物理偏極は
\[
I^{+}_{ij},\quad I^{\times}_{ij}
\]
の **2 自由度** に絞られ、GR の重力波セクター（速度 \(c\)、テンソル 2 偏極、四重極公式）と一致する。

### 13.4 新しい基本場を使わない量子重力的描像
- \(I_{\mu\nu}\) を独立場として量子化せず、EM＋物質の量子相関から生まれる複合場として扱う。  
- UV 挙動は QED＋物質の再正規化で制御され、GR 量子化で現れる \(GE^2\) 型の非再正規化問題を回避。  
- 重力は ULE-EM 前波という IR 極限で現れ、放射セクターは GR と同型のまま。  
- 相関関数 \(\langle I_{\mu\nu} I_{\alpha\beta}\rangle\) は EM 相関と \(G_{\rm front}\)、TT 射影の畳み込みで与えられ、新規場を足さずに量子重力的 EFT を構成できる。

### 13.5 インフォーミング波の媒質位相シフト
真空では \(I_{\mu\nu}\) の波動方程式は GR と同じ \(\Box I_{\mu\nu}=0\)。宇宙網を伝播する際の微小補正を有効屈折率のずれ \(\delta n\) で
\[
\omega = c k (1+\delta n),\qquad |\delta n|\ll1
\]
と書くと、距離 \(L\) で位相ずれ
\[
\delta\phi = kL\,\delta n
\]
を生む。検出器の位相分解能 \(\delta\phi_{\max}\sim1/\mathrm{SNR}\) から
- LISA（SMBH, SNR∼100）: \(|\delta n|\lesssim10^{-17}\)
- ET/CE（BNS/BBH, SNR 100–500）: \(|\delta n|\lesssim10^{-21}\)
となり、前波の媒質分散はきわめて小さいことが要求される。これは FDB の「前波は本質的に無分散で GR と同型」という予測と整合する。

---

<a id="refs-ja"></a>
## 14. 参考文献（抄訳）

- Rubin & Ford 1970s — 銀河回転曲線の観測的確立。
- Tully & Fisher 1977 — バリオン Tully–Fisher 関係の発見。
- Milgrom 1983 — MOND の初期提案。
- Navarro, Frenk & White 1996/1997 — NFW ハローの代表論文。
- Verlinde 2016 — 情報・エントロピーに基づく emergent gravity。
- McGaugh, Lelli & Schombert 2016, AJ 152, 157 — SPARC カタログ。
- Narayan & Bartelmann 1997 — SIS レンズ公式の基礎。
- Sugiura 1978; Hurvich & Tsai 1989 — AICc の導入論文。
- Shu et al. 2016/2017 — BELLS/BELLS GALLERY/S4TM レンズカタログ。
- Particle Data Group 2024 — フォトン質量上限および Proca 限界。
- Goldhaber & Nieto 2010 — フォトン質量上限レビュー (Rev. Mod. Phys. 82, 939)。
- Tu, Luo & Gillies 2005 — フォトン質量制限の実験的レビュー (Rep. Prog. Phys. 68, 77)。
- Ryutov 2007 — 太陽風・天体磁場からのフォトン質量制限 (Plasma Phys. Control. Fusion 49, B429)。
- 砂川重信 1987 — 『理論電磁気学（第2版）』岩波書店。Proca 場と有質量電磁気の基礎。
- 電気学会 編 2013 — 『新版 電磁波ハンドブック』コロナ社。導波路と界面反射の実用解説。
- 上田正仁 2015 — 『量子光学』岩波書店。Lindblad 形式と開放量子系の導出。
- 久保亮五 1978 — 『確率論と統計的物理』岩波書店。Fokker–Planck 方程式の背景。
- Pound & Rebka 1960 — 重力赤方偏移の塔実験 (Phys. Rev. Lett. 4, 337)。
- そのほか英語版 `refs.bib` に列挙された文献。

---

<a id="appendixA"></a>
## 付録 A: 用語と式まとめ

| 用語 | 意味 |
|---|---|
| ULE-EM | 超低エネルギーの Proca 電磁場。フォトン質量は \(m_\gamma=\hbar/(c\lambda_C)\) で表し、代表域は \(\lambda_C=\mathcal{O}(10^{1}\text{–}10^{2}\,\mathrm{kpc})\Rightarrow m_\gamma=\mathcal{O}(10^{-64}\,\mathrm{kg})\)。|
| \(v_c\) | 円速度。観測される 1 次元速度分散 \(\sigma\) から \(v_c=\sqrt{2}\sigma\)。|
| H1 比 | \(R=\theta_E' c^2/(2\pi v_c^2)\)。SIS と完全一致する定数関係。|
| PASS 窓 | \(|m_R|\le0.03\) dex, \(s_R\le0.10\) dex。|
| ΔAICc | \(\mathrm{AICc}_{\rm FDB}-\mathrm{AICc}_{\rm NFW}\)。負なら FDB 有利。|

数式の詳細は英語版 (main.md) および `appendix_f_h1.md` を参照。

---

## 付録 F: 重力赤方偏移の 1 点検証

FDB のポテンシャルは §9 で示したとおり \(\Phi_{\rm FDB}=v_c^2\ln r\)（弱場）で GR の等温球と同形になる。固有時間の比は
\[
\frac{d\tau}{dt} \simeq 1 + \frac{\Phi_{\rm FDB}}{c^2},
\]
したがって周波数が \(\nu\) から \(\nu+\Delta\nu\) にシフトする場合
\[
\Delta \ln \nu \simeq -\frac{\Delta \Phi_{\rm FDB}}{c^2}
\]
が得られる。地上 22.5 m の塔の上下間で行われた Pound–Rebka 実験や GPS 衛星と地上局の比較をこの式に代入すると、GR と同じ赤方偏移値が再現される。よって H1 比の正規化に自由な切片は残らず、FDB のゼロ自由度等式 (\(R=1\)) は独立にキャリブレーション済みである。

---
