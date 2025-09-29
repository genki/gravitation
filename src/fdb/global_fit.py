from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import List, Tuple

import numpy as np
from scipy.optimize import least_squares

from .sparc import load_sparc_rotmod, RotMod
from .models import gr_baryon_velocity, fdb3_velocity


@dataclass
class GlobalFitResult:
    a: float
    b: float
    c: float
    ml_disk: np.ndarray
    ml_bul: np.ndarray
    redchi2_gr: float
    redchi2_fdb3: float


def _fit_fdb3_single(rot: RotMod) -> Tuple[float, float, float]:
    def resid(p):
        a, b, c, ml_d, ml_b = p
        vhat = fdb3_velocity(rot.r_kpc, rot.vgas, rot.vdisk, rot.vbul,
                             a, b, c, ml_d, ml_b)
        return (vhat - rot.vobs) / np.maximum(rot.everr, 1.0)

    x0 = np.array([200.0, 3.0, 1.0, 0.5, 0.7])
    lb = np.array([0.0, 0.1, 0.2, 0.0, 0.0])
    ub = np.array([5e4, 50.0, 3.0, 1.5, 2.0])
    res = least_squares(resid, x0, bounds=(lb, ub), max_nfev=400)
    return tuple(res.x[:3])  # a, b, c


def _robust_center(vals: np.ndarray) -> Tuple[float, float]:
    med = np.median(vals)
    mad = np.median(np.abs(vals - med)) + 1e-6
    # 1.4826*MAD ≈ σ だが、弱事前なので少し広めに。
    sig = 2.0 * 1.4826 * mad + 1e-3
    return float(med), float(sig)


def global_fit(directory: Path) -> GlobalFitResult:
    files = sorted(Path(directory).glob("*_rotmod.dat"))
    rots: List[RotMod] = [load_sparc_rotmod(p) for p in files]
    g = len(rots)
    if g == 0:
        raise FileNotFoundError("rotmodが見つかりません")

    # 予備: 単銀河フィットで a,b,c の中心/分散を推定
    abs_: List[Tuple[float, float, float]] = []
    for r in rots:
        try:
            abs_.append(_fit_fdb3_single(r))
        except Exception:
            continue
    if not abs_:
        # フォールバック
        abs_ = [(200.0, 3.0, 1.0)]
    a0, sa = _robust_center(np.array([x[0] for x in abs_]))
    b0, sb = _robust_center(np.array([x[1] for x in abs_]))
    c0, sc = _robust_center(np.array([x[2] for x in abs_]))

    # 共同フィット: 共有(a,b,c) + 銀河ごと(ml_d, ml_b)
    def pack(a, b, c, ml_d, ml_b):
        return np.concatenate([[a, b, c], ml_d, ml_b])

    def unpack(x):
        a, b, c = x[:3]
        ml_d = x[3 : 3 + g]
        ml_b = x[3 + g : 3 + 2 * g]
        return a, b, c, ml_d, ml_b

    x0 = pack(a0, b0, c0, np.full(g, 0.5), np.full(g, 0.7))
    lb = pack(0.0, 0.1, 0.5, np.zeros(g), np.zeros(g))
    ub = pack(5e4, 50.0, 3.0, np.full(g, 1.5), np.full(g, 2.0))

    def resid_all(x):
        a, b, c, ml_d, ml_b = unpack(x)
        resids = []
        for i, r in enumerate(rots):
            vgr = gr_baryon_velocity(r.r_kpc, r.vgas, r.vdisk, r.vbul,
                                     ml_d[i], ml_b[i])
            vhat = fdb3_velocity(r.r_kpc, r.vgas, r.vdisk, r.vbul,
                                 a, b, c, ml_d[i], ml_b[i])
            e = np.maximum(r.everr, 1.0)
            resids.append((vhat - r.vobs) / e)
            # 追加: GR整合の緩い拘束（Vhat>=Vgrを弱く促す）
            resids.append(0.05 * np.maximum(vgr - vhat, 0.0) / e)
        rcat = np.concatenate(resids)
        # RJ風弱事前: a,b,c を( a0,b0,c0 )にL2拘束
        rj = np.array([(a - a0) / sa, (b - b0) / sb, (c - c0) / sc])
        # M/L緩い拘束
        mlp = np.concatenate([(ml_d - 0.5) / 0.5, (ml_b - 0.7) / 0.5])
        return np.concatenate([rcat, 0.1 * rj, 0.05 * mlp])

    res = least_squares(resid_all, x0, bounds=(lb, ub), max_nfev=2000)
    a, b, c, ml_d, ml_b = unpack(res.x)

    # メトリクス: 合成redχ²（自由度は概算）
    ysz = sum(r.r_kpc.size for r in rots)
    dof_gr = ysz - 2 * g
    dof_f3 = ysz - (3 + 2 * g)

    def rc(model):
        chi2 = 0.0
        for i, r in enumerate(rots):
            e = np.maximum(r.everr, 1.0)
            if model == "gr":
                v = gr_baryon_velocity(r.r_kpc, r.vgas, r.vdisk, r.vbul,
                                       ml_d[i], ml_b[i])
            else:
                v = fdb3_velocity(r.r_kpc, r.vgas, r.vdisk, r.vbul,
                                  a, b, c, ml_d[i], ml_b[i])
            chi2 += np.sum(((r.vobs - v) / e) ** 2.0)
        return chi2

    rc_gr = rc("gr") / max(dof_gr, 1)
    rc_f3 = rc("f3") / max(dof_f3, 1)

    return GlobalFitResult(
        a=a, b=b, c=c, ml_disk=ml_d, ml_bul=ml_b,
        redchi2_gr=rc_gr, redchi2_fdb3=rc_f3,
    )

