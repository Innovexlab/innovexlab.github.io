#!/usr/bin/env python3
"""Spell out each acronym at its first use in a page's <main> content.

The glossary lives in tools/content/acronyms.py. tools/build_library.py applies this to the
pages it generates. For hand-written pages, run:

    python tools/expand_acronyms.py            # rewrite pages in place
    python tools/expand_acronyms.py --check    # list what would change, exit 1 if anything

It is idempotent: an acronym already written as "expansion (ACR)" or "ACR (gloss)" is left
alone. Headings, column headers (<th> without scope="row"), <abbr>, <code>, <script>,
<style> and elements marked data-acronyms="off" are skipped; the first use in running text
is expanded instead.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools" / "content"))
from acronyms import ACRONYMS, NOT_ACRONYMS  # noqa: E402

SKIP_TAGS = {"h1", "h2", "h3", "h4", "h5", "h6", "th", "abbr", "code", "script", "style", "title", "button", "svg"}
BLOCK_TAGS = {"p", "li", "td", "th", "dd", "dt", "div", "figcaption", "caption", "section", "article",
              "aside", "ol", "ul", "dl", "figure", "blockquote", "option", "label", "legend", "summary", "br",
              "h1", "h2", "h3", "h4", "h5", "h6", "table", "tr", "main"}
VOID = {"br", "img", "hr", "input", "meta", "link", "source", "wbr", "col"}

_tokens = sorted(ACRONYMS, key=len, reverse=True)
TOKEN_RE = re.compile(r"(?<![\w\-./#])(" + "|".join(re.escape(t) for t in _tokens) + r")(s?)(?![\w])(?!-\d)")
# Norovirus GI / GII are genogroups, not "gastrointestinal".
GENOGROUP = re.compile(r"Norovirus\s*$")
CAPS_RE = re.compile(r"(?<![\w\-./#])([A-Z][A-Za-z]*[A-Z][A-Za-z0-9]*(?:-[A-Za-z0-9]+)*|[A-Z]{2,}[0-9]*)(?![\w])")


def family(tok):
    e = ACRONYMS[tok]
    return e[2] if len(e) > 2 else tok


def plural(exp):
    return exp if exp.endswith("s") and not exp.endswith("ss") else exp + "s"


def render(tok, pl, ctx_before, after=""):
    """Return (text replacing the token plus any compound suffix, consumed suffix length, lead?)."""
    exp, style = ACRONYMS[tok][0], ACRONYMS[tok][1]
    word = tok + pl
    if style == "gloss":
        comp = re.match(r"-[A-Za-z]+", after)
        if comp:  # COLA-accredited -> COLA-accredited (COLA: gloss)
            return f"{word}{comp.group(0)} ({tok}: {exp})", len(comp.group(0)), False
        return f"{word} ({exp})", 0, False
    full = plural(exp) if pl else exp
    if not ctx_before.strip() or re.search(r"[.!?]\s*$", ctx_before):
        full = full[:1].upper() + full[1:]
    return f"{full} ({word})", 0, True


def _norm(t):
    return re.sub(r"\s+", " ", t).lower().replace("’", "'")


def already_explained(tok, pl, before, after):
    """True if this occurrence is already explained next to it."""
    exp = ACRONYMS[tok][0]
    first = re.escape(exp.split()[0].lower().strip(","))
    m = re.match(r"(?:-[A-Za-z]+)?\s*\(([^)]*)", after)
    if m and (re.search(r"\b" + first + r"\b", m.group(1).lower()) or tok in m.group(1)):
        return True  # ACR (gloss) or ACR-word (ACR is ...)
    if before.rstrip().endswith("("):
        return True  # "phrase (ACR": the acronym abbreviates the phrase before it
    if _norm(exp) in _norm(before) or _norm(plural(exp)) in _norm(before):
        return True  # expansion written before, e.g. "(carbapenem-resistant Enterobacterales, CRE)"
    if _norm(exp) in _norm(after[:len(exp) + 25]):
        return True  # "COLA is a national organization ..."
    return False


def fix_article(before, rendered):
    m = re.search(r"\b([Aa]n?) $", before)
    if not m:
        return before
    want_an = bool(re.match(r"[aeioAEIO]", rendered))
    art = m.group(1)
    new = ("An" if art[0] == "A" else "an") if want_an else ("A" if art[0] == "A" else "a")
    return before[:m.start(1)] + new + " "


class Expander:
    """Walks <main> HTML, keeping text per block element so context spans inline tags."""

    def __init__(self):
        self.seen: set[str] = set()
        self.changes: list[str] = []
        self.unexplained: list[str] = []

    def run(self, html):
        out, stack = [], []
        block_text = ""  # plain text of the current block so far (for capitals and articles)
        for part in re.split(r"(<!--.*?-->|<[^>]+>)", html, flags=re.S):
            if not part:
                continue
            if part.startswith("<"):
                m = re.match(r"</?\s*([a-zA-Z0-9]+)", part)
                if m and not part.startswith("<!"):
                    name = m.group(1).lower()
                    if part.startswith("</"):
                        if name in stack or name + "!" in stack:
                            while stack and stack.pop().rstrip("!") != name:
                                pass
                    elif name not in VOID and not part.endswith("/>"):
                        # Skip headings, column headers and anything marked data-acronyms="off";
                        # row headers (<th scope="row">) are processed like table cells.
                        off = (name in SKIP_TAGS and not (name == "th" and 'scope="row"' in part))                             or 'data-acronyms="off"' in part
                        stack.append(name + ("!" if off else ""))
                    if name in BLOCK_TAGS or 'class="lib-aka"' in part:
                        block_text = ""  # card descriptions start a new sentence
                out.append(part)
                continue
            skipping = any(t.endswith("!") for t in stack)
            out.append(part if skipping else self._text(part, block_text))
            block_text += out[-1]
        return "".join(out)

    def _text(self, text, block_before):
        res, pos = [], 0
        for m in TOKEN_RE.finditer(text):
            tok, pl = m.group(1), m.group(2)
            if pl and tok + pl in ACRONYMS:
                continue
            fam = family(tok)
            before_local = text[:m.start()]
            before = block_before + "".join(res) + text[pos:m.start()]
            if tok in ("GI", "GII") and GENOGROUP.search(before):
                key, label = "genogroup-" + tok, " (genogroup " + tok[1:] + ")"
                if key not in self.seen:
                    self.seen.add(key)
                    if not text[m.end():].startswith(" (genogroup"):
                        res.append(text[pos:m.end()] + label)
                        pos = m.end()
                continue
            if fam in self.seen:
                continue
            self.seen.add(fam)
            if already_explained(tok, pl, before, text[m.end():]):
                continue
            if re.match(r"\s*\(", text[m.end():]):
                self.unexplained.append(f"{tok + pl} followed by parentheses | …{before[-40:]}{text[m.start():m.end() + 30]}")
                continue
            if before.count("(") > before.count(")"):
                self.unexplained.append(f"{tok + pl} inside parentheses | …{before[-60:]}")
                continue
            rendered, extra, lead = render(tok, pl, before, text[m.end():])
            chunk = text[pos:m.start()]
            if lead:
                chunk = fix_article(chunk, rendered) if chunk else chunk
            res.append(chunk + rendered)
            pos = m.end() + extra
            self.changes.append(f"{tok + pl} -> {rendered}  | …{before_local[-40:]}")
        res.append(text[pos:])
        return "".join(res)


def expand_main(main_html):
    ex = Expander()
    return ex.run(main_html), ex


def expand_page(s):
    m = re.search(r'(<main id="main">)(.*?)(</main>)', s, flags=re.S)
    if not m:
        return s, Expander()
    body, ex = expand_main(m.group(2))
    return s[:m.start(2)] + body + s[m.end(2):], ex


def unknown_caps(s):
    """All-caps words in <main> running text that are neither in the glossary nor allowed."""
    m = re.search(r'<main id="main">(.*?)</main>', s, flags=re.S)
    if not m:
        return []
    text = re.sub(r"(?s)<(script|style)\b.*?</\1>|<!--.*?-->", " ", m.group(1))
    text = re.sub(r"<[^>]+>", " ", text)
    found = set()
    for w in CAPS_RE.findall(text):
        base = w[:-1] if w.endswith("s") and w[:-1] in ACRONYMS else w
        if base in ACRONYMS or base in NOT_ACRONYMS or re.fullmatch(r"[A-Z]-?[0-9]*", base):
            continue
        if any(base.startswith(a + "-") and a in ACRONYMS for a in ACRONYMS):
            continue  # compound such as ESBL-producing
        found.add(w)
    return sorted(found)


def hand_pages():
    gen = {"learn/organisms", "testing"}
    for p in sorted(ROOT.glob("**/*.html")):
        rel = p.relative_to(ROOT).as_posix()
        if rel.startswith(("partials/", "tests/", "docs/", "node_modules/")) or rel == "learn/sources.html" or any(rel.startswith(g + "/") for g in gen):
            continue
        yield p


def main(argv):
    check = "--check" in argv
    pages = [(ROOT / a).resolve() for a in argv if not a.startswith("--")] or list(hand_pages())
    dirty = 0
    for p in pages:
        s = p.read_text(encoding="utf-8")
        new, ex = expand_page(s)
        if new != s:
            dirty += 1
            print(f"{p.relative_to(ROOT).as_posix()}:")
            for c in ex.changes:
                print("   ", c)
            if not check:
                p.write_text(new, encoding="utf-8", newline="\n")
        if ex.unexplained:
            print(f"{p.relative_to(ROOT).as_posix()}: NEEDS MANUAL WORDING")
            for c in ex.unexplained:
                print("   !", c)
    print(("would change" if check else "changed"), dirty, "page(s)")
    return 1 if (check and dirty) else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
