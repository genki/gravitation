"""
Model adapter layer and simple model classes for fair comparisons.

Classes expose a shared interface:
  - params: dict-like of model hyperparameters
  - predict_accel(R, components) -> ndarray acceleration[g]

Where `components` is a dict with at least:
  - 'g_gas', 'g_star', optionally 'g_disk', 'g_bul', 'SBdisk', and metadata.

This adapter wraps existing implementations so scripts can migrate gradually.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Any
import numpy as np

M_PER_KM = 1.0e3
KPC_IN_M = 3.08567758149137e19
_A0_DEFAULT_KPC = 1.2e-10 * (KPC_IN_M / (M_PER_KM ** 2))


@dataclass
class ModelBase:
    name: str
    params: Dict[str, float]

    def predict_accel(self, R: np.ndarray, components: Dict[str, np.ndarray]) -> np.ndarray:
        raise NotImplementedError


@dataclass
class GRBaryonModel(ModelBase):
    """GR (no DM) baseline: gas_scale * g_gas + mu * g_star."""

    def predict_accel(self, R: np.ndarray, components: Dict[str, np.ndarray]) -> np.ndarray:
        gg = float(self.params.get("gas_scale", 1.0)) * components["g_gas"]
        mu_d = self.params.get("mu_d")
        mu_b = self.params.get("mu_b")
        if (mu_d is not None) or (mu_b is not None):
            g_disk = components.get("g_disk")
            g_bul = components.get("g_bul")
            mu_d = float(mu_d if mu_d is not None else 0.0)
            mu_b = float(mu_b if mu_b is not None else 0.0)
            return gg + mu_d * g_disk + mu_b * g_bul
        mu = float(self.params.get("mu", 1.0))
        return gg + mu * components["g_star"]


@dataclass
class FDB3Model(ModelBase):
    """FDB3 ULW-EM model wrapper: baseline + ULW term.

    Required params: lam, A, gas_scale, mu or (mu_d, mu_b)
    components must contain: 'SBdisk', 'g_gas', ('g_star' or both 'g_disk','g_bul')
    """

    def predict_accel(self, R: np.ndarray, components: Dict[str, np.ndarray]) -> np.ndarray:
        from scripts.compare_fit_multi import model_ulw_accel
        lam = float(self.params["lam"])
        A = float(self.params["A"])
        pix = float(self.params.get("pix_kpc", 0.2))
        size = int(self.params.get("size", 256))
        boost = float(self.params.get("boost", 0.0))
        s1 = float(self.params.get("s1_kpc", lam / 8.0))
        s2 = float(self.params.get("s2_kpc", lam / 3.0))
        pad = int(self.params.get("pad_factor", 2))
        g_ulw = A * model_ulw_accel(R, components["SBdisk"], lam, A=1.0, pix_kpc=pix,
                                    size=size, boost=boost, s1_kpc=s1, s2_kpc=s2,
                                    pad_factor=pad)
        base = GRBaryonModel("GR(noDM)", {
            k: self.params[k] for k in ("mu", "mu_d", "mu_b", "gas_scale") if k in self.params
        }).predict_accel(R, components)
        return base + g_ulw - (float(self.params.get("mu", 0.0)) * components.get("g_star", 0.0) if "mu" in self.params else 0.0)


@dataclass
class MONDModel(ModelBase):
    """Simple MOND a(mu): a = (aN/2) + sqrt((aN/2)^2 + aN a0).
    Not a full TeVeS; provided for baseline comparison only.
    """

    def predict_accel(self, R: np.ndarray, components: Dict[str, np.ndarray]) -> np.ndarray:
        raw_a0 = self.params.get("a0")
        if raw_a0 is None:
            a0 = _A0_DEFAULT_KPC
        else:
            a0_val = float(raw_a0)
            if a0_val < 1e-6:  # assume SI (m/s^2) and convert
                a0 = a0_val * (KPC_IN_M / (M_PER_KM ** 2))
            else:
                a0 = a0_val
        # Here we assume components['g_baryon'] is provided if available; otherwise use gas+mu*star
        if "g_baryon" in components:
            gN = components["g_baryon"]
        else:
            gg = float(self.params.get("gas_scale", 1.0)) * components["g_gas"]
            mu = float(self.params.get("mu", 1.0))
            gN = gg + mu * components["g_star"]
        # simple interpolation formula
        half = 0.5 * gN
        return half + np.sqrt(half * half + gN * a0)


def build_models(kind: str, params: Dict[str, float]) -> ModelBase:
    k = kind.lower()
    if k in ("gr", "gr_nodm", "baryon"):
        return GRBaryonModel("GR(noDM)", params)
    if k in ("fdb", "fdb3", "ulw", "ulw-em"):
        return FDB3Model("FDB3", params)
    if k in ("mond",):
        return MONDModel("MOND", params)
    raise ValueError(f"unknown model kind: {kind}")
