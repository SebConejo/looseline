# Ink

A Claude Code skill that makes hand-drawn editorial illustrations and animates them like a hand-drawn cartoon.

Every drawing comes in two versions: a still image and a looping animation. An image generator (Gemini) draws three key drawings of the same scene on one sheet: the rest state, halfway and the full action. Scripts cut and align them, reject a sheet with a black fill or a frame around the drawing, and play the drawings 1, 2, 3, 2 in a loop, 250 ms each, while the ink boils slightly on every frame.

```sh
node scripts/make.mjs --subject "A person in profile sits at a desk with a laptop and a paper coffee cup." \
  --states "hand resting on the cup | the cup lifted halfway | the cup at the mouth, sipping" --out work/coffee
```

This writes `work/coffee/still.png` and `work/coffee/anim.html`. `library/anim/index.html` shows 19 examples with both versions side by side.

For longer stories, the skill also splits a drawing into ink and watercolor layers and cuts pose sheets into character poses, then animates them at 10 frames per second.

## Install

```sh
git clone git@github.com:SebConejo/ink.git ~/codebase/ink
ln -s ~/codebase/ink ~/.claude/skills/ink
```

Then in Claude Code: `/ink an icon of a person opening a door`.

## Requirements

- Composio CLI signed in, with a Gemini connection (image generation)
- Node.js 20+
- Python 3 with Pillow and numpy
- Chrome or Chromium for `scripts/check.mjs`

## Layout

```
SKILL.md              the workflow Claude follows
references/style.md   the style, rejected tries, judge questions
references/motion.md  animation rules and the scene file format
scripts/make.mjs      the default: still + 1-2-3-2 animation in one command
scripts/generate.mjs  prompt + Gemini generation through Composio
scripts/frames.py     cut a sheet of key drawings into aligned frames
scripts/flipbook.mjs  frames -> scene.json played in a given order
scripts/layers.py     split a drawing into ink and watercolor layers
scripts/poses.py      cut a pose sheet into aligned poses
scripts/build.mjs     scene.json + images -> one standalone HTML page
scripts/runtime.js    the 10 fps player inlined into each page
scripts/check.mjs     rule check + contact sheet in headless Chrome
examples/             three finished animations
library/anim/         19 subjects in two versions (still and 1-2-3-2)
evals/evals.json      test prompts and what a good answer contains
```
