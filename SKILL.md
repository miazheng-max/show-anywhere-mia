---
name: show-anywhere-slide
description: Build beautiful, self-contained HTML presentations that run in any browser — mobile-first 9:16 portrait by default, widescreen 16:9 on request. Bundles 46 complete design systems (12 curated presets + 34 full template design docs) and a browsable visual style gallery, so the user picks a look by sight instead of describing it in words. Use when the user wants to make a deck, slides, presentation, PPT, 演示文稿, or 手机端PPT; wants to convert a .pptx or an article/PDF into slides; wants to browse or compare visual styles/templates; or asks for a "style gallery". Handles Chinese and other CJK content with correct typography. Everything needed is bundled — no companion skill required.
---

# Show Anywhere (Mia)

Turn content into a presentation that looks designed, runs as a single HTML file, and works on a phone.

Two things make this different from asking an agent to "make me some slides":

1. **You pick the look by seeing it.** A browsable gallery of all 46 bundled design systems — real color swatches in their real display fonts — instead of the agent guessing your taste from two adjectives.
2. **Portrait-first.** The default canvas is 1080×1920 (9:16), sized for a phone screen, because most decks now get read on a phone rather than projected. Widescreen is one sentence away when you want it.

## Core Principles

1. **Zero dependencies** — one self-contained HTML file, all CSS/JS inline. No npm, no build step, no framework.
2. **Show, don't tell** — people discover what they want by looking, not by describing.
3. **Distinctive design** — no generic "AI slop": no Inter/Roboto/Arial, no purple-gradient-on-white, no cookie-cutter card grids.
4. **Progressive disclosure** — read the compact index first; load exactly one full `design.md` after the user picks. Never bulk-read design docs.
5. **Fixed stage, never reflow** — every slide is authored at one canvas size and the whole stage is scaled to fit. Slides letterbox/pillarbox; they never re-layout per device.

## What's Bundled

| Path | What it is |
| --- | --- |
| `template-pack/selection-index.json` | Compact metadata for all 34 template design systems — read this first |
| `template-pack/templates/<slug>/design.md` | One complete design system (palette, type scale, components, CJK guidance). Read **one**, only after the user picks |
| `template-pack/templates/<slug>/preview.md` | Lightweight style card for quick previews |
| `reference/STYLE_PRESETS.md` | The 12 curated presets (vibe/layout/typography/colors) |
| `reference/viewport-base.css` | Mandatory fixed-stage CSS — include its full contents in every deck |
| `reference/html-template.md` | HTML architecture and JS controller reference |
| `reference/animation-patterns.md` | CSS animation snippets by feeling |
| `scripts/render-gallery.py` | Renders the browsable style gallery |
| `scripts/extract-pptx.py` | Extracts text/images from a .pptx for conversion |
| `scripts/export-pdf.py` | Exports a finished deck to PDF, one page per slide |
| `scripts/deploy.sh` | Publishes a deck to a public URL (Vercel) |

---

## Phase 0 — Detect Mode

- **New deck** from a topic, notes, article, or PDF → start the Four Questions.
- **Convert a .pptx** → PPTX Conversion below, then rejoin at Q3 (style).
- **Edit an existing deck** made by this skill → Modifying an Existing Deck.

---

## The Four Questions — the entire intake flow

The user answers exactly **four questions** before generation starts. Nothing else is asked unless something is genuinely blocking.

**Ask every question in the language the user is writing in.** A user typing Chinese gets the questions in Chinese; English gets English. The wording below is a reference, not a fixed script — translate naturally.

| # | Question | When |
|---|---|---|
| 1 | **Purpose** — what is this for? | Asked together with Q2, first message |
| 2 | **Density** — detail-rich or concise? | Asked together with Q1 |
| 3 | **Style** — pick a palette from the gallery | After Q1+Q2; render the gallery, then stop and wait |
| 4 | **Output** — HTML or PDF? | Right after the style is chosen, before generating |

Do **not** ask about: slide count (derive it from the content and the density answer), orientation (portrait 9:16 is the default; only switch to 16:9 if the user themselves asks for widescreen/projector), or inline editing (always on).

### Q1 — Purpose

> What will this deck be used for?
> - Marketing / promotion
> - Training / explanation
> - Talk / pitch on stage
> - Internal report
> - Something else (tell me)

### Q2 — Content density

> Which shape fits better?
> - **Detail-rich** — more like ~6+ self-contained pages the reader can study on their own
> - **Concise for speaking** — fewer words, bigger type, you talk over it

Ask Q1 and Q2 together in one message (use the host's structured-question UI if it has one). Skip anything the user already said.

If the user supplied source material (article, PDF, notes), read it before proposing an outline.

### Handling source images

If the source has images worth keeping:

1. Extract them (`pdfimages`, PyMuPDF, or the pptx script) and **look at each one**.
2. Judge each: usable or not, what concept it carries, and — importantly — **whether it's safe to republish**. Screenshots containing real names, email addresses, phone numbers, or account details must be excluded or redacted. Say so rather than silently dropping them.
3. Design slides *around* the surviving images, don't bolt them on afterward.
4. Downscale to ~900px wide, then inline as `data:` URIs so the deck stays one portable file.

---

## Q3 — Style (the gallery)

Render the gallery to a temp path (never into the user's project), passing the conversation's language:

```bash
python3 <skill-dir>/scripts/render-gallery.py <temp-dir>/style-gallery.html --lang zh   # or --lang en
```

This regenerates `gallery-data.json` fresh from the bundled design systems, then produces one self-contained HTML file with search, mood-tag filters, a preset/library toggle, and an **EN/中 language switch** — the interface, every card's description, and all tags render fully in either language. The full gallery is also pre-rendered into the HTML in the `--lang` language, so even a viewer that never runs JavaScript still sees every card.

**Then get it in front of the user so it opens on its own — they must not have to click a file attachment.** In order:

1. **Host has a publish/artifact tool (e.g. Claude Code's `Artifact`) → use that tool, and only that tool.** It is what makes the page appear in the user's side panel automatically, with JavaScript running. **Never deliver the gallery as a plain file attachment or point the user at a local file path when an artifact tool exists** — Claude Code's file preview renders local HTML as a static snapshot (no JS: search, filters, language toggle and selection are all dead, and before pre-rendering existed the page showed up completely blank). A file chip the user has to click is exactly the failure mode this rule exists to prevent.
2. No artifact tool → open it locally yourself: `open <path>` (macOS), `xdg-open <path>` (Linux), `start <path>` (Windows).
3. Neither works (headless/remote) → give the file path and describe 4–6 styles that fit their brief in text, so they can still choose.

Tell them: search or filter by mood, click a card to select, copy the name (or just type it), and paste it back in chat.

**Then stop and wait.** Do not pick for them. Do not start generating.

> Prefer the gallery. Fall back to describing 3 AI-picked options only if rendering genuinely fails.

## Q4 — Output format

The moment the user names a style, ask the last question (again in their language):

> How do you want the result?
> - **HTML (recommended)** — opens in any browser, and you can click any text to edit it afterwards
> - **PDF** — a downloadable static file for sending or printing; text is not editable

Do not offer "deploy to a public URL" as one of these options. Deployment exists (`scripts/deploy.sh`) but only happens if the user later explicitly asks for a shareable link.

If they choose PDF: still generate the HTML deck first (it is the source of truth), then export it with `scripts/export-pdf.py` and deliver the PDF as the primary artifact.

With all four answers in hand, generate.

---

## Generate

Once the user names a style:

1. Look up its `kind` in `gallery-data.json`.
2. `kind: bold` → read **that one** `template-pack/templates/<slug>/design.md` in full. Never read others.
3. `kind: preset` → read that entry's section in `reference/STYLE_PRESETS.md`.
4. Read `reference/viewport-base.css` and include its **entire** contents in the deck's `<style>`.

Treat the design doc as the recipe: keep its palette, fonts, spacing rhythm, decorative vocabulary, and component grammar. Don't copy its demo content.

### Fixed-stage rules (non-negotiable)

- Author every slide at the chosen canvas — **1080×1920 portrait** (default) or 1920×1080 landscape.
- Scale the whole stage with a single `transform`; letterbox/pillarbox as needed.
- Never use responsive breakpoints to rearrange slide content.
- Use fixed px measurements at canvas scale. `clamp()` only for UI outside the stage.
- Switch slides with `.active`/`.visible` (visibility/opacity/pointer-events) — **never** `display:none`, which later layout rules can override into showing every slide at once.
- Never negate a CSS function directly (`-clamp(...)` is silently ignored) — use `calc(-1 * clamp(...))`.
- Include `prefers-reduced-motion` support.

### Portrait conversion — the part that goes wrong

Every bundled design system was authored for landscape region-splits (side-by-side columns, left/right panels). Portrait is a **re-authoring**, not a resize. Three failure modes, in priority order:

**1. Dead space at the bottom.** A region sized for a 1080px-tall canvas leaves ~800px empty on a 1920px-tall one. Fix by going *bigger* before going *centered*:

| Element | Timid first pass | Actually correct |
| --- | --- | --- |
| Headline | 40–48px | **72–80px** |
| Decorative numerals / accents | 20–24px | **60–64px** |
| Eyebrow / label | 12–14px | **20px** |
| Body / card text | 14–16px | **22–24px** |

Spacing follows the same logic: *tight* (~12px) between lines inside one component, *loose* (24–32px) between sibling components. Not one uniform gap everywhere.

**2. Wrong alignment mode.** This is content-dependent — don't apply one rule to the whole deck:
- `justify-content: center` when the body is **one cohesive visual block** (a card grid, a diagram, a single big stat). It has enough graphic weight to read as a deliberate centered hero.
- `justify-content: flex-start` (flush under the headline, ~24–28px gap) when the body is **sequential content read in order** — numbered steps, a timeline, dialogue. Reading order beats vertical balance.

**3. Loose footer.** Pin footer chrome ~30–40px from the bottom edge. Use the canvas nearly edge to edge.

Only add more content beats as a last resort, and prefer splitting into two slides over stretching blocks apart to fake height.

**Multi-column comparisons** (before/after, vague vs. exact) become a **vertical stack** in portrait. Never force a cramped two-column grid at 1080px wide.

### Density

- **Speaker-led** — more slides, fewer ideas each, large type, section beats, quote slides.
- **Reading-first** — self-contained slides, structured grids, comparison tables, annotated diagrams, concise explanatory copy.

Baseline always applies: no scrolling, no overflow, no overlapping panels, nothing below comfortable reading size. If a slide overflows, split it — never shrink until cramped.

### CJK content

When the deck is Chinese/Japanese/Korean, follow the chosen design doc's CJK section, plus:

- Pair the Latin display font with a CJK face in the same stack (e.g. `"Newsreader","Noto Serif SC",serif`) so Latin and Hanzi each render correctly.
- Body line-height ~1.7 (up from 1.5). Zero out `letter-spacing` on Hanzi runs; keep tracking only on Latin spans.
- Drop `text-transform: uppercase` on Hanzi — Chinese has no case.
- **Full-width punctuation** in Chinese sentences: `，。：；？（）「」` and curly quotes `“”`. Never half-width `,.:;?()` inside a Chinese sentence. This is the single most common tell of a machine-made Chinese deck.
- No terminal `。` on display headlines.
- Insert a space between adjacent Hanzi and Latin/digit runs (`2026 年`, `AI 语境`).
- Don't switch CJK families mid-sentence.

### Inline editing — always on, never a toggle

Set `contenteditable="true"` on every text element **at load**. Do not build a hover hotzone or an edit-mode toggle button: toggle clicks can silently fail to register, and the user just sees a deck that "can't be edited" with no error.

- Debounce-save on `input`; save immediately on `blur` — **capture phase**, since contenteditable elements don't bubble blur.
- Persist to `localStorage` under a deck-specific key; restore on load.
- `Ctrl/Cmd+S` for a manual save with a toast.
- Show a small non-interactive badge ("✎ click any text to edit") — not a button.
- Guard navigation: wheel/touch/arrow-key handlers must ignore events originating inside an editable element, or typing will flip slides.

### Navigation

Keyboard (arrows/space/PageUp/PageDown), mouse wheel, and touch swipe. Debounce ~700ms per step and clamp at the first/last slide.

---

## PPTX Conversion

```bash
python3 <skill-dir>/scripts/extract-pptx.py <input.pptx> <output_dir>
```

(needs `python-pptx`). Show the user the extracted titles and image count to confirm, then continue from Q3 (style). Preserve text, images, slide order, and speaker notes (as HTML comments).

---

## Modifying an Existing Deck

Fitting is the main risk. Before adding anything, count what's already on the slide.

- Adding text → max 4–6 bullets per slide; beyond that, make a continuation slide.
- Adding an image → if the slide is already full, move it to its own slide. Never just append.
- After **any** change, re-verify overflow and overlap (below).
- If a change will cause overflow, reorganize proactively and tell the user what you split.

---

## Verification — before you call it done

Do not report success off a single screenshot, and do not trust the design doc's prose over what the page actually looks like.

1. **Geometry check** — for each slide, compare the content's `getBoundingClientRect().bottom` against its container's. Anything positive is overflow.
2. **Look at every slide.** Screenshot each one and actually inspect it. Numbers can't catch a decoration that renders as broken bars, a chart legend colliding with a caption, or a figure that reads as an empty box.
3. **Check images loaded** — `img.complete && img.naturalWidth > 0` for all.
4. **Decorative SVG needs the same scrutiny as text.** A pattern that's "correct" per the design doc can still read as a rendering bug (stair-stepped scanlines look like broken lines, not an effect). If it looks broken, it *is* broken — replace it.
5. If a screenshot and the geometry numbers disagree, investigate rather than believing the convenient one. A blank screenshot after many rapid resize/navigate calls is usually a tool compositing glitch — reload in a fresh tab and re-check before "fixing" a non-bug.

---

## Delivery

Tell the user:

- Where the file is, which style, how many slides, and the canvas size.
- Navigation: arrows / space / scroll / swipe.
- Editing: click any text; `Ctrl/Cmd+S` to save; changes persist in that browser.
- How to customize: `:root` CSS variables for color, the font `<link>` for typography.
- **What you left out and why** — e.g. images skipped for containing personal data.

If the host has a publish/artifact tool, **publish the deck through it — never hand the deck over as a plain file attachment**. The same static-snapshot rule as the gallery applies, and it bites harder here: a no-JS preview of a deck shows only the first slide, with no navigation and no click-to-edit, which the user reads as "the deck is broken". The artifact tool is what makes it open in their side panel automatically with everything working. When publishing, strip the `<!DOCTYPE>`/`<html>`/`<head>`/`<body>` wrapper if the host supplies its own skeleton, and make sure every image is an inlined `data:` URI, since a published page can't read local disk.

The output format was already settled by Q4 — deliver that. Afterwards, offer revisions; mention a shareable public link only if the user brings it up.

---

## Export and Share

### PDF (runs automatically when Q4 = PDF; also available on request later)

```bash
python3 <skill-dir>/scripts/export-pdf.py <deck.html> [output.pdf] [--compact]
```

Needs `pip install playwright && python3 -m playwright install chromium` (first run downloads ~150 MB of Chromium; warn the user it takes a minute).

It reads the canvas size off the deck's own `.deck-stage`, so a portrait deck produces portrait pages and a landscape deck landscape pages — no flag to set. Animations are flattened to their final state, which is expected for a static file; say so rather than letting the user discover it. `--compact` renders at 2/3 scale for a noticeably smaller file. If the result is over ~10 MB, offer `--compact` instead of silently shipping something too big to email.

### Public URL

```bash
bash <skill-dir>/scripts/deploy.sh <deck.html | deck-folder/>
```

**Publishing is outward-facing and effectively irreversible — a URL can be cached or indexed even after you delete the project. Never run this on your own initiative.** Require an explicit, specific request to publish *this* deck; agreement to build a deck is not agreement to publish it. The script prompts for confirmation on its own; do not pass `--yes` to route around that prompt unless the user has just told you to publish in this conversation.

Before deploying, re-read the deck for anything that shouldn't be public — client names, unreleased numbers, personal data in screenshots — and raise it rather than assuming it was intended.

Needs Node.js and a free Vercel account. If the user isn't logged in, the script walks them through it; they complete the login themselves.

---

## Anti-Slop Reminders

You converge on safe, generic choices unless you push against it:

- Vary across generations. If you keep reaching for the same font (Space Grotesk is a known attractor), pick something else.
- Commit to a dominant color with sharp accents rather than an evenly-distributed timid palette.
- Give backgrounds atmosphere — layered gradients, geometric structure, texture — not flat fills.
- Spend animation budget on one well-orchestrated staggered load, not scattered micro-interactions.
- Never render workflow text on a slide: no "preview", "Option A", "template", "safe choice", file paths, or the user's own requirement notes.
