#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Dict, List, Tuple

import numpy as np
import matplotlib
matplotlib.use('Agg')
from matplotlib import pyplot as plt
from matplotlib.ticker import MultipleLocator

from scripts.figs.io_rep6 import load_observed, load_model
try:
    from scripts.utils.mpl_fonts import use_jp_font as _use_jp_font  # optional
except Exception:
    _use_jp_font = None


COL = {
    'OBS': '#000000',
    'GR': '#888888',
    'GRDM': '#7f3fbf',
    'MOND': '#2ca02c',
    'FDB_WS': '#d62728',
    'FDB_IF': '#1f77b4',
}


def _png_meta(out: Path, meta: Dict[str, object]) -> None:
    try:
        from PIL import Image, PngImagePlugin
        im = Image.open(out)
        info = PngImagePlugin.PngInfo()
        info.add_text('Description', json.dumps(meta, ensure_ascii=False))
        # lightweight XMP payload
        xmp = (
            '<x:xmpmeta xmlns:x="adobe:ns:meta/">'
            '<rdf:RDF xmlns:rdf="http://www.w3.org/1999/02/22-rdf-syntax-ns#">'
            '<rdf:Description xmlns:rep6="https://example/ns/rep6"'
            + ''.join([f' rep6:{k}="{meta.get(k)}"' for k in ('N','k','rchi2','AICc','seed','shared_sha')]) +
            '/></rdf:RDF></x:xmpmeta>'
        )
        info.add_itxt('XML:com.adobe.xmp', xmp, zip=False)
        im.save(out, pnginfo=info)
    except Exception:
        pass


def _footnote_line(meta_baseline: Dict[str, object], deltas: Dict[str, float], seed: int, shared_sha: str) -> str:
    return (
        f"N={int(meta_baseline['N'])}, k={int(meta_baseline['k'])}, "
        f"rχ²={float(meta_baseline['rchi2']):.3f}, AICc={float(meta_baseline['AICc']):.1f}, "
        f"ΔAICc(IF/GRDM/MOND)={deltas['FDB_IF']:+.1f}/{deltas['GRDM']:+.1f}/{deltas['MOND']:+.1f}, "
        f"σ_floor=clip(0.03×V,3..7) km/s, rng={seed}, shared_sha={shared_sha}"
    )


def plot_one(gal: str, out_path: Path, force_template: bool = False) -> Dict[str, object]:
    obs = load_observed(gal)
    floor = np.clip(0.03 * np.abs(obs.V), 3.0, 7.0)
    # Models
    gr = load_model(gal, 'GR')
    grdm = load_model(gal, 'GRDM')
    mond = load_model(gal, 'MOND')
    fws = load_model(gal, 'FDB_WS')
    fif = load_model(gal, 'FDB_IF')
    # Fair N: use baseline FDB_WS meta
    baseline = fws['meta']  # type: ignore
    # ΔAICc vs baseline
    deltas = {
        'FDB_IF': float(fif['meta']['AICc']) - float(baseline['AICc']),  # type: ignore
        'GRDM': float(grdm['meta']['AICc']) - float(baseline['AICc']),    # type: ignore
        'MOND': float(mond['meta']['AICc']) - float(baseline['AICc']),    # type: ignore
    }

    # Axes limits
    x = obs.R
    x0, x1 = float(np.nanmin(x)), float(np.nanmax(x))
    xr = (x0 + 0.02 * (x1 - x0), x1 * 1.02)
    vmax = float(np.nanmax(obs.V + 1.2 * floor))
    vmin = float(np.nanmin(obs.V - 1.2 * floor))

    if _use_jp_font:
        try:
            _use_jp_font()
        except Exception:
            pass
    fig = plt.figure(figsize=(6.0, 5.0), dpi=150)
    gs = fig.add_gridspec(2, 1, height_ratios=[2.0, 1.0], hspace=0.1)
    ax = fig.add_subplot(gs[0, 0])
    axr = fig.add_subplot(gs[1, 0], sharex=ax)

    # Observations
    ax.errorbar(obs.R, obs.V, yerr=floor, fmt='o', ms=3.5, color=COL['OBS'], alpha=0.9, label='観測')

    def draw_total(ax, arr: Dict[str, object], color: str, label: str):
        ax.plot(obs.R, arr['V_total'], color=color, lw=2.2, label=label)

    # Totals
    draw_total(ax, gr, COL['GR'], 'GR（可視のみ, Total）')
    draw_total(ax, grdm, COL['GRDM'], 'GR+DM(NFW, Total)')
    draw_total(ax, mond, COL['MOND'], 'MOND（Total）')
    draw_total(ax, fws, COL['FDB_WS'], 'FDB‑W·S（Total）')
    draw_total(ax, fif, COL['FDB_IF'], 'FDB‑Φ·η（Total）')
    # FDB addition as dashed thin
    ax.plot(obs.R, fws['V_add'], color=COL['FDB_WS'], lw=1.2, ls='--', alpha=0.7, label='FDB追加（W·S）')
    ax.plot(obs.R, fif['V_add'], color=COL['FDB_IF'], lw=1.2, ls='--', alpha=0.7, label='FDB追加（Φ·η）')

    ax.set_xlim(*xr)
    ax.set_ylim(vmin, vmax)
    ax.set_ylabel('速度 [km/s]')
    ax.grid(True, ls=':', alpha=0.4)
    ax.legend(ncol=2, fontsize=8, frameon=False)
    ax.yaxis.set_major_locator(MultipleLocator(10 if vmax - vmin > 120 else 5))

    # Residuals vs baseline FDB_WS Total
    res = obs.V - fws['V_total']  # type: ignore
    axr.axhline(0.0, color='#666', lw=1.0)
    band = 3.0 * floor
    axr.fill_between(obs.R, -band, band, color='#e6f2ff', alpha=0.6, label='±3σ')
    axr.plot(obs.R, res, color=COL['FDB_WS'], lw=1.2, label='残差（対 FDB‑W·S）')
    axr.set_xlim(*xr)
    axr.set_xlabel('半径 [kpc]')
    axr.set_ylabel('残差 [km/s]')
    axr.grid(True, ls=':', alpha=0.4)
    axr.legend(fontsize=8, frameon=False)
    axr.yaxis.set_major_locator(MultipleLocator(10 if vmax - vmin > 120 else 5))

    # Mini table (AICc / rχ² / ΔAICc vs W·S)
    rows = [
        ('GR+DM', grdm['meta']),
        ('MOND', mond['meta']),
        ('FDB‑W·S', fws['meta']),
        ('FDB‑Φ·η', fif['meta']),
    ]
    table_lines = []
    for name, m in rows:
        aic = float(m['AICc'])
        rchi = float(m['rchi2'])
        da = aic - float(baseline['AICc'])
        table_lines.append(f"{name}: AICc={aic:.1f} rχ²={rchi:.3f} ΔAICc={da:+.1f}")
    txt = '\n'.join(table_lines)
    ax.text(0.99, 0.02, txt, transform=ax.transAxes, va='bottom', ha='right', fontsize=7,
            bbox=dict(facecolor='white', alpha=0.8, edgecolor='none', boxstyle='round,pad=0.3'))

    # Footnote band
    seed = 42
    # shared sha
    try:
        shared_sha = hashlib.sha256(Path('data/shared_params.json').read_bytes()).hexdigest()[:12]
    except Exception:
        shared_sha = 'unknown'
    fn = _footnote_line(baseline, deltas, seed, shared_sha)
    fig.subplots_adjust(bottom=0.18)
    fig.text(0.01, 0.01, fn, fontsize=7)

    out_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out_path, dpi=150)

    # Also write SVG with embedded metadata
    out_svg = out_path.with_suffix('.svg')
    fig.savefig(out_svg, format='svg')
    try:
        svg = Path(out_svg).read_text(encoding='utf-8')
        meta_json = json.dumps({
            'N': int(baseline['N']), 'k': int(baseline['k']), 'rchi2': float(baseline['rchi2']),
            'AICc': float(baseline['AICc']), 'seed': seed, 'shared_sha': shared_sha
        }, ensure_ascii=False)
        svg = svg.replace('<svg ', '<svg xmlns:rep6="https://example/ns/rep6" ', 1)
        insert = f'<metadata id="rep6">{meta_json}</metadata>'
        svg = svg.replace('>', '>' + insert, 1)
        Path(out_svg).write_text(svg, encoding='utf-8')
    except Exception:
        pass

    plt.close(fig)

    # Embed PNG metadata
    _png_meta(out_path, meta={
        'N': int(baseline['N']), 'k': int(baseline['k']), 'rchi2': float(baseline['rchi2']),
        'AICc': float(baseline['AICc']), 'seed': seed, 'shared_sha': shared_sha
    })

    # Write sidecar JSON for injector
    meta_out = out_path.with_suffix('.json')
    meta_out.write_text(json.dumps({
        'galaxy': gal,
        'footnote': fn,
        'baseline': {'AICc': float(baseline['AICc']), 'rchi2': float(baseline['rchi2']), 'N': int(baseline['N']), 'k': int(baseline['k'])},
        'dAICc': deltas,
    }, ensure_ascii=False, indent=2), encoding='utf-8')
    return {
        'galaxy': gal,
        'img': str(out_path),
        'baseline': baseline,
        'deltas': deltas,
    }


def main() -> int:
    ap = argparse.ArgumentParser(description='rep6 unified plotting (Total baseline, template v2)')
    ap.add_argument('--all', action='store_true', help='plot all galaxies from data/sparc/sets/rep6.txt')
    ap.add_argument('--galaxy', type=str, default='', help='single galaxy name')
    ap.add_argument('--out', type=str, default='assets/rep6', help='output directory')
    ap.add_argument('--force-template', type=str, default='v2', help='placeholder for compatibility')
    args = ap.parse_args()
    out_dir = Path(args.out)
    if args.all:
        names = [ln.strip() for ln in Path('data/sparc/sets/rep6.txt').read_text(encoding='utf-8').splitlines() if ln.strip() and not ln.startswith('#')]
    else:
        if not args.galaxy:
            raise SystemExit('--galaxy is required without --all')
        names = [args.galaxy]
    results = []
    for nm in names:
        p = out_dir / f'{nm}_rep6.png'
        results.append(plot_one(nm, p, force_template=bool(args.force_template)))
    print('wrote', len(results), 'figures to', out_dir)
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
