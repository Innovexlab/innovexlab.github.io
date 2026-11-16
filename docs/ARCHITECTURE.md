# Architecture

## Summary

A hand-written static site: HTML pages, one CSS file, two small JavaScript files. GitHub Pages
serves the repository root from the `main` branch. There is **no build step, no framework and no
package manager**; a developer needs only a browser, Git and Python (for the helper scripts).

```
Browser ──HTTPS──> GitHub Pages (www.innovexlab.com, repo root on main)
                        │
                        ├── *.html               pages (header/footer copied in from partials/)
                        ├── assets/css/site.css  design tokens + all styles
                        ├── assets/js/site-config.js  settings (Client Portal URL)
                        └── assets/js/site.js    progressive enhancements

contact.html form ──POST──> formsubmit.co ──email──> info@innovex-lab.com
                              └── redirect ──> /thankyou.html
```

## Why this design (decision record)

| Decision | Reason | Revisit when |
|---|---|---|
| Keep plain static HTML on GitHub Pages | The existing site already works this way; DNS, HTTPS and hosting are in place; anyone can edit it; nothing to patch or upgrade | A content editor needs to publish articles without touching HTML (News & Insights phase). Then evaluate Jekyll collections (already available on Pages) before any new framework |
| Shared header/footer via `partials/` + `tools/sync_partials.py` | Pages has no server-side includes and we don't want a build pipeline. The script gives one source of truth while the committed HTML stays exactly what is served | Number of pages grows past ~20, or a Jekyll layout is adopted |
| Progressive enhancement | The menu, form and links all work with JavaScript disabled; JS only improves them | Never relax for core paths (contact, phone, navigation) |
| System font stack, no external CSS/JS | Fast on phones in the field, no third-party requests, no cookie banner needed | A brand typeface is supplied with a web licence |
| FormSubmit for the form | Already in use; requires no server. Its delivery must be verified (task W03) | Spam volume, delivery problems or a need for CRM routing |
| Client Portal URL in `site-config.js`, links hidden by default | One switch for header, mobile menu, footer, contact and How to Start; prevents publishing a guessed URL | Portal verified: set the URL; JS-free fallback could then be hard-coded |
| `tools/check_site.py` + `tools/run_browser_smoke.py` as the test suite | Encodes the content rules (claims that need proof) and basic SEO/a11y so mistakes are caught before review | Add rules whenever a reviewer catches something by hand |

## Pages and the content pattern

Every clinical message follows the marketing standard's order:

1. **Situation**: a moment a director of nursing or clinician recognizes
2. **Mechanism**: molecular testing reads organisms and resistance genes directly from the specimen
3. **Decision**: what the result can inform (precautions, cohorting, antibiotic choice…)
4. **Honest limit**: what a molecular result can't tell you on its own
5. **One action**: book a 15-minute panel review

Pages reuse a small set of components defined in `site.css`:

| Component | Class | Used on |
|---|---|---|
| Dark top band | `.hero`, `.hero--page` | every page |
| Card | `.card`, `.panel-card` | Home, Testing, About, Thank-you |
| Numbered steps | `.steps` | Home, How to Start |
| Highlighted note | `.callout` | startup benefit (Home, How to Start) |
| Limits box | `.limits` | Testing, About |
| FAQ | `.faq` + native `<details>` | How to Start |
| CTA band | `.cta-band` (partial) | all marketing pages |
| Form | `.form`, `.form-row`, `.field-error`, `.error-summary`, `.notice-phi` | Contact |

## CSS

- **Tokens first.** Colors, type sizes, spacing and radius are CSS custom properties at the top of
  `site.css`. Change brand values there only. Contrast ratios are noted next to each color.
- **Mobile-first.** Base rules are for phones; `@media (min-width: 40rem)` and `(min-width: 60rem)`
  add tablet/desktop layout. A narrow rule `(max-width: 29.99rem)` compacts the header on small phones.
- **BEM-ish naming:** `.block`, `.block__part`, `.block--variant`.
- Focus ring: `:focus-visible` uses `--color-focus` (amber), visible on both navy and white.

## JavaScript (`assets/js/site.js`)

One IIFE, five independent functions, no dependencies:

| Function | What it does | Without JS |
|---|---|---|
| `initMobileNav` | Menu button toggles `#site-nav`, keeps `aria-expanded` in sync, Escape closes | Nav is always shown (CSS only collapses it when `<html class="js">`) |
| `initPortalLinks` | If `INNOVEX_CONFIG.portalUrl` is an `https://` URL, sets `href` on every `[data-portal-link]`, opens in new tab, unhides wrappers, hides `[data-portal-fallback]` | Portal links stay hidden; "call the lab" fallback shows |
| `initFooterYear` | Fills `[data-year]` | Static year in HTML |
| `initPanelPreselect` | `contact.html?panel=uti` preselects the panel `<select>` | Visitor picks the panel |
| `initFormValidation` | Inline, screen-reader-announced errors + error summary; disables the button while sending | Browser's native `required`/`type=email` validation |

Links inside the site are **root-absolute** (`/testing.html`, `/assets/...`) so pages can live in
subfolders (e.g. a future `/testing/uti.html`) and still share the same header/footer. Preview with
`python -m http.server` from the repo root (opening files directly via `file://` will not resolve them).

**No-JS fail-safe:** an inline `<head>` script adds `class="js"` (so the phone menu can start
collapsed without flashing open) and removes it again on `load` if `site.js` never set
`window.INNOVEX_READY`. A failed script therefore leaves the menu visible rather than stuck closed.

## Partials

Pages contain marker comments:

```html
<!-- PARTIAL:header -->
...generated, do not edit here...
<!-- /PARTIAL:header -->
```

`python tools/sync_partials.py` replaces everything between the markers with `partials/header.html`
(and likewise `cta-band`, `footer`). It adds `aria-current="page"` to the nav link whose
`data-nav` matches the page's `<body data-page="…">`. `--check` exits non-zero if any page is stale;
`tools/check_site.py` runs it automatically.

To add a page: copy an existing page, change `<title>`, description, canonical, `og:*`,
`data-page` and content; add it to `sitemap.xml` (and to `partials/header.html` nav if it belongs
there); run sync + checks.

## SEO

Each page has a unique `<title>`, meta description (50–160 chars), canonical URL on
`https://www.innovexlab.com`, Open Graph tags, and is listed in `sitemap.xml` unless `noindex`.
Home carries `MedicalBusiness` JSON-LD limited to facts the site already publishes (name, address,
phone, email). Add hours, accreditation or service area to it **only** once verified.

## Not in this repository (by design)

- Patient data of any kind; the site never asks for it.
- The client test portal (external system; we only link to it).
- The future private staff workspace (a separate authenticated app with its own hosting; GitHub
  Pages cannot run server code and this repo is public).
- Internal marketing evidence, pricing and review notes (kept in the private project docs).
