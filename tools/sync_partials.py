#!/usr/bin/env python3
"""Copy shared HTML partials (header, CTA band, footer) into every page.

Why this exists
---------------
The site is plain HTML served by GitHub Pages with no build step, so there is
no template engine to include a shared header. Instead each page contains
marker comments, and this script rewrites the content between them from the
files in ``partials/``:

    <!-- PARTIAL:header -->   ...generated...   <!-- /PARTIAL:header -->

Edit ``partials/<name>.html``, then run::

    python tools/sync_partials.py          # rewrite pages in place
    python tools/sync_partials.py --check  # CI mode: fail if any page is stale

Active navigation
-----------------
Each page's ``<body data-page="testing">`` value is matched against the nav
links' ``data-nav="testing"`` attribute; the matching link gets
``aria-current="page"`` so screen readers and CSS know the current page.

Only the Python standard library is used.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PARTIALS_DIR = ROOT / "partials"

# Matches one marked block; group 1 = partial name, group 2 = indentation of the opening marker.
BLOCK_RE = re.compile(
    r"(?P<indent>[ \t]*)<!-- PARTIAL:(?P<name>[\w-]+) -->\n.*?<!-- /PARTIAL:(?P=name) -->",
    re.DOTALL,
)
PAGE_RE = re.compile(r'<body[^>]*\bdata-page="([\w-]+)"')


def render_partial(name: str, page_id: str | None, indent: str) -> str:
    """Return the partial's markup, indented and with aria-current applied."""
    path = PARTIALS_DIR / f"{name}.html"
    if not path.exists():
        raise SystemExit(f"error: page references missing partial {path.relative_to(ROOT)}")
    body = path.read_text(encoding="utf-8").rstrip("\n")
    if page_id:
        body = body.replace(f'data-nav="{page_id}"', f'data-nav="{page_id}" aria-current="page"')
    lines = [(indent + line) if line.strip() else "" for line in body.split("\n")]
    note = f"{indent}<!-- Generated from partials/{name}.html by tools/sync_partials.py. Edit the partial, not this block. -->"
    return (
        f"{indent}<!-- PARTIAL:{name} -->\n{note}\n"
        + "\n".join(lines)
        + f"\n{indent}<!-- /PARTIAL:{name} -->"
    )


def sync_page(path: Path) -> tuple[str, str]:
    """Return (original, updated) text for one HTML page."""
    original = path.read_text(encoding="utf-8")
    match = PAGE_RE.search(original)
    page_id = match.group(1) if match else None

    def replace(m: re.Match) -> str:
        return render_partial(m.group("name"), page_id, m.group("indent"))

    return original, BLOCK_RE.sub(replace, original)


def main(argv: list[str]) -> int:
    check_only = "--check" in argv
    stale = []
    for page in sorted([*ROOT.glob("*.html"), *ROOT.glob("testing/*.html"), *ROOT.glob("learn/*.html"),
                         *ROOT.glob("testing/panels/*.html"), *ROOT.glob("learn/organisms/*.html")]):
        original, updated = sync_page(page)
        if original == updated:
            continue
        stale.append(page.name)
        if not check_only:
            page.write_text(updated, encoding="utf-8", newline="\n")
            print(f"updated {page.name}")
    if check_only and stale:
        print("Pages out of sync with partials/: " + ", ".join(stale))
        print("Run: python tools/sync_partials.py")
        return 1
    if not stale:
        print("All pages already in sync with partials/.")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
