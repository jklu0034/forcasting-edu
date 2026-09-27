#!/usr/bin/env python3
"""Build the Western Confetti static site from the design exports.

The four screens in design/ are the original HTML exports and are kept
untouched. This script copies each one into site/, wires up navigation
(the exports use data-path="..." href="#" placeholders), links the course
cards through to the pathways and contact pages, and makes the pages
production-ready:

- the Tailwind Play CDN script is replaced by stylesheets compiled with the
  Tailwind CLI, using the tailwind.config each export ships inline;
- hotlinked images are downloaded once into site/assets/img/ and served
  locally, so the site does not depend on the design tool's image URLs.

site/contact.html is hand-written (no design export existed for the
Contact tab); it is not generated, but it shares the main stylesheet and
is scanned when that stylesheet is compiled.

Usage: npm install && npm run build   (or: python3 scripts/build.py)
"""
import hashlib
import pathlib
import re
import subprocess
import sys
import urllib.request

ROOT = pathlib.Path(__file__).resolve().parent.parent
DESIGN = ROOT / "design"
SITE = ROOT / "site"
IMG = SITE / "assets" / "img"
CSS = SITE / "assets" / "css"
TW = ROOT / "tailwind"

# Screens 01-03 share one Tailwind config; 04 ships its own palette.
# bundle -> (export whose config it uses, plugins, pages it styles)
BUNDLES = {
    "main": ("01-home.html", [], ["index.html", "story.html", "courses.html", "contact.html"]),
    "pathways": (
        "04-couples-pathways.html",
        ["@tailwindcss/forms", "@tailwindcss/container-queries"],
        ["pathways.html"],
    ),
}

# data-path value used in the exports -> page in site/
ROUTES = {
    "journey": "index.html",
    "courses": "courses.html",
    "team-story": "story.html",
    "contact-support": "contact.html",
}

# design export -> (output page, <title>)
PAGES = {
    "01-home.html": ("index.html", "Western Confetti · Learn Hebrew Together"),
    "02-team-story.html": ("story.html", "Our Story · Western Confetti"),
    "03-course-catalogue.html": ("courses.html", "Course Catalogue · Western Confetti"),
    "04-couples-pathways.html": ("pathways.html", "The Couples Pathways · Western Confetti"),
}


def link_routes(html):
    def repl(m):
        path = m.group(1)
        if path not in ROUTES:
            sys.exit(f"unknown data-path {path!r}")
        return f'data-path="{path}" href="{ROUTES[path]}"'

    return re.sub(r'data-path="([^"]+)" href="#"', repl, html)


def add_title(html, title):
    return html.replace("</head>", f"<title>{title}</title>\n</head>", 1)


def replace_n(html, pattern, make, expected, flags=re.S):
    """Replace each regex match with make(index, match); assert the count."""
    count = 0

    def repl(m):
        nonlocal count
        count += 1
        return make(count, m)

    out = re.sub(pattern, repl, html, flags=flags)
    if count != expected:
        sys.exit(f"pattern matched {count} times, expected {expected}: {pattern}")
    return out


def raise_modal(html):
    # The exports give the bottom-sheet modal and the tab bar both z-50; the
    # nav comes later in the DOM, so it covers the modal's submit button.
    return replace_n(
        html,
        r'<div class="fixed inset-0 z-50 ',
        lambda i, m: '<div class="fixed inset-0 z-[60] ',
        expected=1,
    )


def local_images(html):
    """Download each hotlinked image once and point the page at the copy."""
    IMG.mkdir(parents=True, exist_ok=True)

    def repl(m):
        url = m.group(1)
        stem = hashlib.sha1(url.encode()).hexdigest()[:12]
        existing = list(IMG.glob(stem + ".*"))
        if existing:
            path = existing[0]
        else:
            with urllib.request.urlopen(url, timeout=30) as r:
                data = r.read()
            ext = ".png" if data[:4] == b"\x89PNG" else ".jpg"
            path = IMG / (stem + ext)
            path.write_bytes(data)
            print(f"  downloaded {path.relative_to(ROOT)}")
        return f'src="assets/img/{path.name}"'

    return re.sub(r'src="(https://lh3\.googleusercontent\.com/[^"]+)"', repl, html)


def bundle_for(page):
    return next(name for name, (_, _, pages) in BUNDLES.items() if page in pages)


def compiled_css(html, page):
    """Swap the Play CDN script and inline config for the compiled stylesheet."""
    html = replace_n(
        html,
        r'<script src="https://cdn\.tailwindcss\.com[^"]*"></script>\s*<script id="tailwind-config">.*?</script>',
        lambda i, m: f'<link href="assets/css/{bundle_for(page)}.css" rel="stylesheet"/>',
        expected=1,
    )
    return html.replace("</head>", '<link href="assets/img/favicon.png" rel="icon" type="image/png"/>\n</head>', 1)


def write_tailwind_configs():
    TW.mkdir(exist_ok=True)
    for name, (src, plugins, pages) in BUNDLES.items():
        html = (DESIGN / src).read_text(encoding="utf-8")
        config = re.search(r"tailwind\.config\s*=\s*(\{.*?\})\s*</script>", html, re.S).group(1)
        content = ", ".join(f'"site/{p}"' for p in pages)
        requires = ", ".join(f'require("{p}")' for p in plugins)
        (TW / f"{name}.config.js").write_text(
            f"// Generated by scripts/build.py from design/{src}; do not edit.\n"
            f"const config = {config};\n"
            f"config.content = [{content}];\n"
            f"config.plugins = [{requires}];\n"
            "module.exports = config;\n",
            encoding="utf-8",
        )


def compile_css():
    CSS.mkdir(parents=True, exist_ok=True)
    for name in BUNDLES:
        subprocess.run(
            ["npx", "--no-install", "tailwindcss", "-c", f"tailwind/{name}.config.js",
             "-i", "tailwind/input.css", "-o", f"site/assets/css/{name}.css", "--minify"],
            cwd=ROOT, check=True,
        )


def course_catalogue(html):
    html = raise_modal(html)
    # "View Course & Enroll" buttons -> the matching track on the pathways page.
    # Card order (Foundations, Mixed-Level, Travel) matches Tracks 01-03.
    return replace_n(
        html,
        r'<button (class="w-full h-12 bg-primary[^"]*")>(\s*<span>View Course &amp; Enroll</span>.*?)</button>',
        lambda i, m: f'<a {m.group(1)} href="pathways.html#track-0{i}">{m.group(2)}</a>',
        expected=3,
    )


def couples_pathways(html):
    html = raise_modal(html)
    # Anchor each track so course cards can deep-link to it.
    html = replace_n(
        html,
        r'<article class="',
        lambda i, m: f'<article id="track-0{i}" class="scroll-mt-24 ',
        expected=3,
    )
    # The export's audio preview looks up its card with closest('.p-3.5'),
    # which is an invalid selector (unescaped dot) and throws on every click.
    html = replace_n(
        html,
        r"closest\('\.p-3\.5'\)",
        lambda i, m: r"closest('.p-3\\.5')",
        expected=1,
    )
    # "Begin Pathway" -> enrolment enquiry on the contact page, track preselected.
    return replace_n(
        html,
        r'<button (class="h-11 px-5 rounded-xl bg-primary[^"]*")>(\s*<span>Begin Pathway</span>.*?)</button>',
        lambda i, m: f'<a {m.group(1)} href="contact.html#enrol-track-{i}">{m.group(2)}</a>',
        expected=3,
    )


TRANSFORMS = {
    "03-course-catalogue.html": course_catalogue,
    "04-couples-pathways.html": couples_pathways,
}


def main():
    SITE.mkdir(exist_ok=True)
    for src, (out, title) in PAGES.items():
        html = (DESIGN / src).read_text(encoding="utf-8")
        html = add_title(html, title)
        html = compiled_css(html, out)
        html = local_images(html)
        html = link_routes(html)
        if src in TRANSFORMS:
            html = TRANSFORMS[src](html)
        if 'href="#"' in html:
            sys.exit(f"{src}: unlinked href=\"#\" remains")
        (SITE / out).write_text(html, encoding="utf-8")
        print(f"design/{src} -> site/{out}")
    favicon = IMG / "favicon.png"
    logo = re.search(r'alt="Western Confetti Logo" [^>]*src="assets/img/([^"]+)"',
                     (SITE / "index.html").read_text(encoding="utf-8")).group(1)
    favicon.write_bytes((IMG / logo).read_bytes())
    write_tailwind_configs()
    compile_css()


if __name__ == "__main__":
    main()
