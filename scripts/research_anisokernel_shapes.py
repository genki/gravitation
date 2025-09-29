#!/usr/bin/env python3
from __future__ import annotations
"""
Anisotropic FDB kernel (1/r + quadrupole P2) numerical demos for sphere/rod/disk.
Generates vector acceleration fields and radial profiles to validate scaling.
Outputs PNGs under server/public/reports/ and server/public/assets/research/.
"""
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from scripts.utils.mpl_fonts import use_jp_font
from pathlib import Path

def P2(u):
    return 0.5*(3.0*u*u - 1.0)

def g_of_r(r, ell0, m=2):
    if ell0 <= 0:
        return np.zeros_like(r)
    return np.exp(- (np.abs(r)/ell0)**2)

def build_shapes(n=129, L=20.0):
    y = np.linspace(-L, L, n)
    x = np.linspace(-L, L, n)
    xx, yy = np.meshgrid(x, y, indexing='xy')
    rr = np.sqrt(xx**2 + yy**2)
    # Sphere-like (2D Gaussian blob)
    sph = np.exp(- (rr/3.0)**2)
    sph /= np.sum(sph)
    # Finite rod along x at y=0
    rod = np.exp(- (yy/0.5)**2) * (np.abs(xx) <= 6.0)
    rod /= np.sum(rod)
    # Thin exponential disk (axisymmetric in plane)
    disk = np.exp(- rr/5.0)
    disk /= np.sum(disk)
    return (x, y, sph, rod, disk)

def accel_field(rho: np.ndarray, x: np.ndarray, y: np.ndarray,
                nvec=(0.0, 0.0, 1.0), alpha=0.3, ell0=5.0, m=2) -> tuple[np.ndarray, np.ndarray]:
    # Real-space convolution with vector kernel a ~ r/|r|^3 times anisotropic factor
    ny, nx = rho.shape
    xx, yy = np.meshgrid(x, y, indexing='xy')
    ax = np.zeros_like(xx)
    ay = np.zeros_like(yy)
    # Precompute source coords
    src = np.argwhere(rho > 0)
    if src.size == 0:
        return ax, ay
    # Normalize mass per pixel
    M = rho / np.sum(rho)
    # Assume disk plane (z=0); director n along z for disk/rod by default
    for (jy, ix) in src:
        mx = x[ix]; my = y[jy]
        rx = xx - mx; ry = yy - my
        r2 = rx*rx + ry*ry + 1e-6
        r = np.sqrt(r2)
        # thin-disk approx in plane: cos=0 -> P2=-1/2
        anis = 1.0 + alpha * g_of_r(r, ell0, m) * (-0.5)
        fac = M[jy, ix] * anis / (r2 * r)
        ax += fac * rx
        ay += fac * ry
    return ax, ay

def radial_profile(ax, ay, x, y):
    xx, yy = np.meshgrid(x, y, indexing='xy')
    rr = np.sqrt(xx**2 + yy**2)
    ar = (ax*xx + ay*yy) / (rr + 1e-9)
    rb = np.linspace(0.5, rr.max(), 40)
    prof = []
    for i in range(len(rb)-1):
        m = (rr >= rb[i]) & (rr < rb[i+1])
        if np.any(m):
            prof.append((0.5*(rb[i]+rb[i+1]), np.nanmedian(np.abs(ar[m]))))
    if not prof:
        return np.array([]), np.array([])
    rmid, amid = zip(*prof)
    return np.array(rmid), np.array(amid)

def plot_field(axf, ayf, x, y, title, out_png):
    plt.figure(figsize=(5,4))
    plt.streamplot(x, y, axf, ayf, density=1.2, color=np.hypot(axf, ayf), cmap='viridis')
    plt.colorbar(label='|a| (arb.)')
    plt.title(title)
    plt.xlabel('x [kpc]'); plt.ylabel('y [kpc]')
    Path(out_png).parent.mkdir(parents=True, exist_ok=True)
    plt.tight_layout(); plt.savefig(out_png, dpi=120); plt.close()

def plot_profile(r, a, title, out_png):
    plt.figure(figsize=(5,3.2))
    eps=1e-9
    if r.size:
        plt.loglog(r+eps, a+eps, 'o-', ms=3, label='|a_r|')
        rref = np.array([max(r.min(),1e-3), r.max()])
        plt.loglog(rref, (a.max()*(rref[0]/rref)), '--', lw=1, label='~1/r')
        plt.loglog(rref, (a.max()*(rref[0]/rref)**2), '--', lw=1, label='~1/r^2')
    plt.legend(); plt.title(title)
    plt.xlabel('r [kpc]'); plt.ylabel('|a_r| (arb.)')
    Path(out_png).parent.mkdir(parents=True, exist_ok=True)
    plt.tight_layout(); plt.savefig(out_png, dpi=120); plt.close()

def main():
    use_jp_font()
    out_dir = Path('server/public/assets/research')
    rep_dir = Path('server/public/reports')
    x, y, sph, rod, disk = build_shapes(n=129, L=20.0)
    sets = [('Sphere-like', sph, (0,0,1)), ('Rod-x', rod, (0,0,1)), ('Disk', disk, (0,0,1))]
    for name, rho, nvec in sets:
        ax, ay = accel_field(rho, x, y, nvec=nvec, alpha=0.3, ell0=5.0, m=2)
        plot_field(ax, ay, x, y, f'FDB anisotropic accel — {name}', out_dir/f'fdb_field_{name}.png')
        r, a = radial_profile(ax, ay, x, y)
        plot_profile(r, a, f'a_r profile — {name}', out_dir/f'fdb_prof_{name}.png')
    # simple index
    lines = ["<h1>FDB anisotropic kernel demos</h1>"]
    for name,_rho,_ in sets:
        lines.append(f"<h2>{name}</h2>")
        lines.append(f"<figure class='card'><img src='../assets/research/fdb_field_{name}.png' style='max-width:100%;height:auto'></figure>")
        lines.append(f"<figure class='card'><img src='../assets/research/fdb_prof_{name}.png' style='max-width:100%;height:auto'></figure>")
    rep_dir.mkdir(parents=True, exist_ok=True)
    (rep_dir/'fdb_aniso_demos.html').write_text("\n".join(lines), encoding='utf-8')
    print('wrote reports:', rep_dir/'fdb_aniso_demos.html')

if __name__ == '__main__':
    main()
