#!/usr/bin/env python3
from __future__ import annotations
import re
from pathlib import Path


def read_vars(p: Path) -> dict:
    d: dict[str, str] = {}
    if not p.exists():
        return d
    for ln in p.read_text(encoding='utf-8').splitlines():
        m = re.match(r"^([A-Za-z0-9_\.]+):\s*(.*)$", ln.strip())
        if not m:
            continue
        k, v = m.group(1), m.group(2)
        d[k] = v
    return d


def main() -> int:
    root = Path(__file__).resolve().parents[2]
    vars_yml = root / 'paper/_variables.yml'
    out = root / 'paper/paper.tex'
    v = read_vars(vars_yml)
    title = v.get('title', 'Apparent Gravitation from FDB of ULM (formerly ULW-EM)')
    subtitle = v.get('subtitle', '')
    eps = v.get('params.mu_eps', v.get('mu_eps', '1.0'))
    k0 = v.get('params.mu_k0', v.get('mu_k0', '0.2'))
    mm = v.get('params.mu_m', v.get('mu_m', '2'))
    gas = v.get('params.gas_scale', v.get('gas_scale', '1.33'))
    dA = v.get('params.delta_aicc', v.get('delta_aicc', '0'))
    Ntot = v.get('params.N_total', v.get('N_total', '0'))
    Kgr = v.get('params.k_sum_gr', v.get('k_sum_gr', '0'))
    Kulw = v.get('params.k_sum_ulw', v.get('k_sum_ulw', '0'))
    shf = v.get('fingerprints.shared_params_json', '')
    cvf = v.get('fingerprints.cv_shared_summary_json', '')

    lines: list[str] = []
    lines += [
        '% arXiv-ready minimal TeX (revtex4-2)',
        '\\documentclass[twocolumn,nofootinbib]{revtex4-2}',
        '\\usepackage{amsmath,amssymb,graphicx,hyperref}',
        '\\hypersetup{colorlinks=true,linkcolor=blue,citecolor=blue,urlcolor=blue}',
        '\\newcommand{\\ulw}{\\mathrm{ULW}}',
        '\\newcommand{\\fdb}{\\mathrm{FDB}}',
        '\\begin{document}',
    ]
    lines.append('\\title{' + title + '\\\\vspace{0.3em}\\normalsize ' + subtitle + '}')
    lines += [
        '\\author{First Last}',
        '\\affiliation{Institute}',
        '\\date{\\today}',
        '\\begin{abstract}',
        'We present a minimal formulation of Future--Decoherence Bias (FDB) of the ultra-long electromagnetic mode (ULM; formerly ULW-EM) that produces apparent gravitation from observable baryons and the electron-density geometry. Under a strict fair-comparison protocol (common $n$, common error floor, common penalty AICc), FDB improves fits and recovers $1/r^2$ at outer radii. Shared $\\mu(k)$ is fixed ($\\epsilon=' + str(eps) + ', $k_0=' + str(k0) + '\\,\\mathrm{kpc}^{-1}$, $m=' + str(mm) + '$, $\\mathrm{gas\\_scale}=' + str(gas) + '$); only $\\Upsilon_\\*$ and $a_2$ vary per galaxy.',
        '\\end{abstract}',
        '\\maketitle',
        '',
        '\\section{Introduction}',
        'Context of GR+DM vs apparent-gravity hypothesis; contributions of this work.',
        '',
        '\\section{Theory (Minimal)}',
        'Two-layer split: isotropic GR-equivalent from $(\\rho_\\*,\\rho_\\mathrm{gas})$ and an additional interface $\\Sigma$ term from iso-$\\omega_\\mathrm{cut}$ surfaces; Lambert kernel as default.',
        '',
        '\\section{Data and Preprocessing}',
        'SPARC 3.6$\\mu$m mass, HI+He gas, H$\\alpha\\rightarrow$EM$\\rightarrow n_e\\rightarrow\\omega_\\mathrm{cut}$; velocity fields and tilted rings.',
        '',
        '\\section{Experimental Design (Fair Comparison)}',
        'Common $n$, error floor, and AICc; baselines (GR, MOND, GR+DM with c--M prior). FDB uses fixed shared $\\mu(k)$.',
        '',
        '\\section{Results: Benchmarks}',
        '\\begin{figure}[t]',
        '  \\centering',
        '  \\includegraphics[width=0.95\\linewidth]{figures/ngc3198_outer_gravity.png}',
        '  \\caption{NGC 3198: $g(R)R^2$ with outer linear fit (slope and 95\\% CI).}',
        '\\end{figure}',
        '',
        '\\section{Cross-Validation Summary}',
        'Aggregate $\\Delta\\mathrm{AICc} = ' + str(dA) + '$ ( $N=' + str(Ntot) + '$; $k_\\mathrm{GR}=' + str(Kgr) + '$, $k_\\mathrm{ULW}=' + str(Kulw) + '$ ).',
        '',
        '\\section{Negative-control Tests / Sensitivity / Ablations}',
        'Electron-density perturbation null tests and error-floor/$H_{\\rm cut}$ sensitivity.',
        '',
        '\\section{Discussion and Conclusions}',
        'Geometry, outer recovery; limits and future work. Reproducibility fingerprints: shared\\_params.json=' + shf + ', cv\\_shared\\_summary.json=' + cvf + '.',
        '',
        '\\bibliographystyle{apsrev4-2}',
        '\\bibliography{refs}',
        '\\end{document}',
    ]
    out.write_text('\n'.join(lines) + '\n', encoding='utf-8')
    print('wrote', out)
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
