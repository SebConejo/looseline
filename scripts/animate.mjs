import { existsSync, readFileSync, writeFileSync } from "node:fs";
import { join, resolve } from "node:path";

const dir = resolve(process.argv[2] || "");
if (!process.argv[2] || !existsSync(join(dir, "layer-ink.png"))) {
  console.error(`usage: node scripts/animate.mjs library/NN-slug

Writes DIR/scene.json, a light animation of a single library drawing:
the watercolor spreads, the drawing arrives with a small bounce and breathes
while its ink boils, painted motifs pop in and float, then everything leaves
and the loop starts again. Build it with scripts/build.mjs. A drawing whose
idea needs a body that changes pose needs a pose sheet instead
(references/motion.md, section 2).`);
  process.exit(2);
}
const meta = (name) => (existsSync(join(dir, `${name}.json`)) ? JSON.parse(readFileSync(join(dir, `${name}.json`), "utf8")) : null);
const staging = meta("staging") || {};
const ink = meta("layer-ink");
const [W, H] = ink.size;
const centre = (b) => [Math.round((b[0] + b[2]) / 2), Math.round((b[1] + b[3]) / 2)];
const layers = [];
const loop = 5400;

const washName = staging.move === "source" ? "layer-wash" : existsSync(join(dir, "color-patch.png")) ? "color-patch" : null;
if (washName && meta(washName)?.bbox) {
  const b = meta(washName).bbox;
  const [cx, cy] = centre(b);
  layers.push({
    id: "wash",
    kind: "wash",
    src: `${washName}.png`,
    origin: [cx, cy],
    reveal: { type: "bloom", cx, cy, radius: Math.round(Math.hypot(b[2] - b[0], b[3] - b[1]) * 0.75), track: [[0, 0], [500, 0], [1500, 1], [4300, 1], [4900, 0], [loop, 0]] },
    track: { scale: [[0, 0.92], [500, 0.92], [1500, 1], [4300, 1], [4900, 0.92], [loop, 0.92]] },
  });
}
const b = ink.bbox;
const foot = [Math.round((b[0] + b[2]) / 2), b[3]];
layers.push({
  id: "drawing",
  kind: "ink",
  src: "layer-ink.png",
  boil: true,
  origin: foot,
  track: {
    opacity: [[0, 0], [250, 1, "linear"], [4700, 1], [5000, 0, "linear"], [loop, 0]],
    y: [[0, 24], [600, 0, "back"], [4700, 0], [5000, 16, "in"], [loop, 24]],
    sy: [[0, 1], [700, 1], [1700, 1.018], [2700, 0.99], [3700, 1.018], [4500, 1], [loop, 1]],
  },
});
if (staging.move !== "source" && meta("color-motifs")?.bbox) {
  const m = meta("color-motifs").bbox;
  const edge = Math.min(m[0], m[1], W - m[2], H - m[3]);
  const tight = edge < 70;
  layers.push({
    id: "motifs",
    kind: "wash",
    src: "color-motifs.png",
    boil: true,
    origin: centre(m),
    float: { amp: tight ? 3 : 10, period: 1400, weight: [[0, 0], [1500, 0], [1900, 1], [4400, 1], [4700, 0]] },
    track: {
      scale: [[0, 0], [1300, 0], [1750, 1, tight ? "out" : "back"], [4400, 1], [4750, 0], [loop, 0]],
      rotate: tight ? [[0, 0]] : [[0, 0], [1750, 0], [2600, 3], [3500, -3], [4400, 0], [loop, 0]],
    },
  });
}
const scene = {
  title: (meta("judge")?.what_it_shows || dir.split("/").pop()).replace(/^\w/, (c) => c.toUpperCase()),
  caption: staging.why || "",
  size: [W, H],
  fps: 10,
  loop,
  still: 2600,
  boil: { freq: 0.018, scale: 5 },
  layers,
};
writeFileSync(join(dir, "scene.json"), JSON.stringify(scene, null, 1));
console.log(`${dir.split("/").pop()}: scene with ${layers.map((l) => l.id).join(", ")}`);
