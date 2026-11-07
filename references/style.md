# Style: hand-drawn ink with watercolor accents

This is the style every drawing must match. The image generator draws; the judge (you, reading the image) checks it against this page before any animation work starts. Every rule here came from a reviewed try: the ones marked "rejected" were refused by the owner.

## 1. The style in one paragraph

Simple symbolic subjects (hands, people, objects, symbols) drawn with a thick black felt-tip marker on warm off-white paper. The line is confident and slightly irregular: it thickens and thins, its ends are blunt, its edge is a little rough. Shapes are simplified and imperfect: rectangles lean, circles are ovals, fingers differ. People are adult editorial silhouettes. A coral watercolor patch appears in some drawings, loose and offset from the ink. Lots of empty space. One idea per drawing.

## 2. Where the hand-made look comes from

At three scales, and only three:

| Scale | What the hand does | Amount |
|---|---|---|
| Shape | corners land off, straight edges bow, circles turn oval, repeated parts differ, the whole object tilts | clearly visible |
| Stroke | the marker thickens and thins with pressure; blunt ends; a slightly rough edge | visible on a close look |
| Micro | bumps or jitter along the path | none |

Rejected: a line made of segments with cut ends (jerky); bumps along a smooth line (jerky); a constant-width line on perfect geometry (looks like a vector icon, not a drawing).

## 3. Line

- Near-black ink, about #1B1B1A.
- Medium-heavy marker: on a 1024 px drawing the line is about 12 to 18 px. Thin lines read as unfinished (rejected).
- Width varies along the stroke, ends are blunt, edges slightly rough.
- One contour is one gesture: a hand is one line that goes up and down each finger, a speech bubble with its tail is one line.

## 4. Contacts

Two parts that touch along a length (pressed fingers, an arm against the body, legs together) share one line. Two nearby lines are either one line or clearly apart with paper between them, never a black smear or a white sliver in between (rejected: the black smear between fingers).

## 5. Shapes

- Reduce every object to its essential, recognisable form.
- Rounded rectangles, ovals, soft curves, open contours where a line is not needed.
- Slight distortions of scale help the meaning (an oversized hand that holds something).
- Flat, two-dimensional. Never isometric or 3D.

## 5b. Simple and imperfect

- **Few elements, no fine detail.** One subject, one or two objects. A document is a few wavy lines, a screen holds two or three marks at most, never a full interface (rejected: the crowded dashboard screen, the detailed papers and house picture under a magnifier).
- **Objects are drawn by hand, never precise.** A calculator, a card or a gear leans, its keys are a few uneven marks, its lines wobble (rejected: a calculator that looked technical and perfect).
- **No written AI.** Artificial intelligence is never the letters "AI": show an abstract spark or a soft knot of lines, never a real company logo (rejected: a gear marked AI, stock-photo look).

## 6. People

- Adult editorial silhouettes in profile or three-quarter view.
- Small head; the nose is part of the contour; a closed eye is a short curve; at most a mouth line.
- One flowing contour; simplified hands; no anatomy, no hair. **Clothes are suggested, never drawn**: no suits, collars, ties, buttons or pockets. A bare silhouette reads as dressed (accepted: the people around the checklist; rejected: suits in the exchange and snow-globe scenes).
- **Never a round smiley head with dot eyes and a smile arc.** It reads as a children's emoji (rejected).
- Gestures carry the meaning and may be exaggerated.

## 7. Color

| Element | Value |
|---|---|
| Paper | #FAF9F6 (the page card uses #F4F2EC) |
| Ink | #1B1B1A |
| Watercolor | coral #F5A39B, with #F8B6AD and #F6C4BA |
| Optional grey flat fill | #DEDAD0, inside a shape, one or two shapes at most |

No other color, no gradient, no shadow, no texture on ink or paper.

## 8. Watercolor

- In about one drawing out of three, never as the only content of the idea.
- Loose: behind the ink, overflowing the contour or offset from it. It never traces the contour.
- Translucent, soft irregular edge, light paper grain, pigment pooling at the rim.
- It covers at most 20% of the canvas.
- **Watercolor is always really painted, never computed.** It comes from the generator: either inside the generated drawing, or as a real painted patch from `library/_washes` placed behind the ink by `scripts/color.py`. A tint computed by code reads as a flat fill, even with noise and grain (rejected 2026-11-07: the piggy bank, guitar and books looked like three flat fills next to the painted door).
- What makes it watercolor: visible brush strokes, uneven pigment, darker pooling at the rim, light streaks and gaps, paper grain, and a shape that overflows the object instead of filling it.
- **Every accepted drawing has two versions**: ink only, and with watercolor. Color is always this watercolor.
- **Coloring is a staging choice, not a fill.** Decide per drawing which of three moves helps the idea, then use one, sometimes two:
  1. **Background**: one large painted patch behind the whole subject gives depth. The subject stays paper on top of it (the runner in the door, the reader on his books).
  2. **Object**: a patch behind the one object that carries the idea (the piggy bank). Every other part of the subject in front of it stays paper (the coins, the person sitting on it).
  3. **Added motif**: painted elements that tell the action, placed around the subject (music notes and a wavy staff around a playing guitar, sparkles around a success, a heart above a gift).
- Ask "what would an illustrator add to make the idea read?" before choosing. A generic patch behind a group or an object that does not point at the idea fails (rejected: the patch behind the network tree, the patch behind the exchanged folder, the sparkles over the payment card). Coloring a small part that carries no meaning (the guitar body, two books of a stack) adds nothing (rejected 2026-11-07).
- The watercolor never crosses the rest of the subject: only the chosen object, the empty background and placed motifs take color.
- **A watercolor element never sits on another watercolor area**: coral on coral disappears (rejected: a coral heart rising over a coral background).

## 9. Composition

- One idea, one subject or a small group.
- The subject fills 45 to 70% of the canvas, near the centre, with calm space around.
- Slight asymmetry. No background scene, no frame, no border.
- No words, except symbols that belong to an object.

## 10. Forbidden

Corporate flat characters, isometric, 3D, photorealism, anime or comic shading, gradients, glass effects, multicolor palettes, large solid fills, heavy shadows, ornament, busy backgrounds, stock-illustration look. Copying a reference drawing: references give the style, never the drawing.

## 11. Judge questions for a generated drawing

The fresh judge agent uses `references/judge.md`, which turns these questions into a strict yes/no grid with calibration examples. Summary:

1. Can you name the idea in five words?
2. Does it look drawn by hand with a felt marker, not like a vector icon?
3. Is the line thick enough, with blunt ends and a varying width?
4. Are hands correct: the right number of fingers, fingers joined cleanly, no extra limb?
5. Are people adult editorial silhouettes, with no round smiley head?
6. Is there calm empty space around the subject?
7. Is coral the only color, used sparingly, and does it look painted?
8. For a pose sheet: is it the same character in every pose, same size, same baseline, with space between the poses?
