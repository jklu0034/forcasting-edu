#!/usr/bin/env python3
"""Build the Western Confetti static site from the design exports.

The four screens in design/ are the original HTML exports and are kept
untouched. This script copies each one into site/, wires up navigation
(the exports use data-path="..." href="#" placeholders), and links the
course cards through to the pathways and contact pages.

site/contact.html is hand-written (no design export existed for the
Contact tab) and is not generated here.

Usage: python3 scripts/build.py
"""
import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
DESIGN = ROOT / "design"
SITE = ROOT / "site"

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
        lambda i, m: f'<a {m.group(1)} href="contact.html?topic=enrol&amp;track={i}">{m.group(2)}</a>',
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
        html = link_routes(html)
        if src in TRANSFORMS:
            html = TRANSFORMS[src](html)
        if 'href="#"' in html:
            sys.exit(f"{src}: unlinked href=\"#\" remains")
        (SITE / out).write_text(html, encoding="utf-8")
        print(f"design/{src} -> site/{out}")


if __name__ == "__main__":
    main()
