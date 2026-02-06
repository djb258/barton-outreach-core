# Outreach Operational Spine Doctrine

**Status**: LOCAL EXTENSION
**Authority**: barton-outreach-core (extends IMO-Creator)
**Version**: 1.0.0
**Last Updated**: 2026-02-05

---

## Purpose

This doctrine defines the Outreach Operational Spine — the central workflow table that all sub-hubs join to via `outreach_id`.

---

## Operational Spine Definition

The **operational spine** is `outreach.outreach`. It:
- Owns workflow state for the Outreach hub
- Provides the universal join key (`outreach_id`) for all sub-hubs
- Tracks operational timestamps and status

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    OUTREACH OPERATIONAL SPINE                                │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  outreach.outreach (SPINE TABLE)                                             │
│  ───────────────────────────────                                             │
│  outreach_id            PK (minted here, registered in CL)                   │
│  sovereign_company_id   FK → cl.company_identity                             │
│  status                 WORKFLOW STATE                                       │
│  created_at             Operational timestamp                                │
│  updated_at             Operational timestamp                                │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Universal Join Key

All sub-hub tables MUST join to the spine via `outreach_id`:

| Sub-Hub | Table | Join Column |
|---------|-------|-------------|
| Company Target | `outreach.company_target` | `outreach_id` FK |
| People Intelligence | `outreach.people` | `outreach_id` FK |
| DOL Filings | `outreach.dol` | `outreach_id` FK |
| Blog Content | `outreach.blog` | `outreach_id` FK |
| BIT Scores | `outreach.bit_scores` | `outreach_id` FK |

---

## Spine vs Registry

| Aspect | CL Authority Registry | Outreach Spine |
|--------|----------------------|----------------|
| **Purpose** | Identity pointers | Workflow state |
| **Table** | `cl.company_identity` | `outreach.outreach` |
| **Primary Key** | `sovereign_company_id` | `outreach_id` |
| **State Stored** | Which hubs claimed | Current workflow status |
| **Writes** | WRITE-ONCE per hub | Continuous updates |

---

## Outreach Init Pattern

When initializing a new company for outreach:

```python
# STEP 1: Verify company exists in CL and is unclaimed
SELECT sovereign_company_id FROM cl.company_identity
WHERE sovereign_company_id = $sid
  AND outreach_id IS NULL;

# STEP 2: Mint outreach_id in operational spine
INSERT INTO outreach.outreach (outreach_id, sovereign_company_id, status)
VALUES ($new_outreach_id, $sid, 'INIT');

# STEP 3: Register outreach_id in CL authority registry (WRITE-ONCE)
UPDATE cl.company_identity
SET outreach_id = $new_outreach_id
WHERE sovereign_company_id = $sid
  AND outreach_id IS NULL;

# STEP 4: Verify registration succeeded
if affected_rows != 1:
    ROLLBACK()
    HARD_FAIL("Outreach ID already claimed or invalid SID")
```

---

## Waterfall Order

Sub-hubs execute in waterfall order, each requiring the previous to PASS:

| Order | Sub-Hub | Doctrine ID | Must PASS Before |
|-------|---------|-------------|------------------|
| 1 | Company Target | 04.04.01 | People Intelligence |
| 2 | DOL Filings | 04.04.03 | People Intelligence |
| 3 | People Intelligence | 04.04.02 | Outreach Execution |
| 4 | Blog Content | 04.04.05 | (parallel) |
| 5 | Outreach Execution | 04.04.04 | Handoff |

---

## Data Ownership

| Location | Stores | Examples |
|----------|--------|----------|
| `outreach.outreach` | Spine + workflow state | status, timestamps |
| `outreach.company_target` | Company targeting | domain, email_method |
| `outreach.people` | Contact records | name, email, slot_type |
| `outreach.dol` | DOL filing data | EIN, form_5500 |
| `outreach.blog` | Content signals | about_url, news_url |
| `outreach.bit_scores` | BIT engine output | score, tier |

---

## Sub-Hub Rules

| Rule | Enforcement |
|------|-------------|
| No sub-hub writes without valid `outreach_id` | FK constraint |
| Each sub-hub must PASS before next executes | Gate validation |
| No lateral reads between sub-hubs | Spoke contracts only |
| Data flows FORWARD ONLY | Bound by `outreach_id` |
| Sub-hubs may re-run if upstream unchanged | Idempotent design |

---

## Handoff Pattern

Outreach ends at meeting booking. Sales takes over:

```
OUTREACH                                    SALES
   │                                          │
   │ ──► Generate calendar link               │
   │     (signed: sid + oid + sig + TTL)      │
   │                                          │
   │ ──► Meeting booked webhook ─────────────►│
   │                                          │
   │     [OUTREACH ENDS HERE]                 │ Sales Init worker
   │                                          │ (snapshots Outreach data)
   │                                          │ Mints sales_process_id
   │                                          │ Writes to CL (ONCE)
```

---

## Enforcement

This doctrine is enforced by:
- `ops/enforcement/hub_gate.py` — Golden Rule validation
- `ops/enforcement/schema_guard.py` — Cross-hub isolation
- FK constraints on all sub-hub tables
- OSAM query routing (`doctrine/OSAM.md`)

---

## Traceability

| Document | Reference |
|----------|-----------|
| Parent Doctrine | CONSTITUTION.md |
| Authority Registry | doctrine/CL_AUTHORITY_DOCTRINE.md |
| OSAM | doctrine/OSAM.md |
| Domain Spec | doctrine/REPO_DOMAIN_SPEC.md |
| CLAUDE.md | §Outreach Operational Spine |

---

## Document Control

| Field | Value |
|-------|-------|
| Created | 2026-02-05 |
| Type | LOCAL EXTENSION |
| Status | ACTIVE |
| Change Protocol | ADR required |
