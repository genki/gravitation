import argparse
import json
from pathlib import Path

import numpy as np

from helpers_sparc import glob_rotmods, load_sparc_catalog, parse_rotmod_file, robust_outer_velocity


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--rotmod_dir", required=True)
    ap.add_argument("--catalog", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--n_tail", type=int, default=3)
    ap.add_argument("--iqr_clip", type=float, default=2.5)
    args = ap.parse_args()

    cat = load_sparc_catalog(args.catalog)
    name2M = {str(row["name"]).lower(): float(row["Mbar"]) for _, row in cat.iterrows()}

    ratios = []
    total = 0
    for rot_path in glob_rotmods(args.rotmod_dir):
        name = rot_path.name.replace("_rotmod.dat", "").lower()
        if name not in name2M:
            continue
        Mbar = name2M[name]
        if Mbar <= 0:
            continue
        df = parse_rotmod_file(rot_path)
        if df.empty or len(df) < args.n_tail:
            continue
        vout = robust_outer_velocity(df["v_obs"], n_tail=args.n_tail)
        if vout > 0:
            ratios.append((vout ** 4) / Mbar)
            total += 1

    ratios = np.array(ratios)
    if ratios.size == 0:
        raise RuntimeError("No usable ratios from SPARC data")

    q1, q3 = np.percentile(ratios, [25, 75])
    iqr = q3 - q1
    lo, hi = q1 - args.iqr_clip * iqr, q3 + args.iqr_clip * iqr
    ratios_f = ratios[(ratios >= lo) & (ratios <= hi)]
    if ratios_f.size == 0:
        ratios_f = ratios

    A_hat = float(np.median(ratios_f))
    mad = 1.4826 * np.median(np.abs(ratios_f - A_hat))
    med_unc = float(mad / np.sqrt(ratios_f.size))

    out = {
        "A_BTFR_median": A_hat,
        "A_BTFR_median_unc": med_unc,
        "N_used": int(ratios_f.size),
        "N_total": int(total),
    }

    Path(args.out).parent.mkdir(parents=True, exist_ok=True)
    with open(args.out, "w") as f:
        json.dump(out, f, indent=2)
    print(json.dumps(out, indent=2))


if __name__ == "__main__":
    main()
