#!/usr/bin/env python3
from __future__ import annotations
import csv
import json
import math
import random
from pathlib import Path
from typing import List, Tuple, Dict


def read_alpha_csv(p: Path) -> List[float]:
    vals: List[float] = []
    with p.open(newline="", encoding="utf-8") as f:
        r = csv.DictReader(f)
        for row in r:
            try:
                v = float(row["alpha_line"])  # type: ignore[index]
                if math.isfinite(v):
                    vals.append(v)
            except Exception:
                continue
    return vals


def cliffs_delta(x: List[float], y: List[float]) -> float:
    """Cliff's delta: P(X>Y) - P(X<Y). Range [-1, 1]."""
    nx, ny = len(x), len(y)
    gt = lt = 0
    for a in x:
        for b in y:
            if a > b:
                gt += 1
            elif a < b:
                lt += 1
    if nx * ny == 0:
        return float("nan")
    return (gt - lt) / float(nx * ny)


def hodges_lehmann(x: List[float], y: List[float]) -> float:
    """Hodges–Lehmann estimator of location difference: median of pairwise (y - x)."""
    diffs: List[float] = []
    for a in x:
        diffs.extend(b - a for b in y)
    diffs.sort()
    n = len(diffs)
    if n == 0:
        return float("nan")
    mid = n // 2
    if n % 2 == 1:
        return diffs[mid]
    else:
        return 0.5 * (diffs[mid - 1] + diffs[mid])


def cohens_d(x: List[float], y: List[float]) -> float:
    nx, ny = len(x), len(y)
    if nx < 2 or ny < 2:
        return float("nan")
    mx = sum(x) / nx
    my = sum(y) / ny
    sx2 = sum((v - mx) ** 2 for v in x) / (nx - 1)
    sy2 = sum((v - my) ** 2 for v in y) / (ny - 1)
    sp = math.sqrt(((nx - 1) * sx2 + (ny - 1) * sy2) / (nx + ny - 2))
    if sp == 0:
        return float("nan")
    return (my - mx) / sp  # positive means y > x


def bootstrap_ci(xs: List[float], ys: List[float], B: int = 2000, seed: int = 0) -> Dict[str, float]:
    """Percentile bootstrap CI for median difference (y - x)."""
    rnd = random.Random(seed)
    n, m = len(xs), len(ys)
    if n == 0 or m == 0:
        return {"p2.5": float("nan"), "p50": float("nan"), "p97.5": float("nan")}
    meds: List[float] = []
    for _ in range(B):
        xb = [xs[rnd.randrange(n)] for _ in range(n)]
        yb = [ys[rnd.randrange(m)] for _ in range(m)]
        xb.sort(); yb.sort()
        # sample medians
        def median(arr: List[float]) -> float:
            k = len(arr)
            mid = k // 2
            if k % 2 == 1:
                return arr[mid]
            return 0.5 * (arr[mid - 1] + arr[mid])
        meds.append(median(yb) - median(xb))
    meds.sort()
    def pct(p: float) -> float:
        i = p * (len(meds) - 1)
        lo = int(math.floor(i)); hi = int(math.ceil(i))
        t = i - lo
        return (1 - t) * meds[lo] + t * meds[hi]
    return {"p2.5": pct(0.025), "p50": pct(0.5), "p97.5": pct(0.975)}


def main() -> int:
    lsb_csv = Path("assets/results/alpha_line_lsb.csv")
    hsb_csv = Path("assets/results/alpha_line_hsb.csv")
    out_json = Path("assets/results/alpha_line_effects.json")

    if not lsb_csv.exists() or not hsb_csv.exists():
        raise SystemExit("missing CSVs. Run scripts/analyze_groups.py first to generate them.")

    lsb = read_alpha_csv(lsb_csv)
    hsb = read_alpha_csv(hsb_csv)

    eff_delta = cliffs_delta(lsb, hsb)  # positive if HSB > LSB
    hl = hodges_lehmann(lsb, hsb)       # median(y - x)
    d = cohens_d(lsb, hsb)              # standardized difference
    ci = bootstrap_ci(lsb, hsb, B=2000, seed=20250901)

    out = {
        "n": {"lsb": len(lsb), "hsb": len(hsb)},
        "cliffs_delta": eff_delta,
        "hodges_lehmann": hl,
        "cohens_d": d,
        "median_diff_ci": ci,
        "interpretation": {
            "direction": "positive means HSB > LSB",
            "magnitude_hint": "|delta|≈0.11 small, 0.28 medium, 0.43 large (Romano et al.)"
        }
    }
    out_json.parent.mkdir(parents=True, exist_ok=True)
    out_json.write_text(json.dumps(out, indent=2), encoding="utf-8")

    # Optional quick violin plot
    try:
        import matplotlib
        matplotlib.use('Agg')
        import matplotlib.pyplot as plt
        from scripts.utils.mpl_fonts import use_jp_font
        use_jp_font()
        import numpy as np
        fig = plt.figure(figsize=(5.2, 3.2), dpi=160)
        data = [np.array(lsb, dtype=float), np.array(hsb, dtype=float)]
        plt.violinplot(data, showmeans=True, showmedians=True)
        plt.xticks([1, 2], ["LSB", "HSB"])
        plt.ylabel("alpha_line")
        plt.title("alpha_line by group (violin)")
        fig.tight_layout()
        fig_path = Path("assets/figures/alpha_line_violin.png")
        fig_path.parent.mkdir(parents=True, exist_ok=True)
        plt.savefig(fig_path)
        plt.close(fig)
    except Exception as e:
        print("warn: violin plot skipped:", e)

    print("wrote", out_json)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
