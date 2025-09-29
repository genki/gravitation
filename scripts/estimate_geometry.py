#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, Tuple, Optional

import numpy as np
from PIL import Image


def choose_image(dirpath: Path) -> Optional[Path]:
    # Preference order: PS1 r, Legacy Surveys, SDSS, unWISE W1
    prefs = ["ps1_r.jpg", "ls-dr9.jpg", "sdss_dr17.jpg", "unwise_W1.jpg"]
    for name in prefs:
        p = dirpath / name
        if p.exists():
            return p
    # try any jpg
    for p in sorted(dirpath.glob("*.jpg")):
        return p
    return None


def estimate_pa_q(img: np.ndarray) -> Tuple[float, float]:
    """Estimate position angle (deg) and axis ratio q from image moments.

    Returns (pa_deg, q), where pa is the angle of the major axis measured
    from +x toward +y in image coordinates.
    """
    # convert to float and normalize
    I = img.astype(np.float32)
    if I.ndim == 3:
        # simple luminance
        I = 0.2126 * I[..., 0] + 0.7152 * I[..., 1] + 0.0722 * I[..., 2]
    I = np.nan_to_num(I)
    # enhance contrast: subtract median background, clip
    med = float(np.median(I))
    J = np.clip(I - med, 0.0, None)
    # weight by a soft power to reduce starburst outliers
    W = np.power(J, 0.8)
    if np.all(W <= 0):
        return 0.0, 1.0
    ny, nx = W.shape
    y = np.arange(ny, dtype=np.float32)
    x = np.arange(nx, dtype=np.float32)
    yy, xx = np.meshgrid(y, x, indexing="ij")
    wsum = float(np.sum(W) + 1e-12)
    x0 = float(np.sum(W * xx) / wsum)
    y0 = float(np.sum(W * yy) / wsum)
    dx = xx - x0
    dy = yy - y0
    mxx = float(np.sum(W * dx * dx) / wsum)
    myy = float(np.sum(W * dy * dy) / wsum)
    mxy = float(np.sum(W * dx * dy) / wsum)
    cov = np.array([[mxx, mxy], [mxy, myy]], dtype=np.float64)
    # eigen decomposition
    vals, vecs = np.linalg.eigh(cov)
    # sort descending by eigenvalue (major axis first)
    order = np.argsort(vals)[::-1]
    vals = vals[order]
    vecs = vecs[:, order]
    a2, b2 = float(vals[0]), float(vals[1])
    a = np.sqrt(max(a2, 1e-12))
    b = np.sqrt(max(b2, 1e-12))
    q = float(np.clip(b / a, 1e-3, 1.0))
    vx, vy = float(vecs[0, 0]), float(vecs[1, 0])
    pa = np.degrees(np.arctan2(vy, vx))  # image coords: +x right, +y down
    return pa, q


def process_all(imaging_root: Path) -> Dict[str, Dict[str, float]]:
    out: Dict[str, Dict[str, float]] = {}
    for d in sorted(imaging_root.iterdir()):
        if not d.is_dir():
            continue
        # directory name is galaxy label; manifest may hold canonical name
        name = d.name
        man = d / "manifest.json"
        if man.exists():
            try:
                meta = json.loads(man.read_text(encoding="utf-8"))
                if isinstance(meta, list) and meta:
                    name = meta[0].get("name", name)
            except Exception:
                pass
        imgp = choose_image(d)
        if not imgp:
            continue
        try:
            img = Image.open(imgp).convert("RGB")
            arr = np.asarray(img)
            pa, q = estimate_pa_q(arr)
            out[name] = {"pa_deg": float(pa), "q": float(q), "src": str(imgp)}
            print(f"{name}: pa={pa:.1f} deg, q={q:.3f} ({imgp.name})")
        except Exception as e:
            print("warn:", name, e)
    return out


def main() -> int:
    root = Path("data/imaging")
    if not root.exists():
        print("error: imaging root not found:", root)
        return 1
    res = process_all(root)
    outp = root / "geometry.json"
    outp.write_text(json.dumps(res, indent=2), encoding="utf-8")
    print("saved:", outp)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

