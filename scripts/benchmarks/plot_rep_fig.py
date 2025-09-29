#!/usr/bin/env python3
"""Generate representative rotation curve comparison figures under fair settings."""
from __future__ import annotations

import argparse
import json
import math
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
from matplotlib import pyplot as plt
from scripts.utils.mpl_fonts import use_jp_font
from matplotlib.ticker import MultipleLocator
from scripts.fit_sparc_fdbl import read_sparc_massmodels
from scripts.compare_fit_multi import model_ulw_accel, line_bias_accel

# Constants
M_PER_KM = 1.0e3
KPC_IN_M = 3.08567758149137e19
A0_SI = 1.2e-10  # m/s^2
A0_KPC = A0_SI * (KPC_IN_M / (M_PER_KM ** 2))
CHISQ_PRIOR_SIGMA_LN_C = 0.35

COLORS = {
    "data": "#000000",
    # Unified palette (rep6 template v2)
    "GR": "#888888",          # gray
    "MOND": "#2ca02c",        # green
    "GRDM": "#7f3fbf",        # purple
    "GRDM-noprior": "#8c564b",
    "FDB": "#d62728",         # red
}

@dataclass
class ModelResult:
    name: str
    velocity: np.ndarray
    residual: np.ndarray
    chi2: float
    k: int
    n: int
    label: str
    style: str = "-"
    color: Optional[str] = None
    annotation: Optional[str] = None

    @property
    def rchi2(self) -> float:
        dof = max(self.n - self.k, 1)
        return self.chi2 / dof

    @property
    def aic(self) -> float:
        return self.chi2 + 2 * self.k

    @property
    def aicc(self) -> float:
        if self.n - self.k - 1 <= 0:
            return float("nan")
        return self.aic + (2 * self.k * (self.k + 1)) / (self.n - self.k - 1)


def ensure_tmp_dir() -> Path:
    d = Path("tmp/rep_fig")
    d.mkdir(parents=True, exist_ok=True)
    return d


def error_floor(V: np.ndarray) -> np.ndarray:
    floor = np.clip(0.03 * np.abs(V), 3.0, 7.0)
    return floor


def prepare_data(name: str) -> Dict[str, np.ndarray]:
    rc = read_sparc_massmodels(Path("data/sparc/MassModels_Lelli2016c.mrt"), name)
    R = rc.R
    Vobs = rc.Vobs
    eV_raw = np.maximum(rc.eV, 1e-6)
    floor = error_floor(Vobs)
    eV_plot = np.sqrt(eV_raw * eV_raw + floor * floor)
    Rm = np.maximum(R, 1e-6)
    Vgas2 = rc.Vgas * rc.Vgas
    Vstar2 = rc.Vdisk * rc.Vdisk + rc.Vbul * rc.Vbul
    g_gas_base = Vgas2 / Rm
    g_star_base = Vstar2 / Rm
    return {
        "rc": rc,
        "R": R,
        "Rm": Rm,
        "Vobs": Vobs,
        "eV": eV_raw,
        "sigma_acc": eV_raw,
        "sigma_plot": eV_plot,
        "g_gas_base": g_gas_base,
        "g_star_base": g_star_base,
    }


def fit_mu_gr(g_obs: np.ndarray, eg: np.ndarray, g_star: np.ndarray, g_extra: np.ndarray, g_gas: np.ndarray) -> float:
    y = g_obs - g_gas - g_extra
    x = g_star
    w = 1.0 / np.maximum(eg, 1e-6)
    num = float(np.nansum(w * x * y))
    den = float(np.nansum(w * x * x))
    return max(0.0, num / max(den, 1e-30))


def chi2_acc(g_obs: np.ndarray, eg: np.ndarray, g_model: np.ndarray) -> float:
    w = 1.0 / np.maximum(eg, 1e-6)
    return float(np.nansum(((g_model - g_obs) * w) ** 2))


def compute_models(
    name: str,
    data: Dict[str, np.ndarray],
    psf_sigma: float = 0.0,
    temp_dir: Optional[Path] = None,
    run_fdb: bool = True,
    fdb_config: Optional[Dict[str, Any]] = None,
    *,
    mond_mu_source: str = "gr",
    mond_mu_fixed: float = 0.6,
    mu_max: Optional[float] = None,
    write_meta: bool = True,
    fit_uses_floor: bool = False,
) -> List[ModelResult]:
    R = data["R"]
    Rm = data["Rm"]
    Vobs = data["Vobs"]
    sigma_acc = data["sigma_acc"]
    sigma_plot = data["sigma_plot"]
    g_gas_base = data["g_gas_base"]
    g_star_base = data["g_star_base"]

    mask = np.isfinite(Vobs) & np.isfinite(sigma_acc)
    R = R[mask]
    Rm = Rm[mask]
    Vobs = Vobs[mask]
    sigma_acc = sigma_acc[mask]
    sigma_plot = sigma_plot[mask]
    g_gas_base = g_gas_base[mask]
    g_star_base = g_star_base[mask]

    n = len(R)

    g_obs = (Vobs * Vobs) / Rm
    _sigma_fit = sigma_plot if fit_uses_floor else sigma_acc
    eg = 2.0 * Vobs * _sigma_fit / Rm
    gas_scale_common = 1.33
    if fdb_config is not None:
        try:
            gas_scale_common = float(fdb_config.get('gas_scale', gas_scale_common))
        except Exception:
            gas_scale_common = 1.33

    results: List[ModelResult] = []

    # GR (visible only)
    g_gas_common = gas_scale_common * g_gas_base
    mu_gr = fit_mu_gr(g_obs, eg, g_star_base, np.zeros_like(g_obs), g_gas_common)
    if mu_max is not None:
        mu_gr = float(np.clip(mu_gr, 0.0, float(mu_max)))
    g_gr = g_gas_common + mu_gr * g_star_base
    v_gr = np.sqrt(np.maximum(g_gr * Rm, 0.0))
    res_gr = (Vobs - v_gr) / sigma_plot
    chi_gr = chi2_acc(g_obs, eg, g_gr)
    results.append(ModelResult("GR", v_gr, res_gr, chi_gr, k=1, n=n,
                               label=f"GR (μ={mu_gr:.3f})", color=COLORS["GR"]))

    # MOND (simple interpolating function)
    if mond_mu_source == "fixed":
        mu_mond = float(max(0.0, mond_mu_fixed))
    elif mond_mu_source == "refit":
        grid = np.linspace(0.0, mu_max if (mu_max is not None) else 2.0, 81)
        best = (float("inf"), mu_gr)
        for mu_try in grid:
            aN_try = g_gas_common + mu_try * g_star_base
            half_try = 0.5 * aN_try
            g_m_try = half_try + np.sqrt(np.maximum(half_try * half_try + aN_try * A0_KPC, 0.0))
            chi_try = chi2_acc(g_obs, eg, g_m_try)
            if chi_try < best[0]:
                best = (chi_try, float(mu_try))
        mu_mond = best[1]
    else:
        mu_mond = mu_gr
    if mu_max is not None:
        mu_mond = float(np.clip(mu_mond, 0.0, float(mu_max)))

    aN = g_gas_common + mu_mond * g_star_base
    half = 0.5 * aN
    g_mond = half + np.sqrt(np.maximum(half * half + aN * A0_KPC, 0.0))
    v_mond = np.sqrt(np.maximum(g_mond * Rm, 0.0))
    res_mond = (Vobs - v_mond) / sigma_plot
    chi_mond = chi2_acc(g_obs, eg, g_mond)
    results.append(ModelResult(
        "MOND",
        v_mond,
        res_mond,
        chi_mond,
        k=1,
        n=n,
        label=(r"MOND ($a_0\approx3.7\times10^{3}$ km$^2$ s$^{-2}$/kpc)"
               + f" [μ={mu_mond:.3f}, src={mond_mu_source}]") ,
        color=COLORS["MOND"],
    ))

    # GR+DM (NFW) grid search
    def cM_expected(V200: float) -> float:
        return max(5.0, min(20.0, 10.0 * (max(V200, 1e-6) / 200.0) ** (-0.1)))

    def nfw_velocity(R: np.ndarray, V200: float, c: float) -> np.ndarray:
        G = 4.30091e-6  # kpc km^2 / (s^2 Msun)
        H0 = 70.0  # km/s/Mpc
        rho_c = 3 * (H0 / 1000.0) ** 2 / (8 * math.pi * G)  # Msun/kpc^3
        delta_c = 200.0 / 3.0 * (c ** 3) / (math.log(1 + c) - c / (1 + c))
        Rvir = V200 / (10 * H0 / 1000.0)
        rs = Rvir / c
        x = np.maximum(R / rs, 1e-8)
        M_enclosed = 4 * math.pi * delta_c * rho_c * rs ** 3 * (np.log(1 + x) - x / (1 + x))
        return np.sqrt(np.maximum(G * M_enclosed / np.maximum(R, 1e-6), 0.0))

    def grid_search(prior: bool) -> Tuple[float, float, float, float]:
        best = (math.inf, 120.0, 10.0, mu_gr)
        for V200 in [80, 120, 160, 200, 240, 280]:
            for c in [5.0, 7.0, 10.0, 12.0, 15.0, 20.0]:
                Vdm = nfw_velocity(R, V200, c)
                g_dm = (Vdm * Vdm) / Rm
                mu = fit_mu_gr(g_obs, eg, g_star_base, g_dm, g_gas_common)
                g_model = g_gas_common + mu * g_star_base + g_dm
                chi = chi2_acc(g_obs, eg, g_model)
                if prior:
                    c_exp = cM_expected(V200)
                    penalty = ((math.log(max(c, 1e-6)) - math.log(c_exp)) / CHISQ_PRIOR_SIGMA_LN_C) ** 2
                    chi_eff = chi + penalty
                else:
                    chi_eff = chi
                if chi_eff < best[0]:
                    best = (chi_eff, V200, c, mu)
        return best

    chi_pr, V200_pr, c_pr, mu_pr = grid_search(True)
    Vdm_pr = nfw_velocity(R, V200_pr, c_pr)
    g_dm_pr = (Vdm_pr * Vdm_pr) / Rm
    g_model_pr = g_gas_base + mu_pr * g_star_base + g_dm_pr
    v_grdm_pr = np.sqrt(np.maximum(g_model_pr * Rm, 0.0))
    res_grdm_pr = (Vobs - v_grdm_pr) / sigma_plot
    chi_grdm_pr = chi2_acc(g_obs, eg, g_model_pr)
    results.append(ModelResult("GRDM", v_grdm_pr, res_grdm_pr, chi_grdm_pr, k=3, n=n,
                               label=f"GR+DM (c–M prior, V200={V200_pr:.0f}, c={c_pr:.1f})",
                               color=COLORS["GRDM"]))

    chi_np, V200_np, c_np, mu_np = grid_search(False)
    Vdm_np = nfw_velocity(R, V200_np, c_np)
    g_dm_np = (Vdm_np * Vdm_np) / Rm
    g_model_np = g_gas_base + mu_np * g_star_base + g_dm_np
    v_grdm_np = np.sqrt(np.maximum(g_model_np * Rm, 0.0))
    res_grdm_np = (Vobs - v_grdm_np) / sigma_plot
    chi_grdm_np = chi2_acc(g_obs, eg, g_model_np)
    results.append(ModelResult("GRDM-noprior", v_grdm_np, res_grdm_np, chi_grdm_np, k=3, n=n,
                               label=f"GR+DM (事前なし, V200={V200_np:.0f}, c={c_np:.1f})",
                               style='--', color=COLORS["GRDM-noprior"]))

    # FDB via compare_fit_multi
    use_fdb = None
    for candidate in [Path(f'data/results/{name.lower()}_surface_fixed_eps.json'),
                      Path(f'data/results/{name.lower()}_surface.json')]:
        if candidate.exists():
            try:
                use_fdb = json.loads(candidate.read_text())
                break
            except Exception:
                use_fdb = None
    if use_fdb is None and fdb_config and isinstance(fdb_config.get('mu', {}).get('ULW', {}), dict) and name in fdb_config['mu']['ULW']:
        use_fdb = fdb_config
    if use_fdb is None:
        if not run_fdb:
            raise RuntimeError(f'FDB config missing for {name} and run_fdb disabled')
        if temp_dir is None:
            temp_dir = ensure_tmp_dir()
        names_file = Path(f"data/sparc/sets/{name.lower()}_only.txt")
        if not names_file.exists():
            raise FileNotFoundError(f"names file missing: {names_file}")
        out_json = temp_dir / f"{name}_fdb.json"
        if run_fdb or not out_json.exists():
            cmd = [
                'PYTHONPATH=.',
                './.venv/bin/python',
                'scripts/compare_fit_multi.py',
                '--names-file', str(names_file),
                '--fdb-mode', 'surface',
                '--boost', '0.5',
                '--boost-tie-lam',
                '--auto-geo',
                '--pad-factor', '2',
                '--eg-frac-floor', '0.15',
                '--inv1-orth',
                '--gas-scale-grid', '1.0,1.33',
                '--lam-grid', '15,18,20,24',
                '--A-grid', '80,100,125',
                '--out', str(out_json),
            ]
            subprocess.run(' '.join(cmd), shell=True, check=True)
        use_fdb = json.loads(out_json.read_text())
    gas_scale_common = float(use_fdb.get('gas_scale', gas_scale_common))
    lam = float(use_fdb.get('lam', 15.0))
    A = float(use_fdb.get('A', 100.0))
    gas_scale = float(use_fdb.get('gas_scale', 1.33))
    boost = float(use_fdb.get('boost', 0.5))
    pix_kpc = float(use_fdb.get('pix_kpc', 0.2))
    size = int(use_fdb.get('size', 256))
    mu_info = use_fdb.get('mu', {}).get('ULW', {}).get(name)
    mu_ulw = float(mu_info.get('mu', 0.7)) if isinstance(mu_info, dict) else float(mu_info or 0.7)
    alpha_line = 0.0
    if isinstance(mu_info, dict) and 'alpha_line' in mu_info:
        alpha_line = float(mu_info['alpha_line'])
    beta_forward = float(use_fdb.get('meta', {}).get('beta_forward', 0.0))
    g_gas = gas_scale * g_gas_base
    # ULW acceleration (unit A=1.0 baseline)
    s1 = lam / 8.0
    s2 = lam / 3.0
    g_ulw_unit = model_ulw_accel(R, data['rc'].SBdisk, lam_kpc=lam, A=1.0, pix_kpc=pix_kpc,
                                 size=size, boost=boost, s1_kpc=s1, s2_kpc=s2,
                                 pad_factor=2, aniso_angle=0.0)
    g_line = line_bias_accel(R, data['rc'].SBdisk, pix_kpc=pix_kpc, size=size,
                             line_eps_kpc=float(use_fdb.get('line_eps_kpc', 0.5)),
                             pad_factor=2, beta_forward=beta_forward)
    g_fdb = g_gas + mu_ulw * g_star_base + A * g_ulw_unit + alpha_line * g_line
    v_fdb = np.sqrt(np.maximum(g_fdb * Rm, 0.0))
    res_fdb = (Vobs - v_fdb) / sigma_plot
    chi_fdb = chi2_acc(g_obs, eg, g_fdb)
    results.append(ModelResult("FDB", v_fdb, res_fdb, chi_fdb, k=4, n=n,
                               label=f"FDB (λ={lam:.1f} kpc, A={A:.0f})",
                               color=COLORS["FDB"]))

    # write diagnostic meta
    if write_meta and temp_dir is not None:
        try:
            meta = {
                "name": name,
                "A0_KPC": A0_KPC,
                "mu_gr": float(mu_gr),
                "mu_mond": float(mu_mond),
                "mond_mu_source": mond_mu_source,
                "gN_stats": {
                    "min": float(np.nanmin(aN)),
                    "p50": float(np.nanmedian(aN)),
                    "max": float(np.nanmax(aN)),
                },
                "V_obs_max": float(np.nanmax(Vobs)),
            }
            (temp_dir / f"rep_meta_{name.lower()}.json").write_text(json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")
        except Exception:
            pass
    return results


def apply_psf(values: np.ndarray, R: np.ndarray, sigma_kpc: float) -> np.ndarray:
    if sigma_kpc <= 0.0:
        return values
    smoothed = np.empty_like(values)
    for i, r in enumerate(R):
        weights = np.exp(-0.5 * ((R - r) / sigma_kpc) ** 2)
        weights /= np.sum(weights)
        smoothed[i] = np.sum(weights * values)
    return smoothed


def plot_figure(name: str, data: Dict[str, np.ndarray], models: List[ModelResult],
                outdir: Path, psf_sigma: float) -> Path:
    R = data['R']
    Vobs = data['Vobs']
    eV = data['eV']

    # sort by radius
    order = np.argsort(R)
    R_sorted = R[order]
    V_sorted = Vobs[order]
    e_sorted = eV[order]

    use_jp_font()
    fig, (ax_top, ax_res) = plt.subplots(2, 1, figsize=(7.2, 6.0), sharex=True,
                                         gridspec_kw={'height_ratios': [3, 1.5]})

    ax_top.fill_between(R_sorted, V_sorted - e_sorted, V_sorted + e_sorted,
                        color=COLORS['data'], alpha=0.1, label='観測 ±σ')
    ax_top.errorbar(R_sorted, V_sorted, yerr=e_sorted, fmt='o', ms=3,
                    color=COLORS['data'], ecolor='#444444', capsize=2, label='観測')

    legend_handles = []
    for model in models:
        v = model.velocity[order]
        if psf_sigma > 0.0:
            v = apply_psf(v, R_sorted, psf_sigma)
        line = ax_top.plot(R_sorted, v, model.style, lw=1.8,
                           color=model.color or None,
                           label=f"{model.label} (Total; AICc={model.aicc:.1f}, rχ²={model.rchi2:.2f}, k={model.k})")
        legend_handles.extend(line)

    ax_top.set_ylabel('速度 [km/s]')
    ax_top.grid(True, ls=':', alpha=0.4)
    ax_top.legend(frameon=False, fontsize=8)
    ax_top.set_title(f'{name}: 公平な代表比較図 (Total基準, PSF σ={psf_sigma:.2f} kpc, N={len(R_sorted)})')

    ax_res.axhline(0.0, color='black', lw=0.8)
    ax_res.fill_between(R_sorted, 1, -1, color='#dddddd', alpha=0.5)
    ax_res.fill_between(R_sorted, 2, -2, color='#eeeeee', alpha=0.5)

    for model in models:
        res = model.residual[order]
        if psf_sigma > 0.0:
            res = apply_psf(res, R_sorted, psf_sigma)
        ax_res.plot(R_sorted, res, model.style, lw=1.5, color=model.color or None,
                    label=f'{model.name}')

    ax_res.set_xlabel('半径 [kpc]')
    ax_res.set_ylabel('(V_obs - V_model)/σ')
    ax_res.grid(True, ls=':', alpha=0.4)
    ax_res.set_ylim(-4, 4)
    ax_res.yaxis.set_major_locator(MultipleLocator(1))

    # Footnote band (unified spec: N,k,rχ²,AICc,ΔAICc,σ_floor,rng,shared_sha)
    try:
        fdb = next(m for m in models if m.name == 'FDB')
    except StopIteration:
        fdb = min(models, key=lambda m: m.aicc)
    d_mond = next((m.aicc - fdb.aicc for m in models if m.name == 'MOND'), float('nan'))
    d_grdm = next((m.aicc - fdb.aicc for m in models if m.name == 'GRDM'), float('nan'))
    seed = 42
    import hashlib
    try:
        shared_sha = hashlib.sha256(Path('data/shared_params.json').read_bytes()).hexdigest()[:12]
    except Exception:
        shared_sha = 'unknown'
    foot = (
        f"N={fdb.n}, k={fdb.k}, rχ²={fdb.rchi2:.3f}, AICc={fdb.aicc:.1f}, "
        f"ΔAICc(MOND/GR+DM vs FDB)={d_mond:+.1f}/{d_grdm:+.1f}, "
        f"σ_floor=clip(0.03×V, 3..7) km/s, rng={seed}, shared_sha={shared_sha}"
    )
    fig.subplots_adjust(bottom=0.16)
    fig.text(0.01, 0.01, foot, fontsize=8)

    outdir.mkdir(parents=True, exist_ok=True)
    out_path = outdir / f'rep_{name.lower()}.png'
    fig.tight_layout(rect=(0,0.03,1,1))
    fig.savefig(out_path, dpi=180)
    # Also write SVG with embedded metadata (seed/shared_sha)
    out_svg = outdir / f'rep_{name.lower()}.svg'
    fig.savefig(out_svg, format='svg')
    try:
        svg = out_svg.read_text(encoding='utf-8')
        meta_json = json.dumps({'name': name, 'seed': seed, 'shared_sha': shared_sha}, ensure_ascii=False)
        if '<metadata' not in svg:
            svg = svg.replace('<svg ', '<svg xmlns:rep6="https://example/ns/rep6" ', 1)
            svg = svg.replace('>', '>' + f'<metadata id="rep6">{meta_json}</metadata>', 1)
            out_svg.write_text(svg, encoding='utf-8')
    except Exception:
        pass
    # Embed basic PNG metadata
    try:
        from PIL import Image, PngImagePlugin
        im = Image.open(out_path)
        info = PngImagePlugin.PngInfo()
        info.add_text('Description', json.dumps({'name': name, 'seed': seed, 'shared_sha': shared_sha}, ensure_ascii=False))
        im.save(out_path, pnginfo=info)
    except Exception:
        pass
    plt.close(fig)
    return out_path


def main() -> None:
    parser = argparse.ArgumentParser(description='Generate fair representative comparison figures')
    parser.add_argument('--name', action='append', help='Galaxy name (SPARC)', default=None)
    parser.add_argument('--outdir', default='server/public/reports/figs', help='Output directory')
    parser.add_argument('--psf-sigma-kpc', type=float, default=0.0, help='Optional Gaussian PSF sigma [kpc] applied uniformly')
    parser.add_argument('--no-run-fdb', action='store_true', help='Skip compare_fit_multi execution and reuse existing JSON if present')
    parser.add_argument('--fdb-json', default='data/results/multi_fit_expanded20_eps0.3_orth_eg015.json', help='Precomputed multi-fit JSON for per-galaxy parameters')
    parser.add_argument('--mond-mu-source', type=str, default='gr', choices=['gr','fixed','refit'], help='source of μ used in MOND g_N (default: gr)')
    parser.add_argument('--mond-mu-fixed', type=float, default=0.6, help='μ used when --mond-mu-source=fixed')
    parser.add_argument('--mu-max', type=float, default=None, help='optional upper bound on μ for stability')
    parser.add_argument('--no-meta', action='store_true', help='do not write diagnostic meta JSON')
    parser.add_argument('--fit-uses-floor', action='store_true', help='use error floor in eg for fitting/metrics')
    args = parser.parse_args()

    fdb_config = None
    fdb_path = Path(args.fdb_json) if args.fdb_json else None
    if fdb_path and fdb_path.exists():
        try:
            fdb_config = json.loads(fdb_path.read_text())
        except Exception as exc:
            print(f"[warn] failed to load FDB JSON {fdb_path}: {exc}")
            fdb_config = None
    elif fdb_path:
        print(f"[warn] FDB JSON not found: {fdb_path}")

    names = args.name or ['NGC3198', 'NGC2403']
    outdir = Path(args.outdir)
    tmp_dir = ensure_tmp_dir()

    for name in names:
        data = prepare_data(name)
        models = compute_models(
            name,
            data,
            psf_sigma=args.psf_sigma_kpc,
            temp_dir=tmp_dir,
            run_fdb=not args.no_run_fdb,
            fdb_config=fdb_config,
            mond_mu_source=args.mond_mu_source,
            mond_mu_fixed=args.mond_mu_fixed,
            mu_max=args.mu_max,
            write_meta=not args.no_meta,
            fit_uses_floor=args.fit_uses_floor,
        )
        out_path = plot_figure(name, data, models, outdir, args.psf_sigma_kpc)
        print(f'Wrote {out_path}')

if __name__ == '__main__':
    main()
