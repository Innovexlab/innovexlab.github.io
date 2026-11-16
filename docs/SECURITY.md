# Security notes (developers)

The site is static HTML, CSS and a small amount of plain JavaScript on GitHub Pages. There is
no server code, database, login, cookies or analytics. What a visitor's browser runs, and where
it sends anything, is set by the files in this repository. This page explains the protections
in place and how to keep them working. **It is not a statement that the site has no
vulnerabilities.**

Found a security problem? Don't open a public issue. Contact the lab privately at
info@innovex-lab.com or (352) 328-3066.

## What GitHub Pages can and cannot do

| Control | On GitHub Pages | What we do |
|---|---|---|
| HTTPS | "Enforce HTTPS" setting; http:// redirects to https:// | Keep it on; every link and asset is https or same-site (`check_site.py`) |
| Custom HTTP response headers (CSP, `X-Frame-Options`, `Referrer-Policy`, `Permissions-Policy`, HSTS) | **Not supported**: no `_headers` file, no server config | CSP and referrer policy as `<meta>` tags (below) |
| `frame-ancestors` (anti-framing), `report-uri`/`report-to`, `sandbox` | **Ignored in a `<meta>` CSP** (header only) | Not available; accepted risk (no logged-in actions to hijack) |
| Publishing only some files | `_config.yml` `exclude` list (Jekyll) | Every developer-only path is excluded; `check_site.py` fails if a new one isn't |

Adding headers would need a CDN or proxy in front of Pages (for example Cloudflare). That is a
new service and needs an owner decision; it is not set up.

## Content-Security-Policy (every page, in `<head>`)

```
default-src 'none'; script-src 'self' 'sha256-…'; style-src 'self'; img-src 'self';
font-src 'self'; form-action 'self' https://formsubmit.co; base-uri 'none'; object-src 'none'
```

- **Scripts:** only `/assets/js/*.js` from this site, plus the one small inline `<head>` script
  (the `js` class fail-safe), which is allowed by its sha256 hash. No inline event handlers
  (`onclick=`), no `eval`, no third-party scripts.
- **Styles, images, fonts:** this site only. No `style=""` attributes, which the policy blocks.
- **Forms:** may only post to FormSubmit, or to this site. `'self'` is needed because
  browsers also apply `form-action` to the redirect back to `/thankyou.html`.
- **Everything else** (fetch/XHR, frames, plugins, `<base>`) is blocked.
- JSON-LD (`<script type="application/ld+json">`) is data, not code. The policy doesn't block
  it and it needs no hash.

The `<meta>` must stay **before** every `<script>` and stylesheet. The policy only covers what
comes after it.

### If you change the inline head script
Its hash changes. `python tools/check_site.py` then fails and prints the exact new `<meta>` to
paste into every page. Don't "fix" this with `'unsafe-inline'`; `check_site.py` rejects it.

### If you need a third-party service (fonts, maps embed, analytics, chat)
It needs an owner decision first (privacy notice, and no patient data). Then add its exact
origin to the matching directive in every page and in `CSP_TEMPLATE` in `tools/check_site.py`,
and run `tools/run_security_check.py`. Never use `*`, `data:` or `http:`.

## Referrer policy

`<meta name="referrer" content="strict-origin-when-cross-origin">`. Other sites (including
FormSubmit and Google Maps) see only `https://www.innovexlab.com/`, never the page path or a
`?src=` code. This matches modern browsers' default; the tag makes it explicit for all browsers.

## JavaScript rules (`assets/js/`)

- Build DOM with `textContent`, `createElement` and `setAttribute`. Never `innerHTML`,
  `outerHTML`, `insertAdjacentHTML`, `document.write`, `eval`, `new Function` or string
  timers. `check_site.py` (`UNSAFE_JS`) enforces this. The one allowed `innerHTML` use is
  clearing a list (`= ""`).
- URL parameters are untrusted. `?panel=` only selects an existing `<option>`. `?src=` is kept
  only if it matches `^[a-z0-9-]{1,40}$`, and is re-checked when read back from
  `sessionStorage`.
- The portal URL comes only from `site-config.js` and is used only if it starts with
  `https://`. `check_site.py` also rejects credentials, spaces and quotes.

## The contact form

- Posts to FormSubmit over HTTPS. FormSubmit emails the lab's inbox; it is a third-party
  processor, and the page says so.
- **No patient information:** there are no patient fields (enforced), and a warning sits
  beside the free-text box. FormSubmit is not a HIPAA business associate of the lab, so don't
  add fields or wording that invite PHI.
- Spam: FormSubmit captcha on (`_captcha=false` is rejected), plus the `_honey` trap.
- The tests never send the form. `run_keyboard_check.py` and `run_browser_smoke.py` block
  formsubmit.co. `run_security_check.py` intercepts the POST in the browser and answers it
  locally. A real delivery test needs the owner's specific authorization (DEPLOYMENT.md).

## CI (`.github/workflows/site-checks.yml`)

Read-only token, `pull_request` trigger (not `pull_request_target`), actions pinned to commit
SHAs, `persist-credentials: false`, and axe-core verified by tarball sha512 and file sha256.
When updating an action, change the SHA and the version comment together.

## Never commit (the repository is public)

Secrets, tokens, `.env` files, backups/bundles, CRM or lead exports, spreadsheets, internal
pricing, private project records or patient information. `.gitignore` and `check_site.py`
(`FORBIDDEN_TRACKED`) block the common cases. Git history is public too: if something slips
in, removing it in a later commit is not enough. Tell the repo admin so it can be rotated or
purged.

## Checks

```
python tools/check_site.py          # static rules, incl. section 9 "security"
python tools/run_security_check.py  # in Chrome: 0 policy violations on every page,
                                    # policy enforced (controls), injection payloads inert,
                                    # portal switch, form POST intercepted (never sent)
```
