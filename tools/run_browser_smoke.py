#!/usr/bin/env python3
"""Run tests/browser_smoke.html in headless Chrome/Edge and report the result.

Usage (from the repo root)::

    python tools/run_browser_smoke.py            # starts its own preview server
    python tools/run_browser_smoke.py --browser "C:/path/to/chrome.exe"

What it does
1. Builds temporary fixtures in tests/ (git-ignored, deleted afterwards):
   - fixture_no_js.html / fixture_no_js_contact.html: site.js URL broken on
     purpose (menu fail-safe; the form must still validate natively);
   - fixture_portal.html: portalUrl set to a dummy https URL (enabled portal);
   - fixture_portal_bad.html: portalUrl set to a non-https value (must stay hidden).
2. Serves the repo on a free localhost port.
3. Opens the smoke page in headless Chrome with a throw-away profile and reads
   the results from the DOM (--dump-dom).
4. Prints each PASS/FAIL line.

Exit codes
  0  every test passed
  1  at least one test failed (a real site problem)
  2  the browser produced no results (environment problem: browser missing,
     blocked by a sandbox, crashed, or timed out). Diagnostics are printed so
     this is never confused with a pass or with a test failure.

Only the Python standard library is used. Needs Google Chrome or Microsoft Edge.
"""
from __future__ import annotations

import functools
import http.server
import re
import shutil
import subprocess
import sys
import tempfile
import threading
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
TESTS = ROOT / "tests"
CANDIDATES = [
    r"C:\Program Files\Google\Chrome\Application\chrome.exe",
    r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
    r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
    "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
    "google-chrome", "chromium", "chromium-browser", "chrome",
]


def find_browser(argv: list[str]) -> str:
    if "--browser" in argv:
        return argv[argv.index("--browser") + 1]
    for c in CANDIDATES:
        if Path(c).exists() or shutil.which(c):
            return c
    raise SystemExit("No Chrome/Edge found; pass --browser <path>.")


def build_fixtures() -> list[Path]:
    """Write the temporary fixture pages; return their paths so they can be deleted."""
    def variant(src: str, name: str, title: str, old: str, new: str) -> Path:
        html = (ROOT / src).read_text(encoding="utf-8")
        assert old in html, f"{src}: expected {old!r} (fixture would be meaningless)"
        html = html.replace(old, new).replace("<title>", f"<title>[TEST FIXTURE — {title}] ", 1)
        path = TESTS / name
        path.write_text(html, encoding="utf-8", newline="\n")
        return path

    def config(name: str, body: str) -> Path:
        # A separate .js file, not an inline <script>: the pages' Content-Security-Policy
        # only allows same-origin scripts plus the one hashed inline script.
        path = TESTS / name
        path.write_text(body, encoding="utf-8", newline="\n")
        return path

    no_js = ("/assets/js/site.js", "/assets/js/does-not-exist.js")
    cfg = '<script src="/assets/js/site-config.js" defer></script>'
    return [
        variant("index.html", "fixture_no_js.html", "site.js missing", *no_js),
        variant("contact.html", "fixture_no_js_contact.html", "site.js missing", *no_js),
        config("fixture_portal_config.js",
               'window.INNOVEX_CONFIG={portalUrl:"https://portal.example.test/login",'
               'portalExternalLabel:"(opens the client portal in a new tab)"};\n'),
        variant("index.html", "fixture_portal.html", "portal enabled", cfg,
                '<script src="/tests/fixture_portal_config.js" defer></script>'),
        config("fixture_portal_bad_config.js", 'window.INNOVEX_CONFIG={portalUrl:"javascript:alert(1)"};\n'),
        variant("index.html", "fixture_portal_bad.html", "non-https portal", cfg,
                '<script src="/tests/fixture_portal_bad_config.js" defer></script>'),
    ]


def main(argv: list[str]) -> int:
    browser = find_browser(argv)
    fixtures = build_fixtures()

    class QuietHandler(http.server.SimpleHTTPRequestHandler):
        def log_message(self, *args):  # keep test output readable
            pass

    handler = functools.partial(QuietHandler, directory=str(ROOT))
    server = http.server.ThreadingHTTPServer(("127.0.0.1", 0), handler)
    port = server.server_address[1]
    threading.Thread(target=server.serve_forever, daemon=True).start()
    profile = tempfile.mkdtemp(prefix="innovex-smoke-")
    url = f"http://127.0.0.1:{port}/tests/browser_smoke.html"
    try:
        # A throw-away --user-data-dir avoids clashing with a Chrome window the
        # developer already has open (a common cause of empty output).
        proc = subprocess.run(
            [browser, "--headless=new", "--disable-gpu", "--no-first-run",
             "--no-default-browser-check", f"--user-data-dir={profile}",
             "--virtual-time-budget=30000", "--dump-dom", url],
            capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=180,
        )
        out, err, code = proc.stdout, proc.stderr, proc.returncode
    except (OSError, subprocess.TimeoutExpired) as exc:
        out, err, code = "", repr(exc), None
    finally:
        server.shutdown()
        for f in fixtures:
            f.unlink(missing_ok=True)
        shutil.rmtree(profile, ignore_errors=True)

    m = re.search(r'<pre id="results">(.*?)</pre>', out, re.S)
    if not m or "SUMMARY:" not in m.group(1):
        print("ENVIRONMENT FAILURE: the browser returned no test results.")
        print(f"  browser: {browser}\n  exit code: {code}\n  stdout bytes: {len(out)}")
        print("  stderr (last 15 lines):")
        for line in (err or "").strip().splitlines()[-15:]:
            print("    " + line)
        print("  Not a test result. Check the browser can start headless here (sandboxed "
              "agents often block it), then rerun. Manual run: python -m http.server 8765 and "
              "open http://127.0.0.1:8765/tests/browser_smoke.html")
        return 2
    text = m.group(1).replace("&amp;", "&").replace("&lt;", "<").replace("&gt;", ">")
    print(text)
    return 0 if "SUMMARY: PASS" in text else 1


if __name__ == "__main__":
    # Windows consoles (cp1252) cannot print every character; never crash on output.
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(errors="replace")
    sys.exit(main(sys.argv[1:]))
