"""Add real painted watercolor to an accepted ink drawing.

usage:
  python3 -I scripts/color.py DIR --from-source
      the generated drawing already holds good watercolor: keep it as the color
      version and write the ink-only version
  python3 -I scripts/color.py DIR --list
      writes DIR/regions.png: every closed region of the drawing, numbered
  python3 -I scripts/color.py DIR [--background] [--regions 6,7+8] [--add "staff@700,260,330,-10;note@860,330,90"]
      writes DIR/color-wash.png, DIR/version-color.jpg and DIR/version-ink.jpg

Three ways to color, chosen per drawing (references/style.md, section 8):
  --background   one large painted patch behind the whole subject, for depth
  --regions      a painted patch behind one object (regions joined by + share one)
  --add          painted motifs that tell the action, kind@x,y,width[,degrees];
                 kinds are the "kind" fields in library/_motifs/*.json

The watercolor never crosses the rest of the subject: every part of the drawing
other than the chosen regions stays paper, so people, coins or books in front
read white, while the patch may overflow into the empty background. Motifs are
placed on top of that rule, where you put them.

Nothing here paints: every patch and motif is a real painted swatch from a
generated sheet (scripts/washes.py). A region is a connected area of paper
enclosed by ink, after closing gaps narrower than --close half-size pixels.
"""
import glob
import json
import sys

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

PAPER = (244, 242, 236)
CORAL = (240, 128, 110)
ROOT = __file__.rsplit("/scripts/", 1)[0]


def opt(name, default=None):
    return sys.argv[sys.argv.index(name) + 1] if name in sys.argv else default


def label(free):
    h, w = free.shape
    lab = np.zeros((h, w), np.int32)
    sizes = [0]
    n = 0
    for y0 in range(0, h, 2):
        for x0 in range(0, w, 2):
            if not free[y0, x0] or lab[y0, x0]:
                continue
            n += 1
            stack = [(y0, x0)]
            lab[y0, x0] = n
            count = 0
            while stack:
                y, x = stack.pop()
                count += 1
                for ny, nx in ((y + 1, x), (y - 1, x), (y, x + 1), (y, x - 1)):
                    if 0 <= ny < h and 0 <= nx < w and free[ny, nx] and not lab[ny, nx]:
                        lab[ny, nx] = n
                        stack.append((ny, nx))
            sizes.append(count)
    return lab, sizes


def grow(mask, size):
    img = Image.fromarray((mask > 0).astype(np.uint8) * 255)
    return np.asarray(img.filter(ImageFilter.MaxFilter(size | 1))) > 0


def up(mask, size):
    img = Image.fromarray((mask > 0).astype(np.uint8) * 255).resize(size, Image.BILINEAR)
    return np.asarray(img).astype(np.float32) / 255


def load(kind_dir):
    out = []
    for f in sorted(glob.glob(f"{ROOT}/library/{kind_dir}/patch-*.png")):
        out.append((f, json.load(open(f[:-4] + ".json"))))
    return out


def stamp(canvas, path, cx, cy, tw, th, degrees):
    patch = Image.open(path).resize((max(8, int(tw)), max(8, int(th))), Image.LANCZOS)
    patch = patch.rotate(degrees, expand=True, resample=Image.BICUBIC)
    pa = np.asarray(patch).astype(np.float32)[..., 3] / 255
    H, W = canvas.shape
    px, py = int(cx - pa.shape[1] / 2), int(cy - pa.shape[0] / 2)
    sx, sy = max(0, -px), max(0, -py)
    x0, y0, x1, y1 = max(0, px), max(0, py), min(W, px + pa.shape[1]), min(H, py + pa.shape[0])
    if x1 > x0 and y1 > y0:
        piece = pa[sy:sy + y1 - y0, sx:sx + x1 - x0]
        canvas[y0:y1, x0:x1] = 1 - (1 - canvas[y0:y1, x0:x1]) * (1 - piece)


def pick(pool, aspect, rng):
    pool = sorted(pool, key=lambda p: abs(np.log(p[1]["aspect"] / aspect)))
    return pool[min(len(pool) - 1, int(rng.integers(0, 2)))]


def main():
    if len(sys.argv) < 3:
        print(__doc__)
        sys.exit(2)
    d = sys.argv[1].rstrip("/")
    ink_img = Image.open(f"{d}/layer-ink.png")
    W, H = ink_img.size
    ink = np.asarray(ink_img).astype(np.float32)[..., 3] / 255
    close = int(opt("--close", "9"))
    small = ink[::2, ::2]
    closed = grow(small > 0.25, close) if close > 1 else small > 0.25
    lab, sizes = label(~closed)
    border = set(np.unique(np.concatenate([lab[0], lab[-1], lab[:, 0], lab[:, -1]]))) - {0}
    keep = [i for i in range(1, len(sizes)) if i not in border and sizes[i] > 150]

    if "--from-source" in sys.argv:
        src = Image.open(f"{d}/source.jpg").convert("RGB")
        src.save(f"{d}/version-color.jpg", quality=92)
        base = Image.new("RGB", (W, H), PAPER)
        base.paste(ink_img, (0, 0), ink_img)
        base.save(f"{d}/version-ink.jpg", quality=92)
        print(f"{d}: color version is the generated drawing itself")
        return

    if "--list" in sys.argv:
        base = Image.new("RGB", (W, H), PAPER)
        base.paste(ink_img, (0, 0), ink_img)
        tint = np.zeros(lab.shape + (4,), np.uint8)
        rng = np.random.default_rng(3)
        for i in keep:
            tint[lab == i] = (*rng.integers(80, 230, 3), 90)
        over = Image.fromarray(tint, "RGBA").resize((W, H), Image.NEAREST)
        base.paste(over, (0, 0), over)
        draw = ImageDraw.Draw(base)
        try:
            font = ImageFont.truetype("/System/Library/Fonts/Supplemental/Arial Bold.ttf", 26)
        except Exception:
            font = ImageFont.load_default()
        for i in keep:
            ys, xs = np.nonzero(lab == i)
            draw.text((int(np.median(xs)) * 2 - 10, int(np.median(ys)) * 2 - 14), str(i), fill=(200, 0, 0), font=font)
        base.save(f"{d}/regions.png")
        print(f"{d}/regions.png: {len(keep)} regions")
        return

    rng = np.random.default_rng(int(opt("--seed", "1")))
    washes = [p for p in load("_washes") if p[1].get("kind") not in ("heart", "splash")]
    motifs = load("_motifs")
    subject = ~np.isin(lab, list(border))
    alpha = np.zeros((H, W), np.float32)
    allowed = np.zeros(lab.shape, bool)
    notes = []

    if "--background" in sys.argv:
        ys, xs = np.nonzero(subject)
        x0, x1, y0, y1 = xs.min() * 2, xs.max() * 2, ys.min() * 2, ys.max() * 2
        bw, bh = (x1 - x0) * 0.95, (y1 - y0) * 0.8
        f, meta = pick(washes, bw / bh, rng)
        cx = (x0 + x1) / 2 + (rng.random() - 0.5) * 0.1 * bw
        cy = (y0 + y1) / 2 - 0.04 * bh
        stamp(alpha, f, cx, cy, bw, bh, float((rng.random() - 0.5) * 8))
        notes.append(f"background: {meta['kind']} patch")

    groups = [[int(v) for v in g.split("+")] for g in (opt("--regions") or "").split(",") if g]
    for g in groups:
        region = np.isin(lab, g)
        allowed |= grow(region, close)
        ys, xs = np.nonzero(region)
        x0, x1, y0, y1 = xs.min() * 2, xs.max() * 2, ys.min() * 2, ys.max() * 2
        bw, bh = x1 - x0, y1 - y0
        f, meta = pick(washes, bw / max(1, bh), rng)
        over = 1.12 + rng.random() * 0.12
        cx = (x0 + x1) / 2 + (rng.random() - 0.5) * 0.1 * bw
        cy = (y0 + y1) / 2 + (rng.random() - 0.5) * 0.1 * bh
        stamp(alpha, f, cx, cy, bw * over, bh * over, float((rng.random() - 0.5) * 10))
        notes.append(f"regions {g}: {meta['kind']} patch")

    knock = up(subject & ~allowed, (W, H))
    alpha *= 1 - knock

    for spec in [s for s in (opt("--add") or "").split(";") if s.strip()]:
        kind, rest = spec.strip().split("@")
        vals = [float(v) for v in rest.split(",")]
        x, y, w = vals[:3]
        deg = vals[3] if len(vals) > 3 else 0
        match = [p for p in motifs if p[1].get("kind") == kind]
        if not match:
            print(f"no motif of kind {kind}; kinds: {sorted({p[1].get('kind') for p in motifs})}")
            sys.exit(1)
        f, meta = match[0]
        stamp(alpha, f, x, y, w, w / meta["aspect"], deg)
        notes.append(f"motif {kind} at {int(x)},{int(y)}")

    alpha = np.clip(alpha, 0, 1)
    out = np.zeros((H, W, 4), np.uint8)
    out[..., :3] = CORAL
    out[..., 3] = (alpha * 255).astype(np.uint8)
    wash = Image.fromarray(out, "RGBA")
    wash.save(f"{d}/color-wash.png", optimize=True)
    ys, xs = np.nonzero(alpha > 0.2)
    bbox = [int(xs.min()), int(ys.min()), int(xs.max()), int(ys.max())] if len(xs) else None
    with open(f"{d}/color-wash.json", "w") as f:
        json.dump({"size": [W, H], "bbox": bbox, "made_with": sys.argv[2:]}, f)
    for name, layers in (("version-color.jpg", [wash, ink_img]), ("version-ink.jpg", [ink_img])):
        base = Image.new("RGB", (W, H), PAPER)
        for layer in layers:
            base.paste(layer, (0, 0), layer)
        base.save(f"{d}/{name}", quality=92)
    print(f"{d}: " + "; ".join(notes))


main()
