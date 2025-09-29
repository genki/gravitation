#!/usr/bin/env python3
from __future__ import annotations
import argparse, os, subprocess, tempfile
from pathlib import Path
from astropy.io import fits
from astropy.cosmology import Planck18 as COSMO
import astropy.units as u
import math

def pixel_scale_kpc_per_pix(hdr: fits.Header, z_lens: float) -> float:
    if 'CD1_1' in hdr and 'CD2_2' in hdr:
        cd11=float(hdr['CD1_1']); cd12=float(hdr.get('CD1_2',0.0))
        cd21=float(hdr.get('CD2_1',0.0)); cd22=float(hdr['CD2_2'])
        s1=math.hypot(cd11,cd12); s2=math.hypot(cd21,cd22)
        pix_deg=(s1+s2)/2.0
    elif 'CDELT1' in hdr and 'CDELT2' in hdr:
        pix_deg=(abs(float(hdr['CDELT1']))+abs(float(hdr['CDELT2'])))/2.0
    else:
        raise RuntimeError('WCS scale not found (CD* or CDELT* required)')
    kpc_per_arcsec = (COSMO.kpc_proper_per_arcmin(z_lens).to(u.kpc/u.arcsec)).value
    return kpc_per_arcsec * (pix_deg*3600.0)

def add_pixkpc(path: Path, z_lens: float):
    with fits.open(path, mode='update') as hdul:
        hdr=hdul[0].header
        pixkpc=pixel_scale_kpc_per_pix(hdr, z_lens)
        hdr['PIXKPC']=(float(pixkpc),'kpc per pixel')
        hdr['BUNIT']=('dimensionless','kappa (convergence)')
        hdr['ZLENS']=(float(z_lens),'lens redshift')
        hdul.flush()
    print(f'Added PIXKPC={pixkpc:.6f} to {path}')

def main():
    ap=argparse.ArgumentParser(description='Run Lenstool to export kappa FITS and add PIXKPC header')
    ap.add_argument('--par', required=True, help='Path to Lenstool model.par')
    ap.add_argument('--out', required=True, help='Output FITS filename (kappa_obs.fits)')
    ap.add_argument('--zlens', type=float, required=True, help='Lens redshift')
    ap.add_argument('--zs', type=float, default=1.0, help='Source redshift for normalization (often 2.0 or 1.0)')
    ap.add_argument('--grid', type=int, default=512, help='Grid size (N=Nx=Ny)')
    ap.add_argument('--fov-arcsec', type=float, default=256.0, help='Half-size of FoV in arcsec (total=2*value)')
    ap.add_argument('--env-prefix', default='.mamba/envs/lenstool_env', help='Prefix of lenstool env (micromamba)')
    args=ap.parse_args()

    par=Path(args.par).resolve()
    out=Path(args.out).resolve()
    out.parent.mkdir(parents=True, exist_ok=True)

    # Build runmode script
    xmin=-args.fov_arcsec; ymin=-args.fov_arcsec; xmax=args.fov_arcsec; ymax=args.fov_arcsec
    run=f"""
runmode
  grid {args.grid} {args.grid}  {xmin:.6f} {ymin:.6f}  {xmax:.6f} {ymax:.6f}
  mass 1 {args.grid} {args.zlens:.6f} {args.zs:.6f} {out}
end
""".strip()+"\n"

    with tempfile.NamedTemporaryFile('w', delete=False) as tf:
        tf.write(run)
        tf.flush()
        runfile=tf.name

    # Run lenstool in env
    cmd=[os.path.join(args.env_prefix,'bin','lenstool'), str(par)]
    print('Running:', ' '.join(cmd), '<', runfile)
    with open(runfile,'r') as fin:
        res=subprocess.run(cmd, stdin=fin, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
    print(res.stdout)
    if res.returncode!=0:
        raise SystemExit('lenstool failed')

    if not out.exists():
        raise SystemExit(f'Output FITS not found: {out}')
    add_pixkpc(out, args.zlens)

if __name__=='__main__':
    main()

