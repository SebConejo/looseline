# Line style (the default)

Few loose black brush lines, playful disproportion, flat off-white paper cutouts on a flat terracotta background. `scripts/generate.mjs --style line` (the default) adds these rules to every prompt. Each rule below comes from a verdict on real drawings.

## The look

- **Few lines, like loose string.** Thick black brush-pen line, wobbly, rounded ends. Shapes may stay open. "One line" is a spirit, not a law: several clean strokes beat one line tied in messy loops.
- **Disproportion on purpose.** Big hands, tiny head, short legs. In a hand close-up, fingers are loops and one finger can be bigger. An eye or a mouth can stand for the whole head when it carries the idea.
- **Flat cutouts.** Objects are flat off-white shapes (#F4F1EA), slightly irregular, no outline, with a few black lines only when the object would not read without them (a payment terminal gets a screen line and key dots).
- **Flat terracotta background** (#C96F53), filling the square. No frame, no border line, no shading, no texture, no words.

## People

- **Body parts are the black line only**, never filled white or black. A white hand reads as an object and breaks the set (rejected: the eye shaded by a white hand).
- **Detail follows the zoom.** A whole body keeps the face, hands and feet simple; detailed hands or feet only when the drawing is a close-up of them.
- **Every arm ends in a hand.** An arm that stops short reads as a stump (rejected: the runner without hands).
- **Faces nearly empty**: a calm closed-eye curve at most. No mouth, nose or eyebrows: a drawn profile with mouth and nose read as angry (rejected: the first coffee).
- **Nothing between the legs.** The legs leave the hips as two smooth separate strokes; a loop or knot there reads as genitals (rejected: the suitcase runner).
- **No clothes.** The line style does not dress people; the simple body with no detail reads fine.

## Subjects

- **Add no one.** The generator likes to add a small head, a bird or a second character. Say "no head, face or person" in any subject made of hands or objects only (rejected: a person above the envelope, a head next to the checklist, a person behind the sneaker).
- **Small motion.** Only the moving part changes, slightly, between the three drawings; everything else stays still (references: the book whose page turns, the arm holding out the gift).
- **Keep places fixed.** Name where things stand ("on the right, in every panel") when a character could swap sides (rejected: the door where the person jumped to the other side).

## After generation

Read the three frames before delivering. Look for an added person or animal, a filled body, a crotch loop, a scenery that changes between frames, and an object whose fill changes between frames (the snow globe white then terracotta flickers).
