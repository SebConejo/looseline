import { existsSync, readFileSync, writeFileSync } from "node:fs";
import { dirname, join, resolve } from "node:path";
import { fileURLToPath } from "node:url";

const HERE = dirname(fileURLToPath(import.meta.url));
const args = process.argv.slice(2);
if (!args[0]) {
  console.error("usage: node scripts/build.mjs scene.json [--out page.html]");
  process.exit(2);
}
const scenePath = resolve(args[0]);
const dir = dirname(scenePath);
const outAt = args.indexOf("--out");
const out = outAt > -1 ? resolve(args[outAt + 1]) : scenePath.replace(/\.json$/, ".html");
const scene = JSON.parse(readFileSync(scenePath, "utf8"));

const dataUri = (file) => {
  const path = resolve(dir, file);
  if (!existsSync(path)) throw new Error(`${file} not found next to ${scenePath}`);
  return `data:image/png;base64,${readFileSync(path).toString("base64")}`;
};
const metaOf = (file) => {
  const path = resolve(dir, file.replace(/\.png$/, ".json"));
  return existsSync(path) ? JSON.parse(readFileSync(path, "utf8")) : null;
};

const [W, H] = scene.size;
for (const layer of scene.layers) {
  const files = layer.poses || [layer.src];
  if (!layer.bbox) {
    const boxes = files.map(metaOf).filter((m) => m && m.bbox);
    if (boxes.length) {
      const [iw, ih] = boxes[0].size;
      const kx = (layer.w ?? W) / iw, ky = (layer.h ?? H) / ih;
      const x0 = Math.min(...boxes.map((m) => m.bbox[0])), y0 = Math.min(...boxes.map((m) => m.bbox[1]));
      const x1 = Math.max(...boxes.map((m) => m.bbox[2])), y1 = Math.max(...boxes.map((m) => m.bbox[3]));
      layer.bbox = [(layer.x ?? 0) + x0 * kx, (layer.y ?? 0) + y0 * ky, (layer.x ?? 0) + x1 * kx, (layer.y ?? 0) + y1 * ky].map((v) => Math.round(v));
    }
  }
  if (layer.poses) layer.poses = layer.poses.map(dataUri);
  else layer.src = dataUri(layer.src);
}

const runtime = readFileSync(join(HERE, "runtime.js"), "utf8");
const esc = (s) => String(s ?? "").replace(/&/g, "&amp;").replace(/</g, "&lt;");
const paper = scene.paper || "#f4f2ec";
const html = `<!doctype html>
<html lang="${scene.lang || "en"}">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>${esc(scene.title)}</title>
<style>
*{box-sizing:border-box}
body{margin:0;background:#efede7;color:#1b1b1a;font:15px/1.45 ui-sans-serif,system-ui,-apple-system,sans-serif}
main{max-width:${Math.min(900, Math.max(420, W))}px;margin:0 auto;padding:32px 16px 48px}
figure{margin:0;background:${paper};border:1px solid #0000000f;border-radius:14px;overflow:hidden}
figure svg{display:block;width:100%;height:auto}
figcaption{padding:8px 14px 10px;color:#8b867d;font-size:13px;background:#faf9f6}
#stage.sheet{display:flex;gap:12px;padding:12px;background:#efede7}
#stage.sheet .cell{width:300px;flex:none;background:${paper};border-radius:10px;overflow:hidden}
#stage.sheet .cell span{display:block;padding:4px 8px;color:#8b867d;font-size:12px;background:#faf9f6}
body.bare main{max-width:none;padding:0}
body.bare figure{border:0;border-radius:0;background:transparent}
body.bare figcaption{display:none}
</style>
</head>
<body>
<main>
  <figure>
    <div id="stage"></div>
    <figcaption>${esc(scene.caption || scene.title)}</figcaption>
  </figure>
</main>
<script>${runtime}</script>
<script>
if (/[?&](sheet|check)/.test(location.search)) document.body.classList.add("bare");
INK.play(document.getElementById("stage"), ${JSON.stringify(scene)});
</script>
</body>
</html>
`;
writeFileSync(out, html);
console.log(`wrote ${out} (${Math.round(html.length / 1024)} KB)`);
