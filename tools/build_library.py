#!/usr/bin/env python3
"""Build the organism library (learn/organisms/) and the panel pages (testing/panels/) from tools/content/.

    python tools/build_library.py && python tools/sync_partials.py

Two layers, kept separate on purpose:
  * learn/organisms/*.html: GENERAL clinical education (what each organism is, infections, symptoms,
    resistance, treatment considerations). No InnovexLab menu claims. Publishable after clinical review.
  * testing/panels/*.html: InnovexLab panel pages listing targets as printed on the requisition forms
    (owner decision 2026-11-16: the requisition forms are the menu of record).
Every page carries the medical disclaimer and a cited source list (tools/content/references.py); the
hand-written learn/ pages get the same disclaimer block, replaced between markers on each build.
Pages reuse about.html's <head> (security policy, icons, scripts) and the shared partials.
"""
from __future__ import annotations

import html
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(Path(__file__).resolve().parent / "content"))
from organisms_bacteria import BACTERIA  # noqa: E402
from organisms_other import OTHER  # noqa: E402
from panels import PANELS, MICROGRAPHS  # noqa: E402
from references import R as REFS, ORG_REFS, PANEL_REFS  # noqa: E402
from image_sources import IMAGE_SOURCES  # noqa: E402
from cards import CARDS, GENE_CARDS  # noqa: E402
sys.path.insert(0, str(Path(__file__).resolve().parent))
from expand_acronyms import expand_main, expand_page  # noqa: E402

ORGS = BACTERIA + OTHER
import json as _json  # noqa: E402
TITLES_JSON = _json.dumps({o["slug"]: o["title"] for o in ORGS}, separators=(",", ":"))
BY_SLUG = {o["slug"]: o for o in ORGS}
NOTICE = "General medical information for education only, not medical advice."
ACCESSED = "November 2026"
DISCLAIMER = (
    '<div class="disclaimer" role="note" aria-labelledby="disclaimer-heading"><h2 id="disclaimer-heading">Medical disclaimer</h2>'
    "<p>This page is general educational information summarized from published public-health and professional-society "
    "guidance. It is not medical advice, a diagnosis or a treatment recommendation, and reading it does not create a "
    "clinician&ndash;patient relationship with InnovexLab. Decisions about testing, diagnosis and treatment belong to the "
    "treating clinician, using the patient&rsquo;s history and examination, laboratory and susceptibility results, local "
    "resistance patterns and current guidelines. Guidance changes over time; consult the original sources for the latest "
    "version. InnovexLab provides this information as is and does not warrant that it is complete or current.</p>"
    "<p>Patients with questions about their health should contact their own healthcare provider. "
    "In an emergency, call 911.</p>"
    '<p><a class="arrow-link" href="/learn/sources.html">Sources, image credits and editorial policy</a></p></div>')
CTA = "Request a consultation"
TARGET_CAVEAT = ("Detection of a target does not by itself establish infection or determine treatment; results are interpreted by "
                 "the ordering clinician with the clinical picture and, where indicated, culture and susceptibility testing.")
TARGET_CAVEAT_GENE = ("Detection of a resistance gene does not by itself determine susceptibility or treatment, and an undetected "
                      "gene does not prove susceptibility; results are interpreted with culture and susceptibility testing.")
SITE = "https://www.innovexlab.com"
GROUP_ORDER = ["Bacteria: Gram-negative", "Bacteria: Gram-positive", "Bacteria: atypical and cell-wall-deficient",
               "Vaginal microbiome bacteria", "Viruses: respiratory", "Viruses: gastrointestinal",
               "Viruses: skin, eye and genital", "Fungi: yeasts", "Fungi: molds, dermatophytes and Pneumocystis", "Parasites"]
GENES = {"gene-mecA": "mecA", "gene-van": "vanA/vanB", "gene-esbl": "ESBL genes", "gene-ampc": "AmpC",
         "gene-carbapenemase": "carbapenemases", "gene-qnr": "qnr", "gene-erm": "erm", "gene-mef": "mefA", "gene-pvl": "PVL"}
MORPH = {  # key: (caption, svg body)
    "rod-neg": ("Gram-negative rods", "rods", "#e07a93", "#a8435d"),
    "rod-pos": ("Gram-positive rods", "rods", "#6a4c9c", "#3f2a63"),
    "rod-pos-spore": ("Gram-positive spore-forming rods", "spore", "#6a4c9c", "#3f2a63"),
    "coccobacillus-neg": ("Gram-negative coccobacilli", "cocco", "#e07a93", "#a8435d"),
    "coccobacillus-var": ("Gram-variable coccobacilli", "cocco", "#b77fb0", "#7a4f75"),
    "curved-neg": ("Curved Gram-negative rods", "curved", "#e07a93", "#a8435d"),
    "diplococcus-neg": ("Gram-negative diplococci", "diplo", "#e07a93", "#a8435d"),
    "diplococcus-pos": ("Gram-positive diplococci", "diplo", "#6a4c9c", "#3f2a63"),
    "cocci-cluster": ("Gram-positive cocci in clusters", "cluster", "#6a4c9c", "#3f2a63"),
    "cocci-chain": ("Gram-positive cocci in pairs and chains", "chain", "#6a4c9c", "#3f2a63"),
    "no-wall": ("No cell wall: not seen on Gram stain", "nowall", "none", "#5b6b7b"),
    "intracellular": ("Obligate intracellular bacteria (inclusions inside a host cell)", "intracell", "#e07a93", "#a8435d"),
    "spirochete": ("Spirochete (corkscrew-shaped bacterium)", "spiro", "none", "#3f2a63"),
    "virus-enveloped": ("Enveloped virus", "venv", "#c9d8e8", "#0b2c4a"),
    "virus-naked": ("Non-enveloped virus", "vnaked", "#c9d8e8", "#0b2c4a"),
    "yeast": ("Yeast: budding cells and pseudohyphae", "yeast", "#b9a6d8", "#5b4a7e"),
    "mold": ("Mold: branching hyphae with spores", "mold", "#cfe3d4", "#2e6b45"),
    "cyst": ("Fungal cysts", "cyst", "#d7e3ef", "#0b2c4a"),
    "protozoan": ("Protozoan parasite", "protozoan", "#f1dfc6", "#7a5527"),
}


def esc(t):
    return html.escape(t, quote=True)


def gene_links(text, prefix="/learn/resistance-genes.html"):
    # Gene markers are removed from the sentence and listed once at the end, avoiding stacked parentheses.
    ids = list(dict.fromkeys(re.findall(r"\[\[(gene-[A-Za-z]+)\]\]", text)))
    out = esc(re.sub(r"\s*\[\[gene-[A-Za-z]+\]\]", "", text))
    if ids:
        links = ", ".join(f'<a href="{prefix}#{g}">{GENES[g]}</a>' for g in ids)
        out += f' <span class="gene-refs">Resistance-gene guide: {links}.</span>'
    return out


def sources_block(keys, heading_id="sources-heading"):
    assert keys, "every cited page needs at least one verified source"
    items = "".join(f'<li>{esc(REFS[k][0])}. <a href="{esc(REFS[k][2])}" rel="external">{esc(REFS[k][1])}</a>.</li>' for k in keys)
    return (f'<section class="sources" aria-labelledby="{heading_id}"><h2 id="{heading_id}">Sources</h2>'
            f'<ol class="ref-list">{items}</ol><p class="ref-note">Sources accessed {ACCESSED}. Links open external sites '
            "that InnovexLab does not control.</p></section>")


ABBREV = re.compile(r"(?:\b[A-Z]|\bspp|\be\.g|\bi\.e|\bU\.S|\bvs)$")


def title_case(name):
    def cap(w):
        lead = "(" if w.startswith("(") else ""
        core = w[len(lead):]
        return w if core.isupper() else lead + core[:1].upper() + core[1:]
    return " ".join(cap(w) for w in name.split(" "))


def mid_case(name):
    return name if name[:2].isupper() else name[:1].lower() + name[1:]


def card_text(o):
    """One-line description for library and panel cards (tools/content/cards.py, else the summary's first sentence)."""
    return CARDS.get(o["slug"]) or first_sentence(o["summary"])


def resistance_heading(o):
    g = o["group"]
    if g.startswith(("Bacteria", "Vaginal")):
        return "Antibiotic resistance"
    if g.startswith("Viruses"):
        return "Antiviral resistance"
    if g.startswith("Fungi"):
        return "Antifungal resistance"
    return "Drug resistance"


def first_sentence(t):
    # A period ends the sentence only when it is not part of an abbreviation such as "E. coli" or "spp.".
    for m in re.finditer(r"\.(?=\s|$)", t):
        if not ABBREV.search(t[:m.start()]):
            return t[:m.end()]
    return t


# ------------------------------------------------------------------ schematic SVGs
def morph_svg(kind, fill, stroke, title):
    shapes = {
        "rods": '<g><rect x="30" y="40" width="50" height="18" rx="9"/><rect x="95" y="30" width="46" height="18" rx="9" transform="rotate(20 118 39)"/><rect x="40" y="80" width="48" height="18" rx="9" transform="rotate(-15 64 89)"/><rect x="100" y="90" width="50" height="18" rx="9"/><rect x="60" y="118" width="46" height="18" rx="9" transform="rotate(30 83 127)"/></g>',
        "spore": '<g><rect x="30" y="45" width="56" height="18" rx="4"/><rect x="100" y="40" width="56" height="18" rx="4"/><rect x="50" y="95" width="56" height="18" rx="4"/><rect x="118" y="100" width="40" height="18" rx="4"/></g><g fill="#ffffff"><ellipse cx="78" cy="54" rx="6" ry="6"/><ellipse cx="148" cy="49" rx="6" ry="6"/><ellipse cx="98" cy="104" rx="6" ry="6"/></g>',
        "cocco": '<g><rect x="40" y="40" width="22" height="14" rx="7"/><rect x="80" y="36" width="22" height="14" rx="7"/><rect x="120" y="48" width="22" height="14" rx="7"/><rect x="56" y="80" width="22" height="14" rx="7"/><rect x="100" y="86" width="22" height="14" rx="7"/><rect x="138" y="96" width="22" height="14" rx="7"/><rect x="70" y="120" width="22" height="14" rx="7"/></g>',
        "curved": '<g fill="none" stroke-width="10" stroke-linecap="round"><path d="M35 60c15-20 35-20 45 0s30 20 40 0"/><path d="M60 110c12-16 30-16 38 0s26 16 34 0"/><path d="M130 50c10-14 24-14 32 0"/></g>',
        "diplo": '<g><circle cx="60" cy="50" r="12"/><circle cx="84" cy="50" r="12"/><circle cx="120" cy="80" r="12"/><circle cx="144" cy="80" r="12"/><circle cx="56" cy="112" r="12"/><circle cx="80" cy="112" r="12"/></g>',
        "cluster": '<g><circle cx="80" cy="50" r="12"/><circle cx="104" cy="48" r="12"/><circle cx="126" cy="56" r="12"/><circle cx="70" cy="72" r="12"/><circle cx="94" cy="72" r="12"/><circle cx="118" cy="78" r="12"/><circle cx="84" cy="96" r="12"/><circle cx="108" cy="100" r="12"/><circle cx="96" cy="120" r="12"/></g>',
        "chain": '<g><circle cx="40" cy="40" r="11"/><circle cx="62" cy="46" r="11"/><circle cx="83" cy="55" r="11"/><circle cx="102" cy="68" r="11"/><circle cx="117" cy="86" r="11"/><circle cx="128" cy="107" r="11"/><circle cx="50" cy="110" r="11"/><circle cx="72" cy="112" r="11"/></g>',
        "nowall": '<g stroke-dasharray="4 4" stroke-width="2"><circle cx="60" cy="50" r="10"/><ellipse cx="100" cy="64" rx="13" ry="8"/><circle cx="140" cy="48" r="7"/><ellipse cx="70" cy="104" rx="8" ry="12"/><circle cx="118" cy="110" r="11"/><circle cx="150" cy="92" r="7"/></g>',
        "intracell": '<g><ellipse cx="95" cy="80" rx="70" ry="55" fill="#f4f7fb"/><circle cx="70" cy="70" r="20" fill="#ffffff"/></g><g><circle cx="64" cy="64" r="4"/><circle cx="74" cy="66" r="4"/><circle cx="68" cy="76" r="4"/><circle cx="78" cy="76" r="4"/><circle cx="120" cy="96" r="4"/><circle cx="128" cy="90" r="4"/></g>',
        "spiro": '<g fill="none" stroke-width="4" stroke-linecap="round"><path d="M20 70c8-14 16-14 24 0s16 14 24 0 16-14 24 0 16 14 24 0 16-14 24 0 16 14 24 0"/><path d="M40 120c6-10 12-10 18 0s12 10 18 0 12-10 18 0 12 10 18 0 12-10 18 0"/></g>',
        "venv": '<g><circle cx="95" cy="80" r="42"/></g><g stroke-width="3" stroke-linecap="round" fill="none"><path d="M95 32v-10M95 128v10M47 80h-10M143 80h10M61 46l-7-7M129 114l7 7M61 114l-7 7M129 46l7-7"/></g><g fill="#0b2c4a"><circle cx="95" cy="20" r="4"/><circle cx="95" cy="140" r="4"/><circle cx="35" cy="80" r="4"/><circle cx="155" cy="80" r="4"/><circle cx="52" cy="37" r="4"/><circle cx="138" cy="123" r="4"/><circle cx="52" cy="123" r="4"/><circle cx="138" cy="37" r="4"/></g>',
        "vnaked": '<g><polygon points="95,35 135,58 135,102 95,125 55,102 55,58"/></g><g fill="none" stroke-width="2"><path d="M95 35v90M55 58l80 44M135 58l-80 44"/></g>',
        "yeast": '<g><ellipse cx="60" cy="50" rx="18" ry="13"/><ellipse cx="84" cy="40" rx="9" ry="7"/><ellipse cx="130" cy="60" rx="17" ry="13"/><rect x="40" y="96" width="44" height="14" rx="7"/><rect x="82" y="98" width="44" height="14" rx="7" transform="rotate(10 104 105)"/><rect x="122" y="108" width="40" height="14" rx="7" transform="rotate(-8 142 115)"/></g>',
        "mold": '<g fill="none" stroke-width="6" stroke-linecap="round"><path d="M20 120c30-10 50-30 70-60M90 60c10 20 30 30 60 30M70 92c-10-20-10-40 0-60"/></g><g><circle cx="70" cy="28" r="7"/><circle cx="80" cy="22" r="6"/><circle cx="60" cy="22" r="6"/><circle cx="154" cy="90" r="7"/><circle cx="160" cy="80" r="6"/></g>',
        "cyst": '<g><circle cx="60" cy="60" r="18"/><circle cx="110" cy="50" r="16"/><circle cx="80" cy="108" r="18"/><circle cx="135" cy="100" r="15"/></g>',
        "protozoan": '<g><path d="M60 50c25-18 70-10 80 20s-10 55-45 55-55-20-50-45 0-25 15-30z"/></g><g fill="#7a5527"><circle cx="85" cy="72" r="7"/><circle cx="110" cy="80" r="7"/></g><g fill="none" stroke-width="2"><path d="M140 70c15-10 25-5 30 5M58 52c-12-10-22-8-28 0"/></g>',
    }[kind]
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 190 160" role="img" aria-label="{esc(title)}">'
            f'<rect width="190" height="160" rx="8" fill="#ffffff"/>'
            f'<g fill="{fill}" stroke="{stroke}" stroke-width="2">{shapes}</g></svg>\n')


def write_morphs():
    out = ROOT / "assets/img/morph"
    out.mkdir(parents=True, exist_ok=True)
    for key, (cap, kind, fill, stroke) in MORPH.items():
        (out / f"{key}.svg").write_text(morph_svg(kind, fill, stroke, cap + " (schematic)"), encoding="utf-8", newline="\n")


# ------------------------------------------------------------------ page shell
TEMPLATE = (ROOT / "about.html").read_text(encoding="utf-8")


def shell(path, page_id, title, desc, main, noindex=False):
    s = TEMPLATE
    url = f"{SITE}/{path[:-len('index.html')] if path.endswith('/index.html') else path}"
    s = re.sub(r"<title>.*?</title>", f"<title>{esc(title)}</title>", s, count=1)
    robots = '\n  <meta name="robots" content="noindex">' if noindex else ""
    s = re.sub(r'<meta name="description" content="[^"]*">', f'<meta name="description" content="{esc(desc)}">{robots}', s, count=1)
    s = re.sub(r'<link rel="canonical" href="[^"]*">', f'<link rel="canonical" href="{url}">', s, count=1)
    s = re.sub(r'<meta property="og:title" content="[^"]*">', f'<meta property="og:title" content="{esc(title)}">', s, count=1)
    s = re.sub(r'<meta property="og:description" content="[^"]*">', f'<meta property="og:description" content="{esc(desc)}">', s, count=1)
    s = re.sub(r'<meta property="og:url" content="[^"]*">', f'<meta property="og:url" content="{url}">', s, count=1)
    s = s.replace('<body data-page="about">', f'<body data-page="{page_id}">', 1)
    main = expand_main(main)[0]  # spell out each acronym at its first use on the page
    s = re.sub(r'  <main id="main">.*?</main>', lambda m: '  <main id="main">\n' + main.strip("\n") + "\n  </main>", s, count=1, flags=re.S)
    (ROOT / path).parent.mkdir(parents=True, exist_ok=True)
    (ROOT / path).write_text(s, encoding="utf-8", newline="\n")


def desc_trim(t, n=158):
    t = re.sub(r"\s+", " ", t)
    return t if len(t) <= n else t[: n - 1].rsplit(" ", 1)[0] + "…"


# ------------------------------------------------------------------ organism pages
def figure_for(o):
    m = MICROGRAPHS.get(o["slug"])
    cap, *_ = MORPH[o["morph"]]
    schematic = (f'<figure class="org-figure"><img src="/assets/img/morph/{o["morph"]}.svg" width="190" height="160" '
                 f'alt="{esc(cap)}, schematic"><figcaption>{esc(cap)}. Schematic, not to scale; InnovexLab.</figcaption></figure>')
    if not m:
        return schematic
    f, w, h, alt, credit = m
    return (f'<figure class="org-figure org-figure--photo"><img src="/assets/img/organisms/{f}" width="{w}" height="{h}" loading="lazy" '
            f'decoding="async" alt="{esc(alt)}"><figcaption>{credit} <a href="{esc(IMAGE_SOURCES[o["slug"]][0])}" rel="external">Image source</a></figcaption></figure>' + schematic)


def organism_page(o, prev_o, next_o):
    aka = f'<p class="org-aka">{esc(o["aka"])}</p>' if o.get("aka") else ""
    control = (f'<h2>Infection control and public health</h2><p>{esc(o["control"])}</p>' if o.get("control") else "")
    nav = '<nav class="org-pager" aria-label="Organism library pages" data-pager>'
    nav += f'<a href="/learn/organisms/{prev_o["slug"]}.html" rel="prev" data-pager-prev>&larr; {esc(prev_o["title"])}</a>' if prev_o else "<span data-pager-prev></span>"
    nav += '<a href="/learn/organisms/index.html" data-pager-home>All organisms</a>'
    nav += f'<a href="/learn/organisms/{next_o["slug"]}.html" rel="next" data-pager-next>{esc(next_o["title"])} &rarr;</a>' if next_o else "<span data-pager-next></span>"
    nav += "</nav>"
    nav = nav.replace("data-pager>", f'data-pager data-titles="{esc(TITLES_JSON)}">', 1)
    main = f"""    <section class="hero hero--page" aria-labelledby="page-heading">
      <div class="container">
        <nav class="breadcrumb" aria-label="Breadcrumb"><a href="/learn/infections.html">Clinical resources</a> <span aria-hidden="true">/</span> <a href="/learn/organisms/index.html">Organism library</a></nav>
        <span class="eyebrow">{esc(o["group"])}</span>
        <h1 id="page-heading"><i>{esc(o["title"])}</i></h1>
        {aka}
      </div>
    </section>

    <section class="section" aria-labelledby="overview-heading">
      <div class="container">
        <p class="education-notice" role="note"><strong>{NOTICE}</strong> Treatment considerations summarize published guidance at drug-class level; therapy is chosen by the treating clinician using laboratory results, the clinical picture and current guidelines.</p>
        <div class="org-layout">
          <div class="prose">
            <h2 id="overview-heading">Overview</h2>
            <p>{esc(o["summary"])}</p>
            <h2>Infections</h2>
            <p>{esc(o["infections"])}</p>
            <h2>Signs and symptoms</h2>
            <p>{esc(o["symptoms"])}</p>
            <h2>{resistance_heading(o)}</h2>
            <p>{gene_links(o["resistance"])}</p>
            <h2>Treatment considerations</h2>
            <p>{esc(o["treatment"])}</p>
            {control}
          </div>
          <div class="org-aside">{figure_for(o)}</div>
        </div>
        {sources_block(ORG_REFS[o["slug"]])}
        {DISCLAIMER}
        {nav}
      </div>
    </section>"""
    first = first_sentence(o["summary"])
    shell(f"learn/organisms/{o['slug']}.html", "resources", f"{o['title']} | Organism Library | InnovexLab",
          desc_trim(f"{o['title']}: {first} Infections, symptoms, resistance and treatment considerations."), main)


def library_index():
    letters = sorted({o["title"][0].upper() for o in ORGS})
    groups = ""
    for g in GROUP_ORDER:
        items = sorted([o for o in ORGS if o["group"] == g], key=lambda o: o["title"].lower())
        if not items:
            continue
        lis = "\n".join(
            f'            <li data-filter-text="{esc((o["title"] + " " + o.get("aka", "")).lower())}"><a href="/learn/organisms/{o["slug"]}.html">'
            f'<span class="lib-name" data-acronyms="off"><i>{esc(o["title"])}</i></span><span class="lib-aka">{esc(card_text(o))}</span></a></li>'
            for o in items)
        gid = re.sub(r"[^a-z]+", "-", g.lower()).strip("-")
        groups += f"""
        <section class="lib-group" aria-labelledby="{gid}" data-filter-group>
          <h2 id="{gid}">{esc(g)} <span class="lib-count">({len(items)})</span></h2>
          <ul class="lib-list">
{lis}
          </ul>
        </section>"""
    az = sorted(ORGS, key=lambda o: o["title"].lower())
    azlist = "\n".join(f'            <li><a href="/learn/organisms/{o["slug"]}.html"><i>{esc(o["title"])}</i></a></li>' for o in az)
    main = f"""    <section class="hero hero--page" aria-labelledby="page-heading">
      <div class="container">
        <nav class="breadcrumb" aria-label="Breadcrumb"><a href="/learn/infections.html">Clinical resources</a></nav>
        <span class="eyebrow">Clinical resources</span>
        <h1 id="page-heading">Organism library</h1>
        <p>Bacteria, viruses, fungi and parasites relevant to molecular infection testing: what each one is, the infections and symptoms it causes, resistance and treatment considerations.</p>
      </div>
    </section>

    <section class="section" aria-labelledby="browse-heading">
      <div class="container">
        <p class="education-notice" role="note"><strong>{NOTICE}</strong> This library does not replace advice from a clinician, and each page cites its sources. For InnovexLab&rsquo;s panels and their targets, see <a href="/testing/panels/index.html">Panels</a>.</p>
        <h2 id="browse-heading" class="visually-hidden">Browse organisms</h2>
        <div class="lib-tools">
          <label for="organism-filter" class="lib-filter-label" hidden>Find an organism</label>
          <input id="organism-filter" class="lib-filter" type="search" placeholder="Type a name, e.g., Klebsiella" autocomplete="off" aria-describedby="filter-status" hidden>
          <span id="filter-status" class="lib-status" role="status" aria-live="polite"></span>
        </div>
        <p class="lib-jump">Jump to: {" &middot; ".join(f'<a href="#{re.sub(r"[^a-z]+", "-", g.lower()).strip("-")}">{esc(g)}</a>' for g in GROUP_ORDER if any(o["group"] == g for o in ORGS))} &middot; <a href="#a-z">A&ndash;Z</a></p>
{groups}
        <section class="lib-group" aria-labelledby="a-z">
          <h2 id="a-z">A&ndash;Z <span class="lib-count">({len(az)})</span></h2>
          <p class="lib-letters">{" ".join(letters)}</p>
          <ul class="lib-az">
{azlist}
          </ul>
        </section>
        {DISCLAIMER}
      </div>
    </section>"""
    shell("learn/organisms/index.html", "resources", "Organism Library | Clinical Resources | InnovexLab",
          "Organism library: bacteria, viruses, fungi and parasites, with the infections and symptoms they cause, resistance and treatment considerations.", main)


# ------------------------------------------------------------------ panel pages (DRAFT)
def panel_page(p):
    order = []
    for _, targets in p["sections"]:
        for _, slug in targets:
            if not slug.startswith("gene-") and slug not in order:
                order.append(slug)
    ctx = f"?panel={p['id']}&amp;list={','.join(order)}"
    rows = ""
    for section, targets in p["sections"]:
        lis = ""
        for printed, slug in targets:
            if slug.startswith("gene-"):
                lis += (f'            <li><a href="/learn/resistance-genes.html#{slug}"><span class="lib-name" data-acronyms="off">{esc(printed)}</span>'
                        f'<span class="lib-aka">{esc(GENE_CARDS[slug])}</span></a></li>\n')
                continue
            o = BY_SLUG[slug]
            lis += (f'            <li><a href="/learn/organisms/{slug}.html{ctx}"><span class="lib-name" data-acronyms="off"><i>{esc(printed)}</i></span>'
                    f'<span class="lib-aka">{esc(card_text(o))}</span></a></li>\n')
        rows += f"""
        <h3>{esc(section)} <span class="lib-count">({len(targets)})</span></h3>
        <ul class="lib-list">
{lis}        </ul>"""
    n = sum(len(t) for _, t in p["sections"])
    main = f"""    <section class="hero hero--page" aria-labelledby="page-heading">
      <div class="container">
        <nav class="breadcrumb" aria-label="Breadcrumb"><a href="/testing.html">Testing</a> <span aria-hidden="true">/</span> <a href="/testing/panels/index.html">Panels</a></nav>
        <span class="eyebrow">Testing services &middot; Panels</span>
        <h1 id="page-heading">{esc(p["name"])} panel</h1>
        <p>{esc(p["intro"])}</p>
      </div>
    </section>

    <section class="section" aria-labelledby="targets-heading">
      <div class="container">
        <p class="education-notice" role="note"><strong>{NOTICE}</strong> Targets are listed as they appear on InnovexLab&rsquo;s {esc(p["source"])}. {TARGET_CAVEAT_GENE if p["id"] == "resistance" else TARGET_CAVEAT}</p>
        <div class="split">
          <div>
            <h2>When to consider testing</h2>
            <p>{esc(p["when"])}</p>
          </div>
          <div class="limits">
            <h2>Interpretation</h2>
            <p>{esc(p["interpret"])}</p>
          </div>
        </div>
        {p.get("figure", "")}
        <h2 id="targets-heading">Targets ({n})</h2>
        <p>{"Select a gene for its mechanism and clinical significance." if p["id"] == "resistance" else "Select a target for its clinical summary, symptoms, resistance and treatment considerations."}</p>
{rows}
        <p class="mt-6"><a class="button button--primary" href="/contact.html?panel={p["panel_param"]}#book">{CTA}</a></p>
        {sources_block(PANEL_REFS[p["id"]])}
        {DISCLAIMER}
      </div>
    </section>"""
    shell(f"testing/panels/{p['id']}.html", "testing", f"{title_case(p['name'])} Panel Targets | InnovexLab",
          desc_trim(f"Every target on the InnovexLab {mid_case(p['name'])} panel, each linked to its clinical summary, symptoms, resistance and treatment considerations."), main)


def all_targets():
    membership = {}
    for p in PANELS:
        for _, targets in p["sections"]:
            for printed, slug in targets:
                if slug.startswith("gene-"):
                    continue
                membership.setdefault(slug, [])
                if p["id"] not in [x["id"] for x in membership[slug]]:
                    membership[slug].append(p)
    groups = ""
    for g in GROUP_ORDER:
        items = sorted([o for o in ORGS if o["group"] == g and o["slug"] in membership], key=lambda o: o["title"].lower())
        if not items:
            continue
        rows = "\n".join(
            f'            <tr data-filter-text="{esc((o["title"] + " " + o.get("aka", "") + " " + " ".join(p["name"] for p in membership[o["slug"]])).lower())}">'
            f'<th scope="row"><a href="/learn/organisms/{o["slug"]}.html"><i>{esc(o["title"])}</i></a>'
            f'{"<br><span class=lib-aka>" + esc(o["aka"]) + "</span>" if o.get("aka") else ""}</th>'
            f'<td><ul class="panel-tags">' + "".join(f'<li><a href="/testing/panels/{p["id"]}.html">{esc(p["name"])}</a></li>' for p in membership[o["slug"]]) + "</ul></td></tr>"
            for o in items)
        gid = "all-" + re.sub(r"[^a-z]+", "-", g.lower()).strip("-")
        groups += f"""
        <section class="lib-group" aria-labelledby="{gid}" data-filter-group>
          <h2 id="{gid}">{esc(g)} <span class="lib-count">({len(items)})</span></h2>
          <div class="table-wrap" role="region" aria-label="{esc(g)}: organisms and panels" tabindex="0">
            <table class="data-table data-table--targets">
              <thead><tr><th scope="col">Organism</th><th scope="col">Panels</th></tr></thead>
              <tbody>
{rows}
              </tbody>
            </table>
          </div>
        </section>"""
    main = f"""    <section class="hero hero--page" aria-labelledby="page-heading">
      <div class="container">
        <nav class="breadcrumb" aria-label="Breadcrumb"><a href="/testing/panels/index.html">Panels</a></nav>
        <span class="eyebrow">Testing services &middot; Panels</span>
        <h1 id="page-heading">All targets, by organism</h1>
        <p>Every organism detected across InnovexLab&rsquo;s panels, once, with the panels it appears on.</p>
      </div>
    </section>
    <section class="section" aria-labelledby="all-heading">
      <div class="container">
        <p class="education-notice" role="note"><strong>{NOTICE}</strong> Targets are listed as they appear on InnovexLab&rsquo;s requisition forms. Detection of a target does not by itself establish infection or determine treatment; results are interpreted by the ordering clinician with the clinical picture and, where indicated, culture and susceptibility testing.</p>
        <h2 id="all-heading" class="visually-hidden">Organisms and panels</h2>
        <div class="lib-tools">
          <label for="organism-filter" class="lib-filter-label" hidden>Find an organism or panel</label>
          <input id="organism-filter" class="lib-filter" type="search" placeholder="Type an organism or panel, e.g., Candida or Wound" autocomplete="off" aria-describedby="filter-status" hidden>
          <span id="filter-status" class="lib-status" role="status" aria-live="polite"></span>
        </div>
        <p class="lib-jump">Panels: {" &middot; ".join(f'<a href="/testing/panels/{p["id"]}.html">{esc(p["name"])}</a>' for p in PANELS if p["id"] != "resistance")} &middot; <a href="/learn/resistance-genes.html">Resistance genes</a></p>
{groups}
        {DISCLAIMER}
      </div>
    </section>"""
    shell("testing/panels/all-targets.html", "testing", "All InnovexLab Targets by Organism",
          "Every organism detected across InnovexLab panels, listed once with the panels it appears on and a link to its clinical summary.", main)


def panel_index():
    lis = "\n".join(f'          <li><a href="/testing/panels/{p["id"]}.html"><span class="lib-name">{esc(p["name"])}</span>'
                    f'<span class="lib-aka">Targets as printed: {sum(len(t) for _, t in p["sections"])}</span></a></li>'
                    for p in PANELS)
    main = f"""    <section class="hero hero--page" aria-labelledby="page-heading">
      <div class="container">
        <span class="eyebrow">Testing services</span>
        <h1 id="page-heading">InnovexLab panels</h1>
        <p>Every panel with its full target list. Each target links to its clinical summary in the organism library.</p>
      </div>
    </section>
    <section class="section" aria-labelledby="panels-heading">
      <div class="container">
        <p class="education-notice" role="note"><strong>{NOTICE}</strong> Targets are listed as they appear on InnovexLab&rsquo;s requisition forms. Detection of a target does not by itself establish infection or determine treatment; results are interpreted by the ordering clinician with the clinical picture and, where indicated, culture and susceptibility testing.</p>
        <h2 id="panels-heading">Panels</h2>
        <ul class="lib-list">
{lis}
        </ul>
        <p><a class="arrow-link" href="/testing/panels/all-targets.html">All targets, by organism, with their panels</a></p>
        <p><a class="arrow-link" href="/learn/organisms/index.html">Organism library</a> &nbsp; <a class="arrow-link" href="/learn/resistance-genes.html">Resistance genes</a></p>
        {DISCLAIMER}
      </div>
    </section>"""
    shell("testing/panels/index.html", "testing", "InnovexLab Panels | Full Target Lists",
          "All InnovexLab panels with their full target lists, each target linked to its clinical summary in the organism library.", main)


def gene_anchors():
    p = ROOT / "learn/resistance-genes.html"
    s = p.read_text(encoding="utf-8")
    for gid, label in {"gene-mecA": "mecA", "gene-van": "vanA, vanB", "gene-esbl": "CTX-M, SHV, TEM", "gene-ampc": "AmpC",
                       "gene-carbapenemase": "KPC, NDM, VIM, IMP, OXA-48", "gene-qnr": "qnrA, qnrB", "gene-erm": "ermA, ermB",
                       "gene-mef": "mefA", "gene-pvl": "PVL"}.items():
        s = s.replace(f'<tr><th scope="row" data-acronyms="off">{label}</th>', f'<tr id="{gid}"><th scope="row" data-acronyms="off">{label}</th>', 1)
    p.write_text(s, encoding="utf-8", newline="\n")


HAND_PAGES = {  # hand-written pages: sources keys, or None to keep the page's own reference list
    "learn/patients.html": ["cdc-ar", "idsa-asb", "idsa-cuti", "cdc-sti"],
    "learn/infections.html": None,  # keeps its own linked "Guidance referred to" list
    "learn/resistance-genes.html": PANEL_REFS["resistance"],
}
OLD_NOTICE = "General information, not a list of InnovexLab test targets."
START, END = "<!-- MEDICAL-DISCLAIMER:START -->", "<!-- MEDICAL-DISCLAIMER:END -->"


def legal_blocks():
    for path, keys in HAND_PAGES.items():
        p = ROOT / path
        s = p.read_text(encoding="utf-8").replace(OLD_NOTICE, NOTICE)
        s = re.sub(re.escape("    " + START) + r".*?" + re.escape(END) + r"\n", "", s, flags=re.S)
        src = sources_block(keys, "page-sources-heading") if keys else ""
        block = (f'    {START}\n    <section class="section" aria-label="Sources and medical disclaimer">\n      <div class="container">\n'
                 f"        {src}\n        {DISCLAIMER}\n      </div>\n    </section>\n    {END}\n")
        s = s.replace("  </main>", block + "  </main>", 1)
        p.write_text(s, encoding="utf-8", newline="\n")


def sources_page():
    keysets = list(ORG_REFS.values()) + list(PANEL_REFS.values()) + [k for k in HAND_PAGES.values() if k]
    used = sorted({k for v in keysets for k in v}, key=lambda k: (REFS[k][0], REFS[k][1].lower()))
    refs = "\n".join(f'          <li>{esc(REFS[k][0])}. <a href="{esc(REFS[k][2])}" rel="external">{esc(REFS[k][1])}</a>.</li>' for k in used)
    rows = "\n".join(
        f'              <tr><th scope="row" data-acronyms="off"><a href="/learn/organisms/{slug}.html"><i>{esc(BY_SLUG[slug]["title"])}</i></a></th>'
        f'<td>{MICROGRAPHS[slug][4]}</td><td>{esc(IMAGE_SOURCES[slug][1])}</td>'
        f'<td><a href="{esc(IMAGE_SOURCES[slug][0])}" rel="external">Wikimedia Commons file page</a></td></tr>'
        for slug in sorted(MICROGRAPHS, key=lambda s: BY_SLUG[s]["title"].lower()))
    photo_rows = "\n".join(
        f'          <li>{esc(what)}: <a href="https://commons.wikimedia.org/wiki/File:APHIS-Moore_Air_Base_in_Texas-Plant_Protection_and_Quarantine_Science_and_Technology_Insect_Management_and_Molecular_Diagnostics_Laboratory_(20230621-CDP-APHIS-{num}).jpg" rel="external">Wikimedia Commons file page</a></li>'
        for what, num in (("Multichannel pipette over a tube strip (home page)", "0577"),
                          ("Pipette tip and sample tube (testing page)", "0661"),
                          ("Gloved hands holding a sample tube (getting-started page)", "0498")))
    disclaimer = DISCLAIMER.replace('<p><a class="arrow-link" href="/learn/sources.html">Sources, image credits and editorial policy</a></p>', "")
    main = f"""    <section class="hero hero--page" aria-labelledby="page-heading">
      <div class="container">
        <nav class="breadcrumb" aria-label="Breadcrumb"><a href="/learn/infections.html">Clinical resources</a></nav>
        <span class="eyebrow">Clinical resources</span>
        <h1 id="page-heading">Sources, image credits and disclaimer</h1>
        <p>How InnovexLab&rsquo;s clinical resources are written, the guidance they draw on, and where every image comes from.</p>
      </div>
    </section>

    <section class="section" aria-labelledby="policy-heading">
      <div class="container prose">
        <p class="education-notice" role="note"><strong>{NOTICE}</strong></p>
        <h2 id="policy-heading">Editorial policy</h2>
        <p>The organism library, the clinical overview, the resistance-gene guide and the patient page summarize guidance published by public-health agencies (chiefly the U.S. Centers for Disease Control and Prevention, CDC) and professional societies (chiefly the Infectious Diseases Society of America, IDSA). Each page lists the sources it draws on. Treatment considerations are given at drug-class level only; doses and regimens are left to the current guideline and the treating clinician.</p>
        <p>Panel pages list targets as printed on InnovexLab&rsquo;s requisition forms. A listed target describes what a panel is designed to detect; it is not a statement about any individual patient&rsquo;s result.</p>
        <p>Content was last updated in {ACCESSED}. To report an error, call <a href="tel:+13523283066">(352) 328-3066</a> or email <a href="mailto:info@innovex-lab.com">info@innovex-lab.com</a>. Please don&rsquo;t include patient information.</p>
        <h2>Sources cited</h2>
        <ol class="ref-list">
{refs}
        </ol>
        <p class="ref-note">Sources accessed {ACCESSED}. Links open external sites that InnovexLab does not control. InnovexLab is not affiliated with or endorsed by these organizations.</p>
      </div>
    </section>

    <section class="section section--surface" aria-labelledby="images-heading">
      <div class="container">
        <h2 id="images-heading">Image credits</h2>
        <p>Microscope, culture and illustration images are public domain or released under CC0, mostly from the CDC Public Health Image Library, NIAID and the USDA Agricultural Research Service, obtained through Wikimedia Commons. They show organisms, not patients. Schematic drawings are InnovexLab&rsquo;s own and are not to scale.</p>
        <div class="table-wrap" role="region" aria-label="Image credits table, scrollable" tabindex="0">
          <table class="data-table">
            <thead><tr><th scope="col">Organism page</th><th scope="col">Image and credit</th><th scope="col">Copyright status</th><th scope="col">Source</th></tr></thead>
            <tbody>
{rows}
            </tbody>
          </table>
        </div>
        <h3>Decorative laboratory photographs</h3>
        <p>The laboratory photographs on the home, testing and getting-started pages are public-domain images from the U.S. Department of Agriculture (Animal and Plant Health Inspection Service, 2023), obtained through Wikimedia Commons. They were taken in a federal laboratory and do not show InnovexLab&rsquo;s facility or staff.</p>
        <ul>
{photo_rows}
        </ul>
      </div>
    </section>

    <section class="section" aria-label="Medical disclaimer">
      <div class="container">
        {disclaimer}
      </div>
    </section>"""
    shell("learn/sources.html", "resources", "Sources, Image Credits and Disclaimer | InnovexLab",
          "Editorial policy, cited CDC and IDSA sources, image credits and the medical disclaimer for InnovexLab’s clinical resources.", main)


def main():
    missing = {slug for p in PANELS for _, t in p["sections"] for _, slug in t if not slug.startswith("gene-") and slug not in BY_SLUG}
    assert not missing, f"panel targets without an organism page: {missing}"
    write_morphs()
    gene_anchors()
    ordered = []
    for g in GROUP_ORDER:
        ordered += sorted([o for o in ORGS if o["group"] == g], key=lambda o: o["title"].lower())
    for i, o in enumerate(ordered):
        organism_page(o, ordered[i - 1] if i else None, ordered[i + 1] if i + 1 < len(ordered) else None)
    library_index()
    for p in PANELS:
        panel_page(p)
    panel_index()
    all_targets()
    legal_blocks()
    for path in HAND_PAGES:  # legal_blocks re-inserts plain source lists; expand them again
        p = ROOT / path
        p.write_text(expand_page(p.read_text(encoding="utf-8"))[0], encoding="utf-8", newline="\n")
    sources_page()
    print(f"built {len(ordered)} organism pages, library index, {len(PANELS)} panel pages + panel index, {len(MORPH)} schematics")


if __name__ == "__main__":
    main()
