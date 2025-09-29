#!/usr/bin/env python3
from __future__ import annotations
import json
from pathlib import Path
import numpy as np
from astropy.io import fits

from scripts.fit_sparc_fdbl import read_sparc_massmodels, make_axisymmetric_image
from scripts.compare_fit_multi import chi2, to_accel, line_bias_accel
from theory.info_decoherence import EtaParams
from src.fdb.a_from_info import info_bias_profile_from_map


def with_error_floor(R, Vobs, eV):
    Vobs = np.asarray(Vobs, float); eV = np.asarray(eV, float)
    floor = np.clip(0.03*np.abs(Vobs), 3.0, 7.0)
    eVe = np.sqrt(np.maximum(eV,1e-6)**2 + floor**2)
    return to_accel(R, Vobs, eVe)


def load_ha_or_proxy(name: str):
    p = Path(f'data/halpha/{name}/Halpha_SB.fits')
    if p.exists():
        img = fits.getdata(p).astype(float)
        hdr = fits.getheader(p)
        pix = float(hdr.get('PIXSCALE', 0.305)) / 206265.0 * 1.0
        if not np.isfinite(pix) or pix <= 0:
            pix = 0.2
        return img, pix
    rc = read_sparc_massmodels(Path('data/sparc/MassModels_Lelli2016c.mrt'), name)
    return make_axisymmetric_image(rc.R, rc.SBdisk, pix_kpc=0.2, size=256), 0.2


def downsample_avg(img: np.ndarray, factor: int) -> np.ndarray:
    if factor <= 1:
        return img
    h, w = img.shape[:2]
    nh = (h // factor) * factor
    nw = (w // factor) * factor
    if nh < factor or nw < factor:
        return img  # too small to downsample
    cropped = img[:nh, :nw]
    sh = cropped.reshape(nh // factor, factor, nw // factor, factor)
    return np.nanmean(np.nanmean(sh, axis=3), axis=1)


def fit_mu_alpha(g_obs, eg, g_gas, g_star0, g_add, mask):
    mb = mask & np.isfinite(g_add)
    w = 1.0 / np.maximum(eg[mb], 1e-6)
    X1 = g_star0[mb]; X2 = g_add[mb]
    Y  = g_obs[mb] - g_gas[mb]
    S11 = float(np.nansum(w*X1*X1)); S22 = float(np.nansum(w*X2*X2)); S12 = float(np.nansum(w*X1*X2))
    b1  = float(np.nansum(w*X1*Y));   b2  = float(np.nansum(w*X2*Y))
    det = S11*S22 - S12*S12
    if det <= 0: return 0.7, 0.0
    mu = (b1*S22 - b2*S12) / det
    a  = (S11*b2 - S12*b1) / det
    return float(mu), float(a)


def fit_mu_alpha_C(g_obs, eg, g_gas, g_star0, g_add, g_C, mask):
    mb = mask & np.isfinite(g_add) & np.isfinite(g_C)
    if not np.any(mb):
        return 0.7, 0.0, 0.0
    w = 1.0 / np.maximum(eg[mb], 1e-6)
    X1 = g_star0[mb]; X2 = g_add[mb]; X3 = g_C[mb]
    Y  = g_obs[mb] - g_gas[mb]
    # normal equations for 3 params
    S11 = float(np.nansum(w*X1*X1)); S22 = float(np.nansum(w*X2*X2)); S33 = float(np.nansum(w*X3*X3))
    S12 = float(np.nansum(w*X1*X2)); S13 = float(np.nansum(w*X1*X3)); S23 = float(np.nansum(w*X2*X3))
    b1  = float(np.nansum(w*X1*Y));  b2  = float(np.nansum(w*X2*Y));  b3  = float(np.nansum(w*X3*Y))
    M = np.array([[S11,S12,S13],[S12,S22,S23],[S13,S23,S33]], dtype=float)
    b = np.array([b1,b2,b3], dtype=float)
    try:
        sol = np.linalg.solve(M, b)
        mu, a, c = (float(sol[0]), float(sol[1]), float(sol[2]))
    except Exception:
        mu, a, c = (0.7, 0.0, 0.0)
    return mu, a, c


def aicc(chi, k, N):
    return float(chi + 2*k + (2*k*(k+1))/max(N-k-1,1))


def evaluate_one(name: str, beta: float, s_kpc: float, sgk: float, max_size: int, quick: bool, extra_c: bool=False, ws_s_list: list[float] | None = None):
    rc = read_sparc_massmodels(Path('data/sparc/MassModels_Lelli2016c.mrt'), name)
    R = rc.R; g_gas = (1.33*(rc.Vgas*rc.Vgas))/np.maximum(R,1e-6); g_star0 = (rc.Vdisk*rc.Vdisk+rc.Vbul*rc.Vbul)/np.maximum(R,1e-6)
    g_obs, eg = with_error_floor(R, rc.Vobs, rc.eV)
    # W·S baseline（公平グリッドで最良を選択）
    s_candidates = list(ws_s_list or [0.4, 0.6, 1.0])
    best_ws = (float('inf'), 0.8, 0.0, 0.0, 0)  # (AICc, s_ws, mu_ws, a_ws, N)
    for s_ws in s_candidates:
        g_ws = line_bias_accel(R, rc.SBdisk, pix_kpc=0.2, size=256, line_eps_kpc=float(s_ws), pad_factor=2)
        m_ws = np.isfinite(g_obs)&np.isfinite(eg)&np.isfinite(g_gas)&np.isfinite(g_star0)&np.isfinite(g_ws)
        if not np.any(m_ws):
            continue
        mu_ws_tmp, a_ws_tmp = fit_mu_alpha(g_obs, eg, g_gas, g_star0, g_ws, m_ws)
        chi_ws_tmp = chi2(g_obs[m_ws], eg[m_ws], (g_gas+mu_ws_tmp*g_star0+a_ws_tmp*g_ws)[m_ws])
        N_tmp = int(np.sum(m_ws)); A_ws_tmp = aicc(chi_ws_tmp, 2, N_tmp)
        if A_ws_tmp < best_ws[0]:
            best_ws = (A_ws_tmp, float(s_ws), float(mu_ws_tmp), float(a_ws_tmp), N_tmp)
    A_ws, s_ws_best, mu_ws, a_ws, N = best_ws
    rchi_ws = float((A_ws - 2*2 - (2*2*(2+1))/max(N-2-1,1)) / max(N-2,1)) if np.isfinite(A_ws) and N>2 else float('nan')
    # Phi·eta trial
    img, pix = load_ha_or_proxy(name)
    # memory guard: reduce image size while scaling pixel size accordingly
    try:
        H, W = int(img.shape[0]), int(img.shape[1])
        max_dim = max(H, W)
    except Exception:
        H = W = max_dim = 0
    if max_dim and max_dim > max_size:
        fac = int(np.ceil(max_dim / float(max_size)))
        img = downsample_avg(img, fac)
        pix = pix * fac
    k_grid = np.linspace(0.02, 1.2, 16 if quick else 24)
    phi_k = np.exp(-(k_grid/sgk)**2)
    g_if = info_bias_profile_from_map(R, img, pix_kpc=pix, k_grid=k_grid, phi_k=phi_k, eta_params=EtaParams(beta=beta, s_kpc=s_kpc))
    m = m_ws & np.isfinite(g_if)
    if not np.any(m):
        return {'name': name, 'ok': False}
    if extra_c:
        g_C = 1.0 / np.clip(R, 1e-6, None)
        mu_if, kappa, C = fit_mu_alpha_C(g_obs, eg, g_gas, g_star0, g_if, g_C, m)
        chi_if = chi2(g_obs[m], eg[m], (g_gas+mu_if*g_star0+kappa*g_if+C*g_C)[m])
        N_if = int(np.sum(m))
        A_if = aicc(chi_if, 3, N_if)
        rchi_if = float(chi_if / max(N_if-3, 1))
        return {'name': name, 'ok': True, 'AICc_ws': A_ws, 'AICc_if': A_if,
                'delta': float(A_if - A_ws), 'beta': beta, 's_kpc': s_kpc, 'sgk': sgk,
                'mu_if': mu_if, 'kappa': kappa, 'C': C, 'k': 3, 'N': N_if, 'rchi2': rchi_if, 'rchi2_ws': rchi_ws, 's_ws': s_ws_best}
    else:
        mu_if, kappa = fit_mu_alpha(g_obs, eg, g_gas, g_star0, g_if, m)
        chi_if = chi2(g_obs[m], eg[m], (g_gas+mu_if*g_star0+kappa*g_if)[m])
        N_if = int(np.sum(m))
        A_if = aicc(chi_if, 2, N_if)
        rchi_if = float(chi_if / max(N_if-2, 1))
        return {'name': name, 'ok': True, 'AICc_ws': A_ws, 'AICc_if': A_if,
                'delta': float(A_if - A_ws), 'beta': beta, 's_kpc': s_kpc, 'sgk': sgk,
                'mu_if': mu_if, 'kappa': kappa, 'k': 2, 'N': N_if, 'rchi2': rchi_if, 'rchi2_ws': rchi_ws, 's_ws': s_ws_best}


def main() -> int:
    import argparse
    ap = argparse.ArgumentParser(description='Fair sweep of Phi·eta params vs W·S (k=2, same N/error)')
    ap.add_argument('--names', type=str, default='NGC3198,NGC2403')
    ap.add_argument('--quick', action='store_true', help='use a tiny grid for fast sanity run')
    ap.add_argument('--max-size', type=int, default=256, help='cap image max dimension via average pooling')
    ap.add_argument('--phase-kernel', action='store_true', help='enable fixed interface-phase kernel (no extra dof)')
    ap.add_argument('--phase-kernel-profile', action='store_true', help='enable fixed radial phase profile φ0(R)=A(1-exp(-R/R0)) (no extra dof)')
    ap.add_argument('--r0-list', type=str, default='', help='comma-separated R0[kpc] values for phase-kernel-profile')
    ap.add_argument('--phi0', type=float, default=0.35, help='fixed phase shift (radians) when phase-kernel is on')
    ap.add_argument('--phi0-list', type=str, default='', help='optional comma-separated list of phi0 to try (each is fixed per trial)')
    ap.add_argument('--extra-c', action='store_true', help='add isotropic 1/R term (third parameter C) for Phi·eta')
    ap.add_argument('--beta', type=float, default=None, help='restrict to a single beta value')
    ap.add_argument('--s', type=float, default=None, help='restrict to a single s_kpc value')
    ap.add_argument('--sgk', type=float, default=None, help='restrict to a single sigma_k value')
    # New: explicit lists to align grids with representative tables (e.g., beta=0.0,0.3; s=0.4,0.6,1.0; sgk=0.5,0.8,1.2)
    ap.add_argument('--beta-list', type=str, default='', help='comma-separated beta values (overrides default grid)')
    ap.add_argument('--s-list', type=str, default='', help='comma-separated s_kpc values (overrides default grid)')
    ap.add_argument('--sgk-list', type=str, default='', help='comma-separated sigma_k values (overrides default grid)')
    ap.add_argument('--ws-s-list', type=str, default='0.4,0.6,1.0', help='comma-separated W·S s[kpc] grid used to pick best AICc_ws')
    args = ap.parse_args()
    names = [n.strip() for n in args.names.split(',') if n.strip()]
    if args.beta is not None and args.s is not None and args.sgk is not None:
        betas = [float(args.beta)]; svals = [float(args.s)]; sgks = [float(args.sgk)]
    elif args.quick:
        betas = [0.0, 0.3]
        svals = [0.5]
        sgks  = [0.6]
    else:
        # Optional overrides from explicit lists
        if args.beta_list.strip():
            try:
                betas = [float(x) for x in args.beta_list.split(',') if x.strip()]
            except Exception:
                betas = [0.0, 0.3]
        else:
            betas = [0.0, 0.3, 0.6]
        if args.s_list.strip():
            try:
                svals = [float(x) for x in args.s_list.split(',') if x.strip()]
            except Exception:
                svals = [0.4, 0.6, 1.0]
        else:
            svals = [0.3, 0.5, 0.8, 1.2]
        if args.sgk_list.strip():
            try:
                sgks = [float(x) for x in args.sgk_list.split(',') if x.strip()]
            except Exception:
                sgks = [0.5, 0.8, 1.2]
        else:
            sgks  = [0.3, 0.6, 1.0]
    out = []
    trials_path = Path('data/results/ws_vs_phieta_trials.ndjson')
    trials_path.parent.mkdir(parents=True, exist_ok=True)
    for nm in names:
        best = None
        phi0s = [args.phi0]
        if args.phase_kernel and args.phi0_list:
            try:
                phi0s = [float(x) for x in args.phi0_list.split(',') if x.strip()]
            except Exception:
                phi0s = [args.phi0]
        # parse WS s-grid once per galaxy
        try:
            ws_s_list = [float(x) for x in (args.ws_s_list or '').split(',') if x.strip()]
        except Exception:
            ws_s_list = [0.4, 0.6, 1.0]
        for b in betas:
            for s in svals:
                for sg in sgks:
                    r = evaluate_one(nm, b, s, sg, max_size=args.max_size, quick=args.quick, extra_c=args.extra_c, ws_s_list=ws_s_list)
                    if args.phase_kernel and r.get('ok'):
                        # overwrite by recomputing IF with phase shift but identical k (=r['k'])
                        # Re-evaluate only the IF side with phase shift
                        rc = read_sparc_massmodels(Path('data/sparc/MassModels_Lelli2016c.mrt'), nm)
                        R = rc.R; g_gas = (1.33*(rc.Vgas*rc.Vgas))/np.maximum(R,1e-6)
                        g_star0 = (rc.Vdisk*rc.Vdisk+rc.Vbul*rc.Vbul)/np.maximum(R,1e-6)
                        g_obs, eg = with_error_floor(R, rc.Vobs, rc.eV)
                        img, pix = load_ha_or_proxy(nm)
                        # downsample guard
                        try:
                            H, W = int(img.shape[0]), int(img.shape[1])
                            max_dim = max(H, W)
                        except Exception:
                            max_dim = 0
                        if max_dim and max_dim > args.max_size:
                            fac = int(np.ceil(max_dim / float(args.max_size)))
                            img = downsample_avg(img, fac); pix = pix * fac
                        k_grid = np.linspace(0.02, 1.2, 16 if args.quick else 24)
                        phi_k = np.exp(-(k_grid/sg)**2)
                        r0s = [3.0]
                        if args.phase_kernel_profile and args.r0_list:
                            try:
                                r0s = [float(x) for x in args.r0_list.split(',') if x.strip()]
                            except Exception:
                                r0s = [3.0]
                        for phi0 in phi0s:
                            for r0 in r0s:
                                etargs = EtaParams(beta=b, s_kpc=s, phase_shift=phi0)
                                if args.phase_kernel_profile:
                                    # fixed profile with base amplitude = |phi0|, R0 candidate
                                    etargs.phase_profile_base = abs(phi0); etargs.phase_profile_R0_kpc = float(r0)
                                    etargs.phase_shift = 0.0
                                g_if2 = info_bias_profile_from_map(R, img, pix_kpc=pix, k_grid=k_grid, phi_k=phi_k,
                                    eta_params=etargs)
                                m = np.isfinite(g_obs)&np.isfinite(eg)&np.isfinite(g_gas)&np.isfinite(g_star0)&np.isfinite(g_if2)
                                if np.any(m):
                                    if r['k'] == 3 and args.extra_c:
                                        g_C = 1.0 / np.clip(R, 1e-6, None)
                                        mu2, kap2, C2 = fit_mu_alpha_C(g_obs, eg, g_gas, g_star0, g_if2, g_C, m)
                                        chi2_if = chi2(g_obs[m], eg[m], (g_gas+mu2*g_star0+kap2*g_if2+C2*g_C)[m])
                                        A_if2 = aicc(chi2_if, 3, int(np.sum(m)))
                                    else:
                                        mu2, kap2 = fit_mu_alpha(g_obs, eg, g_gas, g_star0, g_if2, m)
                                        chi2_if = chi2(g_obs[m], eg[m], (g_gas+mu2*g_star0+kap2*g_if2)[m])
                                        A_if2 = aicc(chi2_if, 2, int(np.sum(m)))
                                    if A_if2 < r['AICc_if']:
                                        r.update({'AICc_if': A_if2, 'delta': float(A_if2 - r['AICc_ws']), 'mu_if': mu2, 'kappa': kap2})
                                        if r['k'] == 3 and args.extra_c:
                                            r.update({'C': C2})
                    # end phase-kernel branch
                    if not r.get('ok'): continue
                    # append trial row (for global merge/monitoring)
                    try:
                        trials_path.open('a', encoding='utf-8').write(json.dumps(r)+'\n')
                    except Exception:
                        pass
                    if best is None or r['delta'] < best['delta']:
                        best = r
        if best is not None:
            out.append(best)
    Path('data/results').mkdir(parents=True, exist_ok=True)
    Path('data/results/ws_vs_phieta_fair_best.json').write_text(json.dumps(out, indent=2), encoding='utf-8')
    # HTML summary
    rep = ['<html lang="ja-JP"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">',
           '<title>Phi·eta fair sweep</title><link rel="stylesheet" href="../styles.css"></head><body>',
           '<header class="site-header"><div class="wrap"><div class="brand">研究進捗</div><nav class="nav"><a href="../index.html">レポート</a><a href="../state_of_the_art/index.html">SOTA</a></nav></div></header>',
           '<main class="wrap"><h1>Phi·eta パラメタ（公平: k=2, 同一N/誤差）スイープ</h1>']
    if out:
        wins = sum(1 for r in out if r['delta'] < 0)
        med = float(np.median([r['delta'] for r in out]))
        q1, q3 = np.percentile([r['delta'] for r in out], [25, 75]); iqr = float(q3-q1)
        rep.append(f'<div class=card><p>勝ち数(Phi·eta): {wins} / {len(out)}（ΔAICc<0勝ち）</p>'
                   f'<p>ΔAICc(Phi·eta−W·S) 中央値[IQR]: {med:.2f} [{iqr:.2f}]</p>'
                   '<p><small>両方式で Υ★とα(κ) を同時最小二乗（k=2）。</small></p></div>')
        # concise policy footnote
        rep.append('<div class=card><small>AICc は per‑galaxy の観測点 N と自由度 k に基づき算出。'
                   ' rχ² は χ²/(N−k) を用い、誤差床は dV_floor=clip(0.03×|Vobs|, 3..7) km/s を適用。</small></div>')
        rep.append('<table><thead><tr><th>Galaxy</th><th>best β</th><th>s[kpc]</th><th>σ_k</th><th>k</th><th>N</th><th>rχ²(IF)</th><th>rχ²(WS)</th><th>ΔAICc</th><th>AICc(IF/WS)</th><th>links</th></tr></thead><tbody>')
        for r in out:
            nm = r['name']
            prof = Path('server/public/reports') / f"{nm.lower()}_phieta_profile.html"
            bench = f'bench_{nm.lower()}.html'
            link_parts = []
            if prof.exists():
                link_parts.append(f'<span class="pill-links"><a href="{prof.name}">profile</a></span>')
            if (Path('server/public/reports')/bench).exists():
                link_parts.append(f'<span class="pill-links"><a href="{bench}">bench</a></span>')
            ji = Path('server/public/reports') / f"{nm.lower()}_JI_vector_panel.html"
            if ji.exists():
                link_parts.append(f'<span class="pill-links"><a href="{ji.name}">JI vector</a></span>')
            # local stability / outer slope stability
            loc = Path('server/public/reports') / f"{nm.lower()}_local_stability.html"
            if loc.exists():
                link_parts.append(f'<span class="pill-links"><a href="{loc.name}">local stability</a></span>')
            oss = Path('server/public/reports') / f"{nm.lower()}_outer_slope_stability.html"
            if oss.exists():
                link_parts.append(f'<span class="pill-links"><a href="{oss.name}">outer slope</a></span>')
            link = ' · '.join(link_parts)
            kcol = int(r.get('k', 2))
            Ncol = int(r.get('N', 0)); rc2 = float(r.get('rchi2', float('nan'))); rc2w = float(r.get('rchi2_ws', float('nan')))
            a_if = float(r.get('AICc_if', float('nan'))); a_ws = float(r.get('AICc_ws', float('nan')))
            a_pair = f'<small>{a_if:.1f} / {a_ws:.1f}</small>'
            rep.append(f"<tr><td>{nm}</td><td>{r['beta']:.2f}</td><td>{r['s_kpc']:.2f}</td><td>{r['sgk']:.2f}</td><td>{kcol:d}</td><td>{Ncol:d}</td><td>{rc2:.2f}</td><td>{rc2w:.2f}</td><td>{r['delta']:.2f}</td><td>{a_pair}</td><td>{link}</td></tr>")
        rep.append('</tbody></table>')
        # Quick panels (thumbnails) per galaxy if assets exist
        rep.append('<h2>Quick Panels</h2>')
        for r in out:
            nm = r['name']
            base = Path('server/public/reports')
            thumbs = []
            # κ profile thumbnail
            prof_png = base / f"{nm.lower()}_phieta_profile.png"
            if prof_png.exists():
                thumbs.append(f'<div class="card"><p><b>{nm}: κプロファイル</b></p><img src="{prof_png.name}" style="max-width:100%"></div>')
            # JI vector panel
            ji_png = base / f"{nm.lower()}_JI_vector_panel.png"
            if ji_png.exists():
                thumbs.append(f'<div class="card"><p><b>{nm}: J_I ベクトル（β=0/β>0）</b></p><img src="{ji_png.name}" style="max-width:100%"></div>')
            # local stability
            loc_png = base / f"{nm.lower()}_local_dAICc_heat.png"
            if loc_png.exists():
                thumbs.append(f'<div class="card"><p><b>{nm}: ΔAICc ヒート</b></p><img src="{loc_png.name}" style="max-width:100%"></div>')
            # outer slope stability
            oss_png = base / f"{nm.lower()}_outer_slope_stability.png"
            if oss_png.exists():
                thumbs.append(f'<div class="card"><p><b>{nm}: 外縁傾き 安定性</b></p><img src="{oss_png.name}" style="max-width:100%"></div>')
            # ω_cut vs residual maps
            wcut_maps = base / f"{nm.lower()}_wcut_vs_vres_maps.png"
            if wcut_maps.exists():
                thumbs.append(f'<div class="card"><p><b>{nm}: ω_cut × 残差（地図）</b></p><img src="{wcut_maps.name}" style="max-width:100%"></div>')
            if thumbs:
                rep.extend(thumbs)
    else:
        rep.append('<div class=card><p><small>有効な結果がありません。</small></p></div>')
    rep.append('</main></body></html>')
    Path('server/public/reports').mkdir(parents=True, exist_ok=True)
    Path('server/public/reports/ws_vs_phieta_fair.html').write_text('\n'.join(rep), encoding='utf-8')
    print('wrote server/public/reports/ws_vs_phieta_fair.html')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
