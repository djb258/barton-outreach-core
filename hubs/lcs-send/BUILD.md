# LCS Hub — Build Documentation

| Field | Value |
|-------|-------|
| **CTB Position** | BRANCH — the pipeline hub. All spokes connect here. |
| **Input** | Signals from dumb worker spokes in standard format. Webhooks from delivery platforms. |
| **Middle** | Gate stack → CID compile → SID design → MID deliver → webhook process. |
| **Output** | Delivered messages. Tracked campaigns. Enriched CID. Closed circle. |
| **Circle** | Signal → CID → SID → MID → webhook → engagement history → Monte Carlo → next SID smarter. |

| Field | Value |
|-------|-------|
| Location | `workers/lcs-hub/` |
| Built | 2026-03-23 |
| Status | BUILD — smoke test pending |
| ORBT | BUILD |
| Governing Engine | Foundational Bedrock (`law/doctrine/FOUNDATIONAL_BEDROCK.md`) |

---

## What Was Built

### File Structure

```
workers/lcs-hub/
├── BUILD.md                          ← This file (you are here)
├── wrangler.toml                     ← CF Worker config: cron, D1, Queues, secrets
├── package.json                      ← Dependencies + scripts
├── tsconfig.json                     ← TypeScript config
└── src/
    ├── index.ts                      ← Main entry: scheduled(), queue(), fetch()
    ├── types.ts                      ← All type definitions (standard interfaces)
    ├── utils.ts                      ← mintId(), logEvent(), logError(), isSuppressed(), suppress()
    ├── gates.ts                      ← 9-gate stack (the valves)
    ├── compiler.ts                   ← CID compile → SID design → MID deliver
    ├── spokes/
    │   ├── signal-intake.ts          ← Spoke IN: validate + write signals to queue
    │   └── delivery.ts              ← Spoke OUT: route to Mailgun/HeyReach
    └── migrations/
        └── 001_lcs_tables.sql        ← D1 schema: 7 tables
```

---

## Architecture: Hub-Spoke

```
                    ┌──────────────────────────────┐
                    │          LCS HUB             │
                    │                              │
                    │  scheduled() → Producer      │
                    │  queue()     → Consumer       │
                    │  fetch()     → HTTP API       │
                    │                              │
                    │  LOGIC:                       │
                    │    gates.ts    (9 valves)     │
                    │    compiler.ts (CID→SID→MID)  │
                    │    utils.ts   (events/errors) │
                    └──────────────┬───────────────┘
                                   │
          ┌────────────────────────┼────────────────────────┐
          │                        │                        │
   ┌──────┴──────┐         ┌──────┴──────┐          ┌──────┴──────┐
   │ SPOKES IN   │         │ SPOKES OUT  │          │ FEEDBACK    │
   │             │         │             │          │             │
   │ POST /signal│         │ Mailgun API │          │ POST        │
   │ POST /signals│        │ HeyReach API│          │ /webhook/   │
   │             │         │ (via direct)│          │  mailgun    │
   │ Standard    │         │             │          │  heyreach   │
   │ Signal fmt  │         │ Standard    │          │             │
   │             │         │ MessagePkg  │          │ Traces back │
   │             │         │             │          │ via mid_id  │
   └─────────────┘         └─────────────┘          └─────────────┘
```

---

## D1 Tables (7 total)

| Table | Type | Purpose |
|-------|------|---------|
| `company` | Workspace | Company data seeded from Neon vault. Gate stack reads this. |
| `signal_queue` | Ingress | Signals from dumb workers. Standard format. |
| `cid` | CANONICAL (Stage 1) | Compiled intelligence dossier per company. |
| `sid` | CANONICAL (Stage 2) | Campaign design with message sequence. |
| `mid` | CANONICAL (Stage 3) | Individual delivery records per message. |
| `suppression` | Shutoff | Learned blocks (strike 3, bounces, unsubscribed). |
| `event` | CET (audit) | Append-only event log. Every action logged. |
| `err0` | ERROR (drain) | All failures. Stage + type + detail. |

### CQRS
- Each stage writes to its own CANONICAL table
- All failures write to err0 (single ERROR table)
- All actions logged to event (append-only CET)
- All writes are INSERTs (immutability enforced)

---

## Standard Signal Format (Spoke IN Interface)

Every dumb worker must emit signals in this format:

```json
{
  "sovereign_company_id": "uuid",
  "worker": "DOL | PEOPLE | BLOG | TALENT_FLOW",
  "signal_type": "RENEWAL_APPROACHING | TF-01 | EXPANSION | etc.",
  "magnitude": 55,
  "expires_at": "2026-06-23T00:00:00Z",
  "raw_payload": { "...worker-specific data..." }
}
```

**Hub doesn't care which worker produced it.** Add a new worker → emit signals in this format → hub processes them. Zero code changes to hub.

### API Endpoints for Signal Ingestion
- `POST /signal` — single signal
- `POST /signals` — batch of signals

---

## Standard Message Package (Spoke OUT Interface)

Every delivery adapter receives this format:

```typescript
{
  mid_id: string;
  sid_id: string;
  cid_id: string;
  sovereign_company_id: string;
  sequence_num: number;
  channel: 'MG' | 'HR';
  path_type: 'WARM' | 'COLD';
  recipient_email: string | null;
  recipient_linkedin: string | null;
  subject: string;
  body_plain: string;
  body_html: string;
}
```

**Add a new delivery channel → accept this format → route it.** Zero code changes to hub.

---

## Pipeline Flow (Producer → Consumer)

### Producer (cron — `scheduled()`)
1. Scans `signal_queue` for `status = 'pending'`
2. Groups by `sovereign_company_id`
3. Marks signals as `'processing'`
4. Queues a `compile_cid` job per company to CF Queue

### Consumer (queue — `queue()`)
Processes four job types in sequence:

| Job Type | What It Does | Queues Next |
|----------|-------------|-------------|
| `compile_cid` | Aggregates signals + layers → writes CID | `design_sid` |
| `design_sid` | Reads CID → queries svg-brain → builds campaign | `deliver_mid` |
| `deliver_mid` | Ships next message in sequence via Mailgun/HeyReach | — (waits for webhook) |
| `process_webhook` | Updates MID status, checks strikes, handles CTA click | — (may queue next `deliver_mid`) |

---

## 9-Gate Stack (`gates.ts`)

| Gate | Name | Type | Hard Stop? |
|------|------|------|-----------|
| 0 | `agent_assignment` | Agent in 100mi radius | YES |
| 1 | `geography` | PA/VA/MD/OH/WV/KY | YES |
| 2 | `size` | 50-2,000 employees | YES |
| 3 | `dol_filing` | Form 5500 exists | YES |
| 4 | `renewal_window` | Within 120-day window | No |
| 5 | `premium_trend` | YoY premium increase | No |
| 6 | `talent_flow` | TF signal active | No |
| 7 | `blog_signal` | Blog signal active | No |
| 8 | `composite_signal` | ≥1 substantive gate (3-7) passed | YES |

**Must pass**: Gates 0, 1, 2, 3, and 8 (hard stops).
**Signal boosters**: Gates 4-7 (contribute to gate 8 composite).

---

## Compiler (`compiler.ts`)

### Stage 1: CID Compile — `compileCid()`
1. Fetch signals from D1
2. Fetch company data from Neon vault (TODO: wire Hyperdrive)
3. Build signal presence for gate evaluation
4. Run 9-gate stack
5. Compile 5 intelligence layers (financial, personnel, behavioral, movement, engagement)
6. Write CID to D1
7. Mark signals as compiled
8. Queue `design_sid` if gates passed

### Stage 2: SID Design — `designSid()`
1. Read compiled CID
2. Determine campaign type from signal combination
3. Route to audience (CFO/CEO money path vs HR workload path)
4. Check suppression list
5. Query svg-brain for content (600 pages)
6. Build message sequence (1-5 messages depending on campaign type)
7. Write SID to D1
8. Queue `deliver_mid`

### Stage 3: MID Deliver — `deliverMid()`
1. Read SID
2. Find next undelivered message in sequence
3. Build message package
4. Write MID record (queued)
5. Route to Mailgun or HeyReach
6. Update delivery status
7. Check strike count on failure (strike 3 → suppress)

---

## Two Message Paths

| Path | Target | Core Message | Tone |
|------|--------|-------------|------|
| `cfo_ceo_money` | CFO first, then CEO | "10% of your people cost 85%. I manage that 10%." | Patton — authority, data-led |
| `hr_workload` | HR | "I take enrollment, tickets, vendors off your plate." | Patton — pain elimination |

### Campaign Types

| Type | Signals | Touches | Duration |
|------|---------|---------|----------|
| `monthly_touch` | No movement | 1 | Single send |
| `renewal` | DOL signals | 4 | ~3 weeks |
| `exec_change` | Talent Flow | 3 | ~2 weeks |
| `activity` | Blog signals | 3 | ~2 weeks |
| `priority` | 3+ signals (hot) | 5 | ~3 weeks |

---

## HTTP API Endpoints

| Method | Path | Purpose |
|--------|------|---------|
| GET | `/health` | Health check + signal/CID counts |
| POST | `/signal` | Ingest single signal (spoke IN) |
| POST | `/signals` | Ingest signal batch (spoke IN) |
| POST | `/webhook/mailgun` | Mailgun delivery webhook |
| POST | `/webhook/heyreach` | HeyReach delivery webhook |
| GET | `/status` | Pipeline stats (signals, CIDs, SIDs, MIDs, errors, suppressions) |
| GET | `/company/{id}` | Full company detail (signals, CIDs, SIDs, MIDs, events) |
| GET | `/trace/{id}` | Bidirectional ID trace (SIG-, CID-, SID-, MID- prefix) |
| POST | `/seed` | Seed company data into D1 workspace (JSON array) |

---

## ID Chain

```
sovereign_company_id (permanent — from company_target)
  └── SIG-{DATE}-{ULID}        (signal from dumb worker)
       └── CID-{DATE}-{ULID}    (compiled dossier)
            └── SID-{DATE}-{ULID} (campaign)
                 ├── MID-{SID}-01-MG  (message 1, email)
                 ├── MID-{SID}-02-MG  (message 2, email)
                 └── MID-{SID}-03-HR  (message 3, LinkedIn)
```

Trace any ID forward or reverse via `GET /trace/{id}`.

---

## Secrets Required (from Doppler)

| Secret | Doppler Key | Purpose |
|--------|------------|---------|
| `NEON_URL` | `OUTREACH_DATABASE_URL` | Neon vault (35,629 companies) |
| `SVG_BRAIN_API_KEY` | `SVG_BRAIN_API_KEY` | Content library (590 docs) |
| `IMO_BRAIN_API_KEY` | `IMO_BRAIN_API_KEY` | System knowledge |
| `COMPOSIO_API_KEY` | `GLOBAL_COMPOSIO_API_KEY` | Integration router |
| `MAILGUN_API_KEY` | `GLOBAL_MAILGUN_API_KEY` | Email delivery |
| `HEYREACH_API_KEY` | `GLOBAL_HEYREACH_API_KEY` | LinkedIn delivery |

---

## What's TODO (Not Yet Wired)

| Item | Where | What's Needed |
|------|-------|---------------|
| **Neon→D1 Seed Script** | seed endpoint + script | Build script to pull territory dossier (35,629 companies) from Neon vault → D1 company table. Same SEED→WORK→PUSH lifecycle as People Worker 200. Seed endpoint at POST /seed accepts JSON array. |
| **D1 database creation** | `wrangler.toml` | Run `wrangler d1 create lcs-hub` and update database_id. |
| **CF Queue creation** | `wrangler.toml` | Run `wrangler queues create lcs-pipeline` and `wrangler queues create lcs-dlq`. |
| **Monte Carlo** | `compiler.ts → designSid()` | Wire to layer0-engine for sigma tracking and campaign optimization. |
| **WARM/COLD path detection** | `compiler.ts → determinPathType()` | Wire CID reachability layer (SocialSweep or connection data). Currently defaults to COLD. |
| **AI tail personalization** | `compiler.ts → buildMessageSequence()` | Claude API for final message personalization after deterministic assembly. |
| **Composio routing** | `spokes/delivery.ts` | Currently hits Mailgun/HeyReach APIs directly. Could route through Composio for unified integration. |
| **Message templates** | `compiler.ts → getCampaignBody()` | Currently hardcoded Patton-tone templates. Wire svg-brain content into dynamic assembly. |
| **Neon vault promotion** | — | After CID/SID/MID complete, promote results from D1 workspace to Neon vault. |

---

## Smoke Test Checklist

When ready to test:

**Phase 1: Infrastructure**
1. [ ] Create D1 database: `wrangler d1 create lcs-hub`
2. [ ] Update `wrangler.toml` with real database_id
3. [ ] Create queues: `wrangler queues create lcs-pipeline` + `lcs-dlq`
4. [ ] Run migration: `npm run d1:migrate:local`
5. [ ] `npm run dev` — start local

**Phase 2: Seed D1 (Neon → D1)**
6. [ ] POST test company to `/seed` with all fields (agent, DOL data, people slots)
7. [ ] Verify company row exists in D1

**Phase 3: Spoke IN (Signal Ingestion)**
8. [ ] POST a test signal to `/signal` for the seeded company
9. [ ] Verify signal_queue row created in D1
10. [ ] Verify event logged in CET

**Phase 4: Hub (Gate Stack + CID Compile)**
11. [ ] Trigger producer (cron or manual)
12. [ ] Verify signal marked as 'processing'
13. [ ] Verify CID compiled — check `/status`
14. [ ] Verify gate results in CID record — all 9 gates evaluated
15. [ ] Verify 5 intelligence layers populated

**Phase 5: Hub (SID Design)**
16. [ ] Verify SID designed with campaign type + audience path
17. [ ] Verify message sequence created (correct touch count for campaign type)
18. [ ] Verify svg-brain queried for content (check content_sources)

**Phase 6: Spoke OUT (MID Delivery)**
19. [ ] Verify MID record created with 'queued' status
20. [ ] Verify message sent to Mailgun (check Dave's test inbox)
21. [ ] Verify MID status updated to 'sent'

**Phase 7: Feedback (Webhook)**
22. [ ] POST fake webhook to `/webhook/mailgun` with mid_id in payload
23. [ ] Verify MID status updated to 'delivered'
24. [ ] Verify event logged in CET

**Phase 8: Trace (Bidirectional)**
25. [ ] `GET /trace/MID-xxx` → traces back to SID → CID → signals
26. [ ] `GET /company/{id}` → shows full timeline

**Phase 9: Error Path**
27. [ ] Simulate bounce webhook → verify err0 entry
28. [ ] Send 3 bounces → verify strike 3 → verify suppression entry
29. [ ] Send another signal for suppressed company → verify blocked

**Each phase is independent. If one fails, you know exactly which spoke or hub stage broke.**

---

## Document Control

| Field | Value |
|-------|-------|
| Created | 2026-03-23 |
| Version | 1.0.0 |
| Authority | Foundational Bedrock (`law/doctrine/FOUNDATIONAL_BEDROCK.md`) |
| Process Docs | `PROCESS-LCS-v2.md` (plumbing), `PROCESS-COMPILER.md` (water) |
| Location | `workers/lcs-hub/` |
| Pattern | Same as Intelligence Engine (producer/consumer/CF Queues) |
