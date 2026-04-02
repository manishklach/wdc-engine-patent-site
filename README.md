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

## Local preview

Run a simple static server:

```powershell
cd C:\Users\ManishKL\Documents\Playground\wdc-engine-site
python -m http.server 8000
```

Then open `http://localhost:8000`.

Opening `index.html` directly also works for a quick review, but a local server is preferred.

## GitHub Pages deployment

### Dedicated repository

1. Push the contents of this folder as the repository root.
2. In GitHub, open `Settings -> Pages`.
3. Choose `Deploy from a branch`.
4. Select the default branch and `/ (root)`.
5. Save.

### Subfolder inside another repository

Use one of these approaches:

1. Copy the site into the repo root for a Pages-only repository.
2. Copy the site into `/docs` and publish Pages from that folder.
3. Use a GitHub Actions Pages workflow that uploads this folder as the static artifact.

All paths in this site are relative, so it can be hosted from a GitHub Pages project subpath without rewriting asset URLs.

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
```

## Notes

- This is a public technical overview, not legal advice and not a substitute for the filing itself.
- The site copy is rewritten for clarity and public presentation rather than reproduced as long verbatim patent text.
- If you later want a public patent PDF link, add the PDF to the repo and update the relevant CTA in `index.html`.
