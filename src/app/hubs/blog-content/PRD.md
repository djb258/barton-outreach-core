# PRD — Hub

## Conformance

| Field | Value |
|-------|-------|
| **Doctrine Version** | 1.1.0 |
| **CTB Version** | 1.0.0 |
| **CC Layer** | CC-02 |

---

## 1. Sovereign Reference (CC-01)

| Field | Value |
|-------|-------|
| **Sovereign ID** | barton-enterprises |
| **Sovereign Boundary** | Marketing intelligence and executive enrichment operations |

---

## 2. Hub Identity (CC-02)

| Field | Value |
|-------|-------|
| **Hub Name** | Blog Content |
| **Hub ID** | HUB-BLOG-001 |
| **Owner** | Outreach Team |
| **Version** | 1.0.0 |

---

## 3. Purpose

Provide **timing signals** from news, funding events, and content sources. BIT modulation only — cannot mint, revive, or trigger enrichment. FINAL hub in waterfall — context is finalized after this hub.

**Waterfall Position**: 4th (LAST) sub-hub in canonical waterfall (after People Intelligence).

---

## 3.1 Scope Lock (DOCTRINE LOCK)

> **The Blog Sub-Hub records *where* a company publishes, not *how large* the audience is.**

### Company-Level Only

The Blog Sub-Hub operates **exclusively at the company level**. It captures company-owned digital presence surfaces for **presence verification and timing signals only**.

### Social Platform Treatment

Social platforms (X/Twitter, Instagram, LinkedIn, YouTube, TikTok, etc.) are treated as:
- **Company-owned distribution surfaces**
- Captured for **presence + verification only**
- Used to detect timing signals (funding announcements, leadership changes, etc.)

### Explicitly Prohibited (HARD LAW)

The following are **permanently forbidden** in Blog Sub-Hub:

| Category | Forbidden Fields |
|----------|-----------------|
| **Audience Metrics** | `followers`, `follower_count`, `following`, `subscribers` |
| **Engagement Metrics** | `likes`, `views`, `comments`, `shares`, `retweets`, `impressions` |
| **Computed Scores** | `engagement_rate`, `engagement_score`, `reach`, `sentiment`, `sentiment_score` |
| **Post Analytics** | `post_frequency`, `avg_engagement`, `virality_score` |
| **People-Level Data** | Individual follower lists, commenter profiles, engagement by person |

### Enforcement

```
DISALLOW_SOCIAL_METRICS = True
```

CI will **FAIL** if any forbidden field patterns appear in Blog code.

### What Blog Sub-Hub DOES

- Records that a company has a LinkedIn page (presence)
- Detects funding announcements posted on social platforms (timing signal)
- Classifies events from company press releases and news

### What Blog Sub-Hub DOES NOT DO

- Count followers or subscribers
- Measure engagement rates or reach
- Analyze sentiment on comments
- Track post frequency or performance
- Store any people-level social data

---

## 4. CTB Placement

| Field | Value | CC Layer |
|-------|-------|----------|
| **Trunk** | sys | CC-02 |
| **Branch** | outreach | CC-02 |
| **Leaf** | blog-content | CC-02 |

---

## 5. IMO Structure (CC-02)

| Layer | Role | Description | CC Layer |
|-------|------|-------------|----------|
| **I — Ingress** | Dumb input only | Receives outreach_id, slot_assignments from People; news feeds | CC-02 |
| **M — Middle** | Logic, decisions, state | Signal processing, BIT modulation | CC-02 |
| **O — Egress** | Output only | Emits timing_signals to BIT Engine | CC-02 |

---

## 6. Spokes (CC-03 Interfaces)

| Spoke Name | Type | Direction | Contract | CC Layer |
|------------|------|-----------|----------|----------|
| company-blog | I | Inbound | outreach_id, domain | CC-03 |
| dol-blog | I | Inbound | outreach_id, regulatory_data | CC-03 |
| people-blog | I | Inbound | outreach_id, slot_assignments | CC-03 |
| blog-bit | O | Outbound | outreach_id, timing_signals | CC-03 |

---

## 7. Constants vs Variables

| Element | Type | Mutability | CC Layer |
|---------|------|------------|----------|
| Hub ID | Constant | Immutable | CC-02 |
| Hub Name | Constant | ADR-gated | CC-02 |
| Doctrine ID (04.04.05) | Constant | Immutable | CC-02 |
| CTB Placement | Constant | ADR-gated | CC-02 |
| Primary Table | Constant | ADR-gated | CC-02 |
| Signal Types | Constant | ADR-gated | CC-02 |
| BIT Impact Values | Constant | ADR-gated | CC-02 |
| outreach_id | Variable | Runtime | CC-04 |
| timing_signals | Variable | Runtime (from feeds) | CC-04 |

---

## 8. Tools

| Tool | Solution Type | CC Layer | IMO Layer | ADR Reference |
|------|---------------|----------|-----------|---------------|
| News Feed Parser | Deterministic | CC-02 | M | N/A (Free) |
| Signal Classifier | Deterministic | CC-02 | M | N/A (Local) |

---

## 9. Guard Rails

| Guard Rail | Type | Threshold | CC Layer |
|------------|------|-----------|----------|
| People Intelligence PASS | Validation | MUST have upstream PASS | CC-03 |
| No paid tools | Validation | Free signals only | CC-03 |
| No enrichment trigger | Validation | Timing signals only | CC-03 |
| No company minting | Validation | MUST NOT mint or revive | CC-03 |

---

## 10. Kill Switch

| Field | Value |
|-------|-------|
| **Activation Criteria** | People Intelligence not PASS |
| **Trigger Authority** | CC-02 (Hub) |
| **Emergency Contact** | Outreach Team |

---

## 11. Promotion Gates

| Gate | Artifact | CC Layer | Requirement |
|------|----------|----------|-------------|
| G1 | PRD | CC-02 | Hub definition approved |
| G2 | ADR | CC-03 | Architecture decision recorded |
| G3 | Work Item | CC-04 | Execution item created |
| G4 | PR | CC-04 | Code reviewed and merged |
| G5 | Checklist | CC-04 | Compliance verification complete |

---

## 12. Failure Modes

| Failure | Severity | CC Layer | Remediation |
|---------|----------|----------|-------------|
| Upstream hub not PASS | CRITICAL | CC-03 | STOP - upstream dependency |
| Feed parse error | LOW | CC-04 | Log warning, continue |
| Signal classification fails | LOW | CC-04 | Default to no BIT impact |
| Context finalization fails | HIGH | CC-04 | Log error, mark context FAIL |

---

## 12.1 Error Handling Discipline (DOCTRINE LOCK)

### First-Class Error Outputs

Errors are **first-class outputs**, not hidden logging. Every failure MUST be persisted to `outreach.blog_errors`.

```
ENFORCE_ERROR_PERSISTENCE = True
```

### Error Table Schema

| Column | Type | Required | Description |
|--------|------|----------|-------------|
| error_id | UUID | PK | Primary key |
| outreach_id | UUID | FK | Spine anchor |
| pipeline_stage | VARCHAR | Yes | ingest, parse, classify, write, emit |
| failure_code | VARCHAR | Yes | BLOG-XXX code |
| blocking_reason | TEXT | Yes | Human-readable |
| severity | VARCHAR | Yes | INFO, WARN, ERROR, FATAL |
| retry_allowed | BOOLEAN | Yes | Always FALSE |
| process_id | UUID | Yes | Traceability |
| raw_input | JSONB | No | Original payload |
| stack_trace | TEXT | No | Exception trace |
| created_at | TIMESTAMPTZ | Yes | When recorded |

### Error Codes

| Code | Stage | Description |
|------|-------|-------------|
| BLOG-I-NO-OUTREACH | ingest | No outreach_id provided |
| BLOG-I-NOT-FOUND | ingest | outreach_id not in spine |
| BLOG-I-NO-DOMAIN | ingest | No domain in spine |
| BLOG-I-UPSTREAM-FAIL | ingest | CT not PASS |
| BLOG-I-ALREADY-PROCESSED | ingest | Idempotent skip |
| BLOG-M-CLASSIFY-FAIL | classify | Classification failed |
| BLOG-O-WRITE-FAIL | write | Neon write failed |

### No Silent Failures

- CI Guard 13: Verifies `ENFORCE_ERROR_PERSISTENCE` assertion
- CI Guard 14: Verifies `blog_errors` references exist
- CI Guard 15: Checks for print statements bypassing persistence

---

## 13. PID Scope (CC-04)

| Field | Value |
|-------|-------|
| **PID Pattern** | `HUB-BC-{TIMESTAMP}-{RANDOM_HEX}` |
| **Retry Policy** | New PID per retry |
| **Audit Trail** | Required |

---

## 14. Human Override Rules

Override requires CC-02 (Hub Owner) or CC-01 (Sovereign) approval:
- Manual signal injection for known events
- Force context finalization despite feed errors
- Adjust BIT impact values for specific signals

---

## 15. Observability

| Type | Description | CC Layer |
|------|-------------|----------|
| **Logs** | Feed processing, signal emissions, context finalization | CC-04 |
| **Metrics** | SIGNAL_COVERAGE, signals_per_company, BIT_modulation_rate | CC-04 |
| **Alerts** | Feed unavailable, context finalization failures | CC-03/CC-04 |

---

## Approval

| Role | Name | Date |
|------|------|------|
| Sovereign (CC-01) | | |
| Hub Owner (CC-02) | | |
| Reviewer | | |

---

## Traceability

| Artifact | Reference |
|----------|-----------|
| Canonical Doctrine | CANONICAL_ARCHITECTURE_DOCTRINE.md |
| Hub/Spoke Doctrine | HUB_SPOKE_ARCHITECTURE.md |
