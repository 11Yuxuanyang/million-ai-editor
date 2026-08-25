# Funny AI/Business Cover Reference

Use this style for Chinese AI/business talking-head videos when the user wants a cover that feels funny, punchy, and internet-native.

Default deliverable: generate two covers from the same concept, one 4:3 horizontal and one 3:4 vertical. The 3:4 version should be recomposed, not cropped from 4:3.

## Visual Formula

- Dark tech/business background, usually black or deep navy.
- Huge Chinese headline in white plus bright yellow; 1-2 dominant lines.
- Presenter face on one side, preferably close, expressive, slightly confused, warning, or amused.
- One concrete gag object that explains the joke: pot/锅, warning sign, robot, invoice, phone, coins, broken UI, etc.
- One small subtitle strip at the bottom only if it remains readable.
- Strong contrast and sharp shapes; avoid pastel lecture aesthetics.

## Ratio Rules

- **4:3 horizontal**: Use a left/right poster layout, often giant text on the left/center and presenter on the right.
- **3:4 vertical**: Use stacked text, closer presenter framing, and a smaller but still readable gag object. Keep the punchline visible in the upper/middle area.
- Do not use one image as a lazy crop for the other. Generate both with matching concept and separate composition.

## Good Hook Pattern

Use a funny but still truthful sentence:

- `AI不背锅`
- `你俩没对齐`
- `别让AI猜`
- `上下文没给够`
- `不是模型笨`

The cover text should usually sharpen the title, not copy it verbatim.

## Prompt Notes

- Ask imagegen for the whole finished cover.
- Include “professional Douyin creator cover” and “thumbnail-safe layout”.
- Tell it to render exact Simplified Chinese and no extra text.
- If the cover needs a presenter, use a real video frame as identity reference.
- If a previous generation got the face right but the text wrong, regenerate with fewer text elements and stronger “correct Chinese text” constraints.

## Validation

Approve only if:

- The main headline is readable at phone thumbnail size.
- The Chinese characters are correct enough to publish.
- The gag object is understandable in one glance.
- The presenter is recognizable enough for the account.
- No major word is cropped in either the 4:3 or 3:4 frame.

Reject if it looks like a generated poster, a lecture slide, or a generic AI gradient background.
