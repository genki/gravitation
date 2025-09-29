#!/usr/bin/env python3
from __future__ import annotations
import csv
import io
from pathlib import Path
import requests


def fetch_2mrs(outdir: Path) -> Path:
    outdir.mkdir(parents=True, exist_ok=True)
    url = "https://vizier.cds.unistra.fr/viz-bin/asu-tsv"
    params = {
        "-source": "J/ApJS/199/26/table3",
        "-out": "RAJ2000,DEJ2000,cz,GLON,GLAT,KCmag",
        "-out.max": "999999",
    }
    r = requests.get(url, params=params, timeout=120)
    r.raise_for_status()
    txt = r.text
    lines = [ln for ln in txt.splitlines() if ln and not ln.startswith("#")]
    path = outdir / "2mrs_table3.tsv"
    path.write_text("\n".join(lines), encoding="utf-8")
    return path


def main() -> int:
    out = fetch_2mrs(Path("data/lss"))
    print(f"saved: {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

