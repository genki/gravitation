from __future__ import annotations
from dataclasses import dataclass
import numpy as np


@dataclass
class VoxelGrid:
    """Regular voxel grid holding mass density ρ.

    Attributes
    - origin: (x0,y0,z0) in meters
    - spacing: (dx,dy,dz) in meters
    - rho: ndarray (nz, ny, nx) mass density in kg/m^3
    """

    origin: tuple[float, float, float]
    spacing: tuple[float, float, float]
    rho: np.ndarray

    @property
    def shape(self) -> tuple[int, int, int]:
        return tuple(self.rho.shape)

    def coords(self) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
        nz, ny, nx = self.rho.shape
        z0, y0, x0 = self.origin[2], self.origin[1], self.origin[0]
        dz, dy, dx = self.spacing[2], self.spacing[1], self.spacing[0]
        x = x0 + dx * (np.arange(nx) + 0.5)
        y = y0 + dy * (np.arange(ny) + 0.5)
        z = z0 + dz * (np.arange(nz) + 0.5)
        return np.meshgrid(x, y, z, indexing='xy')  # (ny,nx), but we'll transpose as needed

    def cell_centers(self) -> np.ndarray:
        nx, ny, nz = self.rho.shape[2], self.rho.shape[1], self.rho.shape[0]
        x0, y0, z0 = self.origin
        dx, dy, dz = self.spacing
        xs = x0 + dx * (np.arange(nx) + 0.5)
        ys = y0 + dy * (np.arange(ny) + 0.5)
        zs = z0 + dz * (np.arange(nz) + 0.5)
        X, Y, Z = np.meshgrid(xs, ys, zs, indexing='xy')
        return np.stack([X, Y, Z], axis=-1)  # (ny, nx, nz, 3)


def make_uniform_sphere(R: float, rho0: float, spacing: float) -> VoxelGrid:
    """Create a uniform-density sphere with radius R (m) and density rho0 (kg/m^3).
    Grid is cubic with isotropic spacing.
    """
    # choose a box that encloses sphere with margin ~1 cell
    n_cells = int(np.ceil((2*R) / spacing)) + 2
    n = max(8, n_cells | 1)  # ensure odd for symmetry
    half = n * spacing / 2
    origin = (-half, -half, -half)
    rho = np.zeros((n, n, n), dtype=float)
    # voxel centers
    xs = np.linspace(-half + spacing/2, half - spacing/2, n)
    X, Y, Z = np.meshgrid(xs, xs, xs, indexing='ij')
    r = np.sqrt(X**2 + Y**2 + Z**2)
    rho[r <= R] = rho0
    return VoxelGrid(origin=origin, spacing=(spacing, spacing, spacing), rho=rho)


def make_finite_rod(L: float, radius: float, rho0: float, spacing: float) -> VoxelGrid:
    """Uniform cylinder of length L along z-axis and radius (m)."""
    nxy = int(np.ceil((2*radius)/spacing)) + 4
    nz = int(np.ceil(L/spacing)) + 4
    n = max(8, nxy)
    m = max(8, nz)
    half_xy = n * spacing / 2
    half_z = m * spacing / 2
    origin = (-half_xy, -half_xy, -half_z)
    rho = np.zeros((m, n, n), dtype=float)
    xs = np.linspace(-half_xy + spacing/2, half_xy - spacing/2, n)
    zs = np.linspace(-half_z + spacing/2, half_z - spacing/2, m)
    X, Y, Z = np.meshgrid(xs, xs, zs, indexing='ij')
    Rxy = np.sqrt(X**2 + Y**2)
    mask = (Rxy <= radius) & (np.abs(Z) <= L/2)
    rho = rho.transpose(0,2,1)  # ensure (nz,ny,nx) layout
    rho[mask.transpose(2,0,1)] = rho0
    return VoxelGrid(origin=origin, spacing=(spacing, spacing, spacing), rho=rho)


def make_thin_disk(R: float, h: float, rho0: float, spacing: float) -> VoxelGrid:
    """Axisymmetric thin disk (uniform slab of half-thickness h/2) in z with radius R."""
    n = int(np.ceil((2*R)/spacing)) + 4
    nz = max(8, int(np.ceil(h/spacing)) + 4)
    n = max(8, n)
    half_xy = n * spacing / 2
    half_z = nz * spacing / 2
    origin = (-half_xy, -half_xy, -half_z)
    rho = np.zeros((nz, n, n), dtype=float)
    xs = np.linspace(-half_xy + spacing/2, half_xy - spacing/2, n)
    zs = np.linspace(-half_z + spacing/2, half_z - spacing/2, nz)
    X, Y, Z = np.meshgrid(xs, xs, zs, indexing='ij')
    Rxy = np.sqrt(X**2 + Y**2)
    mask = (Rxy <= R) & (np.abs(Z) <= h/2)
    rho[mask.transpose(2,0,1)] = rho0
    return VoxelGrid(origin=origin, spacing=(spacing, spacing, spacing), rho=rho)

