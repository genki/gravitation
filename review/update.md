# FDB 理論アップデート指示 — 形状依存の四重極“情報ポテンシャル”拡張

> 目的：**球状では GR と同等**、**ディスク／棒では中心向きの追加“見かけ加速度”**が自然に出るよう、  
> FDB の第一原理（将来記録率 Λ に基づく情報ポテンシャル）を **最小限の論理的拡張**で更新する。

---

## 0. 要約（今回の変更点）

- **等方核**（従来：\(K_0(\mathbf{r})=1/|\mathbf{r}|\)）に、**等方平均ゼロの四重極成分**を追加：
  \[
  \boxed{\;K(\mathbf{r};\mathbf{n},\alpha)=\frac{1}{|\mathbf{r}|}\Big[\,1+\alpha\,g(|\mathbf{r}|)\,P_2\!\big(\hat{\mathbf{r}}\!\cdot\!\mathbf{n}\big)\Big]\;}
  \]
  ここで \(P_2(u)=\tfrac12(3u^2-1)\)。追加項の**角度平均はゼロ**のため、球では等方核を保ちます。
- **形状ディレクター \(\mathbf{n}(\mathbf{y})\)** と **異方強度 \(\alpha(\mathbf{y})\)** を、**潮汐テンソル**（球で消える）から構成。
- **超長波のみ有効**（太陽系では無効）：\(g(r)\) は銀河スケールでのみ非ゼロ、**高 \(k\)** で消える。
- これにより  
  **(i) 球状⇒GR 同等／(ii) ディスク面内⇒中心向き追加／(iii) 棒軸方向⇒中心向き追加／(iv) 楕円外縁⇒GR より強め**  
  の4性質を **第一原理の整合のまま**成立させる。

---

## 1. 第一原理式（静的・弱場近似）の更新

FDB の情報ポテンシャル（見かけ）：
\[
\Phi_{\rm eff}(\mathbf{x}) \equiv \frac{U_{\rm info}}{m}
\;=\; -\,G\!\!\int\! \rho(\mathbf{y})\,K\big(\mathbf{x}-\mathbf{y};\,\mathbf{n}(\mathbf{y}),\alpha(\mathbf{y})\big)\,d^3y.
\]

- **核の定義**（本更新）：
  \[
  K(\mathbf{r};\mathbf{n},\alpha)=\frac{1}{r}\Big[1+\alpha\,g(r)\,P_2(\hat{\mathbf{r}}\!\cdot\!\mathbf{n})\Big],
  \quad r=|\mathbf{r}|.
  \]
- **形状ディレクターと強度**（球で消える構成）：
  \[
  Q_{ij}(\mathbf{y})\equiv \partial_i\partial_j\Phi_N(\mathbf{y})-\frac{\delta_{ij}}{3}\nabla^2\Phi_N(\mathbf{y}),
  \quad \|Q\|=\sqrt{Q_{ij}Q_{ij}},
  \]
  \[
  \mathbf{n}(\mathbf{y})=\text{eigvec}_{\max}\{Q(\mathbf{y})\},\qquad
  \alpha(\mathbf{y})=\lambda_{\rm aniso}\,\frac{\|Q(\mathbf{y})\}}{\|Q\|_{\rm ref}+q_{\rm floor}}.
  \]
  - \(\Phi_N\)：**バリオン**（Υ\_★ とガス）から解いたニュートンポテンシャル  
  - **球対称**なら \(Q=0\Rightarrow \alpha=0\)（自動で等方核に戻る）

- **スケール関数**（超長波のみ有効）：
  \[
  g(r)=\exp\!\Big[-(r/\ell_0)^2\Big]\quad\text{（代表例）},\qquad
  \text{フーリエでは }\; \mu_2(k)=\exp\!\big[-(k/k_0)^{m}\big],\; k_0=\ell_0^{-1},\;m\ge 2.
  \]

> **注**：等方平均 \(\int P_2\,d\Omega=0\) のため、追加項は**角度平均で消失**。これが球・太陽系テストの安全弁。

---

## 2. 4 性質の理論的整合（符号と帰結）

- **球状**：\(Q=0\Rightarrow \alpha=0\)。核は \(1/r\) に戻り、**GR 弱場と同等**。
- **ディスク**（法線 \(\mathbf{n}\)）：**面内**では \(\hat{\mathbf{r}}\!\cdot\!\mathbf{n}=0\Rightarrow P_2=-1/2\)。  
  \(\Delta\Phi\propto -G\!\int\rho\,\alpha g\,P_2<0\) ⇒ **中心向きの追加**（面直方向は弱化寄り）。
- **棒**（横断面の \(\mathbf{n}\) 束）：横断面平均でも \(\langle P_2\rangle\approx -1/2\) が残る ⇒ **軸方向の収束**。
- **楕円**：中心はほぼ球 ⇒ 追加ほぼゼロ。外縁は扁平 ⇒ \(\alpha>0\) で **GR より強め**。  
  ⇒ **V–R** は中心 GR、外側で上振れ傾向。

---

## 3. 制約・整合（破綻防止のガードレール）

1. **太陽系 Null**：\(\mu_2(k)\to 0\)（高 \(k\)）を保証。\(k_0\) は**kpc スケール以下**に設定。  
2. **角平均ゼロ**：等方平均で必ず \(K\to 1/r\)。  
3. **正値性**：記録率 \(\Lambda\ge 0\) を保つため \(|\alpha g|\ll 1\)。  
4. **保存場**：\(\Phi_{\rm eff}\) はスカラー。**渦なし**・保存力で見かけの保存則が保たれる。  
5. **レンズ整合**：\(\Phi_{\rm eff}\) は**無色**。異方項は**シア**を与えるが小さく保つ。  
6. **全銀河共通**：\((\lambda_{\rm aniso},\ell_0,m)\) は原則 **共通**。ファインチューニング禁止。

---

## 4. 具体パラメータ（推奨既定と推定方法）

- **グローバル**（全銀河共通）  
  - \(k_0=\ell_0^{-1}\in[0.02,0.10]\,\mathrm{kpc^{-1}}\)（例）  
  - \(m\in\{2,3,4\}\)（高 \(k\) 収束の強さ）  
  - \(\lambda_{\rm aniso}\in[0,\,\mathcal{O}(1)]\)（CV で同定）  
  - \(\|Q\|_{\rm ref}\)：**規格化**（例：サンプルの中央値）
- **ローカル**（銀河ごとに推定）  
  - Υ\_★,disk / Υ\_★,bulge（**点±68%CI** 表記）  
  - ガス比 `gas_scale`（狭い事前、例 1.33±0.1）

---

## 5. 実装（推奨パイプライン）

### 5.1 物理場の前計算
1. **バリオン場**：表面密度（星・ガス）→ 3D/薄板近似で \(\rho_b\)。  
2. **\(\Phi_N\)**：Poisson を解いてニュートンポテンシャル。  
3. **潮汐テンソル**：\(Q_{ij}\) を計算（スムージング半径は \(\ell_0\) と同程度）。  
4. **\(\mathbf{n},\alpha\)**：最大固有ベクトルで \(\mathbf{n}\)、ノルムから \(\alpha\)（小さい領域では \(\alpha\to 0\)）。

### 5.2 核の適用（2案）
- **（A）実空間：局所異方核の直接積分**  
  \(\Phi_{\rm eff}(\mathbf{x})=-G\sum_{\mathbf{y}}\rho(\mathbf{y})\,K(\mathbf{x}-\mathbf{y};\mathbf{n}_\mathbf{y},\alpha_\mathbf{y})\,\Delta V\)  
  → 木法／FMM で高速化（異方項は短レンジ \(g(r)\) のため局所和で十分）。
- **（B）近似フーリエ：局所一様近似タイル**  
  \(\mathbf{n},\alpha\) をタイル状に**局所一定**とみなし、各タイルで  
  \(\Phi_{\rm eff}(\mathbf{k})=-\frac{4\pi G}{k^2}\!\big[\mu_0(k)+\mu_2(k)\,(\hat{\mathbf{k}}\!\cdot\!\mathbf{n})^2-\tfrac{1}{3}\mu_2(k)\big]\rho(\mathbf{k})\)  
  を適用し逆 FFT。タイル境界でブレンド。

> **注**：\((\hat{\mathbf{k}}\!\cdot\!\mathbf{n})^2-\tfrac{1}{3}\) は \(P_2\) の \(k\)-空間表現（TT 射影）。  
> 球では \(\mathbf{n}\) 未定義だが \(\alpha=0\) なので不要。

---

## 6. フィッティング／SOTA 反映

- **CV グリッド**：\((\lambda_{\rm aniso},\,k_0,\,m,\,gas\_scale)\) を共有パラメータとして探索（**全銀河共通**）。  
- **誤差モデル**：`rχ²=χ²/(N−k)` に統一。Student‑t/Huber オプション、速度誤差 floor+jitter で rχ²≈1。  
- **公平比較**：AICc は **同一 n**（共通データ点）で計算。per‑galaxy 勝率（ΔAICc<0）を併記。  
- **表示**：M/L は **Υ\_★**（表示層）／`ML_star_*`（データ層）。代表 3 列パネル（GR+DM／MOND／FDB）を更新。  
- **使用 ID**：`used_ids.csv` を CV/SOTA からリンクし、再現性を確保。

---

## 7. 単体テスト（受入基準）

1. **球対称質量**（プラマーモデル等）：\(\max|\Delta a|/|a_{\rm GR}|<10^{-4}\)（数値誤差内）。  
2. **薄円盤**（指数円盤）：面内で \(\Delta a_R>0\)、面外で \(|\Delta a_z|\) は小。  
3. **棒（Ferrers bar）**：棒軸方向で \(\Delta a_\parallel>0\)。  
4. **複合（楕円）**：中心は GR 一致、外縁で \(V(R)\) が上振れ（μ(k) 既定で一貫）。  
5. **太陽系相当**：\(k\sim 1/\mathrm{AU}\) で \(\mu_2\to 0\)（Shapiro/偏向に変化なし）。  
6. **レンズ**：等色性（波長独立）・シアの過剰が既知許容内。

---

## 8. 既定値（初期デプロイ）

- \(k_0 = 0.05\ \mathrm{kpc^{-1}}\), \(m=2\), \(\lambda_{\rm aniso}=0.3\), \(q_{\rm floor}=0.05\,\|Q\|_{\rm median}\).  
- ガス倍率 \(1.33\pm0.1\)。Υ\_★ は色–SPS 事前＋観測で更新（点±68%CI 表記）。

---

## 9. 注意事項（理論整合）

- **“重力”の語は使用しない**：本拡張は **“将来記録率の角度依存”** による **見かけのポテンシャルの偏り**。  
- **等価原理**：\(\Phi_{\rm eff}\) は質量に比例し、加速度は質量に独立。  
- **無信号原理**：\(\alpha,\mathbf{n}\) は**過去のバリオン配置**から構成。能動制御で場を即時操作できない。

---

## 10. コミット／実装メモ

- `core/fdb_kernel.py`: `K_iso(r)=1/r`, `K_aniso(r,n,alpha)=K_iso*(1+alpha*g(r)*P2(dot(rhat,n)))`.  
- `core/shape_tensor.py`: \(Q_{ij}\) の計算・スムージング・固有分解。  
- `fit/cv_shared.json`: 共有 \((\lambda_{\rm aniso},k_0,m,gas)\) のグリッド／事前・結果の単一ソース化。  
- `reports/*`: AICc+(n,k) 表記統一、`rχ²=χ²/(N−k)` 注記、Υ\_★ 表示・GR+DM/MOND/FDB の 3 列比較。  
- `data/used_ids.csv`: 解析に用いた ID の全量公開（noBL/withBL の別）。

---
