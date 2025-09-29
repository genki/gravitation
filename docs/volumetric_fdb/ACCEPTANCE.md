Acceptance Criteria (Go Sign)

Basics
- Sphere (uniform): Φ matches GR inside/outside within ≤1% on coarse grids; tighter with refinement.
- Rod (finite): near-field ~1/r, far-field ~1/r^2 transition is reproduced.
- Thin disk: in-plane strengthening with correct sign and expected magnitude trend.

Generalization and Fairness
- Common n, error model (Student‑t/Huber + velocity floor), and penalties (AICc/WAIC/LOO) across GR+DM/MOND/FDB.
- Achieve ΔAICc ≤ −10 vs GR+DM for a significant subset; WAIC/ELPD consistent.
- Prospective test: with common μ0(k) and Â_y fixed, fit only Υ★ and gas_scale and retain wins.

Reproducibility
- Archive used_ids.csv, fitted (ε,k0,m), lmax, and distribution statistics of a_{lm}(y).
- Log grid spacing, boundary conditions, random seeds, and kernel regularizers.

