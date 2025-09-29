#!/usr/bin/env python3
from __future__ import annotations
import json
import os
import socket
import subprocess as sp
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict


def _git_rev() -> str | None:
    try:
        return sp.check_output(["git", "rev-parse", "HEAD"], text=True).strip()
    except Exception:
        return None


def write_artifact(kind: str, payload: Dict[str, Any], out_dir: Path | None = None) -> Path:
    outd = out_dir or Path("data/artifacts")
    outd.mkdir(parents=True, exist_ok=True)
    ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    host = socket.gethostname().split(".")[0]
    fname = f"{ts}_{kind}_{host}.json"
    meta = {
        "kind": kind,
        "ts": ts,
        "cwd": os.getcwd(),
        "host": host,
        "git": {"rev": _git_rev()},
    }
    data = {"meta": meta, "payload": payload}
    outp = outd / fname
    outp.write_text(json.dumps(data, indent=2), encoding="utf-8")
    return outp


if __name__ == "__main__":
    # Simple smoke test
    p = write_artifact("smoke", {"ok": True})
    print("wrote", p)

