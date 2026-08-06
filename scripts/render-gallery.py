#!/usr/bin/env python3
"""
Renders the browsable style gallery: regenerates gallery-data.json (by
running build-gallery-data.py fresh, so the gallery always reflects the
design systems currently bundled in this skill), then injects that data
plus a batched Google Fonts URL for every card's display font into
assets/gallery-template.html.

The full gallery — shell text AND all 46 cards — is PRE-RENDERED into the
HTML here, in the language given by --lang. This matters: some hosts
(notably Claude Code's local-file preview) display HTML as a static
snapshot with JavaScript disabled, and a JS-only gallery shows up there as
a completely blank page. With the SSR pass the snapshot is fully readable;
the page's own script then re-renders on top to add search, filters, the
EN/中 toggle, and selection.

This file also owns the i18n dictionaries (shell strings + mood/formality/
scheme translations) and injects them into the template as JSON — single
source of truth for both the SSR pass and the in-page script.

Usage:
    python3 render-gallery.py <output_path.html> [--lang en|zh]

--lang should match the language of the conversation (default: en).
The output path is required — the skill instructs the agent to pass a
temp/scratch path so nothing is left behind in the user's project.
Output is one self-contained HTML file the user can open in any browser.
"""
import html
import json
import os
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

# ─── i18n: single source of truth (injected into the template as JSON) ────

SHELL_I18N = {
    "en": {
        "intro": "A quick-look card for every available palette + typeface. This is not a layout preview — real typographic detail only shows up in the generated deck. Pick one you like and tell the assistant its name.",
        "countUnit": "styles",
        "searchPh": "Search by name, mood, keyword… e.g. warm / editorial / dark",
        "kindAll": "All", "kindPreset": "Presets", "kindBold": "Library",
        "kindNote": "Presets = a one-line layout hint + palette/font (lightweight) · Library = a full design-system doc with components, type scale and decorative detail (richer, generation follows it more closely)",
        "empty": "No matching styles — try another keyword",
        "selLabel": "Selected", "copy": "Copy name", "copied": "Copied ✓",
        "copyManual": "Press ⌘/Ctrl+C", "badgePreset": "PRESET", "badgeLibrary": "LIBRARY",
    },
    "zh": {
        "intro": "当前可用的全部配色 + 字体速览卡片——这不是版式预览，真正的排版细节要看到生成结果才会体现。挑一个喜欢的，把名字告诉助手，就用它来生成。",
        "countUnit": "个风格",
        "searchPh": "按名字、气质、关键词搜索…比如 温暖 / 编辑风 / 深色",
        "kindAll": "全部", "kindPreset": "精选预设", "kindBold": "模板库",
        "kindNote": "精选预设 = 一句话版式提示 + 配色/字体（轻量） · 模板库 = 完整设计系统文档，含具体组件、字号阶梯、装饰细节（更详尽，生成效果更贴合）",
        "empty": "没有匹配的风格 — 试试换个关键词",
        "selLabel": "已选", "copy": "复制名称", "copied": "已复制 ✓",
        "copyManual": "请手动按 ⌘/Ctrl+C", "badgePreset": "预设", "badgeLibrary": "模板库",
    },
}

MOOD_ZH = {
    "activist": "行动主义", "approachable": "亲和", "archival": "档案感", "artistic": "艺术",
    "atmospheric": "氛围感", "bauhaus": "包豪斯", "bold": "大胆", "calm": "沉稳",
    "cheerful": "欢快", "clean": "干净", "confident": "自信", "considered": "考究",
    "crafted": "匠心", "creative": "创意", "cultural-institution": "文化机构",
    "cyberpunk": "赛博朋克", "design-led": "设计主导", "design-research": "设计研究",
    "developer-focused": "开发者向", "dramatic": "戏剧感", "earthy": "大地气息",
    "editorial": "编辑风", "electric": "电光", "elegant": "优雅", "energetic": "活力",
    "expressive": "表现力", "fresh": "清新", "friendly": "友好", "fun": "有趣",
    "futuristic": "未来感", "geeky": "极客", "graphic": "图形感", "hacker": "黑客",
    "handmade": "手作", "high-contrast": "高对比", "high-impact": "冲击力",
    "honest": "朴实", "hospitality": "款待感", "indie": "独立", "institutional": "机构感",
    "intellectual": "知性", "intentional": "用心", "intimate": "亲密",
    "kawaii-tech": "萌系科技", "ledger": "账本风", "literary": "文学", "lo-fi": "低保真",
    "loud": "张扬", "luxe": "奢华", "magazine-cover": "杂志封面",
    "messy-on-purpose": "刻意凌乱", "mid-century": "中古现代", "modern": "现代",
    "modernist": "现代主义", "monochrome": "单色", "moody": "暗调情绪", "natural": "自然",
    "newspaper": "报纸风", "nocturnal": "夜色", "nostalgic": "怀旧", "organic": "有机",
    "organized": "有序", "personality-driven": "个性鲜明", "playful": "俏皮",
    "poster-like": "海报感", "precise": "精准", "premium": "高级",
    "product-catalogue": "产品目录", "professional": "专业", "punchy": "干脆有力",
    "quiet": "安静", "raw": "粗粝", "restrained": "克制", "retro": "复古",
    "retro-modern": "复古现代", "retro-tech": "复古科技", "scholarly": "学术",
    "small-batch": "小批量", "social": "社交", "sophisticated": "老练",
    "structural": "结构感", "studious": "书卷", "sunny": "明媚", "tactile": "质感",
    "tech-print": "科技印刷", "technical": "技术流", "techy": "科技感",
    "thoughtful": "深思", "trustworthy": "可信赖", "underground": "地下",
    "warm": "温暖", "warm-classical": "暖调古典", "warm-minimal": "暖调极简",
    "warm-modern": "暖调现代", "warm-retro": "暖调复古", "weighty": "厚重",
    "wholesome": "治愈", "witty": "机智", "workshop": "工坊",
}
FORMALITY_ZH = {
    "high": "正式", "medium-high": "偏正式", "medium": "中等",
    "medium-low": "偏随性", "low": "随性",
}
SCHEME_ZH = {"light": "浅色", "dark": "深色", "mixed": "明暗混合"}


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


# ─── SSR: mirror of the template's cardHTML(), for the no-JS snapshot ─────

def text_color_for(hex_color):
    c = hex_color.lstrip("#")
    if len(c) < 6:
        return "#111"
    r, g, b = int(c[0:2], 16), int(c[2:4], 16), int(c[4:6], 16)
    lum = (0.299 * r + 0.587 * g + 0.114 * b) / 255
    return "#141414" if lum > 0.6 else "#F5F2E8"


def zh_mood(m):
    return MOOD_ZH.get(m, m)


def ssr_card(item, lang):
    zh = lang == "zh"
    t = SHELL_I18N[lang]
    bg = (item.get("colors") or ["#cccccc"])[0]
    text_color = text_color_for(bg)
    swatches = "".join(
        f'<span style="background:{c}"></span>' for c in item["colors"][:5]
    )
    pills = "".join(
        f'<span class="pill">{html.escape(zh_mood(m) if zh else m)}</span>'
        for m in item["mood"][:3]
    )
    extra_vals = [
        (FORMALITY_ZH.get(item.get("formality"), item.get("formality"))
         if zh else item.get("formality")),
        (SCHEME_ZH.get(item.get("scheme"), item.get("scheme"))
         if zh else item.get("scheme")),
    ]
    extra = "".join(
        f'<span class="pill">{html.escape(v)}</span>' for v in extra_vals if v
    )
    kind_label = t["badgePreset"] if item["kind"] == "preset" else t["badgeLibrary"]
    kind_bg = "rgba(255,255,255,0.22)" if item["kind"] == "preset" else "rgba(0,0,0,0.18)"
    tagline = (item.get("tagline_zh") or item["tagline"]) if zh else item["tagline"]
    return (
        f'<article class="card" data-slug="{html.escape(item["slug"])}" tabindex="0" '
        f'role="button" aria-pressed="false">'
        f'<div class="plate" style="background:{bg};color:{text_color};">'
        f'<span class="check">✓</span>'
        f'<span class="kind-badge" style="background:{kind_bg};color:{text_color};">'
        f'{html.escape(kind_label)}</span>'
        f'<div class="name" style="font-family:\'{html.escape(item["font"])}\', '
        f'var(--font-display);">{html.escape(item["name"])}</div></div>'
        f'<div class="swatches">{swatches}</div>'
        f'<div class="body"><p class="tagline">{html.escape(tagline)}</p>'
        f'<div class="meta">{pills}{extra}</div></div></article>'
    )


def ssr_chips(data, lang):
    counts = {}
    for item in data:
        for m in item["mood"]:
            counts[m] = counts.get(m, 0) + 1
    top = sorted(counts, key=lambda m: -counts[m])[:12]
    return "".join(
        f'<button class="chip" data-mood="{html.escape(m)}">'
        f'{html.escape(zh_mood(m) if lang == "zh" else m)}</button>'
        for m in top
    )


def main():
    lang = "en"
    pos = []
    args = sys.argv[1:]
    i = 0
    while i < len(args):
        if args[i] == "--lang":
            if i + 1 >= len(args) or args[i + 1] not in ("en", "zh"):
                raise SystemExit("--lang takes 'en' or 'zh'")
            lang = args[i + 1]
            i += 2
        else:
            pos.append(args[i])
            i += 1
    if not pos:
        raise SystemExit("Usage: render-gallery.py <output_path.html> [--lang en|zh]")
    out_path = pos[0]

    data = build_data()

    # drift guard: every mood in the data must have a Chinese translation
    missing = sorted({m for e in data for m in e["mood"]} - set(MOOD_ZH))
    if missing:
        sys.stderr.write(
            "WARNING: moods without Chinese translation (will show in English "
            "in zh mode): " + ", ".join(missing) + "\n"
        )

    fonts_query = google_fonts_query(item["font"] for item in data)

    with open(TEMPLATE_PATH, encoding="utf-8") as f:
        template = f.read()

    # JSON is embedded inside <script type="application/json"> blocks — only
    # the closing-tag sequence needs escaping so the browser's HTML parser
    # can't be tricked into ending the block early.
    def as_json(obj):
        return json.dumps(obj, ensure_ascii=False, separators=(",", ":")) \
            .replace("</script", "<\\/script")

    i18n_payload = {
        "shell": SHELL_I18N,
        "mood_zh": MOOD_ZH,
        "formality_zh": FORMALITY_ZH,
        "scheme_zh": SCHEME_ZH,
    }

    t = SHELL_I18N[lang]
    rendered = (
        template
        .replace("__CARD_FONTS_QUERY__", fonts_query)
        .replace("__DATA__", as_json(data))
        .replace("__I18N__", as_json(i18n_payload))
        .replace("__SSR_LANG__", lang)
        .replace("__SSR_INTRO__", html.escape(t["intro"]))
        .replace("__SSR_COUNT_UNIT__", html.escape(t["countUnit"]))
        .replace("__SSR_SEARCH_PH__", html.escape(t["searchPh"], quote=True))
        .replace("__SSR_KIND_ALL__", html.escape(t["kindAll"]))
        .replace("__SSR_KIND_PRESET__", html.escape(t["kindPreset"]))
        .replace("__SSR_KIND_BOLD__", html.escape(t["kindBold"]))
        .replace("__SSR_KIND_NOTE__", html.escape(t["kindNote"]))
        .replace("__SSR_SEL_LABEL__", html.escape(t["selLabel"]))
        .replace("__SSR_COPY__", html.escape(t["copy"]))
        .replace("__SSR_CHIPS__", ssr_chips(data, lang))
        .replace("__SSR_CARDS__", "".join(ssr_card(item, lang) for item in data))
        .replace("__SSR_TOTAL__", str(len(data)))
    )

    leftovers = [tok for tok in ("__SSR_", "__DATA__", "__I18N__",
                                 "__CARD_FONTS_QUERY__") if tok in rendered]
    if leftovers:
        raise SystemExit(f"Unsubstituted placeholders remain: {leftovers}")

    os.makedirs(os.path.dirname(os.path.abspath(out_path)) or ".", exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(rendered)

    print(f"Rendered {len(data)} styles to {out_path} (lang={lang}, pre-rendered "
          f"for no-JS viewers)")


if __name__ == "__main__":
    main()
