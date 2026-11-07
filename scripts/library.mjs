import { spawn } from "node:child_process";
import { existsSync, mkdirSync, readFileSync } from "node:fs";
import { dirname, join, resolve } from "node:path";
import { fileURLToPath } from "node:url";

const HERE = dirname(fileURLToPath(import.meta.url));
const ROOT = resolve(HERE, "..");
const args = process.argv.slice(2);
const opt = (name, fallback) => {
  const i = args.indexOf(name);
  return i > -1 ? args[i + 1] : fallback;
};
if (args.includes("--help")) {
  console.log(`usage: node scripts/library.mjs [--only 1-10] [--retry 7] [--note "judge reasons"] [--jobs 4]

Generates library/<id>-<slug>/source.jpg for every catalog entry that has none,
then splits it into ink and wash layers. --retry regenerates one entry (the old
source becomes source-rejected-N.jpg) and adds --note to its prompt.`);
  process.exit(0);
}
const catalog = JSON.parse(readFileSync(join(ROOT, "library/catalog.json"), "utf8"));
const range = opt("--only");
let wanted = catalog;
if (range) {
  const [a, b] = range.split("-").map(Number);
  wanted = catalog.filter((e) => e.id >= a && e.id <= (b ?? a));
}
const retry = opt("--retry");
if (retry) wanted = catalog.filter((e) => e.id === Number(retry));
const note = opt("--note", "");
const jobs = Number(opt("--jobs", 4));

const dirOf = (e) => join(ROOT, "library", `${String(e.id).padStart(2, "0")}-${e.slug}`);
const run = (cmd, argv) =>
  new Promise((done) => {
    const child = spawn(cmd, argv, { cwd: ROOT });
    let out = "";
    child.stdout.on("data", (d) => (out += d));
    child.stderr.on("data", (d) => (out += d));
    child.on("close", (code) => done({ code, out }));
  });

async function one(e) {
  const dir = dirOf(e);
  mkdirSync(dir, { recursive: true });
  const src = join(dir, "source.jpg");
  if (retry && existsSync(src)) {
    let n = 1;
    while (existsSync(join(dir, `source-rejected-${n}.jpg`))) n++;
    await run("mv", [src, join(dir, `source-rejected-${n}.jpg`)]);
  }
  if (existsSync(src)) return `${e.id} ${e.slug}: already there`;
  const subject = note ? `${e.subject} Avoid: ${note}` : e.subject;
  const gen = await run("node", ["scripts/generate.mjs", "--subject", subject, "--out", src, ...(e.wash ? ["--wash"] : [])]);
  if (gen.code !== 0) return `${e.id} ${e.slug}: generation failed: ${gen.out.trim().slice(0, 300)}`;
  const split = await run("python3", ["-I", "scripts/layers.py", src, join(dir, "layer")]);
  return `${e.id} ${e.slug}: ok${split.code ? " (layer split failed)" : ""}`;
}

const queue = [...wanted];
const workers = Array.from({ length: jobs }, async () => {
  while (queue.length) {
    const e = queue.shift();
    console.log(await one(e));
  }
});
await Promise.all(workers);
