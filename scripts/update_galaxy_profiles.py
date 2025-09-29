#!/usr/bin/env python3
from __future__ import annotations
import re
import json
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any, Tuple

from scripts.fit_sparc_fdbl import read_sparc_massmodels, read_sparc_meta
from scripts.compare_fit_multi import model_ulw_accel
import numpy as np


def pick_sota_galaxies(sota_html: Path) -> List[str]:
    html = sota_html.read_text(encoding='utf-8')
    names: List[str] = []
    for m in re.finditer(r"paper/figures/tri_compare_([A-Za-z0-9\-]+)\.svg", html):
        names.append(m.group(1))
    for m in re.finditer(r"paper/figures/compare_fit_([A-Za-z0-9\-]+)_shared\.svg", html):
        nm = m.group(1)
        if nm not in names:
            names.append(nm)
    seen = set(); out = []
    for nm in names:
        if nm in seen: continue
        seen.add(nm); out.append(nm)
    return out


def load_latest_multi() -> Dict[str, Any] | None:
    res = sorted(Path('data/results').glob('multi_fit_cv_train_*.json'), key=lambda p: p.stat().st_mtime, reverse=True)
    if not res:
        res = sorted(Path('data/results').glob('multi_fit*.json'), key=lambda p: p.stat().st_mtime, reverse=True)
    if not res:
        return None
    try:
        return json.loads(res[0].read_text(encoding='utf-8'))
    except Exception:
        return None


def per_gal_ulw_stats(nm: str, shared: Dict[str, Any]) -> Tuple[float, int, float]:
    rc = read_sparc_massmodels(Path('data/sparc/MassModels_Lelli2016c.mrt'), nm)
    R = rc.R; Rm = np.maximum(R, 1e-6)
    Vobs = rc.Vobs; eV = np.maximum(rc.eV, 1e-6)
    floor = np.clip(0.03 * np.abs(Vobs), 3.0, 7.0)
    eVe = np.sqrt(eV**2 + floor**2)
    g_obs = (Vobs * Vobs) / Rm
    eg_obs = 2.0 * Vobs * np.maximum(eVe, 1e-6) / Rm
    w = 1.0 / np.maximum(eg_obs, 1e-6)
    g_gas = (rc.Vgas * rc.Vgas) / Rm
    vstar2 = rc.Vdisk * rc.Vdisk + rc.Vbul * rc.Vbul
    g_star = vstar2 / Rm
    lam = float(shared.get('lam', 20.0)); A = float(shared.get('A', 1.0))
    g_ulw1 = model_ulw_accel(R, rc.SBdisk, lam_kpc=lam, A=1.0, pix_kpc=0.2, size=256,
                             boost=0.5, s1_kpc=lam/8.0, s2_kpc=lam/3.0, pad_factor=2)
    mu_ulw = None
    mu_node = (shared.get('mu', {}).get('ULW', {}) or {}).get(nm, {})
    if isinstance(mu_node, dict):
        mu_ulw = float(mu_node.get('mu', mu_node.get('mu_d', 0.6)))
    elif isinstance(mu_node, (int, float)):
        mu_ulw = float(mu_node)
    else:
        mu_ulw = 0.6
    gas_scale = float(shared.get('gas_scale', 1.0))
    g_model = gas_scale * g_gas + mu_ulw * g_star + A * g_ulw1
    m = np.isfinite(g_obs) & np.isfinite(eg_obs) & np.isfinite(g_model)
    N = int(np.sum(m))
    chi = float(np.nansum(((g_model[m] - g_obs[m]) * w[m]) ** 2))
    rchi = chi / max(N - 1, 1)
    return rchi, N, mu_ulw


def summarize_meta(nm: str) -> Dict[str, Any]:
    meta = read_sparc_meta(Path('data/sparc/SPARC_Lelli2016c.mrt'), nm)
    d: Dict[str, Any] = {}
    for key in ['D', 'inc', 'T', 'L']:
        if hasattr(meta, key):
            d[key] = getattr(meta, key)
    return d


def write_profile(nm: str, data: Dict[str, Any], out: Path) -> None:
    out.parent.mkdir(parents=True, exist_ok=True)
    now = datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')
    shared = {
        'lam': data.get('lam'), 'A': data.get('A'), 'gas_scale': data.get('gas_scale'), 'mu': data.get('mu', {})
    }
    try:
        rchi, N, mu_ulw = per_gal_ulw_stats(nm, shared)
    except Exception:
        rchi, N, mu_ulw = (float('nan'), 0, float('nan'))
    mu_gr_node = (data.get('mu', {}).get('GR', {}) or {}).get(nm, {})
    mu_gr = mu_gr_node.get('mu') if isinstance(mu_gr_node, dict) else mu_gr_node
    ml_gr = f"{mu_gr:.3g}" if isinstance(mu_gr, (int, float)) else '-'
    ml_ulw = f"{mu_ulw:.3g}" if isinstance(mu_ulw, (int, float)) else '-'
    tri = Path('paper/figures') / f'tri_compare_{nm}.svg'
    tri_tag = f"<img src='../../paper/figures/{tri.name}' style='max-width:100%;height:auto'>" if tri.exists() else ""
    meta = summarize_meta(nm)
    lines = []
    lines.append(f"## Auto Profile ({now})\n")
    lines.append(f"- 概要: SPARC銀河 {nm}。T={meta.get('T','?')}, 距離 D={meta.get('D','?')} Mpc, 傾斜 inc={meta.get('inc','?')} 度。")
    lines.append(f"- 共有 μ(k): ε={data.get('mu_k',{}).get('eps','?')}, k0={data.get('mu_k',{}).get('k0','?')} kpc⁻¹, m={data.get('mu_k',{}).get('m','?')}, gas={data.get('gas_scale','?')}")
    lines.append(f"- ML(Υ★): GR={ml_gr}, ULW={ml_ulw}")
    lines.append(f"- ULW適合: rχ²≈{rchi:.2f}（N={N}）")
    if tri_tag:
        lines.append("\n<figure>" + tri_tag + f"<figcaption>{nm}: GR+DM/MOND/FDB 三面図</figcaption></figure>\n")
    if out.exists():
        txt = out.read_text(encoding='utf-8')
        txt += "\n\n" + "\n".join(lines) + "\n"
        out.write_text(txt, encoding='utf-8')
    else:
        hdr = f"# {nm} プロファイル\n\n"
        out.write_text(hdr + "\n".join(lines) + "\n", encoding='utf-8')


def main() -> int:
    sota = Path('server/public/state_of_the_art/index.html')
    if not sota.exists():
        raise SystemExit('SOTA HTML not found')
    names = pick_sota_galaxies(sota)
    data = load_latest_multi()
    if not data:
        raise SystemExit('multi_fit*.json not found')
    for nm in names:
        write_profile(nm, data, Path('memo/galaxies') / f'{nm}.md')
        print('updated profile:', nm)
    return 0


if __name__ == '__main__':
    raise SystemExit(main())

