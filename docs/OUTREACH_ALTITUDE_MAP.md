# OUTREACH PROGRAM — ALTITUDE MAP (30000→5000)  [Input → Middle → Output]

## [30000] VISION
- Generate qualified conversations that convert to booked appointments and revenue.
- **Doctrine**: History-first, idempotent, altitude-coded steps; all writes pass validators; full audit via master_error_log.

## [20000] CATEGORIES (BRANCHES)
1. **Lead Branch** (Company → Roles)
2. **Messaging Branch** (Draft → Personalize → Approvals)
3. **Delivery Branch** (Send → Track → Reply Handling)
4. **Scheduling Branch** (Book → Confirm → Sync)
5. **Feedback & Scoring Branch** (Engagement → Fit → Phase)
6. **Compliance & Observability Branch** (Errors → Heartbeats → Dashboards)
7. **Data Vault & Promotion Branch** (Staging → Canonical → Vault)

## [10000] SPECIALIZATION (Per Branch → Sub-lanes, Queues, Tables, Tools)

### A) LEAD BRANCH
**Lanes:**
1. Intake (Apollo CSV) → staging: `marketing.company_intake`
2. Canonicalize Company → `marketing.company` (upsert)
3. Create Role Slots (CEO/CFO/HR) → `marketing.company_role_slot`
4. Scrape Contacts (Apify) → staging→normalized; history: `marketing.slot_history`
5. Validate Contacts (Validator) → `marketing.person`; status: `outreach.lead_pipeline_status`

**Queues/States:**
- `outreach.lead_queue` {queued|scraping|validating|completed|error}

**Tools:**
- CSV Ingest (Render)
- Apify Scrapers
- Validator (Mindpal/Claude)
- Neon (vault)

**Observability:**
- `shq.master_error_log`
- Lead Tracker view (Neon/Looker)

### B) MESSAGING BRANCH
**Lanes:**
1. Persona & Tone Resolve (company_industry, role, signals)
2. Message Draft (templates + variables) → `messaging.outbox_draft`
3. Personalization (LI/website snippets) → `messaging.outbox_personalized`
4. Approval/Gate (policy checks, length, compliance) → `messaging.outbox_ready`

**Queues:**
- `messaging.compose_queue`
- `messaging.approval_queue`

**Tools:**
- Template engine
- Policy checker
- Style canon

### C) DELIVERY BRANCH (Instantly / HeyReach / Email API)
**Lanes:**
1. Channel Mapping (email, LI, alt) → `delivery.channel_map`
2. Rate/QPS Guardrails → `shq_guardrails`
3. Send & Track → `delivery.events` (delivered/open/click/reply/bounce)
4. Reply Routing/Parse → `delivery.reply_inbox` → `triage_queue`

**Queues:**
- `delivery.send_queue`
- `delivery.reply_queue`

**Tools:**
- Instantly API
- HeyReach API
- Mail provider
- Webhooks to Render/Vercel

### D) SCHEDULING BRANCH
**Lanes:**
1. Qualify → `lead_fit_score` (feedback branch)
2. Propose Times → `scheduling.proposals`
3. Book & Confirm → `scheduling.bookings` (+ Google/Outlook sync)
4. Handover → `crm.opportunities` / meetings

**Queues:**
- `scheduling.queue`
- `reminders.queue`

**Tools:**
- Calendar API
- Link router
- CRM connector

### E) FEEDBACK & SCORING BRANCH
**Lanes:**
1. Signal Capture (opens/clicks/replies/site_visits) → `analytics.signal_log`
2. Lead Scoring (rules/model) → `analytics.lead_score`
3. Phase Promotion/Demotion → `outreach.lead_pipeline_status`
4. Content Learning Loop (what worked) → `messaging.template_performance`

**Tools:**
- Rules engine
- (optional) light ML scorer

### F) COMPLIANCE & OBSERVABILITY BRANCH
**Lanes:**
1. Error Logging → `shq.master_error_log` (unique_id, process_id, blueprint_id, hint)
2. Heartbeats & Step Telemetry → `shq.heartbeat_log` (blueprint_version_hash)
3. Dashboards → Looker/Vercel read-only views
4. Policy & Opt-out Registry → `compliance.contact_prefs` / `suppression_list`

**Tools:**
- Doctrine Tracker
- Looker
- Vercel (read/admin only)

### G) DATA VAULT & PROMOTION BRANCH
**Lanes:**
1. Staging → Canonical (idempotent upserts) → Neon (STAMPED)
2. History-First Writes → `*_history` tables (`slot_history`, `delivery.events`)
3. Promotion Gates (validators) → vault tables (`marketing.person`, `marketing.company`)
4. Backfill & Refresh (≥30d) → `backfill.cron_log`

**Tools:**
- Validators
- Migration/DDL
- CI "make verify"

## [5000] EXECUTION MODEL (Cross-cutting)
- **Orchestration**: Render workers (ingest/scrape/validate), Apify jobs; Vercel for admin UI + webhooks.
- **Keys/Secrets**: Env-scoped; RLS on Neon; write via Render; Vercel read-only service user.
- **CI**: SQL lint, migrations, fixture dry-run, env checks.
- **Registries (SHQ)**: `shq_tool_registry`, `shq_process_registry`, `shq_process_key_reference` (Barton IDs).
- **Queues**: `lead_queue`, `compose_queue`, `approval_queue`, `send_queue`, `reply_queue`, `scheduling.queue`, `backfill.queue`.
- **Guardrails**: per-domain QPS caps, monthly caps, retries with backoff, dead-letter queues.