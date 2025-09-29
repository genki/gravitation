#!/usr/bin/env python3
from __future__ import annotations
import json, math
from pathlib import Path
import argparse

import numpy as np
from astropy.io import fits


def cps_to_flux(cps: np.ndarray, photflam: float, fwhm: float, cw: float) -> np.ndarray:
    # SINGS推奨の概略式: F_line[erg s^-1 cm^-2] = 3e-5 * CPS * PHOTFLAM * (FWHM / CW^2)
    return (3e-5) * cps * float(photflam) * (float(fwhm) / (float(cw) ** 2))


def to_surface_brightness(F_line: np.ndarray, pixscale_arcsec: float) -> np.ndarray:
    Apix = (float(pixscale_arcsec) ** 2)
    return F_line / max(Apix, 1e-20)


def to_rayleigh(I_erg_arcsec2: np.ndarray) -> np.ndarray:
    # 1 R = 5.66e-18 erg s^-1 cm^-2 arcsec^-2 at H-alpha
    return I_erg_arcsec2 / 5.66e-18


def to_EM_pc_cm6(I_R: np.ndarray, Te: float = 1.0e4) -> np.ndarray:
    # EM[pc cm^-6] ≈ 2.75 * (Te/1e4 K)^0.9 * I_R
    return 2.75 * ((float(Te) / 1.0e4) ** 0.9) * I_R


def main() -> int:
    ap = argparse.ArgumentParser(description='Ingest H-alpha FITS (SINGS/IRSA) and calibrate to surface brightness + EM map')
    ap.add_argument('--in', dest='inp', type=Path, required=True, help='input FITS (HA_SUB)')
    ap.add_argument('--name', type=str, required=True, help='galaxy name (e.g., NGC3198)')
    ap.add_argument('--outdir', type=Path, default=Path('data/halpha'))
    ap.add_argument('--nii-ratio', type=float, default=None, help='[NII]/Halpha ratio (constant) for decontamination')
    ap.add_argument('--ebv', type=float, default=None, help='foreground E(B-V) for extinction correction')
    ap.add_argument('--k-ha', type=float, default=2.53, help='A_Ha/E(B-V) coefficient (CCM+O’Donnell, typical 2.5–3.3)')
    ap.add_argument('--Te', type=float, default=1.0e4, help='electron temperature for EM conversion')
    args = ap.parse_args()

    hdul = fits.open(args.inp)
    img = hdul[0].data.astype(float)
    hdr = hdul[0].header
    photflam = float(hdr.get('PHOTFLAM', np.nan))
    fwhm = float(hdr.get('FWHM', np.nan))
    cw = float(hdr.get('CW', np.nan))
    pixscale = float(hdr.get('PIXSCALE', np.sqrt(abs(hdr.get('CD1_1', 0.0) * hdr.get('CD2_2', 0.0))) * 3600.0)) or 0.305

    # CPS→flux→surface brightness（校正情報が無ければ相対単位で代用）
    cal_ok = np.isfinite(photflam) and np.isfinite(fwhm) and np.isfinite(cw)
    if cal_ok:
        F_line = cps_to_flux(img, photflam, fwhm, cw)
        I_ha = to_surface_brightness(F_line, pixscale)
    else:
        I_ha = np.array(img, dtype=float)
        # 非負にクリップして相対スケールに正規化
        I_ha = I_ha - np.nanmin(I_ha)
        p95 = np.nanpercentile(I_ha, 95) if np.isfinite(I_ha).any() else 1.0
        I_ha = I_ha / (p95 if p95 > 0 else 1.0)
    # [NII] decontamination (if ratio provided)
    meta = {'source': str(args.inp), 'PHOTFLAM': photflam, 'FWHM': fwhm, 'CW': cw, 'PIXSCALE': pixscale, 'calibrated': bool(cal_ok)}
    if args.nii_ratio is not None and args.nii_ratio >= 0.0:
        I_ha = I_ha / (1.0 + float(args.nii_ratio))
        meta['nii_ratio'] = float(args.nii_ratio)
    # Foreground extinction correction (if E(B-V) provided)
    if args.ebv is not None and float(args.ebv) > 0.0:
        Aha = float(args.k_ha) * float(args.ebv)
        I_ha = I_ha * (10.0 ** (0.4 * Aha))
        meta['E_BV'] = float(args.ebv)
        meta['k_Ha'] = float(args.k_ha)
    # EM map
    I_R = to_rayleigh(I_ha)
    EM = to_EM_pc_cm6(I_R, Te=args.Te)
    # Write outputs
    out_dir = args.outdir / args.name
    out_dir.mkdir(parents=True, exist_ok=True)
    # Halpha_SB.fits
    h_hdr = hdr.copy()
    h_hdr['BUNIT'] = 'erg s^-1 cm^-2 arcsec^-2' if cal_ok else 'arb'
    fits.writeto(out_dir / 'Halpha_SB.fits', I_ha.astype(np.float32), h_hdr, overwrite=True)
    # EM_pc_cm6.fits
    e_hdr = hdr.copy()
    e_hdr['BUNIT'] = 'pc cm^-6' if cal_ok else 'arb'
    fits.writeto(out_dir / 'EM_pc_cm6.fits', EM.astype(np.float32), e_hdr, overwrite=True)
    # metadata
    meta.update({'Te': float(args.Te), 'outputs': ['Halpha_SB.fits', 'EM_pc_cm6.fits']})
    (out_dir / 'Halpha_metadata.json').write_text(json.dumps(meta, indent=2), encoding='utf-8')
    print('wrote', out_dir)
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
