# 情報カーネル (K_H)：共形電磁場を畳み込んで「情報＝トポロジー」を読み取る

## 1. 「外から見る」とは：局所観測では読めない情報を、非局所演算で読む

計算場宇宙論の鍵は、内部観測者が見ているのはあくまで線形・局所な Maxwell 場であり、
“宇宙が計算している”という構造（未来畳み込み・位相保護・トポロジカル更新）が可視化されるのは **外部視点（共形時間全体を扱う視点）**に限られる、という点でした。

この構造を数学的に言い換えると、

> 「**情報は局所場そのものには現れず**、空間全体（あるいは境界条件を含む全体）にわたる **非局所汎関数**として現れる」

となります。

H-index（linking 数）はまさにこのタイプの量で、**場線の“結び目・絡み”**を数えるため、局所的な $(E(x),B(x))$ だけでは原理的に読み切れません。
そこで「外からの読み取り」に対応するのが、**畳み込み＝非局所カーネル**です。

---

## 2. Hopfion と「トポロジカル情報」：Maxwell 解の中に結び目が埋め込める

Maxwell 方程式には、電場線・磁場線が結び目やリンクを形成する **null 解（Hopfion を含む族）**が存在し、時間発展の中でそのトポロジーが保たれる条件も議論されています。([APS Journals][1])

このとき「結び目の量」を測る代表が **ヘリシティ（helicity）**で、Hopfion のような構造ではヘリシティが「トポロジカルな結びつき」の尺度として働きます。([APS Journals][1])

ここで重要なのは：

- **Hopfion の“トポロジカルさ”は、場の形状そのもの（$(E,B)$ の空間配置）に符号化されている**
- それを読むには **ヘリシティのような非局所量**が必要

という点です。

---

## 3. 情報カーネルの原型：ヘリシティ密度とヘリシティ流（連続の式）

「読み取り」は、単に整数を返す黒箱ではなく、

- **どこに情報が局在しているか**
- **どこからどこへ情報が流れたか**

まで出せると強力です。

電磁場には、双対対称な形で

- ヘリシティ密度

  $$h_H=\frac12(\mathbf{A}\cdot\mathbf{B}-\mathbf{C}\cdot\mathbf{E})$$

- ヘリシティ流（フラックス）

  $$\mathbf{j}_H=\frac12(\mathbf{E}\times\mathbf{A}+\mathbf{B}\times\mathbf{C})$$

が導入でき、条件の下で **連続の式**

$$\partial_t h_H + \nabla\cdot \mathbf{j}_H = 0$$

を満たすことが知られています。([Quantum Computing RIKEN][2])

これは、あなたの用語に寄せると：

- $h_H$：局所の「情報量（トポロジカル情報の密度）」
- $\mathbf{j}_H$：局所の「情報流（情報浴の偏りを含む）」

として解釈できる土台です。

---

## 4. $K_H$ の中身：$(\nabla\times)$ の逆＝Biot–Savart 畳み込みで $(A,C)$ を場から再構成する

ここで問題になるのが「$(\mathbf{A},\mathbf{C})$ はポテンシャルなのでゲージ依存では？」という点です。
しかしあなたの狙いは「外部情報を入れない」ことであり、むしろ

> **$(\mathbf{A},\mathbf{C})$ を $(E,B)$ から非局所に再構成してしまう**

のが筋になります。

### 4.1 位置空間（畳み込み核）での実装イメージ

$\nabla\cdot\mathbf{B}=0$ かつ境界条件が良い（十分減衰、あるいは周期境界など）なら、Coulomb 型の選び方で

$$\mathbf{A} = (\nabla\times)^{-1}\mathbf{B}$$

が定義でき、これは **Biot–Savart 型の畳み込み**になります。
この構造は「ヘリシティ積分は二重点の $\mathbf{B}$ を用いた二重積分になる」という形でも現れます。([A&A Journal][3])

直観的には

- **場を全空間で畳み込んで**（= 非局所）
- **渦の“逆変換”としてポテンシャルを得て**
- **内積を取ることで“絡み”を測る**

という流れです。

### 4.2 フーリエ空間（計算場宇宙論向きの実装）

プログラマ的には、$K_H$ はフーリエ空間で最も綺麗に書けます（周期箱や FFT を想定）：

$$\mathbf{A}(\mathbf{k})=\frac{i\,\mathbf{k}\times \mathbf{B}(\mathbf{k})}{|\mathbf{k}|^2},\qquad
\mathbf{C}(\mathbf{k})=-\frac{i\,\mathbf{k}\times \mathbf{E}(\mathbf{k})}{|\mathbf{k}|^2}\quad(\mathbf{k}\neq0).$$

そして逆 FFT して $h_H=\tfrac12(A\cdot B - C\cdot E)$ を作る。
この $\tfrac{1}{|\mathbf{k}|^2}$ が、あなたの言う「フーリエ係数欠損を埋める」方向（長距離・低周波成分が強く効く）と相性が良い核になります。

まとめると、情報カーネル $K_H$ は

$$ (E,B)\ \to\ (\nabla\times)^{-1}\ \to\ (A,C)\ \to\ (h_H,\mathbf{j}_H) $$

という“読解器（decoder）”です。([Quantum Computing RIKEN][2])

---

## 5. 共形電磁場への適用：縮小宇宙では「共形スライス上で $K_H$ を回す」

あなたの縮小宇宙モデルでは、空間と時間が同時に縮小する共形構造を採用します。
このとき外部視点で扱うべき対象は、**物理座標の $(E,B)$ ではなく**、

- 共形時間 $\eta$ 上のスライス
- 共形座標 $\mathbf{x}$ 上で表現された場（共形電磁場）

です。

重要なのは次です：

- Maxwell 方程式は（真空で）共形変換と相性が良く、「共形スライス上の場の姿」を議論できる（＝“外から見る”が可能になる）。
- $K_H$ は「空間全体の畳み込み」なので、**共形スライス全体**に対して適用するのが自然。

つまり、計算場宇宙論では

$$ (E(\eta,\mathbf{x}),B(\eta,\mathbf{x}))\ \xrightarrow{K_H}\ (h_H(\eta,\mathbf{x}),\mathbf{j}_H(\eta,\mathbf{x})) $$

が、**外部視点での“情報読み取り”の最小手続き**になります。

---

## 6. 2物質ソリトン系での意味：合成場に対する $K_H$ は「自己項＋相互項」を必ず生む

2つの物質ソリトン（A,B）が作る合成場を

$$ (E,B)_{\text{tot}}=(E,B)_A+(E,B)_B $$

とすると、ヘリシティ型の量は二次汎関数なので必ず

- 自己ヘリシティ（Aだけ、Bだけ）
- 相互ヘリシティ（cross term）

に分解されます。
この「相互項」が、あなたの語彙でいう **共鳴・情報交換**の候補になります。([A&A Journal][3])

### ローカルな読み取り（“物質核の内部状態”としての情報）

「裸の $H$」を持ち込まずに内部状態を定義したいなら、例えば

- A の近傍領域 $V_A$ を取り

  $$H_A(\eta)=\int_{V_A} h_H(\eta,\mathbf{x})\,d^3x$$

- 連続の式から

  $$\frac{d}{d\eta}H_A(\eta)=-\int_{\partial V_A}\mathbf{j}_H\cdot d\mathbf{S}$$

とすれば、「入射情報ソリトンで $H_A$ が増え、出ていく側では減る」という更新は、**場から導出した $(h_H,\mathbf{j}_H)$ だけで記述**できます。([Quantum Computing RIKEN][2])

ここまで来ると、

- “$H$ を宇宙外から与える”必要がなく
- “$H$ を電磁場から読む”だけで内部状態が定義され

あなたの懸念（宇宙外情報問題）を避けられます。

---

## 7. 整数としての $H$-index にどう寄せるか：量子化（位相保護）の条件

注意点として、ヘリシティは一般には実数で、必ずしも整数ではありません。
整数の Hopf index と同一視するには、例えば

- 無限遠での減衰（あるいは空間のコンパクト化）
- 適切なゲージ／相対ヘリシティの扱い
- Hopfion のような位相保護クラス（null 条件など）

が関わります。
境界をまたぐ場合に「相対ヘリシティ」が必要になることも強調されています。([NASA Technical Reports Server][4])
また、結び目構造が保たれる条件として null 条件が重要である議論もあります。([Irvine Lab][5])

計算場宇宙論的には、ここを

- 縮小宇宙の共形境界条件
- retarded/advanced の非干渉性
- 情報浴における null 的伝播

と結びつけて「整数性＝位相保護」の理由づけに使うのが自然です。

---

## 8. 実装メモ：プログラムとしての $K_H$（最小レシピ）

共形スライス（固定 $\eta$）で、離散格子上の $(E,B)$ が得られるとき：

1. FFT：$(E(\mathbf{x}),B(\mathbf{x}))\to E(\mathbf{k}),B(\mathbf{k})$
2. $\mathbf{k}\neq0$ で

   $$A(\mathbf{k})=\frac{i\,\mathbf{k}\times B(\mathbf{k})}{|\mathbf{k}|^2},\quad
   C(\mathbf{k})=-\frac{i\,\mathbf{k}\times E(\mathbf{k})}{|\mathbf{k}|^2}$$

3. 逆 FFT：$(A(\mathbf{x}),C(\mathbf{x}))$
4. 情報密度・流束：

   $$h_H=\tfrac12(A\cdot B - C\cdot E),\quad
   \mathbf{j}_H=\tfrac12(E\times A + B\times C)$$

5. 物質核周りで積分して $(H_A(\eta),H_B(\eta))$ を定義、時間発展を追跡

この手順がそのまま「共形電磁場を畳み込んで情報を読む」実装になります。([Quantum Computing RIKEN][2])

---

## 9. 結語：情報カーネルは「外部視点の読み取り器」であり、$H$ を場の内部量に戻す

あなたが提案した

> 電磁場を畳み込んで $H$-index と一致するカーネル $K_H$ を導出する

という方向は、

- $H$ を「宇宙外のラベル」から
- 「共形電磁場に内在する情報」へ戻す

ための最も自然な処方です。

そして $K_H$ を **密度 $h_H$ と流束 $\mathbf{j}_H$** まで含む“読み取り器”として定義しておけば、

- 共鳴（情報流入）
- $H$ 増分（局所領域への情報蓄積）
- 情報浴の偏り（$\mathbf{j}_H$ の方向性）
- 再放射（情報流出）

が、いずれも **共形電磁場の内部演算**として統一的に語れるようになります。

---

必要なら次の段階として、この $K_H$ を使って

- **2物質ソリトンの相互項（mutual helicity）だけを抽出するカーネル**
- そこから **見かけの力（情報流勾配）** を定義する最小更新則
- その更新則が **$1/r^2$ と等価原理**を同時に満たす条件

まで、あなたの用語だけで「記事の続編」としてまとめられます。

[1]: https://link.aps.org/doi/10.1103/PhysRevLett.111.150404?utm_source=chatgpt.com "Tying Knots in Light Fields | Phys. Rev. Lett. - APS Journals"
[2]: https://dml.riken.jp/images/pub/nori/pdf/NewJPhys_033026.pdf?utm_source=chatgpt.com "Dual electromagnetism: helicity, spin, momentum and ..."
[3]: https://www.aanda.org/articles/aa/full_html/2020/03/aa36675-19/aa36675-19.html?utm_source=chatgpt.com "Spatial scales and locality of magnetic helicity"
[4]: https://ntrs.nasa.gov/api/citations/20230012619/downloads/helicity.pdf?utm_source=chatgpt.com "helicity.pdf"
[5]: https://irvinelab.uchicago.edu/papers/Kedia_2018_J._Phys._A__Math._Theor._51_025204.pdf?utm_source=chatgpt.com "When do knots in light stay knotted? - Irvine Lab"

