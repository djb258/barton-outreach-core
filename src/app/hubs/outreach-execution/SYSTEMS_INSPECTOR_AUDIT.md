# Outreach Execution Hub - Systems Inspector Audit

**Audit Date**: 2025-12-26
**Inspector**: Doctrine-Compliant Systems Inspector
**Doctrine Version**: CL Parent-Child Model v1.1

---

## Executive Summary

### Ground Truth Verification

| Assertion | Status | Evidence |
|-----------|--------|----------|
| Outreach contains exactly 4 sub-hubs | ⚠️ PARTIAL | 3 implemented, 1 missing (Blog) |
| CL is parent identity authority | ⚠️ VIOLATION | `company-intelligence` acts as CL |
| Outreach references CL via `company_unique_id` | ⚠️ VIOLATION | Outreach WRITES to company tables |
| Outreach does NOT mint/infer/override identity | ❌ VIOLATION | `company-intelligence` mints IDs |

### Critical Findings

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                        DOCTRINE VIOLATIONS DETECTED                          │
└─────────────────────────────────────────────────────────────────────────────┘

🚨 CRITICAL: hubs/company-intelligence acts as CL (Parent Hub)
   - Declared as type: axle (should be sub-hub)
   - Claims ownership of company_master, bit_scores
   - Writes to marketing.company_master (CL-owned table)
   - Mints company_unique_id (CL exclusive authority)

🚨 CRITICAL: Blog sub-hub NOT IMPLEMENTED
   - Only signal-company spoke exists (pass-through)
   - No outreach.blog_signals table found
   - No blog processing logic implemented

⚠️ WARNING: Architectural confusion
   - company-intelligence should be Company Target (internal anchor)
   - Current implementation assumes company-intelligence IS CL
   - No actual CL integration exists in this repo
```

---

## Sub-Hub Registry

| # | Declared Sub-Hub | Implementation Status | Directory |
|---|------------------|----------------------|-----------|
| 1 | Company Target | ⚠️ MISNAMED as `company-intelligence` | `hubs/company-intelligence/` |
| 2 | People | ✅ IMPLEMENTED | `hubs/people-intelligence/` |
| 3 | DOL | ✅ IMPLEMENTED | `hubs/dol-filings/` |
| 4 | Blog / Content | ❌ NOT IMPLEMENTED | None (only spoke contract) |

---

# 1. COMPANY TARGET Sub-Hub

**Implementation**: `hubs/company-intelligence/`
**Doctrine ID**: 04.04.01 (INCORRECT - should be 04.04.04.01)
**Status**: ⚠️ DOCTRINE VIOLATION - Acting as CL instead of Outreach sub-hub

## A) ERD (Tables + Relationships)

### Tables Used

| Table | Purpose | PK | company_unique_id | Ownership | R/W |
|-------|---------|----|--------------------|-----------|-----|
| `marketing.company_master` | Company records | `company_unique_id` | IS PK | ⚠️ CL-owned (violated) | WRITE |
| `funnel.suspect_universe` | Funnel tracking | `suspect_id` | FK via `company_id` | Outreach-owned | WRITE |
| `funnel.bit_signal_log` | BIT signals | `signal_id` | FK | Outreach-owned | WRITE |
| `marketing.company_slot` | Slot requirements | `company_slot_unique_id` | FK | People-owned | READ |

### Schema: marketing.company_master

```sql
-- DOCTRINE VIOLATION: This table should be owned by CL, not Outreach
CREATE TABLE marketing.company_master (
    company_unique_id TEXT PRIMARY KEY,    -- ⚠️ Minted here (CL exclusive)
    company_name TEXT,
    domain TEXT,                            -- Golden Rule anchor
    email_pattern TEXT,                     -- Golden Rule anchor
    ein TEXT,
    industry TEXT,
    employee_count INTEGER,
    address_state TEXT,
    bit_score NUMERIC,                      -- ⚠️ Should be in outreach schema
    data_quality_score NUMERIC,
    created_at TIMESTAMP,
    updated_at TIMESTAMP
);
```

### Schema: funnel.suspect_universe

```sql
CREATE TABLE funnel.suspect_universe (
    suspect_id UUID PRIMARY KEY,
    company_id UUID NOT NULL,              -- FK to company
    person_id UUID NOT NULL,
    email VARCHAR(255) NOT NULL,
    funnel_state funnel.lifecycle_state,   -- SUSPECT, WARM, HOT, etc.
    funnel_membership funnel.funnel_membership,
    current_bit_score INTEGER,
    email_open_count INTEGER,
    email_click_count INTEGER,
    email_reply_count INTEGER,
    is_bounced BOOLEAN,
    is_unsubscribed BOOLEAN,
    created_at TIMESTAMPTZ
);
```

### Relationship List

```
marketing.company_master.company_unique_id (PK)
    │
    ├──► funnel.suspect_universe.company_id (FK)
    ├──► funnel.bit_signal_log.company_id (FK)
    ├──► marketing.company_slot.company_unique_id (FK)
    └──► marketing.people_master.company_unique_id (FK)
```

### Identity Doctrine Check

| Check | Result | Evidence |
|-------|--------|----------|
| Stores company metadata? | ❌ YES (VIOLATION) | Writes to `marketing.company_master` |
| Attempts identity inference? | ❌ YES (VIOLATION) | `phase1_company_matching.py` does fuzzy matching |
| Mints company_unique_id? | ❌ YES (VIOLATION) | `company_hub.py` generates Barton IDs |

---

## B) Pipeline (Tool → Logic → Table)

### Step 1: Company Intake Load

| Attribute | Value |
|-----------|-------|
| **Step Name** | Load Raw Intake Data |
| **Entry Trigger** | CSV upload / API call |
| **Tool(s)** | Pandas DataFrame, internal loader |
| **Inputs** | `intake.company_raw_intake` table or CSV file |
| **Logic** | |
| - Filters | None at intake |
| - Matching | None |
| - Scoring | None |
| - Dedupe | None |
| - Gating | None |
| - Normalization | Basic field mapping |
| **Outputs** | In-memory DataFrame |
| **Failure Behavior** | HARD_FAIL if file/table missing |
| **Logged To** | `public.shq_error_log` |

### Step 2: Phase 1 - Company Matching (DOCTRINE VIOLATION)

| Attribute | Value |
|-----------|-------|
| **Step Name** | Fuzzy Company Matching |
| **Entry Trigger** | Pipeline invocation |
| **Tool(s)** | RapidFuzz, internal fuzzy matcher |
| **Inputs** | Raw company names from intake |
| **Logic** | |
| - Filters | None |
| - Matching | ⚠️ FUZZY NAME MATCHING (violates CL doctrine) |
| - Scoring | RapidFuzz ratio >= 85 threshold |
| - Dedupe | Domain-based deduplication |
| - Gating | Match score >= 85 required |
| - Normalization | Lowercase, strip suffixes (Inc, LLC, etc.) |
| **Outputs** | Matched company_unique_id |
| **Failure Behavior** | SOFT_FAIL - routes to Phase 1b (unmatched hold) |
| **Logged To** | Internal stats dictionary |

**File**: `hubs/company-intelligence/imo/middle/phases/phase1_company_matching.py`

### Step 3: Phase 1b - Unmatched Hold Export

| Attribute | Value |
|-----------|-------|
| **Step Name** | Export Unmatched to Hold |
| **Entry Trigger** | Fuzzy match fails |
| **Tool(s)** | Internal exporter |
| **Inputs** | Unmatched records from Phase 1 |
| **Logic** | |
| - Filters | fuzzy_score < 85 |
| - Matching | None |
| - Scoring | None |
| - Dedupe | None |
| - Gating | All unmatched go to hold |
| - Normalization | None |
| **Outputs** | Hold queue / manual review file |
| **Failure Behavior** | SOFT_FAIL - continue pipeline |
| **Logged To** | Stats |

**File**: `hubs/company-intelligence/imo/middle/phases/phase1b_unmatched_hold_export.py`

### Step 4: Phase 2 - Domain Resolution

| Attribute | Value |
|-----------|-------|
| **Step Name** | Resolve Company Domain |
| **Entry Trigger** | After Phase 1 match |
| **Tool(s)** | DNS lookup, Clearbit API (external) |
| **Inputs** | Matched company records |
| **Logic** | |
| - Filters | company_unique_id NOT NULL |
| - Matching | Domain to company |
| - Scoring | None |
| - Dedupe | Domain uniqueness check |
| - Gating | Valid DNS required |
| - Normalization | Lowercase, strip www/http |
| **Outputs** | `marketing.company_master.domain` updated |
| **Failure Behavior** | SOFT_FAIL - mark domain as null |
| **Logged To** | Stats |

**File**: `hubs/company-intelligence/imo/middle/phases/phase2_domain_resolution.py`

### Step 5: Phase 3 - Email Pattern Waterfall

| Attribute | Value |
|-----------|-------|
| **Step Name** | Discover Email Pattern |
| **Entry Trigger** | Domain resolved |
| **Tool(s)** | Hunter.io, internal pattern guesser, MillionVerifier |
| **Inputs** | Domain, known emails |
| **Logic** | |
| - Filters | domain NOT NULL |
| - Matching | Pattern candidates to known emails |
| - Scoring | Pattern confidence score |
| - Dedupe | None |
| - Gating | Confidence >= 0.7 required |
| - Normalization | Pattern template normalization |
| **Outputs** | `marketing.company_master.email_pattern` updated |
| **Failure Behavior** | SOFT_FAIL - mark pattern as null |
| **Logged To** | Stats |

**File**: `hubs/company-intelligence/imo/middle/phases/phase3_email_pattern_waterfall.py`

### Step 6: Phase 4 - Pattern Verification

| Attribute | Value |
|-----------|-------|
| **Step Name** | Verify Email Pattern |
| **Entry Trigger** | Pattern discovered |
| **Tool(s)** | MillionVerifier API |
| **Inputs** | Generated test emails |
| **Logic** | |
| - Filters | email_pattern NOT NULL |
| - Matching | None |
| - Scoring | Verification confidence |
| - Dedupe | None |
| - Gating | Verified = true required |
| - Normalization | None |
| **Outputs** | Pattern verification status |
| **Failure Behavior** | SOFT_FAIL - mark unverified |
| **Logged To** | Stats |

**File**: `hubs/company-intelligence/imo/middle/phases/phase4_pattern_verification.py`

### Step 7: Neon Write

| Attribute | Value |
|-----------|-------|
| **Step Name** | Persist to Neon |
| **Entry Trigger** | Phase 4 complete |
| **Tool(s)** | psycopg2, CompanyNeonWriter |
| **Inputs** | Processed company records |
| **Logic** | |
| - Filters | None (writes all) |
| - Matching | None |
| - Scoring | None |
| - Dedupe | UPSERT on company_unique_id |
| - Gating | None |
| - Normalization | None |
| **Outputs** | `marketing.company_master` rows |
| **Failure Behavior** | HARD_FAIL - rollback transaction |
| **Logged To** | `public.shq_error_log` |

**File**: `hubs/company-intelligence/imo/output/neon_writer.py`

---

## C) Tool Utilization Matrix

| Tool | Purpose | Inputs | Logic Location | Writes Tables | Reads Tables | Logged? |
|------|---------|--------|----------------|---------------|--------------|---------|
| RapidFuzz | Fuzzy company matching | Company names | `phases/phase1_company_matching.py` | None | `marketing.company_master` | Y |
| DNS Resolver | Domain resolution | Company domain | `phases/phase2_domain_resolution.py` | None | None | N |
| Hunter.io | Email pattern discovery | Domain | `phases/phase3_email_pattern_waterfall.py` | None | None | N |
| MillionVerifier | Email verification | Emails | `phases/phase4_pattern_verification.py` | None | None | Y |
| psycopg2 | Database writes | Records | `neon_writer.py` | `marketing.*`, `funnel.*` | All | Y |

### Flags

| Tool | Issue |
|------|-------|
| ⚠️ RapidFuzz | Enables identity inference (fuzzy name matching) - DOCTRINE VIOLATION |
| ⚠️ psycopg2 | Writes to CL-owned tables (`marketing.company_master`) - DOCTRINE VIOLATION |

---

## D) Troubleshooting Playbook

### Issue: Company Not Found After Match

```
CHECK ORDER:
1. Check Phase 1 stats: did fuzzy match succeed?
   → Query: SELECT * FROM public.shq_error_log WHERE component = 'phase1_company_matching'

2. Check threshold: was score >= 85?
   → Log: pipeline.stats['total_matched'] vs pipeline.stats['total_processed']

3. Check Phase 1b: was company routed to hold queue?
   → File: Check hold export output

4. Verify Neon write succeeded:
   → Query: SELECT * FROM marketing.company_master WHERE company_name ILIKE '%{name}%'
```

### Issue: Domain Resolution Failed

```
CHECK ORDER:
1. Verify DNS is reachable
   → Command: nslookup {domain}

2. Check Phase 2 logs
   → Log: pipeline.stats['domains_resolved']

3. Check if domain already exists
   → Query: SELECT * FROM marketing.company_master WHERE domain = '{domain}'
```

### Issue: Email Pattern Missing

```
CHECK ORDER:
1. Check Phase 3 ran
   → Log: pipeline.stats['patterns_discovered']

2. Verify Hunter.io API key
   → Env: HUNTER_API_KEY

3. Check pattern confidence
   → Log: pattern discovery output
```

### Issue: BIT Score Not Updating

```
CHECK ORDER:
1. Verify signal emitted
   → Query: SELECT * FROM funnel.bit_signal_log WHERE company_id = '{id}'

2. Check BIT Engine stats
   → Log: bit_engine.stats

3. Verify signal type valid
   → Code: hub.company.bit_engine.SignalType enum
```

---

# 2. PEOPLE Sub-Hub

**Implementation**: `hubs/people-intelligence/`
**Doctrine ID**: 04.04.02
**Status**: ✅ COMPLIANT (with caveats)

## A) ERD (Tables + Relationships)

### Tables Used

| Table | Purpose | PK | company_unique_id | Ownership | R/W |
|-------|---------|----|--------------------|-----------|-----|
| `marketing.people_master` | Person records | `person_unique_id` | FK | People-owned | WRITE |
| `marketing.company_slot` | Slot assignments | `company_slot_unique_id` | FK | People-owned | WRITE |
| `marketing.company_master` | Company anchor | `company_unique_id` | IS PK | CL-owned | READ |

### Schema: marketing.people_master

```sql
CREATE TABLE marketing.people_master (
    person_unique_id TEXT PRIMARY KEY,
    full_name TEXT,
    email TEXT,
    email_verified BOOLEAN DEFAULT FALSE,
    linkedin_url TEXT,
    title TEXT,
    company_unique_id TEXT NOT NULL,       -- FK to company_master
    slot_type TEXT,                         -- CEO, CFO, HR, etc.
    seniority_rank INTEGER,
    created_at TIMESTAMP,
    updated_at TIMESTAMP,

    CONSTRAINT fk_company
        FOREIGN KEY (company_unique_id)
        REFERENCES marketing.company_master(company_unique_id)
);
```

### Schema: marketing.company_slot

```sql
CREATE TABLE marketing.company_slot (
    company_slot_unique_id TEXT PRIMARY KEY,
    company_unique_id TEXT NOT NULL,
    slot_type TEXT NOT NULL,               -- CEO, CFO, HR
    person_unique_id TEXT,                 -- FK to people_master
    is_filled BOOLEAN DEFAULT FALSE,
    filled_at TIMESTAMP,
    last_refreshed_at TIMESTAMP,

    CONSTRAINT fk_company
        FOREIGN KEY (company_unique_id)
        REFERENCES marketing.company_master(company_unique_id)
);
```

### Relationship List

```
marketing.company_master.company_unique_id
    │
    ├──► marketing.company_slot.company_unique_id
    │         │
    │         └──► marketing.people_master.person_unique_id
    │
    └──► marketing.people_master.company_unique_id
```

### Identity Doctrine Check

| Check | Result | Evidence |
|-------|--------|----------|
| Stores company metadata? | ✅ NO | Only stores person data |
| Attempts identity inference? | ⚠️ INDIRECT | Uses Company Hub for matching |
| Mints company_unique_id? | ✅ NO | Receives from Company Hub |

---

## B) Pipeline (Tool → Logic → Table)

### Step 1: Hub Gate Validation (THE GOLDEN RULE)

| Attribute | Value |
|-----------|-------|
| **Step Name** | Validate Company Anchor |
| **Entry Trigger** | Person record received |
| **Tool(s)** | `ops.enforcement.hub_gate` |
| **Inputs** | Person record with company_name |
| **Logic** | |
| - Filters | None |
| - Matching | Company name to company_unique_id |
| - Scoring | None |
| - Dedupe | None |
| - Gating | ⚠️ HARD_FAIL if company_id/domain/email_pattern missing |
| - Normalization | None |
| **Outputs** | Validated company anchor |
| **Failure Behavior** | HARD_FAIL - route to Company Pipeline |
| **Logged To** | Stats |

**File**: `hubs/people-intelligence/imo/middle/hub_gate.py`

### Step 2: Phase 5 - Email Generation

| Attribute | Value |
|-----------|-------|
| **Step Name** | Generate Email Address |
| **Entry Trigger** | Company anchor validated |
| **Tool(s)** | Internal pattern applier |
| **Inputs** | Person name, company email_pattern |
| **Logic** | |
| - Filters | email_pattern NOT NULL |
| - Matching | None |
| - Scoring | None |
| - Dedupe | None |
| - Gating | Pattern must exist |
| - Normalization | Name normalization (remove accents, etc.) |
| **Outputs** | Generated email address |
| **Failure Behavior** | SOFT_FAIL - mark email as null |
| **Logged To** | Stats |

**File**: `hubs/people-intelligence/imo/middle/phases/phase5_email_generation.py`

### Step 3: Phase 6 - Slot Assignment

| Attribute | Value |
|-----------|-------|
| **Step Name** | Assign to Slot |
| **Entry Trigger** | Email generated |
| **Tool(s)** | Internal slot assigner |
| **Inputs** | Person title, seniority |
| **Logic** | |
| - Filters | title NOT NULL |
| - Matching | Title to slot type (CEO/CFO/HR) |
| - Scoring | Seniority rank (1-5 scale) |
| - Dedupe | One person per slot (highest seniority wins) |
| - Gating | Seniority >= existing occupant required |
| - Normalization | Title normalization |
| **Outputs** | `marketing.company_slot` assignment |
| **Failure Behavior** | SOFT_FAIL - person not slotted |
| **Logged To** | Stats |

**File**: `hubs/people-intelligence/imo/middle/phases/phase6_slot_assignment.py`

### Step 4: Phase 7 - Enrichment Queue

| Attribute | Value |
|-----------|-------|
| **Step Name** | Queue for Enrichment |
| **Entry Trigger** | Slot assigned |
| **Tool(s)** | Apify (LinkedIn scraper), internal queue |
| **Inputs** | LinkedIn URL |
| **Logic** | |
| - Filters | linkedin_url NOT NULL |
| - Matching | None |
| - Scoring | None |
| - Dedupe | LinkedIn URL uniqueness |
| - Gating | None |
| - Normalization | LinkedIn URL normalization |
| **Outputs** | Enrichment queue entry |
| **Failure Behavior** | SOFT_FAIL - skip enrichment |
| **Logged To** | `marketing.data_enrichment_log` |

**File**: `hubs/people-intelligence/imo/middle/phases/phase7_enrichment_queue.py`

### Step 5: Email Verification Sub-Wheel

| Attribute | Value |
|-----------|-------|
| **Step Name** | Verify Email |
| **Entry Trigger** | Email generated |
| **Tool(s)** | MillionVerifier API |
| **Inputs** | Generated email |
| **Logic** | |
| - Filters | email NOT NULL |
| - Matching | None |
| - Scoring | Verification result (valid/invalid/risky) |
| - Dedupe | None |
| - Gating | valid result required for outreach eligibility |
| - Normalization | Email lowercase |
| **Outputs** | `marketing.people_master.email_verified` |
| **Failure Behavior** | SOFT_FAIL - mark unverified |
| **Logged To** | Stats |

**File**: `hubs/people-intelligence/imo/middle/sub_wheels/email_verification/`

### Step 6: Phase 8 - Output Writer

| Attribute | Value |
|-----------|-------|
| **Step Name** | Persist to Neon |
| **Entry Trigger** | All phases complete |
| **Tool(s)** | psycopg2, PeopleNeonWriter |
| **Inputs** | Processed person records |
| **Logic** | |
| - Filters | is_complete = true |
| - Matching | None |
| - Scoring | None |
| - Dedupe | UPSERT on person_unique_id |
| - Gating | None |
| - Normalization | None |
| **Outputs** | `marketing.people_master`, `marketing.company_slot` |
| **Failure Behavior** | HARD_FAIL - rollback |
| **Logged To** | `public.shq_error_log` |

**File**: `hubs/people-intelligence/imo/middle/phases/phase8_output_writer.py`

---

## C) Tool Utilization Matrix

| Tool | Purpose | Inputs | Logic Location | Writes Tables | Reads Tables | Logged? |
|------|---------|--------|----------------|---------------|--------------|---------|
| Hub Gate | Company anchor validation | Company name | `hub_gate.py` | None | `marketing.company_master` | Y |
| Pattern Applier | Email generation | Name + pattern | `phase5_email_generation.py` | None | `marketing.company_master` | N |
| Slot Assigner | Slot competition | Title, seniority | `phase6_slot_assignment.py` | `marketing.company_slot` | Same | Y |
| Apify | LinkedIn enrichment | LinkedIn URL | `phase7_enrichment_queue.py` | `marketing.data_enrichment_log` | None | Y |
| MillionVerifier | Email verification | Email | `sub_wheels/email_verification/` | None | None | Y |
| psycopg2 | Database writes | Records | `neon_writer.py` | `marketing.people_master` | All | Y |

### Flags

| Tool | Issue |
|------|-------|
| ✅ Hub Gate | Properly validates company anchor before processing |
| ⚠️ Indirect CL access | Reads from `marketing.company_master` (should be via spoke) |

---

## D) Troubleshooting Playbook

### Issue: Person Not Matched to Company

```
CHECK ORDER:
1. Check Hub Gate validation
   → Log: people_hub.stats['failed_anchor']

2. Verify company exists in company_master
   → Query: SELECT * FROM marketing.company_master WHERE company_name ILIKE '%{name}%'

3. Check Golden Rule requirements
   → Query: SELECT company_unique_id, domain, email_pattern
            FROM marketing.company_master WHERE company_unique_id = '{id}'
   → All three must be NOT NULL
```

### Issue: Email Not Generated

```
CHECK ORDER:
1. Check email_pattern exists
   → Query: SELECT email_pattern FROM marketing.company_master WHERE company_unique_id = '{id}'

2. Check Phase 5 ran
   → Log: people_hub.stats['emails_generated']

3. Verify name normalization
   → Log: Check for special characters in name
```

### Issue: Slot Assignment Failed

```
CHECK ORDER:
1. Check seniority competition
   → Query: SELECT * FROM marketing.company_slot
            WHERE company_unique_id = '{company_id}' AND slot_type = '{slot}'

2. Verify existing occupant seniority
   → Compare seniority_rank values

3. Check slot type mapping
   → Verify title → slot_type mapping in code
```

---

# 3. DOL Sub-Hub

**Implementation**: `hubs/dol-filings/`
**Doctrine ID**: 04.04.03
**Status**: ✅ COMPLIANT (with caveats)

## A) ERD (Tables + Relationships)

### Tables Used

| Table | Purpose | PK | company_unique_id | Ownership | R/W |
|-------|---------|----|--------------------|-----------|-----|
| `dol.form_5500` | Filing records | `filing_id` | FK via EIN match | DOL-owned | WRITE |
| `dol.schedule_a` | Insurance data | `schedule_id` | FK via filing_id | DOL-owned | WRITE |
| `marketing.company_master` | EIN lookup | `company_unique_id` | IS PK | CL-owned | READ |

### Schema: dol.form_5500 (INFERRED)

```sql
-- Note: Schema inferred from code, VERIFY against actual Neon schema
CREATE TABLE dol.form_5500 (
    filing_id TEXT PRIMARY KEY,
    ein TEXT NOT NULL,                     -- EIN for company matching
    plan_name TEXT,
    plan_year_begin DATE,
    plan_year_end DATE,
    total_participants INTEGER,
    total_assets NUMERIC,
    company_unique_id TEXT,                -- FK populated after EIN match
    is_matched BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP,
    updated_at TIMESTAMP
);
```

### Schema: dol.schedule_a (INFERRED)

```sql
CREATE TABLE dol.schedule_a (
    schedule_id TEXT PRIMARY KEY,
    filing_id TEXT NOT NULL,               -- FK to form_5500
    broker_name TEXT,
    broker_fees NUMERIC,
    carrier_name TEXT,
    policy_type TEXT,
    created_at TIMESTAMP
);
```

### Relationship List

```
dol.form_5500.ein
    │
    └──► marketing.company_master.ein (lookup, not FK)
              │
              └──► dol.form_5500.company_unique_id (populated after match)

dol.form_5500.filing_id
    │
    └──► dol.schedule_a.filing_id (FK)
```

### Identity Doctrine Check

| Check | Result | Evidence |
|-------|--------|----------|
| Stores company metadata? | ✅ NO | Only stores filing data |
| Attempts identity inference? | ✅ NO | EIN match is exact (not fuzzy) |
| Mints company_unique_id? | ✅ NO | Receives from company_master lookup |

---

## B) Pipeline (Tool → Logic → Table)

### Step 1: Federal Data Load

| Attribute | Value |
|-----------|-------|
| **Step Name** | Load DOL Data Files |
| **Entry Trigger** | Annual/quarterly DOL data release |
| **Tool(s)** | Internal importer, pandas |
| **Inputs** | DOL EFAST2 data files (CSV/XML) |
| **Logic** | |
| - Filters | None at load |
| - Matching | None |
| - Scoring | None |
| - Dedupe | filing_id uniqueness |
| - Gating | None |
| - Normalization | EIN normalization (remove dashes) |
| **Outputs** | In-memory DataFrame |
| **Failure Behavior** | HARD_FAIL if file corrupt |
| **Logged To** | Stats |

**File**: `hubs/dol-filings/imo/middle/importers/import_5500.py`

### Step 2: EIN Matching (Tool 18)

| Attribute | Value |
|-----------|-------|
| **Step Name** | Match EIN to Company |
| **Entry Trigger** | Data loaded |
| **Tool(s)** | Internal EIN matcher |
| **Inputs** | Form 5500 EIN field |
| **Logic** | |
| - Filters | ein NOT NULL |
| - Matching | ✅ EXACT EIN MATCH ONLY (doctrine compliant) |
| - Scoring | None |
| - Dedupe | None |
| - Gating | Exact match required (no fuzzy) |
| - Normalization | EIN format: 9 digits, no dashes |
| **Outputs** | company_unique_id populated |
| **Failure Behavior** | SOFT_FAIL - mark unmatched |
| **Logged To** | Stats |

**File**: `hubs/dol-filings/imo/middle/ein_matcher.py`

### Step 3: Schedule A Extraction

| Attribute | Value |
|-----------|-------|
| **Step Name** | Extract Schedule A Data |
| **Entry Trigger** | Form 5500 loaded |
| **Tool(s)** | Internal parser |
| **Inputs** | Schedule A attachments |
| **Logic** | |
| - Filters | Has Schedule A attachment |
| - Matching | filing_id to parent Form 5500 |
| - Scoring | None |
| - Dedupe | schedule_id uniqueness |
| - Gating | None |
| - Normalization | Fee normalization |
| **Outputs** | `dol.schedule_a` records |
| **Failure Behavior** | SOFT_FAIL - skip Schedule A |
| **Logged To** | Stats |

**File**: `hubs/dol-filings/imo/middle/importers/import_schedule_a.py`

### Step 4: BIT Signal Emission

| Attribute | Value |
|-----------|-------|
| **Step Name** | Emit DOL Signals |
| **Entry Trigger** | EIN matched |
| **Tool(s)** | BIT Engine |
| **Inputs** | Matched filing data |
| **Logic** | |
| - Filters | is_matched = true |
| - Matching | None |
| - Scoring | Signal impact (+10 for large plan, etc.) |
| - Dedupe | Signal deduplication (same signal within 24h) |
| - Gating | None |
| - Normalization | None |
| **Outputs** | `funnel.bit_signal_log` |
| **Failure Behavior** | SOFT_FAIL - signal not emitted |
| **Logged To** | Stats |

**File**: `hubs/dol-filings/imo/middle/dol_hub.py`

---

## C) Tool Utilization Matrix

| Tool | Purpose | Inputs | Logic Location | Writes Tables | Reads Tables | Logged? |
|------|---------|--------|----------------|---------------|--------------|---------|
| DOL Importer | Load federal data | CSV/XML files | `importers/import_5500.py` | `dol.form_5500` | None | Y |
| EIN Matcher | Exact EIN lookup | EIN | `ein_matcher.py` | None | `marketing.company_master` | Y |
| Schedule A Parser | Extract broker data | Attachments | `importers/import_schedule_a.py` | `dol.schedule_a` | None | Y |
| BIT Engine | Signal emission | Filing data | `dol_hub.py` | `funnel.bit_signal_log` | None | Y |

### Flags

| Tool | Issue |
|------|-------|
| ✅ EIN Matcher | Exact match only - doctrine compliant |
| ⚠️ BIT Engine | Located in company-intelligence hub (should be Outreach-local?) |

---

## D) Troubleshooting Playbook

### Issue: EIN Not Matched

```
CHECK ORDER:
1. Verify EIN format
   → Expected: 9 digits, no dashes (e.g., 123456789)
   → Query: SELECT ein FROM dol.form_5500 WHERE filing_id = '{id}'

2. Check company_master has EIN
   → Query: SELECT * FROM marketing.company_master WHERE ein = '{ein}'

3. Verify EIN normalization
   → Code: ein_matcher.py normalize_ein()
```

### Issue: Schedule A Missing

```
CHECK ORDER:
1. Verify filing has Schedule A
   → Query: SELECT * FROM dol.form_5500 WHERE filing_id = '{id}'

2. Check import log
   → Log: schedule_a_importer.stats['records_imported']

3. Verify filing_id FK
   → Query: SELECT * FROM dol.schedule_a WHERE filing_id = '{id}'
```

### Issue: BIT Signal Not Emitted

```
CHECK ORDER:
1. Verify filing is matched
   → Query: SELECT is_matched FROM dol.form_5500 WHERE filing_id = '{id}'

2. Check signal deduplication
   → May be blocked by 24h dedupe window

3. Verify BIT Engine received signal
   → Query: SELECT * FROM funnel.bit_signal_log
            WHERE company_id = '{id}' AND signal_source = 'dol_node'
```

---

# 4. BLOG / CONTENT Sub-Hub

**Implementation**: ❌ NOT IMPLEMENTED
**Doctrine ID**: 04.04.04.04 (proposed)
**Status**: ❌ MISSING

## A) ERD (Tables + Relationships)

### Tables Required (NOT FOUND)

| Table | Purpose | PK | Status |
|-------|---------|----|----|
| `outreach.blog_signals` | News/content signals | `signal_id` | ❌ NOT FOUND |
| `outreach.content_engagement` | Content tracking | `engagement_id` | ❌ NOT FOUND |

### What Exists

Only a spoke contract exists:

**File**: `contracts/signal-company.contract.yaml`

```yaml
contract:
  id: CONTRACT-SIGNAL-CO
  description: |
    Unidirectional ingress spoke from Signal Intake to Company Intelligence Hub.
    Handles external signals (news, blog mentions, competitor intel).
    This is NOT a hub - it's a pure pass-through spoke.
```

### Identity Doctrine Check

| Check | Result | Evidence |
|-------|--------|----------|
| Stores company metadata? | N/A | Not implemented |
| Attempts identity inference? | N/A | Not implemented |
| Mints company_unique_id? | N/A | Not implemented |

---

## B) Pipeline (Tool → Logic → Table)

### ❌ NO PIPELINE IMPLEMENTED

The signal-company spoke contract defines data flow but no implementation exists.

**Expected Pipeline** (from contract):

```
Signal Source (news/blog)
    │
    ▼
Signal Intake (external API)
    │
    ▼
signal-company spoke (pass-through)
    │
    ▼
Company Intelligence Hub (⚠️ should be Company Target)
    │
    ▼
BIT Signal Log (for scoring)
```

---

## C) Tool Utilization Matrix

### ❌ NO TOOLS IMPLEMENTED

**Expected Tools** (based on doctrine):

| Tool | Purpose | Status |
|------|---------|--------|
| Firecrawl | Web scraping | ❌ NOT IMPLEMENTED |
| News API | News monitoring | ❌ NOT IMPLEMENTED |
| Sentiment Analyzer | Content analysis | ❌ NOT IMPLEMENTED |

---

## D) Troubleshooting Playbook

### ❌ N/A - NOT IMPLEMENTED

---

# APPENDIX A: Doctrine Violations Summary

## Critical Violations

| ID | Violation | Location | Remediation |
|----|-----------|----------|-------------|
| DV-001 | `company-intelligence` acts as CL | `hubs/company-intelligence/` | Rename to Company Target, make child of CL |
| DV-002 | Writes to `marketing.company_master` | `neon_writer.py` | CL should own this table |
| DV-003 | Mints `company_unique_id` | `company_hub.py` | Only CL may mint |
| DV-004 | Fuzzy company name matching | `phase1_company_matching.py` | CL owns identity resolution |
| DV-005 | Blog sub-hub not implemented | N/A | Implement per doctrine |

## Remediation Path

```
1. Rename hubs/company-intelligence → hubs/company-target
2. Change type: axle → type: sub-hub
3. Add parent: HUB-COMPANY-LIFECYCLE
4. Move marketing.company_master ownership to CL repo
5. Change company-intelligence to READ from CL, not WRITE
6. Implement outreach.company_target table (internal anchor)
7. Implement Blog sub-hub with outreach.blog_signals table
```

---

# APPENDIX B: Neon Schema Summary

## Schemas Touched by Outreach

| Schema | Tables | Owner | Outreach Access |
|--------|--------|-------|-----------------|
| `marketing` | `company_master`, `people_master`, `company_slot` | ⚠️ MIXED | READ+WRITE (violation) |
| `funnel` | `suspect_universe`, `bit_signal_log`, `engagement_events` | Outreach | WRITE |
| `dol` | `form_5500`, `schedule_a` | DOL | WRITE |
| `intake` | `company_raw_intake`, `people_raw_intake` | Outreach | WRITE |
| `public` | `shq_error_log` | System | WRITE |

## Missing Schemas (per doctrine)

| Schema | Purpose | Status |
|--------|---------|--------|
| `cl` | Company Lifecycle tables | ❌ NOT CREATED |
| `outreach` | Outreach-owned tables | ❌ NOT CREATED |

---

*Audit Complete*
*Inspector: Doctrine-Compliant Systems Inspector*
*Date: 2025-12-26*
