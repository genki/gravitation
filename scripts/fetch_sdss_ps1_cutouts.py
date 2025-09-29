#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""指定ターゲットのSDSS/PS1カットアウトを取得する。

用法:
  uv run scripts/fetch_sdss_ps1_cutouts.py \
    --targets data/imaging/targets.txt --out data/imaging

依存: requests
注意: 一部ターゲットはSDSSフットプリント外。PS1を併用する。
"""

from __future__ import annotations

import csv
import json
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

import requests


SESAME = (
    "https://cds.u-strasbg.fr/cgi-bin/nph-sesame/-oI/A?{name}"
)
SDSS = (
    "https://skyserver.sdss.org/dr17/SkyServerWS/ImgCutout/getjpeg"
)
PS1 = (
    "https://ps1images.stsci.edu/cgi-bin/ps1cutouts"
)


@dataclass
class Target:
    name: str
    ra: float
    dec: float


def read_targets(path: Path) -> list[str]:
    out: list[str] = []
    for ln in path.read_text().splitlines():
        s = ln.strip()
        if not s or s.startswith("#"):
            continue
        out.append(s)
    return out


def resolve_sesame(name: str) -> Optional[Target]:
    url = SESAME.format(name=requests.utils.quote(name))
    r = requests.get(url, timeout=20)
    if r.status_code != 200:
        return None
    for ln in r.text.splitlines():
        if ln.startswith("%J "):
            try:
                parts = ln[3:].strip().split()
                ra = float(parts[0])
                dec = float(parts[1])
                return Target(name=name, ra=ra, dec=dec)
            except Exception:
                continue
    return None


def fetch_sdss_jpeg(t: Target, out: Path, size: int = 512) -> Optional[Path]:
    params = {
        "ra": f"{t.ra}",
        "dec": f"{t.dec}",
        "scale": "0.396127",  # ")/pix
        "width": f"{size}",
        "height": f"{size}",
    }
    try:
        r = requests.get(SDSS, params=params, timeout=12)
        if r.status_code != 200 or (
            r.headers.get("Content-Type", "").startswith("text")
        ):
            return None
        p = out / "sdss_dr17.jpg"
        p.write_bytes(r.content)
        return p
    except Exception:
        return None


def fetch_ps1_cutout(
    t: Target, out: Path, size: int = 512, filt: str = "i"
) -> Optional[Path]:
    params = {
        "pos": f"{t.ra},{t.dec}",
        "filter": filt,
        "filetypes": "stack",  # deep stacks
        "size": f"{size}",
        "output_size": f"{size}",
        "verbose": "0",
    }
    r = requests.get(PS1, params=params, timeout=30)
    if r.status_code != 200:
        return None
    # ps1cutouts returns an HTML with <img src="..."> links. Fetch first.
    src = None
    for ln in r.text.splitlines():
        ln = ln.strip()
        if "<img src=\"" in ln and "&output_size=" in ln:
            # extract URL between quotes
            i = ln.find("<img src=\"") + len("<img src=\"")
            j = ln.find("\"", i)
            src = ln[i:j]
            if src.startswith("//"):
                src = "https:" + src
            break
    if not src:
        return None
    r2 = requests.get(src, timeout=30)
    if r2.status_code != 200:
        return None
    ext = ".jpg" if "jpeg" in r2.headers.get("Content-Type", "") else ".fits"
    p = out / f"ps1_{filt}{ext}"
    p.write_bytes(r2.content)
    return p


def save_manifest(outdir: Path, recs: list[dict]) -> None:
    man = outdir / "manifest.json"
    man.write_text(json.dumps(recs, ensure_ascii=False, indent=2))


def main() -> None:
    import argparse

    ap = argparse.ArgumentParser()
    ap.add_argument("--targets", type=Path,
                    default=Path("data/imaging/targets.txt"))
    ap.add_argument("--out", type=Path, default=Path("data/imaging"))
    ap.add_argument("--size", type=int, default=512)
    ap.add_argument("--ps1_filters", default="gri")
    args = ap.parse_args()

    names = read_targets(args.targets)
    args.out.mkdir(parents=True, exist_ok=True)
    summary: list[dict] = []

    for nm in names:
        tgt = resolve_sesame(nm)
        if tgt is None:
            summary.append({"name": nm, "status": "resolve_failed"})
            continue
        od = args.out / nm
        od.mkdir(parents=True, exist_ok=True)
        got: list[str] = []
        p_sdss = fetch_sdss_jpeg(tgt, od, size=args.size)
        if p_sdss:
            got.append(p_sdss.name)
        for f in args.ps1_filters:
            p = fetch_ps1_cutout(tgt, od, size=args.size, filt=f)
            if p:
                got.append(p.name)
            time.sleep(0.2)
        summary.append({
            "name": nm,
            "ra": tgt.ra,
            "dec": tgt.dec,
            "files": got,
        })
        save_manifest(od, recs=[{"name": nm, "ra": tgt.ra,
                                 "dec": tgt.dec, "files": got}])
        time.sleep(0.3)

    save_manifest(args.out, recs=summary)


if __name__ == "__main__":
    main()
