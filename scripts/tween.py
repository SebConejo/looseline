"""Draw in-between frames between key frames by following the line motion.

usage: python3 -I scripts/tween.py DIR [--key key] [--out frame] [--between 2] [--loop]

DIR/key1.png, key2.png, ... are aligned key frames (scripts/frames.py). For each
pair of neighbours, the dense optical flow between their ink is measured, both
keys are pushed toward each other along it, and the two are blended. The blend
is sharpened back into a solid marker line, so an in-between reads as a drawing,
not a double exposure. Writes DIR/frame1.png ... with --between frames inside
each pair; --loop also tweens from the last key back to the first.
"""
import glob
import json
import os
import sys

import cv2
import numpy as np
from PIL import Image


def opt(name, default):
    return sys.argv[sys.argv.index(name) + 1] if name in sys.argv else default


def load(path):
    a = np.asarray(Image.open(path).convert("RGBA")).astype(np.float32) / 255
    return a


def flow(a, b):
    """Flow field that maps pixels of a to b, measured on blurred ink."""
    def prep(x):
        g = (x[..., 3] * 255).astype(np.uint8)
        return cv2.GaussianBlur(g, (0, 0), 6)
    dis = cv2.DISOpticalFlow_create(cv2.DISOPTICAL_FLOW_PRESET_ULTRAFAST)
    dis.setFinestScale(1)
    dis.setPatchSize(16)
    dis.setPatchStride(4)
    return dis.calc(prep(a), prep(b), None)


def warp(img, fl, t):
    """Sample img at p - t * flow(p): pushes its content t of the way along the flow."""
    h, w = img.shape[:2]
    gx, gy = np.meshgrid(np.arange(w, dtype=np.float32), np.arange(h, dtype=np.float32))
    mx, my = gx - t * fl[..., 0], gy - t * fl[..., 1]
    return cv2.remap(img, mx, my, cv2.INTER_LINEAR, borderMode=cv2.BORDER_CONSTANT, borderValue=0)


def between(a, b, t):
    fab = flow(a, b)
    fba = flow(b, a)
    wa = warp(a, fba, t)        # a moved forward: sample a backward along b->a
    wb = warp(b, fab, 1 - t)    # b moved backward
    out = (1 - t) * wa + t * wb
    al = out[..., 3]
    # sharpen the blended alpha back into one solid line
    solid = np.clip((al - 0.22) / 0.4, 0, 1)
    rgb = np.where(al[..., None] > 1e-4, out[..., :3] / np.maximum(al[..., None], 1e-4), 0)
    return np.dstack([np.clip(rgb, 0, 1), solid])


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(2)
    d = sys.argv[1].rstrip("/")
    key = opt("--key", "key")
    out = opt("--out", "frame")
    n = int(opt("--between", "2"))
    keys = sorted(glob.glob(f"{d}/{key}[0-9]*.png"), key=lambda f: int(os.path.basename(f)[len(key):-4]))
    imgs = [load(f) for f in keys]
    pairs = list(zip(imgs, imgs[1:])) + ([(imgs[-1], imgs[0])] if "--loop" in sys.argv else [])
    frames = []
    for a, b in pairs:
        frames.append(a)
        for k in range(1, n + 1):
            frames.append(between(a, b, k / (n + 1)))
    if "--loop" not in sys.argv:
        frames.append(imgs[-1])
    for f in glob.glob(f"{d}/{out}[0-9]*.png") + glob.glob(f"{d}/{out}[0-9]*.json"):
        os.remove(f)
    for i, f in enumerate(frames, 1):
        img = Image.fromarray((np.clip(f, 0, 1) * 255).astype(np.uint8), "RGBA")
        path = f"{d}/{out}{i}.png"
        img.save(path, optimize=True)
        ys, xs = np.nonzero(np.asarray(img)[..., 3] > 64)
        with open(path[:-4] + ".json", "w") as fh:
            json.dump({"size": list(img.size), "bbox": [int(xs.min()), int(ys.min()), int(xs.max()), int(ys.max())]}, fh)
    print(f"{len(keys)} keys -> {len(frames)} frames")


main()
