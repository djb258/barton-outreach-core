# Content Pages
## Serves NotebookLM-generated education content as branded web pages with 9 configurable media slots.
### Status: BUILD
### Medium: worker
### Business: svg-agency

---

# IDENTITY (Thing — what this IS)

_Everything in this cluster answers: what exists? These are constants that don't change regardless of who reads this or when._

## 1. IDENTITY

| Field | Value |
|-------|-------|
| ID | content-pages |
| Name | Content Pages |
| Medium | worker |
| Business Silo | svg-agency |
| CTB Position | leaf -> workers/content-pages |
| ORBT | BUILD |
| Strikes | 0 |
| Authority | inherited — imo-creator |
| Last Modified | 2026-04-04 |
| BAR Reference | none |

### HEIR (8 fields — Aviation Model, Bedrock S8)

| Field | Value |
|-------|-------|
| sovereign_ref | imo-creator |
| hub_id | content-pages |
| ctb_placement | leaf |
| imo_topology | output |
| cc_layer | CC-03 context |
| services | Cloudflare Pages, CF Stream |
| secrets_provider | none |
| acceptance_criteria | Pages build succeeds, all 9 slots render when configured, CF Stream video plays |


### Worker Fill Rule
Identity must match the real worker and sit at `leaf -> workers/<name>`.

### Cross-reference
- `law/doctrine/WORKER_FILL_INSTRUCTIONS.md` §1
- `workers/content-pages/wrangler.toml`
- `workers/content-pages/MANUAL.md`

**0 -> 1 when:** ID/name/medium/HEIR match the worker, `ctb_placement = leaf`, and bindings/services are not overstated.

---

## 2. PURPOSE

_What breaks without it. What business outcome it serves. If you can't answer this, it shouldn't exist._

Content Pages is the public-facing delivery layer for NotebookLM-generated education content. Without it, the 5500 compliance training (video, audio, slides, infographic, quiz, flashcards, mindmap, datatable, report) has no web presence. Downstream sales meetings and client education depend on these pages existing at branded URLs.


### Worker Fill Rule
State the worker's business outcome, who starves without it, and the operational risk if it fails.

### Cross-reference
- `law/doctrine/WORKER_FILL_INSTRUCTIONS.md` §2
- `workers/content-pages/wrangler.toml`
- `workers/content-pages/MANUAL.md`

**0 -> 1 when:** purpose is business-level, names downstream consumers, and avoids collapsing into route detail.

---

## 3. RESOURCES

_Everything this depends on. A mechanic reads this and knows exactly what to set up before it can run._

### Dependencies

| Dependency | Type | What It Provides | Status |
|-----------|------|-----------------|--------|
| Cloudflare Pages | service | Static hosting via pages_build_output_dir=./dist | DONE |
| CF Stream | service | Video playback (streamId-based embed) | DONE |
| Vite | build tool | React + TypeScript bundling | DONE |
| NotebookLM | content source | Raw education artifacts (audio, slides, etc.) | DONE |

### Downstream Consumers

| Consumer | What It Needs |
|----------|--------------|
| Sales Portal (900) | Links to education content pages |
| Client Portal (830) | Embedded education resources |
| Marketing | Public URLs for content distribution |

### Tools & Integrations (if applicable)

| Item | Type | Cost Tier | Credentials | What It Does |
|------|------|-----------|-------------|-------------|
| CF Stream | video hosting | Free (included) | none | Serves video by streamId |

### Secrets (if applicable)

None.


### Worker Fill Rule
Inventory every binding class, secret, trigger, upstream dependency, and downstream consumer; absent classes must be explicit `none`.

### Cross-reference
- `law/doctrine/WORKER_FILL_INSTRUCTIONS.md` §3
- `workers/content-pages/wrangler.toml`
- `workers/content-pages/MANUAL.md`

**0 -> 1 when:** resources agree with the local worker config and no binding class is silently omitted.

---

# CONTRACT (Flow — what flows through this)

_Everything in this cluster answers: what moves? How does data/work enter, get processed, and exit?_

## 4. IMO — Input, Middle, Output

### Two-Question Intake (Bedrock S3)
1. **"What triggers this?"** — A browser request to the Pages URL
2. **"How do we get it?"** — CF Pages serves the Vite-built static bundle

### Input
NotebookLM artifacts configured as a ContentConfig object in App.tsx. Each config specifies brand, title, and up to 9 media slots (video, audio, slides, report, infographic, quiz, flashcards, mindmap, datatable).

### Middle

| Step | Input | What Happens | Output | Tool Used |
|------|-------|-------------|--------|-----------|
| 1 | ContentConfig object | Vite builds React app with slot components | Static HTML/JS/CSS in ./dist | Vite |
| 2 | Browser request | CF Pages serves built assets | Rendered page | Cloudflare Pages |
| 3 | Video slot present | CF Stream embed renders in-page | Playable video | CF Stream |

_For workers: the Middle is the request-process-response cycle._

### Output
Branded web page with education content rendered across active slots. Empty slots are hidden automatically.

### Circle (Bedrock S5)
User engagement on content pages feeds back into sales meeting prep (900) and client education tracking. Content gaps identified during sales meetings trigger new NotebookLM artifact generation.


### Worker Fill Rule
Document the worker as trigger/request -> process -> response, with worker code as hub and routes/triggers as spokes.

### Cross-reference
- `law/doctrine/WORKER_FILL_INSTRUCTIONS.md` §4
- `workers/content-pages/wrangler.toml`
- `workers/content-pages/MANUAL.md`

**0 -> 1 when:** Two-Question Intake, Input, Middle, Output, and Circle are explicit and match the real triggers/handlers.

---

## 5. DATA SCHEMA

_Where the data lives. What's read, written, joined. The plumbing._

### READ Access

| Source | What It Provides | Join Key |
|--------|-----------------|----------|
| ContentConfig (App.tsx) | Media slot configuration | brand + title |
| CF Stream | Video content | streamId |
| /content/* static files | Audio, slides, infographics | file path |

### WRITE Access

| Target | What It Writes | When |
|--------|---------------|------|
| ./dist (build output) | Static HTML/JS/CSS | At build time |

### Join Chain

```
ContentConfig
  -> CF Stream (streamId)
  -> Static assets (/content/*)
```

### Forbidden Paths

| Action | Why |
|--------|-----|
| Direct database writes | This is a static content worker — no D1/Neon bindings |
| Runtime content modification | Content is build-time only — deploy to change |


### Worker Fill Rule
Name every read path, write path, join chain, CQRS pair, and forbidden path for the worker.

### Cross-reference
- `law/doctrine/WORKER_FILL_INSTRUCTIONS.md` §5
- `workers/content-pages/wrangler.toml`
- `workers/content-pages/MANUAL.md`

**0 -> 1 when:** schema/plumbing matches the worker's real bindings or explicitly notes when a local binding file is absent.

---

## 6. DMJ — Define, Map, Join (law/doctrine/DMJ.md)

_Three steps. In order. Can't skip._

### 6a. DEFINE (Build the Key)

| Element | ID | Format | Description | C or V |
|---------|-----|--------|-------------|--------|
| Brand | brand | 'svg' or 'weewee' | Which brand theme to apply | C |
| Slot structure | ContentConfig | TypeScript interface | 9 named slots with typed shapes | C |
| Slot content | video.streamId, audio.src, etc. | string values | Actual media references | V |
| Page title | title | string | Display title for the content page | V |

### 6b. MAP (Connect Key to Structure)

| Source | Target | Transform |
|--------|--------|-----------|
| ContentConfig.video.streamId | CF Stream embed | direct |
| ContentConfig.audio.src | HTML5 audio player | direct |
| ContentConfig.slides.src | PDF embed/download | direct |

### 6c. JOIN (Path to Spine)

| Join Path | Type | Description |
|-----------|------|-------------|
| content-pages -> sales-portal-900 | indirect | Links from sales meeting pages |
| content-pages -> client-portal-830 | indirect | Embedded in client views |


### Worker Fill Rule
Every element must be defined with ID + format + C/V, mapped to a structural target, and joined back to the worker spine or sovereign trunk.

### Cross-reference
- `law/doctrine/WORKER_FILL_INSTRUCTIONS.md` §6
- `workers/content-pages/wrangler.toml`
- `workers/content-pages/MANUAL.md`

**0 -> 1 when:** every defined element is mapped and every join path closes without orphaned worker elements.

---

## 7. CONSTANTS & VARIABLES (Bedrock S2)

### Constants (structure — never changes)
- ContentConfig interface (9 slots: video, audio, slides, report, infographic, quiz, flashcards, mindmap, datatable)
- Slot component rendering logic (empty = hidden)
- Brand themes ('svg', 'weewee')
- Vite build pipeline (React + TypeScript)

### Variables (fill — changes every run/cycle)
- Specific content per topic (streamId, file paths, quiz questions)
- Page title and description text
- Which slots are active per page


### Worker Fill Rule
Separate worker architecture/constants from runtime fill and state the guard rails on variables.

### Cross-reference
- `law/doctrine/WORKER_FILL_INSTRUCTIONS.md` §7
- `workers/content-pages/wrangler.toml`
- `workers/content-pages/MANUAL.md`

**0 -> 1 when:** constants and variables are clearly separated and no structural element is left unclassified.

---

## 8. STOP CONDITIONS (Bedrock S6)

| Condition | Action |
|-----------|--------|
| CF Stream video ID invalid | HALT — verify streamId exists |
| Static asset 404 | HALT — check /content/* paths |
| Vite build fails | HALT — fix TypeScript errors |
| ContentConfig missing required fields | HALT — brand and title are required |


### Worker Fill Rule
Include intake failure, repeated failure, strike escalation, and human stop conditions specific to this worker.

### Cross-reference
- `law/doctrine/WORKER_FILL_INSTRUCTIONS.md` §8
- `workers/content-pages/wrangler.toml`
- `workers/content-pages/MANUAL.md`

**0 -> 1 when:** at least four deterministic stop conditions are present, including intake failure, repeated failure, strike escalation, and human stop/confirmation.

---

# GOVERNANCE (Change — how this is controlled)

_Everything in this cluster answers: what transforms? How is quality measured, verified, certified?_

## 9. VERIFICATION

_Executable proof that it works. Run these._

```
1. npm run build → expected: ./dist directory created with index.html
2. Open dist/index.html locally → expected: page renders with configured slots
3. CF Stream embed loads → expected: video plays without CORS errors
4. Empty slot check → expected: unconfigured slots are hidden, not broken
```

**Three Primitives Check (Bedrock S1):**
1. **Thing:** Does the ContentConfig exist with valid slot definitions?
2. **Flow:** Does the Vite build produce deployable assets?
3. **Change:** Does the page render all configured slots correctly?


### Worker Fill Rule
Verification must be runnable against the worker's actual routes, bindings, and state transitions.

### Cross-reference
- `law/doctrine/WORKER_FILL_INSTRUCTIONS.md` §9
- `workers/content-pages/wrangler.toml`
- `workers/content-pages/MANUAL.md`

**0 -> 1 when:** at least three tests are runnable as written and Thing/Flow/Change correspond to real worker existence, flow, and state change.

---

## 10. ANALYTICS

_The BUILD-OPERATE gate. Three sub-layers._

### 10a. Metrics

_Define BEFORE build starts._

| Metric | Unit | Baseline | Target | Tolerance |
|--------|------|----------|--------|-----------|
| Build time | seconds | BASELINE | <30s | +/- 10s |
| Page load time | seconds | BASELINE | <3s | +/- 1s |
| Slot render success | percentage | BASELINE | 100% | 0% tolerance |

### 10b. Sigma Tracking (Bedrock S2)

| Metric | Run 1 | Run 2 | Run 3 | Trend | Action |
|--------|-------|-------|-------|-------|--------|
| Build time | — | — | — | PENDING | First deployment needed |

### 10c. ORBT Gate Rules

| From | To | Gate |
|------|-----|------|
| BUILD | OPERATE | All 9 slots tested, CF Stream verified, 3 successful builds + auditor sign-off |
| OPERATE | REPAIR | Any slot rendering failure or Stream embed broken |
| REPAIR | OPERATE | Fix + all slots verified + auditor sign-off |
| Any (Strike 3) | TROUBLESHOOT/TRAIN | Fleet-wide fix -> AD |


### Worker Fill Rule
Metrics must be measurable for this worker, sigma must follow Bedrock semantics, and BUILD -> OPERATE gates must name the owner.

### Cross-reference
- `law/doctrine/WORKER_FILL_INSTRUCTIONS.md` §10
- `workers/content-pages/wrangler.toml`
- `workers/content-pages/MANUAL.md`

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
- `workers/content-pages/wrangler.toml`
- `workers/content-pages/MANUAL.md`

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
| action | Certified — airworthiness confirmed |
| gates_passed | { imo: true, ctb: true, circle: true } |
| signed_by | Auditor (different engine than builder) |
| signed_at | timestamp |


### Worker Fill Rule
During BUILD, keep certification fields pending; after audit, this becomes the legal identity of the worker manual.

### Cross-reference
- `law/doctrine/WORKER_FILL_INSTRUCTIONS.md` §12
- `workers/content-pages/wrangler.toml`
- `workers/content-pages/MANUAL.md`

**0 -> 1 when:** BUILD state is honest and no fake OPERATE claim appears before sign-off.

---

## 13. FLEET FAILURE REGISTRY

| Pattern ID | Location | Error Code | First Seen | Occurrences | Strike Count | Status |
|-----------|----------|-----------|-----------|-------------|-------------|--------|
| — | — | — | — | — | — | — |

**Strike 1:** Repair. **Strike 2:** Scrutiny. **Strike 3:** Troubleshoot/Train -> Airworthiness Directive.


### Worker Fill Rule
Log repeated worker-specific failure patterns with strike counts and AD status where applicable.

### Cross-reference
- `law/doctrine/WORKER_FILL_INSTRUCTIONS.md` §13
- `workers/content-pages/wrangler.toml`
- `workers/content-pages/MANUAL.md`

**0 -> 1 when:** failure patterns are tracked with strike counts, status, and explanatory notes, including strike-3 escalation.

---

## 14. SESSION LOG

| Date | What Was Done | LBB Record |
|------|---------------|-----------|
| 2026-04-04 | Initial MANUAL.md created from wrangler.toml + source analysis | pending |


### Worker Fill Rule
Append every material change to the worker or its manual without deleting history.

### Cross-reference
- `law/doctrine/WORKER_FILL_INSTRUCTIONS.md` §14
- `workers/content-pages/wrangler.toml`
- `workers/content-pages/MANUAL.md`

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
