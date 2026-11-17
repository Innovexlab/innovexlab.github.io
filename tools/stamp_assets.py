#!/usr/bin/env python3
"""Add a content-hash version to the shared CSS/JS references on every page, so browsers (and GitHub
Pages caches) fetch the new file whenever it changes:

    <link rel="stylesheet" href="/assets/css/site.css?v=1a2b3c4d">
    <script src="/assets/js/site.js?v=5e6f7a8b" defer></script>

    python tools/stamp_assets.py           # rewrite pages
    python tools/stamp_assets.py --check   # exit 1 if any page has a missing or stale version

check_site.py runs the --check mode. Run this after editing site.css / site.js / site-config.js.
"""
from __future__ import annotations

import hashlib
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
ASSETS = ["assets/css/site.css", "assets/js/site.js", "assets/js/site-config.js"]
SKIP = {".git", "tools", "tests", "partials", "docs", ".github", "node_modules"}


def version(rel):
    return hashlib.sha256((ROOT / rel).read_bytes()).hexdigest()[:8]


def pages():
    for p in sorted(ROOT.rglob("*.html")):
        if not any(part in SKIP for part in p.relative_to(ROOT).parts[:-1]):
            yield p


def main(argv):
    check = "--check" in argv
    versions = {a: version(a) for a in ASSETS}
    stale = []
    for page in pages():
        s = page.read_text(encoding="utf-8")
        new = s
        for asset, v in versions.items():
            new = re.sub(rf'(["\'])/{re.escape(asset)}(?:\?v=[0-9a-f]+)?\1', rf'\1/{asset}?v={v}\1', new)
        if new != s:
            if check:
                stale.append(page.relative_to(ROOT).as_posix())
            else:
                page.write_text(new, encoding="utf-8", newline="\n")
    if check and stale:
        print(f"stale asset versions in {len(stale)} page(s), e.g. {stale[:3]}; run python tools/stamp_assets.py")
        return 1
    if not check:
        print("stamped", versions)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
