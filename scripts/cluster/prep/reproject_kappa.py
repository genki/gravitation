#!/usr/bin/env python3
"""Reproject observed kappa maps onto the Σ_e grid for cluster holdouts."""
from __future__ import annotations

import argparse
import shutil
from pathlib import Path

import numpy as np
from astropy.io import fits
from astropy.wcs import WCS
from scipy.ndimage import map_coordinates


DATA_ROOT = Path("data/cluster")


def reproject_cluster(cluster: str, overwrite: bool = False) -> None:
    root = DATA_ROOT / cluster
    if not root.exists():
        raise FileNotFoundError(f"cluster directory not found: {root}")

    sigma_path = root / "sigma_e.fits"
    if not sigma_path.exists():
        raise FileNotFoundError(f"expected sigma_e.fits for target grid: {sigma_path}")

    orig_path = root / "kappa_obs_orig.fits"
    src_path = root / "kappa_obs.fits"
    if orig_path.exists():
        kappa_source = orig_path
    elif src_path.exists():
        if overwrite:
            shutil.copy2(src_path, orig_path)
            kappa_source = orig_path
        else:
            orig_path = src_path.with_name("kappa_obs_orig.fits")
            shutil.copy2(src_path, orig_path)
            kappa_source = orig_path
    else:
        raise FileNotFoundError(f"kappa_obs.fits not found for cluster {cluster}")

    with fits.open(kappa_source) as hdul:
        kappa_data = hdul[0].data.astype(np.float64)
        kappa_header = hdul[0].header.copy()

    with fits.open(sigma_path) as hdul:
        target_header = hdul[0].header.copy()
        target_shape = hdul[0].data.shape

    kappa_wcs = WCS(kappa_header)
    target_wcs = WCS(target_header)

    ny, nx = target_shape
    y_idx, x_idx = np.indices((ny, nx), dtype=np.float64)
    ra, dec = target_wcs.all_pix2world(x_idx, y_idx, 0)
    kx, ky = kappa_wcs.all_world2pix(ra, dec, 0)

    reproj = map_coordinates(
        kappa_data,
        (ky, kx),
        order=1,
        mode="constant",
        cval=np.nan,
    )
    reproj = np.nan_to_num(reproj, nan=0.0)

    out_header = target_header.copy()
    if "PIXKPC" not in out_header and "PIXKPC" in kappa_header:
        out_header["PIXKPC"] = kappa_header["PIXKPC"]
    if "BUNIT" not in out_header and "BUNIT" in kappa_header:
        out_header["BUNIT"] = kappa_header["BUNIT"]

    fits.PrimaryHDU(reproj, header=out_header).writeto(src_path, overwrite=True)
    print(f"wrote {src_path}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Reproject kappa_obs.fits onto sigma_e grid")
    parser.add_argument(
        "--cluster",
        action="append",
        default=[],
        help="cluster name(s) under data/cluster",
    )
    parser.add_argument(
        "--all",
        action="store_true",
        help="reproject all clusters that have sigma_e.fits",
    )
    parser.add_argument(
        "--overwrite",
        action="store_true",
        help="overwrite existing kappa_obs_orig.fits with new backup",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    clusters = set(args.cluster)
    if args.all:
        clusters.update(p.name for p in DATA_ROOT.iterdir() if (p / "sigma_e.fits").exists())
    if not clusters:
        raise SystemExit("no clusters specified; use --cluster NAME or --all")
    for cluster in sorted(clusters):
        reproject_cluster(cluster, overwrite=args.overwrite)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
