# DOL Subhub — EIN Resolution Spoke
## Barton Doctrine Framework | SVG-PLE Marketing Core

**Document ID**: `01.04.02.04.22000.001`
**Version**: 2.0.0
**Last Updated**: 2025-01-01
**Altitude**: 20,000 ft (Category / Spoke Layer)
**Role**: EIN Resolution Spoke — Links EIN to Sovereign Company Identity
**Status**: Active | Production Ready

---

## Document Overview

This doctrine defines the **DOL Subhub — EIN Resolution Spoke**, whose **sole responsibility** is to **link Employer Identification Numbers (EIN) to existing sovereign company identities** using authoritative **DOL / EBSA filings**.

**CRITICAL**: This spoke emits **facts only**. It does NOT:
- Assign buyer intent scores
- Trigger outreach campaigns
- Detect compliance violations as signals
- Enrich people or contacts
- Infer anything beyond EIN ↔ company linkage

---

## Section 1: Explicit Scope Definition

### ✅ What This Spoke DOES

| Function | Description |
|----------|-------------|
| **EIN Resolution** | Link EIN numbers to `company_unique_id` |
| **Source Verification** | Validate authoritative DOL/EBSA filings |
| **Identity Gating** | FAIL HARD if identity requirements not met |
| **Audit Logging** | Log ALL events to AIR (success and failure) |
| **Append-Only Storage** | No updates, no overwrites, no rescans |

### ❌ What This Spoke Does NOT Do (EXPLICIT NON-GOALS)

| Removed Function | Previous Reference | Status |
|------------------|-------------------|--------|
| Buyer Intent Scoring | BIT integration | **REMOVED** |
| BIT Event Creation | `dol_violation` → BIT events | **REMOVED** |
| OSHA Citations | Compliance Monitor scope | **REMOVED** |
| EEOC Complaints | Compliance Monitor scope | **REMOVED** |
| Slack Alerts | Outreach automation | **REMOVED** |
| Salesforce Sync | CRM integration | **REMOVED** |
| Grafana Dashboards | Monitoring | **REMOVED** |
| Outreach Triggers | Wheel Rim integration | **REMOVED** |
| People Enrichment | Contact data | **REMOVED** |

**Downstream systems MAY consume the EIN ↔ company linkage, but they MAY NOT influence this spoke.**

---

## Section 2: Hard Identity Gating (FAIL HARD)

Before **ANY** DOL interaction, the following identity gate MUST pass:

### Required Fields (ALL MANDATORY)

| Field | Type | Description |
|-------|------|-------------|
| `company_unique_id` | VARCHAR(50) | Sovereign, immutable company identifier |
| `outreach_context_id` | VARCHAR(100) | Context tracking per HEIR doctrine |
| `state` | VARCHAR(2) | US state code |

### Required Identity Anchors (AT LEAST ONE)

| Anchor | Description |
|--------|-------------|
| `company_domain` | Company website domain (e.g., `example.com`) |
| `linkedin_company_url` | LinkedIn company page URL |

### Gate Failure Behavior

If **ANY** requirement is missing:

```
1. ABORT immediately
2. Log AIR event (IDENTITY_GATE_FAILED)
3. Do NOT scrape
4. Do NOT query
5. Do NOT retry
6. Do NOT infer
```

**There are NO fallbacks. There are NO retries. Silence = FAIL.**

---

## Section 3: Data Model

### Table: `dol.ein_linkage` (APPEND-ONLY)

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `linkage_id` | VARCHAR(50) | PK, auto-generated | Barton ID: `01.04.02.04.22000.###` |
| `company_unique_id` | VARCHAR(50) | FK, IMMUTABLE | Sovereign company identifier |
| `ein` | VARCHAR(10) | NOT NULL, FORMAT CHECK | Format: `XX-XXXXXXX` |
| `source` | VARCHAR(50) | NOT NULL, ENUM | `DOL_FORM_5500`, `EBSA_FILING`, etc. |
| `source_url` | TEXT | NOT NULL | Direct URL to authoritative filing |
| `filing_year` | INTEGER | NOT NULL, RANGE CHECK | Year of DOL/EBSA filing |
| `hash_fingerprint` | VARCHAR(64) | NOT NULL, SHA-256 | Document integrity hash |
| `created_at` | TIMESTAMPTZ | NOT NULL | Immutable creation timestamp |
| `outreach_context_id` | VARCHAR(100) | NOT NULL | Required context ID |

### Immutability Rules

| Rule | Enforcement |
|------|-------------|
| No Updates | Trigger: `trg_block_ein_linkage_update` → RAISE EXCEPTION |
| No Deletes | Trigger: `trg_block_ein_linkage_delete` → RAISE EXCEPTION |
| No Overwrites | UNIQUE constraint on `(company_unique_id, ein)` |
| One EIN Per Record | Multi-EIN = FAIL HARD |
| Hash Required | Every record must have `hash_fingerprint` |

### Table: `dol.air_log` (Audit, Integrity, Resolution)

| Column | Type | Description |
|--------|------|-------------|
| `air_log_id` | VARCHAR(50) | Barton ID: `01.04.02.04.22000.9##` |
| `company_unique_id` | VARCHAR(50) | May be NULL if identity gate failed |
| `outreach_context_id` | VARCHAR(100) | Required context ID |
| `event_type` | VARCHAR(50) | Event classification (see below) |
| `event_status` | VARCHAR(20) | `SUCCESS`, `FAILED`, `ABORTED` |
| `event_message` | TEXT | Human-readable event description |
| `event_payload` | JSONB | Additional event data |
| `identity_gate_passed` | BOOLEAN | TRUE if gate passed |
| `identity_anchors_present` | JSONB | Snapshot of anchors at event time |
| `created_at` | TIMESTAMPTZ | Event timestamp |

### AIR Event Types

| Event Type | Trigger | Status |
|------------|---------|--------|
| `IDENTITY_GATE_FAILED` | Missing required fields/anchors | ABORTED |
| `MULTI_EIN_FOUND` | Multiple EINs found | ABORTED |
| `EIN_MISMATCH` | EIN differs from existing | ABORTED |
| `FILING_TTL_EXCEEDED` | Filing too old | ABORTED |
| `SOURCE_UNAVAILABLE` | DOL source unreachable | ABORTED |
| `CROSS_CONTEXT_CONTAMINATION` | Context mismatch detected | ABORTED |
| `EIN_FORMAT_INVALID` | Invalid EIN format | ABORTED |
| `HASH_VERIFICATION_FAILED` | Hash mismatch | ABORTED |
| `LINKAGE_SUCCESS` | Successful EIN linkage | SUCCESS |

---

## Section 4: Pipeline Logic (STRICT)

### Pipeline Flow

```
┌─────────────────────────────────────────────────────────────────┐
│                    DOL SUBHUB PIPELINE                           │
└─────────────────────────────────────────────────────────────────┘

     ┌──────────────────┐
     │   Company Hub    │
     │      PASS        │
     │                  │
     │ • company_unique_id (sovereign)
     │ • outreach_context_id
     │ • state
     │ • company_domain OR linkedin_company_url
     └────────┬─────────┘
              │
              ▼
     ┌──────────────────┐
     │  Identity Gate   │ ─────────► FAIL HARD if missing
     │   Validation     │            Log AIR: IDENTITY_GATE_FAILED
     └────────┬─────────┘
              │ PASS
              ▼
     ┌──────────────────┐
     │   DOL Subhub     │
     │ (EIN Resolution  │
     │     ONLY)        │
     │                  │
     │ • Apify/Firecrawl retrieve filings
     │ • Parse EIN from Form 5500 / EBSA
     │ • Validate EIN format
     │ • Compute hash fingerprint
     └────────┬─────────┘
              │
              ▼
     ┌──────────────────┐
     │  Kill Switch     │ ─────────► FAIL HARD on any trigger
     │    Checks        │            Log AIR: [event_type]
     │                  │
     │ • Multiple EINs?
     │ • EIN mismatch?
     │ • Filing TTL exceeded?
     │ • Source unavailable?
     │ • Cross-context contamination?
     └────────┬─────────┘
              │ PASS
              ▼
     ┌──────────────────┐
     │  Append EIN      │
     │    Linkage       │
     │                  │
     │ INSERT INTO dol.ein_linkage
     └────────┬─────────┘
              │
              ▼
     ┌──────────────────┐
     │   Emit AIR       │
     │    Event         │
     │                  │
     │ Log: LINKAGE_SUCCESS
     └──────────────────┘
              │
              ▼
     ┌──────────────────┐
     │   DOWNSTREAM     │  (NOT part of this spoke)
     │   CONSUMERS      │
     │                  │
     │ Other systems may read
     │ dol.ein_linkage but
     │ CANNOT influence this spoke
     └──────────────────┘
```

### Implementation Rules

| Rule | Requirement |
|------|-------------|
| **Tool Usage** | Apify / Firecrawl for filing retrieval ONLY |
| **Parsing** | Logic lives in code, not external services |
| **EIN Validation** | Format (XX-XXXXXXX) + consistency check |
| **Hash Fingerprint** | Required for EVERY record |
| **Silence = FAIL** | No "unknown" states allowed |
| **No Retries** | Kill switch = permanent abort |
| **No Fallback** | No alternative paths on failure |

---

## Section 5: Kill Switches (REQUIRED)

**Kill switches abort processing and log to AIR. There are NO retries.**

### Kill Switch Conditions

| Condition | Event Type | Behavior |
|-----------|-----------|----------|
| Multiple EINs found for company | `MULTI_EIN_FOUND` | ABORT + AIR log |
| EIN mismatch across filings | `EIN_MISMATCH` | ABORT + AIR log |
| Filing older than doctrine TTL | `FILING_TTL_EXCEEDED` | ABORT + AIR log |
| DOL source unavailable | `SOURCE_UNAVAILABLE` | ABORT + AIR log |
| Cross-context contamination | `CROSS_CONTEXT_CONTAMINATION` | ABORT + AIR log |

### Filing TTL Configuration

Default TTL: **3 years** (configurable via `p_filing_ttl_years` parameter)

```sql
-- Example: Filing from 2020 in year 2025 = 5 years > 3 year TTL = FAIL
SELECT * FROM dol.insert_ein_linkage(
  ...,
  p_filing_year := 2020,
  p_filing_ttl_years := 3  -- Default
);
-- Result: FILING_TTL_EXCEEDED, ABORTED
```

---

## Section 6: Numbering Convention

### Barton ID Format

```
01.04.02.04.22000.###
│  │  │  │  │     │
│  │  │  │  │     └─ Entity ID (001-999)
│  │  │  │  └─────── Base: 22000 (DOL EIN spoke)
│  │  │  └────────── Schema: 04 (PLE system)
│  │  └───────────── Altitude: 02 (Category/Spoke)
│  └──────────────── Application: 04 (SVG-PLE)
└─────────────────── Subhive: 01 (Marketing/Sales)
```

### ID Ranges

| Range | Purpose | Example |
|-------|---------|---------|
| `001-899` | EIN Linkage records | `01.04.02.04.22000.001` |
| `901-999` | AIR Log entries | `01.04.02.04.22000.901` |

---

## Section 7: Relationship to PLE (ISOLATED)

### Architecture Position

```
┌─────────────────────────────────────────────────────────────────┐
│                         PLE SYSTEM                               │
└─────────────────────────────────────────────────────────────────┘

    ┌─────────────┐     ┌─────────────┐     ┌─────────────┐
    │   Talent    │     │   Renewal   │     │     DOL     │
    │    Flow     │     │   Intel     │     │    EIN      │
    │  (Spoke 1)  │     │  (Spoke 2)  │     │  (Spoke 3)  │
    └──────┬──────┘     └──────┬──────┘     └─────────────┘
           │                   │                   │
           │                   │                   │
           ▼                   ▼                   │
    ┌─────────────────────────────────────┐       │
    │              BIT AXLE               │       │ NO CONNECTION
    │        (Scoring Engine)             │ ◄─────┼─────────────
    └─────────────────────────────────────┘       │
                     │                             │
                     ▼                             │
    ┌─────────────────────────────────────┐       │
    │            WHEEL RIM                │       │ NO CONNECTION
    │      (Outreach Automation)          │ ◄─────┴─────────────
    └─────────────────────────────────────┘
```

### Integration Points

| System | Connection | Status |
|--------|------------|--------|
| Company Hub | `company_unique_id` FK | ✅ REQUIRED |
| BIT Axle | None | ❌ NO CONNECTION |
| Wheel Rim | None | ❌ NO CONNECTION |
| Talent Flow | None | ❌ NO CONNECTION |
| Renewal Intel | None | ❌ NO CONNECTION |

### Downstream Consumption

Other systems MAY:
- READ from `dol.ein_linkage`
- READ from `dol.companies_with_ein` view
- READ from `dol.air_log` for audit

Other systems MAY NOT:
- WRITE to DOL tables
- Trigger DOL operations
- Influence DOL processing
- Modify DOL records

---

## Section 8: Failure Routing & Error Enforcement

### Dual-Write Doctrine (MANDATORY)

All DOL Subhub failures are dual-written to:
1. **AIR event log** (authoritative / audit) — `dol.air_log`
2. **Canonical error table** (operational / triage) — `shq.error_master`

**AIR is authoritative; `shq.error_master` is operational.**

**NOTE**: `shq_error_log` is DEPRECATED and must not be referenced.

### Error Write Contract

On every abort path, the following is written to `shq.error_master`:

| Field | Value |
|-------|-------|
| `error_id` | Auto-generated UUID |
| `process_id` | `01.04.02.04.22000` |
| `agent_id` | `DOL_EIN_SUBHUB` |
| `severity` | `HARD_FAIL` |
| `error_type` | Error code from enum |
| `message` | `[ERROR_CODE] description` |
| `context` | JSON with air_event_id, payload |

### Error Codes (LOCKED ENUM)

| Error Code | Trigger |
|------------|---------|
| `IDENTITY_GATE_FAILED` | Missing required identity fields |
| `MULTI_EIN_FOUND` | Multiple EINs for company |
| `EIN_MISMATCH` | EIN differs across filings |
| `FILING_TTL_EXCEEDED` | Filing older than TTL |
| `SOURCE_UNAVAILABLE` | DOL source unreachable |
| `CROSS_CONTEXT_CONTAMINATION` | Context mismatch |
| `EIN_FORMAT_INVALID` | Invalid EIN format |
| `HASH_VERIFICATION_FAILED` | Hash mismatch |
| `COMPANY_TARGET_NOT_PASS` | Company Target not PASS |
| `DOL_FILING_NOT_CONFIRMED` | Fuzzy found candidates but deterministic rejected all |

**No new codes. No renaming. No retries.**

### Execution Order (CANONICAL)

```
Company Target (PASS)
        ↓
DOL Subhub — EIN Resolution
```

DOL **MUST NOT run** unless Company Target has completed with status `PASS`.

### Write Sequence

```
1. Company Target Gate check (FIRST - before any DOL access)
      ↓
2. Validation fails
      ↓
3. failHard() called
      ↓
4. Write to dol.air_log (AIR - authoritative)
      ↓
5. Write to shq.error_master (operational)
      ↓
6. Return failure result (terminate execution)
```

### Query DOL EIN Failures (24h)

```sql
SELECT * FROM shq.error_master
WHERE process_id = '01.04.02.04.22000'
  AND created_at >= NOW() - INTERVAL '24 hours'
ORDER BY created_at DESC;
```

---

## Section 9: Fuzzy Matching Boundary (Discovery Only)

### Absolute Rule

> **DOL fuzzy matching is allowed ONLY to locate candidate Form 5500 filings.**
> It must NEVER:
> - ❌ Attach an EIN
> - ❌ Resolve company identity
> - ❌ Decide truth
> - ❌ Write data

**Fuzzy output = CANDIDATE SET ONLY**

### Boundary Definition

| Location | Fuzzy Logic | Status |
|----------|-------------|--------|
| `ctb/sys/dol-ein/` | ✅ Allowed (discovery only) | Active |
| `ctb/sys/company-target/` | ❌ NOT allowed (uses upstream resolution) | Locked |
| `analytics.v_5500_*` | ❌ Forbidden | Locked |

### Purpose

Fuzzy matching is used to match:
- `company_name`
- `company_domain` (optional)
- `linkedin_company_name` (optional)

Against Form 5500 filing fields:
- `plan_sponsor_name`
- `plan_name`

**Goal**: Identify candidate filings to inspect, NOT to accept.

### Execution Flow

```
Company Target (PASS, EIN locked)
        ↓
DOL Subhub
  ├─ fuzzy → candidate filings
  ├─ deterministic validation
        ├─ PASS → append-only write
        └─ FAIL → error_master + AIR
```

### Deterministic Validation (CRITICAL - Post-Fuzzy)

For each candidate filing discovered via fuzzy match:

| Check | Requirement | Behavior if Failed |
|-------|-------------|-------------------|
| EIN Match | EIN in filing MUST exactly match resolved EIN | REJECT candidate |
| Filing TTL | Filing year must be within TTL | REJECT candidate |
| Sponsor EIN | Plan sponsor EIN (if present) must match | REJECT candidate |

**If NO candidate passes deterministic checks**: `FAIL HARD` with `DOL_FILING_NOT_CONFIRMED`

### Error Code: DOL_FILING_NOT_CONFIRMED

| Field | Value |
|-------|-------|
| Trigger | Fuzzy found candidates, deterministic rejected all |
| Type | Filing discovery failure (NOT EIN failure) |
| Resolution | Manual review or enrichment |

**This is NOT an EIN failure — EIN is already locked from Company Target.**

### Implementation Files

| File | Purpose |
|------|---------|
| `ctb/sys/dol-ein/findCandidateFilings.js` | Fuzzy discovery + deterministic validation |
| `ctb/sys/dol-ein/ein_validator.js` | `failHardFilingNotConfirmed()` function |

### No Retries. No Fallback.

If deterministic validation rejects all fuzzy candidates:
1. Write to AIR: `DOL_FILING_NOT_CONFIRMED`
2. Write to `shq.error_master`
3. Abort execution
4. No retry logic
5. No fallback enrichment in DOL

---

## Section 10: Audit & Data Lineage Rules

### Monthly Compliance Check

```sql
-- Run monthly audit
SELECT
  event_type,
  event_status,
  COUNT(*) AS count,
  MIN(created_at) AS earliest,
  MAX(created_at) AS latest
FROM dol.air_log
WHERE created_at >= NOW() - INTERVAL '30 days'
GROUP BY event_type, event_status
ORDER BY count DESC;
```

### Data Lineage Requirements

| Field | Lineage Tracked |
|-------|-----------------|
| `company_unique_id` | Source: Company Hub (immutable) |
| `ein` | Source: DOL/EBSA filing (verified) |
| `source` | Filing type classification |
| `source_url` | Direct URL to authoritative document |
| `hash_fingerprint` | SHA-256 of source document |
| `outreach_context_id` | HEIR doctrine context tracking |

### Compliance Verification

```sql
-- Verify all linkages have required fields
SELECT COUNT(*) AS invalid_linkages
FROM dol.ein_linkage
WHERE source_url IS NULL
   OR hash_fingerprint IS NULL
   OR outreach_context_id IS NULL;
-- Expected: 0
```

---

## Section 11: Example Scenario

### Scenario: TechStart Inc EIN Resolution

**Context**:
- Company: TechStart Inc
- `company_unique_id`: `04.04.02.04.30000.042`
- State: VA
- Domain: techstart.io
- Goal: Link EIN from Form 5500 filing

**Step 1: Identity Gate Check**

```sql
SELECT * FROM dol.validate_identity_gate(
  '04.04.02.04.30000.042',  -- company_unique_id
  'CTX-2025-TS-001',        -- outreach_context_id
  'VA',                     -- state
  'techstart.io',           -- company_domain
  NULL                      -- linkedin_company_url (optional)
);

-- Result:
-- is_valid: TRUE
-- failure_reason: NULL
-- identity_anchors: {"company_domain": true, "linkedin_company_url": false}
```

**Step 2: Retrieve Form 5500 via Apify**

```javascript
// Apify actor retrieves Form 5500 from DOL EFAST2
const filing = await apify.call('dol-form-5500-scraper', {
  company_name: 'TechStart Inc',
  state: 'VA',
  ein_hint: null  // Do not provide hint - must discover
});

// Result:
// {
//   ein: '54-1234567',
//   plan_name: 'TechStart Inc 401(k) Plan',
//   filing_year: 2024,
//   source_url: 'https://www.efast.dol.gov/5500/2024/54-1234567.pdf',
//   document_hash: 'a1b2c3d4e5f6...' // SHA-256
// }
```

**Step 3: Insert EIN Linkage**

```sql
SELECT * FROM dol.insert_ein_linkage(
  '04.04.02.04.30000.042',                    -- company_unique_id
  'CTX-2025-TS-001',                          -- outreach_context_id
  'VA',                                        -- state
  'techstart.io',                             -- company_domain
  NULL,                                        -- linkedin_company_url
  '54-1234567',                               -- ein
  'DOL_FORM_5500',                            -- source
  'https://www.efast.dol.gov/5500/2024/54-1234567.pdf',  -- source_url
  2024,                                        -- filing_year
  'a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4e5f6a1b2'  -- hash
);

-- Result:
-- success: TRUE
-- linkage_id: '01.04.02.04.22000.001'
-- air_log_id: '01.04.02.04.22000.901'
-- message: 'LINKAGE_SUCCESS'
```

**Step 4: Verify Linkage**

```sql
SELECT * FROM dol.companies_with_ein
WHERE company_unique_id = '04.04.02.04.30000.042';

-- Result:
-- company_unique_id: 04.04.02.04.30000.042
-- company_name: TechStart Inc
-- ein: 54-1234567
-- source: DOL_FORM_5500
-- filing_year: 2024
-- linkage_created_at: 2025-01-01 10:30:00
```

### Failure Scenario: Multi-EIN Detected

**Attempt to add second EIN (should FAIL)**:

```sql
SELECT * FROM dol.insert_ein_linkage(
  '04.04.02.04.30000.042',  -- Same company
  'CTX-2025-TS-002',
  'VA',
  'techstart.io',
  NULL,
  '54-7654321',  -- DIFFERENT EIN
  'EBSA_FILING',
  'https://www.dol.gov/ebsa/...',
  2023,
  'b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3'
);

-- Result:
-- success: FALSE
-- linkage_id: NULL
-- air_log_id: '01.04.02.04.22000.902'
-- message: 'EIN_MISMATCH'
```

**AIR Log Entry**:

```sql
SELECT * FROM dol.air_log WHERE air_log_id = '01.04.02.04.22000.902';

-- Result:
-- event_type: EIN_MISMATCH
-- event_status: ABORTED
-- event_message: 'EIN mismatch: existing=54-1234567, new=54-7654321'
-- event_payload: {"existing_ein": "54-1234567", "new_ein": "54-7654321", "existing_count": 1}
```

---

## Section 12: DOL Violation Discovery (Fact Storage)

### Purpose

The DOL Subhub includes violation discovery capability to:
1. **Pull violator data** from DOL sources (OSHA, EBSA, WHD, OFCCP)
2. **Match violations to EIN** using existing EIN linkages
3. **Store violation facts** for downstream outreach systems

**This is FACT STORAGE ONLY — no scoring, no outreach triggers in DOL.**

### Architecture

```
DOL Violation Sources
        ↓
[OSHA, EBSA, WHD, OFCCP]
        ↓
DOL Violation Discovery
        ↓
Match to EIN Linkage
        ↓
        ├─ MATCHED → Store in dol.violations
        │              ↓
        │           Downstream systems READ facts
        │           for outreach about remediation
        │
        └─ UNMATCHED → Log for enrichment
                       (violation has no EIN linkage)
```

### Source Agencies (LOCKED ENUM)

| Agency | Description | Data Source |
|--------|-------------|-------------|
| `OSHA` | Occupational Safety & Health | enforcedata.dol.gov |
| `EBSA` | Employee Benefits Security | dol.gov/agencies/ebsa |
| `WHD` | Wage and Hour Division | dol.gov/agencies/whd |
| `OFCCP` | Federal Contract Compliance | dol.gov/agencies/ofccp |
| `MSHA` | Mine Safety & Health | msha.gov |

### Violation Matching Rules

| Rule | Requirement |
|------|-------------|
| EIN Required | Violation must have valid EIN (XX-XXXXXXX) |
| Match to Linkage | EIN must exist in `dol.ein_linkage` |
| No New EINs | Violations do NOT create EIN linkages |
| Append-Only | Violations are facts, not mutable |

### Data Model

**Table: `dol.violations`** (Append-Only)

| Column | Type | Description |
|--------|------|-------------|
| `violation_id` | VARCHAR(50) | Barton ID: `01.04.02.04.22000.5#####` |
| `ein` | VARCHAR(10) | EIN (must exist in ein_linkage) |
| `company_unique_id` | VARCHAR(50) | Linked company ID |
| `source_agency` | VARCHAR(20) | OSHA, EBSA, WHD, etc. |
| `case_number` | VARCHAR(50) | Agency case number |
| `violation_type` | VARCHAR(100) | Type of violation |
| `severity` | VARCHAR(20) | WILLFUL, SERIOUS, etc. |
| `penalty_initial` | DECIMAL | Initial penalty amount |
| `penalty_current` | DECIMAL | Current penalty amount |
| `status` | VARCHAR(30) | OPEN, CONTESTED, SETTLED, etc. |
| `site_state` | VARCHAR(2) | Location state |
| `violation_description` | TEXT | Description from DOL |
| `source_url` | TEXT | Source citation URL |
| `hash_fingerprint` | VARCHAR(64) | SHA-256 for deduplication |
| `created_at` | TIMESTAMPTZ | Discovery timestamp |

### Views for Outreach

| View | Purpose |
|------|---------|
| `dol.v_companies_with_violations` | Companies with open/contested violations |
| `dol.v_violation_summary` | Aggregate stats by company |
| `dol.v_recent_violations` | Last 90 days discoveries |

### AIR Event Types (Violations)

| Event Type | Trigger |
|------------|---------|
| `VIOLATION_DISCOVERED` | New violation found |
| `VIOLATION_EIN_MATCHED` | Matched to existing EIN |
| `VIOLATION_EIN_NOT_FOUND` | No EIN linkage exists |
| `VIOLATION_DUPLICATE` | Duplicate skipped |
| `VIOLATION_BATCH_COMPLETE` | Batch processing done |

### Downstream Consumption

Outreach systems MAY:
- READ from `dol.violations`
- READ from violation views
- Use facts for messaging about remediation

Outreach systems MAY NOT:
- Write to DOL tables
- Modify violation records
- Trigger DOL operations

### Schema File
- [`doctrine/schemas/dol_violations-schema.sql`](../schemas/dol_violations-schema.sql)

### Implementation File
- [`ctb/sys/dol-ein/findViolations.js`](../../ctb/sys/dol-ein/findViolations.js)

---

## Document History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 2.1.0 | 2025-01-02 | Barton Outreach Team | Added violation discovery (fact storage) |
| 2.0.0 | 2025-01-01 | Barton Outreach Team | Complete refactor: EIN Resolution only, removed buyer intent |
| 1.0.0 | 2025-11-07 | Barton Outreach Team | Initial Compliance Monitor doctrine (DEPRECATED) |

---

## Cross-References

### Schema Files
- [`doctrine/schemas/dol_ein_linkage-schema.sql`](../schemas/dol_ein_linkage-schema.sql) - EIN linkage
- [`doctrine/schemas/dol_violations-schema.sql`](../schemas/dol_violations-schema.sql) - Violations

### Related Doctrines (NO INTEGRATION)
- [`PLE-Doctrine.md`](./PLE-Doctrine.md) - Master PLE overview (DOL isolated)
- [`BIT-Doctrine.md`](./BIT-Doctrine.md) - Scoring engine (NO connection to DOL)

### Authoritative Sources
- [DOL EFAST2](https://www.efast.dol.gov/) - Form 5500 filings
- [EBSA](https://www.dol.gov/agencies/ebsa) - Employee Benefits Security Administration

---

**End of DOL EIN Resolution Spoke Doctrine**

*This spoke emits FACTS ONLY. It does NOT score, trigger, or influence downstream systems.*
