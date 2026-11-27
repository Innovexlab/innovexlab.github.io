# Changelog

Format: newest first. Record **deployments** separately from implementation: an entry is "Released"
only when merged to `main` and smoke-tested on the live site.

## Unreleased — home-page video (2026-11-25)

### Added
- Home page: "InnovexLab in one minute", the owner's commercial (cut_02) in a native video player.
  It loads only when played (poster image first), is compressed to 18 MB (1080p, H.264) and
  carries English captions (`assets/video/innovexlab-overview.en.vtt`) and a transcript, with
  "Tests are billed separately." beneath it.

### Changed
- Content-Security-Policy on every page adds `media-src 'self'` so the video and captions can load.
- `check_site.py`: `OWNER_APPROVED_LINES` exempts only the three exact narration sentences the owner
  approved on 2026-11-25 (speed, brief-based collection, no-cost onboarding); `.mp4` is allowed only
  under `assets/video/`.

## Unreleased — design polish and copy review (2026-11-18)

### Fixed
- Cards in two-column grids (testing page, clinical overview) no longer sit out of line: a stacked-card
  margin also applied inside grids.
- Medical wording: rotavirus vaccine scope (rotavirus A), influenza C (no seasonal epidemics),
  Lactobacillus iners (not protective), dermatophytes (main cause as a group), chlamydia and
  trichomonas ("the cause of" an infection), MERS dated to 2012, trichomonas resistance ("uncommon"),
  E. coli and ESBL treatment wording, Pneumocystis grouped under its own fungus heading.
- Awkward acronym expansions: AmpC and TEM glosses shortened, CD4 explained after "count", "DNA gyrase"
  left as the enzyme name, slash-joined acronyms (IDSA and SHEA; NIAID, NIH) now explained.

### Changed
- Home hero shows a laboratory photograph beside the headline on desktop; the duplicate home contact
  section was removed (the call-to-action band and footer carry the same details).
- Header: the consultation button sits after the navigation on desktop; navigation uses sentence case.
- Footer: links in two labelled columns (Laboratory, Resources), including Sources and disclaimer.
- FAQ questions show a plus/minus indicator.
- Testing page: panel links read "View all targets" and "Discuss this panel" (panel name for screen
  readers); the repeated consultation block before the call-to-action band became "Adding a panel".
- About page: clinical resources moved beside the interpretation box; COLA row reads "COLA-accredited".
- Organism library and panel target cards use one descriptive sentence per organism
  (`tools/content/cards.py`) instead of alias lists or clipped plural sentences; resistance-gene
  targets on panel pages say what the genes are, in words.
- Organism pages: the resistance heading names the drug type (antibiotic, antiviral, antifungal);
  the notice no longer mentions susceptibility results on virus and parasite pages.
- Panel pages: full panel names in headings, breadcrumb Testing / Panels, and a gene-specific caveat
  on the resistance panel.
- Getting-started photo replaced with one that shows no identifiable person
  (`lab-sample-tube.jpg`, USDA APHIS 20230621-CDP-APHIS-0498, public domain); `lab-benches.jpg` removed.

## Unreleased — acronyms and laboratory photos (2026-11-17)

### Changed
- Every acronym is spelled out at its first use on each page (for example, "urinary tract infection
  (UTI)", "Centers for Disease Control and Prevention (CDC)"); glossary in `tools/content/acronyms.py`,
  applied by `tools/expand_acronyms.py` and enforced by `check_site.py`. Header, footer and
  credentials band use `<abbr>` tooltips, and the credentials band has a one-line note that spells
  out CLIA, COLA and PCR. Testing-area names read "Urinary tract infection (UTI)" and
  "Sexually transmitted infection (STI)", matching "Gastrointestinal (GI)".
- Image credits now read "Photographer, CDC" instead of "CDC (Photographer)"; CDC treatment-guideline
  citations use the full title "Sexually Transmitted Infections Treatment Guidelines".
- Organism title "SARS-CoV-2 (COVID-19)" is now "SARS-CoV-2"; varicella-zoster virus reads
  "(human herpesvirus 3, HHV-3)".

### Added
- Three decorative laboratory photographs (public domain, USDA), on Home, Testing and Getting
  Started, credited on the sources page with a note that they do not show InnovexLab's facility.

### Fixed
- Data-table row headers may wrap (`min-width: 12rem` instead of `nowrap`), so long organism names
  no longer push links off-screen at 390px.

## Unreleased — professional rewrite

### Changed
- All pages rewritten in a clinical, declarative register for clinicians and administrators: no
  explanatory basics, scenario stories or slogans; panel cards now "Indication" / "Clinical use";
  limitations stated once, plainly. Billing FAQ answer kept verbatim.
- One call to action, "Request a consultation", replaces the repeated "Book a 15-minute panel review";
  nav label "How to Start" → "Getting Started" (URL unchanged).
- Credentials: CLIA certification (CLIA #10D2306552, high-complexity) and COLA accreditation
  (COLA ID 33609), owner-supplied 2026-11-16, in a band under the hero (Home, About), the utility bar,
  footer, About and JSON-LD. `check_site.py` pins both numbers; licence/CAP/ISO/FDA claims stay blocked.
- Visual: squarer corners, flatter shadows, plain navy hero (banner text contrast now ≥ 7:1), outlined
  step numerals, testing-services index and feature columns on Home.

## Released 2026-11-16 — logo (PR #2)

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
