#!/usr/bin/env python3
"""
Convert McGaugh's MilkyWayModel.mrt into a SPARC-like CSV usable with fdb2_fit.py.

We parse only the numeric table (lines with actual numbers) and map columns as:
  Radius -> R_kpc
  Vtot   -> Vobs
  Vdisk  -> Vdisk_rotmod
  Vgas   -> Vgas_rotmod
  Vbulge -> Vbul_rotmod

Surface densities are filled with placeholder 1.0 values (v2 kernel only uses
them to estimate Rd, so this is sufficient for a first experiment).
"""

import sys
import os
import numpy as np
import pandas as pd

# Simple Milky Way disk/bulge scale parameters (for SPARC-like compatibility)
MW_DISK_SIGMA0 = 500.0  # Msun/pc^2 nominal central surface density
MW_DISK_RD_KPC = 2.6    # kpc, exponential scale length
MW_BULGE_EDGE_KPC = 2.5  # kpc, approximate bulge extent


def load_mw_vel_table(path: str) -> pd.DataFrame:
    """Parse MilkyWayModel.mrt (velocities only)."""
    rows = []
    with open(path, "r") as f:
        for line in f:
            s = line.strip()
            if not s or s.startswith("Title") or s.startswith("Byte") or s.startswith("Note"):
                continue
            # numeric lines start with a blank then a digit
            if not (s[0].isdigit() or s[0] in "+-" or s[0] == "."):
                continue
            parts = s.split()
            if len(parts) < 7:
                continue
            try:
                vals = list(map(float, parts[:7]))
            except ValueError:
                continue
            rows.append(vals)
    cols = ["Radius", "Vbulge", "Vgas", "Vdisk", "Vdmhalo", "Vtot", "Vtotcor"]
    return pd.DataFrame(rows, columns=cols)


def load_mw_sd_table(path: str) -> pd.DataFrame:
    """Parse MW2018modelWSD.dat (velocities + surface densities)."""
    df = pd.read_table(
        path,
        comment="#",
        delim_whitespace=True,
        names=["R", "Vbulge", "Vgas", "Vdisk", "Vdmhalo", "Vtot",
               "Vtotcor", "Dbulge", "Ddisk", "Dgas"],
    )
    return df


def main():
    if len(sys.argv) != 4:
        print("Usage: convert_mw_to_sparc.py data/sparc/MilkyWayModel.mrt data/sparc/MW2018modelWSD.dat build/MW_sparc.csv")
        sys.exit(1)
    mrt_path, sd_path, out = sys.argv[1], sys.argv[2], sys.argv[3]
    df_sd = load_mw_sd_table(sd_path)
    if df_sd.empty:
        print("Failed to parse MW2018modelWSD.dat")
        sys.exit(1)

    # For SPARC 一覧との整合性を優先し、MW2018modelWSD.dat 側の
    # バリオン分解をそのまま利用する。Vobs は Vtotcor を採用し、
    # Vdisk/Vgas/Vbulge は同じテーブルから取得する。
    df = df_sd.sort_values("R").reset_index(drop=True)

    R_kpc = df["R"].to_numpy()
    # Use corrected total rotation curve as "observed" Vobs, analogous to SPARC.
    Vobs = df["Vtotcor"].to_numpy()
    eVobs = np.full_like(Vobs, 5.0)
    Vdisk = df["Vdisk"].to_numpy()
    Vgas = df["Vgas"].to_numpy()
    Vbul = df["Vbulge"].to_numpy()

    # Surface densities:
    # - stellar disk: impose an exponential profile with fixed Rd for FDB Rd estimation
    Sigma_star = MW_DISK_SIGMA0 * np.exp(-R_kpc / MW_DISK_RD_KPC)
    # - gas: use Dgas from MW2018modelWSD.dat (already Msun/pc^2)
    Sigma_gas = df["Dgas"].to_numpy()

    out_df = pd.DataFrame(
        {
            "R_kpc": R_kpc,
            "Vobs": Vobs,
            "eVobs": eVobs,
            "Vdisk_rotmod": Vdisk,
            "Vgas_rotmod": Vgas,
            "Vbul_rotmod": Vbul,
            "Sigma_gas": Sigma_gas,
            "Sigma_star": Sigma_star,
        }
    )
    os.makedirs(os.path.dirname(out), exist_ok=True)
    out_df.to_csv(out, index=False)
    print(f"Wrote {out} ({len(out_df)} rows)")


if __name__ == "__main__":
    main()
