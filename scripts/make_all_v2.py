#!/usr/bin/env python3
"""
Build a simple SVG mosaic `out/all.svg` from all `out/*_v2_summary.svg` plots.

The mosaic does not rasterize the individual SVGs; instead it arranges them
via <image> references in a fixed 5-column grid. This keeps everything in
vector form while providing a quick visual index.
"""

import glob
import math
import os
from typing import List


def collect_tags(out_dir: str = "out") -> List[str]:
    pattern = os.path.join(out_dir, "*_v2_summary.svg")
    files = sorted(glob.glob(pattern))
    tags: List[str] = []
    for f in files:
        base = os.path.basename(f)
        if base == "all.svg":
            continue
        if base.startswith("MW_"):
            continue
        tag = base.replace("_v2_summary.svg", "")
        tags.append(tag)
    return tags


def build_mosaic(out_dir: str = "out", ncols: int = 5, tile_px: int = 300) -> None:
    tags = collect_tags(out_dir)
    if not tags:
        print("No *_v2_summary.svg files found under", out_dir)
        return

    n = len(tags)
    nrows = math.ceil(n / ncols)
    width = ncols * tile_px
    height = nrows * tile_px

    lines = [
        '<?xml version="1.0" encoding="UTF-8" standalone="no"?>',
        '<svg xmlns="http://www.w3.org/2000/svg"',
        '     xmlns:xlink="http://www.w3.org/1999/xlink"',
        f'     width="{width}" height="{height}">',
    ]

    for idx, tag in enumerate(tags):
        row = idx // ncols
        col = idx % ncols
        x = col * tile_px
        y = row * tile_px
        href = f"{tag}_v2_summary.svg"
        lines.append(
            f'  <image xlink:href="{href}" x="{x}" y="{y}" '
            f'width="{tile_px}" height="{tile_px}" />'
        )

    lines.append("</svg>")

    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, "all.svg")
    with open(out_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    print(f"Saved SVG mosaic referencing {n} panels to {out_path}")


if __name__ == "__main__":
    build_mosaic()

