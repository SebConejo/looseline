// Runs scripts/make.mjs for every entry of jobs.json that has no anim.html yet.
import { spawn } from "node:child_process";
import { existsSync, readFileSync } from "node:fs";
const only = process.argv[2]?.split(",");
const jobs = JSON.parse(readFileSync("library/anim/jobs.json", "utf8")).filter((j) => (only ? only.includes(j.name) : !existsSync(`library/anim/${j.name}/anim.html`)));
const run = (argv) => new Promise((done) => { const c = spawn("node", argv); let o = ""; c.stdout.on("data", (d) => (o += d)); c.stderr.on("data", (d) => (o += d)); c.on("close", (code) => done({ code, o })); });
await Promise.all(Array.from({ length: 6 }, async () => {
  while (jobs.length) {
    const j = jobs.shift();
    const r = await run(["scripts/make.mjs", "--subject", j.subject, "--states", j.states, "--out", `library/anim/${j.name}`, ...(j.wash ? ["--wash"] : [])]);
    console.log(`${j.name}: ${r.code ? "FAILED" : "ok"} | ${r.o.split("\n").filter((l) => l.startsWith("try")).join(" ; ")}`);
  }
}));
