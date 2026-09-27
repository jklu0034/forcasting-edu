# Western Confetti — Couples Hebrew (mobile web app)

A static, mobile-first site built from four design exports. No build tooling or
server is needed: Tailwind (Play CDN), Google Fonts and the images are all
hotlinked.

## Screens

| Tab / route          | File                  | Source                              |
| -------------------- | --------------------- | ----------------------------------- |
| Home                 | `site/index.html`     | `design/01-home.html`               |
| Courses — catalogue  | `site/courses.html`   | `design/03-course-catalogue.html`   |
| Courses — pathways   | `site/pathways.html`  | `design/04-couples-pathways.html`   |
| Team / Story         | `site/story.html`     | `design/02-team-story.html`         |
| Contact              | `site/contact.html`   | hand-written (no design was supplied) |

Flow: Home → Course Catalogue → "View Course & Enroll" opens the matching track
on Pathways (`pathways.html#track-0N`) → "Begin Pathway" opens Contact with the
enrolment topic and track preselected (`contact.html#enrol-track-N`).

## Run locally

```sh
python3 -m http.server 8000 -d site
# open http://localhost:8000
```

Any static host works (GitHub Pages, Nginx, S3, etc.) — serve the `site/` folder.

## Updating from new design exports

`design/` holds the original exports untouched. After replacing a file there,
regenerate the four generated pages:

```sh
python3 scripts/build.py
```

The script wires up the tab/CTA links, adds page titles, deep-links the course
cards, and fixes two defects in the exports (the quiz modal sitting underneath
the tab bar, and an invalid CSS selector that broke the Pathways audio
previews). It fails loudly if a design change means a fix no longer applies.
`site/contact.html` is not generated and is edited directly.

## Not yet wired up

- The contact form has no backend; it validates and shows a confirmation only.
  The email address `support@westernconfetti.example` is a placeholder.
- Notifications / profile icons in the header are visual only.
- Tailwind's Play CDN is meant for prototyping; for production, compile the CSS
  with the Tailwind CLI.
