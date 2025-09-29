from __future__ import annotations
import numpy as np


def mu0_of_k(k: np.ndarray, eps: float, k0: float, m: float) -> np.ndarray:
    return 1.0 + eps / (1.0 + (np.maximum(k, 1e-12) / max(k0, 1e-12)) ** m)


def kgrid(shape: tuple[int,int,int], spacing: tuple[float,float,float]) -> tuple[np.ndarray,np.ndarray,np.ndarray,np.ndarray]:
    nz, ny, nx = shape
    dz, dy, dx = spacing[2], spacing[1], spacing[0]
    kx = 2*np.pi * np.fft.fftfreq(nx, d=dx)
    ky = 2*np.pi * np.fft.fftfreq(ny, d=dy)
    kz = 2*np.pi * np.fft.fftfreq(nz, d=dz)
    KZ, KY, KX = np.meshgrid(kz, ky, kx, indexing='ij')
    K = np.sqrt(KX*KX + KY*KY + KZ*KZ)
    return KX, KY, KZ, K

