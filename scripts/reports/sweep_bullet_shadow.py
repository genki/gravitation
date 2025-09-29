#!/usr/bin/env python3
"""Parameter sweep helper for Bullet holdout shadow metrics.

Runs scripts/reports/make_bullet_holdout.py over a grid of parameter settings
and logs the resulting S_shadow / ΔAICc statistics for quick comparison.
"""
from __future__ import annotations

import argparse
import itertools
import json
import os
import subprocess
import sys
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Iterable, Optional

REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_TRAIN = "Abell1689,CL0024"
DEFAULT_HOLDOUT = "Bullet"
RESULTS_DIR = REPO_ROOT / "tmp" / "sweep"
CLUSTER_DIR = REPO_ROOT / "server" / "public" / "reports" / "cluster"

def _parse_float_list(text: str | None) -> list[float]:
    if not text:
        return []
    values: list[float] = []
    for token in text.split(','):
        token = token.strip()
        if not token:
            continue
        try:
            values.append(float(token))
        except ValueError:
            continue
    return values

@dataclass(frozen=True)
class SweepPoint:
    psf_sigma: Optional[float]
    hp_sigma: Optional[float]
    weight_power: Optional[float]
    mask_q: Optional[float]
    edge_q: Optional[float]
    se_q: Optional[float]
    sn_q: Optional[float]

    def as_dict(self) -> dict[str, Optional[float]]:
        return {
            "psf_sigma": self.psf_sigma,
            "hp_sigma": self.hp_sigma,
            "weight_power": self.weight_power,
            "mask_q": self.mask_q,
            "edge_q": self.edge_q,
            "se_q": self.se_q,
            "sn_q": self.sn_q,
        }

def _format_arg_list(values: Iterable[float]) -> str:
    return ",".join(f"{v:g}" for v in values)


def run_holdout(point: SweepPoint, args: argparse.Namespace) -> dict:
    env = os.environ.copy()
    perm_shadow = args.perm_shadow
    perm_resid = args.perm_resid if args.perm_resid is not None else args.perm_shadow
    env.update({
        "BULLET_SHADOW_PERM_N": str(perm_shadow),
        "BULLET_SHADOW_PERM_MIN": str(perm_shadow),
        "BULLET_PERM_N": str(perm_resid),
        "BULLET_PERM_MIN": str(perm_resid),
        "BULLET_BOOT_N": str(args.boot_n),
    })
    if point.mask_q is not None:
        env["BULLET_MASK_Q"] = f"{point.mask_q:g}"
    if point.edge_q is not None:
        env["BULLET_SHADOW_EDGE_QS"] = f"{point.edge_q:g}"
    if point.se_q is not None:
        env["BULLET_SHADOW_SE_Q"] = f"{point.se_q:g}"
    if point.sn_q is not None:
        env["BULLET_SHADOW_SN_Q"] = f"{point.sn_q:g}"

    cmd = [
        sys.executable,
        "scripts/reports/make_bullet_holdout.py",
        "--train",
        args.train,
        "--holdout",
        args.holdout,
    ]
    if point.psf_sigma is not None:
        cmd += ["--sigma-psf", f"{point.psf_sigma:g}"]
    if point.hp_sigma is not None:
        cmd += ["--sigma-highpass", f"{point.hp_sigma:g}"]
    if point.weight_power is not None:
        cmd += ["--weight-powers", f"{point.weight_power:g}"]
    if point.mask_q is not None:
        cmd += ["--roi-quantiles", f"{point.mask_q:g}"]
    if args.beta_sweep:
        cmd += ["--beta-sweep", args.beta_sweep]
    try:
        subprocess.run(cmd, cwd=REPO_ROOT, check=True, env=env)
    except subprocess.CalledProcessError as exc:
        raise RuntimeError(f"holdout command failed with exit code {exc.returncode}") from exc

    summary_path = CLUSTER_DIR / f"{args.holdout}_holdout.json"
    if not summary_path.exists():
        raise FileNotFoundError(f"Expected summary at {summary_path}")
    with summary_path.open("r", encoding="utf-8") as fp:
        summary = json.load(fp)
    return summary


def extract_metrics(summary: dict) -> dict:
    indicators = summary.get("indicators", {})
    shadow_block = indicators.get("S_shadow", {})
    perm = shadow_block.get("perm", {}) or {}
    values = shadow_block.get("values", {}) or {}
    neg_top = indicators.get("neg_corr_top10", {}) or {}
    neg_global = indicators.get("neg_corr_global", {}) or {}
    delta = summary.get("delta", {}) or {}

    result = {
        "S_shadow": values.get("global"),
        "S_shadow_outer": values.get("outer_r75"),
        "p_perm": perm.get("p_perm_one_sided_pos"),
        "perm_n": perm.get("n"),
        "delta_FDB_minus_rot": delta.get("FDB_minus_rot"),
        "delta_FDB_minus_shift": delta.get("FDB_minus_shift"),
        "spearman_top10": neg_top.get("spear_r"),
        "spearman_top10_p": neg_top.get("p"),
        "spearman_global": neg_global.get("spear_r"),
        "spearman_global_p": neg_global.get("p"),
    }
    return result


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Sweep Bullet holdout parameters")
    parser.add_argument("--train", default=DEFAULT_TRAIN, help="Training clusters list (comma separated)")
    parser.add_argument("--holdout", default=DEFAULT_HOLDOUT, help="Holdout cluster name")
    parser.add_argument("--psf", default="1.0", help="Comma-separated PSF sigma list (pix)")
    parser.add_argument("--hp", default="1.0", help="Comma-separated high-pass sigma list (pix)")
    parser.add_argument("--weights", default="0.0", help="Comma-separated weight exponents")
    parser.add_argument("--mask-q", default="0.75", help="Mask quantile list")
    parser.add_argument("--edge-q", default="0.75", help="Edge gradient quantile list")
    parser.add_argument("--se-q", default="0.75", help="Σ_e quantile list")
    parser.add_argument("--sn-q", default="0.9", help="Signal-to-noise quantile list")
    parser.add_argument("--perm-shadow", type=int, default=256, help="Shadow permutation count per run")
    parser.add_argument("--perm-resid", type=int, default=256, help="Residual permutation count per run")
    parser.add_argument("--boot-n", type=int, default=0, help="Bootstrap sample count (default 0 to skip)")
    parser.add_argument("--beta-sweep", default="", help="Optional beta sweep list to pass through")
    parser.add_argument("--output", default="", help="Optional output JSONL path")
    args = parser.parse_args(argv)

    psf_list = _parse_float_list(args.psf) or [None]
    hp_list = _parse_float_list(args.hp) or [None]
    weight_list = _parse_float_list(args.weights) or [None]
    mask_list = _parse_float_list(args.mask_q) or [None]
    edge_list = _parse_float_list(args.edge_q) or [None]
    se_list = _parse_float_list(args.se_q) or [None]
    sn_list = _parse_float_list(args.sn_q) or [None]

    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    if args.output:
        output_path = Path(args.output)
        output_path.parent.mkdir(parents=True, exist_ok=True)
    else:
        timestamp = datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")
        output_path = RESULTS_DIR / f"bullet_shadow_sweep_{timestamp}.jsonl"

    combos = itertools.product(psf_list, hp_list, weight_list, mask_list, edge_list, se_list, sn_list)
    results: list[dict] = []

    for combo in combos:
        point = SweepPoint(*combo)
        summary = run_holdout(point, args)
        metrics = extract_metrics(summary)
        record = {
            "params": point.as_dict(),
            "metrics": metrics,
        }
        results.append(record)
        with output_path.open("a", encoding="utf-8") as fp:
            fp.write(json.dumps(record, ensure_ascii=False) + "\n")
        print(json.dumps(record, ensure_ascii=False))
        sys.stdout.flush()

    print(f"wrote {len(results)} records to {output_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
