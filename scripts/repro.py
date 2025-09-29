#!/usr/bin/env python3
"""One-click reproducibility runner for key SOTA assets.

This script executes the minimum set of pipelines (benches, bullet holdout,
BAO validation, SOTA build) and verifies a handful of load-bearing metrics.
It is intended to be wired into CI via `make repro`.
"""
from __future__ import annotations

import json
import math
import os
import re
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Dict, Iterable, List, Tuple

REPO_ROOT = Path(__file__).resolve().parents[1]
ENV = os.environ.copy()
ENV.setdefault("PYTHONPATH", str(REPO_ROOT))
PY = sys.executable


@dataclass(frozen=True)
class Check:
    description: str
    fn: Callable[[], None]


def run_step(description: str, command: List[str]) -> None:
    print(f"[repro] {description} -> {' '.join(command)}")
    subprocess.run(command, check=True, env=ENV, cwd=REPO_ROOT)


def assert_close(actual: float, expected: float, *, rel: float = 1e-6, abs_tol: float = 1e-6, label: str = "value") -> None:
    if not math.isfinite(actual):
        raise AssertionError(f"{label}: non-finite value {actual}")
    if not math.isfinite(expected):
        raise AssertionError(f"{label}: expected non-finite value {expected}")
    diff = abs(actual - expected)
    tol = max(abs_tol, abs(expected) * rel)
    if diff > tol:
        raise AssertionError(f"{label}: |{actual} - {expected}| = {diff} > tolerance {tol}")


def parse_aicc(html_path: Path) -> Dict[str, float]:
    """Extract AICc values from bench HTML (supports legacy paragraph or new table)."""

    text = html_path.read_text(encoding="utf-8")

    # New table format (preferred)
    table_pattern = re.compile(
        r"<tr><th[^>]*>(?P<label>[^<]+)</th>\s*"
        r"<td>[^<]*</td>\s*"  # N
        r"<td>[^<]*</td>\s*"  # N_eff
        r"<td>[^<]*</td>\s*"  # k
        r"<td>(?P<aicc>[^<]+)</td>",
        re.IGNORECASE | re.DOTALL,
    )
    label_map = {
        "GR": "GR",
        "MOND": "MOND",
        "GR+DM(NFW)": "GR+DM",
        "FDB(Σ)": "FDB",
        "FDB(Σ) ": "FDB",
        "FDB": "FDB",
    }
    values: Dict[str, float] = {}
    for match in table_pattern.finditer(text):
        lbl = match.group("label").strip()
        key = label_map.get(lbl)
        if not key:
            continue
        try:
            values[key] = float(match.group("aicc"))
        except ValueError:
            continue
    if {"GR", "GR+DM", "FDB"}.issubset(values.keys()):
        return values

    # Legacy paragraph fallback
    m = re.search(r"AICc: GR=([0-9.]+).*?GR\+DM=([0-9.]+).*?FDB=([0-9.]+)", text, re.DOTALL)
    if m:
        return {
            "GR": float(m.group(1)),
            "GR+DM": float(m.group(2)),
            "FDB": float(m.group(3)),
        }

    raise AssertionError(f"AICc block not found in {html_path}")


def check_bench(path: str, expected: Dict[str, float]) -> None:
    values = parse_aicc(REPO_ROOT / path)
    for key, target in expected.items():
        assert_close(values[key], target, rel=5e-4, abs_tol=1e-2, label=f"{path}:{key}")


def check_bullet_holdout() -> None:
    data = json.loads((REPO_ROOT / "server/public/reports/bullet_holdout.json").read_text(encoding="utf-8"))
    delta = data["delta"]
    assert_close(delta["FDB_minus_shift"], -6.789960654854536e6, rel=5e-4, abs_tol=5e3, label="ΔAICc(FDB-shift)")
    assert_close(delta["FDB_minus_rot"], -6.567600440792531e7, rel=5e-4, abs_tol=5e4, label="ΔAICc(FDB-rot)")
    shadow_block = data.get("shadow_metrics")
    if shadow_block is None:
        shadow_block = data.get("indicators", {}).get("shadow_metrics")
    if shadow_block is None:
        raise AssertionError("shadow metrics not found in bullet_holdout.json")
    s_shadow = shadow_block["S_shadow"]
    if isinstance(s_shadow, dict) and "values" in s_shadow:
        shadow = s_shadow["values"]["global"]
    else:
        shadow = s_shadow["global"]
    assert_close(shadow, 0.4428037804334557, rel=5e-4, abs_tol=1e-3, label="S_shadow(global)")
    if "candidates" in shadow_block and shadow_block["candidates"]:
        p_perm = shadow_block["candidates"][0]["p_perm"]
    else:
        p_perm = shadow_block["S_shadow"]["perm"]["p_perm_one_sided_pos"]
    assert_close(p_perm, 9.999000099990002e-5, rel=5e-3, abs_tol=5e-6, label="S_shadow p_perm")


def check_bao_and_solar() -> None:
    payload = json.loads((REPO_ROOT / "server/public/state_of_the_art/data/fig_eu1c.json").read_text(encoding="utf-8"))
    bao = payload["bao_likelihood"]
    assert_close(bao["chi2_total"], 3.8736175912083666, rel=5e-4, abs_tol=1e-4, label="BAO χ²")
    solar = payload["solar_penalty"]
    status = solar.get("status")
    if status != "pass":
        raise AssertionError(f"Solar penalty status is {status!r}, expected 'pass'")


BENCH_CHECKS: List[Tuple[str, Dict[str, float]]] = [
    ("server/public/reports/bench_ngc3198.html", {"GR": 7051.119, "GR+DM": 7055.531, "FDB": 192.227}),
    ("server/public/reports/bench_ngc2403.html", {"GR": 81666.272, "GR+DM": 81669.864, "FDB": 497.673}),
]


def main() -> int:
    steps = [
        ("NGC 3198 bench", [PY, "scripts/benchmarks/run_ngc3198_fullbench.py"]),
        ("NGC 2403 bench", [PY, "scripts/benchmarks/run_ngc2403_fullbench.py"]),
        ("Bullet holdout", [PY, "scripts/reports/make_bullet_holdout.py"]),
        ("BAO validation", [PY, "scripts/eu/class_validate.py"]),
        ("SOTA build", [PY, "scripts/build_state_of_the_art.py"]),
    ]
    for desc, cmd in steps:
        run_step(desc, cmd)

    print("[repro] verifying benchmarks …")
    for path, expected in BENCH_CHECKS:
        check_bench(path, expected)

    print("[repro] verifying Bullet holdout …")
    check_bullet_holdout()

    print("[repro] verifying BAO & Solar …")
    check_bao_and_solar()

    print("[repro] all checks passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
