// Make every flipbook in jobs.json pass the automatic checks:
// at least 12 panels, steady motion (no pause, no jump), line only (no black fill).
// Up to --tries generations per subject; the best attempt is kept as sheet.jpg.
import { spawn } from "node:child_process";
import { copyFileSync, existsSync, mkdirSync, readFileSync, renameSync } from "node:fs";
const args = process.argv.slice(2);
const tries = Number(args[args.indexOf("--tries") + 1] || 3);
const only = args.find((a) => !a.startsWith("--") && isNaN(Number(a)))?.split(",");
const jobs = JSON.parse(readFileSync("library/flip/jobs.json", "utf8")).filter((j) => !only || only.includes(j.name));
const run = (cmd, argv) => new Promise((done) => { const c = spawn(cmd, argv); let o = ""; c.stdout.on("data", (d) => (o += d)); c.stderr.on("data", (d) => (o += d)); c.on("close", (code) => done({ code, o })); });

async function check(j, sheet) {
  const r = await run("python3", ["-I", "scripts/frames.py", sheet, `work/flipcheck/${j.name}-`, "--grid", j.grid, "--cycle"]);
  const count = Number((r.o.match(/count: (\d+)/) || [])[1] || 0);
  const problems = [];
  if (r.code) problems.push("cut failed");
  if (count < 12) problems.push(`${count} panels`);
  if (/UNEVEN/.test(r.o)) problems.push("uneven " + (r.o.match(/UNEVEN at (.*)/) || [])[1]);
  if (/FILLED/.test(r.o)) problems.push("filled black");
  return problems;
}

mkdirSync("work/flipcheck", { recursive: true });
const queue = [...jobs];
const report = [];
await Promise.all(Array.from({ length: 6 }, async () => {
  while (queue.length) {
    const j = queue.shift();
    const dir = `library/flip/${j.name}`;
    let best = existsSync(`${dir}/sheet.jpg`) ? { file: `${dir}/sheet.jpg`, problems: await check(j, `${dir}/sheet.jpg`) } : null;
    for (let t = 1; t <= tries && (!best || best.problems.length); t++) {
      const out = `${dir}/try-${Date.now()}.jpg`;
      const g = await run("node", ["scripts/generate.mjs", "--kind", "frames", "--grid", j.grid, "--out", out, "--subject", j.subject, ...(j.aspect ? ["--aspect", j.aspect] : []), ...(j.wash ? ["--wash"] : [])]);
      if (g.code) continue;
      const problems = await check(j, out);
      if (!best || problems.length < best.problems.length) best = { file: out, problems };
    }
    if (best && best.file !== `${dir}/sheet.jpg`) {
      if (existsSync(`${dir}/sheet.jpg`)) renameSync(`${dir}/sheet.jpg`, `${dir}/sheet-rejected-${Date.now()}.jpg`);
      copyFileSync(best.file, `${dir}/sheet.jpg`);
    }
    const line = `${j.name}: ${best?.problems.length ? best.problems.join("; ") : "passes"}`;
    report.push(line);
    console.log(line);
  }
}));
