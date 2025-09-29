# FDB方程式の調整(観測V–Rへの適合を意識)

本リポジトリにおけるFDB（Future Decoherence Bias; ULW-EM起源）の
基本方程式は、2D薄円盤近似で
以下でした:

- (∇² − λ⁻²) φ = β j_EM
- g_FDB = −η ∇φ

今回、各銀河のV–R(obs)へより忠実に適合させるため、理論整合な
拡張を既定パス(オプション)として導入しました。

## 追加・調整点
- 異方Yukawa(幾何反映):
  - k² → kᵀ M k + λ⁻² に相当。`q(軸比)`,`PA`を
    `data/imaging/geometry.json`から取得して適用。
  - 実装: `solve_phi_yukawa_aniso` を既定化(オプション)。
- 照度項(散乱・1/r^p由来の補助加速):
  - I = K_p * j_EM,  K_p(r) ≈ 1/(r² + ε²)^{p/2}
  - g_add = −κ ∇I を g に加算。
  - 物理整合: κ = κ₀/λ とし、全体スケールは η(=A)と同時に拡大。
- 非線形源カップリング(弱):
  - j_eff = j (1 + γ |∇φ|²)^q による1–2回の固定点反復。
  - 形状微調整に寄与。γ=0で無効。

これらをまとめると、加速度は

- g = −η ∇φ + g_add,  かつ φ は(等方/異方)Yukawaで求解。

## 使い方(phys-defaults)
- 複数銀河同時: `scripts/compare_fit_multi.py` に追加。
  - `--phys-defaults`: 異方Yukawa(自動幾何) + 照度(κ=κ₀/λ)
  - `--phys-kappa <κ₀>`: 既定0.3。`irr_alpha = κ₀/λ`で前計算し、
    その後Aでスケール(∝A/λ)。
  - `--phys-nl-gamma <γ>`: 非線形γ(既定0)。

例:
```
PYTHONPATH=. .venv/bin/python scripts/compare_fit_multi.py \
  --names-file data/sparc/sets/nearby.txt \
  --boost 0.5 --boost-tie-lam --auto-geo \
  --phys-defaults --phys-kappa 0.3 \
  --out data/results/multi_fit_nearby_phys.json
```

## 影響(近傍セット)
- 共有最良値例: λ≈8 kpc, A≈100, gas_scale=1.33。
- 総χ²は ≈1.8e5 (従来≈1.83e5)へ小改善。
- 形状面(外側R)での適合が安定。

## 今後の調整余地
- κ₀の系統依存(棒/渦・HII比率)の探索。
- 幾何の不確かさ(軸比/PA)に対するロバストネス評価。
- γ>0時の収束判定と反復回数の自動調整。
- 3D厚み/減衰の近似導入(λ_eff(R)や面密度連動)の検討。
