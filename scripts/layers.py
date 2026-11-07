"""Split a generated drawing into an ink layer and a watercolor layer.

usage: python3 -I scripts/layers.py drawing.jpg out/prefix [--wash 244,142,124] [--strength 0.82]

Writes prefix-ink.png and prefix-wash.png (same size as the source, transparent
background) and a .json next to each with its size and the bounding box of its
visible pixels. The ink is read from the red channel (dark in every channel);
the wash is read from red minus blue (warm color). Under the ink lines the wash
is filled from its neighbours, so the wash has no holes when the ink moves.
"""
import json
import sys

import numpy as np
from PIL import Image, ImageFilter


def opt(name, default):
    if name in sys.argv:
        return sys.argv[sys.argv.index(name) + 1]
    return default


def save(alpha, rgb, path):
    out = np.zeros(alpha.shape + (4,), np.uint8)
    out[..., :3] = rgb
    out[..., 3] = (np.clip(alpha, 0, 1) * 255).astype(np.uint8)
    Image.fromarray(out, "RGBA").save(path, optimize=True)
    ys, xs = np.nonzero(alpha > 0.25)
    bbox = [int(xs.min()), int(ys.min()), int(xs.max()), int(ys.max())] if len(xs) else None
    with open(path[:-4] + ".json", "w") as f:
        json.dump({"size": [alpha.shape[1], alpha.shape[0]], "bbox": bbox}, f)
    return bbox


def main():
    if len(sys.argv) < 3:
        print(__doc__)
        sys.exit(2)
    src, prefix = sys.argv[1], sys.argv[2]
    wash_rgb = tuple(int(v) for v in opt("--wash", "244,142,124").split(","))
    strength = float(opt("--strength", "0.82"))
    a = np.asarray(Image.open(src).convert("RGB")).astype(np.float32)
    r, b = a[..., 0], a[..., 2]
    ink = np.clip((215 - r) / 170, 0, 1)
    ink[ink < 0.08] = 0
    wash = np.clip(((r - b) - 14) / 110, 0, 1) * (r > 150)
    grown = np.asarray(Image.fromarray((wash * 255).astype(np.uint8)).filter(ImageFilter.MaxFilter(15)).filter(ImageFilter.GaussianBlur(3))).astype(np.float32) / 255
    wash = np.maximum(wash, grown * (ink > 0.05))
    print("ink", save(ink, (27, 27, 26), f"{prefix}-ink.png"))
    if wash.max() > 0.2:
        print("wash", save(wash * strength, wash_rgb, f"{prefix}-wash.png"))
    else:
        print("wash none")


main()
