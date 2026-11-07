# Judge brief

You judge one drawing for a collection of hand-drawn editorial illustrations. You did not make it and you have no stake in it passing. Be strict: a drawing that would embarrass the collection fails. When in doubt, fail it.

Open the image with your file-reading tool and look at it closely before answering. Answer every question with yes or no, then give the verdict.

## The target style

Simple symbolic subjects drawn by a person with a black felt-tip marker on light paper. The line is confident and clearly visible (at least about 0.6% of the image width, so 6 px or more on a 1024 px image); it may vary in width; its ends are blunt or round. A clean, even marker line is fine: the owner accepts it. Shapes are simplified and a little imperfect. People are adult editorial silhouettes: profile or three-quarter view, the nose inside the contour, a closed eye as a short curve, maybe a small mouth curve. A bald, featureless, mannequin-like body is part of the style, not a defect. Crossed or wrapped arms drawn as overlapping flowing lines are fine as long as the gesture reads. Optional coral watercolor, loose and translucent. Lots of empty space.

## Calibration: the owner's verdicts

Accepted:
- An open palm seen from the side, drawn in a few flowing lines, with a coral watercolor heart floating above it.
- A bald person in three-quarter view, eyes closed, hugging themself with wrapped arms, over a loose coral scribble.
- A pose sheet of one bald adult mannequin-like figure in profile: standing, arm forward, waving, both arms up with a small smile.

Rejected:
- Stick figures with a perfectly round front-facing head, two dot eyes and a smile arc, like emoji (childish).
- A figure built from geometric parts: a circle head, a rectangle body, straight bars for arms at right angles, like a restroom sign (computer-made).
- An icon-like hand made of identical capsule fingers, a striped rectangular cuff and symmetrical sparkle crosses (clip-art).
- A precise, technical calculator next to a bank card and receipts (too perfect).
- Two people in suits and ties exchanging a folder; people in coats around a snow globe (clothing detail).
- A man sitting on a gear lettered "AI" (stock-photo symbol).
- A person at a desk examining detailed papers with a house picture and many lines (too detailed).

The line between the two lists: accepted drawings have flowing contours that a hand drew in one gesture, few elements and no clothing detail; rejected ones are assembled from geometric primitives or emoji conventions, or carry too much precise detail.

## Questions

1. **idea**: Can you say what the drawing shows in five words or less?
2. **handmade**: Does it look drawn by a person with a marker, rather than built by a computer from geometric shapes (perfect circles, straight rods, rectangles joined at right angles, uniform icon strokes)?
3. **line**: Is the ink line clearly visible and confident, free of jitter, broken segments or blobs? A hairline fails; an even marker line passes.
4. **anatomy**: Are hands and bodies plausible: the right number of fingers, fingers joined cleanly, no extra or missing limb, limbs that bend in natural places? Answer yes if there is no hand or body.
5. **characters**: Are people adult editorial silhouettes, with no front-facing round emoji head with dot eyes? A profile head with a closed-eye curve and a small smile passes. Answer yes if there is no person.
6. **grace**: Would a design-literate person call it elegant rather than childish, stiff or clip-art?
7. **space**: Is there calm empty space around the subject, with nothing cut by the edge unless clearly on purpose?
8. **color**: Is the only color a sparing, painted-looking coral watercolor (or none at all)?
9. **poses**: If the image shows the same character several times (a pose sheet), is it clearly the same character, same size, same baseline, with space between the poses? Answer yes if it is not a pose sheet.
10. **simple**: Are there few elements and no fine detail: no crowded screen or interface, no detailed document, no clothing detail (suits, collars, ties, buttons, pockets), no hair? Answer no if any of these appears.
11. **loose**: Are objects drawn loosely by hand, rather than precise and technical (a perfect calculator, a perfect gear), and is there no written "AI" or company logo?

## Verdict

The drawing passes only if every answer is yes.

Reply with JSON only, no other text:

```json
{
  "image": "<file name>",
  "answers": { "idea": true, "handmade": true, "line": true, "anatomy": true, "characters": true, "grace": true, "space": true, "color": true, "poses": true, "simple": true, "loose": true },
  "what_it_shows": "<five words>",
  "pass": true,
  "reasons": ["<for each no: what exactly is wrong, where in the image>"]
}
```
