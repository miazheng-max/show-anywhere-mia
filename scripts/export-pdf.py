#!/usr/bin/env python3
"""
Export a generated deck to PDF — one page per slide.

Auto-detects the deck's canvas size from its own `.deck-stage` element, so a
portrait (1080x1920) deck exports as portrait pages and a landscape
(1920x1080) deck exports as landscape pages. No flag needed.

Requires:
    pip install playwright && python3 -m playwright install chromium

Usage:
    python3 scripts/export-pdf.py <deck.html> [output.pdf] [--compact]

    --compact   Render at 2/3 scale. Noticeably smaller file, slightly
                softer text. Useful when a long deck exceeds mail limits.

Animations are not preserved: each slide is captured in its final,
fully-revealed state. That is intentional — a PDF is a static artifact.
"""
import base64
import http.server
import functools
import os
import socketserver
import sys
import tempfile
import threading
import shutil

try:
    from playwright.sync_api import sync_playwright
except ImportError:
    sys.exit(
        "Playwright is not installed. Run:\n"
        "    pip install playwright && python3 -m playwright install chromium"
    )

DEFAULT_W, DEFAULT_H = 1080, 1920   # this skill's portrait default


def parse_args(argv):
    compact = "--compact" in argv
    pos = [a for a in argv[1:] if not a.startswith("--")]
    if not pos:
        sys.exit(
            "Usage: python3 scripts/export-pdf.py <deck.html> [output.pdf] [--compact]"
        )
    src = os.path.abspath(pos[0])
    if not os.path.isfile(src):
        sys.exit(f"File not found: {src}")
    out = os.path.abspath(pos[1]) if len(pos) > 1 else os.path.splitext(src)[0] + ".pdf"
    return src, out, compact


class QuietHandler(http.server.SimpleHTTPRequestHandler):
    def log_message(self, *args):
        pass


def serve(directory):
    """Serve over HTTP, not file://, so webfonts and relative assets load."""
    handler = functools.partial(QuietHandler, directory=directory)
    socketserver.TCPServer.allow_reuse_address = True
    httpd = socketserver.TCPServer(("127.0.0.1", 0), handler)
    threading.Thread(target=httpd.serve_forever, daemon=True).start()
    return httpd, httpd.server_address[1]


def detect_canvas(page):
    """Read the authored canvas size off the deck itself."""
    dims = page.evaluate(
        """() => {
            const stage = document.querySelector('.deck-stage');
            if (!stage) return null;
            const cs = getComputedStyle(stage);
            const w = parseInt(cs.width), h = parseInt(cs.height);
            return (w > 0 && h > 0) ? {w, h} : null;
        }"""
    )
    if dims:
        return dims["w"], dims["h"]
    print("  ! No .deck-stage found — falling back to "
          f"{DEFAULT_W}x{DEFAULT_H}. If this deck uses a different canvas, "
          "the export may be cropped or letterboxed.")
    return DEFAULT_W, DEFAULT_H


def freeze_animations(page):
    """Disable all transitions/animations for the whole export.

    Entrance animations here are staggered with `transition-delay` (up to
    ~0.5s). Merely setting the final values would start a *new* transition,
    so a screenshot taken shortly after catches later elements mid-fade or
    fully invisible. Killing transitions makes the forced values apply
    instantly, which is what a static export wants.
    """
    page.add_style_tag(content="""
        *, *::before, *::after {
            transition: none !important;
            animation: none !important;
        }
    """)


def show_slide(page, index):
    """Activate one slide using the same class contract the decks use.

    Deliberately does NOT touch `display` — these decks switch slides with
    visibility/opacity, and forcing `display` can make every slide paint at
    once. Inline visibility/opacity is set as a belt-and-braces fallback for
    decks whose CSS keys off something slightly different.
    """
    page.evaluate(
        """(index) => {
            const slides = document.querySelectorAll('.slide');
            slides.forEach((s, i) => {
                const on = i === index;
                s.classList.toggle('active', on);
                s.classList.toggle('visible', on);
                s.style.visibility = on ? 'visible' : 'hidden';
                s.style.opacity = on ? '1' : '0';
                if (on) {
                    // land every entrance animation in its final state
                    s.querySelectorAll('.reveal').forEach(el => {
                        el.style.opacity = '1';
                        el.style.transform = 'none';
                        el.style.visibility = 'visible';
                    });
                }
            });
        }""",
        index,
    )


def main():
    src, out, compact = parse_args(sys.argv)
    serve_dir, filename = os.path.dirname(src), os.path.basename(src)

    httpd, port = serve(serve_dir)
    shots_dir = tempfile.mkdtemp(prefix="deck-pdf-")

    try:
        with sync_playwright() as p:
            browser = p.chromium.launch()
            page = browser.new_page()
            page.goto(f"http://127.0.0.1:{port}/{filename}", wait_until="networkidle")
            page.evaluate("document.fonts.ready")
            page.wait_for_timeout(1200)

            cw, ch = detect_canvas(page)
            scale = 2 / 3 if compact else 1
            vw, vh = int(cw * scale), int(ch * scale)
            orient = "portrait" if ch > cw else "landscape"
            print(f"  Canvas: {cw}x{ch} ({orient})"
                  + (f" -> rendering at {vw}x{vh} (compact)" if compact else ""))

            page.set_viewport_size({"width": vw, "height": vh})
            page.wait_for_timeout(400)   # let the stage rescale to the viewport
            freeze_animations(page)

            count = page.evaluate("document.querySelectorAll('.slide').length")
            if not count:
                sys.exit("  No .slide elements found — is this a generated deck?")
            print(f"  Found {count} slides")

            # hide editing chrome that shouldn't appear in a static export
            page.evaluate(
                """() => {
                    document.querySelectorAll(
                        '.edit-badge, .save-toast, .nav-hint, .deck-controls'
                    ).forEach(el => el.style.display = 'none');
                }"""
            )

            shots = []
            for i in range(count):
                show_slide(page, i)
                page.wait_for_timeout(320)
                path = os.path.join(shots_dir, f"slide-{i+1:03d}.png")
                page.screenshot(path=path)
                shots.append(path)
                print(f"  Captured {i+1}/{count}")

            # assemble: one image per PDF page, page size == canvas size
            imgs_html = "\n".join(
                '<div class="page"><img src="data:image/png;base64,{}"></div>'.format(
                    base64.b64encode(open(s, "rb").read()).decode()
                )
                for s in shots
            )
            pdf_html = f"""<!DOCTYPE html><html><head><style>
                *{{margin:0;padding:0}}
                @page{{size:{vw}px {vh}px;margin:0}}
                .page{{width:{vw}px;height:{vh}px;page-break-after:always;overflow:hidden}}
                .page:last-child{{page-break-after:auto}}
                img{{width:{vw}px;height:{vh}px;display:block}}
            </style></head><body>{imgs_html}</body></html>"""

            print("  Assembling PDF…")
            pdf_page = browser.new_page()
            pdf_page.set_content(pdf_html, wait_until="load")
            pdf_page.pdf(path=out, width=f"{vw}px", height=f"{vh}px",
                         print_background=True,
                         margin={"top": "0", "right": "0", "bottom": "0", "left": "0"})
            browser.close()
    finally:
        httpd.shutdown()
        shutil.rmtree(shots_dir, ignore_errors=True)

    size_mb = os.path.getsize(out) / 1_048_576
    print(f"\n  PDF: {out}  ({size_mb:.1f} MB, {count} pages)")
    if size_mb > 10 and not compact:
        print("  Over 10 MB — re-run with --compact for a much smaller file.")


if __name__ == "__main__":
    main()
