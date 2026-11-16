#!/usr/bin/env python3
"""Check that the site's external links still open (needs internet; not run in CI).

Usage (from the repo root)::

    python tools/check_external_links.py

What it does
    Collects every external https:// <a href> on the public pages (the same
    pages tools/check_site.py scans), skips our own domain (canonical/OG URLs
    point at the live site, which changes only on release) and the form
    service (it is a POST target, never a link to visit), then makes one GET
    request per unique URL and reports the HTTP status.

Nothing is posted or submitted. Exit codes: 0 all reachable, 1 at least one
link failed, 2 no network at all.
"""
from __future__ import annotations

import sys
import urllib.error
import urllib.request
from html.parser import HTMLParser
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from check_site import ROOT, find_pages  # noqa: E402

SKIP_HOSTS = ("www.innovexlab.com", "innovexlab.com", "formsubmit.co")


class Anchors(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.hrefs: list[str] = []

    def handle_starttag(self, tag, attrs):
        href = dict(attrs).get("href") or ""
        if tag == "a" and href.startswith("https://"):
            self.hrefs.append(href)


def main() -> int:
    urls: dict[str, list[str]] = {}
    for page in find_pages():
        parser = Anchors()
        parser.feed(page.read_text(encoding="utf-8"))
        for href in parser.hrefs:
            host = href.split("/")[2]
            if host not in SKIP_HOSTS:
                urls.setdefault(href, []).append(page.relative_to(ROOT).as_posix())
    failed = errors = 0
    for url, pages in sorted(urls.items()):
        req = urllib.request.Request(url, headers={"User-Agent": "innovexlab-link-check/1.0"})
        try:
            with urllib.request.urlopen(req, timeout=20) as resp:
                status = resp.status
        except urllib.error.HTTPError as exc:
            status = exc.code
        except (urllib.error.URLError, TimeoutError, OSError) as exc:
            print(f"ERROR {url} ({exc}) on {', '.join(sorted(set(pages)))}")
            errors += 1
            continue
        ok = 200 <= status < 400
        failed += not ok
        print(f"{'PASS' if ok else 'FAIL'} {status} {url} on {', '.join(sorted(set(pages)))}")
    if urls and errors == len(urls):
        print("ENVIRONMENT FAILURE: no external link could be reached (offline?). Not a result.")
        return 2
    print(f"SUMMARY: {'PASS' if not (failed or errors) else 'FAIL'} ({len(urls)} external links)")
    return 0 if not (failed or errors) else 1


if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(errors="replace")
    sys.exit(main())
