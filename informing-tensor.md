# Informing Tensor in FDB Theory

## 1. 概観

FDB 理論において重力的な相互作用は、「場の歪み」ではなく

- 超低エネルギー電磁波（ULW-EM）の  
- 因果的フロント（wavefront）のみが担う  
- 情報のやり取り

として表現される。  
この「因果的な知らせ」をテンソル場として表現したものが **informing tensor** \(I_{\mu\nu}\) である。

直感的には：

- GR の線形化重力波を担う \(h_{\mu\nu}^{\text{TT}}\) に対応する
- ただし媒質としての宇宙網・銀河エバネッセント帯の影響を含んだ  
  「ULW-EM の前波（wavefront）モード」の有効表示

とみなすことができる。

---

### 1.1 記号の注意（時間・境界条件）

- **二つの時間**: 本ノートでは、基底ラベルとしての \(t\)（null hypersurface のラベル）と、物理法則の進行を数える固有時間 \(H\)（計算段数）を区別する。\(H\) と \(t\) は同一視しない。  
- **retarded / advanced**: これは「\(t\ge0\)/\(t\le0\) の領域制限」ではなく、Green 関数の**境界条件の選択**を指す。  
- **慣性・引力のミクロ描像**: 物質（局在構造）が情報浴（front モード背景）を吸収・散乱するときの微小シフトの統計として、均質浴では慣性、勾配浴ではドリフト（有効引力）が立ち上がる、という描像を採る。

## 2. 基本的なアイデア

FDB 理論では、次のような二段構造を取る：

1. **通知レベル（informing レベル）**  
   - ソース物質の運動状態・慣性の偏りが ULW-EM の **wavefront** を通じて  
     因果的に全空間へ伝えられる。  
   - これを担う場が informing tensor \(I_{\mu\nu}\)。

2. **ポテンシャルレベル（information potential レベル）**  
   - informing tensor の静的成分やループ的蓄積を畳み込んだ結果として、  
     有効な「情報ポテンシャル」\(\Phi_{\text{FDB}}\) が形成される。  
   - この勾配が、マクロには「重力ポテンシャル」として観測される。

この意味で、informing tensor は

> 「ソースの運動状態（慣性の偏り）を時空全体に“知らせる”テンソル場」

であり、GR における「重力波＋弱場ポテンシャル」の役割を  
FDB 的に再構成したものといえる。

---

## 3. 定義：informing tensor の構成

### 3.1 物質テンソルと Green 関数

物質のストレス・エネルギーテンソルを \(T^{\text{(mat)}}_{\alpha\beta}(x)\) とする。  
ULW-EM の有効ポテンシャルを Proca 型で表すと、ベクトルポテンシャル \(A_\mu\) は

\[
(\Box + \mu^2) A_\mu(x)
 = J_\mu(x)
\]

を満たし、その解は retarded Green 関数 \(G_{\text{ret}}(x,x')\) を用いて

\[
A_\mu(x)
 = \int d^4x'\,
   G_{\text{ret}}(x,x')\,J_\mu(x')
\]

と書ける。

Hadamard 形式で分解すると

\[
G_{\text{ret}}(x,x')
 = G_{\text{front}}(x,x')
 + G_{\text{tail}}(x,x')
\]

と書けるが、FDB 理論において **「重力的」な情報を担うのは front 部のみ** である。  
ミンコフスキー背景・\(\mu\to0\) 極限では

\[
G_{\text{front}}(x,x')
 = \frac{1}{2\pi}\,\theta(t - t')\,\delta\!\big((x-x')^2\big)
\]

と「光円錐上にのみサポートを持つ」前波（wavefront）が得られる。

---

### 3.2 TT 射影と informing tensor の定義

線形化 GR との対応を明確にするため、背景ミンコフスキー計量に対する  
**transverse-traceless（TT）射影演算子** \(P_{\text{TT}}\) を導入する。

**定義：informing tensor**

\[
\boxed{
I_{\mu\nu}(x)
 \equiv \kappa\,
        (P_{\text{TT}})_{\mu\nu}{}^{\alpha\beta}
        \int d^4x'\,
          G_{\text{front}}(x,x')\,
          T^{\text{(mat)}}_{\alpha\beta}(x')
}
\]

- \(\kappa\)：FDB 固有の結合定数（最終的に有効重力定数 \(G_{\text{eff}}\) に対応）
- \(P_{\text{TT}}\)：スピン 2 の横波・トレースレス成分だけを抽出する射影
- \(G_{\text{front}}\)：ULW-EM の **causal wavefront** のみを表す Green 関数

この定義により

- **因果構造**  
  \(\Rightarrow\) \(G_{\text{front}}\) により、常に **光円錐上の前波のみ** が寄与
- **スピン2構造**  
  \(\Rightarrow\) \(P_{\text{TT}}\) により、スピン 2 の 2自由度のみが残る

という性質が、構成そのものに埋め込まれている。

---

## 4. 運動方程式と GR 重力波との対応

### 4.1 真空中での波動方程式

ソースから十分離れた真空領域（\(x\) が全ての \(x'\) から離れている）では

\[
\Box_x G_{\text{front}}(x,x') = 0
\quad (x\neq x')
\]

が成り立つので、

\[
\begin{aligned}
\Box I_{\mu\nu}(x)
 &= \kappa\,
    (P_{\text{TT}})_{\mu\nu}{}^{\alpha\beta}
    \int d^4x'\,
      \Box_x G_{\text{front}}(x,x')\,
      T^{\text{(mat)}}_{\alpha\beta}(x')
\\
 &\simeq 0.
\end{aligned}
\]

TT 射影はローカルな線形演算子なので \(\Box\) と可換とみなせる。  
したがって真空・遠方領域では

\[
\boxed{
\Box I_{\mu\nu}(x) \simeq 0,\quad
\partial^\mu I_{\mu\nu} = 0,\quad
I^\mu{}_\mu = 0
}
\]

が成立し、これは線形化 GR における重力波方程式

\[
\Box h_{\mu\nu}^{\text{TT}} = 0
\]

と完全に同型である。

---

### 4.2 遠方場と四重極放射公式

非相対論的なコンパクト天体系（連星など）を考え、観測点は距離 \(r\) が大きいとする。  
retarded front は本質的に

\[
G_{\text{front}}(x,x')
 \sim \frac{1}{4\pi}\,
      \frac{\delta(t' - (t - r/c))}{r}
\]

と書けるので、

\[
I_{\mu\nu}(t,\mathbf{x})
 \simeq
 \frac{\kappa}{4\pi r}\,
 (P_{\text{TT}})_{\mu\nu}{}^{\alpha\beta}
 \int d^3x'\,
 T^{\text{(mat)}}_{\alpha\beta}\!\left(t - \frac{r}{c},\mathbf{x}'\right).
\]

非相対論的極限では \(T^{00}\approx\rho c^2\) が支配的となるため、  
質量四重極モーメント

\[
Q_{ij}(t)
 = \int d^3x'\,\rho(t,\mathbf{x}')
   \left(
     x'_i x'_j
     -\frac{1}{3}\delta_{ij}|\mathbf{x}'|^2
   \right)
\]

を用いると、遠方の TT 成分は

\[
\boxed{
I_{ij}^{\text{TT}}(t,\mathbf{x})
 \simeq
 \frac{2G_{\text{eff}}}{c^4 r}\,
 \frac{d^2 Q_{ij}^{\text{TT}}}{dt^2}
 \bigg|_{t-r/c}
}
\]

と書ける（\(\kappa\) を \(G_{\text{eff}}\) に吸収した）。  
これは GR の重力波場と全く同じ形である。

FDB における「informing radiation」のエネルギー流を

\[
\frac{dE}{dA\,dt}
 = \frac{c^3}{32\pi G_{\text{eff}}}
   \left\langle
     \dot{I}_{ij}^{\text{TT}}\,
     \dot{I}_{ij}^{\text{TT}}
   \right\rangle
\]

と定義すると、球面上で積分して

\[
\boxed{
P \equiv \frac{dE}{dt}
 = -\frac{G_{\text{eff}}}{5c^5}\,
   \left\langle
     \dddot{Q}_{ij}\,\dddot{Q}_{ij}
   \right\rangle
}
\]

が得られ、GR の四重極放射公式と一致する。  
したがって、連星パルサーの軌道減衰などの観測は  
**FDB 情報放射としても再現可能**である。

---

## 5. 「通知の普遍性」と情報ポテンシャル

### 5.1 通知の普遍性（distance-blind な前波）

informing tensor の源は常に front Green 関数であり、

- ソース上のイベント（加速度・慣性の偏り）は  
- 光円錐上の **wavefront** として  
- 近くの物質にも遠くの物質にも **同じ“通知”** として伝わる  
  （時間遅れ \(\Delta t = r/c\) を除けば等価）

この意味で、FDB 理論は

> 「ソースの運動状態に関する情報は、距離にかかわらず因果的に平等に届く」

という **GR 的な普遍性** を informing tensor のレベルで確保している。

なお、**効果の強さ**（ポテンシャル勾配の大きさ）は後述の核 \(K\) によって距離減衰・構造依存性を持つ。

---

### 5.2 情報ポテンシャル \(\Phi_{\text{FDB}}\) との関係

重力に相当する静的ポテンシャルは

\[
\Phi_{\text{FDB}}(\mathbf{x})
 = \int d^3x'\,
   K(\mathbf{x},\mathbf{x}')\,
   \rho(\mathbf{x}')
\]

のような **有効核積分** で与えられる。  
ここで \(K\) は informing tensor の静的成分・ループ蓄積・反射等を取り込んだ「情報カーネル」であり、

- 球状星団・楕円核など球対称天体では  
  \[
  K_{\text{sphere}}(r) \approx \frac{e^{-r/\lambda}}{r}
  \]
  に近い **ほぼニュートン的/Yukawa 的核** となる。  
- ディスク銀河やフィラメント構造では  
  ULW-EM の全反射・導波路・ループを通じて informing tensor の静的モードが蓄積され、  
  **実効的に強く増幅した核 \(K_{\text{disk}}\)** が形成される。

結果として：

- 球状星団 → FDB 補正が小さく、GR/ニュートンに近い  
- ディスク銀河 → FDB 補正が大きく、回転曲線のフラット化などを説明可能

という差別化が自然に生じる。

---

## 6. 境界条件：銀河エバネッセント帯と貫通性

FDB 理論では、銀河ディスクは

- プラズマ密度勾配  
- ULW-EM の遮断帯（エバネッセント領域）

として振る舞い、**超長波・静的成分** の ULW-EM を閉じ込める。

このとき重要なのは、informing tensor のモードを

- **静的・超長波成分**（情報ポテンシャル形成に効く）  
- **時間変化の速い成分**（GR 的重力波に対応する）

に分けることである。

- 静的成分：エバネッセント帯で閉じ込め → 銀河内の情報ポテンシャルを増幅  
- 動的成分：適切なモード分解により、銀河を貫通可能な informing radiation として外部へ伝播  
  → 遠方銀河由来の重力波（LIGO/Virgo/KAGRA 観測）と整合

この切り分けにより、

- 銀河回転曲線の説明（静的 FDB 効果）  
- 重力波透過の観測事実（動的 informing radiation）

を矛盾なく共存させることができる。

---

## 7. GR との関係と未解決課題

### 7.1 GR と一致する部分

- 線形領域での波動方程式：\(\Box I_{\mu\nu}=0\)（TT 条件付き）  
- 重力波の偏極：スピン 2・2自由度のみ  
- 四重極放射公式：連星パルサー等の軌道減衰と整合  
- 弱重力・低速極限では \(\Phi_{\text{FDB}}\) を適切に同定することで  
  太陽系テストと GR におけるニュートン極限を再現可能

### 7.2 FDB が GR と異なる・拡張する部分

- informing tensor は「ULW-EM の前波」という具体的な担体を持つ  
- 情報ポテンシャル核 \(K\) は、  
  銀河エバネッセント帯・宇宙網フィラメントの幾何・トポロジーに依存  
- 銀河・宇宙網スケールでの「ループ蓄積」によって  
  DM 的な効果・有効負圧（加速膨張）を説明する余地を持つ

### 7.3 未解決の理論的課題（例）

- informing tensor の完全な作用汎関数（有効作用）の構成  
- 宇宙網を含む一般背景での \(G_{\text{front}}\) の厳密な形  
- 構造形成シミュレーションにおける \(K(\mathbf{x},\mathbf{x}')\) の具体化  
- Bullet Cluster 型事例や Lyman-α forest との詳細な照合

---

## 8. まとめ

- **informing tensor \(I_{\mu\nu}\)** は  
  ULW-EM の **causal wavefront（前波）** のみを通じて  
  物質テンソル \(T^{\text{(mat)}}_{\alpha\beta}\) の情報を伝える  
  スピン2横波・トレースレスなテンソル場である。  
- 線形領域では GR の重力波セクターと同型の方程式・放射公式を持ち、  
  既存の重力波観測と整合し得る。  
- 一方、その静的成分やループ蓄積を通じて形成される  
  情報ポテンシャル \(\Phi_{\text{FDB}}\) は、銀河や宇宙網の構造に依存して  
  GR とは異なる重力的挙動（回転曲線のフラット化、宇宙加速等）を生み出し得る。

informing tensor は、FDB 理論における

> 「重力情報の因果的通知」

を担う中核的な場であり、  
GR における重力波テンソルの自然な一般化（かつ媒質付き具体化）として位置づけられる。
