#!/usr/bin/env python3
"""
Convert a SPARC rotmod.dat file to a simple CSV expected by fdb_fit.py.

Assumptions:
- Input columns (after header): Rad[kpc], Vobs, errV, Vgas, Vdisk, Vbul, SBdisk, SBbul
- Surface brightness SB* are in L/pc^2.
- Fixed mass-to-light ratios: M/L_disk=0.5, M/L_bulge=0.7 (change below if needed).
- Gas surface density is reconstructed approximately from the gas-only rotation curve Vgas:
    M_enc(R) = Vgas^2 R / G  (G in kpc (km/s)^2 / Msun),
  then annulus mass differences give Sigma_gas. Negative annulus masses are set to zero.

Usage: ./convert_rotmod_to_csv.py data/sparc/sparc_database/NGC2403_rotmod.dat output.csv
"""
import sys
import pandas as pd
import numpy as np

M_L_DISK = 0.5
M_L_BULGE = 0.7
G_KPC = 4.30091e-6  # kpc (km/s)^2 / Msun


def load_rotmod(path: str) -> pd.DataFrame:
    cols = ["Rad", "Vobs", "errV", "Vgas", "Vdisk", "Vbul", "SBdisk", "SBbul"]
    df = pd.read_csv(path, comment="#", delim_whitespace=True, names=cols)
    return df


def convert(df: pd.DataFrame) -> pd.DataFrame:
    sigma_star = df["SBdisk"] * M_L_DISK + df["SBbul"] * M_L_BULGE  # Msun/pc^2

    # Reconstruct gas surface density from gas-only rotation curve Vgas.
    R = df["Rad"].to_numpy()  # kpc
    Vgas = df["Vgas"].to_numpy()  # km/s
    # Enclosed mass from circular velocity: M(<R) = V^2 R / G
    M_enc = (Vgas**2) * R / G_KPC  # Msun
    # Annulus masses
    R_edges = np.concatenate([[R[0]*0.5], 0.5*(R[1:]+R[:-1]), [R[-1]*1.5]])
    area = np.pi * (R_edges[1:]**2 - R_edges[:-1]**2)  # kpc^2
    M_ann = np.diff(np.concatenate([[0.0], M_enc]))  # crude diff; length = len(R)
    M_ann = np.clip(M_ann, 0, None)
    sigma_gas_kpc2 = M_ann / area  # Msun/kpc^2
    sigma_gas = sigma_gas_kpc2 / 1e6  # Msun/pc^2

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
