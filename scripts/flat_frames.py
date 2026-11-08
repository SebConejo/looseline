"""Cut a sheet of three flat-background panels into aligned frames.

usage: python3 -I scripts/flat_frames.py sheet.jpg out/prefix [--count 3] [--size 760]

The "line" style (scripts/generate.mjs --style line) draws each panel as a flat
terracotta square on white. Panels are found as the runs of non-white columns,
then rows. Each frame is a square cut inside its panel, shifted so the black
line of the static parts sits on frame 1, and written as prefixN.png (opaque)
with a .json holding its size and bounding box. Prints `count: N` and
`border: N BOXED` when a panel holds a frame line along its edges.
"""
import json
import sys

import numpy as np
from PIL import Image


def opt(name, default):
    return sys.argv[sys.argv.index(name) + 1] if name in sys.argv else default


def runs(on, min_len):
    out, start = [], None
    for i, v in enumerate(list(on) + [False]):
        if v and start is None:
            start = i
        elif not v and start is not None:
            if i - start >= min_len:
                out.append((start, i))
            start = None
    return out


def shift_of(ref, img):
    f = np.fft.fft2(ref) * np.conj(np.fft.fft2(img))
    c = np.fft.ifft2(f / (np.abs(f) + 1e-9)).real
    dy, dx = np.unravel_index(np.argmax(c), c.shape)
    h, w = ref.shape
    return (dy - h if dy > h // 2 else dy), (dx - w if dx > w // 2 else dx)


def main():
    if len(sys.argv) < 3:
        print(__doc__)
        sys.exit(2)
    src, prefix = sys.argv[1], sys.argv[2]
    want = int(opt("--count", "3"))
    size = int(opt("--size", "760"))
    a = np.asarray(Image.open(src).convert("RGB")).astype(np.int16)
    H, W, _ = a.shape
    from scipy import ndimage
    coral = (a[..., 0] - a[..., 2] > 60) & (a[..., 0] > 120)
    coral = ndimage.binary_closing(coral, iterations=6)
    lab, n = ndimage.label(coral)
    objs = ndimage.find_objects(lab)
    sizes = ndimage.sum(coral, lab, range(1, n + 1))
    big = [objs[i] for i in np.argsort(sizes)[::-1][:want] if sizes[i] > 0.02 * H * W]
    boxes = sorted((sl[1].start, sl[0].start, sl[1].stop, sl[0].stop) for sl in big)
    print(f"count: {len(boxes)}")
    if not boxes:
        sys.exit(1)
    side = int(min(min(x1 - x0, y1 - y0) for x0, y0, x1, y1 in boxes) * 0.94)
    m = 12  # room to shift without leaving the panel

    def crop(b, dy=0, dx=0):
        x0, y0, x1, y1 = b
        cx, cy = (x0 + x1) // 2 + dx, (y0 + y1) // 2 + dy
        return a[cy - side // 2: cy - side // 2 + side, cx - side // 2: cx - side // 2 + side]

    ink = lambda p: (p.max(2) < 90).astype(np.float32)
    ref = ink(crop(boxes[0]))
    framed = 0
    for i, b in enumerate(boxes, 1):
        dy, dx = (0, 0) if i == 1 else shift_of(ref, ink(crop(b)))
        dy, dx = int(np.clip(-dy, -m, m)), int(np.clip(-dx, -m, m))
        p = crop(b, dy, dx)
        k = ink(p)
        edge = max(k[:side // 14].mean(1).max(), k[-side // 14:].mean(1).max(), k[:, :side // 14].mean(0).max(), k[:, -side // 14:].mean(0).max())
        framed += edge > 0.6
        img = Image.fromarray(p.astype(np.uint8)).resize((size, size), Image.LANCZOS)
        # flat colors: a small palette keeps the file light and the look flat
        img.quantize(colors=32, method=Image.Quantize.FASTOCTREE, dither=Image.Dither.NONE).save(f"{prefix}{i}.png", optimize=True)
        with open(f"{prefix}{i}.json", "w") as fh:
            json.dump({"size": [size, size], "bbox": [0, 0, size - 1, size - 1]}, fh)
    print(f"border: {framed}" + (" BOXED" if framed else ""))


main()
