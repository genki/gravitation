#!/usr/bin/env python3
from __future__ import annotations
import subprocess as sp
import json
from pathlib import Path


def run_one(rho: float, w: float, gamma: float, q: float) -> Path | None:
    tag = f"r{rho:.2f}_w{w:.2f}_g{gamma:.2f}_q{q:.2f}".replace(".", "p")
    out = Path("data/results") / f"multi_fit_expanded20_grid_{tag}.json"
    args = [
        "PYTHONPATH=.", "./.venv/bin/python", "scripts/compare_fit_multi.py",
        "--names-file", "data/sparc/sets/expanded20.txt",
        "--boost", "0.5", "--boost-tie-lam",
        "--auto-geo",
        "--gas-scale-grid", "1.0,1.33",
        "--eg-frac-floor", "0.15",
        "--inv1-orth",
        "--mix-lam-ratio", f"{rho}",
        "--mix-w", f"{w}",
        "--aniso-q", f"{q}",
        "--out", str(out),
    ]
    if gamma > 0:
        args += ["--nl-gamma", f"{gamma}"]
    cmd = " ".join(args)
    print("run:", cmd)
    ret = sp.run(cmd, shell=True, check=False, capture_output=True, text=True)
    if ret.returncode != 0:
        print("warn: failed", tag, ret.stderr[-300:])
        return None
    try:
        # sanity
        data = json.loads(out.read_text(encoding="utf-8"))
        _ = data.get("AIC", {}).get("ULW")
        return out
    except Exception as e:
        print("warn: bad json", tag, e)
        return None


def main() -> int:
    rho_list = [0.10, 0.20, 0.33]
    w_list = [0.20, 0.40]
    gamma_list = [0.0, 0.10]
    q_list = [1.0, 0.90]
    outs: list[Path] = []
    for rho in rho_list:
        for w in w_list:
            for g in gamma_list:
                for q in q_list:
                    p = run_one(rho, w, g, q)
                    if p:
                        outs.append(p)
    # pick best by AIC ULW
    best = None
    for p in outs:
        try:
            d = json.loads(p.read_text(encoding="utf-8"))
            aic = d.get("AIC", {}).get("ULW")
            if aic is None:
                aic = d.get("chi2_total", {}).get("ULW")
            aic = float(aic)
        except Exception:
            continue
        if (best is None) or (aic < best[0]):
            best = (aic, p)
    if best:
        print("best:", best[0], best[1])
    else:
        print("no successful runs")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

