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
            continue
        # a box or corner of a panel border: touches the cell edge and its ink
        # lies along the rim of its own bounding box
        touches = ys.start < 10 or xs.start < 10 or ys.stop > h - 10 or xs.stop > w - 10
        if touches and bh > 0.3 * h and bw > 0.3 * w:
            comp = lab[sl] == i
            yy, xx = np.nonzero(comp)
            rim = (yy < 30) | (yy > bh - 30) | (xx < 30) | (xx > bw - 30)
            if rim.mean() > 0.8:
                ink[lab == i] = 0
    return ink


def bands(profile, want, min_gap):
    """Split points of a 1-D ink profile: centres of the empty runs that cut it
    into blocks. Falls back to equal parts when the gaps are not clear."""
    n = len(profile)
    empty = profile < 1
    runs, start = [], None
    for i, e in enumerate(empty):
        if e and start is None:
            start = i
        if not e and start is not None:
            if i - start >= min_gap and start > 0:
                runs.append((start + i) // 2)
            start = None
    cuts = [0] + runs + [n]
    blocks = [(cuts[i], cuts[i + 1]) for i in range(len(cuts) - 1)]
    blocks = [b for b in blocks if profile[b[0]:b[1]].sum() > 0]
    equal = [(i * n // want, (i + 1) * n // want) for i in range(want)]
    sizes = np.array([b[1] - b[0] for b in blocks], float)
    # a regular set of gutters is trusted even when the generator drew a
    # different grid than asked (3 columns instead of 4)
    if len(blocks) >= 2 and sizes.std() / sizes.mean() < 0.2:
        return blocks
    if len(blocks) < want:
        return equal
    # irregular: a gap inside a panel; keep the gutters nearest the expected grid
    if not runs:
        return equal
    cuts = [0] + [min(runs, key=lambda r: abs(r - k * n / want)) for k in range(1, want)] + [n]
    return [(cuts[i], cuts[i + 1]) for i in range(want)]


def panels(a, cols, rows):
    """Panels in reading order, found from the empty gutters between them, so a
    sheet with more or fewer panels than asked is still cut right."""
    on = np.clip((215 - a[..., 0]) / 170, 0, 1) > 0.3
    out = []
    for y0, y1 in bands(on.sum(1), rows, 12):
        for x0, x1 in bands(on[y0:y1].sum(0), cols, 12):
            out.append((y0, y1, x0, x1))
    return out


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
    cells = []
    for y0, y1, x0, x1 in panels(a, cols, rows):
        cell = a[y0:y1, x0:x1]
        if cell.shape[0] < 60 or cell.shape[1] < 60 or ((215 - cell[..., 0]) / 170 > 0.3).sum() < 500:
            continue  # an empty or sliver panel
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
        ink = erase_borders(ink)
        if (ink > 0.3).sum() < 500:
            continue  # only a panel border was there
        cells.append([ink, wash])
    # every frame on one canvas size, the largest panel
    ch, cw = max(c[0].shape[0] for c in cells), max(c[0].shape[1] for c in cells)
    for c in cells:
        for k in range(2):
            pad = np.zeros((ch, cw), np.float32)
            h, w = c[k].shape
            pad[(ch - h) // 2:(ch - h) // 2 + h, (cw - w) // 2:(cw - w) // 2 + w] = c[k]
            c[k] = pad
    print(f"{len(cells)} panels found")

    small = lambda x: np.asarray(Image.fromarray((x * 255).astype(np.uint8)).resize((cw // 4, ch // 4), Image.BILINEAR)).astype(np.float32) / 255
    ref = small(cells[0][0])
    for i, (ink, wash) in enumerate(cells):
        dy, dx = (0, 0)
        if i:
            sy, sx = shift_of(ref, small(ink))
            dy, dx = sy * 4, sx * 4
            cells[i] = [move(ink, dy, dx), move(wash, dy, dx)]
        print(f"frame {i + 1}: shifted {dx},{dy}")

    # motion check: the change from one frame to the next should be steady.
    # A step far below the median is a pause (two frames alike), far above it
    # is a jump. Both read as choppy.
    steps = []
    n = len(cells)
    for i in range(1, n + (1 if "--cycle" in sys.argv else 0)):
        a1, a0 = small(cells[i % n][0]), small(cells[i - 1][0])
        steps.append(float(np.abs(a1 - a0).mean()))
    med = float(np.median(steps))
    bad = [f"{i + 1}->{(i + 1) % n + 1}" for i, v in enumerate(steps) if v < 0.35 * med or v > 2.6 * med]
    print("steps: " + " ".join(f"{v / med:.2f}" for v in steps))
    print("motion: " + ("steady" if not bad else "UNEVEN at " + ", ".join(bad)))
    # fill check: the style is line only; a body filled black covers far more
    # of its box than an outline does
    fills = []
    for ink, _ in cells:
        ys, xs = np.nonzero(ink > 0.3)
        box = (ys.max() - ys.min() + 1) * (xs.max() - xs.min() + 1)
        fills.append(float((ink > 0.5).sum()) / box)
    print(f"fill: {max(fills):.2f}" + (" FILLED" if max(fills) > 0.16 else " line"))
    print(f"count: {len(cells)}")

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
