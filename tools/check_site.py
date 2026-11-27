#!/usr/bin/env python3
"""Automated checks for the InnovexLab static site (stdlib only).

Run before every commit and in CI::

    python tools/check_site.py

Exit code 0 = all checks passed, 1 = at least one failure (each printed).

What is checked, and why
------------------------
1. partials    Shared header/footer/CTA blocks match partials/ (run tools/sync_partials.py).
2. links       Every local href/src points to a real file (resolved relative to the page),
               with the exact upper/lower case of the file name (GitHub Pages is case-
               sensitive; Windows and macOS are not, so a wrong case passes locally and
               404s live), and every #fragment exists in its target page. No plain-http
               links. Every tel: and mailto: link uses the published phone and inbox.
3. metadata    Each page: lang="en", exactly one <h1>, no skipped heading levels going down,
               unique <title> and description (50–160 chars), canonical URL on
               https://www.innovexlab.com.
4. sitemap     sitemap.xml lists exactly the indexable pages (not noindex, not 404).
5. claims      Text a visitor or search engine can see — page text, <title>, meta/OG
               descriptions, JSON-LD, alt/aria-label/title/placeholder attributes — contains
               no claim that needs documented proof first (see CLAIM_RULES). Any page that
               talks about Medicare/payer billing must also carry the Part A consolidated-
               billing exception. CLIA numbers and COLA IDs must equal CLIA_NUMBER / COLA_ID.
               Rules come from the internal claim register (proof gates);
               when a gate closes with evidence, update CLAIM_RULES in the same pull request
               as the copy.
6. form        No patient-information fields; patient-info warning beside free text; every
               field has a <label>; FormSubmit captcha not disabled; _next is a real page on
               the canonical host; ?panel= links match the contact form's options.
               Form contract: posts (POST) to FORM_ACTION; carries _subject, _template,
               _next, lead_source and the _honey spam trap (tabindex=-1, autocomplete=off,
               inside an aria-hidden .hp-field that the CSS moves off-screen); exactly one
               type=email field named "email" (FormSubmit uses it as reply-to); field
               names are unique; every required field has data-label and an aria-
               describedby pointing at its "<id>-error" message element.
7. portal      Client Portal links are hidden in HTML; the configured URL is empty or https.
8. a11y/ids    No duplicate ids; aria-labelledby / aria-describedby / aria-controls / label[for]
               targets exist; images have alt; target=_blank links have rel="noopener".
9. security    (docs/SECURITY.md) Every page carries the same Content-Security-Policy <meta>
               (CSP_TEMPLATE, with the sha256 of every inline script filled in) before any
               script or stylesheet, plus the referrer policy <meta>. No inline event handlers,
               style="" attributes, javascript:/data: URLs or third-party scripts/stylesheets.
               assets/js/*.js contains no HTML-injection or eval-style sinks (UNSAFE_JS). The
               portal URL, if set, is a plain https URL. Every tracked developer-only path is
               excluded from GitHub Pages in _config.yml, and no backup/export/secret-type
               file is tracked in this public repository.

HTML comments and ordinary <script>/<style> code are ignored by the claim check, so
developer notes may mention gated topics. JSON-LD is NOT ignored.
"""
from __future__ import annotations

import base64
import hashlib
import os
import re
import subprocess
import sys
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import parse_qs, urlparse

ROOT = Path(__file__).resolve().parent.parent
SITE_ORIGIN = "https://www.innovexlab.com"
# Published contact points (FACT_REGISTER: published-before). If the owner changes one,
# update it here and in partials/ in the same pull request.
PHONE_TEL = "tel:+13523283066"
INBOX = "info@innovex-lab.com"
FORM_ACTION = f"https://formsubmit.co/{INBOX}"
FORM_HIDDEN_REQUIRED = {"_subject", "_template", "_next", "lead_source"}
NON_INDEXABLE = {"404.html", "thankyou.html"}
# Laboratory identifiers supplied by the owner on 2026-11-16 (company forms; COLA ID from the
# report template). Any CLIA-style number or COLA ID shown on the site must match exactly.
CLIA_NUMBER = "10D2306552"
COLA_ID = "33609"
# Folders that never contain public pages.
SKIP_DIRS = {".git", ".github", "partials", "tools", "docs", "tests", "node_modules"}

# --- Security policy (docs/SECURITY.md) --------------------------------------
# GitHub Pages cannot send custom HTTP headers, so the policy is a <meta> tag on every page.
# {inline} is replaced by the 'sha256-…' source of each inline <script> (the small "js"
# class/fail-safe script in each <head>). If you edit that script, this check prints the
# new policy to paste into every page.
#   form-action 'self' — FormSubmit may redirect back to /thankyou.html; Chrome applies
#                        form-action to redirects too.
CSP_TEMPLATE = ("default-src 'none'; script-src 'self' {inline}; style-src 'self'; img-src 'self'; media-src 'self'; "
                "font-src 'self'; form-action 'self' https://formsubmit.co; base-uri 'none'; "
                "object-src 'none'")
CSP_FORBIDDEN = ("'unsafe-inline'", "'unsafe-eval'", "'unsafe-hashes'", " data:", " *", "http:")
REFERRER_POLICY = "strict-origin-when-cross-origin"
# JavaScript sinks that turn text into HTML or code. site.js builds DOM with textContent and
# setAttribute only; the one allowed innerHTML use clears a list (= "").
UNSAFE_JS = re.compile(r"\.innerHTML\s*=(?!\s*\"\"\s*;)|\.outerHTML\s*=|insertAdjacentHTML|document\.write|"
                       r"\beval\s*\(|new\s+Function\s*\(|set(?:Timeout|Interval)\s*\(\s*[\"'`]|"
                       r"\.(?:href|src|action)\s*=(?!=)(?!\s*\"#\")|location(?:\.href)?\s*=(?!=)|\.srcdoc\b")
# Never tracked in this PUBLIC repo (backups, exports, secrets, private project records).
# Video is allowed only as published site media under assets/video/ (owner decision 2026-11-25).
FORBIDDEN_TRACKED = re.compile(r"^(?!assets/video/[a-z0-9-]+\.mp4$).*\.(bundle|env|pem|key|p12|pfx|csv|xlsx?|sqlite|db|zip|tgz|mp4|mov)$|"
                               r"(^|/)\.env|(^|/)(PROJECT_STATE|SESSION_LOG|TASKS|DECISIONS|FACT_REGISTER|"
                               r"REPO_MAP|LAUNCH_CHECKLIST|FIELD_LINKS|OWNER_REVIEW_PACKET)\b", re.I)
# Tracked paths GitHub Pages SHOULD publish. Everything else must be in _config.yml exclude
# (Jekyll already skips names starting with "." or "_").
PUBLISHED = re.compile(r"^(?:[^/]+\.html|(?:testing|learn)/(?:[^/]+/)?[^/]+\.html|assets/.+|CNAME|robots\.txt|sitemap\.xml)$")
# General clinical education (learn/*.html) and the panel pages (testing/panels/*.html) may name
# organisms and resistance genes. Panel targets follow the requisition forms, which the owner adopted as
# the menu of record on 2026-11-16 (private decision register). Every such page must show the
# education notice, the full medical disclaimer, and (organism and panel pages) a cited Sources list.
EDUCATION_DIR = "learn/"
MENU_DIR = "testing/panels/"
EDUCATION_NOTICE = "General medical information for education only, not medical advice."
DISCLAIMER_MARKS = ("Medical disclaimer", "It is not medical advice, a diagnosis or a treatment recommendation",
                    "In an emergency, call 911.")
SOURCES_REQUIRED = re.compile(r"^(learn/organisms/(?!index\.html)[^/]+|testing/panels/(?!index\.html|all-targets\.html)[^/]+)\.html$")
MENU_RULE_REASON = "target organisms/markers need the signed validated menu"
# Panel pages listing targets from the requisition forms are DRAFTS until the lab confirms the menu.
# They carry class="draft-banner", must be noindex, and FAIL this check unless INNOVEX_ALLOW_DRAFTS=1
# (set only on a draft branch), so they cannot be published by accident.
DRAFT_MARKER = 'class="draft-banner"'

# --- Claim rules -----------------------------------------------------------
# (regex, reason). Case-insensitive. Applied to visible/indexable text only.
CLAIM_RULES: list[tuple[str, str]] = [
    # Prices and numbers
    (r"\$\s?\d", "public prices are not allowed (counsel gate)"),
    (r"\d\s?%|percent", "percentages need documented evidence"),
    (r"\b\d+\s*(targets|pathogens|organisms|markers|genes)\b", "target counts need the signed validated menu"),
    # Speed / turnaround
    (r"\b\d+\s*-?\s*(hour|hr|h|day)s?\b|twenty-?four|within\s+\w+\s+hours?",
     "numeric turnaround/timing needs LIS evidence"),
    (r"turn-?around|same[- ]day|next[- ]day|overnight|\brapid\w*|(?<!acid-)\bfast(er|est)?\b|\bquick(ly|er)?\b|results in\b",
     "speed claims need measured receipt-to-report data"),
    # Credentials. CLIA certification and COLA accreditation were supplied by the owner on
    # 2026-11-16 (company forms + report template) and may be stated; CREDENTIAL_IDS below pins
    # the exact numbers. Anything else (Florida licence, CAP, ISO, FDA status, other
    # accreditation) still needs records first.
    (r"\b(CAP|ISO\s?15189|licen[cs]ed?|FDA[- ](approved|cleared))\b",
     "licence/CAP/ISO/FDA claims need documented certificates (only CLIA and COLA are on record)"),
    (r"(?<!COLA-)(?<!COLA )\baccredit\w*(?! by COLA)",
     "only COLA accreditation is on record; write 'COLA-accredited'"),
    # Logistics, results channels, service area
    (r"\b(courier|pick-?up|driver)s?\b", "courier/pickup coverage is not documented"),
    (r"\b(fax|EHR|EMR|HL7|interface)\w*\b", "result-delivery channels are not documented"),
    (r"statewide|across Florida|throughout Florida|\bserving\b|service area", "service area is not documented"),
    # Performance / quality / superlatives
    (r"faster than|more accurate|most accurate|high(ly)? accurate|\baccura(te|cy)\b|precision|high[- ]quality|"
     r"sensitivity|specificity|\bbest\b|leading|trusted|state[- ]of[- ]the[- ]art|world[- ]class",
     "performance/quality claims need per-target validation"),
    # Cost / coverage
    (r"guarantee\w*|always covered|no cost to (you|your patients|the facilit|your facilit)|free (test|testing|tests)|"
     r"free of charge|at no cost|Medicare covers|covered by|in-network",
     "coverage or free-testing promises are not allowed"),
    (r"better outcomes|improve\w* outcomes", "vague outcome claims fail the marketing standard"),
    (r"\b(brief|diaper)s?\b", "brief-material collection is not approved for release"),
    (r"\bconfus\w*|altered mental|mental status", "a mental-status change alone must not be framed as a reason to test "
     "(stewardship; external review 2026-11-15) — use a clinician-assessed infection question"),
    (r"\b(?:was|been) (?:sent|received|delivered)\b|\bwe(?:'|&rsquo;|’)ve received\b|\bwe received\b",
     "a redirect to the thank-you page does not prove the request reached the inbox; "
     "don't claim delivery (external review 2026-11-15, item 4)"),
    (r"testimonial|\bclients? say\b", "no invented testimonials"),
    (r"\bBennett\b", "partner is not named in external material"),
    # Example target organisms/markers. Allowed only after the lab director's signed, validated menu.
    (r"E\.\s?coli|Klebsiella|Enterococc\w*|Influenza|\bRSV\b|Mycoplasma|Chlamydia|Neisseria|gonorrh\w*|"
     r"Trichomonas|\bMRSA\b|Pseudomonas|Salmonella|Shigella|difficile|Trichophyton|Candida|"
     r"Gardnerella|Atopobium|\bESBL\b|carbapenem\w*|SARS-?CoV|COVID|norovirus|\bHPV\b|\bHSV\b|"
     r"Staph\w*|Strep\w*|Proteus|\bmecA\b|\bvanA\b|\bKPC\b",
     "target organisms/markers need the signed validated menu"),
]

# Exact lines the owner approved for publication although they match a CLAIM_RULES gate.
# Each entry is one sentence of the home-page video narration (captions and transcript),
# approved as cut by the owner on 2026-11-25 (private decision register). Only these exact
# sentences are exempt, and only on the listed page; the rules still apply to all other copy.
OWNER_APPROVED_LINES: dict[str, tuple[str, ...]] = {
    "index.html": (
        "Rapid results equates to a rapid response.",
        "Innovex offers brief-based specimen collection.",
        "Onboarding and initial collection supplies are provided at no cost.",
    ),
}

# Text that mentions payer billing must also include the Part A exception.
BILLING_MENTION_RE = re.compile(r"Medicare|bill the payer|insured patients", re.I)
PART_A_RE = re.compile(r"consolidated billing", re.I)

# Form field names that would collect patient information.
PATIENT_FIELD_RE = re.compile(r"patient|dob|birth|mrn|diagnos|ssn|insurance|member.?id|result", re.I)

# Attributes whose text a visitor or search engine sees.
VISIBLE_ATTRS = ("alt", "aria-label", "title", "placeholder")


class PageParser(HTMLParser):
    """Collects the facts the checks need from one HTML page."""

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.ids: list[str] = []
        self.id_refs: list[tuple[str, str]] = []   # (attribute, referenced id)
        self.links: list[str] = []
        self.text: list[str] = []                   # visible + indexable text
        self.title = ""
        self.meta: dict[str, str] = {}
        self.canonical = ""
        self.html_lang = ""
        self.headings: list[int] = []
        self.fields: list[dict[str, str]] = []
        self.panel_options: list[str] = []
        self.portal_links: list[dict[str, str]] = []
        self.forms: list[dict[str, str]] = []
        self.hp_hidden = False      # saw <div class="hp-field" aria-hidden="true">
        self.images_missing_alt = 0
        self.blank_without_noopener: list[str] = []
        self._skip_depth = 0       # inside ordinary <script>/<style>
        self._in_title = False
        self._in_jsonld = False
        self._in_panel_select = False
        # security (check 9)
        self.csp: list[tuple[int, str]] = []        # (tag position, policy)
        self.first_resource = 0                     # position of first <script>/<link rel=stylesheet>
        self.inline_scripts: list[str] = []
        self.script_srcs: list[str] = []
        self.stylesheets: list[str] = []
        self.inline_handlers: list[str] = []
        self.style_attrs = 0
        self._pos = 0
        self._inline_buf: list[str] | None = None

    def handle_starttag(self, tag, attrs):
        a = {k: (v or "") for k, v in attrs}
        self._pos += 1
        if tag == "meta" and a.get("http-equiv", "").lower() == "content-security-policy":
            self.csp.append((self._pos, a.get("content", "")))
        is_sheet = tag == "link" and "stylesheet" in a.get("rel", "").split()
        if (tag == "script" or is_sheet) and not self.first_resource:
            self.first_resource = self._pos
        if is_sheet:
            self.stylesheets.append(a.get("href", ""))
        if tag == "script":
            if "src" in a:
                self.script_srcs.append(a["src"])
            elif a.get("type") != "application/ld+json":
                self._inline_buf = []
        self.inline_handlers += [f"<{tag} {k}>" for k in a if k.startswith("on")]
        if "style" in a:
            self.style_attrs += 1
        if "id" in a:
            self.ids.append(a["id"])
        for attr in ("aria-labelledby", "aria-describedby", "aria-controls"):
            for ref in a.get(attr, "").split():
                self.id_refs.append((attr, ref))
        if tag == "label" and a.get("for"):
            self.id_refs.append(("label for", a["for"]))
        if tag == "script" and a.get("type") == "application/ld+json":
            self._in_jsonld = True
        elif tag in ("script", "style"):
            self._skip_depth += 1
        if tag == "title":
            self._in_title = True
        if tag == "html":
            self.html_lang = a.get("lang", "")
        if re.fullmatch(r"h[1-6]", tag):
            self.headings.append(int(tag[1]))
        if tag == "meta":
            key = (a.get("name") or a.get("property") or "").lower()
            if key:
                self.meta[key] = a.get("content", "")
                if key in ("description", "og:title", "og:description"):
                    self.text.append(a.get("content", ""))
        if tag == "link" and a.get("rel") == "canonical":
            self.canonical = a.get("href", "")
        for attr in ("href", "src"):
            if a.get(attr):
                self.links.append(a[attr])
        for attr in VISIBLE_ATTRS:
            if a.get(attr):
                self.text.append(a[attr])
        if tag in ("input", "select", "textarea"):
            self.fields.append({"tag": tag, **a})
        if tag == "form":
            self.forms.append(a)
        if "hp-field" in a.get("class", "").split() and a.get("aria-hidden") == "true":
            self.hp_hidden = True
        if tag == "select" and a.get("id") == "panel":
            self._in_panel_select = True
        if tag == "option" and self._in_panel_select and a.get("value"):
            self.panel_options.append(a["value"])
        if "data-portal-link" in a:
            self.portal_links.append(a)
        if tag == "img" and "alt" not in a:
            self.images_missing_alt += 1
        if tag == "a" and a.get("target") == "_blank" and "noopener" not in a.get("rel", ""):
            self.blank_without_noopener.append(a.get("href", "?"))

    def handle_endtag(self, tag):
        if tag == "script" and self._inline_buf is not None:
            self.inline_scripts.append("".join(self._inline_buf))
            self._inline_buf = None
        if tag == "script" and self._in_jsonld:
            self._in_jsonld = False
        elif tag in ("script", "style") and self._skip_depth:
            self._skip_depth -= 1
        if tag == "title":
            self._in_title = False
        if tag == "select":
            self._in_panel_select = False

    def handle_data(self, data):
        if self._inline_buf is not None:
            self._inline_buf.append(data)
        if self._in_title:
            self.title += data
        if not self._skip_depth:      # includes JSON-LD and <title>
            self.text.append(data)

    def handle_comment(self, data):
        pass                           # developer notes: not visible text


def find_pages() -> list[Path]:
    pages = []
    for path in sorted(ROOT.rglob("*.html")):
        rel = path.relative_to(ROOT)
        if any(part in SKIP_DIRS for part in rel.parts[:-1]):
            continue
        pages.append(path)
    return pages


def case_exact(target: Path) -> bool:
    """True if every path component below ROOT matches the on-disk name exactly."""
    try:
        parts = target.relative_to(ROOT).parts
    except ValueError:
        return False
    here = ROOT
    for part in parts:
        if part not in {c.name for c in here.iterdir()}:
            return False
        here = here / part
    return True


def page_url(rel: str) -> str:
    """Public URL for a page path relative to the repo root."""
    if rel == "index.html":
        return SITE_ORIGIN + "/"
    if rel.endswith("/index.html"):
        return f"{SITE_ORIGIN}/{rel[: -len('index.html')]}"
    return f"{SITE_ORIGIN}/{rel}"


def main() -> int:
    failures: list[str] = []
    fail = failures.append
    pages = find_pages()
    parsed: dict[str, PageParser] = {}
    for p in pages:
        parser = PageParser()
        parser.feed(p.read_text(encoding="utf-8"))
        parsed[p.relative_to(ROOT).as_posix()] = parser

    # 1b. shared CSS/JS carry a current content-hash version (cache busting) -----
    stamp = subprocess.run([sys.executable, str(ROOT / "tools" / "stamp_assets.py"), "--check"], capture_output=True, text=True)
    if stamp.returncode != 0:
        fail("assets: " + stamp.stdout.strip())

    # 1. partials -----------------------------------------------------------
    sync = subprocess.run([sys.executable, str(ROOT / "tools" / "sync_partials.py"), "--check"],
                          capture_output=True, text=True)
    if sync.returncode != 0:
        fail("partials: " + sync.stdout.strip().replace("\n", " "))

    titles: dict[str, str] = {}
    descriptions: dict[str, str] = {}
    indexable: set[str] = set()
    panel_links: list[tuple[str, str]] = []

    for name, page in parsed.items():
        page_dir = (ROOT / name).parent

        # 2. links ------------------------------------------------------------
        for link in page.links:
            url = urlparse(link)
            if url.scheme == "http" or link.startswith("//"):
                fail(f"{name}: insecure or protocol-relative link {link!r} (use https://)")
                continue
            if url.scheme in ("javascript", "data", "vbscript"):
                fail(f"{name}: {url.scheme}: URL {link[:40]!r} (blocked by the security policy; use a real link)")
                continue
            if url.scheme == "tel" and link != PHONE_TEL:
                fail(f"{name}: phone link {link!r} is not the published number {PHONE_TEL}")
            # An empty recipient is allowed: "share with my doctor" opens the visitor's own email.
            if url.scheme == "mailto" and url.path not in (INBOX, ""):
                fail(f"{name}: email link {link!r} is not the published inbox {INBOX}")
            if url.scheme in ("https", "mailto", "tel"):
                continue
            if url.path:
                base = ROOT if url.path.startswith("/") else page_dir
                target = (base / url.path.lstrip("/")).resolve()
                if target.is_dir():
                    target = target / "index.html"
                if not target.exists():
                    fail(f"{name}: broken link {link!r}")
                    continue
                # As written (not resolve()d: on Windows resolve() silently fixes the case).
                as_written = Path(os.path.normpath(base / url.path.lstrip("/")))
                if as_written.is_dir():
                    as_written = as_written / "index.html"
                if not case_exact(as_written):
                    fail(f"{name}: link {link!r} differs in upper/lower case from the file "
                         "(works on Windows/macOS, 404 on GitHub Pages)")
                try:
                    target_name = target.relative_to(ROOT).as_posix()
                except ValueError:
                    fail(f"{name}: link {link!r} points outside the site")
                    continue
            else:
                target_name = name
            if url.fragment and target_name in parsed and url.fragment not in parsed[target_name].ids:
                fail(f"{name}: link {link!r} points to missing #{url.fragment}")
            panel = parse_qs(url.query).get("panel")
            if panel and url.path.endswith("contact.html"):   # ?panel= preselects the contact form
                panel_links.append((name, panel[0]))

        # 3. metadata ---------------------------------------------------------
        if page.html_lang != "en":
            fail(f'{name}: <html lang="en"> missing')
        if page.headings.count(1) != 1:
            fail(f"{name}: expected exactly one <h1>, found {page.headings.count(1)}")
        for prev, cur in zip(page.headings, page.headings[1:]):
            if cur > prev + 1:
                fail(f"{name}: heading level jumps from h{prev} to h{cur}")
                break
        title = page.title.strip()
        desc = page.meta.get("description", "").strip()
        if not title:
            fail(f"{name}: missing <title>")
        elif title in titles:
            fail(f"{name}: <title> duplicates {titles[title]}")
        titles.setdefault(title, name)
        if not (50 <= len(desc) <= 160):
            fail(f"{name}: meta description is {len(desc)} chars (want 50–160)")
        elif desc in descriptions:
            fail(f"{name}: meta description duplicates {descriptions[desc]}")
        descriptions.setdefault(desc, name)
        noindex = "noindex" in page.meta.get("robots", "")
        basename = Path(name).name
        if basename != "404.html" and page.canonical != page_url(name):
            fail(f"{name}: canonical should be {page_url(name)}, found {page.canonical!r}")
        if basename in NON_INDEXABLE and not noindex:
            fail(f'{name}: should carry <meta name="robots" content="noindex">')
        if basename not in NON_INDEXABLE and not noindex:
            indexable.add(name)

        # 5. claims -----------------------------------------------------------
        visible = re.sub(r"\s+", " ", " ".join(page.text))
        raw = (ROOT / name).read_text(encoding="utf-8")
        draft = DRAFT_MARKER in raw
        if draft and os.environ.get("INNOVEX_ALLOW_DRAFTS") != "1":
            fail(f"{name}: DRAFT page (target list pending lab confirmation) must not be published; "
                 "remove it, or set INNOVEX_ALLOW_DRAFTS=1 only on a draft branch")
        if draft and "noindex" not in page.meta.get("robots", ""):
            fail(f'{name}: draft page must carry <meta name="robots" content="noindex">')
        education = name.startswith((EDUCATION_DIR, MENU_DIR)) or draft
        if education and not draft:
            if EDUCATION_NOTICE not in visible:
                fail(f"{name}: education/panel page must show the notice: {EDUCATION_NOTICE!r}")
            for mark in DISCLAIMER_MARKS:
                if mark not in visible:
                    fail(f"{name}: education/panel page is missing the medical disclaimer text {mark!r}")
            if SOURCES_REQUIRED.match(name) and not re.search(r'<h2 id="[a-z-]*sources-heading">Sources</h2>', raw):
                fail(f"{name}: organism and panel pages must list their Sources")
        claim_text = visible
        for line in OWNER_APPROVED_LINES.get(name, ()):
            claim_text = claim_text.replace(line, " ")
        for pattern, reason in CLAIM_RULES:
            if education and reason == MENU_RULE_REASON:
                continue   # organism/gene names allowed in general education (notice required above)
            for m in re.finditer(pattern, claim_text, re.I):
                snippet = claim_text[max(0, m.start() - 40): m.end() + 40].strip()
                fail(f"{name}: claim rule — {reason}: “…{snippet}…”")
        for clia in set(re.findall(r"\b\d{2}D\d{7}\b", visible)):
            if clia != CLIA_NUMBER:
                fail(f"{name}: CLIA number {clia} does not match the record ({CLIA_NUMBER})")
        if re.search(r"\bCLIA\s*#", visible) and CLIA_NUMBER not in visible:
            fail(f"{name}: CLIA # shown without the recorded number {CLIA_NUMBER}")
        for cola in set(re.findall(r"COLA ID\s*#?\s*(\w+)", visible)):
            if cola != COLA_ID:
                fail(f"{name}: COLA ID {cola} does not match the record ({COLA_ID})")
        if BILLING_MENTION_RE.search(visible) and not PART_A_RE.search(visible):
            fail(f"{name}: mentions payer/Medicare billing without the Part A consolidated-billing exception")

        # 6. form -------------------------------------------------------------
        has_textarea = False
        labelled = {ref for attr, ref in page.id_refs if attr == "label for"}
        for field in page.fields:
            fname = field.get("name", "")
            ftype = field.get("type", "")
            if fname == "_captcha" and field.get("value", "").lower() == "false":
                fail(f"{name}: FormSubmit captcha must not be disabled (_captcha=false)")
            if fname == "_next":
                nxt = urlparse(field.get("value", ""))
                if f"{nxt.scheme}://{nxt.netloc}" != SITE_ORIGIN or not (ROOT / nxt.path.lstrip("/")).is_file():
                    fail(f"{name}: _next must be an existing page on {SITE_ORIGIN}, found {field.get('value')!r}")
            if fname.startswith("_") or ftype in ("hidden", "submit"):
                continue
            if PATIENT_FIELD_RE.search(fname) or PATIENT_FIELD_RE.search(field.get("id", "")):
                fail(f"{name}: form field {fname!r} looks like patient information")
            if not field.get("id"):
                fail(f"{name}: form field {fname!r} has no id (needed for its <label>)")
            elif field["id"] not in labelled:
                fail(f"{name}: form field #{field['id']} has no <label for>")
            if field["tag"] == "textarea":
                has_textarea = True
        for form in page.forms:
            if form.get("action") != FORM_ACTION or form.get("method", "").upper() != "POST":
                fail(f"{name}: form must POST to {FORM_ACTION}, found "
                     f"{form.get('method')!r} {form.get('action')!r}")
        if page.forms:
            names = [f.get("name", "") for f in page.fields if f.get("name")]
            for dup in sorted({n for n in names if names.count(n) > 1}):
                fail(f"{name}: form field name {dup!r} is used more than once")
            hidden = {f.get("name") for f in page.fields if f.get("type") == "hidden"}
            for missing in sorted(FORM_HIDDEN_REQUIRED - hidden):
                fail(f"{name}: form is missing hidden field {missing!r}")
            emails = [f for f in page.fields if f.get("type") == "email"]
            if len(emails) != 1 or emails[0].get("name") != "email":
                fail(f"{name}: form needs exactly one type=email field named 'email' (reply-to)")
            honey = [f for f in page.fields if f.get("name") == "_honey"]
            if len(honey) != 1 or honey[0].get("tabindex") != "-1" or honey[0].get("autocomplete") != "off":
                fail(f"{name}: _honey spam trap missing, or not tabindex=-1 + autocomplete=off")
            if not page.hp_hidden:
                fail(f'{name}: spam trap must sit in <div class="hp-field" aria-hidden="true">')
            for f in page.fields:
                if "required" in f:
                    fid = f.get("id", "")
                    if not f.get("data-label"):
                        fail(f"{name}: required field #{fid} has no data-label (used in error messages)")
                    if f"{fid}-error" not in f.get("aria-describedby", "").split():
                        fail(f"{name}: required field #{fid} must be aria-describedby '{fid}-error'")
        if has_textarea and "patient information" not in visible.lower():
            fail(f"{name}: free-text field without a patient-information warning")

        # 7. portal -----------------------------------------------------------
        for link in page.portal_links:
            if "hidden" not in link:
                fail(f"{name}: Client Portal link must start hidden (site.js reveals it)")
            if link.get("href"):
                fail(f"{name}: Client Portal href must come from site-config.js, not HTML")

        # 8. a11y / ids -------------------------------------------------------
        seen: set[str] = set()
        for i in page.ids:
            if i in seen:
                fail(f"{name}: duplicate id {i!r}")
            seen.add(i)
        for attr, ref in page.id_refs:
            if ref not in seen:
                fail(f"{name}: {attr} points to missing id {ref!r}")
        if page.images_missing_alt:
            fail(f"{name}: {page.images_missing_alt} <img> without alt")
        for href in page.blank_without_noopener:
            fail(f'{name}: target=_blank link {href!r} needs rel="noopener"')

    # 9. security -----------------------------------------------------------------
    hashes = sorted({"'sha256-" + base64.b64encode(hashlib.sha256(src.encode("utf-8")).digest()).decode() + "'"
                     for page in parsed.values() for src in page.inline_scripts})
    expected_csp = CSP_TEMPLATE.format(inline=" ".join(hashes)).replace("  ", " ")
    if any(bad in expected_csp for bad in CSP_FORBIDDEN):
        fail(f"security: CSP_TEMPLATE contains a forbidden source ({CSP_FORBIDDEN})")
    csp_reported = False
    for name, page in parsed.items():
        if len(page.csp) != 1 or page.csp[0][1] != expected_csp:
            found = [c for _, c in page.csp]
            fail(f"{name}: needs exactly one Content-Security-Policy <meta>, found {len(found)}"
                 + ("" if not found else " with a different policy"))
            if not csp_reported:
                fail(f'  expected: <meta http-equiv="Content-Security-Policy" content="{expected_csp}">')
                csp_reported = True
        elif page.first_resource and page.csp[0][0] > page.first_resource:
            fail(f"{name}: the Content-Security-Policy <meta> must come before every script and stylesheet")
        if page.meta.get("referrer") != REFERRER_POLICY:
            fail(f'{name}: needs <meta name="referrer" content="{REFERRER_POLICY}">')
        for h in page.inline_handlers:
            fail(f"{name}: inline event handler {h} (blocked by the CSP; use assets/js/site.js)")
        if page.style_attrs:
            fail(f"{name}: {page.style_attrs} style=\"\" attribute(s) (blocked by the CSP; use site.css)")
        for res in page.script_srcs + page.stylesheets:
            r = urlparse(res)
            if r.scheme or r.netloc or not res:
                fail(f"{name}: third-party or empty script/stylesheet {res!r} (self-hosted only; see docs/SECURITY.md)")
    for js in sorted((ROOT / "assets" / "js").glob("*.js")):
        for n, line in enumerate(js.read_text(encoding="utf-8").splitlines(), 1):
            code = line.split("//", 1)[0] if not line.lstrip().startswith(("*", "/*")) else ""
            if UNSAFE_JS.search(code):
                fail(f"assets/js/{js.name}:{n}: HTML/code-injection sink: {line.strip()[:70]!r} "
                     "(build DOM with textContent/setAttribute; see docs/SECURITY.md)")
    try:
        tracked = subprocess.run(["git", "ls-files"], cwd=ROOT, capture_output=True, text=True,
                                 check=True).stdout.split()
    except (OSError, subprocess.CalledProcessError):
        tracked = []
        print("note: git not available; tracked-file checks skipped")
    cfg_yml = (ROOT / "_config.yml").read_text(encoding="utf-8")
    excluded = set(re.findall(r"^\s*-\s*(\S+)\s*$", cfg_yml, re.M))
    for path in tracked:
        if FORBIDDEN_TRACKED.search(path):
            fail(f"security: {path} must not be tracked in this PUBLIC repository")
        top = path.split("/")[0]
        if PUBLISHED.match(path) or top.startswith((".", "_")):
            continue
        if path not in excluded and top + "/" not in excluded and top not in excluded:
            fail(f"security: {path} would be published by GitHub Pages; add it to _config.yml exclude")

    # 6b. ?panel= links match the contact form's <option value>s -------------
    options = set(parsed.get("contact.html", PageParser()).panel_options)
    for name, value in panel_links:
        if value not in options:
            fail(f"{name}: ?panel={value} has no matching option on contact.html")

    # 4. sitemap ---------------------------------------------------------------
    sitemap = (ROOT / "sitemap.xml").read_text(encoding="utf-8")
    url_to_page = {page_url(n): n for n in parsed}
    listed = set()
    for loc in re.findall(r"<loc>(.*?)</loc>", sitemap):
        if loc not in url_to_page:
            fail(f"sitemap: {loc} does not match any page")
        else:
            listed.add(url_to_page[loc])
    if listed != indexable:
        fail(f"sitemap: missing {sorted(indexable - listed)} / extra {sorted(listed - indexable)}")

    # 7b. portal config --------------------------------------------------------
    cfg = (ROOT / "assets" / "js" / "site-config.js").read_text(encoding="utf-8")
    m = re.search(r'portalUrl:\s*"([^"]*)"', cfg)
    if not m:
        fail("site-config.js: portalUrl setting not found")
    elif m.group(1):
        pu = urlparse(m.group(1))
        if (pu.scheme != "https" or not pu.hostname or "." not in pu.hostname or pu.username or pu.password
                or re.search(r"[\s<>\"'`\\]", m.group(1))):
            fail("site-config.js: portalUrl must be empty or a plain https:// URL (host, no credentials, "
                 "no spaces or quotes)")

    # 10. acronyms: each spelled out at its first use in a page's <main> (tools/content/acronyms.py)
    sys.path.insert(0, str(ROOT / "tools"))
    from expand_acronyms import expand_page, unknown_caps
    for p in pages:
        name = p.relative_to(ROOT).as_posix()
        s = p.read_text(encoding="utf-8")
        new, ex = expand_page(s)
        if new != s:
            fail(f"{name}: acronym not spelled out at first use ({', '.join(c.split(' ->')[0] for c in ex.changes)}); "
                 "run python tools/expand_acronyms.py (or rebuild generated pages)")
        for u in ex.unexplained:
            fail(f"{name}: acronym needs wording by hand: {u}")
        unknown = unknown_caps(s)
        if unknown:
            fail(f"{name}: abbreviation(s) not in tools/content/acronyms.py: {', '.join(unknown)} "
                 "(add an expansion, or list it in NOT_ACRONYMS if it is a name or code)")

    # The spam-trap container must really be moved off-screen by the CSS.
    css = (ROOT / "assets" / "css" / "site.css").read_text(encoding="utf-8")
    if not re.search(r"\.hp-field\s*\{[^}]*(left:\s*-\d{3,}px|display:\s*none)", css):
        fail("site.css: .hp-field must hide the spam trap (off-screen or display:none)")

    # CNAME must be exactly one hostname line (GitHub Pages requirement).
    cname = (ROOT / "CNAME").read_text(encoding="utf-8").strip().splitlines()
    if cname != ["www.innovexlab.com"]:
        fail(f"CNAME must contain exactly 'www.innovexlab.com', found {cname}")

    if failures:
        print(f"FAILED — {len(failures)} problem(s):")
        for f in failures:
            print("  - " + f)
        return 1
    print(f"OK — {len(pages)} pages checked: partials, links, metadata, headings, sitemap, claims, "
          f"billing caveat, form, portal, ids/a11y, security policy, acronyms.")
    return 0


if __name__ == "__main__":
    # Windows consoles (cp1252) cannot print every character; never crash on output.
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(errors="replace")
    sys.exit(main())
