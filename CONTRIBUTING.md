# Contributing

Thanks for working on innovexlab.com. Read [README.md](README.md) first, then
[docs/CONTENT_RULES.md](docs/CONTENT_RULES.md) before changing any visible text.

## Branches

- `main` is **live**. Every merge to `main` publishes the website.
- Work on a short-lived branch named `<type>/<topic>`:
  `content/…` (copy), `feature/…`, `fix/…`, `docs/…`, `chore/…`.
- Keep one purpose per branch so a reviewer can approve copy separately from code if needed.

## Commits

- Present-tense summary under ~72 characters, then a blank line and the *why* if it isn't obvious.
- Reference the task ID when there is one, e.g. `W03: add reply-to handling to contact form`.
- Commit the regenerated pages together with any partial you changed.

## Before you open a pull request

```bash
python tools/sync_partials.py   # if you edited anything in partials/
python tools/check_site.py      # must print OK
python tools/run_browser_smoke.py   # if you touched JS, forms or navigation
python tools/run_keyboard_check.py  # if you touched markup, CSS, JS or navigation
python tools/run_security_check.py  # if you touched <head>, scripts, the form or the portal (docs/SECURITY.md)
python tools/run_axe_check.py --axe package/axe.min.js   # before a release (download: see the script)
```

Then check by hand:

- Phone width (390px) and desktop; no horizontal scrolling
- Keyboard only: Tab through the page; focus is always visible; the menu opens and Escape closes it
- Every new statement about tests, billing, logistics, people or credentials has an approver (CONTENT_RULES)
- No patient information, secrets or internal documents added

## Pull requests

Fill in the template. Attach phone and desktop screenshots for visual changes. Name the reviewer
for each kind of claim the PR touches. The owner approves anything that will be published.

## Code style

- HTML: semantic elements (`header`, `nav`, `main`, `section`, `article`, `footer`), one `<h1>` per
  page, labels on every form field, `alt` on every image. 2-space indent.
- CSS: use the tokens at the top of `site.css`; no inline styles; mobile-first media queries.
- JS: plain ES5-compatible JavaScript, no dependencies, everything must still work without it.
- Comment the *why*: explain rules and constraints (e.g. why a link is hidden), not what the
  markup obviously does.

## Adding a check

When a reviewer catches a problem by hand, add a rule to `tools/check_site.py` so it can't recur.
Add a short reason string. The script's docstring lists what each section covers.
