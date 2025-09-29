#!/usr/bin/env python3
from __future__ import annotations
import numpy as np
from pathlib import Path
import matplotlib.pyplot as plt


def to_gray(img: np.ndarray) -> np.ndarray:
    if img.ndim == 2:
        return img.astype(float)
    if img.ndim == 3 and img.shape[2] >= 3:
        # simple luminance
        r, g, b = img[..., 0], img[..., 1], img[..., 2]
        return (0.2126 * r + 0.7152 * g + 0.0722 * b).astype(float)
    return img.squeeze().astype(float)


def main() -> int:
    tif = Path('data/cluster/bullet/xray.tif')
    if not tif.exists():
        print('missing:', tif)
        return 1
    img = plt.imread(tif)
    gray = to_gray(img)
    # normalize 0..1
    if np.nanmax(gray) > 0:
        gray = (gray - np.nanmin(gray)) / (np.nanmax(gray) - np.nanmin(gray))
    # resize to 256x256 via ndimage.zoom (linear)
    ny, nx = gray.shape
    import scipy.ndimage as ndi
    zy, zx = 256 / ny, 256 / nx
    out = ndi.zoom(gray, zoom=(zy, zx), order=1)
    np.save('data/cluster/bullet/xray.npy', out)
    print('wrote data/cluster/bullet/xray.npy', out.shape, out.dtype)
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
