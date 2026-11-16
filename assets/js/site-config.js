/* ==========================================================================
   InnovexLab — site configuration (single source of truth)
   --------------------------------------------------------------------------
   Values here change site behavior on EVERY page without editing HTML.
   Loaded before assets/js/site.js on each page.

   CLIENT PORTAL
   - Leave portalUrl as an empty string until the portal owner has confirmed
     the exact HTTPS login address AND it has been tested with a permitted
     test account (task W04). While it is empty, every "Client Portal" link
     stays hidden — we never publish a guessed or placeholder URL.
   - When verified, paste the full address, e.g. "https://portal.example.com/login",
     run `python tools/check_site.py`, preview, then record the change in
     the internal decision register.
   - Must start with https:// or site.js will refuse to show it.
   ========================================================================== */
window.INNOVEX_CONFIG = {
  portalUrl: "",

  // Shown on the Client Portal link for screen readers when it opens another site.
  portalExternalLabel: "(opens the client portal in a new tab)"
};
