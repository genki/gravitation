# 単一銀河系ベンチマーク検証 — NGC 3198（FDB≡Future‑Decoherence‑Bias, DMなし）

この手順書は、SOTA準拠（h‑only＋界面放射Σモデル、共有 μ0(k) 固定）で NGC 3198 を対象にフェアな横並び比較（GR/GR+DM/MOND/FDB[DMなし]）を行うための実行手順です。実データ（SPARC/THINGS/HALOGAS/Hα）の投入有り・無しに関わらず、再現可能な最小セットから始められます。

## 前提
- 共有 μ0(k) を固定: ε=1, k0=0.2 [kpc⁻¹], m=2, gas_scale=1.33
- 太陽系 Null（μ0→1）のログを保存
- フェア条件: 同一 n・同一誤差（clip(0.03×Vobs, 3..7 km/s)）・同一ペナルティ（AICc/WAIC/ELPD）

## ステップ

### 1) clean/固定μ0でのCV（nや誤差の整備）
```
PYTHONPATH=. ./.venv/bin/python scripts/cross_validate_shared.py \
  --names-file data/sparc/sets/clean_for_fit.txt \
  --out-prefix cv_shared_summary \
  --robust huber \
  --fixed-mu-eps 1 --fixed-mu-k0 0.2 --fixed-mu-m 2 --fixed-gas-scale 1.33
# 太陽系Nullログ: data/results/solar_null_log.json
```

### 2) NGC 3198 の前処理（座標・幾何・データ）
- SPARC（3.6µm・回転曲線）を既存 reader で取得（scripts/fit_sparc_fdbl.py の API を利用）。
- THINGS/HALOGAS の HI 面密度→体積化（近似可）、Hα→n_e プロキシ（不足時は SFR マップ代替）。
- セファイド距離・tilted‑ring 幾何を固定（外縁warpは2–3区間分割）。

### 3) 二層の構成（等方＝質量／追加＝界面）
- 等方側: ρ_iso = ρ★ + gas_scale·ρ_gas（減衰やWを掛けない）
- 追加側: Σモデルの薄層化 S(r) を構成: ω_cut=ω_p(n_e) → H_cut, n, δ_ε → S(r)
- ρ_eff = ρ_iso + α_esc·S（FFT/FMMで Φ_eff を評価）

実装API（最小）
```
from fdb.composite import build_layers
rho_iso, S, rho_eff, meta = build_layers(rho_star, rho_gas, n_e_proxy, spacing,
                                         gas_scale=1.33, alpha_esc=alpha, ell_star=ell, omega_star=omega_star)
```

### 4) 角度核（Lambert→前方化）のアブレーション
- `--beta-forward` は界面照度項 `irradiance_log_bias` と 1/r 加速度 `line_bias_accel` に前方化ウエイト \((1+β \cos\theta)/(1+β/2)\) を掛ける。β=0 が従来の Lambert、0<β≤1 で外縁・棒方向を強調。
- 角度は `--aniso-angle` で指定した棒位相（deg）を使用し、`--auto-geo` を併用すると `data/imaging/geometry.json` の位置角が自動で流用される。
- 共有検証では β=0.0 と β≈0.3 を比較し、ΔAICc/ELPD・外縁残差を記録する。例:

  ```sh
  # Lambert (β=0) 基準
  PYTHONPATH=. python scripts/compare_fit_multi.py \
    --names NGC3198 --fdb-mode surface --beta-forward 0.0 \
    --aniso-angle 225 --auto-geo --out results/ngc3198_beta0.json

  # 前方化 β=0.3（棒方向を強調）
  PYTHONPATH=. python scripts/compare_fit_multi.py \
    --names NGC3198 --fdb-mode surface --beta-forward 0.3 \
    --aniso-angle 225 --auto-geo --out results/ngc3198_beta03.json
  ```

  実行後は rχ²・ΔAICc とともに前方化ログ (`meta.beta_forward`) をメモへ記載し、Lambertとの差分を表にまとめる。

### 5) 横並び比較（GR/GR+DM/MOND/FDB[DMなし]）
- AICc/WAIC/ELPD と rχ²=χ²/(N−k) を掲載（同一 n/誤差/ペナルティ）。
- 外縁で 1/r² 復帰の確認（HALOGAS外挙動の比較）。

### 6) 検証図
- 三面図: ρ★, ρ_gas, n_e/ω_cut, S(r), Φ_eff の断面
- 回転曲線分解: v_N²（等方）と δv_FDB²（追加）
- 残差地図: 面内（棒方位・外縁）方向と Hα 分布の相関

## 参考コマンド（デモ図の生成）
```
# 二層デモ（等方＋追加）
PYTHONPATH=src:. python3 scripts/demos/two_layer_demo.py
# 角度核（Lambert→前方化）
PYTHONPATH=src:. python3 scripts/demos/boundary_kernel_demo.py
# 残差ヒートマップ（棒/円盤の例）
PYTHONPATH=src:. python3 scripts/qa/make_residual_demos.py
# SOTA の再生成
PYTHONPATH=src:. python3 scripts/build_state_of_the_art.py
```

---

- 出力: server/public/reports/bench_ngc3198.html（次段スクリプトで自動生成予定）
- 公平比較・監査: scripts/qa/audit_consistency.py（(N,k), rχ²）

***

再現ノートブックや本番フィット（SE‑FDBのg(r)を compare_fit_multi へ統合）は、次段の統合パッチで追加します。
