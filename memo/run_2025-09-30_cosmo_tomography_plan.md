# 宇宙論（WL 2PCF）トモグラフィ拡張計画（タスクC-1）

## 目的
- KiDS-450 の tomographic bins 全体に対して ξ± を正式に評価し、ΛCDM vs Late‑FDB の ΔAICc を **同一共分散**のもとで算出する。

## 設計（最小版）
- データ: `data/weak_lensing/kids450_xi_tomo*.yml` 形式で各ビンの ξ±/共分散を格納（tomo1-1 は既存）。
- 予測: `scripts/reports/make_cosmo_formal.py` の `compute_wl_predictions` を拡張し、複数 z_s（もしくは n(z)）を扱う。
  - n(z) 未整備の段階では、各ビンの代表 z_s を利用（後に n(z) に置換）。
- 評価: 観測ベクトルをビン横断で結合し、共分散もブロック結合して χ²/AICc を算出。

## 実装ステップ
1. YAML スキーマの定義（tomoX-Y 用）とプレースホルダ生成スクリプト（未入手ビンは disabled）。
2. `compute_wl_predictions` に複数ビン対応の引数（例: `z_sources: List[float] | n_of_z: List[Array]`）。
3. 連結ベクトル/共分散での χ²/AICc を算出（k=0前提、後にIAなど追加）。
4. SOTA カードに「tomo全ビン（正式）」を追加（ΔAICc・rχ²・リンク類）。

## 受け入れ基準（DoD対応）
- すべてのビンで **|ΔAICc|≤10** の範囲に収束（“壊さない”）。
- CLASS 設定・μ(a,k)・ビン仕様は JSON で保存し、SOTA からリンクできること。

