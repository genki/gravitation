# Two‑Soliton（物質ソリトン＋情報ソリトン）可視化シミュレーション

本ディレクトリは、**V1 表示スタイル（|E|/|B| 背景＋streamlines＋colorbar）**を厳守しつつ、

- 物質ソリトン（advanced EM Hopfion の簡易模型：核）
- 情報ソリトン（retarded EM Hopfion の簡易模型：入射＋再放射）

の **共形時間 η における時間発展**を GIF として生成するための、実行可能な最小パッケージです。

注意：ここでは **共形場の Maxwell（真空・線形）**の枠内で、Bateman 構成に基づく **null electromagnetic field**
（Riemann–Silberstein ベクトル `F = E + iB = ∇(α^p)×∇(β^q)`）を用いて可視化します。
「共鳴」や「核更新」のように見える現象は、合成場の観測量（|E|,|B|等）に現れる干渉・重ね合わせとして生じます。

---

## 1. 概要（物理モデルの要点）

- **時空**：共形平坦な縮小宇宙（共形時間 η）

  $$
  ds^2 = a(\eta)^2(-c^2 d\eta^2 + dx^2 + dy^2).
  $$

  本コードは共形時間 $\eta$ を直接用い、Maxwell 方程式の共形不変性を利用する（という立て付け）で描きます。

- **物質ソリトンA（核）**
  - advanced Hopfion（Bateman場の時間反転として定義）
  - 本実装では Bateman 構成のパラメータを `(p,q)=(1,3)` として選びます（H=3 の代用ラベル）。

- **情報ソリトンB**
  - retarded Hopfion（Bateman場）
  - `(p,q)=(1,1)`（Hopfion）
  - `x=d` から `-x` 方向へ進むように回転して配置します。

- **可視化（V1）**
  - 背景：共形場の `|E|`, `|B|`（3Dベクトルのノルムを `z=0` 断面で表示）
  - 重ね：`z=0` 断面での `E_xy` / `B_xy` streamlines（赤／シアン）
  - colorbar あり
  - 黒背景

---

## 2. 実行環境

- Python 3.9+
- 必要パッケージ：`numpy`, `matplotlib`, `imageio`

### セットアップ例（venv 推奨）

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -r sim/2-soliton/requirements.txt
```

---

## 3. 実行方法

```bash
.venv/bin/python sim/2-soliton/simulate_two_solitons.py
```

出力：

- `out/2-soliton/two_soliton_V1_hopfion_z0_120f.gif`
  - Bateman 構成の 3D 場を評価し、**z=0 断面**を描画します（共形場のまま）。

---

## 4. パラメータ調整ガイド

スクリプト内（`UniverseConfig` ではなく上部の定数）を調整してください：

- 時間区間：`eta_end`、フレーム数：`N_FRAMES`
- 2体系の配置：`d`（情報ソリトンの初期位置）
- “H” に相当させるラベル：`MATTER.p/q` と `INFO.p/q`（Bateman場の指数）
- 空間サイズ：`L`

---

## 5. 次の改善候補

- Hopfion の厳密解（Bateman/Rañada 形式）への差し替え
- H-index と等高線数の 1 対 1 対応を強制する表示規約
- 論文用（白背景・ベクター無し）図版への派生
