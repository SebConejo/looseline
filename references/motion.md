# Motion

How a drawing becomes an animation, and the scene file that describes it.

## 1. What a good animation is

**Things move, change and get added.** An arm rises, a hand waves, a character jumps, a heart grows out of a palm, a watercolor spreads. A drawing that only traces itself or fades in is not an animation (rejected twice).

- **A small story** of 4 to 7 seconds, then a loop: rest, action, reveal, hold, return to rest.
- **10 frames per second**, fixed. Movement steps from frame to frame, like hand-drawn animation.
- **Boil**: the ink is redrawn slightly differently each frame (`"boil": true` on ink layers). This gives life even when nothing moves.
- **Pose to pose**: a character changes pose by swapping drawings (poses from one pose sheet), not by stretching one drawing.
- **Anticipation and landing**: before a jump, squash for one or two frames (`sy` 0.95, `sx` 1.04); squash again on landing.
- **Pops**: an added element scales from 0 with a small overshoot (`"back"` ease) in 300 to 450 ms.
- **Beats**: a part scales to 1.12 and back in about 340 ms; at most 4 per loop.
- **Holds**: the full state holds at least 1.2 s so the idea can be read.
- **Loop**: the state at `loop` ms equals the state at 0 ms. The check script enforces it.
- **Reduced motion**: the page shows one still frame at `still` ms.

## 2. Where moving parts come from

The generator draws everything. Moving parts must be separate images:

| Need | How to get it |
|---|---|
| ink and watercolor that move apart (a heart that leaves a hand) | one drawing, then `scripts/layers.py` splits the ink and the coral wash into two layers |
| a character that changes pose | one pose sheet (`generate.mjs --kind poses`), then `scripts/poses.py` cuts and aligns the poses on the feet |
| an extra element (a heart, a star, a watercolor blob) | reuse a layer from another drawing, or generate it alone on an empty background |

Gemini through Composio cannot edit an existing image. The same character in several poses must therefore come from **one** pose sheet: separate generations give different characters.

## 3. Scene file

`scene.json` sits next to its images. `node scripts/build.mjs scene.json --out page.html` inlines everything into one standalone page.

```json
{
  "title": "Hello, then joy",
  "caption": "One sentence that says what happens.",
  "size": [520, 760],
  "fps": 10,
  "loop": 6400,
  "still": 3800,
  "boil": { "freq": 0.022, "scale": 4 },
  "layers": [
    {
      "id": "body",
      "kind": "ink",
      "poses": ["pose1.png", "pose2.png", "pose3.png", "pose4.png"],
      "boil": true,
      "origin": [260, 720],
      "pose": [[0, 1], [900, 3], [1200, 2], [2800, 4], [5000, 1]],
      "track": {
        "y": [[0, 0], [2800, 0], [3050, -70, "out"], [3300, 0, "in"], [6400, 0]]
      }
    }
  ]
}
```

Layers paint in order, the first at the back.

| Layer field | Meaning |
|---|---|
| `id` | name used in check messages |
| `kind` | `ink` or `wash` (the check counts washes) |
| `src` / `poses` | one PNG, or several PNGs swapped by `pose` |
| `x`, `y`, `w`, `h` | where the image sits in the scene (default: the whole canvas) |
| `origin` | the point that scales and rotates in place, in scene units: feet for a character, centre for a heart |
| `boil` | redraw the ink slightly each frame |
| `pose` | `[time, pose number]` keys, 1-based; a pose holds until the next key |
| `track` | animated values: `x`, `y` (offsets), `scale`, `sx`, `sy` (multiplied with `scale`), `rotate` (degrees), `opacity` |
| `float` | `{ "amp": 6, "period": 1200, "phase": 0, "weight": keys }` adds a gentle up-down drift |
| `reveal` | `{ "type": "wipe", "dir": "down" }` or `{ "type": "bloom", "cx", "cy", "radius" }` with a `track` from 0 to 1; use it for watercolor that spreads, not as the whole animation |
| `offstage` | the layer enters from outside the canvas on purpose; the frame check skips it |

A key is `[time ms, value, ease]`. The ease shapes the segment that ends at that key: `linear`, `in`, `out`, `inOut` (default), `back` (overshoot, for pops) or `step` (hold the previous value, then jump).

Each image may have a `.json` beside it (written by `layers.py` and `poses.py`) with the bounding box of its visible pixels. The build reads it so the check can tell when a part leaves the canvas.

## 4. Page modes

The built page takes these query strings:

- `?t=2400` shows one frozen frame.
- `?sheet=0,800,1600` shows a row of frozen frames (used by `check.mjs`).
- `?check` writes the check report into the page.
