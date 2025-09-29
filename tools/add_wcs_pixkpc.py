#!/usr/bin/env python3
from __future__ import annotations
import argparse
from pathlib import Path
from typing import Tuple
import re
from astropy.io import fits
from astropy.wcs import WCS
from astropy.cosmology import Planck18 as cosmo
import numpy as np

def parse_par_for_wcs(par_path: Path) -> Tuple[float,float,Tuple[float,float,float,float]]:
    ra = dec = None
    xmin=xmax=ymin=ymax = None
    for ln in par_path.read_text(encoding='utf-8', errors='ignore').splitlines():
        t = ln.strip()
        m = re.match(r"reference\s+3\s+([0-9.+-]+)\s+([0-9.+-]+)", t)
        if m:
            ra = float(m.group(1)); dec = float(m.group(2))
        if t.startswith('champ'):
            # next 4 lines or inline values may exist; try to capture values on subsequent lines
            pass
        m2 = re.match(r"xmin\s+([-0-9.+]+)", t)
        if m2: xmin = float(m2.group(1))
        m2 = re.match(r"xmax\s+([-0-9.+]+)", t)
        if m2: xmax = float(m2.group(1))
        m2 = re.match(r"ymin\s+([-0-9.+]+)", t)
        if m2: ymin = float(m2.group(1))
        m2 = re.match(r"ymax\s+([-0-9.+]+)", t)
        if m2: ymax = float(m2.group(1))
    if None in (ra, dec) or None in (xmin,xmax,ymin,ymax):
        raise RuntimeError("reference or champ not found in par")
    return ra, dec, (xmin,xmax,ymin,ymax)

def parse_par_zlens(par_path: Path) -> float:
    z = None
    for ln in par_path.read_text(encoding='utf-8', errors='ignore').splitlines():
        m = re.search(r"z[_ ]?lens\s+([0-9.]+)", ln)
        if m:
            try:
                z = float(m.group(1))
                break
            except Exception:
                pass
    if z is None:
        raise RuntimeError("z_lens not found in par")
    return z

def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument('--par', required=True, help='path to lenstool .par used (for WCS,z_lens)')
    ap.add_argument('--in', dest='inp', required=True, help='input FITS (kappa)')
    ap.add_argument('--out', required=True, help='output FITS path (standardized)')
    ap.add_argument('--cluster', required=True, help='cluster name for headers')
    args = ap.parse_args()
    par = Path(args.par); fin = Path(args.inp); fout = Path(args.out)
    ra0, dec0, (xmin,xmax,ymin,ymax) = parse_par_for_wcs(par)
    zl = parse_par_zlens(par)
    with fits.open(fin) as hdul:
        data = np.asarray(hdul[0].data, dtype=np.float32)
        ny, nx = data.shape
        # champ is in arcsec relative to reference; assume pixel grid spans [xmin,xmax]x[ymin,ymax]
        # CDELT in deg/pix
        cdelt_x_deg = (xmax - xmin) / float(nx) / 3600.0
        cdelt_y_deg = (ymax - ymin) / float(ny) / 3600.0
        # Define WCS: RA increases with +x (east), Dec with +y (north). FITS uses 1-based CRPIX
        w = WCS(naxis=2)
        w.wcs.ctype = ['RA---TAN','DEC--TAN']
        w.wcs.crval = [ra0, dec0]
        w.wcs.crpix = [ (0.0 - xmin) / ((xmax - xmin)/nx) + 0.5, (0.0 - ymin) / ((ymax - ymin)/ny) + 0.5 ]
        w.wcs.cdelt = np.array([cdelt_x_deg, cdelt_y_deg], dtype=float)
        hdr = w.to_header()
        # Compute PIXKPC at lens redshift (kpc per pixel)
        DA = cosmo.angular_diameter_distance(zl)  # Mpc
        arcsec_to_rad = np.deg2rad(1.0/3600.0)
        # pixel scale in radians (use average of |cdelt|)
        pix_rad = abs(cdelt_x_deg) * np.pi/180.0
        pix_kpc = (DA.value * 1000.0) * pix_rad  # kpc/pix
        # Write new primary HDU
        prihdr = hdul[0].header
        for k,v in hdr.items():
            prihdr[k] = v
        prihdr['BUNIT'] = ('dimensionless', 'Convergence kappa')
        prihdr['PIXKPC'] = (pix_kpc, 'kpc per pixel at z_lens')
        prihdr['Z_LENS'] = (zl, 'Lens redshift used for PIXKPC')
        prihdr['OBJECT'] = (args.cluster, 'Cluster name')
        prihdr['HISTORY'] = 'Standardized WCS/PIXKPC by add_wcs_pixkpc.py'
        hdu = fits.PrimaryHDU(data=data, header=prihdr)
        fout.parent.mkdir(parents=True, exist_ok=True)
        hdu.writeto(fout, overwrite=True)
    print(f"WROTE {fout} PIXKPC={pix_kpc:.6g} kpc/pix, z_lens={zl}")
    return 0

if __name__ == '__main__':
    raise SystemExit(main())

