# Measurement (business-only)

Goal: know which links and panels produce **delivered inquiries**, **booked meetings** and **first
orders**, without tracking visitors.

## What the site records

| Signal | How | Where it shows up |
|---|---|---|
| Panel of interest | Form field `panel_interest`, preselected by `contact.html?panel=<id>` | Inquiry email |
| Link / campaign source | `?src=<code>` on any page → kept for that browser tab → hidden field `lead_source` (default `website`) | Inquiry email |
| Meeting preference | Form field `meeting_preference` | Inquiry email |

That's all. No cookies, no third-party analytics, no tracking pixels, and nothing about form
*contents* goes anywhere except the inquiry email itself. `site.js` (`initLeadSource`) accepts only
`[a-z0-9-]`, up to 40 characters. Anything else is ignored.

**Never** put personal or patient information in a `src` code, such as names or facility names tied
to a person. Use neutral codes.

## Link format for the team

```
https://www.innovexlab.com/<page>?src=<code>#<section>
https://www.innovexlab.com/contact.html?panel=<panel-id>&src=<code>#book
```

Panel ids: `uti`, `wound`, `respiratory`, `gi`, `nail`, `womens-health`, `sti`, `resistance`.

Code convention: `<channel>-<panel>-<yyyymm>`, for example `flyer-wound-202612`, `email-resp-202612`,
`visit-uti-202612`, `qr-gi-202612`. Keep the list of codes in use, and what each one was handed out
on, in the private project docs.

Examples:

- Wound leave-behind with QR code: `https://www.innovexlab.com/testing.html?src=qr-wound-202612#wound`
- Follow-up email straight to booking: `https://www.innovexlab.com/contact.html?panel=respiratory&src=email-resp-202612#book`

## Funnel to track, kept outside the site

Record these by hand or in the CRM from the inquiry emails. Never put them in this repository:

1. Inquiries delivered: emails received, by `lead_source` and `panel_interest`
2. Meetings held
3. Setups signed
4. First order received

Clicks or page views alone don't count as results.

## If page analytics are added later

This needs an owner decision recorded in the private decision register. Use cookieless, aggregate-
only analytics. Don't record form fields or query strings other than `src` and `panel`. Update the
privacy line on the Contact page in the same pull request.
