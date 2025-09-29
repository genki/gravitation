from __future__ import annotations
import numpy as np
from dataclasses import dataclass
from typing import Tuple


@dataclass
class SurfaceMesh:
    centers: np.ndarray  # (M,3)
    normals: np.ndarray  # (M,3), unit
    areas: np.ndarray    # (M,)


def _try_marching_cubes(field: np.ndarray, level: float, spacing: Tuple[float,float,float]) -> SurfaceMesh | None:
    try:
        from skimage.measure import marching_cubes
    except Exception:
        return None
    # verts: (V, 3) in index coordinates; faces: (F, 3) vertex indices
    verts, faces, _, _ = marching_cubes(field.astype(np.float32), level=level, spacing=spacing)
    tri = verts[faces]  # (F,3,3)
    v1 = tri[:,1,:] - tri[:,0,:]
    v2 = tri[:,2,:] - tri[:,0,:]
    n = np.cross(v1, v2)
    area = 0.5 * np.linalg.norm(n, axis=1)
    n_unit = n / (np.linalg.norm(n, axis=1, keepdims=True) + 1e-30)
    centers = tri.mean(axis=1)
    return SurfaceMesh(centers=centers, normals=n_unit, areas=area)


def _voxel_face_surface(field: np.ndarray, level: float, spacing: Tuple[float,float,float]) -> SurfaceMesh:
    # Simple fallback: consider faces between voxels where the scalar crosses the level; add face centers and areas
    nz, ny, nx = field.shape
    dx, dy, dz = spacing[0], spacing[1], spacing[2]
    centers = []
    normals = []
    areas = []
    # x-faces between i and i+1
    fx = (field[:,:,1:] - level) * (field[:,:,:-1] - level) < 0
    iy, iz, ix = np.where(fx)
    for z, y, x in zip(iz, iy, ix):
        cx = (x+1) * dx
        cy = (y+0.5) * dy
        cz = (z+0.5) * dz
        # normal along +x or -x based on gradient sign
        sgn = np.sign((field[z,y,x+1] - field[z,y,x])) or 1.0
        n = np.array([sgn, 0.0, 0.0], dtype=float)
        a = dy*dz
        centers.append([cx, cy, cz]); normals.append(n); areas.append(a)
    # y-faces
    fy = (field[:,1:,:] - level) * (field[:,:-1,:] - level) < 0
    iz, iy, ix = np.where(fy)
    for z, y, x in zip(iz, iy, ix):
        cx = (x+0.5) * dx
        cy = (y+1) * dy
        cz = (z+0.5) * dz
        sgn = np.sign((field[z,y+1,x] - field[z,y,x])) or 1.0
        n = np.array([0.0, sgn, 0.0], dtype=float)
        a = dx*dz
        centers.append([cx, cy, cz]); normals.append(n); areas.append(a)
    # z-faces
    fz = (field[1:,:,:] - level) * (field[:-1,:,:] - level) < 0
    iz, iy, ix = np.where(fz)
    for z, y, x in zip(iz, iy, ix):
        cx = (x+0.5) * dx
        cy = (y+0.5) * dy
        cz = (z+1) * dz
        sgn = np.sign((field[z+1,y,x] - field[z,y,x])) or 1.0
        n = np.array([0.0, 0.0, sgn], dtype=float)
        a = dx*dy
        centers.append([cx, cy, cz]); normals.append(n); areas.append(a)
    if not centers:
        return SurfaceMesh(centers=np.zeros((0,3)), normals=np.zeros((0,3)), areas=np.zeros((0,)))
    centers = np.asarray(centers, dtype=float)
    normals = np.asarray(normals, dtype=float)
    nrm = np.linalg.norm(normals, axis=1, keepdims=True)
    normals = normals / (nrm + 1e-30)
    areas = np.asarray(areas, dtype=float)
    return SurfaceMesh(centers=centers, normals=normals, areas=areas)


def extract_isosurface(field: np.ndarray, level: float, spacing: Tuple[float,float,float]) -> SurfaceMesh:
    mc = _try_marching_cubes(field, level, spacing)
    if mc is not None:
        return mc
    return _voxel_face_surface(field, level, spacing)


def _trilinear_sample(grid: np.ndarray, x: np.ndarray, origin: Tuple[float,float,float], spacing: Tuple[float,float,float]) -> float:
    # x in same units as origin+spacing grid coordinates
    gx = (x[0] - origin[0]) / spacing[0] - 0.5
    gy = (x[1] - origin[1]) / spacing[1] - 0.5
    gz = (x[2] - origin[2]) / spacing[2] - 0.5
    ix = int(np.floor(gx)); iy = int(np.floor(gy)); iz = int(np.floor(gz))
    tx = gx - ix; ty = gy - iy; tz = gz - iz
    nx = grid.shape[2]; ny = grid.shape[1]; nz = grid.shape[0]
    def clamp(i, n):
        return max(0, min(n-1, i))
    ix0 = clamp(ix, nx); ix1 = clamp(ix+1, nx)
    iy0 = clamp(iy, ny); iy1 = clamp(iy+1, ny)
    iz0 = clamp(iz, nz); iz1 = clamp(iz+1, nz)
    c000 = grid[iz0,iy0,ix0]; c100 = grid[iz0,iy0,ix1]
    c010 = grid[iz0,iy1,ix0]; c110 = grid[iz0,iy1,ix1]
    c001 = grid[iz1,iy0,ix0]; c101 = grid[iz1,iy0,ix1]
    c011 = grid[iz1,iy1,ix0]; c111 = grid[iz1,iy1,ix1]
    c00 = c000*(1-tx) + c100*tx
    c01 = c001*(1-tx) + c101*tx
    c10 = c010*(1-tx) + c110*tx
    c11 = c011*(1-tx) + c111*tx
    c0 = c00*(1-ty) + c10*ty
    c1 = c01*(1-ty) + c11*ty
    return float(c0*(1-tz) + c1*tz)


def line_integral_us(
    centers: np.ndarray,
    normals: np.ndarray,
    rho: np.ndarray,
    origin: Tuple[float,float,float],
    spacing: Tuple[float,float,float],
    Ld: float,
    step: float | None = None,
    max_len: float | None = None,
) -> np.ndarray:
    # u_s(s) = ∫_0^∞ q(s - ℓ n) e^{-ℓ/Ld} dℓ, with q ∝ rho
    if step is None:
        step = min(spacing)*0.75
    if max_len is None:
        max_len = 10.0 * max(spacing) * max(rho.shape)
    us = np.zeros((centers.shape[0],), dtype=float)
    for i in range(centers.shape[0]):
        c = centers[i]; n = normals[i]
        acc = 0.0; ell = 0.0
        while ell <= max_len:
            p = c - ell * n
            q = _trilinear_sample(rho, p, origin, spacing)
            acc += q * np.exp(-ell / max(Ld, 1e-9)) * step
            ell += step
        us[i] = acc
    return us


def lambda_at_points(
    centers: np.ndarray,
    normals: np.ndarray,
    areas: np.ndarray,
    J_out: np.ndarray,
    points: np.ndarray,
) -> np.ndarray:
    # Λ(x) = (G/c) ∮ (J_out/π) * cosθ / r^2 dS = (G/cπ) Σ J_out * (n·r)/|r|^3 * dS
    from .constants import G, c
    K = (G / c) / np.pi
    vals = np.zeros((points.shape[0],), dtype=float)
    for j, x in enumerate(points):
        r = x[None,:] - centers  # (M,3)
        r2 = np.sum(r*r, axis=1)
        rnorm = np.sqrt(r2) + 1e-30
        cos_num = np.sum(normals * r, axis=1)
        contrib = J_out * (cos_num / (rnorm**3)) * areas
        vals[j] = K * np.sum(contrib)
    return vals

