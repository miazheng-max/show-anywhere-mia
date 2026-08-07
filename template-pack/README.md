# Bold Template Pack

This pack brings the `beautiful-html-templates` design systems into the
`show-anywhere-slide` skill without making them the default for every deck.

## What To Read

1. Read `template-pack/selection-index.json` first.
2. Shortlist candidates from metadata only:
   - `mood`
   - `tone`
   - `best_for`
   - `avoid_for`
   - `formality`
   - `density`
   - `scheme`
3. For title-slide previews, read only the relevant candidate `preview.md`
   files.
4. After the user chooses a bold template, read exactly that one template's
   full `design.md`.
5. Do not read every `design.md` in the pack.
6. Do not read or copy `template.html` from the source template library unless a
   selected `design.md` is missing a critical implementation detail.

The full source metadata index is not bundled in the user-facing skill. Normal
generation should use `selection-index.json` only.

## How To Use In Frontend Slides

Preview mix:

- 1 safe option from `STYLE_PRESETS.md`
- at least 1 bold option from this pack
- 1 wildcard option, which may be another bold template from this pack or a
  self-generated custom design

Adjust the tone inside that default mix:

- For board, legal, regulatory, healthcare, investor-update, or highly formal
  internal decks, make the safe option very restrained and choose calmer,
  higher-formality bold templates. The wildcard should feel authoritative and
  specific, not merely decorative.
- For bold, editorial, expressive, experimental, or highly designed decks, keep
  the safe option as a readable fallback, choose one strong bold template, and
  use the wildcard for either a second adventurous template or a custom design
  that better matches the user's occasion and vibe.

If the wildcard is custom, it must follow the skill's no-slop aesthetics:
distinctive typography, a committed palette, a recognizable layout system, a
context-specific visual idea, fixed-stage behavior, and no visible process
labels such as "custom", "wildcard", "template", or "preview".

## Implementation Contract

`design.md` is the design-system reference. Treat it as a style recipe, not as
content to copy. `preview.md` is only a lightweight style card for generating
the three title-slide options.

Preview slides must be real title slides for the user's deck. Do not render
template names, option labels, file names, paths, `preview.md`, "generated
from", or user requirement notes on the slide itself.

When generating final slides:

- Keep generated deck output as one self-contained HTML file.
- Include the full contents of `reference/viewport-base.css`.
- Generate every deck as a fixed stage scaled uniformly to the viewport:
  **1080×1920 portrait by default**, or 1920×1080 landscape when the user
  asks for widescreen. This applies even if the source template was
  originally viewport-fluid.
- Treat `vw`, `vh`, and `clamp()` values in a source `design.md` as design
  proportions to translate into fixed stage coordinates.
- These design systems were authored for landscape region-splits. Targeting
  portrait means re-authoring side-by-side regions as vertical stacks — see
  the portrait conversion rules in `SKILL.md`, not a uniform down-scale.
- Preserve the selected template's fonts, palette, decorative vocabulary,
  spacing rhythm, and component grammar.
- Keep the user's actual slide content primary. The template style should shape
  presentation, not override message or structure.
- Verify rendered output for both text overflow and panel overlap. A card can
  pass `scrollHeight` checks while still being covered by another grid panel.
