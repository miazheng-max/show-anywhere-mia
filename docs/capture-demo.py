#!/usr/bin/env python3
"""
Regenerates docs/demo.gif and docs/gallery.png for the README.

Requires:
    pip install playwright pillow && python3 -m playwright install chromium

Usage (from anywhere):
    python3 docs/capture-demo.py

It renders the style gallery to a temp dir, serves that dir on a local port,
drives a headless Chromium through the gallery and the sample deck, then
assembles the frames into an animated GIF.
"""
import functools
import http.server
import os
import shutil
import socketserver
import subprocess
import sys
import tempfile
import threading

from playwright.sync_api import sync_playwright
from PIL import Image, ImageDraw, ImageFont

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DOCS = os.path.join(REPO, "docs")
PORT = 8941

W, H = 1000, 700
PHONE_W, PHONE_H = 395, 700
PAPER = (240, 235, 222)
GRIDLINE = (233, 228, 214)
INK = (31, 43, 224)

work = tempfile.mkdtemp(prefix="show-anywhere-demo-")
frames_dir = os.path.join(work, "frames")
serve_dir = os.path.join(work, "serve")
os.makedirs(frames_dir, exist_ok=True)
os.makedirs(serve_dir, exist_ok=True)

# --- render the gallery + stage the sample deck into one served directory ---
subprocess.run(
    [sys.executable, os.path.join(REPO, "scripts", "render-gallery.py"),
     os.path.join(serve_dir, "gallery.html")],
    check=True,
)
shutil.copy(os.path.join(DOCS, "demo-deck.html"),
            os.path.join(serve_dir, "demo-deck.html"))


class QuietHandler(http.server.SimpleHTTPRequestHandler):
    def log_message(self, *args):
        pass


handler = functools.partial(QuietHandler, directory=serve_dir)
socketserver.TCPServer.allow_reuse_address = True
httpd = socketserver.TCPServer(("127.0.0.1", PORT), handler)
threading.Thread(target=httpd.serve_forever, daemon=True).start()

BASE = f"http://127.0.0.1:{PORT}"
GALLERY, DECK = f"{BASE}/gallery.html", f"{BASE}/demo-deck.html"

frames = []


def add(path, hold=1):
    frames.extend([path] * hold)
    print("  ", os.path.basename(path), f"(hold={hold})")


def snap(page, name, hold=1):
    path = os.path.join(frames_dir, f"{len(frames):03d}_{name}.png")
    page.screenshot(path=path)
    add(path, hold)


def _caption_font():
    for candidate in (
        "/System/Library/Fonts/Supplemental/Arial.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "C:/Windows/Fonts/arial.ttf",
    ):
        if os.path.exists(candidate):
            return ImageFont.truetype(candidate, 17)
    return ImageFont.load_default()


def snap_deck(page, name, caption, hold=1):
    """Screenshot the phone-sized deck, then center it on a full-width canvas
    so a portrait deck reads as intentional rather than lost in letterboxing."""
    raw = os.path.join(frames_dir, f"raw_{name}.png")
    page.screenshot(path=raw)

    shot = Image.open(raw).convert("RGB")
    canvas = Image.new("RGB", (W, H), PAPER)
    d = ImageDraw.Draw(canvas)
    for x in range(0, W, 40):
        d.line([(x, 0), (x, H)], fill=GRIDLINE, width=1)
    for y in range(0, H, 40):
        d.line([(0, y), (W, y)], fill=GRIDLINE, width=1)

    x0 = (W - PHONE_W) // 2
    canvas.paste(shot, (x0, 0))
    d.rectangle([x0 - 1, 0, x0 + PHONE_W, H - 1], outline=INK, width=2)

    # Captions stay ASCII: the fallback faces here have no CJK glyphs and
    # would render Chinese as tofu boxes.
    d.text((36, 34), caption, fill=INK, font=_caption_font())

    path = os.path.join(frames_dir, f"{len(frames):03d}_{name}.png")
    canvas.save(path)
    add(path, hold)


with sync_playwright() as p:
    browser = p.chromium.launch()

    # ---------- the gallery ----------
    page = browser.new_page(viewport={"width": W, "height": H}, device_scale_factor=1)
    page.goto(GALLERY, wait_until="networkidle")
    page.wait_for_timeout(2500)          # let webfonts settle
    snap(page, "gallery_top", hold=6)

    for i in range(3):
        page.mouse.wheel(0, 420)
        page.wait_for_timeout(700)
        snap(page, f"gallery_scroll{i}", hold=2)

    page.evaluate("window.scrollTo({top:0})")
    page.wait_for_timeout(500)

    search = page.locator("#searchInput")
    search.click()
    for ch in "editorial":
        search.type(ch, delay=0)
        page.wait_for_timeout(110)
    page.wait_for_timeout(900)
    snap(page, "gallery_search", hold=5)

    search.fill("")
    page.wait_for_timeout(400)
    page.locator('#kindToggle button[data-kind="bold"]').click()
    page.wait_for_timeout(900)
    snap(page, "gallery_library", hold=4)

    search.fill("cobalt grid")
    page.wait_for_timeout(900)
    snap(page, "gallery_cobalt", hold=5)

    # match the card actually titled "Cobalt Grid" — a plain text search also
    # matches other cards that merely mention cobalt in their description
    page.locator(".card", has_text="Cobalt Grid").first.click()
    page.wait_for_timeout(900)
    snap(page, "gallery_picked", hold=7)
    page.close()

    # ---------- the generated deck, at phone size ----------
    page = browser.new_page(viewport={"width": PHONE_W, "height": PHONE_H},
                            device_scale_factor=1)
    page.goto(DECK, wait_until="networkidle")
    page.wait_for_timeout(2500)
    snap_deck(page, "deck_s1",
              "Generated deck  -  1080x1920 portrait  -  one self-contained HTML file",
              hold=7)

    page.keyboard.press("ArrowDown")
    page.wait_for_timeout(1200)
    snap_deck(page, "deck_s2", "Navigate  -  scroll, swipe, or arrow keys", hold=7)

    page.keyboard.press("ArrowDown")
    page.wait_for_timeout(1200)
    snap_deck(page, "deck_s3", "Edit  -  click any text, no edit mode to turn on", hold=8)

    page.close()
    browser.close()

httpd.shutdown()

# ---------- assemble ----------
imgs = [Image.open(f).convert("RGB") for f in frames]
pal = imgs[0].quantize(colors=180, method=Image.MEDIANCUT)
imgs_q = [im.quantize(colors=180, palette=pal, dither=Image.FLOYDSTEINBERG) for im in imgs]

gif_path = os.path.join(DOCS, "demo.gif")
imgs_q[0].save(gif_path, save_all=True, append_images=imgs_q[1:],
               duration=330, loop=0, optimize=True)

png_path = os.path.join(DOCS, "gallery.png")
Image.open(frames[0]).save(png_path)

print(f"\nGIF: {gif_path}  {os.path.getsize(gif_path)//1024} KB")
print(f"PNG: {png_path}  {os.path.getsize(png_path)//1024} KB")
shutil.rmtree(work, ignore_errors=True)
