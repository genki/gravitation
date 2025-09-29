#!/usr/bin/env python3
from __future__ import annotations
import json
from pathlib import Path
from typing import Dict, Any, List, Tuple
import math

def load_json(p: Path) -> Dict[str, Any]:
    return json.loads(p.read_text(encoding='utf-8'))

def extract_alpha(data: Dict[str, Any]) -> List[float]:
    res: List[float] = []
    ulw = data.get('mu', {}).get('ULW', {})
    for nm, v in ulw.items():
        if isinstance(v, dict) and ('alpha_line' in v):
            try:
                a = float(v['alpha_line'])
                if math.isfinite(a):
                    res.append(a)
            except Exception:
                pass
    return res

def stats(xs: List[float]) -> Dict[str, float]:
    if not xs:
        return {k: float('nan') for k in ['n','mean','p25','p50','p75']}
    xs2 = sorted(xs)
    n = len(xs2)
    def q(p: float) -> float:
        if n == 1:
            return xs2[0]
        i = p * (n - 1)
        lo = int(math.floor(i)); hi = int(math.ceil(i))
        t = i - lo
        return (1-t)*xs2[lo] + t*xs2[hi]
    m = sum(xs2)/n
    return {'n': n, 'mean': m, 'p25': q(0.25), 'p50': q(0.5), 'p75': q(0.75)}

def save_csv(rows: List[Tuple[str, float]], out: Path):
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text("name,alpha_line\n" + "\n".join(f"{n},{a}" for n,a in rows) + "\n", encoding='utf-8')

def main() -> int:
    base = Path('data/results')
    outd = Path('assets/results')
    figd = Path('assets/figures')
    # pick group files (fine)
    lsb = load_json(base / 'multi_fit_lsb_fineA112_orth_eps0.8_eg015.json')
    hsb = load_json(base / 'multi_fit_hsb_fineA112_orth_eps0.8_eg015.json')
    # extract per-galaxy alpha lists
    rows_l: List[Tuple[str, float]] = []
    rows_h: List[Tuple[str, float]] = []
    for nm, v in lsb.get('mu', {}).get('ULW', {}).items():
        if isinstance(v, dict) and ('alpha_line' in v):
            try:
                rows_l.append((nm, float(v['alpha_line'])))
            except Exception:
                pass
    for nm, v in hsb.get('mu', {}).get('ULW', {}).items():
        if isinstance(v, dict) and ('alpha_line' in v):
            try:
                rows_h.append((nm, float(v['alpha_line'])))
            except Exception:
                pass
    save_csv(rows_l, outd / 'alpha_line_lsb.csv')
    save_csv(rows_h, outd / 'alpha_line_hsb.csv')
    # compute stats and write JSON
    s = {
        'lsb': stats([a for _, a in rows_l]),
        'hsb': stats([a for _, a in rows_h]),
    }
    (outd / 'alpha_line_stats.json').write_text(json.dumps(s, indent=2), encoding='utf-8')
    # optional: quick histogram via matplotlib
    try:
        import matplotlib
        matplotlib.use('Agg')
        import matplotlib.pyplot as plt
        import numpy as np
        xs_l = np.array([a for _, a in rows_l], dtype=float)
        xs_h = np.array([a for _, a in rows_h], dtype=float)
        bins = np.linspace(0, max(np.nanmax(xs_l), np.nanmax(xs_h), 10), 30)
        plt.figure(figsize=(6,3.5), dpi=160)
        plt.hist(xs_l, bins=bins, alpha=0.6, label='LSB', color='#1f77b4')
        plt.hist(xs_h, bins=bins, alpha=0.6, label='HSB', color='#ff7f0e')
        plt.xlabel('alpha_line (unit)')
        plt.ylabel('count')
        plt.legend(frameon=False)
        plt.tight_layout()
        figd.mkdir(parents=True, exist_ok=True)
        plt.savefig(figd / 'alpha_line_lsb_hsb_hist.png')
        plt.close()
        print('saved figure:', figd / 'alpha_line_lsb_hsb_hist.png')
    except Exception as e:
        print('warn: histogram skipped:', e)
    print('wrote stats to', outd / 'alpha_line_stats.json')
    return 0

if __name__ == '__main__':
    raise SystemExit(main())

