// One drawing, two versions: the still drawing and its animation.
//
// The animation is three key drawings of the same scene played 1, 2, 3, 2 and
// looped, so the motion goes and comes back with no jump (a cup: hand on the
// cup, cup halfway, cup at the mouth, halfway again).
import { spawn } from "node:child_process";
import { existsSync, mkdirSync, renameSync } from "node:fs";
import { join } from "node:path";

const args = process.argv.slice(2);
const opt = (name, fallback) => {
  const i = args.indexOf(name);
  return i > -1 ? args[i + 1] : fallback;
};
const scene = opt("--subject");
const states = opt("--states");
const out = opt("--out");
if (!scene || !states || !out) {
  console.error(`usage: node scripts/make.mjs --subject "scene" --states "start | middle | end" --out DIR [--wash] [--ms 250] [--tries 3]

--subject   the scene, what stays the same in the three drawings
--states    the three situations, separated by |: 1 the rest state, 2 halfway,
            3 the full action. The animation plays 1, 2, 3, 2 and loops.
--ms        how long each drawing shows (default 250, so one cycle is one second)

Writes DIR/sheet.jpg (the three drawings from the generator), DIR/frame1-3.png,
DIR/still.png (the normal version: drawing 1 on paper), DIR/scene.json and
DIR/anim.html (the animated version). A sheet that does not cut into exactly
three line-only drawings is generated again, up to --tries times.`);
  process.exit(2);
}
const [s1, s2, s3] = states.split("|").map((s) => s.trim());
const ms = Number(opt("--ms", 250));
const tries = Number(opt("--tries", 3));
mkdirSync(out, { recursive: true });

const run = (cmd, argv) =>
  new Promise((done) => {
    const c = spawn(cmd, argv);
    let o = "";
    c.stdout.on("data", (d) => (o += d));
    c.stderr.on("data", (d) => (o += d));
    c.on("close", (code) => done({ code, o }));
  });

const subject = `${scene} Panel 1: ${s1}. Panel 2: ${s2}. Panel 3: ${s3}. Everything else identical in the three panels.`;
let ok = false;
for (let t = 1; t <= tries && !ok; t++) {
  const sheet = join(out, "sheet.jpg");
  if (existsSync(sheet)) renameSync(sheet, join(out, `sheet-rejected-${Date.now()}.jpg`));
  const g = await run("node", ["scripts/generate.mjs", "--kind", "frames", "--grid", "3x1", "--aspect", "16:9", "--out", sheet, "--subject", subject, ...(args.includes("--wash") ? ["--wash"] : [])]);
  if (g.code) {
    console.log(`try ${t}: generation failed: ${g.o.trim().slice(0, 200)}`);
    if (/characters/.test(g.o)) break;  // prompt too long: retrying cannot help
    continue;
  }
  const c = await run("python3", ["-I", "scripts/frames.py", sheet, join(out, "frame"), "--grid", "3x1"]);
  const count = Number((c.o.match(/count: (\d+)/) || [])[1] || 0);
  const filled = /FILLED/.test(c.o);
  const boxed = /BOXED/.test(c.o);
  ok = !c.code && count === 3 && !filled && !boxed;
  console.log(`try ${t}: ${count} drawings${filled ? ", filled black" : ""}${boxed ? ", framed" : ""}${ok ? ", ok" : ""}`);
}
if (!ok) {
  console.error("no clean sheet: rewrite the states (simpler, line only) and run again");
  process.exit(1);
}
await run("node", ["scripts/flipbook.mjs", out, "--seq", `1:${ms},2:${ms},3:${ms},2:${ms}`, "--title", scene.slice(0, 80)]);
await run("node", ["scripts/build.mjs", join(out, "scene.json"), "--out", join(out, "anim.html")]);
await run("python3", ["-I", "-c", `
from PIL import Image
f = Image.open(${JSON.stringify(join(out, "frame1.png"))})
bg = Image.new("RGBA", f.size, (250, 249, 246, 255))
bg.alpha_composite(f)
bg.convert("RGB").save(${JSON.stringify(join(out, "still.png"))})
`]);
console.log(`${out}/still.png  normal version\n${out}/anim.html  animated version (1, 2, 3, 2, ${ms} ms each)`);
