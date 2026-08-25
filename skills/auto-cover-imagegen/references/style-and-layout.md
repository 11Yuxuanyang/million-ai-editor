# Style And Layout

Use this reference when the user provides cover references, palette screenshots, prior versions, or presenter frames.

## Reference Image Roles

Classify every image before prompting:

- **Style reference**: palette, typography, density, mood, background logic.
- **Presenter identity reference**: faces, clothing, body type, pose, expression.
- **Product reference**: app UI, product object, screenshot, scene.
- **Previous version**: what to keep or reject.
- **Edit target**: the exact image to modify while preserving most content.

Never confuse a style reference's text with required cover text. Use its visual logic, not its words.

## Style Extraction

Extract five tokens:

```text
Background: black / cream / gradient / photo / paper / studio / etc.
Palette: 2-4 dominant colors and 1 accent.
Typography: huge block / condensed / rounded sticker / editorial / handwritten / etc.
Density: minimalist / balanced / maximalist.
Mood: documentary / playful / battle poster / premium / funny / urgent.
```

Then adapt for thumbnail readability. A beautiful reference can still be too quiet for a cover; increase title scale or contrast when needed.

## Design Defaults

For creator/business challenge covers:

- Use presenter faces large enough to create trust.
- Use one major number or objective when available.
- Use task cards when the video invites participation.
- Use money and AI symbols as secondary stickers, not wallpaper.
- Keep the main title dominant over decorative objects.

## Ratio Composition

### 4:3

Best for platform cover grids and horizontal previews.

- Presenter on one side, title on the other.
- Keep the main title inside the central 80% safe area.
- Use the lower-right or lower-left for task/status cards.
- Avoid placing small text in corners.

### 3:4

Best for vertical mobile cover slots.

- Stack: badge, title, subtitle, presenter, task/status card.
- Keep faces in the upper or middle third.
- Keep the task card in the lower third with large row height.
- Do not crop a 4:3 cover into 3:4. Recompose it.

## Bright Background Direction

Use when the user says the cover is not attractive enough, too dark, or不要黑色底子:

- Warm off-white, cream, light pink, sky blue, or light mint background.
- Vivid rose pink or deep purple main text.
- Neon lime or yellow-green label strips for secondary hooks.
- White outline around presenters and sticker objects.
- Controlled sticker elements: AI chip, $1M coin, money bills, arrow, check marks.

Avoid muddy beige, low contrast, or too much empty space.

## Minimal Black/Pink Direction

Use only when the user explicitly asks for reference images like a black title card:

- Pure black background.
- Soft pale pink headline.
- White thin condensed secondary text.
- Lots of calm negative space.
- Few or no money stickers.

If the user later asks for more attractiveness or no black background, switch away from this direction.

## QA Checklist

Reject or regenerate if:

- The Chinese title is misspelled, pseudo-written, or cropped.
- The cover has random extra text.
- People are unrecognizable or faces look distorted.
- The reference palette was ignored.
- The task/status block is too small to read.
- The visual metaphor fights the text.
- The cover looks like a presentation slide rather than a thumbnail.
- 3:4 depends on side content from the 4:3 layout.

## Resizing And Padding

- Use exact output dimensions when generated correctly.
- If the ratio already matches and only the pixel dimensions differ, resize with `sips -z`.
- If the ratio is wrong, regenerate or ImageGen-outpaint an exact target-ratio edit. Do not ship visible side bars, blurred filler, or obvious padding.
- Never stretch people or type.
- Avoid cropping faces, titles, or task cards.
