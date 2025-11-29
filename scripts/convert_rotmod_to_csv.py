#!/usr/bin/env python3
"""
Convert a SPARC rotmod.dat file to a simple CSV expected by fdb_fit.py.

Assumptions:
- Input columns (after header): Rad[kpc], Vobs, errV, Vgas, Vdisk, Vbul, SBdisk, SBbul
- Surface brightness SB* are in L/pc^2.
- We use fixed mass-to-light ratios: M/L_disk=0.5, M/L_bulge=0.7 (default).
- Sigma_gas is set to 0 (gas not reconstructed here).

Usage: ./convert_rotmod_to_csv.py data/sparc/sparc_database/NGC2403_rotmod.dat output.csv
"""
import sys
import pandas as pd

M_L_DISK = 0.5
M_L_BULGE = 0.7


def load_rotmod(path: str) -> pd.DataFrame:
    cols = ["Rad", "Vobs", "errV", "Vgas", "Vdisk", "Vbul", "SBdisk", "SBbul"]
    df = pd.read_csv(path, comment="#", delim_whitespace=True, names=cols)
    return df


def convert(df: pd.DataFrame) -> pd.DataFrame:
    sigma_star = df["SBdisk"] * M_L_DISK + df["SBbul"] * M_L_BULGE  # Msun/pc^2
    sigma_gas = 0.0  # placeholder; gas not reconstructed here
    out = pd.DataFrame(
        {
            "R_kpc": df["Rad"],
            "Vobs": df["Vobs"],
            "eVobs": df["errV"],
            "Sigma_star": sigma_star,
            "Sigma_gas": sigma_gas,
        }
    )
    return out


def main():
    if len(sys.argv) != 3:
        print("Usage: convert_rotmod_to_csv.py <rotmod.dat> <output.csv>")
        sys.exit(1)
    inp, outp = sys.argv[1], sys.argv[2]
    df = load_rotmod(inp)
    out = convert(df)
    out.to_csv(outp, index=False)
    print(f"Wrote {outp} ({len(out)} rows)")


if __name__ == "__main__":
    main()
