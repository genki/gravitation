from __future__ import annotations
import numpy as np


def lm_count(lmax: int) -> int:
    return sum(2*l+1 for l in range(lmax+1))


def lm_index(l: int, m: int) -> int:
    """Flatten (l,m) to index in [0, (lmax+1)^2-1] using standard ordering.
    Assumes caller ensures bounds; symmetric with index_lm.
    """
    return l*l + (m + l)


def index_lm(idx: int) -> tuple[int,int]:
    l = int(np.floor(np.sqrt(idx)))
    m = idx - l*l - l
    return l, m


def real_sph_harm(l: int, m: int, theta: np.ndarray, phi: np.ndarray) -> np.ndarray:
    """Real spherical harmonics Y_lm (Condon-Shortley) with real basis.

    For m>0: Y_lm^R = sqrt(2) * (-1)^m * Re(Y_lm)
    For m<0: Y_lm^R = sqrt(2) * (-1)^m * Im(Y_l|m|)
    For m=0: Y_l0^R = Y_l0 (real)

    Requires scipy.special.sph_harm; raises ImportError if missing.
    theta: polar angle [0,π], phi: azimuth [0,2π).
    """
    try:
        from scipy.special import sph_harm as _sph
    except Exception as e:
        raise ImportError("scipy is required for real_sph_harm") from e

    if m == 0:
        return _sph(0, l, phi, theta).real  # m, l, phi, theta order in scipy
    if m > 0:
        Y = _sph(m, l, phi, theta)
        return np.sqrt(2.0) * ((-1)**m) * Y.real
    # m < 0
    Y = _sph(-m, l, phi, theta)
    return np.sqrt(2.0) * ((-1)**m) * Y.imag

