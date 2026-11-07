# Ink

A Claude Code skill that makes hand-drawn editorial illustrations and animates them like a hand-drawn cartoon.

An image generator draws the subject with a thick felt-tip line and occasional coral watercolor. Scripts split the drawing into layers (ink, watercolor, character poses), and a small runtime animates them at 10 frames per second: characters change pose, elements pop in, beat and float, and the ink boils. A check script verifies the loop, the frame and the motion, and writes a contact sheet to review.

## Install

```sh
git clone git@github.com:SebConejo/ink.git ~/codebase/ink
ln -s ~/codebase/ink ~/.claude/skills/ink
```

Then in Claude Code: `/ink a person waving hello, then jumping for joy`.

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
scripts/generate.mjs  prompt + Gemini generation through Composio
scripts/layers.py     split a drawing into ink and watercolor layers
scripts/poses.py      cut a pose sheet into aligned poses
scripts/build.mjs     scene.json + images -> one standalone HTML page
scripts/runtime.js    the 10 fps player inlined into each page
scripts/check.mjs     rule check + contact sheet in headless Chrome
examples/             three finished animations
evals/evals.json      test prompts and what a good answer contains
```
