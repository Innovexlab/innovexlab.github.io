# Changelog

Format: newest first. Record **deployments** separately from implementation: an entry is "Released"
only when merged to `main` and smoke-tested on the live site.

## Unreleased

### Added
- Innovex logo (official mark, confirmed by the owner 2026-11-16) beside the name in the header
  on every page, on a white disc so it reads on the navy header; PNG tab icon and home-screen
  icon (`assets/img/innovex-logo-96.png`, `favicon-48.png`, `apple-touch-icon.png`; ~41 KB total)

### Fixed
- Small phones: the header button's compact padding never applied (overridden by `.button`);
  brand, button and menu share one row again from 360px

## 2026-11-16 — Released (PR #1, merge `4f2ee72`)

Owner-authorized release of the refresh below. Clinical and billing reviewer sign-off deferred by
the owner to after launch; contact-form receipt test pending.


Implemented and checked locally (`tools/check_site.py` OK; visual check at 390px and 1366px).
Not yet owner-, clinically- or billing-reviewed. Not deployed.

### Added
- Security (docs/SECURITY.md): Content-Security-Policy and referrer-policy `<meta>` on every page;
  `check_site.py` section 9 (policy, inline-script hash, no inline handlers/styles/third-party
  scripts, JS injection sinks, portal URL form, Pages exclude list, forbidden tracked files);
  `tools/run_security_check.py`; CI actions pinned to commit SHAs, no persisted token, axe tarball
  sha512 checked before unpacking. Portal test fixtures now use .js files (no inline script).
- `testing.html`: eight testing areas, each with situation, what the result can inform, and a
  panel-specific review link
- `how-to-start.html`: four steps to a first order, who should join the review, practice-manager FAQ
- `404.html`, `sitemap.xml`, favicon
- Shared `assets/css/site.css` (design tokens), `assets/js/site.js`, `assets/js/site-config.js`
- `partials/` and `tools/sync_partials.py` for one shared header/footer
- `tools/check_site.py` automated checks; GitHub Actions workflow `site-checks`
- Client Portal links in header, mobile menu, footer, Contact and How to Start, **hidden** until a
  verified URL is configured
- Developer docs: README, ARCHITECTURE, CONTENT_RULES, DEPLOYMENT, CONTRIBUTING, CLAUDE.md

### Changed
- Home, About, Contact and Thank-you rewritten around one action: "Book a 15-minute panel review"
- Contact form: added role, phone (optional), panel, meeting preference, preferred times; patient-
  information warning; accessible inline validation; captcha re-enabled; redirect on `www` host
- Canonical URLs moved to `https://www.innovexlab.com/…` (the host GitHub Pages serves)
- `robots.txt` replaced (was WordPress boilerplate) and now points to the sitemap
- Mobile navigation with a menu button; phone number always in the header

### Removed
- Example target organisms on panel cards (pending the lab director's signed validated menu)
- Unsupported quality/performance wording ("high-quality", "accurate, timely", "precision",
  "efficient turnaround", "better outcomes")

### Fixed
- `CNAME` contained a stray second line; now exactly `www.innovexlab.com`

### Independent review fixes (same branch)
- Clinical copy: STI screening exception in the limits; UTI situation no longer suggests testing on
  a "sudden change" alone; "pathogen is involved" → "targeted pathogens are detected"; added
  negative-result and mixed-specimen resistance-gene limits
- Part A consolidated-billing exception stated plainly; dropped unverified "in writing" and
  "the options" (logistics)
- Thank-you page no longer implies confirmed delivery; FormSubmit privacy line under the form
- About: "clinical laboratory" → "laboratory" (licence wording is gated)
- Accessibility: two-tone focus ring (WCAG 1.4.11 on white and navy); `[hidden]` always wins;
  open phone menu scrolls at high zoom; menu closes after a link click; error summary no longer
  double-announced
- Robustness: phone menu can't get stuck closed if `site.js` fails (load-time fail-safe)
- All internal links root-absolute so pages can live in subfolders
- `check_site.py` now also scans meta/OG/JSON-LD/attributes, subfolder pages, speed/cost/service-
  area/result-channel/superlative/organism patterns, the Part A caveat, captcha/_next, ?panel values,
  duplicate ids, aria references and heading order
- New real-browser tests: `tools/run_browser_smoke.py` + `tests/browser_smoke.html` (19 checks)

### Stronger tests and tablet layout (same branch, 2026-11-16, session 4)
- `check_site.py`:
  - **case-exact links**: GitHub Pages is case-sensitive, but Windows and macOS are not;
  - no plain-http links;
  - every tel:/mailto: link uses the published number and inbox;
  - **form contract**:
    - POST to FormSubmit;
    - required hidden fields present;
    - one `email` reply-to field;
    - unique field names;
    - spam trap hidden and untabbable;
    - every required field has its error message.
  - Twelve planted faults are each caught.
- Browser smoke tests went from 37 to 55 checks:
  - choosing a menu link closes the menu, and the menu lists all four pages;
  - spaces-only answers are flagged;
  - typed answers survive a failed submit;
  - every error-summary link points at a real field;
  - over-long and spaced `?src=` codes are ignored;
  - the enabled portal is visible on desktop;
  - overflow, contrast and focus are checked at **320px** (WCAG reflow), 390, 768, 1024 and 1366px.
- Keyboard checks went from 96 to 111:
  - the Tab walk now includes the enabled-portal layout at both widths;
  - Windows High Contrast (forced colours): every Tab stop must draw a real outline. A shadow-only
    focus ring fails here, which the planted-fault test confirmed.
- New optional `tools/check_external_links.py`.
- Fixed: at tablet width (768px) the Home "What a molecular result adds" cards wrapped 2+1. Three-card
  grids now go straight from one column to three at 48rem.

### Keyboard and accessibility pass (same branch, 2026-11-16)
- New `tools/run_keyboard_check.py`: real Tab, Shift+Tab, Enter and Escape key events through the
  Chrome DevTools Protocol on every page at 1366px and 390px. Checks the skip link, full Tab order
  (reading order, nothing skipped, no trap), a visible and unobscured focus ring at every stop, the
  phone menu and the contact form's error summary. Result: 96/96 pass.
- New `tools/run_axe_check.py`: axe-core 4.10.2 (pinned by sha256, not committed) plus a worst-case
  contrast check for text on the hero gradients (lowest 4.78:1, needs 4.5:1).
- Fixed: side panels on Home, How to Start, About and Contact were `<aside>` inside `<main>`, a
  misplaced landmark for screen-reader users (axe `landmark-complementary-is-top-level`). They are
  now `<div>`; the Home startup callout is `role="note"`.
- Fixed: the thank-you page's meta description said the request "was sent". A redirect doesn't
  prove delivery, so it now points to the phone number. New `CLAIM_RULES` entry catches
  "was sent / was received / we received" wording.
- CI runs the keyboard and axe checks too (added; not yet run on GitHub).

### External source review follow-up (same branch, 2026-11-15)
- Home hero situation is now a clinician-assessed question (several residents coughing; decide on
  precautions and cohorting). It no longer opens on confusion plus a urine culture. `CLAIM_RULES`
  now flags "confusion"-type wording site-wide.
- Contact form: phone and email fallback under the form; button label restored on Back
  (`data-label-default`); business-only `lead_source` hidden field filled from `?src=` codes
  (`initLeadSource`); privacy line mentions the link code.
- Browser tests 19 → 37:
  - form retry/Back, fallback, lead source;
  - no-JS form native validation;
  - portal enabled, and blocked for non-https URLs;
  - per-page overflow, contrast and focus ring at 390px and 1366px;
  - desktop nav.
- Runner: throw-away Chrome profile, exit code 2 plus diagnostics when the browser returns nothing
  (environment failure, never a pass), console-encoding-safe output.
- Docs:
  - CONTENT_RULES separates draft-permitted lines from release-approved copy (none approved yet) and
    keeps the competitive story as evidence tasks;
  - DEPLOYMENT covers request-to-receipt, FormSubmit's documented behaviour and gaps, the receipt
    test, push options without write access, bundle scope, and that a tag doesn't change production;
  - new MEASUREMENT.md.

## Baseline — tag `baseline-live-2026-11-15` (commit `5052c20`)

The live site before the refresh: Home, About, Contact, Thank-you.
