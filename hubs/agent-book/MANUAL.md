# agent-book — Manual

## 1. Identity
- **Name:** agent-book
- **Type:** Cloudflare Pages (static, public — NO CF Access)
- **Domain:** `agents.insuranceinformatics.com` (custom) / `agent-book-XXX.pages.dev` (pages.dev)
- **Purpose:** Public per-servicing-agent follow-up dashboard. SA-001/SA-002/SA-003 see the list of companies Insurance Informatics emailed on their behalf today, with contact info + CSV download for phone follow-ups.

## 2. Contract (I / M / O)
- **Input:** HTTPS GET with `?agent=SA-001` (or SA-002, SA-003) query param.
- **Middle:** Static HTML loads, JS reads `?agent=`, fetches `https://mission-control-api.svg-outreach.workers.dev/public/agents/{code}/sends?since={today 00:00 UTC}` with NO auth header. Renders sortable/filterable table. Refresh button re-fetches. Download CSV button exports filtered+sorted view (18 columns).
- **Output:** 200 OK `text/html`. Rendered table of today's sends. CSV file download (`SA-001-sends-2026-04-24.csv` format).

## 3. Boundary
- **Public.** No CF Access gate. Anyone with the URL can view.
- **Safe to publish** — data is companies-we-already-emailed, not strategic. No internal system access, no account data, no secrets.
- **Whitelist enforced server-side** — the `/public/agents/:code/sends` API route only accepts codes in `PUBLIC_AGENT_WHITELIST` (SA-001, SA-002, SA-003). Any other code → 403.
- Phone tracking: none. No click tracking on the page itself. Mailgun webhooks fire independently for each email and update `lcs_event` → shows as delivery status changes in the table on next refresh.

## 4. Deploy
```bash
cd workers/agent-book
npx wrangler pages deploy dist --project-name agent-book
```
First-time setup:
```bash
npx wrangler pages project create agent-book --production-branch main
```
Custom domain attach (via CF API using wrangler OAuth token):
```bash
OAUTH=$(grep -E "^oauth_token" ~/AppData/Roaming/xdg.config/.wrangler/config/default.toml | cut -d'"' -f2)
curl -s -X POST -H "Authorization: Bearer $OAUTH" -H "Content-Type: application/json" \
  -d '{"name":"agents.insuranceinformatics.com"}' \
  "https://api.cloudflare.com/client/v4/accounts/a1dd98c646e8d2f4ae6f1ca6c0b79653/pages/projects/agent-book/domains"
```
Then add CNAME in dashboard (no token has DNS-edit): DNS → `insuranceinformatics.com` → Add record → CNAME `agents` → `agent-book-XXX.pages.dev` → Proxied.

## 5. Dependencies
- **mission-control-api** at `https://mission-control-api.svg-outreach.workers.dev`
  - Public route: `GET /public/agents/:agent_code/sends?since={ISO}` (no auth, whitelist)
  - Added 2026-04-24 — BAR-803
- **NOT** behind CF Access. The `/public/agents/*` path is explicitly exempted in the global auth middleware.

## 6. Governance
- `ctb_node`: `barton-enterprises.svg-agency.outreach.delivery.agent-book`
- `CC` layer: CC-03 (fleet)
- Status: BUILD (first deploy 2026-04-24)
- Owner: Dave Barton

## 7. Change Log
- 2026-04-24 — initial build (BAR-803)
