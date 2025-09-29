# κ と C のミクロ起源とサムルール（第一原理の整理）

> ここでは ULW の放射スペクトルと検出効率（記録断面積）から、先に導入した定数 $\kappa$ と $C$ を第一原理で結びつけて一意化する道筋を、数式レベルまで整理します。
>
> 要点:
> - $C$ は「1 個の“記録可能な ULW 量子”が、距離 $R$ でつくる $1/R^2$ 型ハザードの規格化」であり、放射スペクトル $\times$ 記録断面積の周波数積分に等しい。
> - $\kappa$ は「ログ確率（情報作用）をエネルギーに変換するスケール」で、ローレンツ不変の質量固有エネルギーから $\boxed{\kappa = m c^2}$（光は $\kappa^{(\gamma)}=p c$）が自然。これで等価原理と弱レンズの係数 2 が同時に成立する。
> - これらを合わせると $\kappa C/c = G$ が必要十分条件になり、$\kappa=m c^2$ を採れば $\boxed{C=G/c}$ が普遍定数として固定される（“放射×記録”のサムルール）。

---

## 1) 微視的定義：放射スペクトルと記録断面積

- 放射（発信側；テスト粒子）: 単位質量あたり、周波数 $\omega$ の ULW 光子放射数率（全立体角に積分済み）
  $$\phi_{\rm emit}(\omega)\quad[\mathrm{s}^{-1}\,\mathrm{Hz}^{-1}\,\mathrm{kg}^{-1}]$$
  （等方放射でない場合は角度分布 $D_{\rm emit}$ を掛け、最後に平均）。
- 記録（受信側；“検出器”＝質量）: 単位質量あたり、周波数 $\omega$ の実効「記録断面積」
  $$\sigma_M(\omega)\quad[\mathrm{m}^2\,\mathrm{kg}^{-1}]$$
  （検出効率 $\eta(\omega)$ や局所増幅を含めた、不可逆な記録に至る総合効率）。

どちらも組成依存を極力持たない（＝単位質量あたりでほぼ普遍）ことが WEP 整合の要請。

---

## 2) ハザード核と $C$ の導出

距離 $R=\lvert\mathbf{x}-\mathbf{y}\rvert$ の受信素片 $dM=\rho_D(\mathbf{y})\,d^3y$ が受け取る ULW フラックスは等方近似で $\phi_{\rm emit}(\omega)/(4\pi R^2)$。
そこから 1 つの“記録”が成立する微小率は
$$
 d\lambda(\omega)\;=\; \frac{\phi_{\rm emit}(\omega)}{4\pi R^2}\ \sigma_M(\omega)\ dM\ .
$$

周波数と空間にわたって積分すれば、発信点 $\mathbf{x}$ にいるときの総ハザード率は
$$
\Lambda(\mathbf{x})
=\!\int d^3y\,\rho_D(\mathbf{y})\ \underbrace{\frac{1}{R^2}\,\Big[\frac{1}{4\pi}\!\int_0^\infty\!\phi_{\rm emit}(\omega)\,\sigma_M(\omega)\,d\omega\Big]}_{\displaystyle K(R)\equiv C/R^2}\ .
$$
よって、
$$
\boxed{\ C\;=\;\frac{1}{4\pi}\int_0^\infty \phi_{\rm emit}(\omega)\,\sigma_M(\omega)\,d\omega\ }\quad(\text{異方性は角度平均で同等}).
$$
次元確認: $[\phi_{\rm emit}\sigma_M]=\mathrm{m}^2/(\mathrm{s}\cdot\mathrm{kg})$。 

---

## 3) $\kappa$ の規格化とサムルール $\;C=G/c$

- 見かけ“エネルギー”スケールはログ確率（無次元）をエネルギーに写す:
  $$\boxed{\ \kappa = m c^2\ ,\qquad \kappa^{(\gamma)} = p c\ (\text{光})\ }$$
  等価原理（加速度の質量独立）と弱レンズ係数2が自動で成立。
- 点質量 $M$ に対する光円錐積分から（概略）
  $$\ln S(r)\simeq -\,\frac{C\,M}{c}\,\frac{1}{r}\ \Rightarrow\ U_{\rm info}=\kappa\ln S\ \Rightarrow\ \mathbf{g}= -\frac{\kappa}{m}\,\frac{C}{c}\,\frac{M}{r^2}\,\hat{\mathbf{r}}\ .$$
  これがニュートン極限 $\mathbf{g}=-GM\,\hat{\mathbf{r}}/r^2$ と一致する必要十分条件は
  $$\boxed{\ \frac{\kappa}{m}\,\frac{C}{c} = G\ }\ .$$
  $\kappa = m c^2$ なら
  $$\boxed{\ C = \frac{G}{c}\ }\ \simeq\ 2.227\times 10^{-19}\ \frac{\mathrm{m}^2}{\mathrm{s}\cdot\mathrm{kg}}\ .$$
- 2) の第一原理式へ代入:
  $$\boxed{\ \frac{1}{4\pi}\int_0^\infty \phi_{\rm emit}(\omega)\,\sigma_M(\omega)\,d\omega\ =\ \frac{G}{c}\ }\ .$$
（“放射×記録”のサムルール）

---

## 4) 物理要請（WEP／普遍性）と逐次同定

1. WEP: $\phi_{\rm emit}/\mathrm{kg}$ と $\sigma_M/\mathrm{kg}$ は組成に依存しない（許容誤差 $\ll 10^{-13}$）。
2. 相反則: $\phi_{\rm emit}(\omega) \propto \sigma_M(\omega)\,u_{\rm ULW}(\omega)/(\hbar\omega)$ を期待。
   $$C \propto \int \frac{\sigma_M(\omega)^2}{\hbar\omega}\,u_{\rm ULW}(\omega)\,d\omega$$
3. エネルギー流の無矛盾: サムルールは「数（レート）×効率」の制約で、エネルギー保存と矛盾しない。

---

## 5) 標準形（提案）

(A) 形状分離（形×振幅）
- 形状関数（無次元・正規化）: $\varphi(\omega)\ge 0,\ \int \varphi(\omega)\,d\ln\omega=1$
- パラメトリック形: $\phi_{\rm emit}=\Phi_0\,\varphi(\omega),\ \ \sigma_M=\Sigma_0\,g(\omega)$
- サムルール: $\dfrac{\Phi_0\Sigma_0}{4\pi}\int \varphi\,g\,d\omega=G/c$

(B) 相反形（キルヒホッフ近似）
- $\phi_{\rm emit}(\omega)=\alpha\,\sigma_M(\omega)\,\dfrac{u_{\rm ULW}(\omega)}{\hbar\omega}$
- サムルール: $\dfrac{\alpha}{4\pi}\int \dfrac{\sigma_M(\omega)^2}{\hbar\omega}\,u_{\rm ULW}(\omega)\,d\omega=G/c$

---

## 6) 数値スケールの目安

$$\boxed{\ C\ =\ \frac{G}{c}\ \simeq\ 2.227\times 10^{-19}\ \frac{\mathrm{m}^2}{\mathrm{s}\cdot\mathrm{kg}}\ }$$

総放射レート $\Phi_{\rm tot}=\int\phi_{\rm emit}d\omega$、重み付き平均断面積 $\bar{\Sigma}=\frac{\int \phi_{\rm emit}\sigma_M d\omega}{\int \phi_{\rm emit} d\omega}$ とすると、
$$\frac{1}{4\pi}\,\Phi_{\rm tot}\,\bar{\Sigma}\ =\ \frac{G}{c}\ .$$
仮に $\bar{\Sigma}\sim 10^{-2}\ \mathrm{m}^2/\mathrm{kg}$ なら、
$$\Phi_{\rm tot}\sim 4\pi(G/c)/\bar{\Sigma}\ \sim\ 3\times 10^{-16}\ \mathrm{s}^{-1}\,\mathrm{kg}^{-1}.$$

---

## 7) 実験・同定プロトコル（最短経路）

1. “記録”定義の工程化（クリックの定義）
2. 送受一体の相反測定（同一試料で $\phi_{\rm emit},\sigma_M$ を取得）
3. サムルールの検証: $\dfrac{1}{4\pi}\int \phi_{\rm emit}\sigma_M\,d\omega \stackrel{?}{=} G/c$
4. 天文クロスチェック: $\Phi_{\rm eff}$ で回転曲線・弱レンズを同時再現

---

## 8) まとめ

- $C$ は $\displaystyle C=\dfrac{1}{4\pi}\int \phi_{\rm emit}\,\sigma_M\,d\omega$ の第一原理定義を持ち、$\kappa=m c^2$ と組み合わせた $\kappa C/c = G$ により $\boxed{C=G/c}$ に一意化。
- “ULW の放射×記録”のサムルールで WEP と弱場GR同型を満たす。

---

> 付記: 簡易検証スクリプト `scripts/demo_sumrule_kappaC.py` を用意（サンプル形状を内蔵）。

