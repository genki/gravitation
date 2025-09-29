#!/usr/bin/env python3
from __future__ import annotations
import json
import random
import subprocess as sp
from pathlib import Path
from typing import Dict, Any, List, Tuple

LAM_GRID = [18.0, 20.0, 22.0, 24.0]
A_GRID = [100.0, 112.0, 125.0]
GAS_GRID = [1.0, 1.33]
COMMON_ARGS = [
    "--boost", "0.5", "--boost-tie-lam", "--auto-geo",
    "--pad-factor", "2", "--eg-frac-floor", "0.15", "--inv1-orth", "--line-eps", "0.8",
]

def load_names(p: Path) -> List[str]:
    return [ln.strip() for ln in p.read_text(encoding='utf-8').splitlines() if ln.strip() and not ln.strip().startswith('#')]

def write_names(p: Path, arr: List[str]) -> None:
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text("\n".join(arr) + "\n", encoding='utf-8')

def run_multi(names_file: Path, out_json: Path) -> Dict[str, Any]:
    args = [
        "PYTHONPATH=.", "./.venv/bin/python", "scripts/compare_fit_multi.py",
        "--names-file", str(names_file),
        *COMMON_ARGS,
        "--lam-grid", ",".join(str(x) for x in LAM_GRID),
        "--A-grid", ",".join(str(x) for x in A_GRID),
        "--gas-scale-grid", ",".join(str(x) for x in GAS_GRID),
        "--out", str(out_json),
    ]
    sp.run(" ".join(args), shell=True, check=True)
    return json.loads(out_json.read_text(encoding='utf-8'))

def bootstrap(names: List[str], B: int, seed: int, out_json: Path) -> Dict[str, Any]:
    rnd = random.Random(seed)
    picks: List[Tuple[float, float, float]] = []  # (lam, A, gas)
    for b in range(B):
        sample = [rnd.choice(names) for _ in range(len(names))]
        tmp = Path('data/sparc/sets/_boot_tmp_nobl.txt')
        write_names(tmp, sample)
        res = run_multi(tmp, Path(f'data/results/_boot_nobl_{b+1}.json'))
        picks.append((float(res.get('lam')), float(res.get('A')), float(res.get('gas_scale'))))
    from collections import Counter
    c_lam = Counter(l for l, _, _ in picks)
    c_A = Counter(a for _, a, _ in picks)
    c_g = Counter(g for _, _, g in picks)
    out = {
        'B': B,
        'lam_hist': dict(c_lam),
        'A_hist': dict(c_A),
        'gas_hist': dict(c_g),
        'picks': [{'lam': l, 'A': a, 'gas_scale': g} for (l, a, g) in picks],
        'grid': {'lam': LAM_GRID, 'A': A_GRID, 'gas': GAS_GRID},
    }
    out_json.parent.mkdir(parents=True, exist_ok=True)
    out_json.write_text(json.dumps(out, indent=2), encoding='utf-8')
    return out

def main() -> int:
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument('--names-file', type=Path, default=Path('data/sparc/sets/clean_no_blacklist.txt'))
    ap.add_argument('--B', type=int, default=8)
    ap.add_argument('--seed', type=int, default=20250902)
    args = ap.parse_args()
    names = load_names(args.names_file)
    out = bootstrap(names, args.B, args.seed, Path('data/results/boot_nobl.json'))
    # quick bars
    try:
        import matplotlib
        matplotlib.use('Agg')
        import matplotlib.pyplot as plt
        from scripts.utils.mpl_fonts import use_jp_font
        use_jp_font()
        import numpy as np
        def bar_from_hist(h: Dict[float, int], title: str, outp: Path):
            ks = sorted(h.keys())
            vs = [h[k] for k in ks]
            xs = np.arange(len(ks))
            plt.figure(figsize=(4.0,2.8), dpi=160)
            plt.bar(xs, vs, color='#4e79a7')
            plt.xticks(xs, [str(k) for k in ks])
            plt.title(title)
            plt.tight_layout(); outp.parent.mkdir(parents=True, exist_ok=True); plt.savefig(outp); plt.close()
        bar_from_hist(out['lam_hist'], 'noBL: λ bootstrap mode', Path('assets/figures/boot_lam_nobl.png'))
        bar_from_hist(out['A_hist'], 'noBL: A bootstrap mode', Path('assets/figures/boot_A_nobl.png'))
    except Exception as e:
        print('warn: plotting skipped:', e)
    print('wrote bootstrap to data/results/boot_nobl.json')
    return 0

if __name__ == '__main__':
    raise SystemExit(main())
