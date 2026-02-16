# PRD — Company Hub Pipeline v3.0

## Conformance

| Field | Value |
|-------|-------|
| **Doctrine Version** | IMO-Creator v1.0 |
| **Domain Spec Reference** | `doctrine/REPO_DOMAIN_SPEC.md` |
| **CC Layer** | CC-02 |
| **PRD Constitution** | `templates/doctrine/PRD_CONSTITUTION.md` |

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
| **Hub Name** | Company Hub Pipeline |
| **Hub ID** | HUB-COMPANY-PIPELINE |
| **Owner** | Barton Outreach Core |
| **Version** | 3.0.0 |
| **Doctrine ID** | 04.04.02.04.00001.001 |

---

## 3. Purpose & Transformation Declaration

### Transformation Statement (REQUIRED)

> **"This pipeline transforms raw CSV input records and external enrichment sources (CONSTANTS) into company-anchored contact records with verified emails, slots, and lifecycle states (VARIABLES) through CAPTURE (batch intake with correlation ID generation), COMPUTE (company matching, domain resolution, pattern discovery, email generation, slot assignment), and GOVERN (output writing to files and database with full audit trail)."**

| Field | Value |
|-------|-------|
| **Transformation Summary** | Raw input records + external sources → Company-anchored contacts with emails and slots |

### Constants (Inputs)

_Immutable inputs received from outside this system. Reference: `doctrine/REPO_DOMAIN_SPEC.md §2`_

| Constant | Source | Description |
|----------|--------|-------------|
| `input_csv_records` | Batch intake | Raw people records from CSV files |
| `company_master_records` | Marketing schema | Existing company master data |
| `external_email_patterns` | Tier 0/1/2 providers | Pattern discovery from Firecrawl, Hunter.io, etc. |
| `dns_mx_records` | DNS infrastructure | Domain resolution and validation data |
| `linkedin_profile_data` | External enrichment | LinkedIn profile information |

### Variables (Outputs)

_Outputs this system produces. Reference: `doctrine/REPO_DOMAIN_SPEC.md §3`_

| Variable | Destination | Description |
|----------|-------------|-------------|
| `matched_companies` | company_master | Company-matched records with scores |
| `resolved_domains` | company_master | Validated domain assignments |
| `email_patterns` | company_master | Discovered and verified email patterns |
| `generated_emails` | people_master | Pattern-applied email addresses |
| `slot_assignments` | company_slot | Executive slot assignments by company |
| `enrichment_queue` | data_enrichment_log | Items needing additional enrichment |
| `pipeline_audit_log` | audit_log.json | Complete pipeline event history |

### Pass Structure

_Constitutional pass mapping per `PRD_CONSTITUTION.md §Pass-to-IMO Mapping`_

| Pass | Type | IMO Layer | Description |
|------|------|-----------|-------------|
| Batch Intake | **CAPTURE** | I (Ingress) | Receive CSV files, generate correlation_id |
| Company Matching (P1) | **COMPUTE** | M (Middle) | Match input to company_master |
| Domain Resolution (P2) | **COMPUTE** | M (Middle) | Resolve and validate domains |
| Pattern Waterfall (P3) | **COMPUTE** | M (Middle) | Discover email patterns via tiered providers |
| Pattern Verification (P4) | **COMPUTE** | M (Middle) | Verify discovered patterns |
| Email Generation (P5) | **COMPUTE** | M (Middle) | Apply patterns to generate emails |
| Slot Assignment (P6) | **COMPUTE** | M (Middle) | Assign people to company slots |
| Enrichment Queue (P7) | **COMPUTE** | M (Middle) | Queue items needing enrichment |
| Output Writer (P8) | **GOVERN** | O (Egress) | Write outputs with audit trail |

### Scope Boundary

| Scope | Description |
|-------|-------------|
| **IN SCOPE** | Company matching, domain resolution, pattern discovery/verification, email generation, slot assignment, enrichment queuing, output writing |
| **OUT OF SCOPE** | BIT scoring decisions (BIT Engine owns), outreach execution (Outreach Node owns), CL identity minting (CL owns) |

---

## 4. Overview

- **System Name:** Barton Outreach Core
- **Hub Name:** Company Hub
- **Owner:** Barton Outreach Core
- **Version:** 3.0.0 (Constitutional Compliance)
- **Doctrine ID:** 04.04.02.04.00001.001
- **Changes:** Constitutional sections, Correlation ID enforcement, Failure handling standardization, Signal idempotency, Tooling declarations, Promotion states

---

## 5. Purpose

The Company Hub is the **central identity and signal aggregation core** for the Barton Outreach platform. It owns:
- Company identity (company_id, domain, email_pattern)
- Signal aggregation from all spokes
- BIT Engine decision-making for outreach

**Boundary:** All spoke processes require a valid `company_id` anchor from this hub before proceeding.

---

## Correlation ID Doctrine

```
╔═══════════════════════════════════════════════════════════════════════════════╗
║                       CORRELATION ID ENFORCEMENT                              ║
╠═══════════════════════════════════════════════════════════════════════════════╣
║                                                                               ║
║   Every pipeline run MUST have a correlation_id (UUID v4) generated at       ║
║   batch intake. This ID propagates through ALL phases:                       ║
║                                                                               ║
║   1. Phase 1 (Company Matching)                                              ║
║   2. Phase 1b (Unmatched Hold)                                               ║
║   3. Phase 2 (Domain Resolution)                                             ║
║   4. Phase 3 (Email Pattern Waterfall)                                       ║
║   5. Phase 4 (Pattern Verification)                                          ║
║   6. Phase 0 (People Ingest)                                                 ║
║   7. Phases 5-8 (People Pipeline)                                            ║
║   8. All error logs                                                          ║
║                                                                               ║
║   RULES:                                                                      ║
║   1. correlation_id generated ONCE at pipeline start                         ║
║   2. correlation_id propagated to ALL phase inputs/outputs                   ║
║   3. correlation_id included in ALL error log entries                        ║
║   4. correlation_id included in ALL signal emissions                         ║
║   5. correlation_id NEVER modified mid-pipeline                              ║
║                                                                               ║
║   FORMAT: UUID v4 (e.g., "550e8400-e29b-41d4-a716-446655440000")             ║
║                                                                               ║
╚═══════════════════════════════════════════════════════════════════════════════╝
```

---

## 3. Pipeline Walkthrough — Step-by-Step Narrative

### The Complete Journey: Raw Input → Outreach-Ready Contact

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    COMPANY IDENTITY PIPELINE (Phases 1-4)                   │
│                         Establishes Company Anchor                          │
└─────────────────────────────────────────────────────────────────────────────┘
                                     │
                                     ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                       PEOPLE PIPELINE (Phases 0, 5-8)                       │
│                   Processes People Against Company Anchor                   │
└─────────────────────────────────────────────────────────────────────────────┘
                                     │
                                     ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                              BIT ENGINE                                     │
│                      Scores → Decides → Routes to Outreach                  │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

### PHASE 1: Company Matching

**Purpose:** Match input people records to companies in `company_master`.

**Narrative:**
> A CSV file arrives with 10,000 HR contacts. Each row has a person's name, their company name, and optionally a domain. Phase 1 attempts to link each person to a known company in our master database using a three-tier matching hierarchy.

**Matching Hierarchy (Doctrine-Compliant):**

| Tier | Name | Score | Condition |
|------|------|-------|-----------|
| GOLD | Domain Match | 1.0 | Input domain matches company_master.website_url |
| SILVER | Exact Name | 0.95 | Normalized company names match exactly |
| BRONZE | Fuzzy Match | 0.85-0.92 | Jaro-Winkler similarity with city guardrail |

**City Guardrail Rule:**
- Score >= 0.92: Match regardless of location
- Score 0.85-0.92: Match **only if same city**
- Score < 0.85: No match

**Collision Detection:**
- If top 2 candidates within 0.03 score → Flag as COLLISION
- Collisions route to manual review queue

**Tools Invoked:**
- `normalize_company_name()` — Strips Inc, LLC, Corp suffixes
- `normalize_domain()` — Extracts domain from URL
- `jaro_winkler_similarity()` — Fuzzy string matching
- `apply_city_guardrail()` — Location-based match filtering

**Output Data Shape:**
```python
{
    'correlation_id': str,  # REQUIRED - pipeline trace ID
    'person_id': str,
    'input_company_name': str,
    'matched_company_id': str | None,
    'matched_company_name': str | None,
    'match_type': 'domain' | 'exact' | 'fuzzy' | 'none',
    'match_tier': 'gold' | 'silver' | 'bronze' | 'none',
    'match_score': float,  # 0.0 - 1.0
    'confidence': float,
    'is_collision': bool,
    'collision_reason': str | None,
    'city_match': bool,
    'state_match': bool
}
```

---

### PHASE 1b: Unmatched Hold Export

**Purpose:** Quarantine unmatched records to prevent premature enrichment.

**Narrative:**
> Of the 10,000 input records, 8,500 matched to companies. The remaining 1,500 either had no match, triggered a collision, or had low confidence. Phase 1b exports these to a HOLD file for later review or re-processing.

**Export Categories:**
| Category | Reason | Destination |
|----------|--------|-------------|
| `no_match` | No company found above threshold | `people_unmatched_hold.csv` |
| `collision` | Multiple candidates within 0.03 | `people_unmatched_hold.csv` |
| `low_confidence` | Score below 0.85 | `people_unmatched_hold.csv` |

**Output Data Shape:**
```python
{
    'correlation_id': str,  # REQUIRED - pipeline trace ID
    'person_id': str,
    'input_company_name': str,
    'hold_reason': 'no_match' | 'collision' | 'low_confidence',
    'collision_candidates': List[Dict] | None,
    'queued_at': datetime
}
```

---

### PHASE 2: Domain Resolution

**Purpose:** Ensure every matched company has a valid domain.

**Narrative:**
> We now have 8,500 people linked to companies. But some companies in `company_master` don't have a domain. Phase 2 resolves domains from two sources and validates them.

**Resolution Hierarchy:**
1. **company_master** — Pull from `website_url` or `domain` field
2. **input_record** — Use domain from original CSV if company_master missing
3. **DNS/MX Validation** — Verify domain resolves and has mail servers

**Domain Status Values:**
| Status | Meaning | Action |
|--------|---------|--------|
| `valid` | Domain resolves, has MX records | Proceed to Phase 3 |
| `valid_no_mx` | Domain resolves, no MX records | Proceed with warning |
| `parked` | Domain shows parking page | Queue for enrichment |
| `unreachable` | DNS lookup failed | Queue for enrichment |
| `missing` | No domain from any source | Queue for enrichment |

**Tools Invoked:**
- `normalize_domain()` — Extract root domain
- `verify_domain_dns()` — DNS A/AAAA lookup
- `verify_domain_health()` — MX record check, parking detection

**Output Data Shape:**
```python
{
    'correlation_id': str,  # REQUIRED - pipeline trace ID
    'person_id': str,
    'company_id': str,
    'resolved_domain': str | None,
    'domain_source': 'company_master' | 'input_record' | 'none',
    'domain_status': 'valid' | 'valid_no_mx' | 'parked' | 'unreachable' | 'missing',
    'domain_has_mx': bool,
    'domain_needs_enrichment': bool
}
```

---

### PHASE 3: Email Pattern Waterfall

**Purpose:** Discover the email pattern for each company's domain.

**Narrative:**
> We have 8,000 companies with valid domains. But we don't know their email pattern (is it `first.last@domain.com` or `flast@domain.com`?). Phase 3 uses a tiered waterfall of providers to discover patterns.

**Waterfall Tiers:**

| Tier | Cost | Providers | When Used |
|------|------|-----------|-----------|
| **Tier 0** | FREE | Firecrawl, ScraperAPI, Google Places | Always first |
| **Tier 1** | $0.001-0.01 | Hunter.io, Clearbit, Apollo | If Tier 0 fails |
| **Tier 2** | $0.05-0.10 | Prospeo, Snov, Clay | If Tier 1 fails |

**Waterfall Behavior:**
- **STOP** as soon as pattern found with confidence >= 0.7
- If all tiers fail, suggest common patterns for verification
- Cache results to avoid duplicate API calls

**Common Pattern Suggestions (if all fail):**
1. `{first}.{last}@domain.com` (most common)
2. `{first}{last}@domain.com`
3. `{f}.{last}@domain.com`
4. `{first}_{last}@domain.com`

**API Calls Made:**
```
Provider: firecrawl
Endpoint: POST /v1/scrape
Request: { url: "https://example.com/contact" }
Response: { emails: ["john.doe@example.com", "jane.smith@example.com"] }
Pattern Extracted: {first}.{last}
```

**Output Data Shape:**
```python
{
    'correlation_id': str,  # REQUIRED - pipeline trace ID
    'company_id': str,
    'domain': str,
    'email_pattern': str | None,  # e.g., '{first}.{last}'
    'pattern_source': 'tier_0' | 'tier_1' | 'tier_2' | 'suggested' | 'none',
    'pattern_status': 'found' | 'suggested' | 'failed',
    'tier_used': 0 | 1 | 2 | None,
    'provider_used': str | None,
    'confidence': float,
    'sample_emails': List[str],
    'api_calls_made': int,
    'cost_credits': float
}
```

---

### PHASE 4: Pattern Verification

**Purpose:** Verify discovered patterns before email generation.

**Narrative:**
> We found email patterns for 7,500 companies. But some patterns came from scraping with low confidence. Phase 4 verifies patterns using known emails and optional SMTP checks.

**Verification Methods:**

| Method | Cost | Confidence Boost |
|--------|------|------------------|
| **Sample Email Match** | FREE | +0.3 if pattern matches known emails |
| **MX Record Check** | FREE | +0.1 if domain has valid MX |
| **SMTP Verification** | $0.003/email | +0.2 if SMTP accepts |

**Verification Outcome:**
| Outcome | Confidence | Action |
|---------|------------|--------|
| `verified` | >= 0.8 | Proceed to Phase 5 |
| `partial` | 0.5-0.79 | Proceed with warning |
| `failed` | < 0.5 | Queue for re-discovery |

**Output Data Shape:**
```python
{
    'correlation_id': str,  # REQUIRED - pipeline trace ID
    'company_id': str,
    'domain': str,
    'email_pattern': str,
    'verification_status': 'verified' | 'partial' | 'failed',
    'pattern_confidence': float,  # 0.0 - 1.0
    'verification_methods': List[str],
    'sample_emails_tested': int,
    'smtp_verified': bool | None
}
```

---

### PHASE 0: People Ingest (Movement Engine)

**Purpose:** Initialize funnel state for matched people.

**Narrative:**
> With company identity complete, we now process people. Phase 0 initializes each person's lifecycle state in the 4-Funnel GTM system.

**Initial States:**
| State | Meaning | Next Actions |
|-------|---------|--------------|
| `SUSPECT` | New contact, unvalidated | Process through Phases 5-8 |
| `WARM` | Has valid email + slot | Eligible for BIT scoring |
| `TALENTFLOW_WARM` | Detected via movement | Priority processing |

**Output Data Shape:**
```python
{
    'correlation_id': str,  # REQUIRED - pipeline trace ID
    'person_id': str,
    'company_id': str,
    'lifecycle_state': 'SUSPECT' | 'WARM' | 'TALENTFLOW_WARM',
    'funnel_membership': 'SUSPECTS' | 'WARM' | 'APPOINTMENTS',
    'state_initialized_at': datetime
}
```

---

### PHASE 5: Email Generation

**Purpose:** Generate emails using verified patterns.

**Narrative:**
> We have 7,500 companies with verified email patterns and 8,500 matched people. Phase 5 generates emails by applying the pattern to each person's name.

**Pattern Application:**
```python
# Pattern: {first}.{last}
# Person: John Doe at example.com
# Result: john.doe@example.com
```

**Requirements (Company-First Doctrine):**
- `company_id` MUST be present (no floating people)
- `first_name` and `last_name` MUST be present
- Pattern MUST exist from Phase 4

**Waterfall Integration (Optional):**
- If `enable_waterfall=True` and pattern missing, triggers on-demand discovery
- Uses Tier 0 → Tier 1 → Tier 2 progression
- Caches discovered patterns for reuse

**Output Data Shape:**
```python
{
    'correlation_id': str,  # REQUIRED - pipeline trace ID
    'person_id': str,
    'company_id': str,
    'first_name': str,
    'last_name': str,
    'generated_email': str,
    'email_confidence': 'verified' | 'derived' | 'low_confidence' | 'waterfall',
    'pattern_used': str,
    'domain': str
}
```

---

### PHASE 6: Slot Assignment

**Purpose:** Assign people to company HR slots based on title.

**Narrative:**
> We have 8,500 people with emails. Now we classify them into HR slots (CHRO, HR Manager, Benefits Lead, etc.) to prioritize outreach.

**Slot Types (Seniority Order):**

| Slot | Keywords | Seniority Score |
|------|----------|-----------------|
| **CHRO** | Chief HR, VP HR, SVP HR | 90-100 |
| **HR_MANAGER** | HR Director, HR Manager, Head of HR | 72-85 |
| **BENEFITS_LEAD** | Benefits Director, Benefits Manager | 48-70 |
| **PAYROLL_ADMIN** | Payroll Director, Payroll Manager | 45-70 |
| **HR_SUPPORT** | HR Coordinator, HR Specialist, HRBP | 35-55 |
| **UNSLOTTED** | Cannot classify | 0 |

**Slot Rules:**
- **One person per slot per company**
- If conflict → Higher seniority wins
- Empty slots → Recorded in enrichment queue

**Conflict Resolution Example:**
```
Company: Acme Corp
Existing: HR Manager (score: 75)
New:      HR Director (score: 80)
Result:   HR Director replaces HR Manager
```

**Output Data Shape:**
```python
{
    'correlation_id': str,  # REQUIRED - pipeline trace ID
    'person_id': str,
    'company_id': str,
    'slot_type': 'CHRO' | 'HR_MANAGER' | 'BENEFITS_LEAD' | 'PAYROLL_ADMIN' | 'HR_SUPPORT' | 'UNSLOTTED',
    'title': str,
    'seniority_score': int,
    'assignment_reason': str,
    'replaced_person_id': str | None
}
```

---

### PHASE 7: Enrichment Queue

**Purpose:** Queue records needing additional enrichment.

**Narrative:**
> Some people are missing patterns, some slots are unfilled. Phase 7 creates a prioritized queue for future enrichment.

**Queue Categories:**

| Category | Source | Priority |
|----------|--------|----------|
| `missing_pattern` | Phase 5 failures | HIGH |
| `empty_slot` | CHRO/HR_MANAGER unfilled | HIGH |
| `low_confidence` | Pattern confidence < 0.7 | MEDIUM |
| `unslotted` | Title couldn't classify | LOW |

**Output Data Shape:**
```python
{
    'correlation_id': str,  # REQUIRED - pipeline trace ID
    'queue_id': str,
    'company_id': str,
    'person_id': str | None,
    'enrichment_type': 'pattern' | 'slot' | 'verification',
    'priority': 'high' | 'medium' | 'low',
    'queued_at': datetime
}
```

---

### PHASE 8: Output Writer

**Purpose:** Write final outputs and generate pipeline summary.

**Narrative:**
> Pipeline complete. Phase 8 writes all results to files and database, generates statistics, and creates the audit log.

**Output Files:**

| File | Contents |
|------|----------|
| `people_final.csv` | All people with emails, slots |
| `people_unmatched_hold.csv` | Quarantined unmatched |
| `slot_assignments.csv` | Slot assignments by company |
| `enrichment_queue.csv` | Items needing enrichment |
| `pipeline_summary.json` | Statistics and metadata |
| `audit_log.json` | Complete event log |

**Database Writes:**

> **ERD Reference**: `hubs/people-intelligence/SCHEMA.md`

- `people.people_master` — Person records (ERD verified)
- `people.company_slot` — Slot assignments (ERD verified)
- `outreach.people` — Outreach-attached people (ERD verified)
- `public.shq_error_log` — Errors and failures

---

## 4. Spoke Specifications

### People Node Spoke

| Attribute | Value |
|-----------|-------|
| **Spoke Name** | People Node |
| **Parent Hub** | Company Hub |
| **Status** | ACTIVE |
| **Phases** | 0, 5, 6, 7, 8 |

#### Input Contract

| Field | Type | Required | Source |
|-------|------|----------|--------|
| `correlation_id` | string (UUID v4) | YES | Pipeline start |
| `company_id` | string | YES | Phase 1 |
| `domain` | string | YES | Phase 2 |
| `email_pattern` | string | YES | Phase 4 |
| `first_name` | string | YES | Input CSV |
| `last_name` | string | YES | Input CSV |
| `title` | string | NO | Input CSV |

#### Output Contract

| Field | Type | Destination |
|-------|------|-------------|
| `person_id` | string | Company Hub |
| `generated_email` | string | Company Hub |
| `slot_type` | enum | Company Hub |
| `lifecycle_state` | enum | Movement Engine |

#### Tools Invoked

| Tool | API | Parameters | Response |
|------|-----|------------|----------|
| Pattern Templates | Internal | `pattern`, `first_name`, `last_name` | `generated_email` |
| Title Classifier | Internal | `title` | `slot_type`, `seniority_score` |

#### Failure Handling

| Failure | Severity | Routes To | Remediation |
|---------|----------|-----------|-------------|
| Missing `company_id` | CRITICAL | `FailedCompanyMatchSpoke` | Manual review |
| Missing `first_name`/`last_name` | HIGH | `missing_name` queue | Enrichment |
| No pattern found | MEDIUM | `enrichment_queue` | Waterfall retry |
| Title unclassified | LOW | `UNSLOTTED` | Accept |

---

### DOL Node Spoke

| Attribute | Value |
|-----------|-------|
| **Spoke Name** | DOL Node |
| **Parent Hub** | Company Hub |
| **Status** | ACTIVE |
| **Data Source** | DOL Form 5500 filings |

#### Input Contract

| Field | Type | Required | Source |
|-------|------|----------|--------|
| `ein` | string | YES | DOL Form 5500 |
| `plan_name` | string | YES | DOL Form 5500 |
| `participant_count` | int | NO | DOL Form 5500 |

#### Output Contract

| Field | Type | Destination |
|-------|------|-------------|
| `company_id` | string | Company Hub (via EIN lookup) |
| `renewal_date` | date | Company Hub |
| `plan_assets` | decimal | Company Hub |

#### Tools Invoked

| Tool | API | Parameters | Response |
|------|-----|------------|----------|
| EIN Lookup | Internal | `ein` | `company_id` |
| 5500 Parser | Internal | `filing_data` | Structured fields |

#### Failure Handling

| Failure | Severity | Routes To | Remediation |
|---------|----------|-----------|-------------|
| EIN not found | HIGH | `FailedCompanyMatchSpoke` | Manual mapping |
| Invalid filing | MEDIUM | Error log | Skip filing |

---

### Talent Flow Spoke

| Attribute | Value |
|-----------|-------|
| **Spoke Name** | Talent Flow |
| **Parent Hub** | Company Hub |
| **Status** | SHELL |
| **Purpose** | Detect executive movements |

#### Input Contract

| Field | Type | Required | Source |
|-------|------|----------|--------|
| `person_name` | string | YES | LinkedIn |
| `old_company` | string | YES | LinkedIn |
| `new_company` | string | YES | LinkedIn |
| `change_date` | date | YES | LinkedIn |

#### Output Contract

| Field | Type | Destination |
|-------|------|-------------|
| `movement_type` | enum | Company Hub |
| `old_company_id` | string | Company Hub |
| `new_company_id` | string | Company Hub |
| `signal` | BITSignal | BIT Engine |

#### Tools Invoked

| Tool | API | Parameters | Response |
|------|-----|------------|----------|
| Company Gate | Phase 0 | `company_name` | `company_id` or trigger identity pipeline |

#### Failure Handling

| Failure | Severity | Routes To | Remediation |
|---------|----------|-----------|-------------|
| Company not found | MEDIUM | Company Identity Pipeline | Auto-create company |
| Duplicate movement | LOW | Skip | No action |

---

## 5. Data Flow Diagram with Data Shapes

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              INPUT DATA                                     │
│                                                                             │
│   people.csv                                                                │
│   ┌──────────────────────────────────────────────────────────────────────┐ │
│   │ first_name | last_name | company_name    | domain      | city | title│ │
│   │ John       | Doe       | Acme Corp       | acme.com    | NYC  | CHRO │ │
│   │ Jane       | Smith     | Widget Inc      |             | LA   | HR   │ │
│   └──────────────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────────────────┘
                                     │
                                     │ 10,000 records
                                     ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│ PHASE 1: Company Matching                                                   │
│ Input:  people_df (10,000 rows)                                            │
│ Output: matched_df (8,500 rows) + unmatched_df (1,500 rows)                │
│                                                                             │
│   ┌───────────────────────────────────────────────────────────────────────┐│
│   │ person_id | matched_company_id | match_type | match_score | collision ││
│   │ P001      | C001               | domain     | 1.0         | false     ││
│   │ P002      | C042               | fuzzy      | 0.88        | false     ││
│   │ P003      | NULL               | none       | 0.0         | true      ││
│   └───────────────────────────────────────────────────────────────────────┘│
└─────────────────────────────────────────────────────────────────────────────┘
                                     │
                          ┌──────────┴──────────┐
                          ▼                     ▼
               PHASE 1b: Hold Export     Continue Pipeline
               (1,500 unmatched)         (8,500 matched)
                          │                     │
                          ▼                     ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│ PHASE 2: Domain Resolution                                                  │
│ Input:  matched_df (8,500 rows)                                            │
│ Output: domain_df (8,500 rows, 8,000 with valid domain)                    │
│                                                                             │
│   ┌───────────────────────────────────────────────────────────────────────┐│
│   │ person_id | company_id | resolved_domain | domain_status | has_mx    ││
│   │ P001      | C001       | acme.com        | valid         | true      ││
│   │ P002      | C042       | widget.io       | valid         | true      ││
│   │ P004      | C099       | NULL            | missing       | false     ││
│   └───────────────────────────────────────────────────────────────────────┘│
└─────────────────────────────────────────────────────────────────────────────┘
                                     │
                                     │ 8,000 with domain
                                     ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│ PHASE 3: Email Pattern Waterfall                                            │
│ Input:  domain_df (8,000 unique domains)                                   │
│ Output: pattern_df (7,500 patterns found)                                  │
│                                                                             │
│   ┌───────────────────────────────────────────────────────────────────────┐│
│   │ company_id | domain    | email_pattern   | tier_used | confidence    ││
│   │ C001       | acme.com  | {first}.{last}  | 0         | 0.95          ││
│   │ C042       | widget.io | {f}{last}       | 1         | 0.85          ││
│   │ C099       | NULL      | NULL            | NULL      | 0.0           ││
│   └───────────────────────────────────────────────────────────────────────┘│
└─────────────────────────────────────────────────────────────────────────────┘
                                     │
                                     │ 7,500 patterns
                                     ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│ PHASE 4: Pattern Verification                                               │
│ Input:  pattern_df (7,500 patterns)                                        │
│ Output: verified_df (7,200 verified patterns)                              │
│                                                                             │
│   ┌───────────────────────────────────────────────────────────────────────┐│
│   │ company_id | email_pattern  | verification_status | pattern_confidence││
│   │ C001       | {first}.{last} | verified            | 0.95              ││
│   │ C042       | {f}{last}      | partial             | 0.72              ││
│   └───────────────────────────────────────────────────────────────────────┘│
└─────────────────────────────────────────────────────────────────────────────┘
                                     │
         ════════════════════════════╪════════════════════════════════
                  COMPANY IDENTITY COMPLETE — PEOPLE PIPELINE BEGINS
         ════════════════════════════╪════════════════════════════════
                                     │
                                     ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│ PHASE 5: Email Generation                                                   │
│ Input:  matched_people (8,500) + verified_patterns (7,200)                 │
│ Output: people_with_emails (7,000) + missing_pattern (1,500)               │
│                                                                             │
│   ┌───────────────────────────────────────────────────────────────────────┐│
│   │ person_id | company_id | generated_email       | email_confidence    ││
│   │ P001      | C001       | john.doe@acme.com     | verified            ││
│   │ P002      | C042       | jsmith@widget.io      | derived             ││
│   └───────────────────────────────────────────────────────────────────────┘│
└─────────────────────────────────────────────────────────────────────────────┘
                                     │
                                     │ 7,000 with emails
                                     ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│ PHASE 6: Slot Assignment                                                    │
│ Input:  people_with_emails (7,000)                                         │
│ Output: slotted (6,500) + unslotted (500)                                  │
│                                                                             │
│   ┌───────────────────────────────────────────────────────────────────────┐│
│   │ person_id | company_id | slot_type   | seniority_score | replaced    ││
│   │ P001      | C001       | CHRO        | 100             | NULL        ││
│   │ P002      | C042       | HR_MANAGER  | 75              | P999        ││
│   │ P005      | C042       | UNSLOTTED   | 0               | NULL        ││
│   └───────────────────────────────────────────────────────────────────────┘│
└─────────────────────────────────────────────────────────────────────────────┘
                                     │
                                     │ 6,500 slotted
                                     ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│ PHASE 7 & 8: Queue + Output                                                 │
│ Input:  All previous outputs                                               │
│ Output: Files + Database writes + Audit log                                │
│                                                                             │
│   Files Written:                                                            │
│   ├── people_final.csv (7,000 records)                                     │
│   ├── people_unmatched_hold.csv (1,500 records)                            │
│   ├── slot_assignments.csv (6,500 records)                                 │
│   ├── enrichment_queue.csv (2,000 records)                                 │
│   ├── pipeline_summary.json                                                 │
│   └── audit_log.json                                                        │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 6. Integration Points

### Company Identity Pipeline → People Pipeline

| Interface | Data Passed | Format |
|-----------|-------------|--------|
| Phase 4 → Phase 5 | Verified patterns | `pattern_df` DataFrame |
| Phase 1 → Phase 5 | Company linkage | `company_id` column |
| Phase 2 → Phase 5 | Resolved domains | `resolved_domain` column |

### People Pipeline → BIT Engine

| Interface | Data Passed | Format |
|-----------|-------------|--------|
| Phase 6 → BIT | Slot assignments | `SLOT_FILLED` signal |
| Phase 5 → BIT | Email generation | `EMAIL_VERIFIED` signal |
| Phase 0 → BIT | State initialization | `lifecycle_state` |

### BIT Engine → Outreach

| Interface | Data Passed | Format |
|-----------|-------------|--------|
| BIT → Outreach | Score threshold | `BIT_SCORE >= 50` |
| BIT → Outreach | Category | `hot` / `warm` / `cold` |

---

## 7. Guard Rails

| Guard Rail | Type | Threshold | Action |
|------------|------|-----------|--------|
| Collision Detection | Validation | score_diff < 0.03 | Flag for review |
| Fuzzy Match Floor | Validation | score < 0.85 | No match |
| City Guardrail | Validation | score 0.85-0.92 | Require city match |
| API Rate Limit | Rate Limit | Provider-specific | Queue and retry |
| Pattern Confidence | Validation | confidence < 0.5 | Queue for re-discovery |
| Company-First | Validation | company_id = NULL | STOP processing |

---

## 8. Kill Switch

- **Endpoint:** `POST /api/pipeline/kill`
- **Environment Variable:** `PIPELINE_ENABLED=false`
- **Activation Criteria:**
  - Error rate > 10% in 5 minutes
  - API cost > $100 in single run
  - Database connection failure
- **Emergency Contact:** [ASSIGN: On-Call Engineer]

---

## 9. Promotion Gates

| Gate | Requirement |
|------|-------------|
| G1 | All unit tests pass |
| G2 | Phase 1-4 integration tests pass |
| G3 | Sample run with 1,000 records succeeds |
| G4 | Kill switch tested and functional |
| G5 | Rollback procedure verified |

---

## 10. Failure Modes (Standardized)

### Phase-Level Failures

| Failure | Error Code | Phase | Severity | Local Emit | Global Emit | Recovery |
|---------|------------|-------|----------|------------|-------------|----------|
| Database connection lost | PIPE-001 | All | CRITICAL | `pipeline_errors` | `shq_error_log` | Halt, alert |
| No company match found | PIPE-101 | P1 | INFO | `unmatched_hold` | — | Hold export |
| Collision detected | PIPE-102 | P1 | WARN | `collision_queue` | `shq_error_log` | Manual review |
| Domain resolution failed | PIPE-201 | P2 | WARN | `domain_failures` | `shq_error_log` | Queue enrichment |
| API provider down | PIPE-301 | P3 | HIGH | `api_failures` | `shq_error_log` | Next tier |
| Pattern discovery fails | PIPE-302 | P3 | MEDIUM | `pattern_failures` | — | Suggest patterns |
| Pattern verification failed | PIPE-401 | P4 | MEDIUM | `verification_queue` | — | Re-discovery |
| Name parsing failed | PIPE-501 | P5 | WARN | `name_failures` | `shq_error_log` | Queue enrichment |
| Title classification failed | PIPE-601 | P6 | LOW | `unslotted` | — | Accept UNSLOTTED |
| Output write failed | PIPE-801 | P8 | CRITICAL | — | `shq_error_log` | Halt, alert |

### Two-Layer Error Model

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         TWO-LAYER ERROR MODEL                                │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│   LAYER 1: LOCAL (Pipeline Engine owned)                                    │
│   ├── Table: pipeline_errors (marketing schema)                             │
│   ├── Owner: Company Hub Pipeline                                           │
│   ├── Purpose: Operational remediation, retry logic                         │
│   └── Fields: correlation_id, phase, error_code, person_id, timestamp       │
│                                                                             │
│   LAYER 2: GLOBAL (System-wide visibility)                                  │
│   ├── Table: shq_error_log (public schema)                                  │
│   ├── Owner: Platform team                                                  │
│   ├── Purpose: Trend analysis, alerting, cross-system correlation           │
│   └── Fields: correlation_id, component='company_hub_pipeline', error_code  │
│                                                                             │
│   ERROR FLOW:                                                               │
│   1. Error occurs during phase execution                                    │
│   2. Log to local table (pipeline_errors)                                  │
│   3. If severity >= WARN: Also emit to shq_error_log                       │
│   4. Include correlation_id in BOTH logs for cross-reference               │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Error Code Standards

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         ERROR CODE CONVENTIONS                               │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│   Format: PIPE-{PHASE}{NUMBER}                                              │
│                                                                             │
│   Phases:                                                                   │
│   ├── 0XX: Infrastructure/cross-phase errors                                │
│   ├── 1XX: Phase 1 (Company Matching)                                       │
│   ├── 2XX: Phase 2 (Domain Resolution)                                      │
│   ├── 3XX: Phase 3 (Pattern Waterfall)                                      │
│   ├── 4XX: Phase 4 (Pattern Verification)                                   │
│   ├── 5XX: Phase 5 (Email Generation)                                       │
│   ├── 6XX: Phase 6 (Slot Assignment)                                        │
│   ├── 7XX: Phase 7 (Enrichment Queue)                                       │
│   └── 8XX: Phase 8 (Output Writer)                                          │
│                                                                             │
│   Examples:                                                                 │
│   ├── PIPE-001: Database connection lost                                    │
│   ├── PIPE-101: No company match found                                      │
│   ├── PIPE-301: API provider unavailable                                    │
│   └── PIPE-501: Name parsing failed                                         │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 11. Observability

- **Metrics:**
  - `pipeline_duration_seconds`
  - `phase_{N}_match_rate`
  - `api_calls_by_provider`
  - `cost_credits_total`
- **Alerts:**
  - Error rate > 5%
  - Duration > 2x expected
  - API cost spike

---

## 12. Promotion States

### Burn-In Mode vs Steady-State Mode

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         PROMOTION STATE DEFINITIONS                          │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│   BURN-IN MODE (Initial Deployment)                                         │
│   ├── Duration: First 14 days of production                                 │
│   ├── Batch size: Limited to 500 records                                    │
│   ├── Thresholds: Stricter (match score >= 0.90 vs 0.85)                   │
│   ├── Kill switches: More sensitive (5% error rate → kill)                 │
│   ├── Alerting: Immediate on any ERROR severity                            │
│   └── Review: All collisions manually reviewed                              │
│                                                                             │
│   STEADY-STATE MODE (After Validation)                                      │
│   ├── Promotion: After passing all gates below                              │
│   ├── Batch size: Unlimited                                                 │
│   ├── Thresholds: Standard (match score >= 0.85)                           │
│   ├── Kill switches: Standard sensitivity (10% error rate → kill)          │
│   ├── Alerting: Standard alerting rules                                    │
│   └── Review: Only collisions with score_diff < 0.02                       │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Promotion Gates (Burn-In → Steady-State)

| Gate | Criteria | Measurement |
|------|----------|-------------|
| G1 | All unit tests pass | CI/CD pipeline green |
| G2 | Phase 1-4 integration tests pass | Integration suite passes |
| G3 | Sample run with 1,000 records succeeds | `pipeline.runs.success >= 1000` |
| G4 | Kill switch tested and functional | Manual verification |
| G5 | Rollback procedure verified | Documented + tested |
| G6 | Match rate ≥ 85% | `phase1.matched / phase1.total >= 0.85` |
| G7 | Pattern discovery rate ≥ 70% | `phase3.found / phase3.attempted >= 0.70` |
| G8 | Error rate ≤ 3% over 7 days | `pipeline.errors / pipeline.processed <= 0.03` |
| G9 | API cost within budget | `pipeline.cost_total <= $100/run` |
| G10 | No CRITICAL errors in 7 days | `shq_error_log.critical.count(7d) == 0` |

### State Transition

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         STATE TRANSITION FLOW                                │
└─────────────────────────────────────────────────────────────────────────────┘

    ┌───────────────┐                              ┌───────────────┐
    │   BURN-IN     │    All gates G1-G10 pass    │  STEADY-STATE │
    │               │─────────────────────────────►│               │
    │  (14 days)    │                              │  (Ongoing)    │
    └───────────────┘                              └───────────────┘
           │                                              │
           │  Critical failure                            │  Regression detected
           │  or gate regression                         │  (fails G6-G10)
           │                                              │
           ▼                                              ▼
    ┌───────────────┐                              ┌───────────────┐
    │   SUSPENDED   │                              │   BURN-IN     │
    │               │                              │   (Reset)     │
    │  Manual fix   │                              │               │
    │  required     │                              │  Re-validate  │
    └───────────────┘                              └───────────────┘
```

---

## 13. Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | 2025-12-17 | Initial Company Hub Pipeline PRD |
| 1.1 | 2025-12-17 | Updated to Bicycle Wheel Doctrine |
| 2.1 | 2025-12-17 | Hardened: Correlation ID, Failure Handling, Error Codes, Promotion States |

---

## Approval

| Role | Name | Date |
|------|------|------|
| Hub Owner | | |
| Tech Lead | | |
| Reviewer | | |

---

*Document Version: 2.1*
*Template: PRD_HUB.md*
*Doctrine: Bicycle Wheel v1.1 / Barton Doctrine*
