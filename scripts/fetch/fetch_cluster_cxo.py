#!/usr/bin/env python3
"""Download Chandra ACIS primary images (full_img2 / cntr_img2) for given ObsIDs."""

import argparse
import sys
from pathlib import Path
from urllib.parse import urljoin
from urllib.request import Request, urlopen

HREF_MARK = "href=\""


from typing import List, Tuple


def list_obs_files(obsid: int) -> List[Tuple[str, str]]:
    last_digit = str(obsid)[-1]
    base = f"https://cxc.cfa.harvard.edu/cdaftp/byobsid/{last_digit}/{obsid}/primary/"
    req = Request(base, headers={"User-Agent": "Mozilla/5.0"})
    try:
        with urlopen(req) as resp:
            html = resp.read().decode("utf-8", "replace")
    except Exception as exc:
        print(f"error: failed to list {base}: {exc}", file=sys.stderr)
        return []
    files: List[Tuple[str, str]] = []
    for line in html.splitlines():
        line = line.strip()
        if HREF_MARK not in line:
            continue
        frag = line.split(HREF_MARK, 1)[1]
        name = frag.split('"', 1)[0]
        lower = name.lower()
        if lower.endswith(('_full_img2.fits.gz', '_cntr_img2.fits.gz')):
            files.append((base, name))
    return files


def download(base: str, name: str, dest: Path, force: bool = False) -> None:
    dest.parent.mkdir(parents=True, exist_ok=True)
    dpath = dest / name
    if dpath.exists() and not force:
        return
    url = urljoin(base, name)
    req = Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urlopen(req) as resp:
        data = resp.read()
    with open(dpath, "wb") as f:
        f.write(data)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("name", help="cluster directory name under data/cluster")
    parser.add_argument("obsids", nargs="+", type=int, help="Chandra ObsIDs")
    parser.add_argument("--dest", default="data/cluster", help="cluster root (default data/cluster)")
    parser.add_argument("--force", action="store_true", help="redownload even if file exists")
    args = parser.parse_args()

    root = Path(args.dest) / args.name / "cxo"
    root.mkdir(parents=True, exist_ok=True)
    for obs in args.obsids:
        files = list_obs_files(obs)
        if not files:
            print(f"warning: no files found for ObsID {obs}", file=sys.stderr)
            continue
        for base, name in files:
            download(base, name, root, args.force)
            print(f"downloaded {name}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
