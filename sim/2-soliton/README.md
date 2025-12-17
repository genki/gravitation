# Two‑Soliton（物質ソリトン＋情報ソリトン）可視化シミュレーション

本ディレクトリは、**V1 表示スタイル（|E|/|B| 背景＋streamlines＋colorbar）**を厳守しつつ、

- 物質ソリトン（advanced EM Hopfion の簡易模型：核）
- 情報ソリトン（retarded EM Hopfion の簡易模型：入射＋再放射）

の **共形時間 η における時間発展**を GIF として生成するための、実行可能な最小パッケージです。

注意：ここでの場は **定性的可視化**のための簡易モデルであり、厳密な Maxwell–Hopfion 解（Bateman/Rañada 等）ではありません。

---

## 1. 概要（物理モデルの要点）

- **時空**：共形平坦な縮小宇宙（共形時間 η）

  $$
  ds^2 = a(\eta)^2(-c^2 d\eta^2 + dx^2 + dy^2).
  $$

  本コードは共形時間 $\eta$ を直接用い、Maxwell 方程式の共形不変性を利用する（という立て付け）で描きます。

- **物質ソリトン（核）**
  - advanced EM Hopfion（の簡易模型）
  - 初期 H-index = `h0`
  - 共鳴時刻 `eta_star` で **H → H+1**
  - エネルギー分布（|E|, |B|）は **等方的**

- **情報ソリトン**
  - retarded EM Hopfion（の簡易模型）
  - 入射：固定中心から半径 `R=c*η` の殻として伝播
  - 拡散：殻幅増大＋振幅減衰（希薄化）
  - 共鳴後：物質核中心から **再放射**

- **可視化（V1）**
  - 背景：|E|, |B|（imshow）
  - 重ね：E/B の streamlines（赤／シアン）
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

- `sim/2-soliton/out/two_soliton_V1_exact_fixedsim_60f.gif`

---

## 4. パラメータ調整ガイド

スクリプト内（`UniverseConfig` ではなく上部の定数）を調整してください：

- 初期 H-index：`h0`
- 共鳴時刻：`eta_star`
- 再放射の強さ：`A_reemit0`
- 情報ソリトンの希薄化：`alpha_decay`, `sigma_growth`
- 空間サイズ：`L`
- フレーム数：`N_FRAMES`

---

## 5. 次の改善候補

- Hopfion の厳密解（Bateman/Rañada 形式）への差し替え
- H-index と等高線数の 1 対 1 対応を強制する表示規約
- 論文用（白背景・ベクター無し）図版への派生

