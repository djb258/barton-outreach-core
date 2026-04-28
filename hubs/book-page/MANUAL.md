# book-page — Manual

## 1. Identity
- **Name:** book-page
- **Type:** Cloudflare Pages (static)
- **Domain:** `book.insuranceinformatics.com`
- **Purpose:** Branded wrapper around Google Appointment Scheduling iframe for cold-outreach calendar booking. Captures per-prospect view events via `?cid=` query param.

## 2. Contract (I / M / O)
- **Input:** HTTPS GET with optional `?cid={communication_id}` query param.
- **Middle:** Serve static `index.html`. On page load, JS reads `?cid=` and fires one `sendBeacon` (or fetch fallback) to `https://lcs-hub.svg-outreach.workers.dev/track/calendar-view?cid=...`. Page renders regardless of tracker success.
- **Output (Emitted):** 200 OK `text/html` with embedded Google Appointment Scheduling iframe.
- **Output (Retained):** `CALENDAR_VIEWED` event row in `svg-d1-spine.lcs_event` (via lcs-hub).

## 3. Boundary
- Static assets only — no server logic inside book-page itself.
- Click tracking is an **outbound, fire-and-forget** call into lcs-hub. book-page never fails if lcs-hub is down.
- `CALENDAR_BOOKED` (actual booking confirmation) is NOT captured by this page. That arrives via Gmail webhook on marketing@svg.agency when Google sends the booking-confirmed email. Tracked separately in BAR-800 inbox-agent.

## 4. Deploy
```bash
cd workers/book-page
npx wrangler pages deploy dist --project-name book-page
```
First-time setup:
```bash
npx wrangler pages project create book-page --production-branch main
```
**Pages.dev URL (live):** `https://book-page-3wa.pages.dev`

**Custom domain attach (2026-04-24):**
- Pages project domain registration: done via API (`pages/projects/book-page/domains`). Status = `initializing` until DNS CNAME points at the project.
- **DNS CNAME must be added manually** — none of the available CF tokens (wrangler OAuth, CF_API_TOKEN, GLOBAL_CLOUDFLARE_API_TOKEN) hold DNS-edit on zone `insuranceinformatics.com`.
- Dashboard path: Cloudflare → DNS → `insuranceinformatics.com` → Add record → Type `CNAME`, Name `book`, Target `book-page-3wa.pages.dev`, Proxy `ON`.
- Once CNAME propagates, `https://book.insuranceinformatics.com` serves this project and `status` flips to `active` automatically.

## 5. Dependencies
- Google Appointment Scheduling URL baked into iframe `src`. Update `dist/index.html` if Dave regenerates the booking page.
- `lcs-hub` worker route `/track/calendar-view` (added in a sibling dispatch). If that route doesn't exist yet, tracking silently fails — the page still works.

## 6. Governance
- `ctb_node`: `barton-enterprises.svg-agency.outreach.delivery.book-page`
- `CC` layer: CC-03 (fleet)
- Status: BUILD (not yet deployed)
- Owner: Dave Barton

## 7. Change Log
- 2026-04-24 — initial build (BAR-801)
