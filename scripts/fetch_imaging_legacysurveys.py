#!/usr/bin/env python3
"""
LegacySurveys Viewer経由で銀河の画像カットアウトを取得する。

入力名をCDS Sesameで解決し(RA,Dec)を得て、以下のレイヤを保存:
- ls-dr9 (光学RGB合成)
- galex (NUV, FUV)
- unwise-neo7 (W1, W2)

出力: data/imaging/<name>/<layer>[_<band>].jpg
"""
from __future__ import annotations

import argparse
import json
import time
from pathlib import Path
from typing import Optional, Tuple

import requests


def sesame_resolve(name: str) -> Optional[Tuple[float, float]]:
    url = "https://cds.u-strasbg.fr/cgi-bin/nph-sesame/-oI/A?" + \
        requests.utils.quote(name)
    r = requests.get(url, timeout=20)
    if r.status_code != 200:
        return None
    ra = dec = None
    for line in r.text.splitlines():
        if line.startswith("%J "):
            # %J  RA  Dec  = ... also present; we take the two floats
            try:
                parts = line[3:].strip().split()
                ra = float(parts[0])
                dec = float(parts[1])
                return ra, dec
            except Exception:
                continue
    return None


def fetch_cutout(ra: float, dec: float, layer: str, bands: str,
                 pixscale: float, size: int) -> bytes:
    base = "https://www.legacysurvey.org/viewer/cutout.jpg"
    params = {
        "ra": f"{ra}",
        "dec": f"{dec}",
        "layer": layer,
        "pixscale": str(pixscale),
        "size": str(size),
    }
    if bands:
        params["bands"] = bands
    r = requests.get(base, params=params, timeout=30)
    r.raise_for_status()
    return r.content


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--targets", type=Path,
                    default=Path("data/imaging/targets.txt"))
    ap.add_argument("--size", type=int, default=1024)
    args = ap.parse_args()

    raw = args.targets.read_text(encoding="utf-8").splitlines()
    names = [ln.strip() for ln in raw if ln.strip() and \
             not ln.strip().startswith("#")]
    outroot = Path("data/imaging")
    outroot.mkdir(parents=True, exist_ok=True)
    manifest = {}

    for nm in names:
        pos = sesame_resolve(nm)
        if not pos:
            print(f"warn: cannot resolve {nm}")
            continue
        ra, dec = pos
        ddir = outroot / nm.replace(" ", "_")
        ddir.mkdir(parents=True, exist_ok=True)
        items = []
        # Optical (ls-dr9)
        try:
            jpg = fetch_cutout(ra, dec, layer="ls-dr9", bands="", \
                               pixscale=0.262, size=args.size)
            (ddir / "ls-dr9.jpg").write_bytes(jpg)
            items.append({"layer": "ls-dr9", "file": "ls-dr9.jpg"})
        except Exception as e:
            print(f"warn: ls-dr9 failed for {nm}: {e}")
        # GALEX
        for b in ("NUV", "FUV"):
            try:
                jpg = fetch_cutout(ra, dec, layer="galex", bands=b,
                                   pixscale=1.5, size=args.size)
                fn = f"galex_{b}.jpg"
                (ddir / fn).write_bytes(jpg)
                items.append({"layer": "galex", "band": b, "file": fn})
            except Exception as e:
                print(f"warn: galex {b} failed for {nm}: {e}")
        # unWISE
        for b in ("W1", "W2"):
            try:
                jpg = fetch_cutout(ra, dec, layer="unwise-neo7", bands=b,
                                   pixscale=2.75, size=args.size)
                fn = f"unwise_{b}.jpg"
                (ddir / fn).write_bytes(jpg)
                items.append({"layer": "unwise-neo7", "band": b,
                              "file": fn})
            except Exception as e:
                print(f"warn: unwise {b} failed for {nm}: {e}")
        # sleep politely
        time.sleep(0.3)
        manifest[nm] = {"ra": ra, "dec": dec, "files": items}
        (ddir / "manifest.json").write_text(
            json.dumps(manifest[nm], indent=2), encoding="utf-8")

    (outroot / "manifest.json").write_text(
        json.dumps(manifest, indent=2), encoding="utf-8")
    print(f"Saved imaging to {outroot}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
