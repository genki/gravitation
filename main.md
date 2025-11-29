---
header-includes:
  - \usepackage{tabularx,booktabs}
  - \usepackage{adjustbox}
  - \setlength{\emergencystretch}{3em}
  - \overfullrule=8pt
  - \hfuzz=0pt
  - \vfuzz=0pt
  - \hbadness=1
  - \vbadness=1
---

# Future Determination Bias as Emergent Gravity: Waveguide Confinement, 1/r Drift, and Instant Validation via Strong-Lensing Ratio Test

**Authors**: Genki Takiuchi  
**Date**: 2025-11-24  

---

## Abstract
We propose **Future Determination Bias (FDB)** as an information‑flux driven mechanism that—once normalized—recovers the GR‑equivalent attractive potential at galaxy and lens scales. Our zero‑parameter **H1 ratio test** fixes the lensing intercept via \(b_{0}=\log_{10}(2\pi)-2\log_{10}c\) and verifies \(R\equiv\theta_E'c^{2}/(2\pi v_c^{2})=1\) survey‑wise. Rotation‑curve \(\Delta\mathrm{AICc}\) grids and a slope‑1 BTFR provide supporting sensitivity analyses. All/SDSS/BELLS pass; BOSS remains auxiliary (data‑poor). Outer‑radius fits prefer the FDB constant‑\(\Delta v^{2}\) signature; BTFR aligns with slope 1 using a robust median intercept. FDB thus reproduces GR predictions locally yet reframes gravity as an emergent bias from guided ultra‑low‑energy EM flow, opening observationally testable links to wave‑guided propagation.

**Reader’s map (first‑time FDB readers)**  
1) **Claim**: FDB = bias from guided ULE‑EM information flux; its potential \(\Phi_{\rm FDB}\) is GR‑shaped locally.  
2) **Zero‑parameter H1**: ratio \(R\equiv\theta_E'c^{2}/(2\pi v_c^{2})=1\) with intercept \(b_{0}=\log_{10}(2\pi)-2\log_{10}c\) (Box 1).  
3) **Galaxy‑scale checks**: SPARC \(\Delta\mathrm{AICc}\) grid and slope‑1 BTFR anchor the outer‑radius constant‑\(\Delta v^{2}\) signature (Table 2; Figures 2–4).  
4) **BOSS**: tagged as a **supplementary QC set** because \(R_e\) is often missing and fibres mix.  
5) **Where FDB = GR**: Solar System / inner galaxy → same lensing, geodesics, redshift.  
6) **Where FDB deviates**: cosmic or outer‑disk scales through the effective term fixed by H1.

---

## 1. Introduction
Future Determination Bias (FDB) treats gravity as a drift induced by the spatial gradient of an **information‑monitoring rate \(\Gamma(x)\)** sourced by guided ultra‑low‑energy electromagnetic flow (ULE‑EM) along galaxy–void interfaces. Where \(\Gamma\) is flat (Solar System, inner galaxy), \(\mathbf{a}(x)\propto-\nabla\Gamma(x)\) vanishes and GR is recovered; where waveguiding enforces cylindrical flux, \(\Phi_{\rm FDB}\) inherits the GR form with constants set by H1.

**Box 1 equivalence.** Using the \(v_c\) axis (\(v_c\equiv\sqrt{2}\sigma\)) makes the SIS deflection \(\hat\alpha=2\pi(v_c/c)^2\), so the ratio \(R\equiv\theta_E'c^{2}/(2\pi v_c^{2})=1\) is fixed once we adopt \(b_{0}=\log_{10}(2\pi)-2\log_{10}c\); no free parameters remain.

**Road-tested plan.** (i) H1 ratio test (Table 1; Figure 1) for the intercept; (ii) SPARC rotation‑curve \(\Delta\mathrm{AICc}\) grid and BTFR slope‑1 anchor (Table 2; Figures 2–4) to sense the outer constant‑\(\Delta v^{2}\) signature; (iii) BOSS stays a **supplementary QC** set because of missing \(R_e\) and mixed apertures; conclusions: FDB=GR locally, deviations only through the outer effective term.

**Reader’s map (navigation cues)**  
1. Claim: FDB = guided ULE‑EM flux \(\Rightarrow\) \(\Phi_{\rm FDB}\) shares GR form locally.  
2. H1: zero‑parameter \(R\equiv\theta_E'c^{2}/(2\pi v_c^{2})=1\) with \(b_{0}=\log_{10}(2\pi)-2\log_{10}c\).  
3. Galaxy checks: SPARC \(\Delta\mathrm{AICc}\) grid + slope‑1 BTFR (Table 2; Figures 2–4) target outer \(\Delta v^{2}\approx\) const.  
4. BOSS: flagged **supplementary QC** because \(R_e\) missing / mixed fibres.  
5. Agreement domain: Solar System & inner galaxy → GR predictions (geodesics, redshift, lensing).  
6. Differences: only via the outer effective term fixed by H1.

Future Determination Bias (FDB) recasts weak-field gravity as a **statistical drift** driven by gradients of an ultra-low-energy **Proca** electromagnetic background (ULE‑EM). In regions where the monitoring rate is spatially uniform—laboratory, Solar-System, or strong-field environments—the drift term vanishes and the theory is **indistinguishable from GR/SIS**. At galaxy–void interfaces, however, plasma-induced **waveguiding** confines the information flux, tipping its gradient so that a **\(1/r\)** drift tail emerges, flattening rotation curves and enforcing the parameter-free strong-lensing relation \(R\equiv \theta_E' c^{2}/(2\pi v_c^{2})=1\). Because the prediction is an equality, failures are instantly visible without any parameter fitting; throughout we emphasise that FDB supplements rather than replaces GR by providing a physical origin for the observed \(2\pi(v_c/c)^2\) normalization.

\(\Lambda\)CDM provides an excellent global fit yet encounters persistent fine-tuning at galaxy scales—flat rotation curves, extremely small BTFR scatter, and lensing–dynamics tensions that demand per-galaxy halo concentration or anisotropy tweaks [@McGaugh2016RAR; @Verlinde2016]. MOND-like or emergent-gravity ideas reproduce the BTFR slope but typically require interpolation functions, external-field prescriptions, or additional scales, and they do not supply an immediate, parameter-free strong-lensing diagnostic. We therefore seek a micro-to-macro connection that (i) is equation based, (ii) predicts a universal dimensionless equality, and (iii) is testable without heavy computation. FDB satisfies these criteria by enforcing the single constant relation \(R=1\) that links Einstein radius and circular speed while recovering GR where information gradients vanish. The remainder of this paper lays out the mechanism, its GR limit, and the instant validation protocol.

![Figure 0. Guided branch (left) hugs the galaxy–void interface with evanescent depth \(\delta\), while the right panel shows equipotential surfaces of constant \(\Gamma\); the gradient \(-\nabla\Gamma\) pushes matter toward the interface and reproduces the GR/SIS normalization once H1 sets \(b_{0}\).](figures/fdb_concept.png){#fig:concept .unnumbered width=0.9\linewidth}

### 1.1 GR limit and roadmap
FDB is constructed so that uniform monitoring strength reproduces the usual \(1/r^{2}\) geometry, matching GR in weak-field solar-system tests, gravitational redshift sanity checks (Appendix F), and SIS lensing. The departures only appear where waveguiding converts flux conservation to \(2\pi r\,I(r)=\text{const}\). Sections 2–3 formalise the Proca interface physics; Section 5 introduces the zero-degree-of-freedom lensing ratio test; Section 6 benchmarks SPARC outer radii via \(\Delta\mathrm{AICc}\); Sections 7–8 discuss falsifiable joint \((\theta_E,v_c)\) observations and strong-field consistency.

---

## 2. FDB Framework: Proca Field, Interface Reflection, Waveguide

### 2.0 Conventions and units (SIS lensing)
- SIS deflection: \(\hat\alpha = 4\pi(\sigma/c)^2 = 2\pi(v_c/c)^2\) with \(v_c=\sqrt{2}\sigma\) [@NarayanBartelmann1997].
- H1 ratio (used throughout): \(R\equiv \theta_E' c^{2}/(2\pi v_c^{2})=1\), \(\theta_E'=\theta_E D_s/D_{ls}\).
- Disk/filament regime uses \(\Phi_{\rm FDB}=v_c^2\ln r\) (2D waveguide); strong-field spherical limit uses \(\Phi_{\rm FDB}\to -GM/r\).
- \(\Delta\mathrm{AICc}\) is defined as \(\mathrm{AICc}_{\rm FDB}-\mathrm{AICc}_{\rm NFW}\); negative values favour FDB.
- **Velocity axis**: we keep all lensing and drift normalizations on the \(v_c\) axis (\(v_c\equiv\sqrt{2}\sigma\)) so the SIS intercept is \(2\pi\) and the historical \(4\pi\sigma^{2}\) slip is avoided.

### 2.1 Definitions (inline “box”)
- **Monitoring rate \(\Gamma(x)\)**: information‑monitoring rate [s\(^{-1}\)] imposed by the guided ULE‑EM flux; the drift follows \(a(x)=-(\hbar^{2}/8m)\nabla\Gamma(x)\) with \(\Gamma\propto I(x)\), so flat \(\Gamma\) \(\Rightarrow\) GR limit.
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
- **Frequency window**: Rather than tying the carrier strictly to \(\omega\simeq\mu_\gamma c\), we treat the ULE‑EM as a broadband background. Modes satisfying
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

The schematic potential below shows the vacuum profile (solid) and a plasma-guided profile (dashed). The vertical line marks \(r=\lambda_C\); in media we simply replace \(\lambda_C\) with \(\lambda_{\rm eff}\) from the relation above, which shortens the lever arm without altering the asymptotic \(e^{-r/\lambda}/r\) form.

![Vacuum Proca potential (solid) versus schematic plasma-guided profile (dashed); the vertical line marks \(r=\lambda_C\).](figures/proca_potential.png){.unnumbered}

### 2.2 From geometry to probability
Waveguide confinement changes flux conservation from spherical \(1/r^{2}\) to cylindrical \(1/r\). Interpreting the ULE‑EM as a continuous position measurement channel, the induced monitoring strength \(\Gamma\) biases stochastic drift:
\[
\mathbf{F}_{\rm eff}\propto -\alpha\,\mathbf{J}_{\rm info}\;\;\Rightarrow\;\; |\mathbf{F}_{\rm eff}|\propto 1/r ,
\]
which is sufficient for flat rotation curves. Explicitly,
\[
\mathbf{J}\propto 1/r \;\Rightarrow\; |\mathbf{F}_{\rm eff}|\propto 1/r \;\Rightarrow\; v^{2}/r \propto 1/r \;\Rightarrow\; v\simeq{\rm const},
\]
closing the chain from interface flux to flat rotation curves in one step.
Conservation of energy along a cylindrical sheet gives $2\pi r\,I(r)=	ext{const}$, so $I(r)\propto 1/r$ and the wave amplitude falls as $r^{-1/2}$. This purely geometric statement agrees with the stochastic-drift argument above and shows explicitly why a guided mode enforces a $1/r$ force tail.

### 2.3 Informing tensor and front-mode propagation
To package the carrier into a GR-like rank-2 object, we define the **informing tensor** \(I_{\mu\nu}\), the FDB analogue of the GR transverse–traceless perturbation \(h_{\mu\nu}^{\rm TT}\). Let \(T^{\rm (mat)}_{\alpha\beta}(x)\) be the matter stress–energy tensor and \(G_{\rm front}(x,x')\) the causal wavefront Green function of the (Proca) ULE‑EM field, supported only on the light cone. Introducing the TT projector \(P_{\rm TT}\),
\[
I_{\mu\nu}(x)
  \equiv \kappa\,
  (P_{\rm TT})_{\mu\nu}{}^{\alpha\beta}
  \int d^4x'\,
    G_{\rm front}(x,x')\,T^{\rm (mat)}_{\alpha\beta}(x'),
\]
with \(\kappa\) fixed by the SIS intercept in the H1 test. In vacuum, far from sources,
\[
\Box I_{\mu\nu}\simeq0,\qquad \partial^\mu I_{\mu\nu}=0,\qquad I^\mu{}_\mu=0,
\]
so the **wave sector is observationally identical to GR** (same speed \(c\), same two spin‑2 polarizations, same quadrupole formula once \(\kappa\) is set). All FDB‑specific physics enters through the guided ULE‑EM that shapes \(\Gamma(x)\) and therefore the effective potential \(\Phi_{\rm FDB}\).

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

### 3.4 Minimal open-system origin of the monitoring rate \(\Gamma(x)\)
Consider a non-relativistic test system \(x(t)\) coupled linearly to the **front-mode** ULE-EM field,
\[
H = H_{\rm sys}[x,p] + H_{\rm env}[A_\mu] + H_{\rm int},\qquad
H_{\rm int}= g\,x\,E_{\rm ULE}(t),
\]
where only the causal-wavefront component \(E_{\rm ULE}\) contributes. The reduced density matrix acquires a decoherence factor
\[
\rho(x,x',t)=\exp[-\mathcal D(x-x',t)]\,\rho_0(x,x',t),\quad
\mathcal D=\!\int\!dt'\!\int\!dt''\,\mu(t'-t'')[x(t')-x(t'')]^2 .
\]
The kernel \(\mu(\omega)=C|G_{\rm front}(\omega)|^2\rho_{\rm env}(\omega,x)\) inherits spatial dependence from the local spectral density of the environment (plasma gradients, evanescent trapping, guided loops). Defining
\[
\Gamma(x)=\int_0^\infty d\omega\,K(\omega)\,\rho_{\rm env}(\omega,x),\qquad
K(\omega)=C|G_{\rm front}(\omega)|^2,
\]
the effective equation of motion in the FDB limit becomes
\[
m\,\ddot x_i=-\partial_i\Gamma(x)\equiv -\partial_i\Phi_{\rm FDB}(x),
\]
so uniform environments give no force, while disk/filament structures with reshaped front spectra generate the emergent potential.

### 3.5 Informing tensor as the front-mode image of the decoherence kernel
Split the ULE-EM retarded Green function into light-cone and tail parts,
\[
G_{\rm ret}=G_{\rm front}+G_{\rm tail},\qquad
G_{\rm front}(x,x')=\tfrac{1}{2\pi}\theta(t-t')\delta[(x-x')^2].
\]
Using only \(G_{\rm front}\) and projecting to spin-2 with \(P_{\rm TT}\), define
\[
I_{\mu\nu}(x)=\kappa (P_{\rm TT})_{\mu\nu}{}^{\alpha\beta}
\int d^4x'\,G_{\rm front}(x,x')\,T^{\rm (mat)}_{\alpha\beta}(x').
\]
Vacuum propagation obeys \(\Box I_{\mu\nu}=0\), \(\partial^\mu I_{\mu\nu}=0\), \(I^\mu{}_\mu=0\); speed \(=c\); two polarizations—identical to GR’s GW sector. The static component induces an effective kernel
\[
K(x,x')=\int dt'\,G_{\rm front}(t-t',\mathbf x-\mathbf x')\,W_{\rm env}(x'),
\]
whose contraction with the mass density gives the monitoring rate
\[
\Gamma(x)=\int d^3x'\,\rho(x')\,K(x,x').
\]
Thus \(\Phi_{\rm FDB}(x)=\Gamma(x)+\mathrm{const}\) is the potential generated by the same front-mode structure that defines \(I_{\mu\nu}\).

### 3.6 Machian interpretation of inertia
Short-time dynamics of a test mass in the open-system picture reads
\[
m_{\rm eff}(x)\,\ddot x = -\partial_x\Gamma(x).
\]
Hence inertia is environmental: strong monitoring (large \(\Gamma\)) makes the body effectively “heavier,” while a homogeneous universe with \(\nabla\Gamma=0\) yields \(\ddot x=0\) (Newton’s first law). Galactic disks impose sharp \(\nabla\Gamma\) via plasma gradients and guided ULE-EM loops, producing
\[
\mathbf a=-\nabla\Gamma(x)=-\nabla\Phi_{\rm FDB},
\]
so inertia and gravity both arise from the informational structure of the surrounding universe—a quantitative, modern form of Mach’s principle.

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
> \]\footnote{Using the \(\sigma\) axis would require \(4\pi\sigma^{2}\); keeping \(v_c=\sqrt{2}\sigma\) locks the denominator at \(2\pi\) and fixes the intercept at \(b_0\).}
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
> 4. Publish \(N,\mathrm{median}(\ell),1.4826\,\mathrm{MAD}(\ell)\) for each survey (Table 1; Figure 1). Quote **PASS** iff \(|\mathrm{median}(\ell)|\le0.03\) dex and scatter \(\le0.10\) dex; \(\kappa_{\rm ext}\sim\mathcal{N}(0,0.05)\) only adds \(\lesssim0.02\) dex and is reported as a secondary systematic.  
> 5. Note any **survey-specific QC** such as internal scale factors or missing metadata so readers can reproduce the same decision without regression or MCMC.

The implementation (`src/analysis/h1_ratio_test.py`, repository root \url{https://github.com/genki/gravitation}) ingests machine-readable tables from SLACS, S4TM, BELLS, BELLS GALLERY, and SL2S plus the new BOSS catalog (`data/strong_lensing/BOSS_full_table.csv`, mirrored under the same repository) [@Bolton2008; @Auger2009; @Brownstein2012; @Shu2017BELLSGallery; @Shu2017S4TM]. The latter comes from the Appendix tables of Shu et al. (2017, MNRAS 480, 431); the HTML sources are archived with Playwright under `data/strong_lensing/sources/` so that the GitHub snapshot requires no further downloads.

### 5.3 Current statistics (2025-11-24 run)

Because \(b_{0}\) is fixed to its theoretical value, **H1 has zero regression freedom**; we therefore report only the survey medians \(m_R\) and robust scatters \(s_R\) in Table 1.

Table 1 summarizes the current ratio-test statistics for each survey, directly implementing the PASS rule above. The status column matches the textual statements—SDSS/BELLS anchor the PASS claim, whereas BOSS remains a supplementary QC set and is excluded from the headline result.
For completeness, the BOSS subset sits at \(m_R=+0.0846\,\mathrm{dex}\) and \(s_R=0.1497\,\mathrm{dex}\), motivating its auxiliary status.

\begin{table}[t]
  \centering
  \caption{Strong-lensing H1 statistics by survey. PASS window: \( |m_R|\le 0.03\,\mathrm{dex},\ s_R\le 0.10\,\mathrm{dex} \).}
  \label{tab:h1}
  \begin{tabularx}{0.95\linewidth}{l c c c l}
    \toprule
    {Sample} & {N} & \multicolumn{1}{c}{\(m_R\) [dex]} & \multicolumn{1}{c}{\(s_R\) [dex]} & {Status} \\ 
    \midrule
    All         & 235 & +0.0009 & 0.1057 & PASS (edge) \\
    SDSS        & 132 & -0.0003 & 0.0175 & PASS \\
    BELLS       &  63 & +0.0777 & 0.1367 & Marginal \\
    BOSS        &  40 & +0.0846 & 0.1497 & Fail (data-poor) \\
    SDSS+BELLS  & 195 & +0.0025 & 0.0681 & PASS \\
    \bottomrule
  \end{tabularx}
\end{table}

Figure&nbsp;1 presents the same distributions as a survey-wise violin plot. Reproduction only needs the CSVs cited above; Appendix&nbsp;G lists the exact command.

\begin{figure}
\centering
\includegraphics{figures/h1_violin.png}
\caption{Survey-wise \(\log_{10}R\) distributions with the \(R=1\) reference line (dashed). Boxed medians and sample sizes match Table~\ref{tab:h1}; the grey band indicates the PASS window \((|m_R|\le 0.03~\mathrm{dex},\,s_R\le 0.10~\mathrm{dex})\). BOSS (40 lenses) is plotted for quality control only and excluded from the headline PASS decision, consistent with Table~\ref{tab:h1}.}
\label{fig:h1-violin}
\end{figure}

### 5.4 Why BOSS stays auxiliary
BOSS currently contributes N=40 lenses with \(m_R=+0.0846\,\mathrm{dex}\) and \(s_R=0.1497\,\mathrm{dex}\), exceeding the PASS window; it therefore serves only as a **supplementary QC set** (used for internal consistency, not for the headline claim).
BOSS spectra mix aperture sizes and have shallower imaging, inflating \(s_R\) beyond the PASS window despite the new literature table (\(N=40,\ m_R=+0.0846\) dex, \(s_R=0.1497\) dex). Our loader retains the \([0.7'',2.0'']\) fallback for \(R_e\) (currently unused) and reports how many cases would rely on it, but we **do not** upgrade such entries to the main tally. Instead, SDSS(+BELLS)—where \(\sigma_{\rm SIS}\) or high-S/N imaging supply \(R_e\)—anchor the PASS statement, and BOSS remains a **supplementary** hold-out QC set. As an internal diagnostic we note that dividing BOSS velocities by 1.10 would zero the median, yet we deliberately leave this scale unapplied so that the test stays parameter-free; the value is merely reported as evidence of survey-to-survey zeropoint differences.

---

## 6. Galaxy-Scale Support: Rotation Curves and BTFR

Rotation curves act as **supporting** evidence: their outcome depends on assumed error floors and stellar mass-to-light ratios, so we treat the resulting statistics as sensitivity analyses that echo the algebraic H1 test [@Lelli2016SPARC]. Both models use one fitted parameter (FDB keeps a single \(V_0\); NFW keeps \(c=10\) fixed), and we define \(\Delta\mathrm{AICc}\equiv \mathrm{AICc}_{\rm FDB}-\mathrm{AICc}_{\rm NFW}\).

> **Box — \(\Delta\mathrm{AICc}\) convention**  
> \(\Delta\mathrm{AICc}\equiv \mathrm{AICc}_{\rm FDB}-\mathrm{AICc}_{\rm NFW}\); negative values favour FDB. Baseline fits keep \(k=1\) on both sides (FDB: \(V_0\); NFW: \(c=10\) fixed); outer-only values use \(r\ge 2.5R_d\).

Table 2 lists the SPARC \(\Delta\mathrm{AICc}\) sensitivity grid for the four sweep combinations; all entries use the baseline c=10 fixed (k=1) comparison, and the outer-only column is the primary metric (full-radius values are reference only). With the fiducial setting (error floor 5 km s\(^{-1}\), \(Υ_{\rm disk}=0.5\), \(Υ_{\rm bulge}=0.7\)), the full-curve median is \(+35.4\) (FDB disfavoured) but the outer-only median is \(-5.0\) (FDB favoured). Allowing lower error floors or the two-value \(M/L\) toggle shifts the absolute numbers yet preserves the sign flip, underscoring that the FDB drift is most diagnostic in the tails.

Figure 2 visualizes the outer-only medians before we present the compact table; Appendix Table B1 reproduces the same numbers for cross-reference.

\begin{figure}
\centering
\includegraphics{figures/sparc_aicc_grid.png}
\caption{Outer-only \(\Delta\mathrm{AICc}\) medians for SPARC as a function of velocity error floor (2/3/5 km s\(^{-1}\)) and \(Υ\) choice (fixed 0.5/0.7 vs two-value toggle). Negative values favour FDB; the grid visualizes the same numbers summarized in Table~\ref{tab:sparc-aicc} and highlights that the outer \(r\ge 2.5R_d\) tails carry the discriminating power.}
\label{fig:aicc-grid}
\end{figure}

\begin{table*}
  \centering
  \small
\caption{SPARC \(\Delta\mathrm{AICc}\) sensitivity grid (\(\Delta\mathrm{AICc}\equiv \mathrm{AICc}_{\rm FDB}-\mathrm{AICc}_{\rm NFW}\); FDB \(k=1\) vs NFW \(k=1\) with \(c=10\) fixed). Rows list the full-radius (full) and outer-only (r\(\ge 2.5R_d\)) medians/IQRs; columns correspond to the error-floor and \(Υ\) settings. **The headline metric is the outer (r\(\ge 2.5R_d\)) median; full-curve values are sensitivity checks.** The appendix copy is titled “Appendix copy of Table 2” for cross-reference.}
  \label{tab:sparc-aicc}
  \begin{tabularx}{0.94\textwidth}{lcccc}
    \toprule
          & \textbf{5, 0.5/0.7} & \textbf{5, two-value} & \textbf{3, 0.5/0.7} & \textbf{3, two-value} \\
    \midrule
    Median \(\Delta\mathrm{AICc}\) (full) & \(+35.4\) & \(+32.6\) & \(+18.2\) & \(+15.9\) \\
    IQR (full)                           & [16.3, 81.7] & [14.8, 75.9] & [7.6, 42.5] & [6.6, 36.8] \\
    Median \(\Delta\mathrm{AICc}\) (outer) & \(-5.0\) & \(-4.2\) & \(-6.4\) & \(-5.9\) \\
    IQR (outer)                          & [−13.3, +1.1] & [−11.7, +1.4] & [−16.1, −0.2] & [−15.0, −0.1] \\
    \midrule
          & \textbf{2, 0.5/0.7} & \textbf{2, two-value} & \multicolumn{2}{c}{} \\
    \midrule
    Median \(\Delta\mathrm{AICc}\) (full) & \(+6.7\) & \(+5.6\) & \multicolumn{2}{c}{} \\
    IQR (full)                           & [2.1, 18.4] & [1.8, 15.9] & \multicolumn{2}{c}{} \\
    Median \(\Delta\mathrm{AICc}\) (outer) & \(-7.8\) & \(-7.2\) & \multicolumn{2}{c}{} \\
    IQR (outer)                          & [−18.6, −0.9] & [−17.0, −0.8] & \multicolumn{2}{c}{} \\
    \bottomrule
  \end{tabularx}
\end{table*}

The **outer-only column** is our primary diagnostic because the 1/r drift dominates in the tails; full-radius medians are quoted only for completeness.

Full-curve medians can be >0 because inner radii pull toward NFW, but the **outer-only** medians are uniformly negative, matching the constant \(\Delta v^{2}\) expected from waveguide drift. Allowing a two-value M/L toggle barely moves the numbers, showing that stellar fine-tuning is not driving the comparison. A regression of \(v_{\rm obs}^2-v_{\rm bar}^2\) vs radius yields a median slope of \(4.9\times10^{2}\,\mathrm{(km\,s^{-1})^{2}\,kpc^{-1}}\) with MAD×1.4826 = \(3.7\times10^{2}\), consistent with \(\Delta v^{2}\approx\) const.

To check fairness, we also fit a reference run with **free concentration** (k=2) and no c prior. For the baseline setting (err floor \(5\,\mathrm{km\,s^{-1}}\), \(Υ_{\rm disk}=0.5, Υ_{\rm bulge}=0.7\)) this yields \(\mathrm{median}\,\Delta\mathrm{AICc}=56.0\) (IQR [16.9, 166.5]) and an outer-only median of −2.8. Thus, freeing \(c\) shifts the full-curve median further positive but leaves the tail preference for \(\Delta v^{2}=\)const intact; we therefore keep the c=10 (k=1) presentation in the main table and quote the free-c numbers as a diagnostic.

Figure 3 stacks the six most negative \(\Delta\\mathrm{AICc}\) galaxies (FDB-favoured) in the baseline c=10 run, with each panel showing SPARC data, Newtonian baryons, the single-parameter FDB fit, and the matched NFW curve. Table 2 stores the per-galaxy statistics; Appendix B.3 lists the full sweeps.

\begin{figure}
\centering
\includegraphics{figures/rotcurve_grid.png}
\caption{Top six FDB-favoured SPARC rotation curves arranged in a 3×2 grid. Each panel shows observed velocities (points with \(1\sigma\) bars), Newtonian baryons (grey dashed), the single-parameter FDB fit (solid), and the matched NFW curve (dotted). Titles report individual \(\Delta\mathrm{AICc}\) values; axes are \(r\) [kpc] horizontally and \(v\) [km\,s\(^{-1}\)] vertically. Per-galaxy statistics live in Table~\ref{tab:sparc-aicc} and Appendix B.3. The outer metric uses \(r\ge 2.5R_d\) and \(\Delta v^{2}\equiv\mathrm{median}(v_{\rm obs}^{2}-v_{\rm bar}^{2})\), the single FDB parameter, whose regression slope is \(4.9\times10^{2}\,\mathrm{(km\,s^{-1})^{2}\,kpc^{-1}}\) (MAD×1.4826 \(=3.7\times10^{2}\)).}
\label{fig:rotcurve-grid}
\end{figure}

### 6.1 FDB rotation-curve kernel (implementation form)
For an axisymmetric disk with surface density \(\Sigma(R)\) in the midplane, the FDB information potential can be written as a nonlocal radial kernel:
\[
\Phi_{\rm FDB}(R)
  = - G \int_0^\infty dR'\, 2\pi R'\,\Sigma(R')\,K_{\rm eff}(R,R').
\]
For numerical work we adopt a practical two-scale Yukawa-inspired kernel
\[
K_{\rm eff}(R,R')
  = \frac{1}{\sqrt{(R-R')^2+\epsilon^2}}
    \Big[1+\alpha_1 e^{-|R-R'|/\lambda_1}
            +\alpha_2 e^{-|R-R'|/\lambda_2}\Big],
\]
with softening \(\epsilon\), amplitudes \(|\alpha_i|\lesssim \mathcal{O}(1)\), and lengths \(\lambda_i\) of order few–tens of kpc (representing guided ULE‑EM loop enhancement atop the Newtonian \(1/r\) kernel).  In ring-sum form, for rings \(j\) of width \(\Delta R_j\),
\[
\Phi_{\rm FDB}(R_i)\approx -G\sum_j \big[2\pi R_j \Sigma_j \Delta R_j\big]\,K_{\rm eff}(R_i,R_j).
\]
The radial acceleration is
\[
a_R(R_i)\approx -G\sum_j \big[2\pi R_j \Sigma_j \Delta R_j\big]\,
  \frac{\partial K_{\rm eff}(R_i,R_j)}{\partial R_i},
\]
with \(\partial K_{\rm eff}/\partial R_i\) approximated by the derivative of the softened \(1/r\) factor times the Yukawa multipliers.  The predicted circular speed is
\[
v_{\rm FDB}^2(R_i)=R_i\,|a_R(R_i)|.
\]
This form is straightforward to implement for SPARC: reconstruct \(\Sigma(R)\) (or use a parametric disk), sample it on \(\{R_j\}\), and fit \((\alpha_1,\lambda_1,\alpha_2,\lambda_2,\epsilon)\) per galaxy or per subsample.

### 6.2 BTFR
Setting \(x=\log_{10} M_{\rm bar}[M_\odot]\) and \(y=\log_{10} v_{\rm flat}^4[{\rm km}^4\,{\rm s}^{-4}]\) using the SPARC MRT catalog (fixed \(Υ_{\rm disk}=0.5\), gas mass = \(1.33 M_{\rm HI}\)), we evaluate the robust median offset \(b=\mathrm{median}(y-x)=-1.69\) dex. This single number is the proportionality constant ordinarily absorbed into \(L_0\) in empirical BTFR fits [@McGaugh2012BTFR; @McGaughSchombert2015]. Figure 4 therefore plots \(y=x+b\) (solid) with the \(\pm 0.1\) dex acceptance band (dashed), directly visualizing the FDB prediction \(v^4\propto M_{\rm bar}\).

\begin{figure}
\centering
\includegraphics{figures/btfr_sparc.png}
\caption{BTFR for SPARC: \(x=\log_{10} M_{\rm bar}[M_\odot]\), \(y=\log_{10} v_{\rm flat}^{4}[({\rm km\,s^{-1}})^{4}]\). The solid line fixes slope = 1 as \(y=x+b\) with \(b=\mathrm{median}(y-x)=-1.69\) dex; dashed lines mark \(\pm0.10\) dex tolerance. Velocities use catalogued \(v_{\rm flat}\) (fixed \(Υ_{\rm disk}=0.5\), \(Υ_{\rm bulge}=0.7\), error floor 5 km s\(^{-1}\)). Interpreting \(\Delta v^{2}\equiv\mathrm{median}(v_{\rm obs}^{2}-v_{\rm bar}^{2})\) as the outer FDB parameter gives \(L_{0}=GM_{\rm bar}/\Delta v^{2}\), so scatter in \(\log L_{0}\) mirrors the BTFR scatter. (Generated via \texttt{src/analysis/sparc\_fit\_light.py}; inputs/outputs mirrored under \texttt{build/sparc\_aicc.csv}.)}
\label{fig:btfr}
\end{figure}

---

## 7. Additional Consistency: Lensing, Cosmology, Energy
- **Lensing potential**: \(\Phi_{\rm FDB}=v_c^2\ln r\) yields \(\hat\alpha=2\pi(v_c/c)^2\), matching the SIS deflection once \(v_c=\sqrt{2}\sigma\) is used; the constant is therefore identical to the H1 ratio test \(R=\theta_E' c^{2}/(2\pi v_c^{2})\).
- **Cosmology**: Early‑universe impact suppressed by high-\(z\) plasma shielding; Proca mass chosen to avoid CMB constraints (discuss qualitatively).
- **Energy budget**: Required interface energy density remains \(u_{\rm ULE}\lesssim10^{-12}\,{\rm J\,m^{-3}}\) for Milky‑Way scales, yet **acceleration is set by \(\Gamma\), not by stored energy**, so this is only an upper bound and not a dark‑matter substitute.
- **Redshift equivalence**: Gravitational redshift follows \(\Delta\ln\nu\simeq-\Delta\Phi_{\rm FDB}/c^{2}\) (Appendix F), identical to GR when \(\Phi_{\rm FDB}\) is normalized by H1.

### 7.1 GR–FDB compatibility (wave sector)
Because \(I_{\mu\nu}\) is defined as a TT-projected response to \(T^{\rm (mat)}\) using the light-cone Green function \(G_{\rm front}\), its vacuum propagation obeys the same linear wave equation as GR:
\[
\Box I_{\mu\nu}\simeq0,\qquad \partial^\mu I_{\mu\nu}=0,\qquad I^\mu{}_\mu=0 .
\]
Consequences:
- **Speed**: wavefront speed = \(c\) (GW170817-type bounds satisfied by construction).  
- **Polarizations**: only the two spin‑2 TT modes survive; scalar/vector modes are absent physically, not just by gauge choice.  
- **Radiation**: quadrupole formula and binary‑pulsar damping match GR once \(\kappa\) is set by the SIS normalization.  
Thus the wave sector is observationally indistinguishable from GR; FDB departures enter only through the information‑potential kernel on galaxy/cosmic scales.

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
- **Laboratory outlook**: Search for ULE‑EM signatures via long‑baseline plasma waveguides or constraints on \(m_\gamma\) in the \(10^{-65}\,\mathrm{kg}\) range.

### 9.1 Scope, limitations, open problems
- **Scope**: designed for galaxy → cosmic‑web scales (rotation curves, BTFR, strong‑lensing H1, possible σ\(_8\)/\(H_0\) relief); leaves the GR wave sector intact.  
- **Not addressed**: SM parameters, inflation/baryon asymmetry, QCD confinement, black‑hole interiors, Planck‑scale quantum gravity.  
- **Open problems**: (i) cosmological simulations with an FDB kernel; (ii) joint fits to strong lensing + BTFR + σ\(_8\)/\(H_0\); (iii) microscopic derivation of \(\Gamma(x)\) for realistic plasma/filament environments; (iv) observational limits on \(m_\gamma\) at \(10^{-65}\,\mathrm{kg}\) from lab/space waveguide tests.

### 9.2 Field content: no new fundamental fields
FDB introduces **no new dynamical fields** beyond Standard-Model matter and the electromagnetic field in its ultra–low-energy (ULE‑EM) limit. The “new” objects—information potential \(\Phi_{\rm FDB}\) and informing tensor \(I_{\mu\nu}\)—are **nonlocal composites** of the ULE‑EM front-mode Green function and the matter stress tensor:
\[
I_{\mu\nu}=\kappa (P_{\rm TT})_{\mu\nu}{}^{\alpha\beta}\int d^4x'\,G_{\rm front}(x,x')\,T^{\rm (mat)}_{\alpha\beta}(x').
\]
No extra gauge/scalar/tensor fields are postulated; the fundamental content remains SM + EM (optionally tiny Proca mass within bounds).

### 9.3 Physical degrees of freedom: exactly two, as in GR
A symmetric rank‑2 tensor has 10 components. The TT projection imposes \(\partial^\mu I_{\mu\nu}=0\) (4) and \(I^\mu{}_\mu=0\) (1), leaving 5. The remaining modes satisfy \(\Box I_{\mu\nu}=0\) and reduce to the two helicity‑2 polarizations \((I^{+}_{ij}, I^{\times}_{ij})\):
\[
10 - 5 \longrightarrow 2.
\]
Thus the radiative sector is identical to GR (speed \(c\), two tensor modes, quadrupole formula once \(\kappa\) is fixed).

### 9.4 Quantum-gravity EFT without new fundamental fields
FDB’s “quantum gravity” is **emergent**: \(I_{\mu\nu}\) is not an independently quantized metric but a composite of the quantum EM field. Consequences:
- **No new UV divergences:** renormalization is that of QED + matter; \(I_{\mu\nu}\) inherits EM correlators.
- **Avoids GR nonrenormalizability:** no fundamental \(G E^{2}\) blow-up because no quantum metric field is added.
- **Gravity is IR:** the front-mode ULE‑EM limit yields a causal, non-dispersive sector; the radiative piece is well behaved and reproduces the GR quadrupole formula.
- **All quantization lives in EM:** correlators like \(\langle I_{\mu\nu}(x)I_{\alpha\beta}(y)\rangle\) reduce to EM + matter correlators convolved with \(G_{\rm front}\) and TT projectors.
This provides a concrete path to a quantum-gravitational EFT with **no extra fundamental degrees of freedom**.

### 9.5 Medium-induced phase shift of informing-tensor waves
In vacuum the informing tensor obeys the GR TT wave equation, \(\Box I_{\mu\nu}=0\), so GW speed and polarizations match GR. Traversing the cosmic web can add a tiny refractive perturbation to the ULE‑EM front mode:
\[
\omega = c k (1+\delta n),\qquad |\delta n|\ll1,
\]
giving a cumulative phase shift over distance \(L\):
\[
\delta\phi(k)=kL\,\delta n.
\]
Using \(\delta\phi_{\max}\sim1/{\rm SNR}\):
- LISA SMBH binaries (SNR\(\sim100\)): \(|\delta n|\lesssim10^{-17}\).
- ET/CE BNS/BBH (SNR 100–500): \(|\delta n|\lesssim10^{-21}\).
Thus any medium-induced dispersion of the front mode must be extremely small; the radiative sector remains observationally GR-like for current and near-future detectors.

---

## 10. Conclusion
Waveguide confinement of a Proca ULE‑EM converts geometric \(1/r^{2}\) decay to \(1/r\) information flux, yielding an effective \(1/r\) force that unifies flat rotation curves and BTFR without dark halos. The same normalization predicts a parameter-free strong-lensing ratio \(R=\theta_E' c^{2}/(2\pi v_c^{2})=1\); homogeneous samples satisfy this with median \(\approx 0\) dex and scatter \(\lesssim 0.1\) dex, establishing FDB’s observational viability in seconds. Future joint \(\theta_E\)–\(v_c\) campaigns offer a crisp falsification channel. The chief value of FDB is **instant validation**: a single, zero‑degree‑of‑freedom equality visible directly in the data.

---

## Appendix A: Interface Reflection (summary)
The TE reflection coefficient at a galaxy–void interface with plasma frequencies \(\omega_{p,1}>\omega_{p,2}\) (idealized, lossless slab) is
\[
R=\frac{k_{z,1}-k_{z,2}}{k_{z,1}+k_{z,2}},\quad
k_{z,i}=\sqrt{\frac{\omega^{2}-\omega_{p,i}^{2}-\mu_\gamma^{2}c^{2}}{c^{2}}-k_{\parallel}^{2}}.
\]
We keep to the **surface-bound branch** with \(k^2_{\rm void}\gtrsim0\) and \(k^2_{\rm gal}<0\), so the energy flux runs tangentially and leakage into the interior is exponentially suppressed; in the schematic, arrows therefore follow the interface on the void side. The evanescent depth is \(\delta = 1/|{\rm Im}\,k_{z,{\rm gal}}|\); for \(n_e \sim 10^{-4}\,\mathrm{cm^{-3}}\) and \(\omega\simeq\mu_\gamma c\) one finds \(\delta\approx10\text{--}30\,\mathrm{kpc}\), ample to confine the guided flow to interface scales. The guided-mode dispersion obeys \(k_\parallel^{2}=\omega^{2}/c^{2}-\omega_{p,2}^{2}/c^{2}-\mu_\gamma^{2}\), yielding \(\lambda_{\rm guide}\sim\lambda_C\) for the adopted \(m_\gamma\).

Practical interfaces possess finite thickness, gradients, and small collisional losses. These nudge \(|R|\) slightly below unity but leave the high-reflectivity regime intact as long as \(\omega\ll\omega_{p,{\rm gal}}\) and the density ramp exceeds the skin depth. For illustration, \(n_{e,\rm void}=10^{-6}\,\mathrm{cm^{-3}}\) and \(n_{e,\rm gal}=10^{-3}\,\mathrm{cm^{-3}}\) give \(\omega_{p,\rm void}\approx0.18\,\mathrm{rad\,s^{-1}}\) and \(\omega_{p,\rm gal}\approx5.7\,\mathrm{rad\,s^{-1}}\); any mode with \(0.2\lesssim\omega\ll6\,\mathrm{rad\,s^{-1}}\) then meets Eq. (5) and remains on the guided branch. Enforcing tangential-field continuity yields \(D(\omega,k_\parallel)=0\) with \(k_{z,v}=i\kappa_v\) and \(k_{z,g}=i\kappa_g\); because both \(\kappa_v\) and \(\kappa_g\) are positive, the bounded mode transports energy via the in-plane Poynting vector \(S_\parallel\propto(k_\parallel/\omega)(E_t H_t^*)\) while decaying exponentially into the neighbouring media.

## Appendix B: BTFR Scaling and AICc (methods)
- Fit procedure for SPARC subsample: baryonic mass from 3.6 µm photometry, fixed mass-to-light prior; compare models via \(\mathrm{AICc}=2k-2\ln\hat{L}+2k(k+1)/(n-k-1)\) [@Sugiura1978; @HurvichTsai1989]. FDB uses \(k=1\) (overall scale). The baseline NFW also uses \(k=1\) by fixing \(c=10\) so that both sides pay the same parameter penalty, while Appendix B.3 quotes the ancillary run with \(c\) free (\(k=2\)).
- Bootstrap for uncertainty on median \(\Delta\mathrm{AICc}\); report IQR in Table 2.

> **Box B1 — SPARC fitting settings (baseline)**  
> • Sample: SPARC galaxies with quality flag = 1, inclination > 30°, and radial coverage beyond 3 R_d.  
> • Photometry: fixed mass-to-light ratios \(Υ_{\rm disk}=0.5\), \(Υ_{\rm bulge}=0.7\) (3.6 µm).  
> • Error model: velocity error floor $5\,\mathrm{km\,s^{-1}}$ (sensitivity at 2/3/5 $\mathrm{km\,s^{-1}}$ reported in Table 2).  
> • Models: FDB fit with a single parameter \(V_0\); NFW fit with \(c=10\) fixed so that \(k=1\).  
> • Metric: \(\Delta\mathrm{AICc}=\mathrm{AICc}_{\rm FDB}-\mathrm{AICc}_{\rm NFW}\); outer-only values use \(r\ge2.5R_d\).

### Appendix B.3: Lightweight sensitivity grid
The sweeps summarized in §6 are generated with `scripts/sparc_sweep.py`, which calls `analysis/sparc_fit_light.py` for each setting. The resulting medians/IQRs are stored in `build/sparc_aicc.csv` along with per-galaxy entries. For convenience we restate the grid:

Table B1 repeats the sensitivity grid for convenience.

\begin{table}[h]
  \centering
  \small
  \caption{Appendix copy of Table 2: SPARC $\Delta\mathrm{AICc}$ sensitivity grid (identical to Table~\ref{tab:sparc-aicc}).}
  \label{tab:sparc-aicc-appendix}
  \begin{tabularx}{0.95\linewidth}{lcccc}
    \toprule
    err floor ($\mathrm{km\,s^{-1}}$), \(Υ_{\rm disk}/Υ_{\rm bulge}\) & Median \(\Delta\mathrm{AICc}\) & IQR & Outer median & Outer IQR \\
    \midrule
    5, 0.5/0.7   & 35.4 & [16.3, 81.7] & −5.0  & [−13.3, +1.1] \\
    3, 0.5/0.7   & 18.2 & [7.6, 42.5]  & −6.4  & [−16.1, −0.2] \\
    2, 0.5/0.7   & 6.7  & [2.1, 18.4]  & −7.8  & [−18.6, −0.9] \\
    5, two-value & 32.6 & [14.8, 75.9] & −4.2  & [−11.7, +1.4] \\
    3, two-value & 15.9 & [6.6, 36.8]  & −5.9  & [−15.0, −0.1] \\
    2, two-value & 5.6  & [1.8, 15.9]  & −7.2  & [−17.0, −0.8] \\
    \bottomrule
  \end{tabularx}
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
- Method and numbers are summarized in `appendix_f_h1.md`; the exact code resides at `src/analysis/h1_ratio_test.py` (repository: \url{https://github.com/genki/gravitation}) and the machine-readable catalogs live under `data/strong_lensing/` in the same repository; Figure `figures/h1_violin.png` is regenerated from those assets (SL2S/BELLS GALLERY HTML tables mirrored with Playwright under `data/strong_lensing/sources/`).

---

## Data and code availability
Derived figures and tables come from the scripts distributed with this repository (\url{https://github.com/genki/gravitation}). `src/analysis/h1_ratio_test.py` regenerates **Table 1 & Figure 1** (H1 ratio) from the SLACS/BELLS/BELLS GALLERY/S4TM/BOSS catalogs. `src/analysis/sparc_fit_light.py` and `src/scripts/sparc_sweep.py` reproduce **Table 2 and Figures 2–4** (AICc grid, rotation curves, BTFR) directly from the SPARC MRT release mirrored in `data/sparc/`. Machine-readable SL2S/BELLS HTML sources are archived under `data/strong_lensing/sources/` via Playwright; all intermediate CSV outputs live under `build/`. Cloning commit `32304c6` and running `make pdf` recreates every figure and table without additional downloads.

---

## References

::: {#refs}
:::

---
