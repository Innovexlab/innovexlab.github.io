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

  initMobileNav();
  initPortalLinks();
  initFooterYear();
  initPanelPreselect();
  initFormValidation();
  initLeadSource();

  // Tells the inline <head> script that enhancements loaded (see the fail-safe there).
  window.INNOVEX_READY = true;
})();
