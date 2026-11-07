"""Cut a generated sheet of watercolor swatches into separate wash patches.

usage: python3 -I scripts/washes.py library/_washes/sheet1.jpg library/_washes/

Each swatch becomes patch-NN.png: the coral color with the painted texture kept
in the alpha channel (pigment density from the green channel), cropped to the
swatch, plus a .json with its aspect ratio. These real painted patches are what
color.py places behind drawings; code never paints watercolor itself.
"""
import json
import sys

import numpy as np
from PIL import Image, ImageFilter

CORAL = (240, 128, 110)


def main():
    if len(sys.argv) < 3:
        print(__doc__)
        sys.exit(2)
    src, out = sys.argv[1], sys.argv[2].rstrip("/")
    a = np.asarray(Image.open(src).convert("RGB")).astype(np.float32)
    g, r = a[..., 1], a[..., 0]
    paper = np.percentile(g, 90)
    alpha = np.clip((paper - g) / (paper - np.percentile(g, 1)), 0, 1)
    alpha = np.clip((alpha - 0.1) / 0.9, 0, 1) * (r - g > 25)
    blob = np.asarray(Image.fromarray((alpha > 0.12).astype(np.uint8) * 255).filter(ImageFilter.MaxFilter(15))) > 0
    h, w = blob.shape
    lab = np.zeros((h, w), np.int32)
    n = 0
    for y0 in range(0, h, 3):
        for x0 in range(0, w, 3):
            if blob[y0, x0] and not lab[y0, x0]:
                n += 1
                stack = [(y0, x0)]
                lab[y0, x0] = n
                while stack:
                    y, x = stack.pop()
                    for ny, nx in ((y + 1, x), (y - 1, x), (y, x + 1), (y, x - 1)):
                        if 0 <= ny < h and 0 <= nx < w and blob[ny, nx] and not lab[ny, nx]:
                            lab[ny, nx] = n
                            stack.append((ny, nx))
    k = 0
    for i in range(1, n + 1):
        ys, xs = np.nonzero(lab == i)
        if len(ys) < 3000:
            continue
        y0, y1, x0, x1 = ys.min(), ys.max() + 1, xs.min(), xs.max() + 1
        part = alpha[y0:y1, x0:x1] * (lab[y0:y1, x0:x1] == i)
        img = np.zeros(part.shape + (4,), np.uint8)
        img[..., :3] = CORAL
        img[..., 3] = (np.clip(part * 0.9, 0, 1) * 255).astype(np.uint8)
        k += 1
        Image.fromarray(img, "RGBA").save(f"{out}/patch-{k:02d}.png", optimize=True)
        with open(f"{out}/patch-{k:02d}.json", "w") as f:
            json.dump({"size": [int(x1 - x0), int(y1 - y0)], "aspect": round((x1 - x0) / (y1 - y0), 3)}, f)
        print(f"patch-{k:02d}: {x1 - x0}x{y1 - y0}")


main()
