# Instructions for AI coding assistants (Claude Code and similar)

This is the **public** repository for www.innovexlab.com (GitHub Pages, static HTML, no build).

## Before editing

1. Read `README.md`, `docs/ARCHITECTURE.md` and **`docs/CONTENT_RULES.md`**.
2. If the private project docs are available in the workspace
   (`../Innovex_Website_Claude_Code_Handoff_2026-11-15/`), follow its `CLAUDE.md` session workflow
   and update its PROJECT_STATE / TASKS / SESSION_LOG. Never copy those files into this repo.
3. `git status` and `git log --oneline -5`; preserve others' work; never commit directly to `main`.

## Rules

- Improve the existing static site; don't introduce a framework or build step without an
  owner decision recorded in the private decision register.
- Edit shared header/footer/CTA in `partials/`, then `python tools/sync_partials.py`.
- `python tools/check_site.py` must print OK before any commit.
- Public copy must follow `docs/CONTENT_RULES.md`. Do not add test targets, turnaround, accuracy,
  accreditation, coverage, prices, logistics, result channels, people or hours without recorded
  evidence. Don't weaken `CLAIM_RULES` to make a check pass.
- Never set a Client Portal URL unless it has been verified by the portal owner.
- No secrets, CRM data, internal pricing or patient information. This repo is public.
- Do not push, merge or deploy without the owner's explicit approval. Distinguish implemented,
  verified, approved and deployed when reporting.
- Verify visual changes at 390px and desktop widths (headless Chrome screenshots are fine).
