#!/usr/bin/env python3
"""Browser security check: the Content-Security-Policy, injection resistance and the
form's outbound request, in headless Chrome. Nothing ever leaves this computer.

Usage (from the repo root)::

    python tools/run_security_check.py [--browser "C:/path/to/chrome.exe"]

Safety
    Every request the page makes is paused by Chrome (DevTools "Fetch" domain).
    Requests to the local test server continue; ANY other request is answered
    locally or failed, and is never sent: the form's POST to formsubmit.co is
    recorded and answered with a fake redirect. As a second layer, formsubmit.co
    is also on Chrome's blocked-URL list. No email can be sent by this script.

What it checks (docs/SECURITY.md)
    A. Every page: the policy <meta> is present, the page loads with ZERO policy
       violations, the hashed inline <head> script and site.js both run, the
       stylesheet applies, and the page makes no third-party requests at all.
    B. The policy is really enforced (positive controls, so a pass means
       something): an injected inline script does not run; an injected
       third-party image, inline style and third-party script are blocked.
    C. Injection: ?panel=, ?src=, the #fragment and a poisoned sessionStorage
       value carrying HTML/script payloads change nothing (no script runs, no
       element or attribute is created, the hidden lead_source stays clean);
       valid values still work (control).
    D. Portal switch: a dummy https portal is revealed with target=_blank and
       rel=noopener and causes no violation; a javascript: URL stays hidden.
    E. Form: a valid submit produces exactly one POST to the FormSubmit address,
       with the expected fields and only the site's origin as Referer; the
       (fake) redirect back to /thankyou.html is allowed by form-action. A
       redirect to another site, and a form whose action was changed to another
       site, are blocked by form-action.

Exit codes: 0 all pass, 1 a check failed, 2 environment problem (never a pass).
"""
from __future__ import annotations

import json
import sys
import time
from pathlib import Path
from urllib.parse import parse_qs, urlparse

sys.path.insert(0, str(Path(__file__).resolve().parent))
from check_site import FORM_ACTION  # noqa: E402
from run_browser_smoke import build_fixtures, find_browser  # noqa: E402
from run_keyboard_check import PAGES, EnvironmentFailure, Results, chrome_session, set_width  # noqa: E402

# Recorded in every new document before any page script runs (DevTools-injected
# code is exempt from the page's CSP; what it creates is not).
COLLECT_JS = r"""window.__cspv = [];
document.addEventListener('securitypolicyviolation',
  e => window.__cspv.push(e.effectiveDirective + ' ' + (e.blockedURI || '')));"""

PAYLOADS = [
    '"><img src=x onerror="window.__xss=1">',
    "uti'><svg onload=window.__xss=1>",
    "</script><script>window.__xss=1</script>",
    "javascript:window.__xss=1",
]

STATE_JS = r"""(() => ({
  path: location.pathname,
  cspv: window.__cspv || [],
  xss: window.__xss === 1,
  handlers: Array.from(document.querySelectorAll('*')).filter(el =>
              Array.from(el.attributes).some(a => /^on/i.test(a.name))).length,
  injected: document.querySelectorAll('svg, iframe, object, embed, img[src="x"]').length,
  lead: (document.getElementById('lead-source') || {}).value,
  panel: (document.getElementById('panel') || {}).value,
  js: document.documentElement.classList.contains('js'),
  ready: window.INNOVEX_READY === true,
  hasSiteJs: !!document.querySelector('script[src$="/site.js"]'),
  csp: !!document.querySelector('meta[http-equiv="Content-Security-Policy"]'),
  css: document.styleSheets.length > 0 && document.styleSheets[0].cssRules.length > 10,
}))()"""


class Guard:
    """Answers every paused request. Local requests continue; nothing else leaves."""

    def __init__(self, page, base: str):
        self.page, self.base = page, base
        self.form_posts: list[dict] = []
        self.external: list[str] = []
        self.redirect_to = base + "/thankyou.html"
        self.loaded = False

    def handle(self, event: dict) -> None:
        method, params = event.get("method"), event.get("params", {})
        if method == "Page.loadEventFired":
            self.loaded = True
        if method != "Fetch.requestPaused":
            return
        rid, req = params["requestId"], params["request"]
        url = req["url"]
        if url.startswith(self.base + "/"):
            self.page.call("Fetch.continueRequest", requestId=rid)
        elif urlparse(url).hostname == "formsubmit.co":
            self.form_posts.append(req)        # recorded, answered locally, never sent
            self.page.call("Fetch.fulfillRequest", requestId=rid, responseCode=303,
                           responseHeaders=[{"name": "Location", "value": self.redirect_to}], body="")
        else:
            self.external.append(url)
            self.page.call("Fetch.failRequest", requestId=rid, errorReason="BlockedByClient")

    def pump(self, seconds: float, until=lambda: False) -> None:
        end = time.time() + seconds
        while time.time() < end and not until():
            self.page.call("Browser.getVersion")      # reads (and buffers) pending events
            events, self.page.events[:] = list(self.page.events), []
            for e in events:
                self.handle(e)
            time.sleep(0.03)

    def load(self, url: str) -> dict:
        self.loaded = False
        # Not page.call(): Page.navigate only answers once its (paused) request is handled,
        # so send it and let pump() answer the requests; its reply is ignored.
        self.page.next_id += 1
        self.page.ws.send(json.dumps({"id": self.page.next_id, "method": "Page.navigate",
                                      "params": {"url": url}}))
        self.pump(20, lambda: self.loaded)
        if not self.loaded:
            raise RuntimeError(f"page did not load: {url}")
        self.pump(0.3)
        return self.page.js(STATE_JS)


def check_pages(g: Guard, res: Results) -> None:
    for path in PAGES:
        g.external.clear()
        s = g.load(g.base + path)
        res.check(f"{path}: policy present, 0 violations, no third-party requests",
                  s["csp"] and not s["cspv"] and not g.external, f"{s['cspv'][:3]} {g.external[:3]}")
        scripts_ok = s["js"] and s["ready"] if s["hasSiteJs"] else True
        res.check(f"{path}: inline head script + site.js run, stylesheet applies", scripts_ok and s["css"],
                  f"js={s['js']} ready={s['ready']} css={s['css']}")


def check_enforced(g: Guard, res: Results) -> None:
    g.load(g.base + "/index.html")
    g.external.clear()
    g.page.js(r"""(() => {
      const s = document.createElement('script'); s.textContent = 'window.__inl = 1'; document.head.appendChild(s);
      const i = document.createElement('img'); i.src = 'https://tracker.example.test/p.gif'; document.body.appendChild(i);
      const e = document.createElement('script'); e.src = 'https://cdn.example.test/x.js'; document.head.appendChild(e);
      document.body.setAttribute('style', 'outline: 9px solid red');
      return true; })()""")
    g.pump(1.0)
    s = g.page.js("({inl: window.__inl === 1, cspv: window.__cspv, outline: getComputedStyle(document.body).outlineWidth})")
    v = " | ".join(s["cspv"])
    res.check("control: injected inline script is blocked", not s["inl"] and "script-src-elem inline" in v, v)
    res.check("control: third-party image and script are blocked before any request",
              "img-src https://tracker.example.test" in v and "script-src-elem https://cdn.example.test" in v
              and not g.external, f"{v} {g.external}")
    res.check("control: inline style attribute is blocked", s["outline"] != "9px" and "style-src-attr" in v, v)


def check_injection(g: Guard, res: Results) -> None:
    for p in PAYLOADS:
        s = g.load(f"{g.base}/contact.html?panel={_enc(p)}&src={_enc(p)}#{_enc(p)}")
        res.check(f"payload {p[:28]!r}: no script, element, handler or violation; lead_source clean",
                  not s["xss"] and not s["cspv"] and s["handlers"] == 0 and s["injected"] == 0
                  and s["lead"] == "website" and s["panel"] == "",
                  json.dumps({k: s[k] for k in ("xss", "cspv", "handlers", "injected", "lead", "panel")}))
    g.page.js("sessionStorage.setItem('innovex_src', '\"><img src=x onerror=window.__xss=1>'), true")
    s = g.load(g.base + "/contact.html")
    res.check("poisoned sessionStorage code is ignored", not s["xss"] and s["lead"] == "website" and s["injected"] == 0,
              f"lead={s['lead']!r}")
    g.page.js("sessionStorage.clear(), true")
    s = g.load(g.base + "/contact.html?panel=UTI&src=Flyer-UTI")
    res.check("control: valid ?panel= and ?src= still work", s["panel"] == "uti" and s["lead"] == "flyer-uti",
              f"panel={s['panel']!r} lead={s['lead']!r}")
    g.page.js("sessionStorage.clear(), true")


def _enc(text: str) -> str:
    from urllib.parse import quote
    return quote(text, safe="")


def check_portal(g: Guard, res: Results) -> None:
    g.load(g.base + "/tests/fixture_portal.html")
    s = g.page.js(r"""(() => ({cspv: window.__cspv, links: Array.from(document.querySelectorAll('[data-portal-link]'))
      .map(a => ({hidden: a.hidden, href: a.getAttribute('href'), target: a.target, rel: a.rel}))}))()""")
    ok = s["links"] and all(not l["hidden"] and l["href"] == "https://portal.example.test/login"
                            and l["target"] == "_blank" and "noopener" in l["rel"] for l in s["links"])
    res.check("portal on: links revealed with target=_blank rel=noopener, 0 violations", bool(ok) and not s["cspv"],
              json.dumps(s)[:200])
    g.load(g.base + "/tests/fixture_portal_bad.html")
    s = g.page.js("Array.from(document.querySelectorAll('[data-portal-link]')).map(a => [a.hidden, a.getAttribute('href')])")
    res.check("portal javascript: URL stays hidden with no href", all(h and href is None for h, href in s), str(s))


FILL_JS = r"""(() => {
  const f = document.querySelector('form[data-validate]');
  const set = (id, v) => { document.getElementById(id).value = v; };
  set('name', 'Automated security check (never sent)'); set('organization', 'Test');
  set('email', 'test@example.com'); set('role', 'Other'); set('panel', 'not-sure'); set('meeting', 'No preference');
  %s
  f.querySelector('button[type=submit]').click();
  return true; })()"""


def check_form(g: Guard, res: Results) -> None:
    g.form_posts.clear(); g.external.clear()
    g.redirect_to = g.base + "/thankyou.html"
    g.load(g.base + "/contact.html?src=sec-test")
    g.page.js(FILL_JS % "")
    g.pump(8, lambda: g.loaded and g.form_posts)
    g.pump(1.5)
    s = g.page.js(STATE_JS)
    post = g.form_posts[0] if g.form_posts else {}
    fields = parse_qs(post.get("postData", ""), keep_blank_values=True)
    referer = {k.lower(): v for k, v in post.get("headers", {}).items()}.get("referer")
    res.check("form: exactly one POST, to the FormSubmit address (answered locally, not sent)",
              len(g.form_posts) == 1 and post.get("method") == "POST" and post.get("url") == FORM_ACTION,
              f"{len(g.form_posts)} {post.get('method')} {post.get('url')}")
    res.check("form: carries lead_source, empty _honey, reply-to email, no extra fields",
              fields.get("lead_source") == ["sec-test"] and fields.get("_honey") == [""]
              and fields.get("email") == ["test@example.com"]
              and set(fields) <= {"_subject", "_template", "_next", "lead_source", "_honey", "name", "role",
                                  "organization", "email", "phone", "panel_interest", "meeting_preference",
                                  "preferred_times", "message"}, str(sorted(fields)))
    res.check("form: Referer sent to FormSubmit is the site's origin only (no path or ?src=)",
              referer == g.base + "/", repr(referer))
    res.check("form: redirect back to /thankyou.html is allowed by form-action, 0 violations",
              s["path"] == "/thankyou.html" and not s["cspv"] and not g.external, f"{s['path']} {s['cspv']}")

    # Negative 1: the form service redirects somewhere else -> form-action blocks it.
    g.form_posts.clear(); g.external.clear()
    g.redirect_to = "https://elsewhere.example.test/landing"
    g.load(g.base + "/contact.html")
    g.page.js(FILL_JS % "")
    g.pump(5, lambda: bool(g.form_posts))
    g.pump(1.5)
    res.check("control: a redirect to another site after submit is blocked (form-action)",
              len(g.form_posts) == 1 and not g.external, f"posts={len(g.form_posts)} external={g.external}")

    # Negative 2: the form's action is changed to another site -> blocked before any request.
    g.form_posts.clear(); g.external.clear()
    g.redirect_to = g.base + "/thankyou.html"
    g.load(g.base + "/contact.html")
    g.page.js(FILL_JS % "f.setAttribute('action', 'https://collector.example.test/steal');")
    g.pump(3)
    s = g.page.js("({path: location.pathname, cspv: window.__cspv})")
    res.check("control: a form re-pointed at another site is blocked by form-action, nothing requested",
              s["path"] == "/contact.html" and any(v.startswith("form-action") for v in s["cspv"])
              and not g.external and not g.form_posts, json.dumps(s))


def main(argv: list[str]) -> int:
    browser = find_browser(argv)
    res = Results()
    fixtures = build_fixtures()
    try:
        with chrome_session(browser, "innovex-sec-") as (page, base):
            set_width(page, 1366, 900)
            page.call("Page.addScriptToEvaluateOnNewDocument", source=COLLECT_JS)
            page.call("Fetch.enable", patterns=[{"urlPattern": "*", "requestStage": "Request"}])
            g = Guard(page, base)
            check_pages(g, res)
            check_enforced(g, res)
            check_injection(g, res)
            check_portal(g, res)
            check_form(g, res)
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
