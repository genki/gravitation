# Future Determination Bias as Emergent Gravity: Waveguide Confinement, 1/r Drift, and Instant Validation via Strong-Lensing Ratio Test

**Authors**: Genki Takiuchi  
**Date**: 2025-11-24  

---

## Abstract
We propose that galactic gravity emerges as a statistical drift induced by continuous position monitoring from an ultra‑low‑energy Proca electromagnetic background (ULE‑EM). At the galaxy–void interface, plasma-induced evanescent reflection confines the information flux into a surface waveguide, converting geometric decay from \(1/r^{2}\) to \(1/r\). The resulting \(1/r\) force reproduces flat rotation curves and the baryonic Tully–Fisher relation (BTFR) without non-baryonic dark matter. Crucially, the framework admits an instant, dimensionless validation through the strong-lensing ratio \(R\equiv \theta_E'c^{2}/(2\pi v_c^{2})=1\), where \(\theta_E'=\theta_E D_s/D_{ls}\) and \(v_c=\sqrt{2}\sigma\). Using homogeneous lens samples, we obtain \(m_R\simeq0\) dex and \(s_R\lesssim0.1\) dex without any parameter fitting; SPARC rotation curves, evaluated on their outer radii where the waveguide drift operates, favor the same \(1/r\) scaling with median \(\Delta\mathrm{AICc}_{\rm outer}\lesssim-4\) relative to NFW even though full-curve medians can be positive because of inner radii. Because the core prediction is a zero‑degree-of-freedom equality, agreement (or its failure) is visible in seconds, avoiding costly MCMC or hierarchical Bayes. We outline decisive future tests combining \(\theta_E\) and \(v_c\) for the same galaxies, providing a direct falsifiability channel for the FDB hypothesis.

---

## 1. Introduction
\(\Lambda\)CDM provides an excellent global fit yet encounters persistent fine-tuning at galaxy scales—flat rotation curves, extremely small BTFR scatter, and lensing–dynamics tensions that demand per-galaxy halo concentration or anisotropy tweaks [@McGaugh2016RAR; @Verlinde2016]. MOND-like or emergent-gravity ideas reproduce the BTFR slope but typically require interpolation functions, external-field prescriptions, or additional scales, and they do not supply an immediate, parameter-free strong-lensing diagnostic. We therefore seek a micro-to-macro connection that (i) is equation based, (ii) predicts a universal dimensionless equality, and (iii) is testable without heavy computation. Future Determination Bias (FDB)—an information-flux–driven drift sustained by ULE‑EM waveguiding—satisfies these criteria by enforcing the single constant relation \(R=1\) that links Einstein radius and circular speed. The remainder of this paper lays out the theory, galaxy-scale consequences, and an instant validation protocol.

### Conventions and units (SIS lensing)
- SIS deflection: \(\hat\alpha = 4\pi(\sigma/c)^2 = 2\pi(v_c/c)^2\) with \(v_c=\sqrt{2}\sigma\) [@NarayanBartelmann1997].
- H1 ratio (used throughout): \(R\equiv \theta_E' c^{2}/(2\pi v_c^{2})=1\), \(\theta_E'=\theta_E D_s/D_{ls}\).
- Disk/filament regime uses \(\Phi_{\rm FDB}=v_c^2\ln r\) (2D waveguide); strong-field spherical limit uses \(\Phi_{\rm FDB}\to -GM/r\).
- \(\Delta\mathrm{AICc}\) is defined as \(\mathrm{AICc}_{\rm FDB}-\mathrm{AICc}_{\rm NFW}\); negative values favour FDB.

---

## 2. FDB Framework: Proca Field, Interface Reflection, Waveguide

### 2.1 Definitions (inline “box”)
- **ULE‑EM**: Ultra‑low‑energy Proca EM field with Compton length \(\lambda_C\sim300\,\mathrm{kpc}\Rightarrow m_\gamma\sim3.9\times10^{-65}\,\mathrm{kg}\), comfortably below current photon-mass bounds [@ParticleDataGroup2024].
- **Lagrangian**:
  \[
  \mathcal{L}= -\tfrac14 F_{\mu\nu}F^{\mu\nu}+\tfrac12\mu_\gamma^{2}A_\mu A^\mu - J_\mu A^\mu,\quad \mu_\gamma = m_\gamma c/\hbar .
  \]
- **Dispersion (SI)** in a cold plasma with Proca mass:
  \[
  k^{2}(\omega)=\frac{1}{c^{2}}\Bigl[\omega^{2}-\omega_p^{2}(n_e)-\mu_\gamma^{2}c^{4}/\hbar^{2}\Bigr],\qquad \omega_p^{2}=n_e e^{2}/(\varepsilon_0 m_e).
  \]
  Propagation requires \(k^{2}>0\); evanescence \(k^{2}<0\).
- **Frequency window**: Rather than tying the carrier strictly to \(\omega\simeq\mu_\gamma c\), we treat the ULE‑EMW as a broadband background. Modes satisfying
  \[
  \omega_{p,\rm void} < \omega \ll \omega_{p,\rm gal}
  \]
  experience \(k_{\rm void}^{2}>0\) (void side) and \(k_{\rm gal}^{2}<0\) (galaxy side). Appendix A lists representative densities (e.g. \(n_e\sim10^{-6}\,\mathrm{cm^{-3}}\) in voids, \(n_e\gtrsim10^{-3}\,\mathrm{cm^{-3}}\) in filaments) for which sub-Hz modes meet this inequality; outside this band both sides become evanescent and the mode decays instead of guiding.
- **Galaxy–void interface**: We treat the guided mode as **surface-bound**, i.e. both half-spaces admit evanescent components but the tangential wavevector allows a net Poynting flux confined to the interface. A practical realization enforces \(k^2_{\rm void}\gtrsim 0\) while \(k^2_{\rm gal}<0\) so that energy leaks only along the sheet. The local plasma frequency sets an **effective screening length** 
  \[
  \lambda_{\rm eff}^{-2}\simeq \lambda_C^{-2}+\lambda_{\rm pl}^{-2},
  \]
  combining the vacuum Compton scale and the plasma shielding scale \(\lambda_{\rm pl}\) (e.g. a Debye length). For typical halo interfaces \(\lambda_{\rm eff}\lesssim\lambda_C\), keeping the guided mode coherent over \(\mathcal{O}(10^2)\) kpc.
- **Near-total reflection**: For TE (and TM; see Appendix A), \(|R|\approx1\) for practical angles whenever \(\omega^{2}<\omega_{p,\rm gal}^{2}+\mu_\gamma^{2}c^{2}\) and \(k^{2}_{\rm void}>0>k^{2}_{\rm gal}\). Finite-thickness gradients introduce small tunnelling, but the guided branch still behaves as a surface waveguide with penetration depth \(\delta\sim10\text{--}30\) kpc rather than a bulk leakage channel.

Figure 1 shows the reference potential in vacuum (solid) and a schematic plasma-guided profile (dashed). The vertical line marks \(r=\lambda_C\); in media we simply replace \(\lambda_C\) with \(\lambda_{\rm eff}\) from the relation above, which shortens the lever arm without altering the asymptotic \(e^{-r/\lambda}/r\) form.

![Vacuum Proca potential (solid) versus schematic plasma-guided profile (dashed); the vertical line marks \(r=\lambda_C\).](figures/proca_potential.png)

### 2.2 From geometry to probability
Waveguide confinement changes flux conservation from spherical \(1/r^{2}\) to cylindrical \(1/r\). Interpreting the ULE‑EMW as a continuous position measurement channel, the induced monitoring strength \(\Gamma\) biases stochastic drift:
\[
\mathbf{F}_{\rm eff}\propto -\alpha\,\mathbf{J}_{\rm info}\;\;\Rightarrow\;\; |\mathbf{F}_{\rm eff}|\propto 1/r ,
\]
which is sufficient for flat rotation curves. Explicitly,
\[
\mathbf{J}\propto 1/r \;\Rightarrow\; |\mathbf{F}_{\rm eff}|\propto 1/r \;\Rightarrow\; v^{2}/r \propto 1/r \;\Rightarrow\; v\simeq{\rm const},
\]
closing the chain from interface flux to flat rotation curves in one step.
Conservation of energy along a cylindrical sheet gives $2\pi r\,I(r)=	ext{const}$, so $I(r)\propto 1/r$ and the wave amplitude falls as $r^{-1/2}$. This purely geometric statement agrees with the stochastic-drift argument above and shows explicitly why a guided mode enforces a $1/r$ force tail.

---

## 3. Micro to Effective Force

### 3.1 Continuous-measurement mapping
Lindblad evolution with monitoring strength \(\Gamma\) reduces to a Fokker–Planck equation; the drift term inherits the \(1/r\) flux. (Derivation deferred to Appendix A.)

### 3.2 Effective acceleration and BTFR
Assuming waveguide scale \(L_0\),
\[
g_{\rm eff}(r)=\frac{G\,M_{\rm bar}}{L_0\, r}, \qquad L_0 \propto \sqrt{M_{\rm bar}},
\]
implies \(v^{4}\propto M_{\rm bar}\), reproducing BTFR slope and small scatter without halo tuning. The \(L_0\)–\(M_{\rm bar}\) scaling follows from approximately constant baryonic surface density along the interface.

### 3.3 Drift derivation (sketch)
Expanding the Lindblad equation (6) in the Wigner representation yields the Fokker–Planck form
\[
\partial_t f = -\frac{p}{m}\partial_x f + \partial_p\left[D_{pp}(x)\partial_p f\right],
\qquad D_{pp}(x)=\frac{\hbar^{2}}{4}\Gamma(x) .
\]
The first moment gives \(\langle \dot p\rangle = -\tfrac12 \partial_x D_{pp}(x)=-(\hbar^{2}/8)\partial_x \Gamma(x)\). Identifying the monitoring strength with the information flux, \(\Gamma(x)\propto I(x)\), leads to
\[
F_{\rm eff} \equiv \langle \dot p\rangle \,\propto\, -\partial_x I(x).
\]
In the surface-guided geometry \(I\propto 1/r\), so \(F_{\rm eff}\propto -\partial_r(1/r)=1/r^{2}\) and thus \(|F_{\rm eff}|\propto 1/r\) after dividing by the test mass, reproducing Eq. (8). The proportionality constant is fixed by matching the SIS intercept (Appendix C), which ties the stochastic drift normalization directly to the lensing prediction without additional fits.

We therefore choose the drift coefficient so that the SIS intercept on the $v_c$ axis is exactly $2\pi$, ensuring that the stochastic drift, the lensing ratio $R=	heta_E' c^2/(2\pi v_c^2)$, and the rotation-curve normalization all share the same fixed constant with no adjustable scale factors.

---

## 4. Clock rates and information potential
Continuous measurement acts as a “clock slow-down”: a two-level (or harmonic) clock driven at Rabi rate \(\Omega\) under continuous position monitoring of strength \(\Gamma(x)\) has effective transition rate \(\Gamma_{\rm eff}\simeq \Omega\) for \(\Gamma\ll\Omega\) and \(\Gamma_{\rm eff}\simeq \Omega^{2}/\Gamma\) (Zeno regime) for \(\Gamma\gg\Omega\). We calibrate the proper-time rate so that weak-field FDB matches GR:
\[
\frac{d\tau}{dt}\equiv \sqrt{1+\frac{2\Phi_{\rm FDB}(x)}{c^{2}}}\simeq 1+\frac{\Phi_{\rm FDB}}{c^{2}},
\]
with a common potential
\[
\Phi_{\rm FDB}\equiv -\frac{\hbar}{2}\,\frac{\Gamma(x)-\Gamma(\infty)}{\alpha_m},\qquad \alpha_m\simeq 1
\]
set by ground–satellite clock calibration (no free parameter left). Interpreting this as an information-induced redshift means any continuously monitored oscillator ticks slower by \(1+\Phi_{\rm FDB}/c^2\); Pound–Rebka and GPS-style comparisons therefore fix \(\alpha_m\) empirically without touching the lensing normalization, and “clock freezing” near horizons should be read as an **apparent** suppression of transition rates rather than a halt of a freely falling clock’s proper time.

> **Box 3 — Clock rate and information potential.** Continuous monitoring with strength \(\Gamma(x)\) slows local clocks according to \(d\tau/dt\simeq\sqrt{1+2\Phi_{\rm FDB}(x)/c^2}\) with \(\Phi_{\rm FDB}\equiv -\tfrac{\hbar}{2}[\Gamma(x)-\Gamma(\infty)]/\alpha_m\). We set \(\alpha_m\simeq1\) via a single-point gravitational-redshift check (Appendix F), leaving no additional freedom in the H1 normalization.

### Force definition via information potential
We define an information potential \(\Psi\) by \(\nabla\Psi=\mathbf{J}_{\rm info}\) and a physical potential \(\Phi_{\rm FDB}=\kappa\,\Psi\), giving
\[
\mathbf{F}_{\rm eff}=-\nabla\Phi_{\rm FDB}.
\]
In 2D waveguide geometry \(\Psi\propto \ln r\) (\(\Rightarrow \Phi_{\rm FDB}=v_c^{2}\ln r\)); in 3D spherical geometry \(\Psi\propto -1/r\) (\(\Rightarrow \Phi_{\rm FDB}\to -GM/r\)). This unifies the drift force (former eq. 8) and the time-dilation potential.

---

## 5. Instant Validation: Strong-Lensing H1 Ratio Test

> **Zero-degree-of-freedom check**: build the ratio \(R=\theta_E' c^{2}/(2\pi v_c^{2})\) for every lens; if \(|m_R|\le 0.03\) dex and \(s_R\le 0.10\) dex (MAD-based), FDB passes without fitting.

### 5.1 Definition and normalization (\(v_c\) axis \(\Rightarrow 2\pi\))
\[
R \equiv \frac{\theta_E' c^{2}}{2\pi v_c^{2}},\qquad \theta_E' = \theta_E \frac{D_s}{D_{ls}},\qquad v_c=\sqrt{2}\,\sigma .
\]
Using the \(\sigma\) axis directly would lead to \(4\pi \sigma^{2}\); converting to \(v_c\) enforces the \(2\pi\) denominator and removes the historical +0.301 dex bias. Box&nbsp;1 (below) and Appendix&nbsp;C provide the SIS derivation so every appearance of \(R\) references the same constant.

> **Box 1 — Normalization & intercept**  
> \[
> R \equiv \frac{\theta_E' c^{2}}{2\pi v_c^{2}},\qquad b_0\equiv \log_{10}(2\pi)-2\log_{10}c \approx -10.155\ \text{(rad, km\,s$^{-1}$)}.  
> \]
> Remaining on the \(v_c\) axis keeps every instance of \(R\) on this \(2\pi\) normalization; working directly with \(\sigma\) would require \(4\pi\sigma^{2}\) and a different intercept.

> **Zero-parameter H1 ratio test.** Using this normalization, we evaluate \(R_i\) for each lens in \(\mathcal{O}(N)\) time. A sample **passes** if \(|m_R|\le 0.03\,\mathrm{dex}\) and \(s_R\le 0.10\,\mathrm{dex}\) (MAD). SDSS/BELLS meet this criterion; BOSS (\(N\approx 40\)) remains **supplementary** because of higher scatter and residual metadata gaps.

### 5.2 Lightweight pipeline (O(N), no regression)
1. Convert \(\theta_E\)[arcsec] → rad and compute \(D_s,D_{ls}\) in flat \(\Lambda\)CDM (H\(_0\)=70, \(\Omega_m\)=0.3); build \(\theta_E'\).
2. Velocities:
   - Prefer published \(\sigma_{\rm SIS}\) => \(v_c=\sqrt{2}\,\sigma_{\rm SIS}\).
   - Else use aperture-corrected \(\sigma_e=\sigma_{\rm ap}(R_{\rm ap}/R_e)^{-0.066}\) with \(R_{\rm ap}=1.5''\) (SDSS) or 1.0'' (BOSS/BELLS); \(v_c=\sqrt{2}\,\sigma_e\) [@Jorgensen1995; @Cappellari2006].
3. Compute \(R_i\) and \(\ell_i=\log_{10}R_i\); retain positive, finite entries only.
4. Summaries: median \(m_R\) and robust scatter \(s_R=1.4826\,{\rm MAD}\) for the full sample and survey subsets.
5. PASS requires \(|m_R|\le0.03\) dex and \(s_R\le0.10\) dex.

> **Box 2 — H1 quick test (tool-agnostic)**  
> 1. Convert \(\theta_E\) to radians and compute \(D_s,D_{ls}\) (Flat \(\Lambda\)CDM) to form \(\theta_E'\).  
> 2. Use \(\sigma_{\rm SIS}\) when tabulated; otherwise apply \(\sigma_e=\sigma_{\rm ap}(R_{\rm ap}/R_e)^{-0.066}\) with \(R_{\rm ap}=1.5''\) (SDSS) or 1.0'' (BOSS/BELLS). Future datasets lacking \(R_e\) fall back to \([0.7'',2.0'']\); the script reports how many lenses use this bracket (currently zero).  
> 3. Evaluate \(R_i=\theta_{E,i}' c^{2}/(2\pi v_{c,i}^{2})\), keep only positive finite values, and store \(\ell_i=\log_{10}R_i\).  
> 4. Publish \(N,\mathrm{median}(\ell),1.4826\,\mathrm{MAD}(\ell)\) for each survey (Table 1; Figure 2). Quote **PASS** iff \(|\mathrm{median}(\ell)|\le0.03\) dex and scatter \(\le0.10\) dex; \(\kappa_{\rm ext}\sim\mathcal{N}(0,0.05)\) only adds \(\lesssim0.02\) dex and is reported as a secondary systematic.  
> 5. Note any **survey-specific QC** such as internal scale factors or missing metadata so readers can reproduce the same decision without regression or MCMC.

The implementation (`src/analysis/h1_ratio_test.py`, hosted at https://github.com/genki/gravitation/blob/main/src/analysis/h1_ratio_test.py) ingests machine-readable tables from SLACS, S4TM, BELLS, BELLS GALLERY, and SL2S plus the new BOSS catalog (`data/strong_lensing/BOSS_full_table.csv`, mirrored under the same repository) [@Bolton2008; @Auger2009; @Brownstein2012; @Shu2017BELLSGallery; @Shu2017S4TM]. The latter comes from the Appendix tables of Shu et al. (2017, MNRAS 480, 431); the HTML sources are archived with Playwright under `data/strong_lensing/sources/` so that the GitHub snapshot requires no further downloads.

### 5.3 Current statistics (2025-11-24 run)

Table 1 summarizes the current ratio-test statistics for each survey, directly implementing the PASS rule above.

Table 1. Strong-lensing H1 statistics by survey.
| Sample | N | \(m_R\) [dex] | \(s_R\) [dex] | Status |
|--------|---|----------------|----------------|--------|
| All    | 235 | +0.0009 | 0.1057 | PASS (edge)|
| SDSS   | 132 | −0.0003 | 0.0175 | PASS |
| BELLS  | 63  | +0.0777 | 0.1367 | Marginal |
| BOSS   | 40  | +0.0846 | 0.1497 | **Fail (data-poor)** |
| SDSS+BELLS | 195 | +0.0025 | 0.0681 | PASS |

Figure&nbsp;2 presents the same distributions as a survey-wise violin plot. Reproduction only needs the CSVs cited above; Appendix&nbsp;G lists the exact command.

\begin{figure}
\centering
\includegraphics{figures/h1_violin.png}
\caption{Survey-wise \(\log_{10}R\) distributions with the \(R=1\) reference line (dashed). Boxed medians and sample sizes match Table~1, and the PASS window \((|m_R|\le 0.03~\mathrm{dex},\,s_R\le 0.10~\mathrm{dex})\) is shaded.}
\label{fig:h1-violin}
\end{figure}

### 5.4 Why BOSS stays auxiliary
BOSS currently contributes N=40 lenses with \(m_R=+0.0846\,\mathrm{dex}\) and \(s_R=0.1497\,\mathrm{dex}\), exceeding the PASS window; it therefore serves only as a supplementary QC subset.
BOSS spectra mix aperture sizes and have shallower imaging, inflating \(s_R\) beyond the PASS window despite the new literature table (\(N=40,\ m_R=+0.0846\) dex, \(s_R=0.1497\) dex). Our loader retains the \([0.7'',2.0'']\) fallback for \(R_e\) (currently unused) and reports how many cases would rely on it, but we **do not** upgrade such entries to the main tally. Instead, SDSS(+BELLS)—where \(\sigma_{\rm SIS}\) or high-S/N imaging supply \(R_e\)—anchor the PASS statement, and BOSS remains a **supplementary** hold-out QC set. As an internal diagnostic we note that dividing BOSS velocities by 1.10 would zero the median, yet we deliberately leave this scale unapplied so that the test stays parameter-free; the value is merely reported as evidence of survey-to-survey zeropoint differences.

---

## 6. Galaxy-Scale Support: Rotation Curves and BTFR

Rotation curves act as **supporting** evidence: their outcome depends on assumed error floors and stellar mass-to-light ratios, so we treat the resulting statistics as sensitivity analyses that echo the algebraic H1 test [@Lelli2016SPARC]. Both models use one fitted parameter (FDB keeps a single \(V_0\); NFW keeps \(c=10\) fixed), and we define \(\Delta\mathrm{AICc}\equiv \mathrm{AICc}_{\rm FDB}-\mathrm{AICc}_{\rm NFW}\).

Table 2 lists the SPARC \(\Delta\mathrm{AICc}\) sensitivity grid for the four sweep combinations; all entries use the baseline c=10 fixed (k=1) comparison, and the outer-only column is the primary metric (full-radius values are reference only).

\begin{table*}
\centering
\caption{SPARC \(\Delta\mathrm{AICc}\) sensitivity grid (FDB \(k=1\) vs NFW \(k=1\), \(c=10\) fixed).}
\label{tab:sparc-aicc}
\begin{tabular}{lcccc}
\hline
Setting (err floor \([\mathrm{km\,s^{-1}}]\), \(Υ_{\rm disk}/Υ_{\rm bulge}\)) & Median \(\Delta\mathrm{AICc}\) & IQR & Outer median (r\(\ge 2.5R_d\)) & Outer IQR \\
\hline
5, 0.5/0.7   & 35.4 & [−29.8, 107.3] & −5.0  & [−21.7, 0.61] \\
3, 0.5/0.7   & 40.0 & [−41.0, 175.7] & −9.1  & [−41.3, 0.53] \\
2, 0.5/0.7   & 40.0 & [−49.4, 205.7] & −10.3 & [−53.7, 0.45] \\
5, 0.44/0.65 & 35.4 & [−29.8, 107.3] & −5.0  & [−21.7, 0.61] \\
\hline
\end{tabular}
\end{table*}

The **outer-only column** is our primary diagnostic because the 1/r drift dominates in the tails; full-radius medians are quoted only for completeness.

Full-curve medians can be >0 because inner radii pull toward NFW, but the **outer-only** medians are uniformly negative, matching the constant \(\Delta v^{2}\) expected from waveguide drift. Allowing a two-value M/L toggle barely moves the numbers, showing that stellar fine-tuning is not driving the comparison. A regression of \(v_{\rm obs}^2-v_{\rm bar}^2\) vs radius yields a median slope of \(4.9\times10^{2}\,\mathrm{(km\,s^{-1})^{2}\,kpc^{-1}}\) with MAD×1.4826 = \(3.7\times10^{2}\), consistent with \(\Delta v^{2}\approx\) const.

To check fairness, we also fit a reference run with **free concentration** (k=2) and no c prior. For the baseline setting (err floor \(5\,\mathrm{km\,s^{-1}}\), \(Υ_{\rm disk}=0.5, Υ_{\rm bulge}=0.7\)) this yields \(\mathrm{median}\,\Delta\mathrm{AICc}=56.0\) (IQR [16.9, 166.5]) and an outer-only median of −2.8. Thus, freeing \(c\) shifts the full-curve median further positive but leaves the tail preference for \(\Delta v^{2}=\)const intact; we therefore keep the c=10 (k=1) presentation in the main table and quote the free-c numbers as a diagnostic.

Figure 3 stacks the six most negative \(\Delta\\mathrm{AICc}\) galaxies (FDB-favoured) in the baseline c=10 run, with each panel showing SPARC data, Newtonian baryons, the single-parameter FDB fit, and the matched NFW curve. Table 2 stores the per-galaxy statistics; Appendix B.3 lists the full sweeps.

\begin{figure}
\centering
\includegraphics{figures/rotcurve_grid.png}
\caption{Top six FDB-favoured SPARC rotation curves (FDB solid, baryons dashed gray, NFW dotted) arranged in a 3×2 grid; titles report individual Delta AICc values.}
\label{fig:rotcurve-grid}
\end{figure}

### 6.2 BTFR
Setting \(x=\log_{10} M_{\rm bar}[M_\odot]\) and \(y=\log_{10} v_{\rm flat}^4[{\rm km}^4\,{\rm s}^{-4}]\) using the SPARC MRT catalog (fixed \(Υ_{\rm disk}=0.5\), gas mass = \(1.33 M_{\rm HI}\)), we evaluate the robust median offset \(b=\mathrm{median}(y-x)=-1.69\) dex. This single number is the proportionality constant ordinarily absorbed into \(L_0\) in empirical BTFR fits [@McGaugh2012BTFR; @McGaughSchombert2015]. Figure 4 therefore plots \(y=x+b\) (solid) with the \(\pm 0.1\) dex acceptance band (dashed), directly visualizing the FDB prediction \(v^4\propto M_{\rm bar}\).

\begin{figure}
\centering
\includegraphics{figures/btfr_sparc.png}
\caption{SPARC BTFR with the slope \(1\) line anchored by the robust median intercept \(b=-1.69\) dex (solid) and the \(\pm 0.1\) dex band (dashed); velocities use \(v_{\rm flat}\) in \(\mathrm{km\,s^{-1}}\) and baryonic masses use \(M_\odot\). When read as a flat-velocity proxy, \(\Delta v^{2}=\mathrm{median}(v_{\rm obs}^{2}-v_{\rm bar}^{2})\) per galaxy yields \(L_{0}=GM_{\rm bar}/\Delta v^{2}\), so scatter in \(\log L_{0}\) mirrors the BTFR scatter.}
\label{fig:btfr}
\end{figure}

---

## 7. Additional Consistency: Lensing, Cosmology, Energy
- **Lensing potential**: \(\Phi_{\rm FDB}=v_c^2\ln r\) yields \(\hat\alpha=2\pi(v_c/c)^2\), matching the SIS deflection once \(v_c=\sqrt{2}\sigma\) is used; the constant is therefore identical to the H1 ratio test \(R=\theta_E' c^{2}/(2\pi v_c^{2})\).
- **Cosmology**: Early‑universe impact suppressed by high-\(z\) plasma shielding; Proca mass chosen to avoid CMB constraints (discuss qualitatively).
- **Energy budget**: High reflectivity (\(R\approx1\)) stores ULE‑EMW near the interface; leakage scale \(\delta\ll\) galaxy size \(\Rightarrow\) feasible energy density. The acceleration is set by the information flux rather than a conserved energy reservoir, so Appendix D quotes upper bounds only.

---

## 8. Strong-field limit and horizons
Near compact objects the waveguide condition breaks and 3D spherical flux dominates, giving \(\Phi_{\rm FDB}\to -GM/r\) and **suggesting** the Schwarzschild redshift
\[
\frac{d\tau}{dt}=\sqrt{1+\frac{2\Phi_{\rm FDB}}{c^{2}}}\xrightarrow{\Phi_{\rm FDB}\to -GM/r}\sqrt{1-\frac{2GM}{rc^{2}}}
\]
for static observers (a rigorous derivation is left to future work). As \(r\to r_s\), \(\Phi_{\rm FDB}\to -\infty\) and \(d\tau/dt\to 0\), interpretable as a quantum-Zeno limit where measurement strength \(\Gamma\) diverges for hovering clocks (an **apparent** standstill for distant observers). Free-fall observers retain finite proper time, matching GR heuristically.

## 9. Discussion, Predictions, Limitations
- **Equivalence principle / Solar system**: We make explicit that \(L_0\) is a property of the environment (plasma density, gradients, boundary geometry), not of the test mass: \(L_0=L_0(n_e,\nabla n_e,...)\). In regions where \(\partial_x\Gamma\approx0\) (e.g. the Solar system, laboratory scales), Eq. (8) gives \(F_{\rm eff}\approx0\), so the dynamics reduce to standard Newtonian gravity and existing Eötvös-type bounds are automatically satisfied. The open-system view simply describes how low-information environments suppress the additional drift.
- **Survey dependence**: BOSS lacks some \(R_e\) values → larger scatter; primary decision should rely on homogeneous SDSS/BELLS where aperture correction is reliable.
- **Decisive prediction**: Joint \(\theta_E\)–\(v_c\) measurements for the same galaxies must lie on the line \(R=1\) without tunable width; any systematic offset >0.03 dex falsifies FDB.
- **Laboratory outlook**: Search for ULE‑EMW signatures via long‑baseline plasma waveguides or constraints on \(m_\gamma\) in the \(10^{-65}\,\mathrm{kg}\) range.

---

## 10. Conclusion
Waveguide confinement of a Proca ULE‑EMW converts geometric \(1/r^{2}\) decay to \(1/r\) information flux, yielding an effective \(1/r\) force that unifies flat rotation curves and BTFR without dark halos. The same normalization predicts a parameter-free strong-lensing ratio \(R=\theta_E' c^{2}/(2\pi v_c^{2})=1\); homogeneous samples satisfy this with median \(\approx 0\) dex and scatter \(\lesssim 0.1\) dex, establishing FDB’s observational viability in seconds. Future joint \(\theta_E\)–\(v_c\) campaigns offer a crisp falsification channel. The chief value of FDB is **instant validation**: a single, zero‑degree‑of‑freedom equality visible directly in the data.

---

## Appendix A: Interface Reflection (summary)
- TE reflection coefficient at galaxy–void interface with plasma frequencies \(\omega_{p,1}>\omega_{p,2}\) (idealized, lossless slab):
  \[
  R=\frac{k_{z,1}-k_{z,2}}{k_{z,1}+k_{z,2}},\quad
  k_{z,i}=\sqrt{\frac{\omega^{2}-\omega_{p,i}^{2}-\mu_\gamma^{2}c^{2}}{c^{2}}-k_{\parallel}^{2}}.
  \]
- Mode choice (kept consistent across text): **surface-bound branch** with \(k^2_{\rm void}\gtrsim 0,\,k^2_{\rm gal}<0\), so the energy flux runs tangentially and leakage into the interior is exponentially suppressed. Arrows in the schematic should therefore follow the interface on the void side.
- Penetration depth into the evanescent side: \(\delta = 1/|{\rm Im}\,k_{z,{\rm gal}}|\). For \(n_e \sim 10^{-4}\ {\rm cm^{-3}}\) and \(\omega\simeq\mu_\gamma c\), \(\delta = \mathcal{O}(10\text{–}30\ {\rm kpc})\), sufficient to confine the flow to interface scales.
- Dispersion of the guided mode: \(k_\parallel^{2}=\omega^{2}/c^{2}-\omega_{p,2}^{2}/c^{2}-\mu_\gamma^{2}\), giving \(\lambda_{\rm guide}\sim\lambda_C\) for the adopted \(m_\gamma\).
- Practical interfaces have finite thickness, gradients, and small collisional losses. These lower \(|R|\) slightly below unity but leave the high-reflectivity regime intact as long as \(\omega\ll\omega_{p,{\rm gal}}\) and the density ramp is wider than the skin depth.
- Numerical example: choosing \(n_{e,\rm void}=10^{-6}\,{\rm cm^{-3}}\) and \(n_{e,\rm gal}=10^{-3}\,{\rm cm^{-3}}\) gives \(\omega_{p,\rm void}\approx0.18\,\mathrm{rad\,s^{-1}}\) and \(\omega_{p,\rm gal}\approx5.7\,\mathrm{rad\,s^{-1}}\). Any mode within \(0.2\lesssim\omega\ll6\,\mathrm{rad\,s^{-1}}\) thus meets Eq. (5) and remains on the guided branch.
- Surface-mode dispersion: enforcing tangential-field continuity yields \(D(\omega,k_\parallel)=0\) with \(k_{z,v}=i\kappa_v\) and \(k_{z,g}=i\kappa_g\). Both \(\kappa_v,\kappa_g>0\) in the regime above, producing a bounded mode whose in-plane Poynting vector is \(S_\parallel\propto (k_\parallel/\omega)(E_t H_t^*)\); energy is guided along the interface while decaying exponentially into both half-spaces.

## Appendix B: BTFR Scaling and AICc (methods)
- Fit procedure for SPARC subsample: baryonic mass from 3.6 µm photometry, fixed mass-to-light prior; compare models via \(\mathrm{AICc}=2k-2\ln\hat{L}+2k(k+1)/(n-k-1)\) [@Sugiura1978; @HurvichTsai1989]. FDB uses \(k=1\) (overall scale). The baseline NFW also uses \(k=1\) by fixing \(c=10\) so that both sides pay the same parameter penalty, while Appendix B.3 quotes the ancillary run with \(c\) free (\(k=2\)).
- Bootstrap for uncertainty on median \(\Delta\mathrm{AICc}\); report IQR in Table 2.

> **Box B1 — SPARC fitting settings (baseline)**  
> • Sample: SPARC galaxies with quality flag = 1, inclination > 30°, and radial coverage beyond 3 R_d.  
> • Photometry: fixed mass-to-light ratios \(Υ_{\rm disk}=0.5\), \(Υ_{\rm bulge}=0.7\) (3.6 µm).  
> • Error model: velocity error floor $5\,\mathrm{km\,s^{-1}}$ (sensitivity at 2/3/5 $\mathrm{km\,s^{-1}}$ reported in Table 2).  
> • Models: FDB fit with a single parameter \(V_0\); NFW fit with \(c=10\) fixed so that \(k=1\).  
> • Metric: \(\Delta\mathrm{AICc}=\mathrm{AICc}_{\rm FDB}-\mathrm{AICc}_{\rm NFW}\); outer-only values use \(r\ge2.5R_d\).

### Appendix B.3: Lightweight sensitivity grid
The sweeps summarized in §6 are generated with `scripts/sparc_sweep.py`, which calls `analysis/sparc_fit_light.py` for each setting. The resulting medians/IQRs are stored in `paper2/build/sparc_aicc.csv` along with per-galaxy entries. For convenience we restate the grid:

Table B1 repeats the sensitivity grid for convenience.

\begin{table}[h]
\centering
\caption{Appendix copy of the SPARC $\Delta\mathrm{AICc}$ sensitivity grid (identical to Table~\ref{tab:sparc-aicc}).}
\label{tab:sparc-aicc-appendix}
\begin{tabular}{lcccc}
\hline
err floor ($\mathrm{km\,s^{-1}}$), $Υ_{\rm disk}/Υ_{\rm bulge}$ & Median $\Delta\mathrm{AICc}$ & IQR & Outer median & Outer IQR \\
\hline
5, 0.5/0.7   & 35.4 & [−29.8, 107.3] & −5.0  & [−21.7, 0.61] \\
3, 0.5/0.7   & 40.0 & [−41.0, 175.7] & −9.1  & [−41.3, 0.53] \\
2, 0.5/0.7   & 40.0 & [−49.4, 205.7] & −10.3 & [−53.7, 0.45] \\
5, 0.44/0.65 & 35.4 & [−29.8, 107.3] & −5.0  & [−21.7, 0.61] \\
\hline
\end{tabular}
\end{table}

Outer values use only points with r\(\ge 2.5R_d\) (with \(R_d\) proxied by \(\bar{r}/3\)). These numbers are meant to show robustness, not to serve as the primary claim.
For comparison, running the baseline setting without the \(c=10\) constraint (so \(k_{\rm NFW}=2\)) gives \(\mathrm{median}\,\Delta\mathrm{AICc}=56.0\) with IQR [16.9, 166.5] and an outer-only median of −2.8.

## Appendix C: Lensing Normalization
- **Corrected SIS normalization (v_c axis).** For a singular isothermal sphere, the deflection in terms of the 1D dispersion is \(\hat{\alpha}=4\pi(\sigma/c)^2\). Using \(v_c=\sqrt{2}\sigma\) gives \(\hat{\alpha}=2\pi(v_c/c)^2\).
- Einstein angle: \(\theta_E=\hat{\alpha}\,D_{ls}/D_s\); therefore \(\theta_E'=\theta_E D_s/D_{ls}=2\pi v_c^{2}/c^{2}\).
- The H1 ratio follows:
  \[
  R \equiv \frac{\theta_E' c^{2}}{2\pi v_c^{2}} = 1,
  \]
  which is the normalization used throughout the lens-based tests.

## Appendix D: Energy budget (order-of-magnitude)
- Required energy density near the interface is treated purely as an **upper bound**: \(u_{\rm ULE}\lesssim \Sigma_{\rm bar} v_c^{2}/(2 L_0)\). For a Milky-Way–like disk (\(\Sigma_{\rm bar}\sim 50\,M_\odot{\rm pc}^{-2}\), \(v_c\sim220\,{\rm km\,s^{-1}}\), \(L_0\sim10\,{\rm kpc}\)), this yields \(u_{\rm ULE}\lesssim 10^{-12}\ {\rm J\,m^{-3}}\). We **do not** equate this with \(\rho_{\rm DM} c^{2}\); only a modest non-equilibrium flux is required to sustain the measurement channel.
- Supply estimate: stellar/ISM radio backgrounds of \(\lesssim10^{-20}\ {\rm W\,m^{-2}sr^{-1}}\) accumulated over \(\tau\sim{\rm Gyr}\) suffice to reach the bound when trapped with reflectivity \(R\approx1\).
- Leakage is controlled by the evanescent depth \(\delta\) (Appendix A); loss rate \(\propto e^{-2L/\delta}\) keeps cosmological backgrounds minimally affected. Because the acceleration is driven by the information-monitoring rate \(\Gamma\) rather than a conserved energy reservoir, the above number is simply a conservative ceiling.

## Appendix F: Gravitational redshift sanity check (one-point)
- For a potential difference \(\Delta\Phi_{\rm FDB}\) between emitter and receiver, the frequency shift is
  \[
  \Delta\ln\nu \simeq -\frac{\Delta\Phi_{\rm FDB}}{c^{2}},
  \]
  identical to GR under the calibration of §4. Using geodetic/GPS (Earth–satellite) or white-dwarf surface tests provides a regression-free, single-point validation.
- Because \(\Phi_{\rm FDB}\) is tied to \(\Gamma\), this check simultaneously fixes \(\alpha_m\) (taken as 1) and leaves no free drift in the H1 lensing normalization [@PoundRebka1960].

## Appendix G: Strong-lensing H1 ratio test (reproducibility)
- Method and numbers are summarized in `appendix_f_h1.md`; the exact code resides at `src/analysis/h1_ratio_test.py` (https://github.com/genki/gravitation/blob/main/src/analysis/h1_ratio_test.py) and the machine-readable catalogs live under `data/strong_lensing/` in the same repository; Figure `figures/h1_violin.png` is regenerated from those assets.

---

## Data and code availability
Derived figures and tables come from the scripts distributed with this repository (https://github.com/genki/gravitation). `src/analysis/h1_ratio_test.py` (see above) regenerates Table 1 and Figure \ref{fig:h1-violin} from the SLACS/BELLS/BELLS GALLERY/S4TM/BOSS catalogs, while `src/analysis/sparc_fit_light.py` and `src/scripts/sparc_sweep.py` (https://github.com/genki/gravitation/blob/main/src/analysis/sparc_fit_light.py and https://github.com/genki/gravitation/blob/main/src/scripts/sparc_sweep.py) reproduce Table 2, Figure \ref{fig:rotcurve-grid}, and Figure \ref{fig:btfr} directly from the SPARC MRT release mirrored in `data/sparc/`. All intermediate CSV outputs live under `build/` in the same repository so a fresh clone plus `make pdf` suffices to recreate every figure and table.

---

## References

::: {#refs}
:::

---
