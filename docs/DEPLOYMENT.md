# Deployment, operations and backups

## Hosting facts (verified 2026-11-15 via the GitHub API)

| Item | Value |
|---|---|
| Repository | `Innovexlab/innovexlab.github.io` (public), default branch `main` |
| Hosting | GitHub Pages, legacy (Jekyll) build from `main`, folder `/` |
| Custom domain | `www.innovexlab.com` (from `CNAME`); HTTPS enforced |
| Apex domain | `innovexlab.com` redirects to `www` (observed in the September 2026 audit; recheck) |
| DNS provider / owner | **Unknown.** Record here once confirmed |
| Who can push to `main` | Repository admins of the `Innovexlab` organization. **Record names/roles here** |

## How a release works

GitHub Pages publishes whatever is on `main`. A merge **is** a deployment. A tag or a local branch
on its own changes nothing in production.

### Getting a branch onto GitHub (needs someone with write access)

A contributor without push rights can't publish a branch. Choose one, with the owner's approval:

- **A. Grant access:** an `Innovexlab` org admin gives the contributor write access, then
  `git push -u origin <branch>` and open a pull request.
- **B. Admin pushes from a bundle:** the contributor sends `backups/innovexlab-site-YYYY-MM-DD.bundle`;
  the admin runs `git fetch <bundle> <branch>:<branch> && git push -u origin <branch>`.
- **C. Fork pull request:** the contributor forks the (public) repo, pushes the branch to the fork and
  opens a PR. The branch becomes publicly visible, so get the owner's OK first.

### Release steps

1. Work on a branch; run `python tools/check_site.py` (must print `OK`) and
   `python tools/run_browser_smoke.py` (must print `SUMMARY: PASS`; exit code 2 means the browser
   could not run, which is **not** a pass). Then `python tools/run_keyboard_check.py` and
   `python tools/run_axe_check.py --axe package/axe.min.js` and `python tools/run_security_check.py`
   (all `SUMMARY: PASS`; same exit codes).
   None of these sends the contact form.
2. Open a pull request. Complete the checklist in the PR template, including reviewer approvals for
   any clinical, billing, operational or credential copy (see [CONTENT_RULES.md](CONTENT_RULES.md)).
3. The owner reviews a local preview or screenshots and approves the release.
4. Before merging, tag the current live state so rollback is one command:
   `git tag -a live-YYYY-MM-DD -m "Live before <change>" origin/main && git push origin live-YYYY-MM-DD`
5. Merge. Watch **Settings → Pages** or the Actions tab until the "pages build and deployment" run
   is green (about a minute).
6. Post-release smoke test on the live site, phone and desktop:
   - Every nav link, the meeting button and `tel:` link work
   - Form submits and lands on `/thankyou.html`; the marked test arrives in the inbox
   - `https://innovexlab.com` redirects to `https://www.innovexlab.com`; `/sitemap.xml`, `/robots.txt` load
   - A missing URL shows the custom 404 page
7. Record the release: date, merge commit, URL, who approved, smoke-test result (CHANGELOG + the
   private session log).

## Rollback

The site is static, so rollback is a revert:

```bash
git switch main && git pull
git revert --no-edit <merge-commit>      # preferred: keeps history
git push origin main
```

Or restore everything to a tagged state in a new commit:
`git checkout live-YYYY-MM-DD -- . && git commit -m "Roll back to live-YYYY-MM-DD"`.
Never force-push `main`.

The pre-refresh site is tagged **`baseline-live-2026-11-15`** (commit `5052c20`).

## Redundancy and backups

| Copy | Where | How it's kept current |
|---|---|---|
| Primary | GitHub `Innovexlab/innovexlab.github.io` | Pull requests / merges |
| Working clones | Each developer's machine | `git pull` |
| Offline bundle | `backups/` folder in the shared project workspace (synced by OneDrive) | `git bundle create backups/innovexlab-site-YYYY-MM-DD.bundle --all` after each milestone |
| Tags | `baseline-live-2026-11-15`, `live-YYYY-MM-DD` | Before every release |

Restore from a bundle: `git clone backups/innovexlab-site-YYYY-MM-DD.bundle innovexlab.github.io`.
Verify a bundle: `git bundle verify <file>` (run inside any git repository).

**What a bundle does and doesn't hold:** a git bundle contains **committed history, branches and
tags only**. Uncommitted edits, untracked files, ignored files (screenshots, generated test
fixtures), local git config and GitHub settings (Pages, branch protection, secrets) are **not** in
it. Commit before bundling and check `git status --short --ignored` first.

**Restoring production is a release, not a restore:** cloning a bundle or checking out a tag only
changes a local copy. Production changes only when the restored content is merged into `main` on
GitHub (see Rollback).

**Recommended (owner action):** in GitHub → Settings → Branches, protect `main`: require a pull
request and the `site-checks` status check before merging, and block force-pushes.

## Contact form (FormSubmit)

### Request to receipt: what happens

1. **In the browser:** `site.js` checks the fields (inline errors plus a summary). Without JavaScript
   the browser's own `required` / `type=email` checks run. Both are covered by the browser tests.
2. **Submit:** the browser POSTs to `https://formsubmit.co/info@innovex-lab.com`. The button shows
   "Sending…" and is disabled, so a second click can't resubmit. If the visitor comes back with
   **Back**, the button is re-enabled (`pageshow`) so they can retry.
3. **At FormSubmit:** captcha and spam checks, then an email to the inbox. If the form address isn't
   activated yet, FormSubmit sends an activation email instead and **holds** the submission until
   someone confirms (per its FAQ).
4. **Redirect:** `_next` sends the visitor to `/thankyou.html`. **A redirect is not proof of
   delivery.** The thank-you page doesn't claim delivery and tells people to call if they don't hear back.
5. **Provider failure:** FormSubmit's own error page is shown; the site can't detect this. The
   visitor goes Back and can retry. Under the form there is always a fallback: "If the form doesn't
   go through, call (352) 328-3066 or email info@innovex-lab.com."

### What FormSubmit documents (read 2026-11-15) and what it doesn't

- Activation is triggered by the **first submission** and is tied to the **email address in the
  form action**: changing the address needs a new activation. The docs **don't say** whether
  activation also depends on the website domain, so whether a preview or `localhost` submission
  activates the production form is **unknown**.
- Pages opened as `file://` don't work; a page served by a web server is required.
- Submissions are held for 30 days; the `_honey` field silently drops spam.
- `_replyto` sets Reply-To. The docs imply the form's email field supplies it but don't state that
  a field named `email` does this automatically. Check it in the receipt test.
- The docs don't state rate limits, error codes or what visitors see during an outage.
- The live site **already** posts to the same address, so it may already be activated. Nobody has
  confirmed this.

### Receipt test (task W03; a launch acceptance check)

Any real submission sends a real email, so it needs the owner's specific go-ahead and an agreed
recipient, wherever it's sent from. Options:

- **Before release:** with the owner's OK, submit one marked test (`TEST, please ignore`) from a
  served preview (for example `http://127.0.0.1:8765/contact.html`). This tests activation and
  delivery to `info@innovex-lab.com`. `_next` still points to the live thank-you page.
- **At release:** submit the same marked test from `https://www.innovexlab.com/contact.html` on a
  phone off the office network.

Pass criteria, recorded with date, time and who checked:

- the email arrives in the `info@` inbox (check spam);
- every field is present, including `panel_interest`, `meeting_preference` and `lead_source`;
- **Reply** goes to the sender's address;
- a named person owns replies.

If any step fails, the phone and email fallback stays as the contact path, and the release is
treated as incomplete.

- Recommended hardening: replace the plain email in the form action with FormSubmit's random alias
  string, which is sent after activation, so the address isn't scraped from the HTML.
- Captcha is enabled (the old `_captcha=false` was removed) to cut spam.

## Client Portal switch (task W04)

1. Obtain the exact HTTPS login URL from the portal owner and which functions it supports.
2. Test sign-in, password reset and support contact with a permitted test account.
3. Set `portalUrl` in `assets/js/site-config.js`. Run checks, preview, release as above.
Links then appear in the header utility bar, mobile menu, footer, Contact and How to Start pages.

## Where internal docs live

Internal project management (state, task queue, decisions, session log, claim register, marketing
evidence) is kept **outside this public repository**, in the private project-docs repository
(`Innovex_Website_Claude_Code_Handoff_2026-11-15/` in the team's project workspace). Ask the project
owner for access. Do not copy those documents into this repository.
