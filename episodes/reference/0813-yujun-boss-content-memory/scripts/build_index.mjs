import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const template = fs.readFileSync(path.join(root, "index.template.txt"), "utf8");
const captions = JSON.parse(fs.readFileSync(path.join(root, "work/captions.json"), "utf8"));
const timeline = fs.readFileSync(path.join(root, "timeline.js"), "utf8");

const html = captions.map((caption) => `
        <div id="${caption.id}" class="clip body-caption" data-start="${caption.start}" data-duration="${caption.duration}" data-track-index="90">
          <div class="caption-cn">${caption.zh}</div>
          <div class="caption-en">${caption.en.replaceAll("&", "&amp;").replaceAll("<", "&lt;")}</div>
        </div>`).join("");

fs.writeFileSync(
  path.join(root, "index.html"),
  template
    .replace("<!-- CAPTIONS -->", html)
    .replace("/* TIMELINE */", timeline),
  "utf8",
);
