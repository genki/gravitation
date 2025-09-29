#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List

import yaml

REPO_ROOT = Path(__file__).resolve().parents[2]
REQUIRED_MAPS = ["omega_cut.fits", "sigma_e.fits", "kappa_obs.fits"]


def run(cmd: List[str], *, env: Dict[str, str] | None = None) -> None:
    full_env = os.environ.copy()
    if env:
        full_env.update(env)
    print("[holdout]", " ".join(cmd))
    subprocess.run(cmd, check=True, cwd=REPO_ROOT, env=full_env)


@dataclass
class ClusterStatus:
    name: str
    ready: bool
    missing: List[str] = field(default_factory=list)
    tarball: str | None = None
    notes: str | None = None

    def to_dict(self) -> Dict[str, object]:
        return {
            "name": self.name,
            "ready": self.ready,
            "missing": self.missing,
            "tarball": self.tarball,
            "notes": self.notes,
        }


def check_cluster(name: str, tarball: str | None, notes: str | None) -> ClusterStatus:
    root = REPO_ROOT / "data" / "cluster" / name
    missing = [fname for fname in REQUIRED_MAPS if not (root / fname).exists()]
    return ClusterStatus(name=name, ready=not missing, missing=missing, tarball=tarball, notes=notes)


def main() -> int:
    ap = argparse.ArgumentParser(description="Orchestrate cluster holdout pipeline using config/cluster_holdouts.yml")
    ap.add_argument("--config", default="config/cluster_holdouts.yml", help="YAML file describing training clusters and holdouts")
    ap.add_argument("--auto-train", action="store_true", help="Run train_shared_params.py if training clusters are ready")
    ap.add_argument("--auto-holdout", action="store_true", help="Run make_bullet_holdout.py for ready holdouts")
    args = ap.parse_args()

    cfg_path = REPO_ROOT / args.config
    if not cfg_path.exists():
        raise SystemExit(f"config not found: {cfg_path}")
    config = yaml.safe_load(cfg_path.read_text(encoding="utf-8"))

    train_entries = config.get("train", []) or []
    holdout_entries = config.get("holdouts", []) or []

    statuses: Dict[str, ClusterStatus] = {}

    for entry in train_entries:
        name = entry["name"]
        status = check_cluster(name, entry.get("tarball"), entry.get("notes"))
        statuses[name] = status
        print(f"[train] {name}: {'READY' if status.ready else 'missing ' + ','.join(status.missing)}")

    all_train_ready = all(statuses[name].ready for name in statuses if name in [e["name"] for e in train_entries])
    if args.auto_train and all_train_ready:
        train_names = ",".join(entry["name"] for entry in train_entries)
        env = {"PYTHONPATH": str(REPO_ROOT), "TRAIN_CLUSTERS": train_names}
        run([sys_executable(), "scripts/cluster/fit/train_shared_params.py"], env=env)
    elif args.auto_train:
        print("[train] skipped auto-train (missing maps)")

    for entry in holdout_entries:
        name = entry["name"]
        status = check_cluster(name, entry.get("tarball"), entry.get("notes"))
        statuses[name] = status
        print(f"[holdout] {name}: {'READY' if status.ready else 'missing ' + ','.join(status.missing)}")
        if args.auto_holdout and status.ready:
            train_sources = entry.get("training_source") or [t["name"] for t in train_entries]
            train_arg = ",".join(train_sources)
            cmd = [sys_executable(), "scripts/reports/make_bullet_holdout.py", "--train", train_arg, "--holdout", name]
            run(cmd)
        elif args.auto_holdout:
            print(f"[holdout] skipped auto-run for {name} (missing maps)")

    # write status summary for dashboard consumption
    out_path = REPO_ROOT / "server/public/state_of_the_art/holdout_status.json"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    payload = {"clusters": [st.to_dict() for st in statuses.values()]}
    out_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print("wrote", out_path)
    return 0


def sys_executable() -> str:
    return os.environ.get("PYTHON", sys.executable)


if __name__ == "__main__":
    import sys
    raise SystemExit(main())
