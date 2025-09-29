#!/usr/bin/env python3
"""Download Frontier Fields Lenstool FITS for MACSJ0416 and Abell S1063."""
import argparse
import sys
import tarfile
from pathlib import Path
from urllib.parse import urljoin
from urllib.request import urlopen, Request

CLUSTERS = {
    "macs0416": {
        "cats_v4": "https://archive.stsci.edu/pub/hlsp/frontier/macs0416/models/cats/v4/",
        "sharon_v4": "https://archive.stsci.edu/pub/hlsp/frontier/macs0416/models/sharon/v4/",
    },
    "abells1063": {
        "cats_v4": "https://archive.stsci.edu/pub/hlsp/frontier/abells1063/models/cats/v4/",
        "sharon_v4": "https://archive.stsci.edu/pub/hlsp/frontier/abells1063/models/sharon/v4/",
    },
}


def list_fits(url: str) -> list[str]:
    req = Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urlopen(req) as resp:
        html = resp.read().decode("utf-8", "replace")
    entries: list[str] = []
    for line in html.splitlines():
        line = line.strip()
        if not line:
            continue
        parts = line.split("href=")
        if len(parts) < 2:
            continue
        href = parts[1].split('"')[1]
        if href.lower().endswith(".fits"):
            entries.append(href)
    return entries


def download_file(url: str, dest: Path, force: bool) -> None:
    if dest.exists() and not force:
        return
    dest.parent.mkdir(parents=True, exist_ok=True)
    req = Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urlopen(req) as resp:
        data = resp.read()
    with open(dest, "wb") as f:
        f.write(data)


def make_tar(cluster: str, cluster_root: Path, tar_dir: Path) -> Path:
    tar_dir.mkdir(parents=True, exist_ok=True)
    tar_path = tar_dir / f"{cluster}_lenstool_v4.tar.gz"
    with tarfile.open(tar_path, "w:gz") as tar:
        for path in sorted(cluster_root.rglob("*.fits")):
            tar.add(path, arcname=path.relative_to(cluster_root))
    return tar_path


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dest", default="data/raw/frontier", help="Download root directory")
    parser.add_argument("--force", action="store_true", help="Redownload files even if present")
    parser.add_argument("--skip-tar", action="store_true", help="Skip tarball creation")
    args = parser.parse_args()

    root = Path(args.dest)
    for cluster, teams in CLUSTERS.items():
        cluster_root = root / cluster
        for label, url in teams.items():
            dest_dir = cluster_root / label
            fits_files = list_fits(url)
            if not fits_files:
                print(f"warning: no fits files found at {url}", file=sys.stderr)
            for name in fits_files:
                dest = dest_dir / name
                download_file(urljoin(url, name), dest, args.force)
        if not args.skip_tar:
            tar_path = make_tar(cluster, cluster_root, cluster_root)
            print(f"created tarball: {tar_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
