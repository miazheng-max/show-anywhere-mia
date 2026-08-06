# Show Anywhere (Mia)

**Make presentations that look designed, run anywhere, and fit a phone screen.**

An agent skill for [Claude Code](https://claude.com/claude-code) and [OpenAI Codex CLI](https://developers.openai.com/codex/cli). Give it a topic, an article, a PDF, or a `.pptx` — pick a look from a visual gallery — get back a single self-contained HTML file you can open in any browser, edit by clicking on the text, and share as a link.

<p align="center">
  <img src="docs/demo.gif" alt="Browsing the style gallery, filtering by mood, picking Cobalt Grid, and the resulting portrait deck" width="100%">
</p>

## Why this one

**📱 Portrait by default.** The canvas is 1080×1920 (9:16) unless you ask for widescreen. Most decks get read on a phone now, not projected — so that's the default, and the skill knows how to *re-author* a landscape design system into a vertical one rather than just squashing it.

**🎨 You pick the look by seeing it.** 46 complete design systems ship in the box. The skill renders them all as a searchable, filterable gallery — real palettes in their real display fonts — so you choose by sight instead of typing "make it modern but warm" and hoping.

**✍️ Click any text to edit it.** No edit mode, no toggle button to hunt for. Every text element is editable the moment the deck loads; changes autosave to your browser.

**🀄 Chinese that doesn't look machine-made.** Full-width punctuation, proper CJK line-height, no uppercase transforms on Hanzi, spacing between Hanzi and Latin runs. Same for Japanese and Korean.

**📦 One file, zero dependencies.** Inline CSS/JS, images embedded as data URIs. Email it, host it, open it offline.

**📤 Export to PDF or a public link.** PDF export reads the deck's own canvas size, so portrait decks export as portrait pages — no flag to remember. Publishing to a URL always asks first.

## Install

The skill is one folder. Drop it where your agent looks for skills.

### Claude Code

```bash
git clone https://github.com/miazheng-max/show-anywhere-mia.git ~/.claude/skills/show-anywhere-mia
```

Then invoke it with `/show-anywhere-mia`, or just ask for a deck and it will trigger on its own.

### Codex CLI

```bash
git clone https://github.com/miazheng-max/show-anywhere-mia.git ~/.codex/skills/show-anywhere-mia
```

For a project-local install, use `.codex/skills/show-anywhere-mia` inside the repo instead. Codex also reads `~/.agents/skills/` if you keep skills shared across agents.

### Requirements

- Python 3.8+ — standard library only for generating decks and the gallery

Optional, only for the feature that needs it:

| Feature | Needs |
| --- | --- |
| `.pptx` conversion | `pip install python-pptx` |
| PDF export | `pip install playwright && python3 -m playwright install chromium` |
| Publish to a URL | Node.js + a free [Vercel](https://vercel.com) account |

No other companion skill is required. Everything the skill reads is inside this repo.

## How it works

```
You: turn this article into a mobile deck in Chinese

  1  Content     → reads your source, asks purpose / length / density
  2  Style       → renders the gallery, you browse and name a style
  3  Generate    → loads exactly that one design system, builds the deck
  4  Verify      → checks every slide for overflow, overlap, broken images
  5  Deliver     → one HTML file + what got left out and why
  6  Share       → PDF or a public URL, if you ask for it
```

Step 2 is the point. The gallery is a real HTML page with search, mood filters, and a preset/library toggle:

<p align="center">
  <img src="docs/gallery.png" alt="The style gallery: 46 design systems as color-swatch cards, each in its own display font" width="100%">
</p>

## What's in the box

| | |
| --- | --- |
| **12 curated presets** | Bold Signal, Electric Studio, Creative Voltage, Dark Botanical, Notebook Tabs, Pastel Geometry, Split Pastel, Vintage Editorial, Neon Cyber, Terminal Green, Swiss Modern, Paper & Ink |
| **34 full design systems** | Complete design docs — palette, type scale, component grammar, CJK pairings — for templates like Cobalt Grid, Biennale Yellow, Retro Zine, Emerald Editorial, Sakura Chroma, and 29 more |

Each design system is a full specification, not a color preset — which is why a generated deck holds together across title, section, data, quote, and closing slides instead of drifting.

## Repo layout

```
show-anywhere-mia/
├── SKILL.md                       # the skill itself
├── template-pack/
│   ├── selection-index.json       # compact metadata for all 34 systems
│   └── templates/<slug>/
│       ├── design.md              # full design system
│       └── preview.md             # lightweight style card
├── reference/
│   ├── STYLE_PRESETS.md           # the 12 curated presets
│   ├── viewport-base.css          # mandatory fixed-stage CSS
│   ├── html-template.md           # HTML/JS architecture
│   └── animation-patterns.md      # animation snippets by feeling
├── scripts/
│   ├── render-gallery.py          # renders the style gallery
│   ├── build-gallery-data.py      # extracts palettes/fonts from design docs
│   ├── extract-pptx.py            # .pptx → text + images
│   ├── export-pdf.py              # deck → PDF, auto-detects canvas size
│   └── deploy.sh                  # deck → public URL (asks first)
├── assets/
│   └── gallery-template.html      # gallery shell
└── docs/
    ├── demo.gif                   # the README demo
    ├── demo-deck.html             # the 3-slide sample deck in the demo
    └── capture-demo.py            # regenerates the GIF (needs playwright)
```

## Try the gallery on its own

You don't need an agent to look at the styles:

```bash
python3 scripts/render-gallery.py /tmp/style-gallery.html && open /tmp/style-gallery.html
```

## Credits

Built on two MIT-licensed projects by [Zara Zhang](https://github.com/zarazhangrui):

- [**frontend-slides**](https://github.com/zarazhangrui/frontend-slides) — the fixed-stage layout model, style presets, and anti-AI-slop design philosophy this skill is built around.
- [**beautiful-html-templates**](https://github.com/zarazhangrui/beautiful-html-templates) — the 34 bundled design systems.

`show-anywhere-mia` bundles these into a single self-contained skill and adds the visual style gallery, portrait-first defaults, cross-agent portability, expanded CJK typography, and always-on inline editing. See [NOTICE](NOTICE) for exactly what was taken and what was changed.

## License

[MIT](LICENSE).
