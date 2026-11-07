"""Cut a pose sheet into separate poses aligned on the feet.

usage: python3 -I scripts/poses.py sheet.jpg out/prefix [--size 520,760] [--feet 720] [--gap 10]

The sheet holds the same character drawn several times in a row on one
baseline. Poses are found as runs of columns that hold ink, split by at least
--gap empty columns. Each pose is written as prefix1.png, prefix2.png, ... on a
transparent canvas of --size, with the lowest ink row at y = --feet and the
centre of the feet at the horizontal middle, plus a .json with its bounding box.
"""
import json
import sys

import numpy as np
from PIL import Image


def opt(name, default):
    if name in sys.argv:
        return sys.argv[sys.argv.index(name) + 1]
    return default


def main():
    if len(sys.argv) < 3:
        print(__doc__)
        sys.exit(2)
    src, prefix = sys.argv[1], sys.argv[2]
    W, H = (int(v) for v in opt("--size", "520,760").split(","))
    feet_y = int(opt("--feet", "720"))
    min_gap = int(opt("--gap", "10"))
    a = np.asarray(Image.open(src).convert("RGB")).astype(np.float32)
    ink = np.clip((215 - a[..., 0]) / 170, 0, 1)
    ink[ink < 0.08] = 0
    cols = (ink > 0.3).sum(0) > 0
    segs, start, gap = [], None, 0
    for x, on in enumerate(cols):
        if on and start is None:
            start = x
        if not on and start is not None:
            gap += 1
            if gap > min_gap:
                segs.append((start, x - gap))
                start, gap = None, 0
        elif on:
            gap = 0
    if start is not None:
        segs.append((start, len(cols) - 1))
    segs = [s for s in segs if s[1] - s[0] > 60]
    print("poses found:", len(segs))
    for i, (x0, x1) in enumerate(segs):
        sub = ink[:, x0:x1 + 1]
        ys, xs = np.nonzero(sub > 0.3)
        low = ys.max()
        feet = xs[ys > low - 40].mean()
        dx, dy = int(round(W / 2 - feet)), int(round(feet_y - low))
        out = np.zeros((H, W, 4), np.uint8)
        out[..., :3] = (27, 27, 26)
        for y in range(sub.shape[0]):
            ty = y + dy
            if 0 <= ty < H:
                row = sub[y]
                lo, hi = max(0, -dx), min(len(row), W - dx)
                if hi > lo:
                    out[ty, dx + lo:dx + hi, 3] = (row[lo:hi] * 255).astype(np.uint8)
        path = f"{prefix}{i + 1}.png"
        Image.fromarray(out, "RGBA").save(path, optimize=True)
        alpha = out[..., 3] > 64
        ys2, xs2 = np.nonzero(alpha)
        bbox = [int(xs2.min()), int(ys2.min()), int(xs2.max()), int(ys2.max())]
        with open(path[:-4] + ".json", "w") as f:
            json.dump({"size": [W, H], "bbox": bbox}, f)
        cut = xs.min() + dx < 0 or xs.max() + dx >= W or ys.min() + dy < 0
        print(f"pose {i + 1}: bbox {bbox}" + ("  WARNING: cut by the canvas, use a larger --size" if cut else ""))


main()
