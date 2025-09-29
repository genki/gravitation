#!/usr/bin/env python3
"""Bullet holdout SOTA summary generator.

Criteria (aligned with 2025-09-17 directives):
 1. ΔAICc(FDB−shift) ≤ −10
 2. Global S_shadow > 0 and permutation p(one-sided, positive) < 0.05
Ranking is by global Spearman (residual vs Σ_e) ascending, with tie-breakers of
permutation p(one-sided, negative) and bootstrap CI upper bound when present.

Outputs:
 - server/public/reports/sota.json
 - server/public/reports/sota.html
"""
from __future__ import annotations

import json
import math
from pathlib import Path
from typing import Any, Dict, List


def load_json(path: Path) -> Dict[str, Any] | None:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return None


def extract(row: Dict[str, Any]) -> Dict[str, Any] | None:
    try:
        delta = float(row.get("delta", {}).get("FDB_minus_shift"))
        spear = float(row.get("indicators", {}).get("spear_r"))
        perm_neg = float(
            row.get("indicators", {})
            .get("perm_test", {})
            .get("p_perm_one_sided_neg")
        )
        ci = (
            row.get("indicators", {})
            .get("bootstrap", {})
            .get("ci95", [math.nan, math.nan])
        )
        core = float(
            row.get("indicators", {})
            .get("roi_stats", {})
            .get("core_r50", {})
            .get("spear_r")
        )
        outer = float(
            row.get("indicators", {})
            .get("roi_stats", {})
            .get("outer_r75", {})
            .get("spear_r")
        )
        beta = float(row.get("beta"))
        sigma_psf = float(row.get("sigma_psf"))
        hp = float(row.get("indicators", {}).get("hp_sigma_pix"))
        N = int(row.get("N", 0))
        sshadow = row.get("indicators", {}).get("S_shadow", {})
        sval = float(sshadow.get("values", {}).get("global"))
        p_pos = float(sshadow.get("perm", {}).get("p_perm_one_sided_pos"))
        shadow_metrics = row.get("indicators", {}).get("shadow_metrics", {})
        rayleigh = shadow_metrics.get("rayleigh", {}).get("p")
        v_test = None
        v_raw = shadow_metrics.get("v_test")
        if isinstance(v_raw, dict):
            global_v = v_raw.get("global")
            if isinstance(global_v, dict):
                v_test = global_v.get("p")
        return {
            "spearman": spear,
            "delta_aicc": delta,
            "p_perm_neg": perm_neg,
            "ci95": ci,
            "core_spear": core,
            "outer_spear": outer,
            "beta": beta,
            "sigma_psf": sigma_psf,
            "hp_sigma_pix": hp,
            "N": N,
            "shadow_value": sval,
            "shadow_p_pos": p_pos,
            "shadow_rayleigh_p": float(rayleigh)
            if isinstance(rayleigh, (int, float))
            else math.nan,
            "shadow_vtest_p": float(v_test)
            if isinstance(v_test, (int, float))
            else math.nan,
        }
    except Exception:
        return None


def _sanitize(value: Any) -> Any:
    if isinstance(value, dict):
        return {k: _sanitize(v) for k, v in value.items()}
    if isinstance(value, list):
        return [_sanitize(v) for v in value]
    if isinstance(value, float) and not math.isfinite(value):
        return None
    return value


def rank_key(entry: Dict[str, Any]) -> tuple:
    ci = entry.get("ci95", [math.nan, math.nan])
    has_ci = 0
    if not (
        isinstance(ci, (list, tuple))
        and len(ci) >= 2
        and all(isinstance(v, (int, float)) and math.isfinite(v) for v in ci[:2])
    ):
        has_ci = 1
    upper_ci = ci[1] if isinstance(ci, (list, tuple)) and len(ci) > 1 else math.inf
    return (
        has_ci,
        entry["spearman"],
        entry.get("p_perm_neg", 1.0),
        upper_ci,
    )


def gather_candidates(out_dir: Path) -> List[Dict[str, Any]]:
    rows: List[Dict[str, Any]] = []
    for path in sorted(out_dir.glob("bullet_holdout*.json")):
        name = path.name
        if name.endswith("search.json") or name.startswith("train_"):
            continue
        data = load_json(path)
        if not data:
            continue
        entry = extract(data)
        if not entry:
            continue
        entry["file"] = name
        delta = entry.get("delta_aicc")
        sval = entry.get("shadow_value")
        p_pos = entry.get("shadow_p_pos")
        if not (math.isfinite(delta) and delta <= -10):
            continue
        if not (math.isfinite(sval) and sval > 0.0):
            continue
        if not (math.isfinite(p_pos) and p_pos < 0.05):
            continue
        rows.append(entry)
    return rows


def render_html(best: Dict[str, Any], rows: List[Dict[str, Any]]) -> str:
    def fmt_ci(ci: Any) -> str:
        if not (
            isinstance(ci, (list, tuple))
            and len(ci) >= 2
            and all(isinstance(v, (int, float)) and math.isfinite(v) for v in ci[:2])
        ):
            return "[—, —]"
        return f"[{ci[0]:.3f}, {ci[1]:.3f}]"

    header = """
<!doctype html><meta charset='utf-8'>
<title>Bullet SOTA Summary</title>
<style>
body{font:14px/1.45 system-ui,sans-serif;margin:20px}
table{border-collapse:collapse}
th,td{border:1px solid #ccc;padding:6px 10px;white-space:nowrap}
th{background:#f5f5f5}
</style>
<h2>Bullet Holdout — SOTA Summary</h2>
<p>Filters: ΔAICc(FDB−shift) ≤ −10, S_shadow(global) &gt; 0, permutation p(one-sided, positive) &lt; 0.05.</p>
"""
    table = "<table>\n"
    table += (
        "<tr><th>Spearman</th><th>S_shadow</th><th>Perm p(+)</th><th>Perm p(−)</th>"
        "<th>ΔAICc</th><th>CI95</th><th>β</th><th>PSF σ</th><th>HP σ</th><th>N</th><th>Snapshot</th></tr>\n"
    )
    table += (
        f"<tr><td>{best['spearman']:.6f}</td><td>{best['shadow_value']:.3f}</td>"
        f"<td>{best['shadow_p_pos']:.3g}</td><td>{best.get('p_perm_neg', float('nan')):.3g}</td>"
        f"<td>{best['delta_aicc']:.2f}</td>"
        f"<td>{fmt_ci(best['ci95'])}</td>"
        f"<td>{best['beta']:.3f}</td><td>{best['sigma_psf']:.2f}</td>"
        f"<td>{best['hp_sigma_pix']:.1f}</td><td>{best['N']}</td>"
        f"<td><a href='{best['file'].replace('.json','.html')}'>{best['file']}</a></td></tr>\n"
    )
    table += "<tr><th colspan='11'>Top 5</th></tr>\n"
    for entry in rows[:5]:
        table += (
            f"<tr><td>{entry['spearman']:.6f}</td><td>{entry['shadow_value']:.3f}</td>"
            f"<td>{entry['shadow_p_pos']:.3g}</td><td>{entry.get('p_perm_neg', float('nan')):.3g}</td>"
            f"<td>{entry['delta_aicc']:.2f}</td>"
            f"<td>{fmt_ci(entry['ci95'])}</td>"
            f"<td>{entry['beta']:.3f}</td><td>{entry['sigma_psf']:.2f}</td>"
            f"<td>{entry['hp_sigma_pix']:.1f}</td><td>{entry['N']}</td>"
            f"<td><a href='{entry['file'].replace('.json','.html')}'>{entry['file']}</a></td></tr>\n"
        )
    table += "</table>\n"
    extras = "<p><small>Rayleigh p = {rayleigh:.3g}, V-test p = {vtest:.3g}</small></p>".format(
        rayleigh=best.get("shadow_rayleigh_p", math.nan),
        vtest=best.get("shadow_vtest_p", math.nan),
    )
    return header + table + extras


def main() -> int:
    out_dir = Path("server/public/reports")
    out_dir.mkdir(parents=True, exist_ok=True)

    rows = gather_candidates(out_dir)
    if not rows:
        (out_dir / "sota.json").write_text(
            json.dumps({"error": "no feasible snapshots found"}, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )
        print("no feasible snapshots found")
        return 0

    rows.sort(key=rank_key)
    best = rows[0]

    payload = {"best": best, "candidates": rows[:10]}
    (out_dir / "sota.json").write_text(
        json.dumps(_sanitize(payload), indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    html = render_html(best, rows)
    (out_dir / "sota.html").write_text(html, encoding="utf-8")
    print("wrote", out_dir / "sota.json")
    print("wrote", out_dir / "sota.html")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
