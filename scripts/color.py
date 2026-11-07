"""Place real coral watercolor patches behind chosen regions of an ink drawing.

usage:
  python3 -I scripts/color.py DIR --list
      writes DIR/regions.png: every closed region of the drawing with a number
  python3 -I scripts/color.py DIR --regions 6,7+8 [--patch wide] [--seed 1] [--close 9]
      writes DIR/color-wash.png (the watercolor layer), DIR/version-color.jpg
      (paper + watercolor + ink) and DIR/version-ink.jpg (paper + ink only)

DIR holds layer-ink.png (from layers.py). Regions joined by + get one patch
together. The watercolor is never painted by code: a real painted patch from
library/_washes (scripts/washes.py) is chosen by shape, scaled a little larger
than the region, tilted and offset, and placed behind the ink. A region is a connected area of paper
enclosed by ink; gaps narrower than --close (in half-size pixels) are closed
first, because hand-drawn contours are often open.
"""
import json
import sys

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

PAPER = (244, 242, 236)
CORAL = (240, 128, 110)


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
    groups = [[int(v) for v in g.split("+")] for g in opt("--regions", "").split(",") if g]
    chosen = [i for g in groups for i in g]
    forced = opt("--patch")
    rng = np.random.default_rng(int(opt("--seed", "1")))
    root = __file__.rsplit("/scripts/", 1)[0]
    import glob
    patches = []
    for f in sorted(glob.glob(f"{root}/library/_washes/patch-*.png")):
        meta = json.load(open(f[:-4] + ".json"))
        patches.append((f, meta))
    if not patches:
        print("no watercolor patches in library/_washes: run scripts/washes.py on a generated swatch sheet first")
        sys.exit(1)
    W, H = ink_img.size
    wash = np.zeros((H, W), np.float32)
    for g in groups:
        ys, xs = np.nonzero(np.isin(lab, g))
        x0, x1, y0, y1 = xs.min() * 2, xs.max() * 2, ys.min() * 2, ys.max() * 2
        bw, bh = x1 - x0, y1 - y0
        aspect = bw / max(1, bh)
        pool = [p for p in patches if p[1].get("kind") not in ("heart", "splash")]
        if forced:
            pool = [p for p in patches if p[1].get("kind") == forced or p[0].endswith(f"patch-{forced.zfill(2)}.png")]
        pool.sort(key=lambda p: abs(np.log(p[1]["aspect"] / aspect)))
        f, meta = pool[min(len(pool) - 1, int(rng.integers(0, 2)))]
        over = 1.12 + rng.random() * 0.12
        tw, th = int(bw * over), int(bh * over)
        patch = Image.open(f).resize((max(8, tw), max(8, th)), Image.LANCZOS).rotate(float((rng.random() - 0.5) * 10), expand=True, resample=Image.BICUBIC)
        pa = np.asarray(patch).astype(np.float32)[..., 3] / 255
        cx = (x0 + x1) / 2 + (rng.random() - 0.5) * 0.12 * bw
        cy = (y0 + y1) / 2 + (rng.random() - 0.5) * 0.12 * bh
        px, py = int(cx - pa.shape[1] / 2), int(cy - pa.shape[0] / 2)
        sx0, sy0 = max(0, -px), max(0, -py)
        dx0, dy0 = max(0, px), max(0, py)
        dx1, dy1 = min(W, px + pa.shape[1]), min(H, py + pa.shape[0])
        if dx1 <= dx0 or dy1 <= dy0:
            continue
        piece = pa[sy0:sy0 + dy1 - dy0, sx0:sx0 + dx1 - dx0]
        region = wash[dy0:dy1, dx0:dx1]
        wash[dy0:dy1, dx0:dx1] = 1 - (1 - region) * (1 - piece)
        print(f"regions {g}: {meta.get('kind')} patch, {tw}x{th}")
    alpha = np.clip(wash, 0, 1)
    h, w = alpha.shape
    out = np.zeros((h, w, 4), np.uint8)
    out[..., :3] = CORAL
    out[..., 3] = (alpha * 255).astype(np.uint8)
    wash = Image.fromarray(out, "RGBA")
    wash.save(f"{d}/color-wash.png", optimize=True)
    ys, xs = np.nonzero(alpha > 0.2)
    with open(f"{d}/color-wash.json", "w") as f:
        json.dump({"size": [w, h], "bbox": [int(xs.min()), int(ys.min()), int(xs.max()), int(ys.max())], "regions": groups}, f)
    for name, layers in (("version-color.jpg", [wash, ink_img]), ("version-ink.jpg", [ink_img])):
        base = Image.new("RGB", ink_img.size, PAPER)
        for layer in layers:
            base.paste(layer, (0, 0), layer)
        base.save(f"{d}/{name}", quality=92)
    print(f"{d}: color version from regions {chosen}")


main()
