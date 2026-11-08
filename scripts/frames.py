"""Cut a frame sheet into aligned animation frames.

usage: python3 -I scripts/frames.py sheet.jpg out/prefix [--grid 2x2] [--size 760]

The sheet holds the same drawing in a grid of panels (scripts/generate.mjs
--kind frames). Each panel becomes prefixN.png: ink and coral watercolor on a
transparent square of --size pixels. Panel borders the generator may have drawn
are erased. Every frame is shifted so its static parts sit exactly on frame 1
(cross-correlation of the ink), so only the moving part changes when the frames
play. A .json next to each frame holds its size and bounding box.
"""
import json
import sys

import numpy as np
from PIL import Image

INK = (27, 27, 26)
CORAL = (240, 128, 110)


def opt(name, default):
    return sys.argv[sys.argv.index(name) + 1] if name in sys.argv else default


def erase_borders(ink):
    """Remove panel borders the generator may draw around a panel.

    1. Any row or column in the outer eighth of the cell that is mostly ink is a
       border line: its band is blanked, even when the drawing touches it.
    2. An isolated, thin, straight stroke near an edge is a broken border piece.
       A floor line joined to the drawing is one component with it, so it stays.
    """
    from scipy import ndimage
    h, w = ink.shape
    on = ink > 0.4
    for axis, n, span in ((0, h, w), (1, w, h)):
        cover = on.sum(1 - axis) / span
        for i in list(range(n // 8)) + list(range(n - n // 8, n)):
            if cover[i] > 0.45:
                lo, hi = max(0, i - 12), min(n, i + 13)
                if axis == 0:
                    ink[lo:hi, :] = 0
                else:
                    ink[:, lo:hi] = 0
    lab, count = ndimage.label(ndimage.binary_dilation(ink > 0.3, iterations=3))
    for i, sl in enumerate(ndimage.find_objects(lab), 1):
        ys, xs = sl
        bh, bw = ys.stop - ys.start, xs.stop - xs.start
        flat = bh < 0.04 * h and bw > 0.15 * w
        tall = bw < 0.04 * w and bh > 0.15 * h
        near = ys.start < 0.15 * h or ys.stop > 0.85 * h or xs.start < 0.15 * w or xs.stop > 0.85 * w
        if (flat or tall) and near:
            ink[lab == i] = 0
    return ink


def shift_of(ref, img):
    """Translation that moves img onto ref, from FFT cross-correlation."""
    f = np.fft.fft2(ref) * np.conj(np.fft.fft2(img))
    c = np.fft.ifft2(f).real
    y, x = np.unravel_index(np.argmax(c), c.shape)
    h, w = c.shape
    if y > h // 2:
        y -= h
    if x > w // 2:
        x -= w
    return int(y), int(x)


def move(a, dy, dx):
    out = np.zeros_like(a)
    h, w = a.shape[:2]
    ys, yd = (slice(0, h - dy), slice(dy, h)) if dy >= 0 else (slice(-dy, h), slice(0, h + dy))
    xs, xd = (slice(0, w - dx), slice(dx, w)) if dx >= 0 else (slice(-dx, w), slice(0, w + dx))
    out[yd, xd] = a[ys, xs]
    return out


def main():
    if len(sys.argv) < 3:
        print(__doc__)
        sys.exit(2)
    src, prefix = sys.argv[1], sys.argv[2]
    cols, rows = (int(v) for v in opt("--grid", "2x2").split("x"))
    size = int(opt("--size", "760"))
    a = np.asarray(Image.open(src).convert("RGB")).astype(np.float32)
    H, W = a.shape[:2]
    ch, cw = H // rows, W // cols
    cells = []
    for r in range(rows):
        for c in range(cols):
            cell = a[r * ch:(r + 1) * ch, c * cw:(c + 1) * cw]
            R, B = cell[..., 0], cell[..., 2]
            ink = np.clip((215 - R) / 170, 0, 1)
            ink[ink < 0.08] = 0
            # the paper is not always neutral: measure its tint and paint above it
            paper = np.median(R - B)
            wash = np.clip((R - B - paper - 14) / 110, 0, 1) * (ink < 0.3)
            wash[wash < 0.1] = 0
            # a cell edge is never part of the drawing: blank a thin margin
            m = 6
            for layer in (ink, wash):
                layer[:m], layer[-m:], layer[:, :m], layer[:, -m:] = 0, 0, 0, 0
            cells.append([erase_borders(ink), wash])

    small = lambda x: np.asarray(Image.fromarray((x * 255).astype(np.uint8)).resize((cw // 4, ch // 4), Image.BILINEAR)).astype(np.float32) / 255
    ref = small(cells[0][0])
    for i, (ink, wash) in enumerate(cells):
        dy, dx = (0, 0)
        if i:
            sy, sx = shift_of(ref, small(ink))
            dy, dx = sy * 4, sx * 4
            cells[i] = [move(ink, dy, dx), move(wash, dy, dx)]
        print(f"frame {i + 1}: shifted {dx},{dy}")

    # one common crop around everything drawn, kept square and centred
    union = np.zeros((ch, cw), bool)
    for ink, wash in cells:
        union |= (ink > 0.2) | (wash > 0.2)
    ys, xs = np.nonzero(union)
    cx, cy = (xs.min() + xs.max()) / 2, (ys.min() + ys.max()) / 2
    side = int(max(xs.max() - xs.min(), ys.max() - ys.min()) * 1.18)
    x0, y0 = int(cx - side / 2), int(cy - side / 2)

    for i, (ink, wash) in enumerate(cells):
        out = np.zeros((side, side, 4), np.float32)
        for layer, color in ((wash, CORAL), (ink, INK)):
            pad = np.zeros((side, side), np.float32)
            sy0, sx0 = max(0, y0), max(0, x0)
            sy1, sx1 = min(ch, y0 + side), min(cw, x0 + side)
            pad[sy0 - y0:sy1 - y0, sx0 - x0:sx1 - x0] = layer[sy0:sy1, sx0:sx1]
            # paint "over": ink sits on top of the wash
            a_old = out[..., 3]
            a_new = pad + a_old * (1 - pad)
            for k in range(3):
                out[..., k] = np.where(a_new > 0, (color[k] * pad + out[..., k] * a_old * (1 - pad)) / np.maximum(a_new, 1e-6), 0)
            out[..., 3] = a_new
        rgba = np.dstack([out[..., :3], out[..., 3:] * 255]).clip(0, 255).astype(np.uint8)
        img = Image.fromarray(rgba, "RGBA")
        img = img.resize((size, size), Image.LANCZOS)
        path = f"{prefix}{i + 1}.png"
        img.save(path, optimize=True)
        al = np.asarray(img)[..., 3] > 64
        yy, xx = np.nonzero(al)
        with open(path[:-4] + ".json", "w") as f:
            json.dump({"size": [size, size], "bbox": [int(xx.min()), int(yy.min()), int(xx.max()), int(yy.max())]}, f)
    print(f"{len(cells)} frames, {size}px")


main()
