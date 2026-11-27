#!/usr/bin/env python3
"""Real keyboard (Tab-key) navigation check for every page, in headless Chrome.

Usage (from the repo root)::

    python tools/run_keyboard_check.py
    python tools/run_keyboard_check.py --browser "C:/path/to/chrome.exe"

Why this exists
    tests/browser_smoke.html can only call element.focus() from script. That
    proves each control *can* show a focus ring, but not what a keyboard user
    actually gets. This script drives Chrome through the DevTools Protocol and
    sends genuine key events (Tab, Shift+Tab, Enter, Escape), the same input
    path as a physical keyboard.

What it checks, at 1366px (desktop) and 390px (phone) for each page
    1. Skip link: the first Tab lands on "Skip to main content" and it is on
       screen; Enter then Tab moves into <main> (past the header).
    2. Tab order: pressing Tab visits every visible focusable element exactly
       once, in DOM (reading) order, then leaves the page: no keyboard trap,
       no positive tabindex, nothing skipped.
    3. Every stop: :focus-visible matches, a focus indicator is drawn (outline
       or box-shadow), the element is scrolled into the viewport and is not
       entirely hidden behind the sticky header (WCAG 2.4.3, 2.4.7, 2.4.11).
    4. Shift+Tab walks backwards through the same order.
    5. Phone menu (390px): Tab to "Menu", Enter opens it (aria-expanded=true)
       and the next Tab enters the links; Escape closes it and returns focus
       to the button.
    6. Contact form: Tab to the submit button with the form empty, press
       Enter. The error summary appears and takes focus; Tab reaches the
       first error link; Enter on it moves focus to that field.
       Safety: requests to formsubmit.co are blocked at the browser, and an
       empty form never passes validation, so nothing can be sent.
    7. Portal switched on (temporary fixture with a dummy https URL): the
       revealed portal links join the Tab order with a visible focus ring, at
       both widths. (The real site keeps them hidden until a verified URL.)
    8. Windows High Contrast / forced colours (1366px, Home and Contact): box
       shadows are dropped in that mode, so every stop must still draw an
       outline of at least 2px (WCAG 2.4.7 in forced-colours mode).

Exit codes: 0 all pass, 1 a check failed, 2 the browser could not be driven
(environment problem; never a pass).

Standard library only (includes a minimal WebSocket client for DevTools).
"""
from __future__ import annotations

import base64
import contextlib
import functools
import http.server
import json
import os
import shutil
import socket
import struct
import subprocess
import sys
import tempfile
import threading
import time
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from run_browser_smoke import ROOT, build_fixtures, find_browser  # noqa: E402  (shared helpers)

PAGES = ["/index.html", "/testing.html", "/how-to-start.html", "/about.html",
         "/contact.html", "/thankyou.html", "/404.html"]
# Focused pages (testing/*.html, e.g. the UTI draft) are picked up automatically.
PAGES += [f"/{d}/{p.name}" for d in ("testing", "learn", "testing/panels", "learn/organisms")
          for p in sorted((ROOT / d).glob("*.html"))]
WIDTHS = [(1366, 900), (390, 844)]


# --- Minimal WebSocket client (RFC 6455, text frames only) ----------------
class WebSocket:
    def __init__(self, url: str):
        assert url.startswith("ws://")
        hostport, _, path = url[5:].partition("/")
        host, _, port = hostport.partition(":")
        self.sock = socket.create_connection((host, int(port)), timeout=30)
        key = base64.b64encode(os.urandom(16)).decode()
        self.sock.sendall((f"GET /{path} HTTP/1.1\r\nHost: {hostport}\r\nUpgrade: websocket\r\n"
                           f"Connection: Upgrade\r\nSec-WebSocket-Key: {key}\r\n"
                           "Sec-WebSocket-Version: 13\r\n\r\n").encode())
        head = b""
        while b"\r\n\r\n" not in head:
            chunk = self.sock.recv(1)
            if not chunk:
                raise ConnectionError("WebSocket handshake failed")
            head += chunk
        if b" 101 " not in head.split(b"\r\n", 1)[0]:
            raise ConnectionError(head.decode(errors="replace"))

    def _recv_exact(self, n: int) -> bytes:
        buf = b""
        while len(buf) < n:
            chunk = self.sock.recv(n - len(buf))
            if not chunk:
                raise ConnectionError("WebSocket closed")
            buf += chunk
        return buf

    def send(self, text: str) -> None:
        data = text.encode()
        header = bytearray([0x81])  # FIN + text
        n = len(data)
        if n < 126:
            header.append(0x80 | n)
        elif n < 65536:
            header += bytes([0x80 | 126]) + struct.pack(">H", n)
        else:
            header += bytes([0x80 | 127]) + struct.pack(">Q", n)
        mask = os.urandom(4)  # clients must mask frames
        self.sock.sendall(bytes(header) + mask + bytes(b ^ mask[i % 4] for i, b in enumerate(data)))

    def recv(self) -> str:
        message = b""
        while True:
            b1, b2 = self._recv_exact(2)
            n = b2 & 0x7F
            if n == 126:
                n = struct.unpack(">H", self._recv_exact(2))[0]
            elif n == 127:
                n = struct.unpack(">Q", self._recv_exact(8))[0]
            payload = self._recv_exact(n)
            if b1 & 0x0F == 0x9:      # ping -> ignore (Chrome doesn't need pong here)
                continue
            message += payload
            if b1 & 0x80:             # FIN
                return message.decode()


class Page:
    """One Chrome tab driven over DevTools."""

    def __init__(self, ws_url: str):
        self.ws = WebSocket(ws_url)
        self.next_id = 0
        self.events: list[dict] = []

    def call(self, method: str, **params):
        self.next_id += 1
        my_id = self.next_id
        self.ws.send(json.dumps({"id": my_id, "method": method, "params": params}))
        while True:
            msg = json.loads(self.ws.recv())
            if msg.get("id") == my_id:
                if "error" in msg:
                    raise RuntimeError(f"{method}: {msg['error']}")
                return msg.get("result", {})
            self.events.append(msg)

    def js(self, expression: str):
        r = self.call("Runtime.evaluate", expression=expression, returnByValue=True, awaitPromise=True)
        if "exceptionDetails" in r:
            raise RuntimeError(r["exceptionDetails"].get("text", "") + " " + expression[:80])
        return r["result"].get("value")

    def goto(self, url: str) -> None:
        self.events.clear()
        self.call("Page.navigate", url=url)
        deadline = time.time() + 20
        while time.time() < deadline:
            if any(e.get("method") == "Page.loadEventFired" for e in self.events):
                break
            self.events.append(json.loads(self.ws.recv()))
        self.js("document.fonts ? document.fonts.ready.then(() => true) : true")
        time.sleep(0.15)

    def key(self, name: str, shift: bool = False) -> None:
        codes = {"Tab": 9, "Enter": 13, "Escape": 27}
        base = {"key": name, "code": name, "windowsVirtualKeyCode": codes[name],
                "nativeVirtualKeyCode": codes[name], "modifiers": 8 if shift else 0}
        down = dict(base, type="keyDown")
        if name == "Enter":
            down["text"] = "\r"
        self.call("Input.dispatchKeyEvent", **down)
        self.call("Input.dispatchKeyEvent", **dict(base, type="keyUp"))
        time.sleep(0.03)


# In-page helpers: number every focusable element we expect Tab to reach, and
# describe whatever currently has focus.
INDEX_JS = r"""(() => {
  const sel = 'a[href], button, input, select, textarea, summary, video[controls], audio[controls], [tabindex], [contenteditable=""], [contenteditable=true]';
  const all = Array.from(document.querySelectorAll(sel));
  all.forEach(el => el.removeAttribute('data-kb'));
  const positive = all.filter(el => el.tabIndex > 0).map(el => el.outerHTML.slice(0, 80));
  const tabbable = all.filter(el => {
    if (el.disabled || el.tabIndex < 0 || el.closest('[inert]')) return false;
    if (el.type === 'hidden') return false;
    const cs = getComputedStyle(el);
    if (cs.visibility === 'hidden' || cs.display === 'none') return false;
    // checkVisibility() also excludes content inside a closed <details>, which
    // Chrome keeps out of the Tab order.
    if (el.checkVisibility && !el.checkVisibility({visibilityProperty: true})) return false;
    return el.getClientRects().length > 0;
  });
  tabbable.forEach((el, i) => el.setAttribute('data-kb', String(i)));
  return {count: tabbable.length, positive};
})()"""

PROBE_JS = r"""(() => {
  const el = document.activeElement;
  if (!el || el === document.body || el === document.documentElement)
    return {kb: null, tag: 'BODY', label: '', fv: false, ring: false, outline: false, visiblePts: 0, inMain: false,
            expanded: null, inNav: false, cls: '', type: '', href: '', id: ''};
  const r = el.getBoundingClientRect(), cs = getComputedStyle(el);
  const vw = innerWidth, vh = innerHeight;
  const label = (el.getAttribute('aria-label') || el.textContent || el.name || el.id || '').trim().replace(/\s+/g, ' ').slice(0, 40);
  const pts = [[.5, .5], [.1, .1], [.9, .1], [.1, .9], [.9, .9]].map(([fx, fy]) => [r.left + r.width * fx, r.top + r.height * fy]);
  const visiblePts = pts.filter(([x, y]) => {
    if (x < 0 || y < 0 || x >= vw || y >= vh) return false;
    const hit = document.elementFromPoint(x, y);
    if (!hit) return false;
    if (hit === el || el.contains(hit) || hit.contains(el)) return true;
    const lab = hit.closest('label');
    return !!(lab && (lab.htmlFor === el.id || lab.contains(el)));
  }).length;
  const outline = cs.outlineStyle !== 'none' && parseFloat(cs.outlineWidth) >= 2;
  const ring = outline || (cs.boxShadow && cs.boxShadow !== 'none');
  return {kb: el.getAttribute('data-kb'), tag: el.tagName, label, fv: el.matches(':focus-visible'), fw: el.matches(':focus-within'),
          ring, outline, visiblePts, inMain: !!el.closest('main'), expanded: el.getAttribute('aria-expanded'),
          inNav: !!el.closest('#site-nav'), cls: el.className || '', type: el.type || '',
          href: el.getAttribute('href') || '', id: el.id || ''};
})()"""


class Results:
    def __init__(self):
        self.lines: list[str] = []
        self.failed = 0

    def check(self, name: str, ok: bool, detail: str = "") -> None:
        self.lines.append(("PASS " if ok else "FAIL ") + name + ("" if ok or not detail else f" -- {detail}"))
        if not ok:
            self.failed += 1
        print(self.lines[-1], flush=True)


def walk_page(page: Page, base: str, path: str, width: int, res: Results) -> None:
    tag = f"{width}px {path}"
    page.goto(base + path)
    info = page.js(INDEX_JS)
    n = info["count"]
    res.check(f"{tag}: no positive tabindex", not info["positive"], "; ".join(info["positive"]))

    # 1. Skip link
    page.key("Tab")
    first = page.js(PROBE_JS)
    res.check(f"{tag}: first Tab is the skip link, on screen",
              "skip-link" in first["cls"] and first["visiblePts"] > 0, json.dumps(first)[:160])
    page.key("Enter")
    page.key("Tab")
    after = page.js(PROBE_JS)
    res.check(f"{tag}: skip link Enter+Tab lands inside <main>", after["inMain"], json.dumps(after)[:160])

    # 2-3. Full forward walk from a fresh load
    page.goto(base + path)
    page.js(INDEX_JS)
    seq, problems = [], []
    for _ in range(n + 6):
        page.key("Tab")
        p = page.js(PROBE_JS)
        if p["kb"] is None:
            if p["tag"] == "BODY" and seq:
                break             # focus left the document: the walk is complete
            problems.append(f"focused untracked {p['tag']} '{p.get('label', '')}'")
            continue
        k = int(p["kb"])
        inner = bool(seq) and k == seq[-1] and p["tag"] in ("VIDEO", "AUDIO")
        if seq and k == seq[0]:
            break                 # wrapped around to the start
        if not inner:             # inner = next native player control (volume, full screen...) in the same element
            seq.append(k)
        what = f"#{k} {p['tag']} '{p['label']}'" + (" (player control)" if inner else "")
        if not (p["fv"] or (inner and p["fw"])):
            problems.append(f"{what}: :focus-visible not matched")
        if not p["ring"]:
            problems.append(f"{what}: no outline/box-shadow")
        if p["visiblePts"] == 0:
            problems.append(f"{what}: off-screen or fully covered when focused")
    expected = list(range(n))
    res.check(f"{tag}: Tab visits all {n} focusable elements in reading order, no trap",
              seq == expected, f"got {seq[:12]}... len {len(seq)} vs {n}")
    res.check(f"{tag}: every stop shows a visible, unobscured focus ring", not problems, "; ".join(problems[:4]))

    # 4. Shift+Tab goes backwards. Start from the last element (placed there by
    #    script, because where focus sits after leaving the page varies), then
    #    use real Shift+Tab presses.
    if seq == expected and n >= 3:
        page.js(f"document.querySelector('[data-kb=\"{n - 1}\"]').focus()")
        back = []
        for _ in range(2):
            page.key("Tab", shift=True)
            p = page.js(PROBE_JS)
            back.append(int(p["kb"]) if p["kb"] is not None else None)
        res.check(f"{tag}: Shift+Tab walks backwards", back == [n - 2, n - 3], f"got {back}")


def phone_menu(page: Page, base: str, res: Results) -> None:
    page.goto(base + "/index.html")
    page.js(INDEX_JS)
    for _ in range(40):
        page.key("Tab")
        p = page.js(PROBE_JS)
        if "nav-toggle" in p["cls"]:
            break
    res.check("390px menu: Tab reaches the Menu button", "nav-toggle" in p["cls"], json.dumps(p)[:120])
    page.key("Enter")
    p = page.js(PROBE_JS)
    res.check("390px menu: Enter opens it (aria-expanded=true)", p["expanded"] == "true", json.dumps(p)[:120])
    page.key("Tab")
    p = page.js(PROBE_JS)
    res.check("390px menu: next Tab enters the menu links", p["inNav"] and p["fv"], json.dumps(p)[:120])
    page.key("Escape")
    p = page.js(PROBE_JS)
    res.check("390px menu: Escape closes it and returns focus to Menu",
              "nav-toggle" in p["cls"] and p["expanded"] == "false", json.dumps(p)[:120])


def contact_errors(page: Page, base: str, width: int, res: Results) -> None:
    tag = f"{width}px contact form"
    page.goto(base + "/contact.html")
    page.js(INDEX_JS)
    for _ in range(80):
        page.key("Tab")
        p = page.js(PROBE_JS)
        if p["tag"] == "BUTTON" and p["type"] == "submit":
            break
    res.check(f"{tag}: Tab reaches the submit button", p["type"] == "submit", json.dumps(p)[:120])
    page.key("Enter")
    state = page.js("(() => { const s = document.querySelector('.error-summary');"
                    " return {shown: s && !s.hidden, focused: document.activeElement === s,"
                    " url: location.pathname}; })()")
    res.check(f"{tag}: Enter on empty form shows the error summary and focuses it",
              state["shown"] and state["focused"] and state["url"] == "/contact.html", json.dumps(state))
    page.key("Tab")
    p = page.js(PROBE_JS)
    target = p["href"].lstrip("#")
    res.check(f"{tag}: Tab from the summary reaches the first error link",
              p["tag"] == "A" and p["href"].startswith("#"), json.dumps(p)[:120])
    page.key("Enter")
    p = page.js(PROBE_JS)
    res.check(f"{tag}: Enter on the error link focuses that field", bool(target) and p["id"] == target,
              f"expected #{target}, got {json.dumps(p)[:120]}")


class EnvironmentFailure(Exception):
    """The browser could not be started or driven; never reported as a pass."""


@contextlib.contextmanager
def chrome_session(browser: str, prefix: str = "innovex-cdp-"):
    """Serve the repo on a free port, start headless Chrome with DevTools and
    yield (page, base_url); tear everything down afterwards. Also used by
    tools/run_axe_check.py."""

    class Quiet(http.server.SimpleHTTPRequestHandler):
        def log_message(self, *args):
            pass

    class QuietServer(http.server.ThreadingHTTPServer):
        def handle_error(self, request, client_address):
            pass  # Chrome dropping keep-alive connections at exit is not a test result

    server = QuietServer(("127.0.0.1", 0), functools.partial(Quiet, directory=str(ROOT)))
    threading.Thread(target=server.serve_forever, daemon=True).start()
    profile = tempfile.mkdtemp(prefix=prefix)
    proc = None
    try:
        try:
            proc = subprocess.Popen([browser, "--headless=new", "--disable-gpu", "--no-first-run",
                                     "--no-default-browser-check", f"--user-data-dir={profile}",
                                     "--remote-debugging-port=0", "about:blank"],
                                    stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)
            port_file = Path(profile) / "DevToolsActivePort"
            for _ in range(150):
                if port_file.exists() and port_file.read_text().strip():
                    break
                time.sleep(0.1)
            port = int(port_file.read_text().split()[0])
            targets = json.load(urllib.request.urlopen(f"http://127.0.0.1:{port}/json/list", timeout=10))
            ws_url = next(t["webSocketDebuggerUrl"] for t in targets if t.get("type") == "page")
            page = Page(ws_url)
            page.call("Page.enable")
            page.call("Network.enable")
            page.call("Network.setBlockedURLs", urls=["*formsubmit.co*"])  # safety: never send a form
        except Exception as exc:
            err = proc.stderr.read().decode(errors="replace")[-1500:] if proc and proc.poll() is not None else ""
            raise EnvironmentFailure(f"{exc!r}\n  browser: {browser}\n  {err}") from exc
        yield page, f"http://127.0.0.1:{server.server_address[1]}"
    finally:
        if proc:
            proc.kill()
            proc.wait()
        server.shutdown()
        shutil.rmtree(profile, ignore_errors=True)


def set_width(page: Page, width: int, height: int) -> None:
    page.call("Emulation.setDeviceMetricsOverride", width=width, height=height,
              deviceScaleFactor=1, mobile=width < 600)


def forced_colors(page: Page, base: str, res: Results) -> None:
    page.call("Emulation.setEmulatedMedia", features=[{"name": "forced-colors", "value": "active"}])
    try:
        for path in ("/index.html", "/contact.html"):
            page.goto(base + path)
            if path == "/index.html":   # prove the emulation is really on, or the check means nothing
                res.check("forced colours emulation is active",
                          page.js("matchMedia('(forced-colors: active)').matches") is True)
            n = page.js(INDEX_JS)["count"]
            missing = []
            for _ in range(n):
                page.key("Tab")
                p = page.js(PROBE_JS)
                if p["kb"] is not None and not p["outline"]:
                    missing.append(f"#{p['kb']} {p['tag']} '{p['label']}'")
            res.check(f"forced colours 1366px {path}: every stop draws a >=2px outline",
                      not missing, "; ".join(missing[:4]))
    finally:
        page.call("Emulation.setEmulatedMedia", features=[])


def main(argv: list[str]) -> int:
    browser = find_browser(argv)
    res = Results()
    fixtures = build_fixtures()
    try:
        with chrome_session(browser, "innovex-kb-") as (page, base):
            for width, height in WIDTHS:
                set_width(page, width, height)
                for path in PAGES:
                    walk_page(page, base, path, width, res)
                walk_page(page, base, "/tests/fixture_portal.html", width, res)
                contact_errors(page, base, width, res)
                if width < 600:
                    phone_menu(page, base, res)
            set_width(page, 1366, 900)
            forced_colors(page, base, res)
    except EnvironmentFailure as exc:
        print(f"ENVIRONMENT FAILURE: could not start or drive the browser: {exc}")
        return 2
    except Exception as exc:  # browser died mid-run, or a checker bug: never a pass
        print(f"ERROR: run aborted after {len(res.lines)} checks ({exc!r}). Not a test result.")
        return 2
    finally:
        for f in fixtures:
            f.unlink(missing_ok=True)

    total = len(res.lines)
    print(f"SUMMARY: {'PASS' if not res.failed else 'FAIL'} ({total - res.failed}/{total})")
    return 0 if not res.failed else 1


if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(errors="replace")
    sys.exit(main(sys.argv[1:]))
