#!/usr/bin/env python3
from __future__ import annotations
import argparse, json, re, sys, time
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, List

import urllib.parse
import urllib.request


CDX = "https://web.archive.org/cdx/search/cdx"


def http_get(url: str, timeout: float = 20.0) -> bytes:
    req = urllib.request.Request(url, headers={"User-Agent": "WaybackHunt/1.0"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.read()


def list_snapshots(url: str, limit: int = 50) -> list[str]:
    params = {
        "url": url,
        "output": "json",
        "filter": "statuscode:200",
        "collapse": "digest",
        "matchType": "prefix",
        "limit": str(limit),
    }
    q = CDX + "?" + urllib.parse.urlencode(params)
    try:
        raw = http_get(q)
    except Exception:
        return []
    try:
        rows = json.loads(raw.decode("utf-8"))
    except Exception:
        return []
    # First row is header
    out: list[str] = []
    for row in rows[1:]:
        if len(row) >= 3:
            out.append(row[1])  # timestamp
    # sort descending (newest first)
    out.sort(reverse=True)
    return out


def wayback_id_url(ts: str, url: str) -> str:
    return f"https://web.archive.org/web/{ts}id_/{url}"


def is_probably_html(data: bytes) -> bool:
    head = data[:128].lower()
    return (b"<html" in head) or (b"<!doctype" in head) or (b"<head" in head)


@dataclass
class Hit:
    url: str
    ts: str
    size: int
    ok: bool
    path: str


def hunt_and_fetch(
    name: str,
    seeds: list[str],
    pattern: str,
    outdir: Path,
    max_snaps: int = 50,
    max_files: int = 10,
) -> list[Hit]:
    outdir.mkdir(parents=True, exist_ok=True)
    rx = re.compile(pattern, re.I)
    hits: list[Hit] = []
    seen_urls: set[str] = set()

    def fetch_one(candidate_url: str) -> bool:
        # enumerate snapshots for the file url directly
        snaps = list_snapshots(candidate_url, limit=max_snaps)
        for ts in snaps:
            wb = wayback_id_url(ts, candidate_url)
            try:
                data = http_get(wb)
            except Exception:
                continue
            if is_probably_html(data) or len(data) < 64:
                continue
            fn = urllib.parse.unquote(candidate_url.split("/")[-1])
            # ensure filename exists
            if not fn:
                fn = f"{name}_{ts}.bin"
            out = outdir / fn
            out.write_bytes(data)
            hits.append(Hit(url=wb, ts=ts, size=len(data), ok=True, path=str(out)))
            return True
        return False

    # 1) Try direct file URLs discovered in seed pages' HTML
    for seed in seeds:
        snaps = list_snapshots(seed, limit=max_snaps)
        for ts in snaps[:max_snaps]:
            index_url = wayback_id_url(ts, seed)
            try:
                html = http_get(index_url)
            except Exception:
                continue
            try:
                text = html.decode("utf-8", errors="ignore")
            except Exception:
                continue
            # naive href extractor to avoid dependencies
            for m in re.finditer(r'href\s*=\s*"([^"]+)"', text, re.I):
                href = m.group(1)
                if href.startswith("javascript:") or href.startswith("#"):
                    continue
                candidate = urllib.parse.urljoin(seed, href)
                if candidate in seen_urls:
                    continue
                seen_urls.add(candidate)
                if rx.search(candidate):
                    ok = fetch_one(candidate)
                    if ok and len(hits) >= max_files:
                        return hits

    return hits


def main() -> int:
    ap = argparse.ArgumentParser(description="Hunt and fetch kappa-like FITS files via Wayback")
    ap.add_argument("--name", required=True, help="cluster name, used for output dir")
    ap.add_argument("--seeds", nargs="+", help="seed URLs (directory or HTML pages)")
    ap.add_argument("--pattern", required=True, help=r"regex for file URLs to fetch, e.g. '(a1689|abell[-_]?1689).*(kappa|mass).*\\.(fits|fit)' ")
    ap.add_argument("--outdir", default=None, help="output directory (default: data/cluster/<NAME>/wayback_hunt)")
    ap.add_argument("--max-snaps", type=int, default=50)
    ap.add_argument("--max-files", type=int, default=10)
    args = ap.parse_args()

    outdir = Path(args.outdir) if args.outdir else Path("data/cluster")/args.name/"wayback_hunt"
    hits = hunt_and_fetch(
        name=args.name,
        seeds=args.seeds,
        pattern=args.pattern,
        outdir=outdir,
        max_snaps=args.max_snaps,
        max_files=args.max_files,
    )
    log = {
        "name": args.name,
        "seeds": args.seeds,
        "pattern": args.pattern,
        "outdir": str(outdir),
        "hits": [hit.__dict__ for hit in hits],
        "ts": int(time.time()),
    }
    (outdir/"wayback_hunt_log.json").write_text(json.dumps(log, indent=2), encoding="utf-8")
    print(f"found {len(hits)} files; log at {outdir/'wayback_hunt_log.json'}")
    # convenience: if we found exactly one file containing 'kappa', copy to kappa_obs.fits
    kappa_like = [h for h in hits if re.search(r"kappa", h.path, re.I)]
    if len(kappa_like) == 1:
        src = Path(kappa_like[0].path)
        dst = Path("data/cluster")/args.name/"kappa_obs.fits"
        try:
            dst.parent.mkdir(parents=True, exist_ok=True)
            dst.write_bytes(src.read_bytes())
            print("copied", src, "->", dst)
        except Exception:
            pass
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

