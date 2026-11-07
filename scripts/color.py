"""Paint loose coral watercolor into chosen regions of an ink drawing.

usage:
  python3 -I scripts/color.py DIR --list
      writes DIR/regions.png: every closed region of the drawing with a number
  python3 -I scripts/color.py DIR --regions 3,7,12 [--seed 1] [--close 9]
      writes DIR/color-wash.png (the watercolor layer), DIR/version-color.jpg
      (paper + watercolor + ink) and DIR/version-ink.jpg (paper + ink only)

DIR holds layer-ink.png (from layers.py). A region is a connected area of paper
enclosed by ink; gaps narrower than --close (in half-size pixels) are closed
first, because hand-drawn contours are often open. The watercolor follows the region loosely: it is shifted a
little, its edge is irregular, it pools darker at the rim and carries paper
grain, as references/style.md section 8 asks.
"""
import json
import sys

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

PAPER = (244, 242, 236)
CORAL = (244, 142, 124)


def opt(name, default=None):
    if name in sys.argv:
        return sys.argv[sys.argv.index(name) + 1]
    return default


def label(free):
    h, w = free.shape
    lab = np.zeros((h, w), np.int32)
    sizes = [0]
    current = 0
    for y0 in range(0, h, 2):
        for x0 in range(0, w, 2):
            if not free[y0, x0] or lab[y0, x0]:
                continue
            current += 1
            stack = [(y0, x0)]
            lab[y0, x0] = current
            n = 0
            while stack:
                y, x = stack.pop()
                n += 1
                for ny, nx in ((y + 1, x), (y - 1, x), (y, x + 1), (y, x - 1)):
                    if 0 <= ny < h and 0 <= nx < w and free[ny, nx] and not lab[ny, nx]:
                        lab[ny, nx] = current
                        stack.append((ny, nx))
            sizes.append(n)
    return lab, sizes


def blur(a, r):
    img = Image.fromarray((np.clip(a, 0, 1) * 255).astype(np.uint8))
    return np.asarray(img.filter(ImageFilter.GaussianBlur(r))).astype(np.float32) / 255


def noise(shape, scale, rng):
    h, w = shape
    small = rng.random((max(2, h // scale), max(2, w // scale))).astype(np.float32)
    img = Image.fromarray((small * 255).astype(np.uint8)).resize((w, h), Image.BICUBIC)
    return np.asarray(img).astype(np.float32) / 255


def regions_of(ink_alpha, close):
    small = ink_alpha[::2, ::2]
    if close > 1:
        img = Image.fromarray((np.clip(small, 0, 1) * 255).astype(np.uint8))
        small = np.asarray(img.filter(ImageFilter.MaxFilter(close | 1))).astype(np.float32) / 255
    free = small < 0.25
    lab, sizes = label(free)
    border = set(np.unique(np.concatenate([lab[0], lab[-1], lab[:, 0], lab[:, -1]])))
    keep = [i for i in range(1, len(sizes)) if i not in border and sizes[i] > 150]
    return lab, keep


def main():
    if len(sys.argv) < 3:
        print(__doc__)
        sys.exit(2)
    d = sys.argv[1].rstrip("/")
    ink_img = Image.open(f"{d}/layer-ink.png")
    ink = np.asarray(ink_img).astype(np.float32)[..., 3] / 255
    close = int(opt("--close", "9"))
    lab, keep = regions_of(ink, close)
    grow = close
    if "--list" in sys.argv:
        base = Image.new("RGB", ink_img.size, PAPER)
        base.paste(ink_img, (0, 0), ink_img)
        tint = np.zeros(lab.shape + (4,), np.uint8)
        rng = np.random.default_rng(3)
        for i in keep:
            tint[lab == i] = (*rng.integers(80, 230, 3), 90)
        over = Image.fromarray(tint, "RGBA").resize(ink_img.size, Image.NEAREST)
        base.paste(over, (0, 0), over)
        draw = ImageDraw.Draw(base)
        try:
            font = ImageFont.truetype("/System/Library/Fonts/Supplemental/Arial Bold.ttf", 26)
        except Exception:
            font = ImageFont.load_default()
        for i in keep:
            ys, xs = np.nonzero(lab == i)
            cy, cx = int(np.median(ys)) * 2, int(np.median(xs)) * 2
            draw.text((cx - 10, cy - 14), str(i), fill=(200, 0, 0), font=font)
        base.save(f"{d}/regions.png")
        print(f"{d}/regions.png: {len(keep)} regions")
        return
    chosen = [int(v) for v in opt("--regions", "").split(",") if v]
    rng = np.random.default_rng(int(opt("--seed", "1")))
    small_mask = np.isin(lab, chosen).astype(np.float32)
    if grow > 1:
        img = Image.fromarray((small_mask * 255).astype(np.uint8))
        small_mask = np.asarray(img.filter(ImageFilter.MaxFilter(grow | 1))).astype(np.float32) / 255
    mask = np.asarray(Image.fromarray((small_mask * 255).astype(np.uint8)).resize(ink_img.size, Image.BILINEAR)).astype(np.float32) / 255
    h, w = mask.shape
    dx, dy = (rng.random(2) - 0.5) * 0.03 * w
    shifted = np.roll(np.roll(mask, int(dy), 0), int(dx), 1)
    loose = blur(shifted, 9) + (noise((h, w), 40, rng) - 0.5) * 0.55
    body = np.clip((loose - 0.42) * 6, 0, 1)
    rim = np.clip(body - blur(body, 7), 0, 1) * 1.6
    density = 0.42 + 0.18 * noise((h, w), 90, rng) + rim * 0.35
    grain = 0.8 + 0.2 * noise((h, w), 2, rng)
    alpha = np.clip(body * density * grain, 0, 0.85)
    out = np.zeros((h, w, 4), np.uint8)
    out[..., :3] = CORAL
    out[..., 3] = (alpha * 255).astype(np.uint8)
    wash = Image.fromarray(out, "RGBA")
    wash.save(f"{d}/color-wash.png", optimize=True)
    ys, xs = np.nonzero(alpha > 0.2)
    with open(f"{d}/color-wash.json", "w") as f:
        json.dump({"size": [w, h], "bbox": [int(xs.min()), int(ys.min()), int(xs.max()), int(ys.max())], "regions": chosen}, f)
    for name, layers in (("version-color.jpg", [wash, ink_img]), ("version-ink.jpg", [ink_img])):
        base = Image.new("RGB", ink_img.size, PAPER)
        for layer in layers:
            base.paste(layer, (0, 0), layer)
        base.save(f"{d}/{name}", quality=92)
    print(f"{d}: color version from regions {chosen}")


main()
