#!/usr/bin/env python3
"""
Renders the browsable style gallery: regenerates gallery-data.json (by
running build-gallery-data.py fresh, so the gallery always reflects the
design systems currently bundled in this skill), then injects that data
plus a batched Google Fonts URL for every card's display font into
assets/gallery-template.html.

Usage:
    python3 render-gallery.py <output_path.html>

The output path is required — the skill instructs the agent to pass a
temp/scratch path so nothing is left behind in the user's project.
Output is one self-contained HTML file the user can open in any browser.
"""
import html
import json
import os
import re
import subprocess
import sys
import urllib.parse

SKILL_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCRIPTS_DIR = os.path.join(SKILL_DIR, "scripts")
TEMPLATE_PATH = os.path.join(SKILL_DIR, "assets", "gallery-template.html")
DATA_PATH = os.path.join(SKILL_DIR, "gallery-data.json")

# Fonts already loaded by the shell itself (masthead/chrome) — never
# request these again in the per-card query string even if a card also
# happens to use one of them.
SHELL_FONTS = {"Spectral", "Work Sans", "JetBrains Mono"}

# Fonts referenced by some templates/presets that Google Fonts doesn't
# serve (Fontshare exclusives, OS system faces). Cards using these fall
# back to the shell's serif display font — acceptable for a swatch card,
# since the real font shows up correctly once the actual deck is generated.
NOT_ON_GOOGLE_FONTS = {"Clash Display", "Satoshi", "MS Sans Serif", "Segoe UI"}


def build_data():
    cmd = [sys.executable, os.path.join(SCRIPTS_DIR, "build-gallery-data.py")]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        sys.stderr.write(result.stderr)
        raise SystemExit(result.returncode)
    sys.stderr.write(result.stdout)
    with open(DATA_PATH, encoding="utf-8") as f:
        return json.load(f)


def google_fonts_query(fonts):
    seen, families = [], []
    for f in fonts:
        name = f.strip()
        if not name or name in SHELL_FONTS or name in NOT_ON_GOOGLE_FONTS or name in seen:
            continue
        seen.append(name)
        families.append(name)
    parts = []
    for fam in sorted(families):
        parts.append("&family=" + urllib.parse.quote(fam.replace(" ", "+"), safe="+"))
    return "".join(parts)


def main():
    if len(sys.argv) < 2:
        raise SystemExit("Usage: render-gallery.py <output_path.html>")
    out_path = sys.argv[1]

    data = build_data()
    fonts_query = google_fonts_query(item["font"] for item in data)

    with open(TEMPLATE_PATH, encoding="utf-8") as f:
        template = f.read()

    # JSON is embedded inside a <script type="application/json"> block, not
    # an attribute — only the closing-tag sequence needs escaping so the
    # browser's HTML parser can't be tricked into ending the block early.
    data_json = json.dumps(data, ensure_ascii=False, separators=(",", ":"))
    data_json_safe = data_json.replace("</script", "<\\/script")

    rendered = template.replace("__CARD_FONTS_QUERY__", fonts_query)
    rendered = rendered.replace("__DATA__", data_json_safe)

    os.makedirs(os.path.dirname(os.path.abspath(out_path)) or ".", exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(rendered)

    print(f"Rendered {len(data)} styles to {out_path}")


if __name__ == "__main__":
    main()
