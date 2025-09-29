#!/usr/bin/env python3
"""Fast reproducibility checks (no heavy reruns).

This script inspects the already-generated benchmark reports, Bullet holdout
summary, and BAO/Solar payload to ensure key KPIs remain within tolerance.
It is meant for `make repro-local`, which reruns the faster pipelines and
then calls this verifier.
"""
from __future__ import annotations

import json
import math
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]


def _assert_close(actual: float, expected: float, *, rel: float = 5e-4, abs_tol: float = 1e-4, label: str = "value") -> None:
    if not math.isfinite(actual):
        raise AssertionError(f"{label}: non-finite value {actual}")
    diff = abs(actual - expected)
    tol = max(abs_tol, abs(expected) * rel)
    if diff > tol:
        raise AssertionError(f"{label}: |{actual} - {expected}| = {diff} > tolerance {tol}")


def _parse_aicc(path: Path) -> dict[str, float]:
    text = path.read_text(encoding="utf-8")
    # prefer table form
    import re

    pattern = re.compile(
        r"<tr><th[^>]*>(?P<label>[^<]+)</th>\s*<td>[^<]*</td>\s*<td>[^<]*</td>\s*<td>[^<]*</td>\s*<td>(?P<aicc>[^<]+)</td>",
        re.IGNORECASE,
    )
    label_map = {
        "GR": "GR",
        "MOND": "MOND",
        "GR+DM": "GR+DM",
        "GR+DM(NFW)": "GR+DM",
        "FDB(Σ)": "FDB",
        "FDB": "FDB",
    }
    values: dict[str, float] = {}
    for match in pattern.finditer(text):
        key = label_map.get(match.group("label").strip())
        if not key:
            continue
        try:
            values[key] = float(match.group("aicc"))
        except ValueError:
            continue
    if values:
        return values
    m = re.search(r"AICc: GR=([0-9.]+).*?GR\+DM=([0-9.]+).*?FDB=([0-9.]+)", text, re.DOTALL)
    if m:
        return {"GR": float(m.group(1)), "GR+DM": float(m.group(2)), "FDB": float(m.group(3))}
    raise AssertionError(f"AICc block not found in {path}")


def check_benchmarks() -> None:
    targets = {
        Path("server/public/reports/bench_ngc3198.html"): {"GR": 7051.119, "GR+DM": 7055.531, "FDB": 192.227},
        Path("server/public/reports/bench_ngc2403.html"): {"GR": 81666.272, "GR+DM": 81669.864, "FDB": 497.673},
    }
    for rel_path, expected in targets.items():
        values = _parse_aicc(REPO_ROOT / rel_path)
        for key, exp in expected.items():
            _assert_close(values[key], exp, rel=5e-4, abs_tol=1e-2, label=f"{rel_path}:{key}")


def check_bullet_holdout() -> None:
    data = json.loads((REPO_ROOT / "server/public/reports/bullet_holdout.json").read_text(encoding="utf-8"))
    delta = data.get("delta", {})
    _assert_close(delta["FDB_minus_rot"], -6.78594268737874e7, rel=5e-4, abs_tol=5e4, label="ΔAICc(FDB-rot)")
    _assert_close(delta["FDB_minus_shift"], -6.743814854082286e6, rel=5e-4, abs_tol=5e3, label="ΔAICc(FDB-shift)")
    indicators = data.get("indicators", {})
    s_block = indicators.get("S_shadow", {})
    s_val = float((s_block.get("values") or {}).get("global"))
    p_val = float((s_block.get("perm") or {}).get("p_perm_one_sided_pos"))
    _assert_close(s_val, 0.377958, rel=5e-3, abs_tol=5e-4, label="S_shadow(global)")
    _assert_close(p_val, 0.00225, rel=5e-2, abs_tol=5e-4, label="S_shadow p_perm")


def check_bao_and_solar() -> None:
    payload = json.loads((REPO_ROOT / "server/public/state_of_the_art/data/fig_eu1c.json").read_text(encoding="utf-8"))
    bao = payload["bao_likelihood"]
    _assert_close(bao["chi2_total"], 3.8736175912083666, rel=5e-4, abs_tol=1e-4, label="BAO χ²")
    solar = payload["solar_penalty"]
    status = solar.get("status")
    if status != "pass":
        raise AssertionError(f"Solar penalty status is {status!r}, expected 'pass'")


def main() -> int:
    check_benchmarks()
    check_bullet_holdout()
    check_bao_and_solar()
    print("[repro-local] verification passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
