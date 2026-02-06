# PRD: Outreach Execution Hub v4.0

**Version:** 4.0 (Constitutional Compliance)
**Status:** Active
**Constitutional Date:** 2026-01-29
**Last Updated:** 2026-01-29
**Doctrine:** IMO-Creator Constitutional Doctrine
**ADR:** ADR-011_CL_Authority_Registry_Outreach_Spine.md
**Barton ID Range:** `04.04.04.XX.XXXXX.###`

---

## Conformance

| Field | Value |
|-------|-------|
| **Doctrine Version** | IMO-Creator v1.0 |
| **Domain Spec Reference** | `doctrine/REPO_DOMAIN_SPEC.md` |
| **CC Layer** | CC-02 |
| **PRD Constitution** | `templates/doctrine/PRD_CONSTITUTION.md` |
| **CTB Governance** | `docs/CTB_GOVERNANCE.md` |

---

## 1. Sovereign Reference (CC-01)

| Field | Value |
|-------|-------|
| **Sovereign ID** | CL-01 (Company Lifecycle) |
| **Sovereign Boundary** | Company identity and lifecycle state |

---

## 2. Hub Identity (CC-02)

| Field | Value |
|-------|-------|
| **Hub Name** | Outreach Execution |
| **Hub ID** | HUB-OUTREACH |
| **Doctrine ID** | 04.04.04 |
| **Owner** | Barton Outreach Core |
| **Version** | 4.0 |
| **Waterfall Order** | 6 |
| **Classification** | Optional |

---

## 3. Purpose & Transformation Declaration

### Transformation Statement (REQUIRED)

> **"This hub transforms BIT-scored companies with filled slots (CONSTANTS) into outreach-ready campaign assignments with primary contact selection (VARIABLES) through CAPTURE (candidate intake with BIT threshold), COMPUTE (contact selection, campaign matching, cooling-off validation), and GOVERN (outreach log persistence and handoff generation)."**

| Field | Value |
|-------|-------|
| **Transformation Summary** | BIT-scored companies → Outreach-ready campaign assignments |

### Constants (Inputs)

_Immutable inputs received from outside this hub. Reference: `doctrine/REPO_DOMAIN_SPEC.md §2`_

| Constant | Source | Description |
|----------|--------|-------------|
| `outreach_id` | Outreach Spine | Operational identifier |
| `bit_score` | BIT Engine | Buyer intent score (threshold >= 50) |
| `slot_assignments` | People Intelligence | Filled slots (HR, CEO, CFO) |
| `verified_email_pattern` | Company Target | Verified email pattern |
| `company_domain` | Company Target | Validated domain |

### Variables (Outputs)

_Outputs this hub produces. Reference: `doctrine/REPO_DOMAIN_SPEC.md §3`_

| Variable | Destination | Description |
|----------|-------------|-------------|
| `campaign_assignment` | Outreach tables | Campaign and sequence assignment |
| `primary_contact` | Outreach tables | Selected primary contact |
| `outreach_log_record` | Outreach tables | Outreach promotion record |
| `calendar_link` | Handoff | Signed calendar booking link |
| `cooling_off_status` | Outreach tables | Cooling-off period status |

### Pass Structure

_Constitutional pass mapping per `PRD_CONSTITUTION.md §Pass-to-IMO Mapping`_

| Pass | Type | IMO Layer | Description |
|------|------|-----------|-------------|
| Candidate Intake | **CAPTURE** | I (Ingress) | Receive BIT-scored companies above threshold |
| Contact Selection | **COMPUTE** | M (Middle) | Select primary contact (HR > CEO > CFO) |
| Campaign Matching | **COMPUTE** | M (Middle) | Match company to campaign by industry/size |
| Cooling-Off Validation | **COMPUTE** | M (Middle) | Validate 30-day cooling-off period |
| Outreach Persistence | **GOVERN** | O (Egress) | Persist outreach log and generate handoff |

### Scope Boundary

| Scope | Description |
|-------|-------------|
| **IN SCOPE** | Candidate evaluation, contact selection, campaign assignment, cooling-off enforcement, outreach log persistence, calendar handoff |
| **OUT OF SCOPE** | BIT scoring (BIT Engine owns), slot assignment (People owns), email generation (People owns), actual email sending (external system) |

---

## CL Authority Registry + Outreach Spine (LOCKED)

```
╔═══════════════════════════════════════════════════════════════════════════════╗
║                   CL AUTHORITY REGISTRY + OUTREACH SPINE                      ║
║                                                                               ║
║   CL = AUTHORITY REGISTRY (Identity Pointers Only)                            ║
║   ──────────────────────────────────────────────────                          ║
║   cl.company_identity stores:                                                 ║
║   ├── sovereign_company_id  PK (minted by CL)                                 ║
║   ├── outreach_id           WRITE-ONCE (minted by Outreach)                   ║
║   ├── sales_process_id      WRITE-ONCE (minted by Sales)                      ║
║   └── client_id             WRITE-ONCE (minted by Client)                     ║
║                                                                               ║
║   CL does NOT store workflow state, timestamps, or operational data.          ║
║                                                                               ║
║   OUTREACH = OPERATIONAL SPINE (Workflow State)                               ║
║   ─────────────────────────────────────────────                               ║
║   outreach.outreach stores:                                                   ║
║   ├── outreach_id           PK (minted here, registered in CL)                ║
║   ├── sovereign_company_id  FK → cl.company_identity                          ║
║   ├── status                WORKFLOW STATE                                    ║
║   └── timestamps            OPERATIONAL DATA                                  ║
║                                                                               ║
╚═══════════════════════════════════════════════════════════════════════════════╝
```

## Outreach Init Pattern (LOCKED)

```python
# STEP 1: Verify company exists in CL and outreach_id is NULL
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

# STEP 4: Verify write succeeded
if affected_rows != 1:
    ROLLBACK()
    HARD_FAIL("Outreach ID already claimed or invalid SID")
```

## Outreach Hub Responsibilities (LOCKED)

```
╔═══════════════════════════════════════════════════════════════════════════════╗
║                      OUTREACH HUB RESPONSIBILITIES                            ║
║                                                                               ║
║   OUTREACH DOES:                                                              ║
║   ├── Mint outreach_id in outreach.outreach (operational spine)               ║
║   ├── Write outreach_id to CL (ONCE, guarded)                                 ║
║   ├── Generate signed calendar links (sid + oid + sig + TTL)                  ║
║   ├── Drive meetings via calendar booking                                     ║
║   └── Handoff to Sales via booking webhook (NOT direct invocation)            ║
║                                                                               ║
║   OUTREACH DOES NOT:                                                          ║
║   ├── Mint sovereign_company_id (CL owns this)                                ║
║   ├── Mint sales_process_id or client_id (those hubs own them)                ║
║   ├── Write workflow state to CL (CL = identity pointers only)                ║
║   ├── Invoke Sales or Client logic directly                                   ║
║   └── Live-sync with downstream hubs (snapshot at handoff)                    ║
║                                                                               ║
╚═══════════════════════════════════════════════════════════════════════════════╝
```

## Calendar Handoff Pattern

```
OUTREACH                                    SALES
   │                                          │
   │ ──► Generate calendar link               │
   │     https://calendar.example.com/book?   │
   │       sid=...&oid=...&sig=...            │
   │     (signed params, short TTL)           │
   │                                          │
   │ ──► Meeting booked webhook ─────────────►│
   │                                          │
   │     [OUTREACH ENDS HERE]                 │ Sales Init worker starts
   │                                          │ ├── Snapshots Outreach data
   │                                          │ ├── Mints sales_process_id
   │                                          │ └── Writes to CL (ONCE)
```

---

## Spoke Ownership Statement

```
╔═══════════════════════════════════════════════════════════════════════════════╗
║                          OUTREACH SPOKE OWNERSHIP                             ║
║                                                                               ║
║   This spoke OWNS:                                                            ║
║   ├── Outreach candidate evaluation                                           ║
║   ├── Primary contact selection (HR > CEO > CFO priority)                     ║
║   ├── BIT threshold enforcement (>= 50 for outreach)                          ║
║   ├── Cooling-off period enforcement (30-day minimum)                         ║
║   ├── Campaign assignment and tracking                                        ║
║   └── Outreach log persistence                                                ║
║                                                                               ║
║   This spoke DOES NOT OWN:                                                    ║
║   ├── Company identity (company_id, domain, email_pattern)                    ║
║   ├── BIT score calculation (that's BIT Engine)                               ║
║   ├── Email generation or verification (that's People Spoke)                  ║
║   ├── Slot assignment (that's People Spoke)                                   ║
║   ├── Signal emission (signals come FROM other spokes)                        ║
║   └── Actual email sending (that's external system - Instantly/HeyReach)      ║
║                                                                               ║
║   This spoke is the OUTPUT spoke - final decision point before sending.       ║
║                                                                               ║
║   PREREQUISITE: outreach_id + company anchor + bit_score >= 50                ║
╚═══════════════════════════════════════════════════════════════════════════════╝
```

---

## 1. Purpose

The Outreach Spoke is the **OUTPUT node** of the Barton pipeline. It evaluates companies for outreach readiness, selects the primary contact, enforces cooling-off periods, and promotes candidates to the outreach log for campaign execution.

### Core Functions

1. **Candidate Evaluation** - Check BIT threshold (>= 50), anchor slot, domain/pattern
2. **Primary Contact Selection** - Select contact with priority: HR > CEO > CFO
3. **Cooling-Off Enforcement** - Prevent over-messaging (30-day minimum between contacts)
4. **Campaign Assignment** - Assign companies to appropriate outreach campaigns
5. **Outreach Log Persistence** - Write promotion records to Neon

### The Golden Rule (OUTPUT)

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                                                                             │
│   OUTREACH CRITERIA (ALL MUST BE TRUE):                                     │
│                                                                             │
│   ✓ company_id IS NOT NULL                                                  │
│   ✓ domain IS NOT NULL                                                      │
│   ✓ email_pattern IS NOT NULL                                               │
│   ✓ bit_score >= 50 (HOT threshold)                                         │
│   ✓ has at least one filled anchor slot (HR/CEO/CFO)                        │
│   ✓ NOT in cooling-off period (>= 30 days since last contact)               │
│                                                                             │
│   IF ANY CONDITION FAILS: DO NOT PROMOTE TO OUTREACH                        │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 2. Data Flow

```
┌─────────────────┐
│   BIT Engine    │
│  (bit_score)    │
└────────┬────────┘
         │
         ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                          OUTREACH SPOKE                                      │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  1. CANDIDATE EVALUATION                                                    │
│     ├── Load companies with bit_score >= 50                                 │
│     ├── Validate company anchor (company_id, domain, email_pattern)         │
│     ├── Check anchor slot (at least HR, CEO, or CFO filled)                 │
│     └── Verify not in cooling-off period                                    │
│                                                                             │
│  2. PRIMARY CONTACT SELECTION                                               │
│     ├── Priority 1: HR slot (hr_person_id)                                  │
│     ├── Priority 2: CEO slot (ceo_person_id)                                │
│     ├── Priority 3: CFO slot (cfo_person_id)                                │
│     └── Get person data (name, email, title)                                │
│                                                                             │
│  3. CAMPAIGN ASSIGNMENT                                                     │
│     ├── Match company to campaign by industry/size                          │
│     └── Assign sequence_id                                                  │
│                                                                             │
│  4. OUTREACH LOG WRITE                                                      │
│     ├── Create outreach_log record                                          │
│     ├── Set status = 'queued'                                               │
│     └── Record correlation_id for tracing                                   │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
         │
         ▼
┌─────────────────┐
│  Outreach Log   │
│  (Neon DB)      │
└─────────────────┘
         │
         ▼
┌─────────────────┐
│ External System │
│ (Instantly/     │
│  HeyReach)      │
└─────────────────┘
```

---

## 3. Correlation ID Doctrine (HARD LAW)

```
╔═══════════════════════════════════════════════════════════════════════════════╗
║                       CORRELATION ID ENFORCEMENT                              ║
║                                                                               ║
║   DOCTRINE: correlation_id MUST be propagated unchanged across ALL processes ║
║             and into all error logs and outreach records.                     ║
║                                                                               ║
║   RULES:                                                                      ║
║   1. Every outreach evaluation MUST include correlation_id                    ║
║   2. Every outreach_log record MUST include correlation_id                    ║
║   3. Every error logged MUST include correlation_id                           ║
║   4. correlation_id MUST NOT be modified mid-processing                       ║
║                                                                               ║
║   FORMAT: UUID v4 (e.g., "550e8400-e29b-41d4-a716-446655440000")              ║
║   GENERATED BY: Company Pipeline (inherited through processing)               ║
║                                                                               ║
╚═══════════════════════════════════════════════════════════════════════════════╝
```

---

## 4. Primary Contact Selection

### Priority Order

| Priority | Slot | Rationale |
|----------|------|-----------|
| 1 | HR | Primary buyer for benefits/HR tech |
| 2 | CEO | Executive decision maker |
| 3 | CFO | Budget authority |

### Selection Algorithm

```python
def _get_primary_contact(company_id: str, company_data: Dict) -> Optional[Dict]:
    """
    Select primary contact with HR > CEO > CFO priority.
    Returns person data if found, None otherwise.
    """
    slot_priority = [
        ('hr', 'HR'),
        ('ceo', 'CEO'),
        ('cfo', 'CFO')
    ]

    for slot_key, slot_type in slot_priority:
        person_id = company_data.get(f'{slot_key}_person_id')
        if person_id:
            person_data = load_person_by_id(person_id)
            if person_data and person_data.get('email'):
                return {
                    'id': person_id,
                    'name': person_data.get('full_name'),
                    'email': person_data.get('email'),
                    'title': person_data.get('title'),
                    'slot_type': slot_type
                }

    return None  # No valid contact found
```

---

## 5. Cooling-Off Period

### Rules

```
╔═══════════════════════════════════════════════════════════════════════════════╗
║                       COOLING-OFF PERIOD ENFORCEMENT                          ║
║                                                                               ║
║   MINIMUM: 30 days between outreach attempts to same company                  ║
║                                                                               ║
║   CHECK: SELECT MAX(sent_at) FROM outreach_log                                ║
║          WHERE company_id = ? AND status IN ('sent', 'delivered')             ║
║                                                                               ║
║   IF last_contact_date + 30 days > NOW():                                     ║
║       REJECT candidate (reason: 'cooling_off')                                ║
║                                                                               ║
╚═══════════════════════════════════════════════════════════════════════════════╝
```

---

## 6. Kill Switches

| Switch | Threshold | Action |
|--------|-----------|--------|
| `daily_send_limit` | 200 emails | Halt all outreach for day |
| `hourly_send_limit` | 30 emails | Pause for 1 hour |
| `bounce_rate_ceiling` | 10% | Halt and review |
| `unsubscribe_spike` | 5% | Halt and review |

---

## 7. Outreach Log Schema

> **ERD Reference**: `hubs/outreach-execution/SCHEMA.md`

```sql
-- ERD: outreach.send_log (operational send tracking)
CREATE TABLE outreach.send_log (
    send_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    campaign_id UUID REFERENCES outreach.campaigns(campaign_id),
    sequence_id UUID REFERENCES outreach.sequences(sequence_id),
    person_id UUID REFERENCES outreach.people(person_id),
    target_id UUID REFERENCES outreach.company_target(target_id),
    company_unique_id TEXT,
    email_to VARCHAR NOT NULL,
    email_subject TEXT,
    sequence_step INTEGER NOT NULL DEFAULT 1,
    send_status VARCHAR NOT NULL DEFAULT 'pending',  -- pending, sent, delivered, opened, clicked, replied, bounced
    scheduled_at TIMESTAMPTZ,
    sent_at TIMESTAMPTZ,
    delivered_at TIMESTAMPTZ,
    bounced_at TIMESTAMPTZ,
    opened_at TIMESTAMPTZ,
    clicked_at TIMESTAMPTZ,
    replied_at TIMESTAMPTZ,
    open_count INTEGER NOT NULL DEFAULT 0,
    click_count INTEGER NOT NULL DEFAULT 0,
    error_message TEXT,
    retry_count INTEGER NOT NULL DEFAULT 0,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_send_log_campaign ON outreach.send_log(campaign_id);
CREATE INDEX idx_send_log_status ON outreach.send_log(send_status);
CREATE INDEX idx_send_log_person ON outreach.send_log(person_id);
```

---

## 8. Implementation Status

| Component | Status | File |
|-----------|--------|------|
| Outreach Spoke | ✅ Implemented | `spokes/outreach/outreach_spoke.py` |
| Primary Contact Selection | ✅ Implemented | `_get_primary_contact()` |
| BIT Threshold Check | ✅ Implemented | `process()` |
| Cooling-Off Check | ✅ Implemented | `_check_cooling_off()` |
| Neon Writer | ✅ Implemented | `hub/company/neon_writer.py` |
| Outreach Log Schema | ✅ Defined | Above |
| Kill Switches | ✅ Defined | `tests/dry_run_orchestrator.py` |

---

## 9. Dependencies

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                          OUTREACH SPOKE DEPENDENCIES                        │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│   REQUIRED FROM COMPANY HUB:                                                │
│   ├── company_id (valid anchor)                                             │
│   ├── domain (for email generation)                                         │
│   └── email_pattern (for email generation)                                  │
│                                                                             │
│   REQUIRED FROM PEOPLE SPOKE:                                               │
│   ├── hr_person_id, ceo_person_id, cfo_person_id (slot assignments)         │
│   └── Person records with verified emails                                   │
│                                                                             │
│   REQUIRED FROM BIT ENGINE:                                                 │
│   └── bit_score >= 50 (HOT threshold)                                       │
│                                                                             │
│   EXTERNAL DEPENDENCIES:                                                    │
│   ├── Instantly API (for email sending)                                     │
│   └── HeyReach API (for LinkedIn outreach)                                  │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 10. Metrics & KPIs

| Metric | Target | Tracking |
|--------|--------|----------|
| Candidates Evaluated | 100% of HOT companies | Daily |
| Pass Rate | > 80% | Daily |
| Bounce Rate | < 5% | Per campaign |
| Open Rate | > 20% | Per campaign |
| Reply Rate | > 3% | Per campaign |

---

## 11. Database Schema (HARDENED 2026-01-13)

### Schema: `outreach`

| Table | Purpose | RLS Enabled |
|-------|---------|-------------|
| `company_target` | Company anchor records | Yes |
| `people` | Contact/executive data | Yes |
| `engagement_events` | Immutable event log | Yes (+ DELETE blocked) |
| `campaigns` | Campaign definitions | Yes |
| `sequences` | Multi-touch steps | Yes |
| `send_log` | Delivery tracking | Yes |

### RLS Roles

| Role | Permissions |
|------|-------------|
| `outreach_hub_writer` | SELECT, INSERT, UPDATE on outreach.* |
| `hub_reader` | SELECT only on outreach.* |

### Immutability Enforcement

```sql
-- engagement_events DELETE blocked at trigger level
CREATE TRIGGER trg_engagement_events_immutability_delete
    BEFORE DELETE ON outreach.engagement_events
    FOR EACH ROW
    EXECUTE FUNCTION outreach.fn_engagement_events_immutability();
```

### Migration Reference

```
infra/migrations/2026-01-13-outreach-execution-complete.sql
infra/migrations/2026-01-13-enable-rls-production-tables.sql
```

See `infra/MIGRATION_ORDER.md` for execution order.

---

## 12. Version History

| Version | Date | Changes |
|---------|------|---------|
| 2.0 | 2025-12-19 | Initial Outreach Spoke PRD |
| 2.1 | 2025-12-19 | Hardened: Primary contact selection, BIT threshold, cooling-off |
| 2.2 | 2026-01-13 | Execution tables created (campaigns, sequences, send_log), RLS enabled |
| 3.0 | 2026-01-22 | CL Authority Registry + Outreach Spine clarification, calendar handoff pattern |

---

**Last Updated:** 2026-01-22
**Author:** Claude Code
**Approved By:** Barton Doctrine
**Doctrine:** CL Authority Registry + Outreach Operational Spine
**ADR:** ADR-011_CL_Authority_Registry_Outreach_Spine.md
