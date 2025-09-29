#!/usr/bin/env python3
from __future__ import annotations
import argparse, gzip, io
from pathlib import Path
from typing import Optional
import numpy as np
from astropy.io import fits


def pick_primary_fits(cxo_dir: Path, prefer: Optional[str] = None) -> Optional[Path]:
    cand = []
    if prefer:
        p = cxo_dir / prefer
        if p.exists():
            return p
    for p in sorted(cxo_dir.glob('*full_img2.fits.gz')):
        try:
            sz = p.stat().st_size
        except Exception:
            sz = 0
        cand.append((sz, p))
    if not cand:
        return None
    cand.sort(reverse=True)
    return cand[0][1]


def compute_pixkpc(hdr: fits.Header) -> float:
    try:
        # Prefer CD matrix if present
        if ('CD1_1' in hdr) and ('CD2_2' in hdr):
            sx = abs(float(hdr['CD1_1'])); sy = abs(float(hdr['CD2_2']))
            sdeg = (sx + sy) / 2.0
        else:
            sdeg = abs(float(hdr.get('CDELT1', 0.0)))
        sarcsec = sdeg * 3600.0
        # Generic scale: 4.3333 kpc/arcsec (Bullet z~0.296)。他クラスターは目安値。実値は後で更新可。
        return float(sarcsec * 4.3333)
    except Exception:
        return 1.0


def main() -> int:
    ap = argparse.ArgumentParser(description='Build sigma_e.fits and omega_cut.fits from a Chandra primary full_img2 for a given cluster')
    ap.add_argument('--name', required=True, help='cluster name (directory under data/cluster)')
    ap.add_argument('--prefer', default=None, help='optional filename to use within cxo/ (e.g., acisf05356N004_full_img2.fits.gz)')
    args = ap.parse_args()

    root = Path('data/cluster') / args.name
    cxo_dir = root / 'cxo'
    if not cxo_dir.exists():
        print('missing', cxo_dir)
        return 2
    src = pick_primary_fits(cxo_dir, args.prefer)
    if src is None:
        print('no full_img2.fits.gz found in', cxo_dir)
        return 3
    # read gz fits
    with gzip.open(src, 'rb') as f:
        data = f.read()
    hdul = fits.open(io.BytesIO(data))
    img = hdul[0].data.astype(float)
    hdr = hdul[0].header.copy()
    pk = compute_pixkpc(hdr)
    hdr['PIXKPC'] = (pk, 'kpc per pixel (approx generic)')
    root.mkdir(parents=True, exist_ok=True)
    fits.writeto(root / 'sigma_e.fits', img.astype('f4'), hdr, overwrite=True)
    omega = np.sqrt(np.clip(img, a_min=0.0, a_max=None))
    fits.writeto(root / 'omega_cut.fits', omega.astype('f4'), hdr, overwrite=True)
    print('wrote', root / 'sigma_e.fits', 'and', root / 'omega_cut.fits', 'from', src.name)
    return 0


if __name__ == '__main__':
    raise SystemExit(main())

