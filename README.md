# innovexlab.com

Public website for **InnovexLab**, a molecular infection-testing laboratory in Gainesville, Florida.
Served by **GitHub Pages** from the `main` branch of this repository at <https://www.innovexlab.com/>.

The site has one job: help a practice or facility understand one useful molecular-testing use case
and **request a consultation** (a 15-minute panel review). Existing clients get a separate, clearly marked **Client Portal** link
once the portal address has been verified.

> **This repository is public.** Never commit passwords, API keys, CRM/prospect data, pricing
> proposals, internal review notes or any patient information. Internal project documents live in a
> separate private location (see [docs/DEPLOYMENT.md](docs/DEPLOYMENT.md#where-internal-docs-live)).

---

## Quick start (5 minutes)

Requirements: **Git** and **Python 3.9+**. No Node, no package install, no build step.

```bash
git clone https://github.com/Innovexlab/innovexlab.github.io.git
cd innovexlab.github.io
python -m http.server 8765          # preview at http://127.0.0.1:8765/
python tools/check_site.py          # static checks: links, SEO, claim rules (must print OK)
python tools/run_browser_smoke.py   # browser tests in headless Chrome (must end SUMMARY: PASS; exit 2 = browser could not start)
python tools/run_keyboard_check.py  # real Tab-key walk of every page at 1366px and 390px (SUMMARY: PASS)
python tools/run_axe_check.py --axe package/axe.min.js   # axe-core WCAG scan; see the script for the pinned download
python tools/run_security_check.py  # CSP, injection payloads, form request intercepted (never sent); docs/SECURITY.md
python tools/check_external_links.py   # optional, needs internet: external links still open (GET only)
```

Open <http://127.0.0.1:8765/> in a browser. Test at a phone width (390px) and desktop width using the
browser's device toolbar.

## Everyday workflow

1. Create a branch: `git switch -c <type>/<short-name>` (e.g. `content/uti-page`, `fix/form-labels`).
2. Edit pages. **Shared header, CTA band and footer live in `partials/`.** Edit the partial, then run
   `python tools/sync_partials.py` to copy it into every page.
3. Run `python tools/check_site.py` until it prints `OK`.
4. Preview locally on phone and desktop widths; tab through the page with the keyboard.
5. Commit with a clear message, open a pull request, fill in the PR checklist.
6. Content that makes a clinical, billing, operational or credential statement needs the matching
   reviewer's approval **before** merge. See [docs/CONTENT_RULES.md](docs/CONTENT_RULES.md).
7. Merging to `main` publishes the site (GitHub Pages rebuilds in about a minute).

Details: [CONTRIBUTING.md](CONTRIBUTING.md).

## Repository layout

| Path | What it is |
|---|---|
| `index.html` | Home: clinical situation → direct-from-specimen explanation → one-panel offer |
| `testing.html` | The eight testing areas, each with situation / what the result can inform / review button |
| `how-to-start.html` | Four steps from first conversation to first order, plus practice-manager FAQ |
| `about.html` | Who the lab is, location, honest limits. Credentials and team slots are placeholders in comments |
| `contact.html` | Meeting-request form (FormSubmit) + direct contact + existing-client path |
| `thankyou.html` | Shown after a form submit (`noindex`) |
| `404.html` | GitHub Pages "not found" page (root-absolute paths) |
| `assets/css/site.css` | The only stylesheet. Design tokens at the top |
| `assets/js/site.js` | Mobile menu, portal-link reveal, form validation, panel preselect, footer year |
| `assets/js/site-config.js` | **Single switch for the Client Portal URL** (empty = hidden) |
| `assets/img/` | Favicon and future approved images |
| `partials/` | Shared header, CTA band, footer (source of truth; copied into pages) |
| `tools/sync_partials.py` | Copies partials into pages; `--check` mode for CI |
| `tools/check_site.py` | Automated checks: links, metadata, headings, sitemap, claim rules, billing caveat, form, portal, ids/a11y |
| `tools/run_browser_smoke.py` + `tests/browser_smoke.html` | Real-browser tests of the menu, form validation, panel preselect, portal hidden/enabled/blocked, form retry/Back and no-JS behaviour, lead-source codes, no-JS menu fail-safe, and on every page at 390px and 1366px: no sideways scroll, text contrast, visible focus ring. Exit 2 = browser could not run (environment), never a pass |
| `tools/run_keyboard_check.py` | Drives Chrome with genuine key events (DevTools Protocol, standard library only): skip link, full Tab order with no trap, visible and unobscured focus ring at every stop, Shift+Tab, phone menu Enter/Escape, contact-form error summary by keyboard. Blocks formsubmit.co so nothing can be sent |
| `tools/run_security_check.py` | In Chrome: every page loads with zero Content-Security-Policy violations and no third-party requests; controls prove the policy is enforced; URL/sessionStorage payloads stay inert; the form's POST is intercepted and answered locally (never sent). See docs/SECURITY.md |
| `tools/check_external_links.py` | Optional (needs internet; not in CI): one GET per external link, skipping our own domain and the form service |
| `tools/run_axe_check.py` | axe-core 4.10.2 scan (WCAG 2.0–2.2 A/AA + best practice) of every page at both widths, plus a worst-case contrast check for text on gradients (which axe can't rate). axe is downloaded, not committed; the script checks its sha256 |
| `docs/` | Developer documentation (not published to the website) |
| `CNAME` | Custom domain for GitHub Pages: exactly one line, `www.innovexlab.com` |
| `_config.yml` | Tells GitHub Pages which developer files **not** to publish |
| `robots.txt`, `sitemap.xml` | Search engine files; sitemap lists every indexable page |

## Documentation

- [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md): how the site is built and why (no framework, partials, progressive enhancement)
- [docs/CONTENT_RULES.md](docs/CONTENT_RULES.md): what public copy may and may not say, and how claims get approved
- [docs/DEPLOYMENT.md](docs/DEPLOYMENT.md): hosting, DNS, releasing, rolling back, backups, the contact form and the portal switch
- [docs/FOCUSED_PAGES.md](docs/FOCUSED_PAGES.md): layout, rules and checklist for focused clinical pages (one panel, one care setting)
- [docs/MEASUREMENT.md](docs/MEASUREMENT.md): business-only measurement (`?src=` link codes, panel interest) and the team's link format
- [CONTRIBUTING.md](CONTRIBUTING.md): branches, commits, pull requests, review
- [CHANGELOG.md](CHANGELOG.md): what changed and when
- [CLAUDE.md](CLAUDE.md): instructions for AI coding assistants working in this repo

## Status (keep this short and current)

| Area | Status |
|---|---|
| Refreshed site | **Live** since 2026-11-16 (PR #1); logo PR #2; professional copy rewrite + credentials (this change). Clinical/billing reviewer sign-off pending |
| Contact form delivery to `info@innovex-lab.com` | **Unverified**: needs a marked test confirmed in the real inbox |
| Client Portal link | Built but **hidden** until the portal URL is verified |
| Ad video | Not added; waits for claim/rights review, captions and transcript |
| Credentials, team, hours | Not published; wait for transcribed certificates and consent |
