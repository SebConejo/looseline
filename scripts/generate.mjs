import { spawnSync } from "node:child_process";
import { writeFileSync } from "node:fs";
import { resolve } from "node:path";

const STYLE =
  "Loose hand-drawn editorial sketch with one thick black felt-tip marker line (#1B1B1A): thick-thin, blunt ends, slightly wobbly and imperfect, few lines, no fine detail. Draw only what is described: no extra people, heads or objects. People are bald adult silhouettes in profile or three-quarter view, nose in the contour, a closed-eye curve, always dressed: one short stroke marks the neckline, one each sleeve end, one the trouser hem if legs show; nothing else on clothes (no ties, buttons, pockets, hair); never a round smiley head. Objects simplified and imperfect, never precise or technical. Plain off-white background (#FAF9F6), lots of empty space. No words or letters, no icons, no shading, no gradient, no frame.";
// Frame sheets need room for one line per panel, so they use a shorter style.
const STYLE_SHORT =
  "Loose hand-drawn editorial sketch, one thick black felt-tip marker line, thick-thin, blunt ends, slightly wobbly, few lines, no fine detail. Draw only what is described. People: bald adults in profile, nose in the contour, closed-eye curve, dressed: one stroke at neckline, sleeve ends and trouser hems, nothing else on clothes; never a round smiley head. Line only: never fill a shape with black. Off-white paper. No words, icons, shading or frame.";
// The default style since 2026-11-08: few loose brush lines, playful
// disproportion, flat off-white cutouts on a flat terracotta background.
const STYLE_LINE =
  "Style: few thick black brush-pen lines, wobbly, rounded ends, like loose string; open shapes, no messy loops. Bodies: black line only, never filled; big hands, tiny head, short legs. Detail follows zoom: a whole body keeps face, hands, feet simple (closed-eye curve, small plain hands) and every arm ends in a hand; finger loops only in hand close-ups. Legs: two separate strokes, nothing between. Objects: flat off-white paper cutouts, no outline, few black lines. Flat terracotta background (#C96F53); no frame, shading, texture, words or clothes. Add no unlisted person, head or animal.";
const WASH = " Coral watercolor (#F5A39B) only where asked: loose, translucent, paper grain.";
const NO_WASH = " No color at all, black ink only.";

const args = process.argv.slice(2);
const opt = (name, fallback) => {
  const i = args.indexOf(name);
  return i > -1 ? args[i + 1] : fallback;
};
const subject = opt("--subject");
const out = opt("--out");
if (!subject || !out) {
  console.error(`usage: node scripts/generate.mjs --subject "..." --out drawing.jpg [--kind single|poses|frames] [--grid 2x2] [--size 1K|2K] [--poses 4] [--wash] [--aspect 1:1|16:9] [--model gemini-3-pro-image-preview] [--style line|marker]

--kind single   one drawing, subject centred, about 55% of the canvas
--kind poses    one pose sheet: the SAME character drawn --poses times in a row on one baseline; describe each pose in --subject
--kind frames   one frame sheet: the SAME drawing in a --grid 2x2 of panels, only the moving part changes; describe each panel in --subject (2K by default)
--dry           print the prompt and its length, generate nothing
--style line    the default: few brush lines, disproportion, off-white cutouts on terracotta
--style marker  the older style: felt-tip marker on off-white paper, optional coral watercolor
--wash          marker style only: allow coral watercolor where the subject asks for it (otherwise black ink only)`);
  process.exit(2);
}
const kind = opt("--kind", "single");
const count = opt("--poses", "4");
const grid = opt("--grid", "2x2");
const [gc, gr] = grid.split("x").map(Number);
const layout = gr === 1 ? `one row of ${gc} equal panels side by side` : `a ${grid} grid of equal panels (left to right, top to bottom)`;
const heads = {
  poses: `Animation pose sheet: the SAME character drawn ${count} times in a row, evenly spaced, same size, same baseline, no overlap between poses. `,
  frames:
    gr === 1
      ? `Animation key drawings: the SAME drawing in ${layout}, wide margins, no borders or numbers. Identical framing; only the moving part changes. `
      : `Animation frame sheet: the SAME drawing in ${layout}, wide margins, no borders or numbers. Identical framing in every panel. The action advances evenly: each panel one small step further than the previous, no two panels alike, no pauses, no jumps. `,
  single: "Subject centred, about 55% of the canvas. ",
};
const head = heads[kind] || heads.single;
const style = opt("--style", "line");
const lineHeads = {
  frames: `Three square panels on white, wide gutters, identical framing; only the moving part changes, slightly. `,
  poses: `One wide terracotta panel: the SAME character drawn ${count} times in a row, same size, same baseline. `,
  single: "One square terracotta panel, subject centred. ",
};
const prompt = style === "line" ? (lineHeads[kind] || lineHeads.single) + STYLE_LINE + " Scene: " + subject : head + subject + " " + (kind === "frames" ? STYLE_SHORT : STYLE) + (args.includes("--wash") ? WASH : NO_WASH);
if (prompt.length > 1000) {
  console.error(`prompt is ${prompt.length} characters; the managed Gemini connection takes 1000 at most. Shorten --subject by ${prompt.length - 1000}.`);
  process.exit(2);
}
if (args.includes("--dry")) {
  console.log(`${prompt.length} characters\n${prompt}`);
  process.exit(0);
}
const body = {
  model: opt("--model", "gemini-3-pro-image-preview"),
  prompt,
  aspect_ratio: opt("--aspect", kind === "poses" ? "16:9" : "1:1"),
  image_size: opt("--size", kind === "frames" ? "2K" : "1K"),
};
const run = spawnSync("composio", ["execute", "GEMINI_GENERATE_IMAGE", "-d", JSON.stringify(body)], { encoding: "utf8", timeout: 480000, maxBuffer: 1 << 26 });
const text = run.stdout || "";
const start = text.indexOf("{");
let result;
try {
  result = JSON.parse(text.slice(start));
} catch {
  console.error("composio did not return JSON:\n" + text.slice(0, 600) + (run.stderr || "").slice(0, 600));
  process.exit(1);
}
const link = result?.data?.image?.s3url;
if (!result.successful || !link) {
  console.error("generation failed: " + JSON.stringify(result.error || result).slice(0, 600));
  process.exit(1);
}
const response = await fetch(link);
if (!response.ok) {
  console.error(`download failed: ${response.status}`);
  process.exit(1);
}
writeFileSync(resolve(out), Buffer.from(await response.arrayBuffer()));
console.log(`wrote ${resolve(out)} (${prompt.length} prompt characters)`);
