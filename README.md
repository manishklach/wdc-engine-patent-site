# WDC-Engine Patent Microsite

Static GitHub Pages microsite for:

**WDC-Engine - Systems and Methods for Semantic Deduplication and Shared Execution of Agent-Generated Enterprise Tasks**

This project turns the patent specification into a polished public-facing technical overview. The site is intended for engineers, patent reviewers, enterprise buyers, and technical evaluators, while avoiding filing placeholders, draft-only metadata, and patent-office style claim presentation.

## Project purpose

- Present the invention as a clear technical architecture microsite
- Explain semantic deduplication, temporal admission, shared execution units, and result fan-out in web-quality language
- Provide custom diagrams and worked examples grounded in the patent specification
- Stay simple to publish on GitHub Pages with no build step

## Files

- `index.html`: Single-page microsite structure and content
- `styles.css`: Visual system, layout, responsiveness, and diagram styling
- `script.js`: Sticky-header, mobile navigation, and reveal behavior
- `assets/favicon.svg`: Favicon/logo mark
- `assets/og-card.svg`: Social preview graphic
- `prototype/`: Local MVP demonstrating semantic deduplication, temporal admission, shared execution, and result fan-out

## Local preview

Run a simple static server:

```powershell
cd C:\Users\ManishKL\Documents\Playground\wdc-engine-site
python -m http.server 8000
```

Then open `http://localhost:8000`.

Opening `index.html` directly also works for a quick review, but a local server is preferred.

## Prototype

The same repository also contains a working concept demo under `prototype/`.

- Prototype documentation: `prototype/README.md`
- Backend: FastAPI + Redis + sentence-transformers
- Frontend: lightweight static simulator UI

Quick start:

```powershell
cd C:\Users\ManishKL\Documents\Playground\wdc-engine-site\prototype
Copy-Item .env.example .env
docker compose up --build
```

Then open:

- Prototype UI: `http://localhost:4173`
- Prototype API: `http://localhost:8000/api`

## GitHub Pages deployment

This repository includes a GitHub Actions workflow at `.github/workflows/deploy-pages.yml`.

Recommended setup:

1. Keep the site in the repository root.
2. Keep `main` as the source branch for changes.
3. In GitHub, open `Settings -> Pages`.
4. Set the build and deployment source to `GitHub Actions`.
5. Push to `main` to trigger a fresh Pages deployment.

The workflow uploads the repository root as the Pages artifact, so the project site deploys cleanly without moving files into `docs/`.

### Project-site path behavior

This repository is intended to publish as a project site at:

`https://manishklach.github.io/wdc-engine-patent-site/`

Path assumptions:

- Asset links, stylesheet links, script links, favicon links, and internal page links use relative URLs.
- Canonical, Open Graph, Twitter, `robots.txt`, and `sitemap.xml` use the absolute project-site URL above.
- The site therefore works correctly when served from the GitHub Pages repository subpath `/wdc-engine-patent-site/`.

## Updating content when the patent evolves

1. Use the latest patent specification as the source of truth.
2. Update the narrative copy in `index.html`.
3. Keep terminology aligned to the patent version you intend to present.
4. Edit inline SVG diagrams in `index.html` if the architecture or examples change.
5. Update `assets/og-card.svg` if you want the social preview to match revised wording.

## Asset structure

```text
wdc-engine-site/
  index.html
  styles.css
  script.js
  assets/
    favicon.svg
    og-card.svg
    prototype/
      diagrams/
      screenshots/
  prototype/
    README.md
    docker-compose.yml
    .env.example
    backend/
    frontend/
```

## Notes

- This is a public technical overview, not legal advice and not a substitute for the filing itself.
- The site copy is rewritten for clarity and public presentation rather than reproduced as long verbatim patent text.
- If you later want a public patent PDF link, add the PDF to the repo and update the relevant CTA in `index.html`.
