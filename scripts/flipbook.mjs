import { readFileSync, readdirSync, writeFileSync } from "node:fs";
import { join } from "node:path";

const args = process.argv.slice(2);
const opt = (name, fallback) => {
  const i = args.indexOf(name);
  return i > -1 ? args[i + 1] : fallback;
};
const dir = args[0];
const fps = Number(opt("--fps", 12));
if (!dir) {
  console.error(`usage: node scripts/flipbook.mjs DIR [--fps 12] [--seq "1:600,2:200"] [--title "..."] [--prefix frame]

Writes DIR/scene.json that plays DIR/frame1.png, frame2.png, ... (scripts/frames.py)
then loops. By default every frame shows for one tick at --fps (12 frames = one
second). --seq gives an explicit order and milliseconds instead. The line boils at
10 fps on top, so a held frame still looks redrawn by hand. Build it with
node scripts/build.mjs DIR/scene.json.`);
  process.exit(2);
}
const prefix = opt("--prefix", "frame");
const files = readdirSync(dir)
  .filter((f) => new RegExp(`^${prefix}\\d+\\.png$`).test(f))
  .sort((a, b) => parseInt(a.slice(prefix.length)) - parseInt(b.slice(prefix.length)));
const meta = JSON.parse(readFileSync(join(dir, files[0].replace(".png", ".json")), "utf8"));
const [W, H] = meta.size;
const seq = opt("--seq") || files.map((_, i) => `${i + 1}:${1000 / fps}`).join(",");
let t = 0;
const pose = [];
for (const step of seq.split(",")) {
  const [frame, ms] = step.split(":").map(Number);
  if (!files[frame - 1]) throw new Error(`no ${prefix}${frame}.png in ${dir}`);
  pose.push([Math.floor(t), frame]);
  t += ms;
}
t = Math.round(t);
pose.push([t, pose[0][1]]);
const scene = {
  title: opt("--title", ""),
  size: [W, H],
  fps,
  loop: t,
  still: 0,
  boil: { freq: 0.02, scale: 3 },
  layers: [{ id: "frames", kind: "ink", poses: files, boil: true, origin: [W / 2, H / 2], pose, track: {} }],
};
writeFileSync(join(dir, "scene.json"), JSON.stringify(scene, null, 2));
console.log(`${dir}/scene.json: ${pose.length - 1} steps, loop ${t} ms`);
