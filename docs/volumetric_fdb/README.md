Volumetric FDB: Specification and Implementation Notes

Scope
- Defines volumetric hazard Λ(x) and information potential Φ_eff(x).
- Fixes normalization for Â_y( r̂ ) and high‑k roll‑off.
- Introduces constants C and κ to pin units.
- Adds ULM band model (P/D; formerly ULW l/h) and h‑only (ULM‑P) evaluation assumption for cosmological scales.

Equations (discrete-friendly)
- Λ(x) = (G/c) ∫ ρ(y) Â_y( r̂ ) / |x−y|^2 d^3y
- Φ_eff(x) = −G ∫ ρ(y) Â_y( r̂ ) / |x−y| d^3y
  where r̂ = (x−y)/|x−y| and Â_y integrates to 4π over the unit sphere:
  ∫_Ω Â_y( r̂ ) dΩ = 4π. This keeps the l=0 (isotropic) part equal to 1.

Normalization
- Expand Â_y in real spherical harmonics with mean preserved:
  Â_y( r̂ ) = 1 + Σ_{l=2..lmax} Σ_m a_{lm}(y) Y_{lm}( r̂ ),
  with ∫ Y_{lm} dΩ = 0 for l≥1 and ∫ 1 dΩ = 4π.
- High‑k roll‑off: enforce |Â_y| spectral decay for k≫k0 via angular‑frequency penalty
  and optional spatial prefilter (e.g., Gaussian with σ_k ≥ k0) to satisfy solar‑system nulls.

Shared scale function μ0(k)
- μ0(k) = 1 + ε / (1 + (k/k0)^m), common across galaxies with k0,m satisfying solar‑system constraints.
- Two‑stage fitting: (1) isotropic (Â=1) to estimate μ0(k); (2) fix μ0 and fit Â_y residuals.

Constants and footnotes
- C := G/c (used in Λ). κ := m c^2 (bookkeeping for energy‑scale annotations).
- Use SI internally (m, kg, s) and convert at edges.

Numerical evaluation
- Direct summation (baseline, O(NM)) for small validation grids.
- Method A (tiles + inverse FFT): treat a_{lm} piecewise‑constant per tile; combine 1/r convolutions.
- Method B (tree/FMM): accumulate multipoles with lmax ≤ 4; recurse on an octree.

Band model (ULM‑D / ULM‑P; formerly ULW‑l / ULW‑h)
- ULM‑D (ω < ω_cut): diffusive/non‑propagating; locally reprocessed and absorbed into the isotropic monopole (sum‑rule; angle‑mean 1).
- ULM‑P (ω ≥ ω_cut): propagating; sole contributor to far‑field Λ gradient. Keep angular anisotropy via Â_y.
- Cosmological evaluation uses h‑only; l→h reprocessing contributes to the isotropic baseline.

Validation set and acceptance
- Sphere (uniform): matches GR potential inside/outside to within ≤1% on coarse grids.
- Finite rod: near‑field ~1/r transition to far‑field ~1/r^2.
- Thin disk: in‑plane strengthening with correct sign/magnitude.

Data path and artifacts
- Archive: used_ids.csv, fitted (ε,k0,m), lmax, and statistics of a_{lm}(y) fields.
- Repro: record random seeds, grid spacing, boundary conditions, and kernel regularizers.
