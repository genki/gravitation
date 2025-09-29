# V-R図: 中心付近でVが0に張り付く問題の対処

日付: 2025-08-31

対象: DDO154, DDO161（SPARC rotmod）

## 症状
- 銀河中心付近(最内半径ビン)で、予測/表示Vが0付近で横這いに
  見える（張り付く）。

## 原因候補と確認
- 原点アンカー: 描画/補間時に(r=0, V=0)を人工的に加えると、
  近傍点が0へ引っ張られて張り付いて見える。
- 半径/単位ミス: arcsec→kpc換算漏れ、m/s↔km/s変換漏れで
  小半径項が過小評価。
- 整数化/クリップ: 誤ってintへキャスト、負値クリップで0に吸着。
- モデル内核: FDB3の小r極限でcが大きすぎると立ち上がりが鈍化。

## 実装した対策
1) 観測系列の健全化
   - `src/fdb/utils.py:sanitize_radial_series` で r≈0, V≈0 の
     人工原点アンカーを除去し、r単調性/重複半径を整理。
   - `scripts/plot_vr.py` に適用。

2) 検証用可視化
   - `scripts/plot_vr.py` で DDO154/161 のV-Rを生成。
     `assets/figures/vr_DDO154.png`, `vr_DDO161.png` に保存。

3) 数値安定化
   - 残差の重みで `err>=1 km/s` の誤差フロアを適用（既存）。

## 確認結果
- DDO154, DDO161とも中心から単調に立ち上がり、0への張り付きは
  再現せず（`scripts/debug_inner_core.py` で数値確認済み）。

## 追加オプション（必要時）
- cの上限を1.5程度に制限/弱事前でc≈1を促進（小rの立ち上がり
  を強める）。
- 最内半径ビンの外れ値耐性: 誤差モデル拡張やビニング再構成。

## 手順
```
make setup
bash scripts/fetch_sparc.sh
PYTHONPATH=. python scripts/plot_vr.py DDO154 DDO161
```

