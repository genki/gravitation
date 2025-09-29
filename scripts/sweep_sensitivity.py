#!/usr/bin/env python3
from __future__ import annotations
import subprocess as sp
import json
from pathlib import Path
from typing import Dict, Any, List


BASE_ARGS = [
    "PYTHONPATH=.", "./.venv/bin/python", "scripts/compare_fit_multi.py",
    "--names-file", "data/sparc/sets/nearby.txt",
    "--boost", "0.5", "--boost-tie-lam",
    "--gas-scale-grid", "1.33",
    "--mu-min", "0.2", "--mu-max", "0.8",
    "--outer-frac", "0.6", "--outer-weight", "1.0",
]


def run_one(irr: float, nl_gamma: float) -> Dict[str, Any]:
    tag = f"nearby_sens_irr{irr:.2f}_nl{nl_gamma:.2f}"
    out = Path("data/results") / f"multi_fit_{tag}.json"
    args = BASE_ARGS + [
        "--irr-alpha", f"{irr}",
        "--nl-gamma", f"{nl_gamma}", "--nl-q", "1.0", "--nl-iter", "2",
        "--out", str(out),
    ]
    print("run:", " ".join(args))
    env = dict(PATH=str(Path(".venv/bin").resolve()))
    # Use shell to preserve PYTHONPATH=.
    cmd = " ".join(args)
    ret = sp.run(cmd, shell=True, check=False, capture_output=True, text=True)
    if ret.returncode != 0:
        print("warn: failure", ret.stderr)
        return {"tag": tag, "error": ret.stderr, "rc": ret.returncode}
    try:
        data = json.loads(out.read_text(encoding="utf-8"))
        data["tag"] = tag
        data["params"] = {"irr_alpha": irr, "nl_gamma": nl_gamma}
        return data
    except Exception as e:
        return {"tag": tag, "error": str(e), "rc": 1}


def main() -> int:
    irr_list = [0.0, 0.3, 0.5, 0.8]
    nl_list = [0.0, 0.3, 0.6]
    outdir = Path("data/results/sensitivity")
    outdir.mkdir(parents=True, exist_ok=True)
    results: List[Dict[str, Any]] = []
    for irr in irr_list:
        for nl in nl_list:
            res = run_one(irr, nl)
            results.append(res)
    agg = {"grid": results}
    (outdir / "nearby_sensitivity.json").write_text(
        json.dumps(agg, indent=2), encoding="utf-8")
    print("saved:", outdir / "nearby_sensitivity.json")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

