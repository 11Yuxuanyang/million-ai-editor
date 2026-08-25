---
name: auto-cover-imagegen
description: End-to-end short-video cover creation from scripts, reference images, presenter frames, product assets, or rough ideas. Use for Douyin, Xiaohongshu, Bilibili, or YouTube cover generation and iteration, including automatic 4:3 and 3:4 Chinese cover sets.
---

# Auto Cover Imagegen

This is the single cover-workflow entry point. It chooses the hook and composition, calls `imagegen` for the finished bitmap artwork, validates both ratios, obtains independent approval, and packages the results. Do not stack another cover skill on top of it.

## Core Contract

- When invoked from `hyperframe-video-editor`, accept the locked `Cover Brief` section from `MOTION-STORYBOARD.md`, selected presenter-frame paths, and the fixed config reference as the complete production packet. Do not request or load the full editing-session history.
- Default to separate `4:3 / 1440x1080` and `3:4 / 1080x1440` covers unless the user asks otherwise.
- Use ImageGen for the complete creative cover. Do not rebuild typography or composition with HTML, CSS, SVG, canvas, or Python.
- Lock all Simplified Chinese copy before generation; allow no invented captions, fake logos, or pseudo-writing.
- Use one scroll-stopper idea, one visible metaphor, and at most one secondary promise. Never turn the script into a slide.
- Prefer direct execution. Ask only when the claim, identity, product, or commercial wording is genuinely ambiguous.

## Load Only What Helps

- Script, outline, or transcript: [script-to-cover.md](references/script-to-cover.md)
- Reference image, prior cover, palette, or ratio issue: [style-and-layout.md](references/style-and-layout.md)
- Funny Chinese AI/business hook: [funny-ai-business-cover.md](references/funny-ai-business-cover.md)
- Named AI tool plus concrete money/result promise: [ai-tool-money-cover.md](references/ai-tool-money-cover.md)

## Workflow

1. **Ground the episode**
   - Identify the topic, platform, destination, image roles, and newest visual critique.
   - Prefer the locked storyboard cover brief when it exists. If it is inconsistent or lacks a truthful claim, return the packet to the main controller for a corrected brief; do not reopen the full editing transcript inside the cover worker.
   - When given video, inspect representative frames and choose a strong presenter identity reference.

2. **Write a compact cover brief**
   - Record `core promise`, `viewer hook`, exact copy, visual metaphor, style tokens, and separate ratio plans.
   - Choose the most concrete truthful claim a stranger understands in one second.

3. **Generate with ImageGen**
   - Generate `4:3` and `3:4` independently; never crop one into the other.
   - Ask for polished final artwork with large front-facing text and recognizable presenters.
   - If ImageGen returns the wrong ratio, regenerate or edit/outpaint an exact target-ratio image. Do not ship pillar bars or obvious padding. Resize only when the existing aspect ratio already matches.

4. **Inspect both covers**
   - View the actual files. Check every Chinese character, extra text, faces, hands, crop safety, ratio, reference fidelity, visual metaphor, and phone-thumbnail readability.
   - Regenerate weak or incorrect output with one targeted correction; do not patch creative text with code.

5. **Require independent approval**
   - Give both final images and locked copy to an uninvolved read-only Agent.
   - The report must name the reviewer, record an ISO-8601 review time, list both absolute cover paths, and contain exactly one `Final Conclusion: 通过` line.
   - A `返修` requires a new artifact and fresh review. Store the final `通过` report beside the covers.

6. **Package**
   - Save project-bound finals outside `~/.codex/generated_images` as `cover-<slug>-4x3-1440x1080.png` and `cover-<slug>-3x4-1080x1440.png`.
   - Report inline previews, absolute paths, dimensions, and locked copy.
