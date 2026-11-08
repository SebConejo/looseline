// Generates every frame sheet listed in jobs.json that has no sheet.jpg yet.
import { spawn } from "node:child_process";
import { existsSync, mkdirSync, readFileSync } from "node:fs";
const jobs = JSON.parse(readFileSync("library/flip/jobs.json", "utf8"));
const only = process.argv[2]?.split(",");
const run = (argv) => new Promise((done) => { const c = spawn("node", argv); let o = ""; c.stdout.on("data", d => o += d); c.stderr.on("data", d => o += d); c.on("close", code => done({ code, o })); });
const queue = jobs.filter(j => !only || only.includes(j.name));
await Promise.all(Array.from({ length: 6 }, async () => {
  while (queue.length) {
    const j = queue.shift();
    const dir = `library/flip/${j.name}`;
    mkdirSync(dir, { recursive: true });
    if (existsSync(`${dir}/sheet.jpg`) && !only) { console.log(j.name, "already there"); continue; }
    const r = await run(["scripts/generate.mjs", "--kind", "frames", "--grid", j.grid, "--out", `${dir}/sheet.jpg`, "--subject", j.subject, ...(j.aspect ? ["--aspect", j.aspect] : []), ...(j.wash ? ["--wash"] : [])]);
    console.log(j.name, r.code ? "FAILED " + r.o.slice(0, 300) : "ok");
  }
}));
