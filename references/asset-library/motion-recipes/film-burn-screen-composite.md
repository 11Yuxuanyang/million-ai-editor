# Film Burn Overlay Transition + RGB Screen Composite

## Semantic Job

Use an analog film-burn exposure plate to hide a scene cut at its brightest exposure peak. The outgoing shot remains visible under the colored lead-in, and the incoming shot becomes visible under the warm tail. This is an optical chapter transition, not a black fade, a white card, or a directional wipe.

## Exact Identity

- Professional term: `Film Burn Overlay Transition + RGB Screen Composite`
- Chinese retrieval aliases: `胶片烧片转场`、`透明烧片`、`滤色烧片`、`光影冲白转场`
- Distinguish from:
  - `Light Leak Transition`: photographed flare or leaking light may motivate a cut, but it does not necessarily contain a full-frame film-burn exposure peak.
  - `Light Sweep / Light Wipe Transition`: a moving bright edge directly reveals the incoming scene.
  - `Exposure Flash + Bloom`: an exposure/grade treatment generated from the base footage rather than a sourced analog burn plate.
  - `Dip to Black`: explicitly forbidden before this transition.

## Event-Based Timeline

Do not copy fixed seconds from the approved sample. Identify these events in the chosen plate:

1. `burnStart`: first visible red/orange contamination while the plate's dark negative space still dominates.
2. `peakStart`: the near-white exposure begins to cover enough of the frame to hide a cut.
3. `peakCenter`: highest useful full-frame luminance.
4. `peakEnd`: the incoming shot can begin resolving without exposing the edit.
5. `tailEnd`: colored exposure and contrast return to the natural incoming image.

Place the A-to-B cut at `peakCenter`, not at half the overlay duration. For registered
asset `transition.film-burn-screen-composite.v1`, the required visible range is
`0.45–0.58s` and the near-white hiding window is `1–3` frames at `60fps`; the approved
example lands at `0.52s`. A different plate or timing range requires its own registry
record and independent review.

## Composite Pipeline

1. Choose a real or sourced film-burn plate with dark negative space, non-uniform red/orange exposure, a measurable near-white peak, and a usable colored tail.
2. Retime the effect plate independently to the edit rhythm. Do not retime either filmed A/B source again.
3. Composite in RGB space with `Screen` or a restrained additive equivalent.
4. Keep the outgoing shot continuously visible from `burnStart` to the exposure peak.
5. Cut A to B at the highest-luma peak.
6. Keep the colored tail over B, then restore B's natural color and contrast by `tailEnd`.

For FFmpeg, convert both inputs to an RGB working format before blending. Screen blending in planar YUV can create unexpected chroma shifts.

```text
[base]format=gbrp[base_rgb];
[burn]format=gbrp[burn_rgb];
[base_rgb][burn_rgb]blend=all_mode=screen
```

In browser/HyperFrames work, use an actual video overlay with `mix-blend-mode: screen` or a tested WebGL/Canvas equivalent. A black-backed burn plate is not alpha footage: its black pixels become visually transparent because of the blend mode.

## Hard Constraints

- No `Dip to Black`, pre-darkening, black opacity card, or exposure reduction before `burnStart`.
- Do not use a plain white opacity flash as a substitute for the burn plate.
- Do not hide the outgoing shot during the colored lead-in.
- Do not hard-cut the colored tail immediately after the peak.
- Do not let the tail leave a lasting red, orange, or yellow cast on the incoming scene.
- Do not call this `Light Wipe` unless a moving light boundary itself reveals the next shot.
- If the base footage is already near-white, select another plate or another transition; the event anchors may become unreadable.

## Acceptance Frames

Review at least:

1. One clean frame before `burnStart`.
2. A lead-in frame where the outgoing shot is still clearly visible under red/orange contamination.
3. `peakCenter`, where the cut is fully hidden.
4. The first readable incoming frame under the colored tail.
5. `tailEnd`, where the incoming shot has recovered its natural color.

Also check the complete transition for black frames, a visible hard cut, frozen frames, YUV-induced color contamination, prolonged near-white exposure, and a tail that ends abruptly.

## Registered Asset

- Overlay: `references/asset-library/overlays/film-burn-red-orange-screen-v1.mp4`
- Overlay SHA-256: `f6864f074f455b6ee8f54f888aa735787e303b81a1c90a57b7513c6464cad44f`
- Overlay technical specification: H.264, `720×406`, `30000/1001fps`, `yuv420p`, `1.2012s`
- Approved reference: `references/asset-library/previews/film-burn-screen-composite.png`
- Review: `references/asset-library/reviews/film-burn-screen-composite-v1-review.md`
- Source page: `https://ineedfx.com/category/film-burns/`
- Direct pack preview: `https://ineedfx.com/wp-content/uploads/22841660-pack-film-burns-10in1_480p.mp4`
- License: `Creative Commons Attribution 4.0 International (CC BY 4.0)`
- Terms/license: `https://ineedfx.com/terms-and-conditions-license/`
- Required attribution when published: `Certain resources are sourced from iNeedFx.com` or an equivalent credit linking to `iNeedFx.com`
- General usage statement: `https://ineedfx.com/about/`
- Canonical excerpt: approximately `00:07.65–00:08.85` from the downloaded pack preview

The preview contact strip contains user-provided footage and is reference-only. The reusable overlay file itself contains only the sourced effect plate. Do not redistribute the plate as an unattributed stock download or include it in a resold stock-media collection.
