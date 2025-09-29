#!/usr/bin/env python3
from __future__ import annotations
import csv
import json
from pathlib import Path
from typing import List, Tuple, Dict


def read_alpha_csv(p: Path) -> List[float]:
    vals: List[float] = []
    with p.open(newline="", encoding="utf-8") as f:
        r = csv.DictReader(f)
        for row in r:
            try:
                vals.append(float(row["alpha_line"]))
            except Exception:
                continue
    return vals


def two_sample_ks(x: List[float], y: List[float]) -> Tuple[float, float]:
    """Return D statistic and an approximate p-value (Massey, 1951).

    This implementation avoids SciPy; good enough for n~O(1e2).
    """
    import math

    x_sorted = sorted(x)
    y_sorted = sorted(y)
    nx = len(x_sorted)
    ny = len(y_sorted)
    i = j = 0
    cdf_x = cdf_y = 0.0
    D = 0.0
    values = sorted(set(x_sorted + y_sorted))
    for v in values:
        while i < nx and x_sorted[i] <= v:
            i += 1
        while j < ny and y_sorted[j] <= v:
            j += 1
        cdf_x = i / nx
        cdf_y = j / ny
        D = max(D, abs(cdf_x - cdf_y))
    en = math.sqrt(nx * ny / (nx + ny))
    # Asymptotic p-value approximation
    lam = (en + 0.12 + 0.11 / en) * D
    # Kolmogorov distribution Q_KS approximation
    # p ≈ 2 Σ (-1)^{k-1} exp(-2 k^2 lam^2)
    p = 0.0
    for k in range(1, 101):
        p += (2 * (-1) ** (k - 1)) * math.exp(-2 * (k * k) * (lam * lam))
    p = max(min(p, 1.0), 0.0)
    return D, p


def mann_whitney_u(x: List[float], y: List[float]) -> Tuple[float, float]:
    """Mann-Whitney U test with normal approximation for p-value.
    Returns (U, p_two_sided). Ties get average ranks.
    """
    import math

    n1, n2 = len(x), len(y)
    # Rank all values together
    all_vals = [(v, 0) for v in x] + [(v, 1) for v in y]
    all_vals.sort(key=lambda t: t[0])
    ranks = [0.0] * (n1 + n2)
    i = 0
    while i < len(all_vals):
        j = i + 1
        while j < len(all_vals) and all_vals[j][0] == all_vals[i][0]:
            j += 1
        r = (i + j + 1) / 2.0  # average rank (1-indexed)
        for k in range(i, j):
            ranks[k] = r
        i = j
    # Sum ranks for group 1
    R1 = sum(ranks[i] for i in range(len(all_vals)) if all_vals[i][1] == 0)
    U1 = R1 - n1 * (n1 + 1) / 2.0
    U2 = n1 * n2 - U1
    U = min(U1, U2)
    # Normal approximation with tie correction
    # Compute tie correction T = 1 - Σ (t^3 - t) / ((N^3 - N))
    from collections import Counter

    counts = Counter(v for v, _ in all_vals)
    N = n1 + n2
    tie_term = sum(c * c * c - c for c in counts.values())
    T = 1.0 - tie_term / (N * N * N - N)
    mu = n1 * n2 / 2.0
    sigma = math.sqrt(n1 * n2 * (N + 1) / 12.0 * T)
    if sigma == 0:
        z = 0.0
    else:
        # continuity correction
        z = (U + 0.5 - mu) / sigma
    # two-sided p-value
    # Φ(-|z|) * 2
    def phi(z: float) -> float:
        return 0.5 * (1.0 + math.erf(z / (2.0 ** 0.5)))

    p_two = 2.0 * (1.0 - phi(abs(z)))
    return U, max(min(p_two, 1.0), 0.0)


def main() -> int:
    lsb_csv = Path("assets/results/alpha_line_lsb.csv")
    hsb_csv = Path("assets/results/alpha_line_hsb.csv")
    out_json = Path("assets/results/alpha_line_tests.json")

    lsb = read_alpha_csv(lsb_csv)
    hsb = read_alpha_csv(hsb_csv)
    D, p_ks = two_sample_ks(lsb, hsb)
    U, p_mwu = mann_whitney_u(lsb, hsb)

    summary: Dict[str, object] = {
        "n": {"lsb": len(lsb), "hsb": len(hsb)},
        "ks": {"D": D, "p": p_ks},
        "mann_whitney": {"U": U, "p_two_sided": p_mwu},
        "location_shift": (
            sum(hsb) / max(len(hsb), 1) - sum(lsb) / max(len(lsb), 1)
        ),
    }
    out_json.parent.mkdir(parents=True, exist_ok=True)
    out_json.write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print("wrote", out_json)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

