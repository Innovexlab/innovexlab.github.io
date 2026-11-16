# Focused clinical pages: layout and rules

A focused page covers **one panel for one care setting**, such as UTI testing for long-term care. It goes deeper than the Testing card for the same panel. The first one is `testing/uti.html` (draft branch `draft/w06-uti-page`); copy it to start a new one.

Every sentence on a focused page follows [CONTENT_RULES.md](CONTENT_RULES.md). Clinical sentences need the lab director's review, and billing sentences need billing's, **before the page is released**. A page is drafted on its own branch and is never merged with the public-site release by default.

## Section order (keep it)
| # | Section | What goes in it | What never goes in it until evidence and approval exist |
|---|---|---|---|
| 1 | Hero | Breadcrumb (`Testing / <Panel>`); h1; one **clinician-assessed** situation; the general mechanism line; buttons "Review the <panel> panel" (`/contact.html?panel=<id>#book`) and the phone number | Turnaround or speed; accuracy; named targets; a single nonspecific sign as the reason to test |
| 2 | When to test | Who the panel is for, stated as symptoms assessed by a clinician; when **not** to test (screening/colonization), if relevant; a "Before you order, ask" callout (`div.callout role="note"`) | "Test everyone", outbreak-control or outcome promises |
| 3 | What the result can inform | Three cards: what is detected (no names), what the result can inform, "alongside culture, not instead of it" | Organism or gene names, counts, performance |
| 4 | Limits + alongside your current lab | The honest limits list (same substance as Testing); keep-your-current-lab line; startup line **always** followed by "Tests are billed separately" | Prices, "free testing", payer promises without the Part A exception |
| 5 | Review agenda | Four steps (which patients, the specimen, results, first order); who should join; booking button | Specimen instructions, courier, result channels |
| 6 | Questions | `details/summary` FAQ. Answers **reuse wording already on Testing or How to Start**; anything not documented is "confirmed in the panel review" | New facts that appear nowhere else on the site |

Mark where a future proven fact would go with an HTML comment starting `EVIDENCE TASK (<topic>)`. `check_site.py` ignores comments, so the note can name the gated topic.

## Adding a page (checklist)
1. Branch from the release branch, e.g. `draft/wNN-<panel>-page`.
2. Copy `testing/uti.html` to `testing/<panel>.html`. Change the title (unique), the description (50–160 characters, unique), the canonical and `og:url`, and `?panel=<id>`. The id must be one of the contact form's `<option value>`s.
3. Add the page to `sitemap.xml` and to `PAGES` in `tests/browser_smoke.html`. `tools/run_keyboard_check.py` and `tools/run_axe_check.py` pick up every `testing/*.html` page automatically.
4. Link to it from that panel's card on `testing.html` ("More about <panel> testing…").
5. Run `python tools/sync_partials.py`, then every check in [DEPLOYMENT.md](DEPLOYMENT.md) step 1. Take screenshots at 390px and 1366px.
6. Open a pull request marked **draft** until the lab director (and billing, if billing is mentioned) has signed the exact wording.

## Field links
Printed or emailed links to a focused page carry a `?src=` code ([MEASUREMENT.md](MEASUREMENT.md)). Don't print a QR code for a page that isn't live yet.
