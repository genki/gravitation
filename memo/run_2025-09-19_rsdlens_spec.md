# 2025-09-19 軽量尤度データ仕様ドラフト

## 対象
- **RSD (fσ₈)**: BOSS / eBOSS / DESI preview 等で公開されている (z, fσ₈, σ) テーブル
- **弱レンズ 2PCF**: KiDS / DES Y3 の (θ, ξ_+, ξ_−, Cov) ブロック
- **CMB ピーク高さ/比**: Planck 2018 TT/TE/EE summary statistics（peak位置と高さ）

## YAML 形式案
```yaml
z: [0.15, 0.32, 0.57]
values: [0.44, 0.43, 0.43]
covariance:
  - [0.01, 0.002, 0.001]
  - [0.002, 0.015, 0.003]
  - [0.001, 0.003, 0.02]
meta:
  dataset: "BOSS DR12"
  observable: "f_sigma8"
  reference: "Alam+2017"
```
`meta` は脚注用の出典と可視化パラメタを保持。

## モデル生成
- 初期版では CLASS から得られる fσ₈、D_A、H(z) などを既存 `scripts/eu/class_validate.py` の出力からサンプリング。
- `scripts/eu/lightweight_likelihood.py` に callable を追加し、CLASS の結果ファイルまたは数表を読み込むインターフェイスを提供する。

## 次アクション
1. 宇宙論チーム（user, ChatGPT(5 Pro)）とフォーマット/参照文献の確認ミーティング設定。
2. データ取得スクリプト（e.g., `scripts/eu/fetch_rsdlens_data.py`）の雛形を作成。
3. `lightweight_likelihood.py` に RSD/弱レンズ/CMB 向けモデル evaluator を追加し、`make repro` への組み込み計画を策定。

