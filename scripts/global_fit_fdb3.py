#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import annotations

from pathlib import Path
import csv
import numpy as np

from src.fdb.global_fit import global_fit
from src.fdb.sparc import load_sparc_rotmod


def main():
    base = Path("data/sparc/sparc_database")
    outd = Path("assets/results")
    outd.mkdir(parents=True, exist_ok=True)
    res = global_fit(base)
    imp = res.redchi2_gr / max(res.redchi2_fdb3, 1e-9)
    print(
        "Global FDB3: redχ² GR=%.2f FDB3=%.2f  x%.2f  "
        "a=%.2f b=%.2f c=%.2f"
        % (res.redchi2_gr, res.redchi2_fdb3, imp,
           res.a, res.b, res.c)
    )
    # 保存（概要）
    with open(outd / "global_fit_summary.csv", "w",
              newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["metric", "value"])
        w.writerow(["redchi2_gr", f"{res.redchi2_gr:.6f}"])
        w.writerow(["redchi2_fdb3", f"{res.redchi2_fdb3:.6f}"])
        w.writerow(["improvement", f"{imp:.6f}"])
        w.writerow(["a", f"{res.a:.6f}"])
        w.writerow(["b", f"{res.b:.6f}"])
        w.writerow(["c", f"{res.c:.6f}"])

    # 銀河別M/Lを保存
    files = sorted(base.glob("*_rotmod.dat"))
    names = [p.stem.replace("_rotmod", "") for p in files]
    with open(outd / "global_fit_ml.csv", "w",
              newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["name", "ml_disk", "ml_bul"])
        for n, md, mb in zip(names, res.ml_disk, res.ml_bul):
            w.writerow([n, f"{md:.6f}", f"{mb:.6f}"])


if __name__ == "__main__":
    main()
