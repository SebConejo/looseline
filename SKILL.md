---
name: looseline
description: Make hand-drawn editorial illustrations and icons in a loose brush-line style (few thick black lines, playful disproportion, giant hands, tiny heads, flat off-white paper cutouts on a terracotta background), each delivered in two versions, a still image and a looping animation of three key drawings played 1, 2, 3, 2. Use whenever someone wants an illustration, an icon, a spot illustration for a website, a hand-drawn, sketchy or doodle-style drawing, an explainer drawing, or an animated drawing, even if they never say "looseline". Produces still.png and a standalone HTML page per drawing.
license: MIT
compatibility: Needs the Composio CLI signed in with a Gemini connection (image generation), Node.js 20+, Python 3 with Pillow and numpy, and Chrome or Chromium for the checks.
---

# Ink

This skill makes drawings that look drawn by hand with a felt marker, then animates them like a hand-drawn cartoon: the character really moves, elements get added, and the ink is redrawn slightly each frame.

## The one rule that matters

**The generator draws, the code animates and checks.** Never draw subjects by writing SVG coordinates: hands and people drawn that way come out stiff, like toilet-door pictograms or emoji (tried five times, rejected every time). The image generator draws every subject. The code splits the drawing into layers, moves them, and verifies the result.

## Workflow

0. **Default: two versions of every drawing, the normal one and the animated one, in the line style.** Read `references/line-style.md` first. Unless the person asks for something else, describe the scene and three situations of the same action, then run:

   ```
   node scripts/make.mjs --subject "A giant black-line hand holds out a small off-white gift box toward the right; a tiny calm head on the left." \
     --states "the hand close to the face | the hand halfway out | the arm fully stretched out" --out work/gift
   ```

   It generates the three key drawings on one sheet, cuts the terracotta panels and aligns them, rejects a sheet with a frame around a panel (up to 3 tries), and writes `still.png` (the normal version: drawing 1) and `anim.html` (the animated version). The animation plays the drawings **1, 2, 3, 2** and loops, 250 ms each: the motion goes and comes back, so the loop never jumps. Situation 1 is the rest state, 2 is exactly halfway, 3 is the full action; keep the motion small. Write only what must be drawn: a subject of hands or objects says "no head, face or person", or the generator adds one. Read the three frames before delivering (`references/line-style.md`, last section) and generate again when one fails. `library/anim/` holds 20 examples (`index.html` shows both versions side by side, `jobs.json` the subjects and situations, `all.mjs NAME` regenerates one).

   `--style marker` gives the older style: felt-tip marker on off-white paper with optional coral watercolor (`references/style.md`).

   The steps below are for the marker style and anything more: watercolor staging, longer stories, pose sheets.

1. **One idea, one small story.**2. **Decide the moving parts** (`references/motion.md`, section 2):
   - a character that changes pose needs **one pose sheet** with every pose;
   - ink and watercolor that move apart come from one drawing split into two layers;
   - an added element (a heart, a blob) is a layer reused from another drawing or generated alone.
3. **Generate.** `node scripts/generate.mjs --subject "..." --out work/drawing.jpg` for one drawing, `--kind poses --poses 4` for a pose sheet, `--wash` when the idea uses coral watercolor. The style block from `references/style.md` is added for you; the whole prompt must stay under 1000 characters (`--dry` prints it). Describe what to draw, never which reference to copy.
4. **Judge the drawing before anything else, with a fresh judge.** Never judge your own drawing yourself: start a separate agent that has none of this conversation, give it `references/judge.md` and the image path, and ask for the JSON verdict only. Any `false` answer: generate again, feeding the judge's reasons into the new prompt. Never animate a drawing that fails. When several drawings are needed, judge them in parallel.
5. **Make layers.** `python3 -I scripts/layers.py work/drawing.jpg work/name` writes `name-ink.png` and `name-wash.png`. `python3 -I scripts/poses.py work/sheet.jpg work/pose` writes `pose1.png` and the next ones, aligned on the feet. Check that the number of poses found matches the sheet.
5b. **Make the two versions of an accepted drawing.** Every accepted drawing exists without color (ink only) and with color. Color is always the coral watercolor, really painted: never let code compute a tint, it reads as a flat fill. If the generation already holds watercolor, that is the color version. Otherwise choose the staging move first (`references/style.md`, section 8): a background patch for depth, the one object that carries the idea, or painted motifs that tell the action. Then:
   - `python3 -I scripts/color.py DIR --background` puts a large painted patch behind the subject;
   - `python3 -I scripts/color.py DIR --list` numbers the closed regions in `DIR/regions.png`, and `--regions 6` puts a patch behind that object;
   - `--add "staff@760,250,330,-8;note@600,200,70"` places painted motifs (kind@x,y,width,degrees; kinds in `library/_motifs`).
   The rest of the subject always stays paper. Read `version-color.jpg` and ask whether the color helps the idea; if not, choose another move.
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

- `references/line-style.md`: the default line style, its rules and what was rejected. Read it before generating.
- `references/style.md`: the older marker style, what was rejected, and the judge questions.
- `references/judge.md`: the brief given to the fresh judge agent, calibrated on the owner's own verdicts.
- `references/motion.md`: what a good animation is, where moving parts come from, the scene file and the page modes.

## Limits

- Motion is pose to pose. A smooth movement of one limb needs more poses in the sheet; a free bending of an arm is not possible from one drawing.
- The generator sometimes draws wrong hands or changes the character between poses. The judge step catches it; generating again usually fixes it.
- The layer split assumes black ink and warm coral on light paper. Other colors need new thresholds in `layers.py`.
