#!/usr/bin/env python3
"""
Build a mosaic image `out/all.svg` from all `*_v2_summary.svg` plots.

The layout is a fixed 5-column grid, with as many rows as needed to
include every available summary image. This script is intentionally
simple and only depends on matplotlib, which is already used elsewhere
in the project.
"""

import glob
import math
import os
from typing import List

import matplotlib.pyplot as plt


def collect_summary_tags(out_dir: str = "out") -> List[str]:
    """
    Return a sorted list of galaxy tags for which a per-galaxy v2 summary SVG exists.

    Excludes MW and any pre-existing aggregate files.
    """
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


def build_mosaic(out_dir: str = "out", ncols: int = 5) -> None:
    tags = collect_summary_tags(out_dir)
    if not tags:
        print("No *_v2_summary.svg files found under", out_dir)
        return

    n = len(tags)
    nrows = math.ceil(n / ncols)

    fig, axes = plt.subplots(nrows, ncols, figsize=(3 * ncols, 3 * nrows))
    if nrows == 1 and ncols == 1:
        axes = [[axes]]
    elif nrows == 1:
        axes = [axes]
    elif ncols == 1:
        axes = [[ax] for ax in axes]

    flat_axes = [ax for row in axes for ax in row]

    for ax, tag in zip(flat_axes, tags):
        svg_path = os.path.join(out_dir, f"{tag}_v2_summary.svg")
        # 読み込みではなく、テキストとしてラベルだけ付ける簡易ビュー:
        ax.text(
            0.5,
            0.5,
            tag,
            ha="center",
            va="center",
            fontsize=10,
        )
        ax.set_axis_off()

    for ax in flat_axes[len(tags) :]:
        ax.set_axis_off()

    plt.tight_layout()
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, "all.svg")
    fig.savefig(out_path, format="svg")
    plt.close(fig)
    print(f"Saved mosaic placeholder with {len(tags)} panels to {out_path}")


if __name__ == "__main__":
    build_mosaic()
