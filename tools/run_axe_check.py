#!/usr/bin/env python3
"""Automated WCAG scan of every page with axe-core, in headless Chrome.

Usage (from the repo root)::

    python tools/run_axe_check.py --axe path/to/axe.min.js [--browser chrome.exe]

axe-core is NOT vendored in this repo (third-party code; keeps the public repo
small). Get the pinned copy and check it:

    curl -L -o axe.tgz https://registry.npmjs.org/axe-core/-/axe-core-4.10.2.tgz
    tar -xzf axe.tgz package/axe.min.js
    # npm "integrity" of the tarball (sha512, base64):
    #   RE3mdQ7P3FRSe7eqCWoeQ/Z9QXrtniSjp1wUjt5nRC3WIpz5rSCve6o3fsZ2aCpJtrZjSZgjwXAoTO5k4tEI0w==
    # package/axe.min.js sha256 is checked by this script (AXE_SHA256 below).

What it does
    Loads each page at 1366px and 390px, injects axe and runs the rules tagged
    wcag2a, wcag2aa, wcag21a, wcag21aa, wcag22aa and best-practice. Prints every
    violation (impact, rule, elements) and the "incomplete" items axe could not
    decide (for example text over a gradient): those need a person to look.

Exit codes: 0 no violations, 1 violations found, 2 environment problem.
An automated scan covers only part of WCAG. Keyboard behaviour is checked by
tools/run_keyboard_check.py; the rest still needs human review.
"""
from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from run_browser_smoke import find_browser  # noqa: E402
from run_keyboard_check import PAGES, WIDTHS, EnvironmentFailure, chrome_session, set_width  # noqa: E402

AXE_SHA256 = "b511cd9dec01c76f4b2ad1723b66b6db37d4c2eb4ed199076e1829d9ee7b75e3"  # axe-core 4.10.2
TAGS = ["wcag2a", "wcag2aa", "wcag21a", "wcag21aa", "wcag22aa", "best-practice"]

RUN_JS = """axe.run(document, {runOnly: {type: 'tag', values: %s},
                     resultTypes: ['violations', 'incomplete']})
  .then(r => ({
    version: axe.version,
    violations: r.violations.map(v => ({id: v.id, impact: v.impact, help: v.help,
                                        nodes: v.nodes.map(n => n.target.join(' ')).slice(0, 6)})),
    incomplete: r.incomplete.map(v => ({id: v.id, count: v.nodes.length,
                                        nodes: v.nodes.map(n => n.target.join(' ')).slice(0, 4)}))
  }))"""


# axe cannot rate text over a CSS gradient (it reports it as "incomplete").
# This supplementary check takes every colour stop of the gradient(s) behind
# the text and computes the WORST case: each opaque stop as the base, with
# each translucent layer either absent or at its full alpha. It is
# conservative (a radial glow is assumed to reach every pixel).
GRADIENT_JS = r"""(() => {
  const parse = s => (s.match(/rgba?\([^)]*\)/g) || []).map(c => {
    const v = c.match(/[\d.]+/g).map(Number); return [v[0], v[1], v[2], v.length > 3 ? v[3] : 1]; });
  const lum = c => { const f = v => { v /= 255; return v <= .03928 ? v / 12.92 : Math.pow((v + .055) / 1.055, 2.4); };
                     return .2126 * f(c[0]) + .7152 * f(c[1]) + .0722 * f(c[2]); };
  const ratio = (a, b) => { const x = lum(a), y = lum(b); return (Math.max(x, y) + .05) / (Math.min(x, y) + .05); };
  const over = (top, base) => [0, 1, 2].map(i => top[i] * top[3] + base[i] * (1 - top[3]));
  const out = [];
  document.querySelectorAll('body *').forEach(el => {
    const own = Array.from(el.childNodes).some(n => n.nodeType === 3 && n.textContent.trim());
    if (!own || !el.getClientRects().length) return;
    const cs = getComputedStyle(el);
    if (cs.visibility === 'hidden') return;
    let bgEl = el, solid = null;
    for (; bgEl; bgEl = bgEl.parentElement) {
      const b = getComputedStyle(bgEl);
      if (b.backgroundImage.includes('gradient')) break;
      const c = parse(b.backgroundColor)[0];
      if (c && c[3] > 0) { solid = c; break; }
    }
    if (!bgEl || solid) return;                       // solid background: axe already rated it
    const b = getComputedStyle(bgEl);
    const stops = parse(b.backgroundImage).concat(parse(b.backgroundColor));
    const bases = stops.filter(c => c[3] === 1), glazes = stops.filter(c => c[3] > 0 && c[3] < 1);
    const fg = parse(cs.color)[0];
    let worst = Infinity;
    bases.forEach(base => {
      for (let mask = 0; mask < (1 << glazes.length); mask++) {
        let c = base.slice(0, 3);
        glazes.forEach((g, i) => { if (mask & (1 << i)) c = over(g, c); });
        worst = Math.min(worst, ratio(fg.slice(0, 3), c));
      }
    });
    const size = parseFloat(cs.fontSize), bold = parseInt(cs.fontWeight, 10) >= 700;
    const need = (size >= 24 || (bold && size >= 18.66)) ? 3 : 4.5;
    out.push({sel: el.tagName.toLowerCase() + (el.className ? '.' + String(el.className).split(' ')[0] : ''),
              text: el.textContent.trim().slice(0, 30), worst: Math.round(worst * 100) / 100, need});
  });
  return out;
})()"""


def main(argv: list[str]) -> int:
    if "--axe" not in argv:
        print("Pass --axe path/to/axe.min.js (see the docstring for the pinned download).")
        return 2
    source = Path(argv[argv.index("--axe") + 1]).read_bytes()
    digest = hashlib.sha256(source).hexdigest()
    if digest != AXE_SHA256 and "--allow-other-axe" not in argv:
        print(f"axe.min.js sha256 {digest} is not the pinned 4.10.2 build; "
              "pass --allow-other-axe to use it anyway.")
        return 2
    verbose = "--verbose" in argv
    browser = find_browser(argv)
    violations = 0
    try:
        with chrome_session(browser, "innovex-axe-") as (page, base):
            for width, height in WIDTHS:
                set_width(page, width, height)
                for path in PAGES:
                    page.goto(base + path)
                    page.js(source.decode("utf-8"))
                    r = page.js(RUN_JS % json.dumps(TAGS))
                    status = "PASS" if not r["violations"] else "FAIL"
                    review = ", ".join(f"{i['id']} x{i['count']}" for i in r["incomplete"]) or "none"
                    print(f"{status} {width}px {path}: {len(r['violations'])} violations "
                          f"(axe {r['version']}); for human review: {review}")
                    for v in r["violations"]:
                        violations += 1
                        print(f"    [{v['impact']}] {v['id']}: {v['help']}")
                        for n in v["nodes"]:
                            print(f"        {n}")
                    if verbose:
                        for i in r["incomplete"]:
                            print(f"    review {i['id']}: {'; '.join(i['nodes'])}")
                    grad = page.js(GRADIENT_JS)
                    low = [g for g in grad if g["worst"] < g["need"]]
                    lowest = min((g["worst"] for g in grad), default=None)
                    print(f"{'PASS' if not low else 'FAIL'} {width}px {path}: text over gradients, "
                          f"worst-case contrast ({len(grad)} elements; lowest {lowest})")
                    for g in low:
                        violations += 1
                        print(f"    {g['sel']} '{g['text']}': {g['worst']}:1 < {g['need']}:1")
    except EnvironmentFailure as exc:
        print(f"ENVIRONMENT FAILURE: could not start or drive the browser: {exc}")
        return 2
    except Exception as exc:
        print(f"ERROR: run aborted ({exc!r}). Not a test result.")
        return 2
    print(f"SUMMARY: {'PASS' if not violations else 'FAIL'} ({violations} violations)")
    return 0 if not violations else 1


if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(errors="replace")
    sys.exit(main(sys.argv[1:]))
