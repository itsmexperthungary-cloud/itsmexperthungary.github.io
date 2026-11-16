# A. Krisztina Juhász – website

Static personal website (ITSM process consulting and ITIL training), hosted on GitHub Pages.

- `index.html` – main page
- `health-check.html` – ITSM Health Check offer
- `privacy.html` – privacy notice and legal notice
- `assets/` – self-hosted fonts, images, CV

The pages are generated from the design canvas; edit the design, then rebuild.

## Rebuilding

`tools/build_site.py` turns the design canvas artboards into the static pages (self-hosted fonts, Open Graph image, icons) and builds the Hungarian pages in `hu/` from `tools/hu.json`. The build fails if any English text has no Hungarian pair.
