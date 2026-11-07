---
name: ink
description: Make hand-drawn editorial illustrations (thick black felt-tip line, simplified symbolic shapes, adult editorial characters, occasional coral watercolor) and animate them for real at 10 fps (characters change pose, wave and jump, elements pop in, beat and float, the ink boils). Use whenever someone wants a hand-drawn, sketchy, "Anthropic-style" or "Icons8 Ouch-style" illustration, a spot illustration for a website, a doodle-style explainer, or an animated hand-drawn drawing, even if they never say "ink". Produces a standalone HTML page per animation.
license: MIT
compatibility: Needs the Composio CLI signed in with a Gemini connection (image generation), Node.js 20+, Python 3 with Pillow and numpy, and Chrome or Chromium for the checks.
---

# Ink

This skill makes drawings that look drawn by hand with a felt marker, then animates them like a hand-drawn cartoon: the character really moves, elements get added, and the ink is redrawn slightly each frame.

## The one rule that matters

**The generator draws, the code animates and checks.** Never draw subjects by writing SVG coordinates: hands and people drawn that way come out stiff, like toilet-door pictograms or emoji (tried five times, rejected every time). The image generator draws every subject. The code splits the drawing into layers, moves them, and verifies the result.

## Workflow

1. **One idea, one small story.** Write in one sentence what the drawing says, then the story in beats with times: rest, action, reveal, hold, return. Real motion is required: something changes pose, moves or gets added. A drawing that only traces itself or fades in is not an animation.
2. **Decide the moving parts** (`references/motion.md`, section 2):
   - a character that changes pose needs **one pose sheet** with every pose;
   - ink and watercolor that move apart come from one drawing split into two layers;
   - an added element (a heart, a blob) is a layer reused from another drawing or generated alone.
3. **Generate.** `node scripts/generate.mjs --subject "..." --out work/drawing.jpg` for one drawing, `--kind poses --poses 4` for a pose sheet, `--wash` when the idea uses coral watercolor. The style block from `references/style.md` is added for you; the whole prompt must stay under 1000 characters (`--dry` prints it). Describe what to draw, never which reference to copy.
4. **Judge the drawing before anything else, with a fresh judge.** Never judge your own drawing yourself: start a separate agent that has none of this conversation, give it `references/judge.md` and the image path, and ask for the JSON verdict only. Any `false` answer: generate again, feeding the judge's reasons into the new prompt. Never animate a drawing that fails. When several drawings are needed, judge them in parallel.
5. **Make layers.** `python3 -I scripts/layers.py work/drawing.jpg work/name` writes `name-ink.png` and `name-wash.png`. `python3 -I scripts/poses.py work/sheet.jpg work/pose` writes `pose1.png` and the next ones, aligned on the feet. Check that the number of poses found matches the sheet.
5b. **Make the two versions of an accepted drawing.** Every accepted drawing exists without color (ink only) and with color. Color is always the coral watercolor, really painted: never let code compute a tint, it reads as a flat fill. The painted patches live in `library/_washes` (cut from a generated swatch sheet by `scripts/washes.py`). If the generation already holds watercolor, that is the color version. Otherwise `python3 -I scripts/color.py DIR --list` numbers the closed regions in `DIR/regions.png`; pick the regions that carry the idea (the piggy bank, the guitar body, two books of a stack), then `python3 -I scripts/color.py DIR --regions 6,7+8` places a real painted patch behind each region (or group joined by +) and writes `version-ink.jpg`, `version-color.jpg` and the `color-wash.png` layer. Leave people uncolored unless they are the idea.
6. **Write the scene.** `scene.json` next to the images (`references/motion.md`, section 3). Start from the closest example. Put origins where things really pivot: the feet for a character, the centre of a heart.
7. **Build and check.** `node scripts/build.mjs work/scene.json --out work/name.html`, then `node scripts/check.mjs work/name.html --times 0,600,...`. The check must print `0 problems`. Read the contact sheet PNG it writes: does each frame read, does the story show, does anything overlap badly (a coral element on a coral area, a heart on a face)? Fix and repeat.
8. **Deliver** the HTML page. To preview it, never open it in the person's default browser, which may be in use; ask, or use another browser.

## Library

`library/catalog.json` lists the subjects; `node scripts/library.mjs --only 1-10` generates and splits them into `library/NN-slug/`. Each accepted folder holds `source.jpg`, `layer-ink.png`, the watercolor layer, `version-ink.jpg`, `version-color.jpg` and `judge.json`. `--retry N --note "judge reasons"` regenerates a refused one. Reuse a library drawing before generating a new one.

## Examples

Each folder holds the source image, the layers, `scene.json` and the built page. Open the closest one before writing a scene.

- `examples/wave/`: a pose sheet of one adult character cut into 4 poses. He waves, squashes, jumps for joy, a heart pops above him and a watercolor spreads behind him. The reference for character motion.
- `examples/hand-heart/`: one drawing split into ink and wash. The hand rises from below, the heart grows out of the palm, floats and beats, then goes back.
- `examples/hugging/`: a person hugging themself. The ink appears, the watercolor spreads, the person breathes and sways.

## References

- `references/style.md`: the style, what was rejected, and the judge questions. Read it before generating.
- `references/judge.md`: the brief given to the fresh judge agent, calibrated on the owner's own verdicts.
- `references/motion.md`: what a good animation is, where moving parts come from, the scene file and the page modes.

## Limits

- Motion is pose to pose. A smooth movement of one limb needs more poses in the sheet; a free bending of an arm is not possible from one drawing.
- The generator sometimes draws wrong hands or changes the character between poses. The judge step catches it; generating again usually fixes it.
- The layer split assumes black ink and warm coral on light paper. Other colors need new thresholds in `layers.py`.
