# Editorial Taste V1

Status: `independent-review-passed; user-confirmation-pending`

This is the resolved, low-context taste release. Evidence and historical feedback remain
in `docs/taste-model/` and are read only when a decision is disputed.

## Editorial Thesis

Make internet-native talking-head videos that feel authored by a top editor: direct,
legible, rhythmically alive, visually concrete, and commercially credible. Motion serves
meaning. Empty technique, generic AI gloss, and presentation-like information panels are
failures even when technically polished.

## Hard Invariants

- Landscape `1920x1080`, `60fps`, source-quality final, unless the episode explicitly
  overrides delivery.
- Every applicable real-media source is retimed exactly once to `1.1x`.
- Source order is authoritative. Trim only low-head starts, pre/post speech silence, and
  verified dead air. Preserve intentional tail gestures and jokes.
- A meaningful visual change occurs before ten unchanged seconds.
- The first five seconds are designed as the survival window, including action-bound
  sound where useful.
- Presenter continuity is preferred. Do not turn an opening close-up into a small window
  or remove the person behind a PPT-like full screen without a content reason.
- Body captions use the locked system-font bilingual preset after the opening hook.
  During the first-five survival window, do not stack body subtitles under display
  type: use only selective, traceable display words.
- New covers are rendered with ImageGen in both `4:3` and `3:4`.
- Red is excluded from designed palettes by default.
- No gradient haze, glow blobs, generic neon, or ornamental AI atmosphere.
- Never trade editorial, visual, motion, asset, subtitle, or review quality for speed.
  Save time through parallelism, caching, deterministic tooling, and earlier continuous previews.

## Visual Hierarchy

- Build a clear foreground, presenter plane, and background plane.
- Large display type may pass behind or in front of the presenter, but every important
  word remains inferable and faces remain readable.
- Keep some foreground text persistent when it strengthens the argument.
- Use horizontal typography. Never stack Chinese text vertically.
- The opening may start wide and move close, or start close and move wide. Camera
  movement follows speech pressure, not a fixed intro recipe.
- A sudden push-in lands and stays unless the shot contract explicitly motivates a
  return.
- A slow push-in, a fast punch-in, and a second-stage push-in are distinct tools.
- Full-screen B-roll is preferred when the material itself is the evidence. Picture in
  picture is for comparison or continued presenter presence, not as a default frame.
- Portrait windows preserve the original vertical frame width as the window's horizontal
  content extent. Do not crop the face into a square or fill unused height with blurred
  duplicate bands. Corners are rounded.

## Motion Language

- Each important shot has one primary movement.
- Stable high-value combination: motivated 3D perspective tilt, layered parallax, depth
  focus, and a restrained camera push.
- Available language includes: depth pull, focus rack, mask reveal, container morph,
  match transition, card stack, speed blur, scale-to-scene, spotlight focus, vignette
  focus, white-flash/exposure transition, light-leak transition, and optical bloom only
  when a real transition source motivates it.
- Text may rise from the bottom, pass behind the presenter, hold as a foreground anchor,
  or blur as a new layer takes priority.
- Avoid uniform entrances. Some phrases cut on, some fade, some move, and some remain
  still.
- Avoid bounce, comedy motion, repeated shake, arbitrary rotation, and multiple effects
  competing in one shot.
- Use Lottie, GSAP, licensed footage, or a real icon when they express the noun or action
  better than hand-built HTML/SVG. Search before fabricating a real-world object.

## Information Design

- Do not write `A-roll` or editing labels on screen.
- Keep designed copy shorter than spoken captions.
- Relationships, numbers, and business models need explicit structure, readable
  connections, and a verified landed frame.
- Do not cover a complete idea with the next headline.
- A visual metaphor should show the actual noun or process: money needs money, a first
  bucket of gold needs a credible bucket/coin asset, water and tokens need a readable
  transfer.
- Leave intentional negative space. Not every region needs an effect.

## Color and Material

- Use designer-level flat palettes with one structural accent and at most one semantic
  accent.
- Opening display-type colors are chosen per episode from the footage, skin tone,
  meaning, and contrast. Do not freeze white, yellow, orange, or any other hue as the
  universal opening palette.
- Dark stage is allowed; pure black is reserved for credits or an explicit black-stage
  reason.
- Preserve real footage color. Correct exposure, white balance, and contrast; do not
  recolor evidence.
- Frosted glass is a contextual material, not a default card. It must preserve the
  underlying scene and readable contrast.
- Shadows add separation, not cartoon outlines. Avoid dirty, dark, or muddy covers.

## Sound

- Speech is dominant.
- SFX must be caused by a visible action or clear editorial event.
- Use clicks, page turns, cash-register chimes, whooshes, impacts, optical flashes, and
  mechanical layers only when synchronized to the event.
- Do not add a generic mechanical clack to every fast transition.
- Music and SFX require provenance and commercial-use status.

## Negative Space and Restraint

- Text-only is not automatically simple; it can be empty.
- Stillness is useful after motion has landed.
- No-treatment shots are valid when the presenter, joke, gesture, or source material is
  already the strongest image.
- Fewer half-screen panels. Prefer full presenter, full evidence, or a deliberate
  comparison.

## Acceptance Question

At normal playback, can a viewer understand what changed, why it changed, and where their
attention should land without noticing the software?
