# CF Video Hosting — Reference (don't re-research this)

**What this answers:** where do videos (and the other NotebookLM artifacts) get hosted, what's the live URL, how does an MP4 get from "I made it" to "it's playing on a page", and where the source lives. Pinned 2026-05-12.

---

## The live site

| Field | Value |
|-------|-------|
| **Live URL** | `https://content-pages-8as.pages.dev/` |
| **CF Pages project name** | `content-pages` |
| **Current home page** | "Insurance Informatics — The Named Discipline" (SEO website) |
| **Hosting** | Cloudflare Pages (static — Vite/React build → `dist/`) |
| **Source repo** | `barton-outreach-core/hubs/content-pages/` ← **canonical.** (Stale copy at `imo-creator-v2-bar335/workers/content-pages/` — ignore. The memory line "Location: workers/content-pages/" is also stale — that path no longer exists in imo-creator-v2.) |
| **Manual** | `barton-outreach-core/hubs/content-pages/MANUAL.md` (UNIFIED_TEMPLATE worker doc — note: it still cites the old `workers/content-pages/` paths; treat those as `barton-outreach-core/hubs/content-pages/`). |

---

## Two kinds of pages on this site

1. **Website pages** (SEO-first, diagram-heavy) — `WebsitePage` objects in `src/pages/*.ts`, wired into `src/App.tsx` `websiteRoutes`. Current routes:
   `/` (home) · `/what-is-insurance-informatics` · `/how-it-works` · `/executives` · `/hr` · `/permanent` · `/vendors` · `/about` · `/book` · `/insurance-informatics` (alias → home).
   Each section (`PageSection`) can carry a video: `video?: { streamId: string; title: string }`.
2. **Content-viewer pages** (the "9-slot" template) — `ContentConfig` objects in `src/configs/*.ts`, wired into `src/App.tsx`. Current: `content5500`, `the-10-orchestrator`, `informatics-pipeline`, `insurance-informatics-vendor-briefing`, `deconstructing-the-duck`, `insurance-informatics-ctb`.
   9 slots: **video** (CF Stream iframe) · audio · slides · report · infographic · quiz · flashcards · mindmap · datatable.

Both contracts live in `src/types.ts` (`ContentConfig`, `WebsitePage`, `PageSection`). Brand options: `'svg' | 'weewee' | 'insuranceinformatics'`. Static artifacts (audio, slides, infographics, source markdown) live in `public/content/{topic}/`; `public/content/sources/` already holds the 6 video source docs (imo-creator-overview, svg-outreach-overview, svg-sales-{factfinder,insurance-education,cost-presentation,service}).

---

## How an MP4 gets onto a page (the constant — this is PROC-1800)

This is the spine that runs every time, regardless of what tool made the video (HeyGen / In Motion / NotebookLM / Higgsfield / whatever). Full procedure: `Barton-Processes/factory/content/1800-cf-stream-upload/PROCESS-UT.md` (note: that doc cites the old `workers/content-pages/App.tsx` path — it's now `barton-outreach-core/hubs/content-pages/src/App.tsx`).

1. **Upload the MP4 to Cloudflare Stream** — multipart form POST, `file` field:
   ```bash
   curl -s -X POST "https://api.cloudflare.com/client/v4/accounts/$CF_ACCOUNT/stream" \
     -H "Authorization: Bearer $CF_STREAM" -F "file=@/path/to/video.mp4"
   ```
   (`CF_ACCOUNT` = Cloudflare account ID; `CF_STREAM` = Stream API bearer token — both from Doppler.)
2. **Poll for ready** — `curl -s "https://api.cloudflare.com/client/v4/accounts/$CF_ACCOUNT/stream/{uid}" -H "Authorization: Bearer $CF_STREAM"` until `status.state == "ready"`. Record the **UID**.
3. **Wire the UID in** — set `streamId: "{uid}"` in the relevant config:
   - content-viewer page → the `video` field of a `ContentConfig` in `src/configs/{topic}.ts`
   - website page → the `video` field of a `PageSection` in `src/pages/{page}.ts`
4. **Build + deploy**:
   ```bash
   cd barton-outreach-core/hubs/content-pages
   npm run build      # = tsc && vite build  (a predeploy hook also runs gen-voice-spec.mjs)
   npm run deploy     # = wrangler pages deploy dist   (wrangler uses OAuth session, not an API key)
   ```
5. **Verify** — open `https://content-pages-8as.pages.dev/{route}` and confirm the player renders. The raw embed (for testing outside the page) is the CF Stream iframe: `https://customer-{subdomain}.cloudflarestream.com/{uid}/iframe`.

**CF Stream housekeeping:** list all uploaded videos → `curl -H "Authorization: Bearer $CF_STREAM" https://api.cloudflare.com/client/v4/accounts/$CF_ACCOUNT/stream`. Delete → `curl -X DELETE ".../stream/{uid}" -H "Authorization: Bearer $CF_STREAM"`. Dashboard: `https://dash.cloudflare.com/` → Stream.

---

## Quick map

```
make video (HeyGen / In Motion / NotebookLM / Higgsfield / …)
   → MP4
   → CF Stream upload (PROC-1800)         ← the constant; everything funnels here
   → streamId into a ContentConfig / PageSection
   → npm run build && npm run deploy       (barton-outreach-core/hubs/content-pages/)
   → live on https://content-pages-8as.pages.dev/{route}
```

The generators are variable fill. **CF Stream → content-pages → content-pages-8as.pages.dev is the constant.** That's why the heavy/documented part is this leg, not the per-tool lanes.
