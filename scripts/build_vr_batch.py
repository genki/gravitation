#!/usr/bin/env python3
from __future__ import annotations
import subprocess as sp
from pathlib import Path


def run_for_set(names_file: Path, out_suffix: str,
                extra_args: list[str]) -> None:
    names = [
        ln.strip() for ln in names_file.read_text(encoding="utf-8").splitlines()
        if ln.strip() and not ln.strip().startswith('#')
    ]
    for nm in names:
        out = Path("paper/figures") / f"compare_fit_{nm}_{out_suffix}.svg"
        args = [
            "PYTHONPATH=.", "./.venv/bin/python", "scripts/compare_fit_sparc.py",
            nm, "--out", str(out),
        ] + extra_args
        cmd = " ".join(args)
        print("run:", cmd)
        sp.run(cmd, shell=True, check=False)


def main() -> int:
    # Updated V-R figures with current best options
    nearby = Path("data/sparc/sets/nearby.txt")
    barset = Path("data/sparc/sets/barset.txt")
    # Use irradiance and tie-lam DoG; leave aniso/nl off for batch speed
    common = [
        "--irr-alpha", "0.8",
        "--irr-p", "1.0",
        "--boost", "0.5", "--boost-tie-lam",
        "--auto-geo",
        "--pad-factor", "2",
        "--outer-frac", "0.6", "--outer-weight", "1.0",
        "--eg-frac-floor", "0.15",
        "--mix-lam-ratio", "4.0",
        "--mix-w", "0.4",
        "--lam-grid", "2,3,5,8,12,15,20",
        "--A-grid", "0.01,0.0316,0.1,0.316,1,3.16,10,31.6,100,316",
    ]
    if nearby.exists():
        run_for_set(nearby, "upd", common)
    if barset.exists():
        run_for_set(barset, "upd", common + ["--bar-alpha", "0.6",
                                              "--bar-width", "0.8",
                                              "--bar-r0", "0.8"]) 
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
