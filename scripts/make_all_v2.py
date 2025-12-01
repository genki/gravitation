#!/usr/bin/env python3
"""
Build a mosaic image `out/all.png` from all `*_v2_summary.png` plots.

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
import matplotlib.image as mpimg


def collect_summary_images(out_dir: str = "out") -> List[str]:
    """
    Return a sorted list of per-galaxy v2 summary PNGs.

    Excludes the aggregate `all.png` if present.
    """
    pattern = os.path.join(out_dir, "*_v2_summary.png")
    files = sorted(glob.glob(pattern))
    # be defensive: exclude any file named all.png just in case, and drop MW
    files = [
        f
        for f in files
        if os.path.basename(f) != "all.png"
        and not os.path.basename(f).startswith("MW_")
    ]
    return files


def build_mosaic(out_dir: str = "out", ncols: int = 5) -> None:
    files = collect_summary_images(out_dir)
    if not files:
        print("No *_v2_summary.png files found under", out_dir)
        return

    n = len(files)
    nrows = math.ceil(n / ncols)

    # Use a moderate figure size so that individual panels stay readable.
    fig, axes = plt.subplots(nrows, ncols, figsize=(3 * ncols, 3 * nrows))
    # axes can be a scalar if nrows=ncols=1
    if nrows == 1 and ncols == 1:
        axes = [[axes]]
    elif nrows == 1:
        axes = [axes]
    elif ncols == 1:
        axes = [[ax] for ax in axes]

    flat_axes = [ax for row in axes for ax in row]

    for ax, path in zip(flat_axes, files):
        img = mpimg.imread(path)
        ax.imshow(img)
        ax.axis("off")

    # Turn off any unused axes
    for ax in flat_axes[len(files) :]:
        ax.axis("off")

    plt.tight_layout()
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, "all.png")
    fig.savefig(out_path, dpi=150)
    plt.close(fig)
    print(f"Saved mosaic with {len(files)} panels to {out_path}")


if __name__ == "__main__":
    build_mosaic()
