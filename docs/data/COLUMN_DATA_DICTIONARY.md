<!-- AUTO-GENERATED FROM column_registry.yml — DO NOT HAND EDIT -->

# Column Data Dictionary

Generated from `column_registry.yml` — **DO NOT HAND EDIT**

| Field | Value |
|-------|-------|
| Hub | Barton Outreach Core (04.04) |
| Registry Version | 1.0.0 |
| Generated | 2026-02-15T21:19:37Z |
| Regenerate | `./scripts/generate-data-dictionary.sh` |

---

## outreach

Operational spine — all sub-hubs FK to outreach_id. Mints outreach_id, registers in CL.

| Owning Sub-Hub | Leaf Type | Source of Truth | Row Identity |
|----------------|-----------|-----------------|--------------|
| Hub-level (spine) | CANONICAL | true | UUID |

| Column | Type | Format | Nullable | Semantic Role | Description |
|--------|------|--------|----------|---------------|-------------|
| `outreach_id` | UUID | UUID | false | identifier | Universal join key — minted here, propagated to all sub-hub tables |
| `sovereign_company_id` | UUID | UUID | false | foreign_key | FK to cl.company_identity — links outreach record to sovereign identity |
| `status` | TEXT | ENUM | false | attribute | Workflow state of outreach lifecycle (INIT, ACTIVE, COMPLETED, ARCHIVED) |
| `created_at` | TIMESTAMPTZ | ISO-8601 | false | attribute | When the outreach record was created |
| `updated_at` | TIMESTAMPTZ | ISO-8601 | false | attribute | When the outreach record was last updated |

---

# Sub-Hub: company_target


## company_target

Authoritative company list for outreach — 95,837 records. Source of company identity within outreach hub.

| Owning Sub-Hub | Leaf Type | Source of Truth | Row Identity |
|----------------|-----------|-----------------|--------------|
| company_target | CANONICAL | true | UUID |

| Column | Type | Format | Nullable | Semantic Role | Description |
|--------|------|--------|----------|---------------|-------------|
| `outreach_id` | UUID | UUID | false | foreign_key | FK to outreach.outreach spine table |
| `company_unique_id` | TEXT | STRING | false | identifier | Barton company identifier (04.04.01.YY.NNNNNN format) |
| `source` | TEXT | STRING | true | attribute | CL source system that originated this company record |

## company_target_errors

Error tracking for company target sub-hub

| Owning Sub-Hub | Leaf Type | Source of Truth | Row Identity |
|----------------|-----------|-----------------|--------------|
| company_target | ERROR | true | UUID |

| Column | Type | Format | Nullable | Semantic Role | Description |
|--------|------|--------|----------|---------------|-------------|
| `error_id` | UUID | UUID | false | identifier | Primary key for error record |
| `outreach_id` | UUID | UUID | true | foreign_key | FK to spine (nullable — error may occur before entity exists) |
| `error_type` | TEXT | ENUM | false | attribute | Discriminator column — classifies the error |
| `error_message` | TEXT | STRING | false | attribute | Human-readable error description |
| `created_at` | TIMESTAMPTZ | ISO-8601 | false | attribute | When the error was recorded |

---

# Sub-Hub: dol


## dol

DOL bridge table — links outreach companies to DOL Form 5500 filings via EIN. 70,150 records.

| Owning Sub-Hub | Leaf Type | Source of Truth | Row Identity |
|----------------|-----------|-----------------|--------------|
| dol | CANONICAL | true | UUID |

| Column | Type | Format | Nullable | Semantic Role | Description |
|--------|------|--------|----------|---------------|-------------|
| `outreach_id` | UUID | UUID | false | foreign_key | FK to outreach.outreach spine table |
| `ein` | TEXT | STRING | false | identifier | Employer Identification Number (9-digit, no dashes) |
| `filing_present` | BOOLEAN | BOOLEAN | true | attribute | Whether a Form 5500 filing exists for this EIN |
| `funding_type` | TEXT | ENUM | true | attribute | Benefit funding classification (pension_only, fully_insured, self_funded) |
| `renewal_month` | INTEGER | INTEGER | true | metric | Plan year begin month (1-12) |
| `outreach_start_month` | INTEGER | INTEGER | true | metric | 5 months before renewal month (1-12) — when to begin outreach |

## dol_errors

Error tracking for DOL filings sub-hub

| Owning Sub-Hub | Leaf Type | Source of Truth | Row Identity |
|----------------|-----------|-----------------|--------------|
| dol | ERROR | true | UUID |

| Column | Type | Format | Nullable | Semantic Role | Description |
|--------|------|--------|----------|---------------|-------------|
| `error_id` | UUID | UUID | false | identifier | Primary key for error record |
| `outreach_id` | UUID | UUID | true | foreign_key | FK to spine (nullable — error may occur before entity exists) |
| `error_type` | TEXT | ENUM | false | attribute | Discriminator column — classifies the DOL error |
| `error_message` | TEXT | STRING | false | attribute | Human-readable error description |
| `created_at` | TIMESTAMPTZ | ISO-8601 | false | attribute | When the error was recorded |

---

# Sub-Hub: people


## company_slot

Executive position slots per company — 285,012 slots, 177,757 filled (62.4%). CANONICAL table for people sub-hub.

| Owning Sub-Hub | Leaf Type | Source of Truth | Row Identity |
|----------------|-----------|-----------------|--------------|
| people | CANONICAL | true | UUID |

| Column | Type | Format | Nullable | Semantic Role | Description |
|--------|------|--------|----------|---------------|-------------|
| `slot_id` | UUID | UUID | false | identifier | Primary key for the slot record |
| `outreach_id` | UUID | UUID | false | foreign_key | FK to outreach.outreach spine table |
| `slot_type` | TEXT | ENUM | false | attribute | Executive role type (CEO, CFO, HR, CTO, CMO, COO) |
| `is_filled` | BOOLEAN | BOOLEAN | true | attribute | Whether this slot has an assigned person (TRUE = people record linked) |
| `person_unique_id` | TEXT | STRING | true | foreign_key | FK to people.people_master.unique_id (Barton ID format 04.04.02.YY.NNNNNN.NNN) |

## people_master

Contact and executive data — 182,946 records. SUPPORTING table (ADR-020) for people sub-hub.

| Owning Sub-Hub | Leaf Type | Source of Truth | Row Identity |
|----------------|-----------|-----------------|--------------|
| people | SUPPORTING | true | COMPOSITE |

| Column | Type | Format | Nullable | Semantic Role | Description |
|--------|------|--------|----------|---------------|-------------|
| `unique_id` | TEXT | STRING | false | identifier | Barton person identifier (04.04.02.YY.NNNNNN.NNN format, immutable) |
| `first_name` | TEXT | STRING | false | attribute | Person first name from Hunter, Clay, or manual enrichment |
| `last_name` | TEXT | STRING | false | attribute | Person last name from Hunter, Clay, or manual enrichment |
| `email` | TEXT | EMAIL | true | attribute | Person email address |
| `email_verified` | BOOLEAN | BOOLEAN | true | attribute | Whether email was checked via Million Verifier (TRUE = checked) |
| `outreach_ready` | BOOLEAN | BOOLEAN | true | attribute | Whether email is safe to send outreach (TRUE = VALID verified) |
| `linkedin_url` | TEXT | STRING | true | attribute | Person LinkedIn profile URL |

## people_errors

Error tracking for people intelligence sub-hub

| Owning Sub-Hub | Leaf Type | Source of Truth | Row Identity |
|----------------|-----------|-----------------|--------------|
| people | ERROR | true | UUID |

| Column | Type | Format | Nullable | Semantic Role | Description |
|--------|------|--------|----------|---------------|-------------|
| `error_id` | UUID | UUID | false | identifier | Primary key for error record |
| `outreach_id` | UUID | UUID | true | foreign_key | FK to spine (nullable — error may occur before entity exists) |
| `error_type` | TEXT | ENUM | false | attribute | Discriminator column (validation, ambiguity, conflict, missing_data, stale_data, external_fail) |
| `error_stage` | TEXT | ENUM | true | attribute | Pipeline stage where error occurred (slot_creation, slot_fill, etc.) |
| `error_message` | TEXT | STRING | false | attribute | Human-readable error description |
| `retry_strategy` | TEXT | ENUM | true | attribute | How to handle retry (manual_fix, auto_retry, discard) |
| `created_at` | TIMESTAMPTZ | ISO-8601 | false | attribute | When the error was recorded |

---

# Sub-Hub: blog


## blog

Blog content signals per outreach company — 95,004 records

| Owning Sub-Hub | Leaf Type | Source of Truth | Row Identity |
|----------------|-----------|-----------------|--------------|
| blog | CANONICAL | true | UUID |

| Column | Type | Format | Nullable | Semantic Role | Description |
|--------|------|--------|----------|---------------|-------------|
| `outreach_id` | UUID | UUID | false | foreign_key | FK to outreach.outreach spine table |

## blog_errors

Error tracking for blog content sub-hub

| Owning Sub-Hub | Leaf Type | Source of Truth | Row Identity |
|----------------|-----------|-----------------|--------------|
| blog | ERROR | true | UUID |

| Column | Type | Format | Nullable | Semantic Role | Description |
|--------|------|--------|----------|---------------|-------------|
| `error_id` | UUID | UUID | false | identifier | Primary key for error record |
| `outreach_id` | UUID | UUID | true | foreign_key | FK to spine (nullable — error may occur before entity exists) |
| `error_type` | TEXT | ENUM | false | attribute | Discriminator column — classifies the blog error (e.g., BLOG_MISSING) |
| `error_message` | TEXT | STRING | false | attribute | Human-readable error description |
| `created_at` | TIMESTAMPTZ | ISO-8601 | false | attribute | When the error was recorded |

---

# Sub-Hub: bit


## bit_scores

CLS authorization scores per company — 13,226 records

| Owning Sub-Hub | Leaf Type | Source of Truth | Row Identity |
|----------------|-----------|-----------------|--------------|
| bit | CANONICAL | true | UUID |

| Column | Type | Format | Nullable | Semantic Role | Description |
|--------|------|--------|----------|---------------|-------------|
| `outreach_id` | UUID | UUID | false | foreign_key | FK to outreach.outreach spine table |

## bit_errors

Error tracking for BIT/CLS scoring sub-hub

| Owning Sub-Hub | Leaf Type | Source of Truth | Row Identity |
|----------------|-----------|-----------------|--------------|
| bit | ERROR | true | UUID |

| Column | Type | Format | Nullable | Semantic Role | Description |
|--------|------|--------|----------|---------------|-------------|
| `error_id` | UUID | UUID | false | identifier | Primary key for error record |
| `outreach_id` | UUID | UUID | true | foreign_key | FK to spine (nullable — error may occur before entity exists) |
| `error_type` | TEXT | ENUM | false | attribute | Discriminator column — classifies the scoring error |
| `error_message` | TEXT | STRING | false | attribute | Human-readable error description |
| `created_at` | TIMESTAMPTZ | ISO-8601 | false | attribute | When the error was recorded |
