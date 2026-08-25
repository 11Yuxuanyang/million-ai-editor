# Film Burn Screen Composite v1 Independent Asset Review

- Review Agent: `Arendt / /root/independent_preview_review`
- Review mode: independent, read-only
- Review time: `2026-07-28T18:23:03+08:00`

## Reviewed Objects

1. Canonical overlay: `references/asset-library/overlays/film-burn-red-orange-screen-v1.mp4`
2. Reference preview: `references/asset-library/previews/film-burn-screen-composite.png`
3. Motion recipe and source notes: `references/asset-library/motion-recipes/film-burn-screen-composite.md`
4. Approved composition behavior is represented by the preview and review in this asset directory; the disposable experiment project is not a runtime dependency.

## Key Evidence

### Canonical Overlay

- Actual SHA-256 is `f6864f074f455b6ee8f54f888aa735787e303b81a1c90a57b7513c6464cad44f`, matching the motion recipe.
- `ffprobe`: H.264, `720×406`, `yuv420p`, `30000/1001 fps`, `36` frames, `1.2012 s`; all recorded technical fields match the recipe.
- Full-stream decode completed without error.
- Visual review of all 36 frames found only the sourced film-burn plate; no user A-roll, face, room, subtitle, logo, or sample-composite pixel is present.
- The plate contains the required event sequence: dark negative space, red/orange colored lead-in, broad near-white exposure peak, then a warm moving tail that returns to black. Under RGB Screen, its black/dark areas can preserve the base image while the exposure peak can hide the cut.

### Reusable Method

- The recipe explicitly forbids `Dip to Black`, pre-darkening, black cards, and exposure reduction before `burnStart`.
- It requires A to remain visible through the colored lead-in, places the A/B cut at `peakCenter` rather than the temporal midpoint, and keeps B visible under the colored tail until `tailEnd`.
- It requires independent retiming of the effect plate and explicitly forbids retiming A/B again.
- It specifies conversion of both inputs to RGB (`gbrp`) before Screen blending and warns against planar-YUV blending; the included FFmpeg and browser/HyperFrames guidance is actionable.
- The approved sample hash is `100f2c15242f8b6f6a718168d3035b67a4bcc645a700cf235e5a02cff442374a`. Its existing independent review records `通过`, including no pre-darkening, A visibility, exposure-peak cut concealment, B under warm tail, and normal color recovery.

### Preview and Reuse Boundary

- The preview is `1936×368`, SHA-256 `0bd8cde9440a6afdf84b692076dd0e4b832c79f637cbc238f82e41953d4aa7ef`, and visibly contains the user A/B sample footage.
- The recipe explicitly marks that preview as `reference-only` and separately states that the reusable overlay contains only the sourced effect plate. This adequately distinguishes the reusable asset from the user-footage preview.
- The source page, direct pack-preview URL, usage-statement URL, local source file, canonical excerpt `00:07.65–00:08.85`, and episode/sample boundary are recorded consistently across the recipe and source notes.

## Revision Evidence

- Motion recipe lines 79–82 now record `Creative Commons Attribution 4.0 International (CC BY 4.0)`, the official `https://ineedfx.com/terms-and-conditions-license/` URL, the required `iNeedFx.com` attribution, and the separate general usage statement.
- Motion recipe line 85 now expressly forbids unattributed stock-download redistribution and inclusion in a resold stock-media collection.
- Source notes lines 9–11 independently repeat the official terms URL, CC BY 4.0 identity, attribution requirement, and the unattributed redistribution/resale boundary.
- Canonical overlay, preview, and approved-sample hashes remain unchanged from the first review. The revision only corrected provenance/permission documentation and introduced no media regression.

## Issues

- No remaining issue was found in the requested review scope.

Final Conclusion: 通过
