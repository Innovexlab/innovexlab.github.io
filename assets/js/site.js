/* ==========================================================================
   InnovexLab — site behavior
   --------------------------------------------------------------------------
   Plain JavaScript, no libraries, no build step. Every feature here is a
   progressive enhancement: the site still works with JavaScript off
   (navigation is visible, the form uses the browser's own validation).

   Features (each is a small function, called at the bottom):
     1. initMobileNav()       — "Menu" button that opens/closes the nav on phones
     2. initPortalLinks()     — reveals Client Portal links only if a verified URL is configured
     3. initFooterYear()      — keeps the © year current
     4. initPanelPreselect()  — contact.html?panel=uti preselects the panel field
     5. initFormValidation()  — accessible inline errors on the meeting form
     6. initLeadSource()      — copies a ?src= campaign code into the form (business-only measurement)
   ========================================================================== */
(function () {
  "use strict";

  var config = window.INNOVEX_CONFIG || {};

  /* 1. Mobile navigation ------------------------------------------------- */
  function initMobileNav() {
    var toggle = document.querySelector(".nav-toggle");
    var nav = document.getElementById("site-nav");
    if (!toggle || !nav) return;

    function setOpen(open) {
      nav.classList.toggle("is-open", open);
      toggle.setAttribute("aria-expanded", String(open));
    }

    toggle.addEventListener("click", function () {
      setOpen(toggle.getAttribute("aria-expanded") !== "true");
    });

    // Close after choosing a link (matters for same-page #anchors).
    nav.addEventListener("click", function (event) {
      if (event.target.closest("a")) setOpen(false);
    });

    // Escape closes the menu and returns focus to the button (keyboard users).
    document.addEventListener("keydown", function (event) {
      if (event.key === "Escape" && nav.classList.contains("is-open")) {
        setOpen(false);
        toggle.focus();
      }
    });
  }

  /* 2. Client Portal links ---------------------------------------------- */
  // Every element with [data-portal-link] starts with the `hidden` attribute.
  // We only reveal them when site-config.js holds a verified https:// URL.
  function initPortalLinks() {
    var url = (config.portalUrl || "").trim();
    if (!/^https:\/\//i.test(url)) return; // empty or not HTTPS → keep hidden

    var links = document.querySelectorAll("[data-portal-link]");
    Array.prototype.forEach.call(links, function (link) {
      link.setAttribute("href", url);
      link.setAttribute("target", "_blank");
      link.setAttribute("rel", "noopener");
      if (config.portalExternalLabel && !link.querySelector(".visually-hidden")) {
        var sr = document.createElement("span");
        sr.className = "visually-hidden";
        sr.textContent = " " + config.portalExternalLabel;
        link.appendChild(sr);
      }
      link.hidden = false;
      // A wrapper (e.g. a footer <li> or a contact-page card) may also be hidden.
      var wrapper = link.closest("[data-portal-wrapper]");
      if (wrapper) wrapper.hidden = false;
    });

    // Elements shown only while there is NO portal link (e.g. "call us for access").
    var fallbacks = document.querySelectorAll("[data-portal-fallback]");
    Array.prototype.forEach.call(fallbacks, function (el) { el.hidden = true; });
  }

  /* 3. Footer year -------------------------------------------------------- */
  function initFooterYear() {
    var year = document.querySelectorAll("[data-year]");
    Array.prototype.forEach.call(year, function (el) {
      el.textContent = String(new Date().getFullYear());
    });
  }

  /* 4. Panel preselect ---------------------------------------------------- */
  // Testing-page buttons link to contact.html?panel=<value>#book so the
  // visitor doesn't have to choose the panel again.
  function initPanelPreselect() {
    var select = document.getElementById("panel");
    if (!select || !window.URLSearchParams) return;
    var wanted = new URLSearchParams(window.location.search).get("panel");
    if (!wanted) return;
    Array.prototype.forEach.call(select.options, function (option) {
      if (option.value.toLowerCase() === wanted.toLowerCase()) option.selected = true;
    });
  }

  /* 5. Form validation --------------------------------------------------- */
  // Rules come from the HTML itself (required, type="email", pattern), so
  // the markup stays the single source of truth. On a failed submit we:
  //   - mark each bad field aria-invalid and fill its .field-error message,
  //   - show an error summary with links to each field and move focus to it.
  function initFormValidation() {
    var form = document.querySelector("form[data-validate]");
    if (!form) return;

    form.setAttribute("novalidate", ""); // we take over from native bubbles

    // If the visitor comes back with the browser's Back button, the page may be
    // restored from cache with the button still saying "Sending…". Reset it.
    window.addEventListener("pageshow", function () {
      var button = form.querySelector("button[type=submit]");
      if (button && button.disabled) {
        button.disabled = false;
        button.textContent = button.getAttribute("data-label-default") || "Request my panel review";
      }
    });
    var summary = form.querySelector(".error-summary");
    var summaryList = summary ? summary.querySelector("ul") : null;

    // Human-readable message for one field, or "" when the field is valid.
    function messageFor(field) {
      var label = field.getAttribute("data-label") || field.name;
      var value = (field.value || "").trim();
      if (field.required && !value) {
        return field.tagName === "SELECT" ? "Choose your " + label + "." : "Enter your " + label + ".";
      }
      if (value && field.type === "email" && !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(value)) {
        return "Enter an email address like name@practice.com.";
      }
      if (value && field.type === "tel" && value.replace(/\D/g, "").length < 10) {
        return "Enter a full phone number, including area code, or leave it blank.";
      }
      return "";
    }

    function showFieldError(field, message) {
      var error = document.getElementById(field.id + "-error");
      if (message) field.setAttribute("aria-invalid", "true");
      else field.removeAttribute("aria-invalid");
      if (error) error.textContent = message;
    }

    var fields = form.querySelectorAll("input[id], select[id], textarea[id]");

    // Re-check a field when the visitor leaves it, but only after a first
    // failed submit — avoids shouting errors while someone is still typing.
    var attempted = false;
    Array.prototype.forEach.call(fields, function (field) {
      field.addEventListener("blur", function () {
        if (attempted) showFieldError(field, messageFor(field));
      });
    });

    form.addEventListener("submit", function (event) {
      attempted = true;
      var problems = [];
      Array.prototype.forEach.call(fields, function (field) {
        if (field.closest(".hp-field")) return; // skip the spam honeypot
        var message = messageFor(field);
        showFieldError(field, message);
        if (message) problems.push({ id: field.id, message: message });
      });

      if (problems.length === 0) {
        if (summary) summary.hidden = true;
        var button = form.querySelector("button[type=submit]");
        if (button) { button.disabled = true; button.textContent = "Sending…"; }
        return; // let the browser submit to the form service
      }

      event.preventDefault();
      if (summary && summaryList) {
        summaryList.innerHTML = "";
        problems.forEach(function (p) {
          var li = document.createElement("li");
          var a = document.createElement("a");
          a.href = "#" + p.id;
          a.textContent = p.message;
          a.addEventListener("click", function (e) {
            e.preventDefault();
            document.getElementById(p.id).focus();
          });
          li.appendChild(a);
          summaryList.appendChild(li);
        });
        summary.hidden = false;
        summary.focus();
      }
    });
  }

  /* 6. Lead source (business-only measurement) ---------------------------- */
  // Links shared by the team can carry a short campaign code, e.g.
  //   https://www.innovexlab.com/testing.html?src=flyer-uti#uti
  // We keep ONLY that code (letters, digits, hyphens; max 40 chars) for this
  // browser tab, and copy it into the form's hidden "lead_source" field so the
  // inquiry email says which link it came from. No cookies, no third-party
  // analytics, no form contents, no personal data. See docs/MEASUREMENT.md.
  function initLeadSource() {
    var KEY = "innovex_src";
    var code = "";
    if (window.URLSearchParams) {
      var raw = new URLSearchParams(window.location.search).get("src") || "";
      if (/^[a-z0-9-]{1,40}$/i.test(raw)) code = raw.toLowerCase();
    }
    try {
      if (code) window.sessionStorage.setItem(KEY, code);
      else code = window.sessionStorage.getItem(KEY) || "";
    } catch (e) { /* storage blocked (private mode etc.): use the URL code only */ }
    var field = document.getElementById("lead-source");
    if (field && /^[a-z0-9-]{1,40}$/.test(code)) field.value = code;
  }

  /* 7. Copy link ---------------------------------------------------------- */
  // Buttons with data-copy-link="<url>" (hidden in HTML) appear only when the Clipboard API exists.
  // The page address is always shown as text, so visitors without JavaScript can copy it by hand.
  function initCopyLink() {
    if (!navigator.clipboard || !window.isSecureContext) return;
    var buttons = document.querySelectorAll("[data-copy-link]");
    Array.prototype.forEach.call(buttons, function (button) {
      var status = button.parentNode.querySelector(".share__status");
      button.hidden = false;
      button.addEventListener("click", function () {
        navigator.clipboard.writeText(button.getAttribute("data-copy-link")).then(function () {
          if (status) status.textContent = "Link copied. Paste it into a message to your clinician.";
        }, function () {
          if (status) status.textContent = "Copying didn't work here. Select the page address and copy it instead.";
        });
      });
    });
  }

  /* 8. Organism library filter -------------------------------------------- */
  // Shows the search box (hidden without JavaScript) and filters list items by their data-filter-text.
  function initListFilter() {
    var input = document.getElementById("organism-filter");
    if (!input) return;
    var label = document.querySelector("label[for=organism-filter]");
    var status = document.getElementById("filter-status");
    var groups = document.querySelectorAll("[data-filter-group]");
    input.hidden = false;
    if (label) label.hidden = false;
    input.addEventListener("input", function () {
      var q = input.value.trim().toLowerCase();
      var shown = 0;
      Array.prototype.forEach.call(groups, function (group) {
        var visible = 0;
        Array.prototype.forEach.call(group.querySelectorAll("[data-filter-text]"), function (item) {
          var match = !q || item.getAttribute("data-filter-text").indexOf(q) !== -1;
          item.hidden = !match;
          if (match) visible += 1;
        });
        group.hidden = visible === 0;
        shown += visible;
      });
      if (status) status.textContent = q ? shown + (shown === 1 ? " organism" : " organisms") + " found" : "";
    });
  }

  /* 9. Panel-aware organism pager ----------------------------------------- */
  // Organism pages opened from a panel page carry ?panel=<id>&list=<slug,slug,...> (the panel's targets in
  // order). Prev/next then step through that panel only, and the middle link returns to the panel. Every
  // value is validated: the panel id against a fixed list, slugs against a strict pattern and the page's
  // own list of known organisms. Without parameters the pager keeps the full-library order.
  function initPanelPager() {
    var pager = document.querySelector("[data-pager]");
    if (!pager || !window.URLSearchParams) return;
    var params = new URLSearchParams(window.location.search);
    var PANELS = { "uti": "UTI panel", "wound": "Wound panel", "respiratory": "Respiratory panel", "gi": "GI panel",
                   "sti": "STI panel", "womens-health": "Women's health panel", "nail": "Nail fungal panel",
                   "eye": "Eye infection panel", "resistance": "Resistance panel" };
    var panel = params.get("panel") || "";
    if (!Object.prototype.hasOwnProperty.call(PANELS, panel)) return;
    var titles;
    try { titles = JSON.parse(pager.getAttribute("data-titles") || "{}"); } catch (e) { return; }
    var list = (params.get("list") || "").split(",").filter(function (s) {
      return /^[a-z0-9-]{1,60}$/.test(s) && Object.prototype.hasOwnProperty.call(titles, s);
    });
    var match = window.location.pathname.match(/\/learn\/organisms\/([a-z0-9-]+)\.html$/);
    var current = match ? match[1] : "";
    var i = list.indexOf(current);
    if (i === -1) return;
    var query = "?panel=" + encodeURIComponent(panel) + "&list=" + list.join(",");

    function setLink(attr, slug, label) {
      var old = pager.querySelector("[" + attr + "]");
      if (!old) return;
      var el;
      if (slug) {
        el = document.createElement("a");
        el.setAttribute("href", "/learn/organisms/" + slug + ".html" + query);
        el.textContent = label;
      } else {
        el = document.createElement("span");
      }
      el.setAttribute(attr, "");
      old.parentNode.replaceChild(el, old);
    }
    setLink("data-pager-prev", list[i - 1], list[i - 1] ? "\u2190 " + titles[list[i - 1]] : "");
    setLink("data-pager-next", list[i + 1], list[i + 1] ? titles[list[i + 1]] + " \u2192" : "");
    var home = pager.querySelector("[data-pager-home]");
    if (home) {
      home.setAttribute("href", "/testing/panels/" + panel + ".html");
      home.textContent = "Back to " + PANELS[panel] + " (" + (i + 1) + " of " + list.length + ")";
    }
    pager.setAttribute("aria-label", PANELS[panel] + ": organism pages");
  }

  initMobileNav();
  initPortalLinks();
  initFooterYear();
  initPanelPreselect();
  initFormValidation();
  initLeadSource();
  initCopyLink();
  initListFilter();
  initPanelPager();

  // Tells the inline <head> script that enhancements loaded (see the fail-safe there).
  window.INNOVEX_READY = true;
})();
