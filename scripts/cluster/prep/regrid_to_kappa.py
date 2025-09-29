#!/usr/bin/env python3
from __future__ import annotations
import numpy as np
from pathlib import Path


def main() -> int:
    kappa_p = Path('data/cluster/bullet/kappa.npy')
    sigma_p = Path('data/cluster/maps/bullet_sigma_e.npy')
    if not (kappa_p.exists() and sigma_p.exists()):
        print('missing kappa.npy or bullet_sigma_e.npy')
        return 1
    kappa = np.load(kappa_p)
    sigma = np.load(sigma_p)
    if sigma.shape == kappa.shape:
        out = Path('data/cluster/maps/bullet_sigma_e_kappa.npy')
        np.save(out, sigma)
        print('already matched; wrote', out)
        return 0
    import scipy.ndimage as ndi
    zy, zx = kappa.shape[0]/sigma.shape[0], kappa.shape[1]/sigma.shape[1]
    sigma_rg = ndi.zoom(sigma, zoom=(zy, zx), order=1)
    out = Path('data/cluster/maps/bullet_sigma_e_kappa.npy')
    np.save(out, sigma_rg)
    print('wrote', out, sigma_rg.shape)
    return 0


if __name__ == '__main__':
    raise SystemExit(main())

