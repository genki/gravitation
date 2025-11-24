# Appendix G: Strong-Lensing H1 Ratio Test (Reproducibility)

1. **Definition**: \(R=\theta_E' c^{2}/(2\pi v_c^{2})\), with \(\theta_E'=\theta_E D_s/D_{ls}\), \(v_c=\sqrt{2}\sigma\).
2. **Distances**: Flat \(\Lambda\)CDM (H\(_0\)=70, \(\Omega_m=0.3\)); \(D_s,D_{ls}\) via astropy.cosmology.
3. **Velocities**:
   - prefer \(\sigma_{\rm SIS}\) → \(v_c=\sqrt2\,\sigma_{\rm SIS}\);
   - else \(\sigma_e=\sigma_{\rm ap}(R_{\rm ap}/R_e)^{-0.066}\) with \(R_{\rm ap}=\)1.5″ (SDSS) / 1.0″ (BOSS, BELLS); \(v_c=\sqrt2\,\sigma_e\).
4. **Statistics**: \(m_R=\mathrm{median}(\log_{10}R)\); \(s_R=1.4826\,\mathrm{MAD}\).
5. **Pass criterion**: \(|m_R|\le0.03\) dex and \(s_R\le0.10\) dex.
6. **QC**: If a catalog lacks \(R_e\), bracket it in \([0.7'',2.0'']\) and report how many objects rely on that interval (currently zero). Survey-wise medians are published for transparency; e.g., dividing BOSS velocities by 1.10 would zero its median, but we do not apply that factor.
7. **Results (observed, 2025-11-24)**: All=+0.0009 dex / 0.1057 (N=235); SDSS=−0.0003 / 0.0175 (N=132); BELLS=+0.0777 / 0.1367 (N=63); BOSS=+0.0846 / 0.1497 (N=40); SDSS+BELLS=+0.0025 / 0.0681 (N=195).
7. **Code & data**: `analysis/h1_ratio_test.py` (entry point), loaders in `analysis/h1_strong_lens.py`; inputs under `data/strong_lensing/` (including `BOSS_full_table.csv` from Shu+2017 plus Playwright-archived HTML in `data/strong_lensing/sources/`). Run with `PYTHONPATH=. python analysis/h1_ratio_test.py`.
8. **Figure**: `figures/h1_violin.png` (survey-wise \(\log_{10}R\) violin; 0‑dex line and medians).
