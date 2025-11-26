import re
from pathlib import Path
import numpy as np
import pandas as pd


def load_sparc_catalog(catalog_path: str) -> pd.DataFrame:
    """Load SPARC catalog. Falls back to manual parser if needed."""
    try:
        df = pd.read_csv(
            catalog_path,
            sep=r"\s+",
            comment="#",
            engine="python",
            on_bad_lines="skip",
        )
        rename = {}
        for col in df.columns:
            key = col.strip().lower()
            if key in {"name", "galaxy", "galname"}:
                rename[col] = "name"
            elif key in {"mbar", "m_b", "mbary", "mbar_tot"}:
                rename[col] = "Mbar"
            elif key in {"qual", "quality", "q"}:
                rename[col] = "Qual"
        df = df.rename(columns=rename)
        if "name" in df.columns and "Mbar" in df.columns:
            return df
    except Exception:
        pass
    # fallback: manual parse (assumes column2 is log10(Mbar))
    records = {}
    with open(catalog_path) as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith('#'):
                continue
            parts = line.split()
            if len(parts) < 2:
                continue
            name = parts[0]
            try:
                logM = float(parts[1])
            except ValueError:
                continue
            key = name.lower()
            if key not in records:
                records[key] = 10 ** logM
    if not records:
        raise ValueError("Unable to parse catalog: no name/Mbar pairs found")
    return pd.DataFrame({"name": list(records.keys()), "Mbar": list(records.values())})


def parse_rotmod_file(path: Path) -> pd.DataFrame:
    """Parse *_rotmod.dat and return dataframe with required columns."""
    rows = []
    with path.open() as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith(("#", "R", "r")):
                continue
            parts = re.split(r"\s+", line)
            if len(parts) < 3:
                continue
            vals = []
            for p in parts[:7]:
                try:
                    vals.append(float(p))
                except ValueError:
                    vals.append(np.nan)
            while len(vals) < 7:
                vals.append(np.nan)
            r, v, e, vgas, vdisk, vbulge, _ = vals
            rows.append((r, v, e, vgas, vdisk, vbulge))
    df = pd.DataFrame(
        rows,
        columns=["r_kpc", "v_obs", "e_obs", "v_gas", "v_disk", "v_bulge"],
    )
    if df.empty:
        return df
    for col in ["v_gas", "v_disk", "v_bulge"]:
        df[col] = df[col].fillna(0.0)
    df["e_obs"] = df["e_obs"].fillna(np.nan)
    return df


def glob_rotmods(rotmod_dir: str):
    return sorted(Path(rotmod_dir).glob("*_rotmod.dat"))


def robust_outer_velocity(series: pd.Series, n_tail: int = 3) -> float:
    tail = series.tail(n_tail)
    return float(np.median(tail.values))
