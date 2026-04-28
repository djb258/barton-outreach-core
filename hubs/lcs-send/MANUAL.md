# LCS Hub
## The outreach pipeline plumbing -- signal ingestion, CID/SID/MID compilation, domain warmup, and SEED operations.
### Status: BUILD
### Medium: worker
### Business: svg-agency

---

# IDENTITY (Thing -- what this IS)

_Everything in this cluster answers: what exists? These are constants that don't change regardless of who reads this or when._

## 1. IDENTITY

| Field | Value |
|-------|-------|
| ID | lcs-hub |
| Name | LCS Hub |
| Medium | worker |
| Business Silo | svg-agency (outreach) |
| CTB Position | leaf -> workers/lcs-hub |
| ORBT | BUILD |
| Strikes | 0 |
| Authority | inherited -- imo-creator |
| Last Modified | 2026-04-21 |
| BAR Reference | BAR-148, BAR-190, BAR-303, BAR-304, BAR-305, BAR-306, BAR-307, BAR-308 |

### HEIR (8 fields -- Aviation Model, Bedrock S8)

| Field | Value |
|-------|-------|
| sovereign_ref | imo-creator |
| hub_id | lcs-hub |
| ctb_placement | leaf |
| imo_topology | middle |
| cc_layer | CC-03 context |
| services | Cloudflare Workers, D1 (svg-d1-spine, svg-d1-outreach-ops, imo-d1-global), Hyperdrive (Neon), Queues (lcs-pipeline), Composio |
| secrets_provider | doppler (imo-creator / dev) + wrangler secrets |
| acceptance_criteria | Health endpoint returns ok, signal ingestion creates queue entries, CID/SID/MID pipeline completes end-to-end, domain warmup ramps correctly |


### Worker Fill Rule
Identity must match the real worker and sit at `leaf -> workers/<name>`.

### Cross-reference
- `law/doctrine/WORKER_FILL_INSTRUCTIONS.md` §1
- `workers/lcs-hub/wrangler.toml`
- `workers/lcs-hub/src/index.ts`

**0 -> 1 when:** ID/name/medium/HEIR match the worker, `ctb_placement = leaf`, and bindings/services are not overstated.

---

## 2. PURPOSE

_What breaks without it. What business outcome it serves. If you can't answer this, it shouldn't exist._

Without LCS Hub, no outreach signal gets compiled into a communication, no email gets assembled, and no message gets delivered. It is the central hub of the outreach pipeline -- every signal from every spoke flows through it. Downstream, Campaign Engine (700) and Sales Portal (900) starve without compiled CIDs reaching delivery.


### Worker Fill Rule
State the worker's business outcome, who starves without it, and the operational risk if it fails.

### Cross-reference
- `law/doctrine/WORKER_FILL_INSTRUCTIONS.md` §2
- `workers/lcs-hub/wrangler.toml`
- `workers/lcs-hub/src/index.ts`

**0 -> 1 when:** purpose is business-level, names downstream consumers, and avoids collapsing into route detail.

---

## 3. RESOURCES

_Everything this depends on. A mechanic reads this and knows exactly what to set up before it can run._

### Dependencies

| Dependency | Type | What It Provides | Status |
|-----------|------|-----------------|--------|
| svg-d1-spine | database (D1) | Company identity, LCS pipeline tables (signal_queue, cid, sid, mid, event, err0, domain_rotation) | DONE |
| svg-d1-outreach-ops | database (D1) | Company target, DOL, people, blog, vendor data | DONE |
| imo-d1-global | database (D1) | ZIP codes, geo reference tables | DONE |
| Neon OUTREACH | database (Hyperdrive) | Vault -- source of truth for SEED operations only | DONE |
| lcs-pipeline queue | queue | Pipeline job processing (CID -> SID -> MID) | DONE |
| lcs-dlq | queue | Dead letter queue for failed jobs | DONE |
| Mailgun | service | Email delivery (14 domains, warmup ramp) | DONE |
| HeyReach | service | LinkedIn delivery | DONE |
| Composio | service | Integration hub | DONE |

### Downstream Consumers

| Consumer | What It Needs |
|----------|--------------|
| Mission Control dashboard | /health, /status endpoints for pipeline visibility |
| Mailgun webhooks | /webhook/mailgun for delivery status feedback |
| HeyReach webhooks | /webhook/heyreach for LinkedIn delivery feedback |
| Campaign Engine (700) | Compiled CIDs and delivered MIDs |

### Secrets (if applicable)

| Secret | Doppler Project | Config | Used By |
|--------|----------------|--------|---------|
| NEON_URL | imo-creator | dev (OUTREACH_DATABASE_URL) | SEED operations via Hyperdrive |
| SVG_BRAIN_API_KEY | imo-creator | dev | Content library queries |
| IMO_BRAIN_API_KEY | imo-creator | dev | System knowledge queries |
| COMPOSIO_API_KEY | imo-creator | dev (GLOBAL_COMPOSIO_API_KEY) | Integration calls |
| MAILGUN_API_KEY | imo-creator | dev (GLOBAL_MAILGUN_API_KEY) | Email delivery |
| HEYREACH_API_KEY | imo-creator | dev (GLOBAL_HEYREACH_API_KEY) | LinkedIn delivery |


### Worker Fill Rule
Inventory every binding class, secret, trigger, upstream dependency, and downstream consumer; absent classes must be explicit `none`.

### Cross-reference
- `law/doctrine/WORKER_FILL_INSTRUCTIONS.md` §3
- `workers/lcs-hub/wrangler.toml`
- `workers/lcs-hub/src/index.ts`

**0 -> 1 when:** resources agree with the local worker config and no binding class is silently omitted.

---

# CONTRACT (Flow -- what flows through this)

_Everything in this cluster answers: what moves? How does data/work enter, get processed, and exit?_

## 4. IMO -- Input, Middle, Output

### Two-Question Intake (Bedrock S3)
1. **"What triggers this?"** -- Cron (07:00 UTC daily), HTTP requests (signal ingestion, webhooks, SEED, manual /run), queue messages
2. **"How do we get it?"** -- Cron controller, HTTP fetch handler, queue batch consumer

### Input
- Cron trigger at 07:00 UTC daily (scheduled handler)
- HTTP POST signals from upstream spokes
- Webhook payloads from Mailgun and HeyReach
- SEED requests (manual HTTP POST to pull Neon vault data into D1)
- Manual pipeline trigger via /run

### Middle

| Step | Input | What Happens | Output | Tool Used |
|------|-------|-------------|--------|-----------|
| 1 | Cron trigger | Auto-pause domains with >5% bounce rate | Updated domain_rotation | D1 |
| 2 | Cron (Monday) | Advance warmup week for safe domains (20/40/80/150/250) | Updated daily_cap | D1 |
| 3 | Cron | Reset daily send counts for all domains | Zeroed sent_today, bounce_count_24h | D1 |
| 4 | Cron | Find pending signals (LIMIT 50, priority DESC) | Signal list | D1 |
| 5 | Pending signals | Queue compile_cid job per signal | Queue messages | lcs-pipeline queue |
| 6 | compile_cid job | Compile CID from signal, auto-chain to design_sid | CID record + SID job | compiler-v2 |
| 7 | design_sid job | Construct SID (sequence/template), auto-chain to deliver_mid | SID record + MID job | compiler-v2 |
| 8 | deliver_mid job | Deliver MID via Mailgun/HeyReach | Delivery attempt logged | Mailgun/HeyReach |
| 9 | Webhook payload | Update MID delivery status, log event, handle bounces (ORBT strike) | Updated MID + CET event | D1 |
| 9b | Web page-event payload | Log web activity with event_type + page_step; leave delivery_status unset for web events | Page event row in lcs_event | D1 |

### Output
- Pipeline events logged to lcs_event (canonical)
- Errors logged to lcs_err0 (CQRS error table)
- Delivery status updates on lcs_mid_sequence_state
- JSON API responses for /health, /status, /company/:id, /trace/:id

### Circle (Bedrock S5)
Webhook delivery feedback (open/click/bounce) feeds back into MID status. Bounces trigger ORBT strikes. Strike 3 escalates to HUMAN_ESCALATION. Domain pause on >5% bounce rate prevents further sends. All events traced in lcs_event.


### Worker Fill Rule
Document the worker as trigger/request -> process -> response, with worker code as hub and routes/triggers as spokes.

### Cross-reference
- `law/doctrine/WORKER_FILL_INSTRUCTIONS.md` §4
- `workers/lcs-hub/wrangler.toml`
- `workers/lcs-hub/src/index.ts`

**0 -> 1 when:** Two-Question Intake, Input, Middle, Output, and Circle are explicit and match the real triggers/handlers.

---

## 5. DATA SCHEMA

_Where the data lives. What's read, written, joined. The plumbing._

### Bindings

| Binding | Type | Database | ID |
|---------|------|----------|----|
| D1 | D1 | svg-d1-spine | 641a9a1e-0882-41a7-82af-ea700e7cfbb3 |
| D1_OUTREACH | D1 | svg-d1-outreach-ops | 73a285b8-770a-4370-abbe-ce9607be0b34 |
| D1_GLOBAL | D1 | imo-d1-global | 5b902b59-5d65-4c7a-be7c-3763c132b585 |
| HD_NEON | Hyperdrive | Neon OUTREACH | 6a76791c688346e88def0060e41a2be5 |
| LCS_QUEUE | Queue | lcs-pipeline | -- |

### READ Access

| Source | What It Provides | Join Key |
|--------|-----------------|----------|
| lcs_signal_queue (D1) | Pending signals to process | sovereign_company_id |
| lcs_cid (D1) | Compiled communications | communication_id |
| lcs_sid_output (D1) | Assembled sequences | sid_id, communication_id |
| lcs_mid_sequence_state (D1) | Delivery status | mid_id, communication_id |
| lcs_event (D1) | Pipeline event log and web page telemetry | communication_id, sovereign_company_id, event_type, step_name |
| lcs_err0 (D1) | Error records | sovereign_company_id |
| lcs_domain_rotation (D1) | Domain warmup/cap status | domain |
| lcs_signal_registry (D1) | Signal set definitions and hashes | signal_set_hash |
| lcs_engagement_rules (D1) | Closed-loop response rules per trigger event | trigger_event |
| lcs_sequence_def (D1) | Multi-step sequence playbook definitions | sequence_id, step_number |
| lcs_contact_sequence_state (D1) | Per-contact position in active sequences | contact_email, sequence_id |
| lcs_contact_engagement_score (D1) | Composite engagement score per contact | contact_email |
| lcs_contact_channel_state (D1) | Per-contact channel state (email vs LinkedIn) | contact_email |
| lcs_voice_library (D1) | Dave Barton voice constants per target role | voice_id |
| fleet/content/VOICE-SPEC.yaml | Machine voice contract extracted in Thread 1; email copy validation and brand anchor source | file path |
| lcs_m_registry (D1) | Engine constants registry (Dave's M inventory) | constant_id |
| lcs_email_signature (D1) | Email signature templates | signature_id |
| outreach_company_target (D1_OUTREACH) | Company data for compilation | outreach_id |
| cl_company_identity (D1) | Sovereign identity | outreach_id |

### WRITE Access

| Target | What It Writes | When |
|--------|---------------|------|
| lcs_signal_queue (D1) | New signals | /signal, /signals POST |
| lcs_cid (D1) | Compiled CIDs | compile_cid queue job |
| lcs_sid_output (D1) | Assembled SIDs | design_sid queue job |
| lcs_mid_sequence_state (D1) | Delivery attempts + status | deliver_mid + webhooks |
| lcs_event (D1) | All pipeline events and page events | Every pipeline step and web event |
| lcs_err0 (D1) | Errors and bounces | Failures + bounce webhooks |
| lcs_domain_rotation (D1) | Warmup progression, daily resets | Cron handler |
| lcs_contact_sequence_state (D1) | Sequence position, status, next_step_after | compile_cid + cron scheduler |
| lcs_contact_engagement_score (D1) | Engagement score updates on webhook events | Webhook handler (BAR-305) |
| lcs_contact_channel_state (D1) | Channel state upsert on every contact | Webhook handler (BAR-307) |
| lcs_engagement_rules (D1) | Human-configured rules (read-only by compiler) | Seeded at migration; Dave tunes directly |

### Forbidden Paths

| Action | Why |
|--------|-----|
| Neon reads during pipeline WORK phase | SEED-WORK-PUSH lifecycle -- D1 is workspace, Neon is vault only |
| Direct writes to lcs_event from outside worker | CQRS -- events enter from leaves only |
| Modification of DNS for svg.agency, svgwv.com, weewee.me | Protected domains |


### Worker Fill Rule
Name every read path, write path, join chain, CQRS pair, and forbidden path for the worker.

### Cross-reference
- `law/doctrine/WORKER_FILL_INSTRUCTIONS.md` §5
- `workers/lcs-hub/wrangler.toml`
- `workers/lcs-hub/src/index.ts`

**0 -> 1 when:** schema/plumbing matches the worker's real bindings or explicitly notes when a local binding file is absent.

---

## 6. DMJ -- Define, Map, Join (law/doctrine/DMJ.md)

_Three steps. In order. Can't skip._

### 6a. DEFINE (Build the Key)

| Element | ID | Format | Description | C or V |
|---------|-----|--------|-------------|--------|
| Signal | lcs_signal_queue.id | UUID | Inbound trigger from any spoke | C |
| CID | lcs_cid.communication_id | LCS-UUID | Compiled communication package | C |
| SID | lcs_sid_output.sid_id | SID-UUID | Assembled sequence/template | C |
| MID | lcs_mid_sequence_state.mid_id | RUN-UUID | Single delivery attempt | C |
| Domain | lcs_domain_rotation.domain | FQDN | Sending domain identity | C |
| Delivery status | lcs_mid_sequence_state.delivery_status | enum | Current state of a delivery | V |
| Daily send count | lcs_domain_rotation.sent_today | integer | Resets at 07:00 UTC | V |

### 6b. MAP (Connect Key to Structure)

| Source | Target | Transform |
|--------|--------|-----------|
| Signal.sovereign_company_id | CID.sovereign_company_id | direct |
| CID.communication_id | SID.communication_id | direct |
| SID.communication_id | MID.communication_id | direct |
| Webhook payload | MID.delivery_status | classify (mailgun/heyreach event type) |

### 6c. JOIN (Path to Spine)

| Join Path | Type | Description |
|-----------|------|-------------|
| signal -> CID -> SID -> MID | direct | Pipeline chain via communication_id |
| MID -> lcs_event | direct | All events traced by communication_id |
| CID -> cl_company_identity | direct | sovereign_company_id to spine identity |


### Worker Fill Rule
Every element must be defined with ID + format + C/V, mapped to a structural target, and joined back to the worker spine or sovereign trunk.

### Cross-reference
- `law/doctrine/WORKER_FILL_INSTRUCTIONS.md` §6
- `workers/lcs-hub/wrangler.toml`
- `workers/lcs-hub/src/index.ts`

**0 -> 1 when:** every defined element is mapped and every join path closes without orphaned worker elements.

---

## 7. CONSTANTS & VARIABLES (Bedrock S2)

### Constants (structure -- never changes)
- Pipeline chain: Signal -> CID -> SID -> MID (the architecture)
- CQRS tables: lcs_event (canonical) + lcs_err0 (error)
- Domain warmup ramp: week 1=20, 2=40, 3=80, 4=150, 5+=250
- Bounce threshold for auto-pause: 5%
- SEED-WORK-PUSH lifecycle (Neon vault, D1 workspace)
- Queue structure: lcs-pipeline + lcs-dlq, max_batch_size=5, max_retries=3
- Cron schedule: 0 7 * * * (daily at 07:00 UTC)
- ID prefixes: LCS- (CID), SID- (SID), RUN- (MID), ERR- (error)

### Variables (fill -- changes every run/cycle)
- Signal payloads (content of each inbound signal)
- Delivery status per MID (PENDING -> DELIVERED -> OPENED -> CLICKED, or BOUNCED)
- Web events use event_type + page_step/step_name instead of delivery_status
- Daily send counts per domain
- Warmup week per domain
- Bounce rates per domain
- ORBT strike count per company


### Worker Fill Rule
Separate worker architecture/constants from runtime fill and state the guard rails on variables.

### Cross-reference
- `law/doctrine/WORKER_FILL_INSTRUCTIONS.md` §7
- `workers/lcs-hub/wrangler.toml`
- `workers/lcs-hub/src/index.ts`

**0 -> 1 when:** constants and variables are clearly separated and no structural element is left unclassified.

---

## 8. STOP CONDITIONS (Bedrock S6)

| Condition | Action |
|-----------|--------|
| Can't answer two-question intake | HALT |
| Signal missing sovereign_company_id | Reject with 400 |
| Domain bounce rate > 5% | Auto-pause domain |
| Queue job fails 3 retries | Dead letter queue |
| ORBT strike 3 on same company | HUMAN_ESCALATION |
| Cron finds 0 pending signals | Log and exit clean |
| CF Worker CPU limit (50ms) | Runtime timeout |
| CF Worker memory limit (128MB) | OOM kill |
| D1 row size limit (1MB) | Write fails |


### Worker Fill Rule
Include intake failure, repeated failure, strike escalation, and human stop conditions specific to this worker.

### Cross-reference
- `law/doctrine/WORKER_FILL_INSTRUCTIONS.md` §8
- `workers/lcs-hub/wrangler.toml`
- `workers/lcs-hub/src/index.ts`

**0 -> 1 when:** at least four deterministic stop conditions are present, including intake failure, repeated failure, strike escalation, and human stop/confirmation.

---

# GOVERNANCE (Change -- how this is controlled)

_Everything in this cluster answers: what transforms? How is quality measured, verified, certified?_

## 9. VERIFICATION

_Executable proof that it works. Run these._

```
1. GET /health -> expected: { status: "ok", worker: "lcs-hub", version: "v2" } with company count > 0
2. POST /signal with valid payload -> expected: 201 with signal_id
3. POST /run with sovereign_company_id -> expected: full pipeline trace (CID -> SID -> MID)
4. GET /status -> expected: signal/cid/sid/mid counts by status
5. GET /trace/LCS-{id} -> expected: full chain with sids, mids, events
6. POST /seed/clean?table=company_target&limit=10 -> expected: rows seeded from Neon
```

**Three Primitives Check (Bedrock S1):**
1. **Thing:** D1 tables exist (lcs_signal_queue, lcs_cid, lcs_sid_output, lcs_mid_sequence_state, lcs_event, lcs_err0, lcs_domain_rotation)
2. **Flow:** Signal -> queue -> CID -> SID -> MID -> webhook -> event log
3. **Change:** Signal status changes from pending to processed; MID status changes on webhook delivery


### Worker Fill Rule
Verification must be runnable against the worker's actual routes, bindings, and state transitions.

### Cross-reference
- `law/doctrine/WORKER_FILL_INSTRUCTIONS.md` §9
- `workers/lcs-hub/wrangler.toml`
- `workers/lcs-hub/src/index.ts`

**0 -> 1 when:** at least three tests are runnable as written and Thing/Flow/Change correspond to real worker existence, flow, and state change.

---

## 10. ANALYTICS

_The BUILD->OPERATE gate. Three sub-layers._

### 10a. Metrics

_Define BEFORE build starts._

| Metric | Unit | Baseline | Target | Tolerance |
|--------|------|----------|--------|-----------|
| Signal-to-CID conversion | % | BASELINE | >95% | +/- 5% |
| CID-to-delivery rate | % | BASELINE | >90% | +/- 10% |
| Bounce rate per domain | % | BASELINE | <5% | 5% hard cap |
| Pipeline latency (signal -> MID) | ms | BASELINE | <5000 | +/- 2000 |
| Queue DLQ rate | % | BASELINE | <1% | 1% hard cap |

### 10b. Sigma Tracking (Bedrock S2)

| Metric | Run 1 | Run 2 | Run 3 | Trend | Action |
|--------|-------|-------|-------|-------|--------|
| Signal-to-CID | -- | -- | -- | PENDING | First smoke test run |

### 10c. ORBT Gate Rules

| From | To | Gate |
|------|-----|------|
| BUILD | OPERATE | All metrics within tolerance for 3 runs + auditor sign-off |
| OPERATE | REPAIR | Any metric outside tolerance |
| REPAIR | OPERATE | Fix + metric back + auditor verification |
| Any (Strike 3) | TROUBLESHOOT/TRAIN | Fleet-wide fix -> AD |


### Worker Fill Rule
Metrics must be measurable for this worker, sigma must follow Bedrock semantics, and BUILD -> OPERATE gates must name the owner.

### Cross-reference
- `law/doctrine/WORKER_FILL_INSTRUCTIONS.md` §10
- `workers/lcs-hub/wrangler.toml`
- `workers/lcs-hub/src/index.ts`

**0 -> 1 when:** metrics are measurable from worker evidence, sigma trends are meaningful, and ORBT gate rules are explicit.

---

## 11. EXECUTION TRACE

_Append-only. Every action logged. The auditor reads this._

| Field | Format | Required |
|-------|--------|----------|
| trace_id | UUID | Yes |
| run_id | UUID | Yes |
| step | action name | Yes |
| target | measurable | Yes |
| actual | measurable | Yes |
| delta | the gap | Yes |
| status | done / failed / skipped | Yes |
| error_code | text or null | If failed |
| error_message | text or null | If failed |
| tools_used | JSON array | Yes |
| duration_ms | integer | Yes |
| cost_cents | integer | Yes |
| timestamp | ISO-8601 | Yes |
| signed_by | agent or manual | Yes |


### Worker Fill Rule
Execution trace fields must support per-run worker diagnostics and audit review.

### Cross-reference
- `law/doctrine/WORKER_FILL_INSTRUCTIONS.md` §11
- `workers/lcs-hub/wrangler.toml`
- `workers/lcs-hub/src/index.ts`

**0 -> 1 when:** trace fields are sufficient to reconstruct worker execution, failure, and certification evidence.

---

## 12. LOGBOOK (After Certification Only)

_Created ONLY when the auditor certifies (BUILD -> OPERATE). Append-only. The legal identity._

**No logbook during BUILD.**

### Birth Certificate

| Field | Value |
|-------|-------|
| heir_ref | Full HEIR record |
| orbt_entered | BUILD |
| orbt_exited | OPERATE |
| action | Certified -- airworthiness confirmed |
| gates_passed | { imo: true, ctb: true, circle: true } |
| signed_by | Auditor (different engine than builder) |
| signed_at | timestamp |


### Worker Fill Rule
During BUILD, keep certification fields pending; after audit, this becomes the legal identity of the worker manual.

### Cross-reference
- `law/doctrine/WORKER_FILL_INSTRUCTIONS.md` §12
- `workers/lcs-hub/wrangler.toml`
- `workers/lcs-hub/src/index.ts`

**0 -> 1 when:** BUILD state is honest and no fake OPERATE claim appears before sign-off.

---

## 13. FLEET FAILURE REGISTRY

| Pattern ID | Location | Error Code | First Seen | Occurrences | Strike Count | Status |
|-----------|----------|-----------|-----------|-------------|-------------|--------|
| -- | -- | -- | -- | -- | -- | -- |

**Strike 1:** Repair. **Strike 2:** Scrutiny. **Strike 3:** Troubleshoot/Train -> Airworthiness Directive.


### Worker Fill Rule
Log repeated worker-specific failure patterns with strike counts and AD status where applicable.

### Cross-reference
- `law/doctrine/WORKER_FILL_INSTRUCTIONS.md` §13
- `workers/lcs-hub/wrangler.toml`
- `workers/lcs-hub/src/index.ts`

**0 -> 1 when:** failure patterns are tracked with strike counts, status, and explanatory notes, including strike-3 escalation.

---

## 14. SESSION LOG

| Date | What Was Done | LBB Record |
|------|---------------|-----------|
| 2026-04-04 | Initial MANUAL.md created from wrangler.toml + src/index.ts | pending |
| 2026-04-16 | Section 5 updated — 9 new pipeline engine tables added (BAR-303 through BAR-308): lcs_signal_registry, lcs_engagement_rules, lcs_sequence_def, lcs_contact_sequence_state, lcs_contact_engagement_score, lcs_contact_channel_state, lcs_voice_library, lcs_m_registry, lcs_email_signature. CLAUDE.md Pre-Flight section updated with same. BAR references updated in Section 1. | pending |
| 2026-04-21 | Thread 2 wired email deliverability constants into the live compiler-v2 path: Mailgun Reply-To standardized to `dave@svg.agency`, domain picker now respects warmup and bounce health, voice spec bridge added from `fleet/content/VOICE-SPEC.yaml`, and Mailgun reply telemetry now maps into `MID_REPLIED`. | pending |


### Worker Fill Rule
Append every material change to the worker or its manual without deleting history.

### Cross-reference
- `law/doctrine/WORKER_FILL_INSTRUCTIONS.md` §14
- `workers/lcs-hub/wrangler.toml`
- `workers/lcs-hub/src/index.ts`

**0 -> 1 when:** the session log is append-only, dates are preserved, and material manual/build changes are recorded.

---

## Document Control

| Field | Value |
|-------|-------|
| Created | 2026-04-04 |
| Last Modified | 2026-04-04 |
| Version | 1.0.0 |
| Template Version | 1.0.0 |
| Medium | worker |
| US Validated | pending |
| Governing Engine | law/doctrine/FOUNDATIONAL_BEDROCK.md + law/doctrine/DMJ.md |
