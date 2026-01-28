# Technical Architecture Specification: Column Lineage

**Repository**: barton-outreach-core
**Version**: 1.0.0
**Generated**: 2026-01-28
**Purpose**: Where each column value originates — Trace any value to its source

---

## CL Authority Registry

### cl.company_identity

| Column | Source | How Populated |
|--------|--------|---------------|
| `company_unique_id` | Generated | `gen_random_uuid()` at insert |
| `sovereign_company_id` | External | From intake CSV or API |
| `company_name` | External | From intake source |
| `company_domain` | External | From intake or domain discovery |
| `normalized_domain` | Derived | Lowercase, stripped of www/protocol |
| `linkedin_company_url` | Enrichment | LinkedIn API or manual |
| `source_system` | Metadata | Set by intake process |
| `company_fingerprint` | Derived | Hash of name + domain + state |
| `lifecycle_run_id` | Metadata | Processing batch ID |
| `existence_verified` | Verification | Domain check result |
| `verification_run_id` | Metadata | Verification batch ID |
| `verified_at` | Timestamp | When verification completed |
| `domain_status_code` | Verification | HTTP status from domain check |
| `name_match_score` | Algorithm | Fuzzy match score 0-100 |
| `state_match_result` | Verification | State comparison result |
| `canonical_name` | Resolution | Final resolved company name |
| `state_verified` | Verification | Verified state abbreviation |
| `employee_count_band` | Enrichment | Employee range estimate |
| `identity_pass` | Counter | Incremented each verification pass |
| `identity_status` | State Machine | PENDING → RESOLVED/FAILED |
| `last_pass_at` | Timestamp | Last verification timestamp |
| `eligibility_status` | Business Logic | Eligibility determination |
| `exclusion_reason` | Business Logic | Why excluded (if applicable) |
| `entity_role` | Classification | EMPLOYER, VENDOR, etc. |
| `final_outcome` | Business Logic | Final disposition |
| `final_reason` | Business Logic | Reason for final outcome |
| `outreach_id` | Outreach Hub | WRITE-ONCE from outreach.outreach |
| `sales_process_id` | Sales Hub | WRITE-ONCE from Sales |
| `client_id` | Client Hub | WRITE-ONCE from Client |
| `outreach_attached_at` | Timestamp | When outreach_id was written |
| `sales_opened_at` | Timestamp | When sales_process_id was written |
| `client_promoted_at` | Timestamp | When client_id was written |
| `created_at` | Timestamp | Row creation time |

---

## Outreach Spine

### outreach.outreach

| Column | Source | How Populated |
|--------|--------|---------------|
| `outreach_id` | Generated | `gen_random_uuid()` at insert |
| `sovereign_id` | CL | From `cl.company_identity.sovereign_company_id` |
| `domain` | CL | From `cl.company_identity.normalized_domain` |
| `created_at` | Timestamp | Row creation time |
| `updated_at` | Timestamp | Last modification time |

---

## Company Target Sub-Hub

### outreach.company_target

| Column | Source | How Populated |
|--------|--------|---------------|
| `target_id` | Generated | `gen_random_uuid()` at insert |
| `outreach_id` | Spine | From `outreach.outreach.outreach_id` |
| `company_unique_id` | CL | From `cl.company_identity.company_unique_id` (legacy) |
| `email_method` | Discovery | Phase 3 Email Pattern Waterfall |
| `method_type` | Discovery | Classification: PATTERN/CATCHALL/VERIFIED/NONE |
| `confidence_score` | Algorithm | Pattern confidence 0.00-1.00 |
| `is_catchall` | Discovery | Catch-all domain detection |
| `outreach_status` | State Machine | queued → active → completed |
| `execution_status` | State Machine | pending → running → done |
| `bit_score_snapshot` | BIT Engine | Snapshot at targeting time |
| `sequence_count` | Counter | Number of sequences executed |
| `active_sequence_id` | Reference | Current active sequence |
| `source` | Metadata | Lead source identifier |
| `first_targeted_at` | Timestamp | First outreach attempt |
| `last_targeted_at` | Timestamp | Most recent outreach |
| `imo_completed_at` | Timestamp | IMO flow completion |
| `created_at` | Timestamp | Row creation time |
| `updated_at` | Timestamp | Last modification time |

---

## DOL Sub-Hub

### outreach.dol

| Column | Source | How Populated |
|--------|--------|---------------|
| `dol_id` | Generated | `gen_random_uuid()` at insert |
| `outreach_id` | Spine | From `outreach.outreach.outreach_id` |
| `ein` | DOL Matching | From `dol.form_5500.ein` or `dol.ein_urls.ein` |
| `filing_id` | DOL Matching | From `dol.form_5500.filing_id` |
| `form_5500_matched` | Algorithm | True if match found |
| `schedule_a_matched` | Algorithm | True if Schedule A exists |
| `match_confidence` | Algorithm | Match confidence 0.00-1.00 |
| `match_method` | Algorithm | EXACT/FUZZY/EIN_ONLY/NONE |
| `matched_at` | Timestamp | When match was made |
| `created_at` | Timestamp | Row creation time |
| `updated_at` | Timestamp | Last modification time |

### dol.form_5500

| Column | Source | How Populated |
|--------|--------|---------------|
| `filing_id` | DOL | DOL's unique filing identifier |
| `ein` | DOL | Employer Identification Number |
| `plan_name` | DOL | Plan name from filing |
| `sponsor_name` | DOL | Company name from filing |
| `sponsor_state` | DOL | State from filing |
| `plan_year` | DOL | Plan year from filing |
| `plan_year_end_month` | DOL | Plan year end month |
| `total_participants` | DOL | Participant count from filing |
| `total_assets` | DOL | Asset value from filing |
| `filing_date` | DOL | Filing date |
| `form_type` | DOL | 5500, 5500-SF, etc. |
| `plan_type` | DOL | 401K, PENSION, etc. |
| `is_large_plan` | Derived | `total_participants >= 100` |
| `created_at` | Timestamp | Import timestamp |

---

## People Intelligence Sub-Hub

### outreach.people

| Column | Source | How Populated |
|--------|--------|---------------|
| `person_id` | Generated | `gen_random_uuid()` at insert |
| `outreach_id` | Spine | From `outreach.outreach.outreach_id` |
| `person_unique_id` | People | From `people.people_master.unique_id` |
| `slot_type` | Assignment | From `people.company_slot.slot_type` |
| `email` | Generated | Pattern + name: `{first}.{last}@{domain}` |
| `email_verified` | Verification | SMTP check or bounce detection |
| `verification_method` | Verification | How verified: SMTP_CHECK, BOUNCE, etc. |
| `linkedin_url` | People | From `people.people_master.linkedin_url` |
| `title` | People | From `people.people_master.title` |
| `seniority` | People | From `people.people_master.seniority` |
| `seniority_rank` | People | From `people.people_master.seniority_rank` |
| `created_at` | Timestamp | Row creation time |
| `updated_at` | Timestamp | Last modification time |

### people.people_master

| Column | Source | How Populated |
|--------|--------|---------------|
| `unique_id` | Generated | `gen_random_uuid()` at insert |
| `company_unique_id` | CL | From `cl.company_identity.company_unique_id` |
| `full_name` | Enrichment | LinkedIn, Sales Nav, or manual |
| `first_name` | Parsed | Extracted from full_name |
| `last_name` | Parsed | Extracted from full_name |
| `email` | Generated/Enrichment | Pattern-based or enrichment |
| `email_verified` | Verification | SMTP check result |
| `title` | Enrichment | Job title from source |
| `seniority` | Algorithm | C-SUITE, VP, DIRECTOR, etc. |
| `seniority_rank` | Algorithm | 1-10 based on title parsing |
| `linkedin_url` | Enrichment | LinkedIn profile URL |
| `slot_type` | Algorithm | Mapped from title |
| `data_quality_score` | Algorithm | Quality score 0-100 |
| `source` | Metadata | Data source identifier |
| `created_at` | Timestamp | Row creation time |
| `updated_at` | Timestamp | Last modification time |

### people.company_slot

| Column | Source | How Populated |
|--------|--------|---------------|
| `slot_id` | Generated | `gen_random_uuid()` at insert |
| `company_unique_id` | CL | From `cl.company_identity.company_unique_id` |
| `outreach_id` | Spine | From `outreach.outreach.outreach_id` |
| `slot_type` | Definition | CEO, CFO, HR, CTO, CMO, COO |
| `person_unique_id` | Assignment | From `people.people_master.unique_id` |
| `is_filled` | State | True when person assigned |
| `fill_source` | Metadata | How slot was filled |
| `confidence_score` | Algorithm | Assignment confidence |
| `filled_at` | Timestamp | When person was assigned |
| `last_refreshed_at` | Timestamp | Last refresh check |
| `created_at` | Timestamp | Row creation time |
| `updated_at` | Timestamp | Last modification time |

---

## BIT Engine

### outreach.bit_scores

| Column | Source | How Populated |
|--------|--------|---------------|
| `outreach_id` | Spine | PK/FK from `outreach.outreach.outreach_id` |
| `bit_score` | Calculation | Sum of signal impacts (max 100) |
| `bit_tier` | Calculation | Tier based on score thresholds |
| `tier_threshold` | Calculation | Threshold that applied |
| `score_updated_at` | Timestamp | Last score calculation |
| `tier_assigned_at` | Timestamp | Last tier assignment |
| `signal_count` | Calculation | Total signals |
| `dol_signal_count` | Calculation | DOL-sourced signals |
| `blog_signal_count` | Calculation | Blog-sourced signals |
| `movement_signal_count` | Calculation | Movement-sourced signals |
| `custom_signal_count` | Calculation | Custom signals |
| `score_velocity` | Calculation | Score change rate |
| `created_at` | Timestamp | Row creation time |
| `updated_at` | Timestamp | Last modification time |

### outreach.bit_signals

| Column | Source | How Populated |
|--------|--------|---------------|
| `signal_id` | Generated | `gen_random_uuid()` at insert |
| `outreach_id` | Spine | From `outreach.outreach.outreach_id` |
| `signal_type` | Detection | DOL_FILING, BLOG_PRESSURE, MOVEMENT, CUSTOM |
| `signal_subtype` | Detection | More specific classification |
| `signal_impact` | Algorithm | Points for this signal |
| `signal_weight` | Algorithm | Multiplier |
| `signal_source` | Metadata | Where detected |
| `signal_hash` | Algorithm | Hash for deduplication |
| `signal_payload` | Detection | Signal-specific data (JSON) |
| `signal_timestamp` | Detection | When signal occurred |
| `expires_at` | Calculation | Signal expiration time |
| `is_expired` | Calculation | Whether signal has expired |
| `created_at` | Timestamp | Row creation time |

---

## Email Generation Lineage

```
EMAIL FORMULA:
outreach.people.email = pattern(
    outreach.company_target.email_method,
    people.people_master.first_name,
    people.people_master.last_name,
    cl.company_identity.normalized_domain
)

EXAMPLE:
email_method = "{first}.{last}@{domain}"
first_name = "John"
last_name = "Smith"
normalized_domain = "acmecorp.com"
→ email = "john.smith@acmecorp.com"
```

---

## BIT Score Lineage

```
BIT SCORE FORMULA:
outreach.bit_scores.bit_score = MIN(100,
    (outreach.dol.form_5500_matched ? 20 : 0) +
    (outreach.dol.schedule_a_matched ? 10 : 0) +
    (outreach.blog.signal_count * 5) +
    (COUNT(people.person_movement_history) * 15) +
    SUM(custom_signals)
)

TIER ASSIGNMENT:
bit_tier = CASE
    WHEN bit_score >= 80 THEN 'PLATINUM'
    WHEN bit_score >= 60 THEN 'GOLD'
    WHEN bit_score >= 40 THEN 'SILVER'
    WHEN bit_score >= 20 THEN 'BRONZE'
    ELSE 'NONE'
END
```

---

## Document Control

| Field | Value |
|-------|-------|
| Created | 2026-01-28 |
| Version | 1.0.0 |
| Author | Claude Code (AI Employee) |
