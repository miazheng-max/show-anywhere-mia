#!/usr/bin/env python3
"""
Regenerates gallery-data.json from the design systems bundled inside this
skill: the 34 template-pack design systems (colors + display font, parsed
straight out of each template's design.md frontmatter) plus the 12 curated
STYLE_PRESETS.md entries (hardcoded below, since that file is prose/markdown
rather than structured data).

Self-contained: reads only from this skill's own `template-pack/` directory,
so it works the same whether the skill is installed under ~/.claude/skills/,
~/.codex/skills/, ~/.agents/skills/, or a project-local .codex/skills/.

Usage:
    python3 build-gallery-data.py

Output: gallery-data.json in the skill root (a build artifact — regenerate it
rather than editing it by hand or committing a stale copy).
"""
import json
import os
import re

SKILL_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PACK_DIR = os.path.join(SKILL_DIR, "template-pack")


def clean_font(name):
    return name.strip().strip("'").strip('"')


def extract_template_colors(design_md_path):
    """Pulls the `colors:` block and a couple of fontFamily values out of a
    template design.md's YAML frontmatter, without needing a full YAML parser
    (the frontmatter here is simple enough for a regex pass)."""
    try:
        with open(design_md_path, encoding="utf-8") as f:
            content = f.read()
    except FileNotFoundError:
        return {}, []

    m = re.match(r"^---\n(.*?)\n---\n", content, re.DOTALL)
    if not m:
        return {}, []
    frontmatter = m.group(1)

    colors = {}
    cm = re.search(r"^colors:\n((?:  .+\n?)+)", frontmatter, re.MULTILINE)
    if cm:
        for line in cm.group(1).splitlines():
            lm = re.match(r'\s+([\w-]+):\s*"?(#[0-9a-fA-F]{3,8}|rgba?\([^)]*\))"?', line)
            if lm:
                colors[lm.group(1)] = lm.group(2)

    seen = []
    for fam in re.findall(r'fontFamily:\s*"([^"]+)"', frontmatter):
        first = fam.split(",")[0].strip()
        if first not in seen:
            seen.append(first)
    return colors, seen[:2]


def build_bold_entries():
    index_path = os.path.join(PACK_DIR, "selection-index.json")
    if not os.path.isfile(index_path):
        raise SystemExit(
            "Missing template-pack/selection-index.json at {}. The skill's "
            "bundled design systems appear to be incomplete — reinstall the "
            "skill directory in full.".format(index_path)
        )
    with open(index_path, encoding="utf-8") as f:
        index = json.load(f)

    entries = []
    for t in index["templates"]:
        design_md = os.path.join(PACK_DIR, "templates", t["slug"], "design.md")
        colors, fonts = extract_template_colors(design_md)

        seen, swatches = [], []
        for c in colors.values():
            if c.startswith("rgba") or c in seen:
                continue
            seen.append(c)
            swatches.append(c)
        if not swatches:
            swatches = ["#cccccc"]

        entries.append({
            "slug": t["slug"],
            "name": t["name"],
            "tagline": t["tagline"],
            "mood": t["mood"],
            "formality": t["formality"],
            "scheme": t["scheme"],
            "colors": swatches[:5],
            "font": clean_font(fonts[0]) if fonts else "Georgia",
            "kind": "bold",
        })
    return entries


# The 12 reference/STYLE_PRESETS.md entries. That file is prose (vibe/layout/
# typography in free text plus a CSS code block per preset), not structured
# data, so these are transcribed by hand rather than regex-parsed. Re-check
# this list against reference/STYLE_PRESETS.md if its preset roster changes.
PRESET_ENTRIES = [
    dict(slug="bold-signal", name="Bold Signal", tagline="Colored card on dark gradient, oversized section numbers, breadcrumb nav.",
         mood=["confident", "bold", "modern", "high-impact"], formality="medium", scheme="dark",
         colors=["#1a1a1a", "#2d2d2d", "#FF5722", "#ffffff"], font="Archivo Black"),
    dict(slug="electric-studio", name="Electric Studio", tagline="White-over-blue split panel with quote typography as the hero element.",
         mood=["bold", "clean", "professional", "high-contrast"], formality="medium-high", scheme="mixed",
         colors=["#0a0a0a", "#ffffff", "#4361ee"], font="Manrope"),
    dict(slug="creative-voltage", name="Creative Voltage", tagline="Electric blue and neon yellow, halftone texture, script accents.",
         mood=["bold", "creative", "energetic", "retro-modern"], formality="low", scheme="dark",
         colors=["#0066ff", "#1a1a2e", "#d4ff00", "#ffffff"], font="Syne"),
    dict(slug="dark-botanical", name="Dark Botanical", tagline="Blurred soft gradient circles on near-black, warm pink and gold accents.",
         mood=["elegant", "sophisticated", "artistic", "premium"], formality="high", scheme="dark",
         colors=["#0f0f0f", "#d4a574", "#e8b4b8", "#c9b896", "#e8e4df"], font="Cormorant"),
    dict(slug="notebook-tabs", name="Notebook Tabs", tagline="Cream paper card on charcoal, colorful vertical tabs down the right edge.",
         mood=["editorial", "organized", "elegant", "tactile"], formality="medium-high", scheme="mixed",
         colors=["#2d2d2d", "#f8f6f1", "#98d4bb", "#c7b8ea", "#f4b8c5"], font="Bodoni Moda"),
    dict(slug="pastel-geometry", name="Pastel Geometry", tagline="White card on pastel field, tall-to-short pill tabs along the edge.",
         mood=["friendly", "organized", "modern", "approachable"], formality="medium", scheme="light",
         colors=["#c8d9e6", "#faf9f7", "#f0b4d4", "#a8d4c4", "#7c6aad"], font="Plus Jakarta Sans"),
    dict(slug="split-pastel", name="Split Pastel", tagline="Peach-and-lavender vertical split with playful icon badges.",
         mood=["playful", "modern", "friendly", "creative"], formality="low", scheme="light",
         colors=["#f5e6dc", "#e4dff0", "#c8f0d8", "#f0d4e0"], font="Outfit"),
    dict(slug="vintage-editorial", name="Vintage Editorial", tagline="Cream ground, witty conversational copy, geometric line-and-dot accents.",
         mood=["witty", "confident", "editorial", "personality-driven"], formality="medium", scheme="light",
         colors=["#f5f3ee", "#1a1a1a", "#e8d4c0"], font="Fraunces"),
    dict(slug="neon-cyber", name="Neon Cyber", tagline="Deep navy void, cyan-and-magenta neon glow, particle field backdrop.",
         mood=["futuristic", "techy", "confident"], formality="medium", scheme="dark",
         colors=["#0a0f1c", "#00ffcc", "#ff00aa"], font="Clash Display"),
    dict(slug="terminal-green", name="Terminal Green", tagline="GitHub-dark terminal with scan lines and a blinking cursor.",
         mood=["developer-focused", "hacker", "technical"], formality="low", scheme="dark",
         colors=["#0d1117", "#39d353"], font="JetBrains Mono"),
    dict(slug="swiss-modern", name="Swiss Modern", tagline="Bauhaus-inspired grid, pure black and white, one red accent.",
         mood=["clean", "precise", "bauhaus", "structural"], formality="high", scheme="light",
         colors=["#ffffff", "#0d0d0d", "#ff3300"], font="Archivo"),
    dict(slug="paper-ink", name="Paper & Ink", tagline="Warm cream page, drop caps and pull quotes, a single crimson accent.",
         mood=["editorial", "literary", "thoughtful"], formality="high", scheme="light",
         colors=["#faf9f7", "#1a1a1a", "#c41e3a"], font="Cormorant Garamond"),
]


def main():
    bold_entries = build_bold_entries()

    all_entries = [{**p, "kind": "preset"} for p in PRESET_ENTRIES]
    all_entries.extend(bold_entries)

    out_path = os.path.join(SKILL_DIR, "gallery-data.json")
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(all_entries, f, ensure_ascii=False, separators=(",", ":"))

    print(f"Wrote {len(all_entries)} entries "
          f"({len(PRESET_ENTRIES)} presets + {len(bold_entries)} templates) to {out_path}")


if __name__ == "__main__":
    main()
