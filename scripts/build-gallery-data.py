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
            "tagline_zh": TAGLINE_ZH.get(t["slug"], t["tagline"]),
            "mood": t["mood"],
            "formality": t["formality"],
            "scheme": t["scheme"],
            "colors": swatches[:5],
            "font": clean_font(fonts[0]) if fonts else "Georgia",
            "kind": "bold",
        })
    return entries


# Chinese taglines for every entry, keyed by slug. The gallery ships a full
# EN/中 toggle, so每一张卡片的介绍都要有中文版。Hand-written, not machine
# output — keep them short and concrete. If a template is added without an
# entry here, the gallery falls back to its English tagline.
TAGLINE_ZH = {
    # 12 presets
    "bold-signal": "深色渐变上的彩色卡片，超大章节数字与面包屑导航。",
    "electric-studio": "蓝白分栏面板，引言排版本身就是主视觉。",
    "creative-voltage": "电光蓝配霓虹黄，半调网纹与手写体点缀。",
    "dark-botanical": "近黑底上的柔焦渐变光晕，暖粉与金色点缀。",
    "notebook-tabs": "炭黑底上的奶油纸卡，右缘一列彩色竖标签。",
    "pastel-geometry": "粉彩底上的白卡片，边缘高低错落的胶囊标签。",
    "split-pastel": "蜜桃与薰衣草的竖向对分，配俏皮图标徽章。",
    "vintage-editorial": "奶油底色，机智口语化文案，几何线点装饰。",
    "neon-cyber": "深海军蓝虚空，青与品红的霓虹辉光，粒子场背景。",
    "terminal-green": "GitHub 暗色终端风，扫描线与闪烁光标。",
    "swiss-modern": "包豪斯网格，纯黑白，只加一点红。",
    "paper-ink": "暖奶油纸页，首字下沉与大段引文，一抹绯红点缀。",
    # 34 library templates
    "8-bit-orbit": "深蓝虚空上的像素霓虹街机美学。",
    "biennale-yellow": "暖羊皮纸上的太阳黄，深靛蓝衬线与日晕渐变氛围。",
    "block-frame": "新粗野主义，粉彩霓虹色块配粗黑描边。",
    "blue-professional": "奶油纸底配电光钴蓝点缀，干净现代的专业感。",
    "bold-poster": "编辑海报风，巨型 Shrikhand 标题加一点消防红。",
    "broadside": "暗色编辑画布，单一火橙点缀，中西文双语字库。",
    "capsule": "暖骨白上的模块化胶囊卡片，粉彩流行全色盘。",
    "cartesian": "安静的暖中性色盘，古典 Playfair 衬线，从容不迫。",
    "cobalt-grid": "方格纸上的电光钴蓝衬线，阶梯式扫描线装饰与细发丝线。",
    "coral": "近黑底上的奶油与珊瑚色，超大 Bebas Neue 排印。",
    "creative-mode": "奶油纸画布，绿粉橙黄多彩点缀，Archivo Black 标题。",
    "daisy-days": "欢快粉彩，手绘雏菊、星星与彩虹，友好柔软而温暖。",
    "editorial-forest": "森林绿、灰粉与暖奶油，Source Serif 4 的安静季报风。",
    "editorial-tri-tone": "三色编辑系统：灰粉、芥末奶油与深勃艮第。",
    "emerald-editorial": "杂志封面式商务风：祖母绿+海军蓝+纸色，双线刊头装饰。",
    "grove": "森林绿画布配奶油字，古典 Playfair 衬线，一点铁锈红。",
    "long-table": "暖奶油与锈红的晚餐俱乐部风，粗大写标题配 Fraunces 衬线。",
    "mat": "深鼠尾草绿画布，骨白纸与焦橙点缀，带木质感的中古现代。",
    "monochrome": "象牙账本纸配全黑排印，Lora 衬线标题，完全无彩色。",
    "neo-grid-bold": "编辑式新粗野主义，米白纸上只有一点霓虹黄。",
    "peoples-platform": "行动海报能量：奶油底上的蓝橙红，Alfa Slab 配手写笔刷。",
    "pin-and-paper": "黄色纸面配别针插画，墨蓝 Caveat 手写，纸纹肌理。",
    "pink-script": "黑画布、荧光粉点缀、珍珠奶油纸，深夜编辑式的奢华。",
    "playful": "日晒蜜桃底配 Syne 标题，友好的独立产品发布风。",
    "raw-grid": "新粗野主义：粗描边、错位阴影，粉/鼠尾草/墨三色盘。",
    "retro-windows": "Windows 95 窗框：灰色标题栏、像素字体、满格怀旧。",
    "retro-zine": "米纸配绿色点缀，Bebas Neue 加手写体：riso 印刷小志的网页版。",
    "sakura-chroma": "日式复古磁带包装：奶油纸、斜向彩虹缎带、紧凑粗体、JIS 规格勾选框。",
    "scatterbrain": "便利贴灵感：粉彩贴纸、Caveat 手写、Shrikhand 配 Zilla Slab。",
    "signal": "深海军蓝画布，骨白纸与一点哑金，安静而有分量的机构感。",
    "soft-editorial": "暖纸上的 Cormorant Garamond 衬线，鼠尾草、腮红与柠檬点缀。",
    "stencil-tablet": "骨白纸配镂空模板标题，六色大地色盘：考古遇上品牌。",
    "studio": "黑画布配电光黄排印，高压设计工作室美学。",
    "vellum": "深海军蓝画布，暖黄 Cormorant 衬线，一点灰青点缀，安静的书卷气。",
}


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

    all_entries = [
        {**p, "tagline_zh": TAGLINE_ZH.get(p["slug"], p["tagline"]), "kind": "preset"}
        for p in PRESET_ENTRIES
    ]
    all_entries.extend(bold_entries)

    out_path = os.path.join(SKILL_DIR, "gallery-data.json")
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(all_entries, f, ensure_ascii=False, separators=(",", ":"))

    print(f"Wrote {len(all_entries)} entries "
          f"({len(PRESET_ENTRIES)} presets + {len(bold_entries)} templates) to {out_path}")


if __name__ == "__main__":
    main()
