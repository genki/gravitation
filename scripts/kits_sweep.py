#!/usr/bin/env python3
from __future__ import annotations
import os, sys
import json
from pathlib import Path
from typing import Dict, Any, List


def ensure_kits_on_path() -> None:
    kits = Path('kits/.work')
    if kits.exists():
        sys.path.insert(0, str(kits.resolve()))


def sweep() -> Dict[str, Any]:
    ensure_kits_on_path()
    from solar_conjunction import AchromaticShapiroResidualModel
    from frb_lens_blur import FRBAchromaticBlurModel
    from pta_shape import PTACorrelationShapeTest
    from common import R_sun
    import numpy as np
    # Solar conjunction: vary xi and b
    xi_list = [5.0, 10.0, 20.0]  # ps*Rsun^2
    b_Rsun = np.array([3,5,10,20,50], dtype=float)
    sol_rows: List[Dict[str, Any]] = []
    for xi in xi_list:
        sc = AchromaticShapiroResidualModel(sigma0_ps=5.0, xi_ps_Rsun2=float(xi))
        sigs = sc.sigma_ps(b_Rsun * R_sun)
        for b, s in zip(b_Rsun, sigs):
            sol_rows.append({'xi_ps_Rsun2': xi, 'b_Rsun': float(b), 'sigma_ps': float(s)})

    # FRB: vary kappa, tau0
    kappa = np.array([0.1, 0.2, 0.5, 1.0], dtype=float)
    tau0_list = [20.0, 50.0, 100.0]
    frb_rows: List[Dict[str, Any]] = []
    for tau0 in tau0_list:
        frb = FRBAchromaticBlurModel(tau0_us=float(tau0))
        tau = frb.tau_achr_us(kappa)
        for k, t in zip(kappa, tau):
            frb_rows.append({'tau0_us': tau0, 'kappa_eff': float(k), 'tau_achr_us': float(t)})

    # PTA: vary f_nonTT
    fvals = np.linspace(0.0, 0.05, 11)
    pta_rows: List[Dict[str, Any]] = []
    th = np.linspace(1e-3, np.pi-1e-3, 512)
    for f in fvals:
        pta = PTACorrelationShapeTest(f_nonTT=float(f))
        rms = pta.rms_shape_deviation(th, alt='flat')
        need = pta.required_pairs(rms_dev=rms, sigma_pair=0.05)
        pta_rows.append({'f_nonTT': float(f), 'rms_dev': float(rms), 'N_pairs@0.05': int(need)})

    out = {'solar': sol_rows, 'frb': frb_rows, 'pta': pta_rows}
    Path('server/public/kits').mkdir(parents=True, exist_ok=True)
    Path('server/public/kits/sweep.json').write_text(json.dumps(out, indent=2), encoding='utf-8')
    # Simple HTML report
    def h(s: str) -> str:
        return (str(s).replace('&','&amp;').replace('<','&lt;').replace('>','&gt;').replace('"','&quot;'))
    rows: List[str] = []
    rows.append('<h1>Research Kits Sweep (Solar/FRB/PTA)</h1>')
    rows.append('<h2>Solar conjunction (achromatic residual)</h2>')
    rows.append('<table><thead><tr><th>xi [ps Rsun^2]</th><th>b [Rsun]</th><th>RMS [ps]</th></tr></thead><tbody>')
    for r in sol_rows[:20]:
        rows.append(f"<tr><td>{h(r['xi_ps_Rsun2'])}</td><td>{h(r['b_Rsun'])}</td><td>{h(r['sigma_ps'])}</td></tr>")
    rows.append('</tbody></table>')
    rows.append('<h2>FRB achromatic blur</h2>')
    rows.append('<table><thead><tr><th>tau0 [µs]</th><th>kappa_eff</th><th>tau_achr [µs]</th></tr></thead><tbody>')
    for r in frb_rows[:20]:
        rows.append(f"<tr><td>{h(r['tau0_us'])}</td><td>{h(r['kappa_eff'])}</td><td>{h(r['tau_achr_us'])}</td></tr>")
    rows.append('</tbody></table>')
    rows.append('<h2>PTA correlation shape</h2>')
    rows.append('<table><thead><tr><th>f_nonTT</th><th>RMS dev</th><th>N pairs @ σ_pair=0.05</th></tr></thead><tbody>')
    for r in pta_rows:
        rows.append(f"<tr><td>{h(r['f_nonTT'])}</td><td>{h(r['rms_dev'])}</td><td>{h(r['N_pairs@0.05'])}</td></tr>")
    rows.append('</tbody></table>')
    html = (
        '<!doctype html><html lang="ja-JP"><head><meta charset="utf-8">'
        '<meta name="viewport" content="width=device-width,initial-scale=1">'
        '<title>Kits Sweep</title><link rel="stylesheet" href="/styles.css"></head><body>'
        '<header class="site-header"><div class="wrap"><div class="brand">研究進捗</div>'
        '<nav class="nav"><a href="/">ホーム</a><a href="/kits/">Kits</a>'
        '<a href="/state_of_the_art/">SOTA</a></nav></div></header>'
        '<main class="wrap">' + "\n".join(rows) + '</main>'
        '<footer class="site-footer"><div class="wrap">ローカル配信</div></footer></body></html>'
    )
    Path('server/public/kits/sweep.html').write_text(html, encoding='utf-8')
    return out


def main() -> int:
    sweep()
    print('wrote kits sweep to server/public/kits/sweep.html')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
