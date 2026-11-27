# Content rules for public copy

InnovexLab is a CLIA-certified, COLA-accredited molecular laboratory working with clinicians and
facilities. Write in a clinical, declarative register for clinicians and administrators: state facts,
don't explain basics, no stories or slogans, one call to action ("Request a consultation").
Everything the website says about tests, timing, billing,
logistics or credentials may be relied on by a clinician or an administrator, and some statements are
regulated. These rules keep the site accurate. `tools/check_site.py` enforces the mechanical parts;
reviewers enforce the rest.

## The page pattern

Every page or section that sells testing should contain, in order:

1. **A situation** the reader has lived through (six residents coughing; a wound open at week four).
   Not "workflow", "stewardship" or "solutions".
2. **The mechanism**: molecular testing reads organisms and resistance genes directly from the
   specimen, without waiting for culture growth.
3. **The decision** the result can inform: precautions, cohorting, antibiotic choice while culture
   continues, whether to treat. "Better outcomes" is not a decision.
4. **An honest limit**, stated plainly: a positive PCR is not by itself a diagnosis of symptomatic
   infection; a resistance gene does not by itself determine susceptibility or treatment; culture and
   clinical assessment still matter.
5. **One action**: request a consultation (a 15-minute panel review with the laboratory).

Test for filler: delete every mention of Innovex and its testing. If the paragraph still says the
same thing, rewrite it.

## Voice

Short sentences, concrete nouns, one argument per page. Warm and confident; don't hedge every
sentence. American English. No exclamation marks in clinical copy.

**Acronyms.** Spell out every acronym at its first use on each page, as "urinary tract infection
(UTI)", then use the short form. Glossary: `tools/content/acronyms.py`. Generated pages are expanded
automatically by `tools/build_library.py`; after editing a hand-written page, run
`python tools/expand_acronyms.py`. Where the automatic wording would read badly (an acronym already
inside parentheses, or followed by one), the tool asks for hand wording instead. Headings and column
headers keep the short form; the text below them carries the expansion. In compact page chrome
(header, footer, credentials band) use `<abbr title="…">` and spell the term out in nearby text.
`tools/check_site.py` fails on an unexpanded first use or on an all-caps abbreviation missing from
the glossary.

**Photographs.** Decorative photos use `alt=""` and are credited on `learn/sources.html`. Stock or
agency photos must not be presented as InnovexLab's facility, staff or equipment.

## What needs evidence before it can appear

The following require **documented evidence and a named reviewer's approval** before they are
published. Until then, leave them out entirely; do not replace them with vague wording or visible
placeholders.

| Topic | Examples of what NOT to write yet | Reviewer |
|---|---|---|
| Targets, specimens, devices, methods per panel | organism names outside `testing/panels/` and `learn/`, target counts, specimen types other than the UTI swab statement, platform names | Owner decision 2026-11-16: the requisition forms are the menu of record, and their target lists may appear on `testing/panels/` pages. Everything else in this row still needs the lab director |
| Turnaround / speed | "24-hour results", "same-day", "fast", "faster than your lab" | Lab director + measured lab data |
| Accuracy / performance | "accurate", "high specificity", "precision diagnostics", percentages | Lab director (validation data) |
| Accreditation and licences | CLIA certification and COLA accreditation **may be stated**, only with the recorded numbers (`CLIA_NUMBER`, `COLA_ID` in `check_site.py`; owner-supplied 2026-11-16). Florida licence, CAP, ISO, FDA status or any other accreditation still need records | Owner, transcribed from current certificates |
| Billing, coverage, cost | "no cost", "covered by Medicare", prices of any kind | Billing owner (and counsel where applicable) |
| Logistics | courier, pickup, service area, cut-off times, kit contents, delivery timing | Operations owner |
| Results delivery | portal, fax, EHR interface, critical-value calls | Operations owner / portal owner |
| People | names, titles, photos, bios | Each person's written consent |
| Hours, response times | "we reply within 1 business day" | Owner |
| Video and images | any media | Rights/consent and claim review |
| Comparisons | anything implying another lab is slower or worse | Not allowed without comparable data |

**Never:** patient information or realistic patient scenarios presented as real; invented
testimonials; "free testing"; guarantees; public prices.

## Draft-permitted lines (not yet release-approved)

Two different things:

- **Draft-permitted:** the internal proof register lists the sentence as usable wording. It may
  appear on a branch or preview.
- **Release-approved:** the named reviewer has signed off this exact wording for publication, with
  the date recorded in the private claim register. Text inherited from an earlier site or document
  does **not** count as approval.

**As of 2026-11-15, none of the lines below is release-approved.**

| Line | Reviewer needed before release | Notes |
|---|---|---|
| Menu (panel names) | Lab director | |
| Mechanism | Lab director | |
| Startup | Owner | Owner has confirmed the substance; the exact web wording isn't signed off |
| Billing (Part B / Part A) | Billing owner | Not confirmed |
| Self-pay | Billing owner | |
| Logistics | Operations owner | |
| Results | Operations owner | |
| Testing-page situations and limits | Lab director | Also the Home hero situation |

Change the text only with the relevant reviewer. Each line is marked in the HTML with a
`<!-- CLAIM: … -->` comment.

- Menu: "Innovex tests for respiratory, GI, urinary, wound, STI, women's health and nail fungal
  infections, plus antibiotic-resistance genes." (panel names only)
- Mechanism: PCR "reads organisms and resistance genes directly from the specimen, without waiting
  for growth."
- Startup: "Onboarding is free, and we provide the collection supplies needed to start using our lab.
  You can keep your current lab and use Innovex as an additional option." Always keep "Tests are
  billed separately" nearby.
- Billing: "For Medicare Part B and insured patients, we bill the payer directly, with no invoice to
  your facility." It must always be accompanied by the Medicare Part A skilled-nursing exception.
- Self-pay: "Uninsured? Ask us about self-pay options." (no price)
- Logistics: "Ask us how specimens get from your building to our lab."
- Results: "Results go to the ordering provider."

## The competitive story: kept, waiting for evidence

The claim checks keep unproven statements off the site. That doesn't mean they've been dropped from
the sales story. The site already uses these parts of it:

- the direct-from-specimen mechanism ("without waiting for culture growth");
- early information for a decision;
- adding one supplemental panel while keeping your current lab;
- a concrete 15-minute meeting.

These parts are **evidence tasks**. Each goes live as soon as its evidence is signed off:

| Story element | Evidence that unlocks it | Then |
|---|---|---|
| Measured speed (receipt-to-report time) | LIS turnaround data over a stated period, signed by the lab director | Publish the measured figure with its basis; relax the speed rule in `CLAIM_RULES` for that exact wording |
| Accuracy / performance | Per-target validation data | Name the performance claim per panel |
| Brief-material (incontinence-brief) collection | Validation for that specimen type plus lab-director approval | Feature it on the UTI page and in the video |
| Named targets per panel | Done for `testing/panels/` (owner adopted the requisition forms, 2026-11-16) | Organism names elsewhere, e.g. the Testing page, still need the lab director |
| Courier / service area | Operations confirmation | "We pick up from facilities in …" |

Ask for this evidence every review cycle. Don't let a gated element be dropped by default.

## Situations: clinician-assessed only

Scenario copy must describe a clinician-assessed infection question, such as urinary symptoms with a
suspected urinary source, or several residents coughing in one week. Never frame a single nonspecific
sign (for example, a change in mental status) as the reason to test. `CLAIM_RULES` flags
"confusion"-type wording.

## When evidence arrives

1. Record the evidence (document, date, approver) in the private claim register.
2. In one pull request: update the copy, update `CLAIM_RULES` in `tools/check_site.py` if a pattern
   becomes allowed, and note the approval in the PR description.
3. The reviewer named above approves the PR.

### Owner-approved exact lines

When the owner approves a specific sentence for publication although it matches a gate (without
the evidence above), list that exact sentence, per page, in `OWNER_APPROVED_LINES` in
`tools/check_site.py` and record the decision in the private decision register. The rule itself
stays in force for all other copy. Current entries: the three home-page video narration lines on
speed, brief-based collection and no-cost onboarding (owner approval 2026-11-25). The video's
"no cost" line is always shown with "Tests are billed separately."

## Forms and privacy

- Never add fields that collect patient information (names, DOB, results, insurance IDs).
- Keep the patient-information warning next to any free-text box.
- Do not add analytics that capture form contents. Measure delivered inquiries and booked meetings,
  not clicks alone.

## Clinical resources: disclaimer and citations

Every page under `learn/` and `testing/panels/` must show:

- the notice "General medical information for education only, not medical advice.";
- the **Medical disclaimer** block from `tools/build_library.py` (`DISCLAIMER`): not medical advice, no
  clinician–patient relationship, decisions belong to the treating clinician, call 911 in an emergency;
- organism and panel pages also need a **Sources** list.

Cite only public-health agencies and professional-society guidelines, using `tools/content/references.py`.
Open every new URL in a browser before adding it; cdc.gov refuses scripted link checks.
Credit each image in its caption, link its source page, and list it on `learn/sources.html`.
`tools/check_site.py` enforces the notice, the disclaimer and the Sources list.
