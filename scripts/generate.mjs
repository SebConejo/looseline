import { spawnSync } from "node:child_process";
import { writeFileSync } from "node:fs";
import { resolve } from "node:path";

const STYLE =
  "Minimal hand-drawn editorial illustration. One thick black felt-tip marker line (#1B1B1A): confident, thick-thin stroke, blunt ends, slightly rough edge, open contours, simplified symbolic shapes. People are adult editorial silhouettes in profile or three-quarter view, small head, nose in the contour, closed eye as a short curve; never a round smiley head or dot eyes. Plain warm off-white background (#FAF9F6), lots of empty space. No text, no shading, no gradient, no frame, no shadow.";
const WASH = " Coral watercolor (#F5A39B) only where asked: loose, translucent, paper grain, not following the contour.";
const NO_WASH = " No color at all, black ink only.";

const args = process.argv.slice(2);
const opt = (name, fallback) => {
  const i = args.indexOf(name);
  return i > -1 ? args[i + 1] : fallback;
};
const subject = opt("--subject");
const out = opt("--out");
if (!subject || !out) {
  console.error(`usage: node scripts/generate.mjs --subject "..." --out drawing.jpg [--kind single|poses] [--poses 4] [--wash] [--aspect 1:1|16:9] [--model gemini-3-pro-image-preview]

--kind single   one drawing, subject centred, about 55% of the canvas
--kind poses    one pose sheet: the SAME character drawn --poses times in a row on one baseline; describe each pose in --subject
--dry           print the prompt and its length, generate nothing
--wash          allow coral watercolor where the subject asks for it (otherwise black ink only)`);
  process.exit(2);
}
const kind = opt("--kind", "single");
const count = opt("--poses", "4");
const head =
  kind === "poses"
    ? `Animation pose sheet: the SAME character drawn ${count} times in a row, evenly spaced, same size, same baseline, no overlap between poses. `
    : "Subject centred, about 55% of the canvas. ";
const prompt = head + subject + " " + STYLE + (args.includes("--wash") ? WASH : NO_WASH);
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
