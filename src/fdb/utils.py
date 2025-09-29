from __future__ import annotations

import numpy as np


def sanitize_radial_series(r: np.ndarray, v: np.ndarray,
                           rmin: float = 1e-6) -> tuple[np.ndarray,
                                                        np.ndarray]:
    """V-R系列の健全化。

    - r<=rmin かつ v≈0 の人工原点アンカーを除去
    - rの単調増加を保証（同一rは平均化）
    """
    r = np.asarray(r, float)
    v = np.asarray(v, float)
    m = ~((r <= rmin) & (np.abs(v) < 1e-6))
    r, v = r[m], v[m]
    idx = np.argsort(r)
    r, v = r[idx], v[idx]
    # 重複半径を平均
    if r.size == 0:
        return r, v
    out_r = [r[0]]
    out_v = [v[0]]
    for i in range(1, r.size):
        if np.isclose(r[i], out_r[-1], rtol=0, atol=1e-9):
            out_v[-1] = 0.5 * (out_v[-1] + v[i])
        else:
            out_r.append(r[i])
            out_v.append(v[i])
    return np.asarray(out_r), np.asarray(out_v)

