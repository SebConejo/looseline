import { spawnSync } from "node:child_process";
import { existsSync, mkdtempSync, rmSync } from "node:fs";
import { tmpdir } from "node:os";
import { join, resolve } from "node:path";
import { pathToFileURL } from "node:url";

const args = process.argv.slice(2);
if (!args[0]) {
  console.error("usage: node scripts/check.mjs page.html [--times 0,800,1600,2400] [--out sheet.png] [--width 300]");
  process.exit(2);
}
const page = resolve(args[0]);
const opt = (name, fallback) => {
  const i = args.indexOf(name);
  return i > -1 ? args[i + 1] : fallback;
};
const out = resolve(opt("--out", page.replace(/\.html$/, "-sheet.png")));

const candidates = [
  process.env.CHROME_PATH,
  "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
  "/Applications/Chromium.app/Contents/MacOS/Chromium",
  "/Applications/Brave Browser.app/Contents/MacOS/Brave Browser",
  "/usr/bin/google-chrome",
  "/usr/bin/chromium",
  "/usr/bin/chromium-browser",
].filter(Boolean);
const chrome = candidates.find((p) => existsSync(p));
if (!chrome) {
  console.error("no Chrome or Chromium found; set CHROME_PATH");
  process.exit(2);
}

const profile = mkdtempSync(join(tmpdir(), "ink-check-"));
const common = ["--headless=new", "--hide-scrollbars", "--no-first-run", "--no-default-browser-check", "--allow-file-access-from-files", `--user-data-dir=${profile}`];
const url = pathToFileURL(page).href;

const dump = spawnSync(chrome, [...common, "--virtual-time-budget=3000", "--dump-dom", `${url}?check`], { encoding: "utf8", timeout: 90000, maxBuffer: 1 << 28 });
const match = /<pre id="ink-report">([\s\S]*?)<\/pre>/.exec(dump.stdout || "");
if (!match) {
  console.error("the page did not produce a check report");
  console.error((dump.stderr || "").slice(0, 800));
  rmSync(profile, { recursive: true, force: true });
  process.exit(2);
}
const report = JSON.parse(match[1].replace(/&lt;/g, "<").replace(/&gt;/g, ">").replace(/&quot;/g, '"').replace(/&amp;/g, "&"));
console.log(`check: ${report.title}`);
if (report.problems.length) for (const p of report.problems) console.log(`  problem: ${p}`);
else console.log("  0 problems");

const times = opt("--times", "0,600,1200,1800,2400,3000,3600,4200");
const n = times.split(",").length;
const width = Number(opt("--width", 300));
const height = Math.round(width * 1.6) + 60;
spawnSync(chrome, [...common, "--virtual-time-budget=5000", `--window-size=${n * (width + 12) + 12},${height}`, `--screenshot=${out}`, `${url}?sheet=${times}`], { encoding: "utf8", timeout: 120000 });
rmSync(profile, { recursive: true, force: true });
console.log(existsSync(out) ? `sheet: ${out}` : "sheet: screenshot failed");
process.exit(report.problems.length ? 1 : 0);
