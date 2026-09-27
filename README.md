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

## Hosting

`site/` is the complete, self-contained website: compiled CSS, self-hosted
images, no build step on the server. Copy that folder to any static host.

- **GitHub Pages** — `.github/workflows/pages.yml` deploys `site/` on every
  push to the default branch. One-time setup: repo **Settings → Pages →
  Build and deployment → Source: GitHub Actions**.
- **Own web server (Nginx/Apache/IIS)** — copy the contents of `site/` to the
  document root; `index.html` is the home page. Only Google Fonts is loaded
  from outside the server.

## Run locally

```sh
npm run serve        # or: python3 -m http.server 8000 -d site
# open http://localhost:8000
```

## Updating from new design exports

`design/` holds the original exports untouched. After replacing a file there,
rebuild (needs Node 18+ and Python 3):

```sh
npm install
npm run build
```

The build wires up the tab/CTA links, adds page titles and a favicon,
deep-links the course cards, downloads any new images into
`site/assets/img/`, compiles each export's inline Tailwind config into
`site/assets/css/` (`main.css` for Home/Story/Courses/Contact, `pathways.css`
for Pathways, which has its own palette), and fixes two defects in the
exports (the quiz modal sitting underneath the tab bar, and an invalid CSS
selector that broke the Pathways audio previews). It fails loudly if a design
change means a fix no longer applies. Commit the rebuilt `site/`; CI rejects
a push whose `site/` is out of date.

`site/contact.html` is not generated and is edited directly; it uses
`main.css`, so run the build after adding new Tailwind classes to it.

## Not yet wired up

- The contact form has no backend; it validates and shows a confirmation only.
  The email address `support@westernconfetti.example` is a placeholder.
- Notifications / profile icons in the header are visual only.
- Some pages still carry the designer's "UX Decision" annotation notes from
  the exports.
