import fs from "node:fs";
import path from "node:path";
import { createHash } from "node:crypto";
import { fileURLToPath } from "node:url";

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const realRoot = fs.realpathSync(root);

function isInsideRoot(target) {
  return target === realRoot || target.startsWith(`${realRoot}${path.sep}`);
}

function resolveInsideRoot(relative, label) {
  if (!relative) return null;
  if (path.isAbsolute(relative)) throw new Error(`${label} must be relative to the episode`);
  const target = path.resolve(root, relative);
  if (target !== root && !target.startsWith(`${root}${path.sep}`)) {
    throw new Error(`${label} escapes the episode: ${relative}`);
  }
  if (fs.existsSync(target) && !isInsideRoot(fs.realpathSync(target))) {
    throw new Error(`${label} resolves outside the episode: ${relative}`);
  }
  return target;
}

function readJson(relative, fallback = null) {
  const target = resolveInsideRoot(relative, "JSON path");
  return fs.existsSync(target) ? JSON.parse(fs.readFileSync(target, "utf8")) : fallback;
}

function readText(relative, fallback = "") {
  if (!relative) return fallback;
  const target = resolveInsideRoot(relative, "assembly file path");
  return fs.existsSync(target) ? fs.readFileSync(target, "utf8") : fallback;
}

function sha256File(target) {
  return createHash("sha256").update(fs.readFileSync(target)).digest("hex");
}

function escapeHtml(value) {
  return String(value ?? "")
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;");
}

const episode = readJson("episode.json", {});
const defaults = readJson("editorial-defaults.snapshot.json", {});
const aRoll = readJson("work/a-roll.json", {});
const captionsRaw = readJson(episode.paths?.captions ?? "work/captions.json", []);
const captions = Array.isArray(captionsRaw) ? captionsRaw : captionsRaw.captions ?? [];
const sequencePlan = readJson(episode.paths?.sequencePlan ?? "work/sequence-plan.json", { sequences: [] });
if (
  !sequencePlan
  || typeof sequencePlan !== "object"
  || Array.isArray(sequencePlan)
  || !Array.isArray(sequencePlan.sequences)
) {
  throw new Error("sequence plan is malformed; run pack-sequences after fixing it");
}
if (
  !sequencePlan.sequences.every(
    (sequence) => sequence
      && typeof sequence === "object"
      && !Array.isArray(sequence)
      && typeof sequence.id === "string"
      && sequence.id,
  )
) {
  throw new Error("sequence plan contains an invalid sequence; run pack-sequences after fixing it");
}
const assemblyRelative = episode.paths?.assemblyPlan ?? "work/assembly-plan.json";
const assemblyTarget = resolveInsideRoot(assemblyRelative, "assembly plan path");
if (sequencePlan.sequences.length > 0 && !fs.existsSync(assemblyTarget)) {
  throw new Error("assembly plan missing for non-empty V3 sequence plan; run assemble-sequences");
}
const assembly = readJson(assemblyRelative, { sequences: [] });
if (
  !assembly
  || typeof assembly !== "object"
  || Array.isArray(assembly)
  || !Array.isArray(assembly.sequences)
) {
  throw new Error("assembly plan is malformed; run assemble-sequences");
}
const plannedSequences = sequencePlan.sequences;
if (plannedSequences.length === 0 && assembly.sequences.length > 0) {
  throw new Error("assembly plan contains stale sequence artifacts; run assemble-sequences");
}
if (plannedSequences.length > 0) {
  const creativeBriefTarget = resolveInsideRoot(
    episode.paths?.creativeBrief ?? "work/creative-brief.json",
    "creative brief path",
  );
  if (!fs.existsSync(creativeBriefTarget)) {
    throw new Error("creative brief missing for non-empty V3 sequence plan");
  }
  if (assembly?.systemVersion !== 3 || assembly?.episodeId !== episode.id) {
    throw new Error("assembly plan does not belong to this V3 episode; run assemble-sequences");
  }
  if (
    assembly.creativeBriefSha256 !== sha256File(creativeBriefTarget)
    || assembly.sequencePlanSha256 !== sha256File(
      resolveInsideRoot(episode.paths?.sequencePlan ?? "work/sequence-plan.json", "sequence plan path"),
    )
  ) {
    throw new Error("assembly plan is stale; run assemble-sequences");
  }
  const plannedIds = plannedSequences.map((sequence) => sequence?.id);
  const assembledIds = (assembly?.sequences ?? []).map((sequence) => sequence?.id);
  if (JSON.stringify(plannedIds) !== JSON.stringify(assembledIds)) {
    throw new Error("assembly plan sequence coverage is incomplete or out of order; run assemble-sequences");
  }
  for (const sequence of assembly.sequences) {
    const files = sequence?.files ?? {};
    const artifactPaths = [
      ...Object.values(files).filter((value) => typeof value === "string" && value),
      ...(sequence?.assets ?? []).filter((value) => typeof value === "string" && value),
    ];
    const artifactTargets = new Map();
    for (const relative of artifactPaths) {
      artifactTargets.set(
        relative,
        resolveInsideRoot(relative, `assembly sequence ${sequence.id} artifact`),
      );
    }
    const lockedArtifacts = sequence?.artifactSha256;
    if (!lockedArtifacts || typeof lockedArtifacts !== "object" || Array.isArray(lockedArtifacts)) {
      throw new Error(`assembly sequence ${sequence?.id ?? "unknown"} has no artifact lock; run assemble-sequences`);
    }
    if (
      JSON.stringify([...new Set(artifactPaths)].sort())
      !== JSON.stringify(Object.keys(lockedArtifacts).sort())
    ) {
      throw new Error(`assembly sequence ${sequence.id} artifact coverage changed; run assemble-sequences`);
    }
    for (const relative of artifactPaths) {
      const target = artifactTargets.get(relative);
      if (!fs.existsSync(target) || sha256File(target) !== lockedArtifacts[relative]) {
        throw new Error(`assembly sequence ${sequence.id} artifact changed: ${relative}; run assemble-sequences`);
      }
    }
  }
}
const duration = Number(aRoll.duration ?? episode.duration ?? 10);
const width = Number(episode.deliveryOverrides?.width ?? defaults.delivery?.width ?? 1920);
const height = Number(episode.deliveryOverrides?.height ?? defaults.delivery?.height ?? 1080);
const fps = Number(episode.deliveryOverrides?.fps ?? defaults.delivery?.fps ?? 60);
const captionConfig = defaults.captions ?? {};
const shadow = captionConfig.shadow ?? {};
const shadowDistance = Number(shadow.distanceInCapCut ?? 5);
const shadowOpacity = Number(shadow.opacity ?? 0.9);
const fontStack = (captionConfig.fontStack ?? ["-apple-system", "PingFang SC", "sans-serif"])
  .map((font) => (font.includes(" ") ? `"${font}"` : font))
  .join(", ");
const editorialVars = `:root {
  --font-stack: ${fontStack};
  --caption-inset: ${captionConfig.layout1080p?.horizontalInsetPx ?? 150}px;
  --caption-bottom: ${captionConfig.layout1080p?.bottomPx ?? 42}px;
  --caption-gap: ${captionConfig.layout1080p?.lineGapPx ?? 8}px;
  --caption-cn-color: ${captionConfig.chinese?.color ?? "#fff"};
  --caption-cn-size: ${captionConfig.chinese?.sizePx ?? 54}px;
  --caption-cn-weight: ${captionConfig.chinese?.fontWeight ?? 850};
  --caption-cn-line-height: ${captionConfig.chinese?.lineHeight ?? 1.08};
  --caption-en-color: ${captionConfig.english?.color ?? "#ff7a00"};
  --caption-en-size: ${captionConfig.english?.sizePx ?? 32}px;
  --caption-en-weight: ${captionConfig.english?.fontWeight ?? 750};
  --caption-en-line-height: ${captionConfig.english?.lineHeight ?? 1.05};
  --caption-shadow: ${shadowDistance}px ${shadowDistance}px ${Math.max(2, shadowDistance * 2)}px rgba(0, 0, 0, ${shadowOpacity});
}`;

const captionHtml = captions.map((caption, index) => {
  const start = Number(caption.start ?? caption.startSeconds ?? 0);
  const end = Number(caption.end ?? caption.endSeconds ?? start + Number(caption.duration ?? 0));
  const captionDuration = Math.max(0.01, Number(caption.duration ?? end - start));
  const zh = caption.zh ?? caption.cn ?? caption.chinese ?? caption.text ?? "";
  const en = caption.en ?? caption.english ?? "";
  return `<section id="caption-${index + 1}" class="clip body-caption" data-start="${start}" data-duration="${captionDuration}" data-track-index="90" data-layout-allow-overlap>
        <div class="caption-cn">${escapeHtml(zh)}</div>
        ${en ? `<div class="caption-en">${escapeHtml(en)}</div>` : ""}
      </section>`;
}).join("\n      ");

const captionTimeline = captions.map((caption, index) => {
  const start = Number(caption.start ?? caption.startSeconds ?? 0);
  return `timeline.fromTo("#caption-${index + 1}", { opacity: 0, y: 10 }, { opacity: 1, y: 0, duration: 0.12, ease: "power2.out" }, ${start});`;
}).join("\n      ");

const sequenceParts = (assembly.sequences ?? []).map((sequence) => {
  const files = sequence.files ?? {};
  return {
    id: sequence.id,
    fragment: readText(files.fragment),
    styles: readText(files.styles),
    timeline: readText(files.timeline),
  };
});

const sequenceScenes = sequenceParts
  .filter((part) => part.fragment.trim())
  .map((part) => `<!-- V3 sequence ${part.id} -->\n${part.fragment.trim()}`)
  .join("\n      ");

const sequenceStyles = sequenceParts
  .filter((part) => part.styles.trim())
  .map((part) => `/* V3 sequence ${part.id} */\n${part.styles.trim()}`)
  .join("\n");

const sequenceTimeline = sequenceParts
  .filter((part) => part.timeline.trim())
  .map((part) => `// V3 sequence ${part.id}\n{\n${part.timeline.trim()}\n}`)
  .join("\n      ");

const template = fs.readFileSync(path.join(root, "index.template.txt"), "utf8");
const replacements = {
  "{{WIDTH}}": width,
  "{{HEIGHT}}": height,
  "{{FPS}}": fps,
  "{{TITLE}}": escapeHtml(episode.title ?? "Untitled episode"),
  "{{EPISODE_ID}}": escapeHtml(episode.id ?? "main"),
  "{{DURATION}}": duration,
  "{{A_ROLL}}": escapeHtml(episode.paths?.aRoll ?? "assets/media/a-roll-1080p60.mp4"),
  "{{EDITORIAL_VARS}}": editorialVars,
  "{{CAPTIONS}}": captionHtml,
  "{{CAPTION_TIMELINE}}": captionTimeline,
  "{{SEQUENCE_SCENES}}": sequenceScenes,
  "{{SEQUENCE_STYLES}}": sequenceStyles,
  "{{SEQUENCE_TIMELINE}}": sequenceTimeline,
};

let html = template;
for (const [needle, value] of Object.entries(replacements)) {
  html = html.replaceAll(needle, String(value));
}
fs.writeFileSync(path.join(root, "index.html"), html, "utf8");
