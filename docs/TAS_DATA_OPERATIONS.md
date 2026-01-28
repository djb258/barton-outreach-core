# Technical Architecture Specification: Data Operations

**Repository**: barton-outreach-core
**Version**: 1.0.0
**Generated**: 2026-01-28
**Source**: Neon PostgreSQL (live database)
**Purpose**: Unambiguous operational guide for data lookups, joins, and flows

---

## How to Use This Document

This document answers:
1. **"Where do I find X?"** → Table Lookup Guide
2. **"How do I join A to B?"** → Join Path Reference
3. **"What's the flow for operation Y?"** → Data Flow Sequences
4. **"Which tables are involved in Z?"** → Use Case Tables

**RULE**: If you need data, check this document FIRST. Do not guess.

---

## Table of Contents

1. [Primary Key Reference](#1-primary-key-reference)
2. [Join Path Reference](#2-join-path-reference)
3. [Data Lookup Guide](#3-data-lookup-guide)
4. [Data Flow Sequences](#4-data-flow-sequences)
5. [Use Case Query Patterns](#5-use-case-query-patterns)
6. [Sub-Hub Table Ownership](#6-sub-hub-table-ownership)

---

## 1. Primary Key Reference

### Authority Registry (CL)

| Table | Primary Key | Type | Notes |
|-------|-------------|------|-------|
| `cl.company_identity` | `company_unique_id` | UUID | **AUTHORITY SOURCE** - All identity lookups start here |
| `cl.company_domains` | `domain_id` | UUID | FK: `company_unique_id` |
| `cl.company_names` | `name_id` | UUID | FK: `company_unique_id` |
| `cl.identity_confidence` | `company_unique_id` | UUID | PK is also FK |

### Outreach Spine

| Table | Primary Key | Type | Notes |
|-------|-------------|------|-------|
| `outreach.outreach` | `outreach_id` | UUID | **OPERATIONAL SPINE** - All sub-hub lookups join here |
| `outreach.company_target` | `target_id` | UUID | FK: `outreach_id` |
| `outreach.dol` | `dol_id` | UUID | FK: `outreach_id` |
| `outreach.people` | `person_id` | UUID | FK: `outreach_id` |
| `outreach.blog` | `blog_id` | UUID | FK: `outreach_id` |
| `outreach.bit_scores` | `outreach_id` | UUID | PK is also FK |
| `outreach.bit_signals` | `signal_id` | UUID | FK: `outreach_id` |
| `outreach.manual_overrides` | `override_id` | UUID | FK: `outreach_id` |

### People Intelligence

| Table | Primary Key | Type | Notes |
|-------|-------------|------|-------|
| `people.people_master` | `unique_id` | UUID | **PERSON SOURCE** |
| `people.company_slot` | `slot_id` | UUID | FK: `company_unique_id`, `person_unique_id` |

### DOL Filings

| Table | Primary Key | Type | Notes |
|-------|-------------|------|-------|
| `dol.form_5500` | `filing_id` | TEXT | **DOL SOURCE** |
| `dol.schedule_a` | `schedule_id` | UUID | FK: `filing_id` |
| `dol.ein_urls` | `ein` | TEXT | EIN is PK |
| `dol.renewal_calendar` | `renewal_id` | UUID | FK: `filing_id` |

---

## 2. Join Path Reference

### CL → Outreach (Identity to Operations)

```sql
-- Get outreach data for a company
SELECT o.*
FROM cl.company_identity ci
JOIN outreach.outreach o ON o.outreach_id = ci.outreach_id
WHERE ci.company_unique_id = $company_id;

-- IMPORTANT: ci.outreach_id is WRITE-ONCE
-- If ci.outreach_id IS NULL, company is NOT in outreach
```

### Outreach Spine → Sub-Hubs

```sql
-- Company Target (04.04.01)
SELECT ct.*
FROM outreach.outreach o
JOIN outreach.company_target ct ON ct.outreach_id = o.outreach_id
WHERE o.outreach_id = $outreach_id;

-- DOL Filings (04.04.03)
SELECT d.*
FROM outreach.outreach o
JOIN outreach.dol d ON d.outreach_id = o.outreach_id
WHERE o.outreach_id = $outreach_id;

-- People (04.04.02)
SELECT p.*
FROM outreach.outreach o
JOIN outreach.people p ON p.outreach_id = o.outreach_id
WHERE o.outreach_id = $outreach_id;

-- Blog (04.04.05)
SELECT b.*
FROM outreach.outreach o
JOIN outreach.blog b ON b.outreach_id = o.outreach_id
WHERE o.outreach_id = $outreach_id;

-- BIT Scores
SELECT bs.*
FROM outreach.outreach o
JOIN outreach.bit_scores bs ON bs.outreach_id = o.outreach_id
WHERE o.outreach_id = $outreach_id;
```

### Outreach DOL → DOL Source Tables

```sql
-- Get Form 5500 details for an outreach record
SELECT f.*
FROM outreach.dol od
JOIN dol.form_5500 f ON f.filing_id = od.filing_id
WHERE od.outreach_id = $outreach_id;

-- Get Schedule A (insurance) for an outreach record
SELECT sa.*
FROM outreach.dol od
JOIN dol.form_5500 f ON f.filing_id = od.filing_id
JOIN dol.schedule_a sa ON sa.filing_id = f.filing_id
WHERE od.outreach_id = $outreach_id;

-- Get renewal dates for an outreach record
SELECT rc.*
FROM outreach.dol od
JOIN dol.renewal_calendar rc ON rc.filing_id = od.filing_id
WHERE od.outreach_id = $outreach_id;
```

### Outreach People → People Source Tables

```sql
-- Get full person details for outreach people
SELECT pm.*
FROM outreach.people op
JOIN people.people_master pm ON pm.unique_id = op.person_unique_id::uuid
WHERE op.outreach_id = $outreach_id;

-- Get all slot assignments for a company
SELECT cs.*
FROM people.company_slot cs
WHERE cs.outreach_id = $outreach_id;

-- Get person with their slot assignment
SELECT pm.*, cs.slot_type, cs.is_filled
FROM people.people_master pm
JOIN people.company_slot cs ON cs.person_unique_id = pm.unique_id
WHERE cs.outreach_id = $outreach_id;
```

### Complete Company Profile Join

```sql
-- FULL PROFILE: Company with all outreach data
SELECT
    ci.company_unique_id,
    ci.company_name,
    ci.company_domain,
    ci.identity_status,
    ci.eligibility_status,
    o.outreach_id,
    o.created_at as outreach_created,
    ct.email_method,
    ct.confidence_score,
    ct.outreach_status,
    od.ein,
    od.form_5500_matched,
    bs.bit_score,
    bs.bit_tier,
    b.blog_url,
    b.signal_count as blog_signals
FROM cl.company_identity ci
LEFT JOIN outreach.outreach o ON o.outreach_id = ci.outreach_id
LEFT JOIN outreach.company_target ct ON ct.outreach_id = o.outreach_id
LEFT JOIN outreach.dol od ON od.outreach_id = o.outreach_id
LEFT JOIN outreach.bit_scores bs ON bs.outreach_id = o.outreach_id
LEFT JOIN outreach.blog b ON b.outreach_id = o.outreach_id
WHERE ci.company_unique_id = $company_id;
```

---

## 3. Data Lookup Guide

### "I need to find a company by..."

| Lookup By | Table | Column | Query |
|-----------|-------|--------|-------|
| Company ID | `cl.company_identity` | `company_unique_id` | `WHERE company_unique_id = $id` |
| Sovereign ID | `cl.company_identity` | `sovereign_company_id` | `WHERE sovereign_company_id = $sid` |
| Domain | `cl.company_identity` | `normalized_domain` | `WHERE normalized_domain = $domain` |
| Company Name | `cl.company_identity` | `company_name` | `WHERE company_name ILIKE $name` |
| Outreach ID | `outreach.outreach` | `outreach_id` | `WHERE outreach_id = $oid` |
| EIN | `outreach.dol` | `ein` | `WHERE ein = $ein` |

### "I need to find a person by..."

| Lookup By | Table | Column | Query |
|-----------|-------|--------|-------|
| Person ID | `people.people_master` | `unique_id` | `WHERE unique_id = $id` |
| Email | `people.people_master` | `email` | `WHERE email = $email` |
| Company | `people.people_master` | `company_unique_id` | `WHERE company_unique_id = $cid` |
| LinkedIn | `people.people_master` | `linkedin_url` | `WHERE linkedin_url = $url` |
| Slot Type | `people.company_slot` | `slot_type` | `WHERE slot_type = $type` |

### "I need to find DOL data by..."

| Lookup By | Table | Column | Query |
|-----------|-------|--------|-------|
| EIN | `dol.form_5500` | `ein` | `WHERE ein = $ein` |
| Filing ID | `dol.form_5500` | `filing_id` | `WHERE filing_id = $fid` |
| Sponsor Name | `dol.form_5500` | `sponsor_name` | `WHERE sponsor_name ILIKE $name` |
| Plan Year | `dol.form_5500` | `plan_year` | `WHERE plan_year = $year` |
| Renewal Date | `dol.renewal_calendar` | `renewal_date` | `WHERE renewal_date BETWEEN $start AND $end` |

### "I need outreach status for..."

| Need | Table | Columns |
|------|-------|---------|
| Is company in outreach? | `cl.company_identity` | `outreach_id IS NOT NULL` |
| Outreach status | `outreach.company_target` | `outreach_status`, `execution_status` |
| BIT tier | `outreach.bit_scores` | `bit_tier`, `bit_score` |
| Email pattern | `outreach.company_target` | `email_method`, `method_type`, `confidence_score` |
| DOL match status | `outreach.dol` | `form_5500_matched`, `schedule_a_matched` |
| Kill switch active? | `outreach.manual_overrides` | `is_active = true` |

---

## 4. Data Flow Sequences

### Flow 1: New Company Intake → Outreach Init

```
STEP 1: Check if company exists in CL
┌─────────────────────────────────────────────────────────────┐
│ SELECT * FROM cl.company_identity                           │
│ WHERE company_unique_id = $id OR normalized_domain = $dom;  │
└─────────────────────────────────────────────────────────────┘
        │
        ▼
STEP 2: If exists, check if already in outreach
┌─────────────────────────────────────────────────────────────┐
│ SELECT outreach_id FROM cl.company_identity                 │
│ WHERE company_unique_id = $id;                              │
│                                                             │
│ IF outreach_id IS NOT NULL → STOP (already claimed)         │
│ IF outreach_id IS NULL → PROCEED                            │
└─────────────────────────────────────────────────────────────┘
        │
        ▼
STEP 3: Mint outreach_id in operational spine
┌─────────────────────────────────────────────────────────────┐
│ INSERT INTO outreach.outreach (outreach_id, sovereign_id)   │
│ VALUES (gen_random_uuid(), $sovereign_id)                   │
│ RETURNING outreach_id;                                      │
└─────────────────────────────────────────────────────────────┘
        │
        ▼
STEP 4: Register outreach_id in CL (WRITE-ONCE)
┌─────────────────────────────────────────────────────────────┐
│ UPDATE cl.company_identity                                  │
│ SET outreach_id = $new_outreach_id,                         │
│     outreach_attached_at = NOW()                            │
│ WHERE company_unique_id = $id                               │
│   AND outreach_id IS NULL; -- CRITICAL: prevents overwrite  │
│                                                             │
│ IF affected_rows != 1 → ROLLBACK, HARD FAIL                 │
└─────────────────────────────────────────────────────────────┘
```

### Flow 2: Company Target Sub-Hub (04.04.01)

```
INPUT: outreach_id from spine
        │
        ▼
STEP 1: Get company domain from CL
┌─────────────────────────────────────────────────────────────┐
│ SELECT ci.company_domain, ci.normalized_domain              │
│ FROM outreach.outreach o                                    │
│ JOIN cl.company_identity ci ON ci.outreach_id = o.outreach_id│
│ WHERE o.outreach_id = $outreach_id;                         │
└─────────────────────────────────────────────────────────────┘
        │
        ▼
STEP 2: Execute domain resolution + email pattern discovery
        │
        ▼
STEP 3: Write results to company_target
┌─────────────────────────────────────────────────────────────┐
│ INSERT INTO outreach.company_target                         │
│ (target_id, outreach_id, email_method, method_type,         │
│  confidence_score, is_catchall, outreach_status)            │
│ VALUES ($target_id, $outreach_id, $email_method, ...)       │
│ ON CONFLICT (outreach_id) DO UPDATE SET ...;                │
└─────────────────────────────────────────────────────────────┘
        │
        ▼
OUTPUT: PASS/FAIL to next sub-hub
```

### Flow 3: DOL Sub-Hub (04.04.03)

```
INPUT: outreach_id from spine (requires Company Target PASS)
        │
        ▼
STEP 1: Get company name/domain for EIN matching
┌─────────────────────────────────────────────────────────────┐
│ SELECT ci.company_name, ci.normalized_domain                │
│ FROM outreach.outreach o                                    │
│ JOIN cl.company_identity ci ON ci.outreach_id = o.outreach_id│
│ WHERE o.outreach_id = $outreach_id;                         │
└─────────────────────────────────────────────────────────────┘
        │
        ▼
STEP 2: Search DOL filings by name/EIN
┌─────────────────────────────────────────────────────────────┐
│ SELECT f.*                                                  │
│ FROM dol.form_5500 f                                        │
│ WHERE f.sponsor_name ILIKE '%' || $company_name || '%'      │
│    OR f.ein IN (SELECT ein FROM dol.ein_urls                │
│                 WHERE url ILIKE '%' || $domain || '%');     │
└─────────────────────────────────────────────────────────────┘
        │
        ▼
STEP 3: If match found, check Schedule A
┌─────────────────────────────────────────────────────────────┐
│ SELECT sa.*                                                 │
│ FROM dol.schedule_a sa                                      │
│ WHERE sa.filing_id = $matched_filing_id;                    │
└─────────────────────────────────────────────────────────────┘
        │
        ▼
STEP 4: Write results to outreach.dol
┌─────────────────────────────────────────────────────────────┐
│ INSERT INTO outreach.dol                                    │
│ (dol_id, outreach_id, ein, filing_id, form_5500_matched,    │
│  schedule_a_matched, match_confidence, match_method)        │
│ VALUES (...);                                               │
└─────────────────────────────────────────────────────────────┘
        │
        ▼
OUTPUT: PASS/FAIL to next sub-hub
```

### Flow 4: People Intelligence Sub-Hub (04.04.02)

```
INPUT: outreach_id from spine (requires DOL PASS)
        │
        ▼
STEP 1: Get company info
┌─────────────────────────────────────────────────────────────┐
│ SELECT ci.company_unique_id, ct.email_method                │
│ FROM outreach.outreach o                                    │
│ JOIN cl.company_identity ci ON ci.outreach_id = o.outreach_id│
│ JOIN outreach.company_target ct ON ct.outreach_id = o.outreach_id│
│ WHERE o.outreach_id = $outreach_id;                         │
└─────────────────────────────────────────────────────────────┘
        │
        ▼
STEP 2: Find people for company
┌─────────────────────────────────────────────────────────────┐
│ SELECT pm.*                                                 │
│ FROM people.people_master pm                                │
│ WHERE pm.company_unique_id = $company_unique_id;            │
└─────────────────────────────────────────────────────────────┘
        │
        ▼
STEP 3: Assign to slots
┌─────────────────────────────────────────────────────────────┐
│ INSERT INTO people.company_slot                             │
│ (slot_id, company_unique_id, outreach_id, slot_type,        │
│  person_unique_id, is_filled, filled_at)                    │
│ VALUES (...);                                               │
└─────────────────────────────────────────────────────────────┘
        │
        ▼
STEP 4: Generate emails using company email pattern
┌─────────────────────────────────────────────────────────────┐
│ -- Use email_method from company_target                     │
│ -- Pattern: {first}.{last}@domain.com                       │
│ -- Generate: john.smith@acme.com                            │
└─────────────────────────────────────────────────────────────┘
        │
        ▼
STEP 5: Write to outreach.people
┌─────────────────────────────────────────────────────────────┐
│ INSERT INTO outreach.people                                 │
│ (person_id, outreach_id, person_unique_id, slot_type,       │
│  email, email_verified)                                     │
│ VALUES (...);                                               │
└─────────────────────────────────────────────────────────────┘
        │
        ▼
OUTPUT: PASS/FAIL to next sub-hub
```

### Flow 5: BIT Score Calculation

```
INPUT: outreach_id (after all sub-hubs complete)
        │
        ▼
STEP 1: Gather all signals
┌─────────────────────────────────────────────────────────────┐
│ -- DOL signals                                              │
│ SELECT 'DOL_FILING' as type, 20 as impact                   │
│ FROM outreach.dol WHERE outreach_id = $oid AND form_5500_matched;│
│                                                             │
│ -- Blog signals                                             │
│ SELECT 'BLOG_PRESSURE' as type, signal_count * 5 as impact  │
│ FROM outreach.blog WHERE outreach_id = $oid;                │
│                                                             │
│ -- Movement signals                                         │
│ SELECT 'MOVEMENT' as type, 15 as impact                     │
│ FROM people.person_movement_history pmh                     │
│ JOIN outreach.people op ON op.person_unique_id = pmh.person_unique_id│
│ WHERE op.outreach_id = $oid;                                │
└─────────────────────────────────────────────────────────────┘
        │
        ▼
STEP 2: Calculate score (sum of impacts, max 100)
        │
        ▼
STEP 3: Assign tier
┌─────────────────────────────────────────────────────────────┐
│ PLATINUM: bit_score >= 80                                   │
│ GOLD:     bit_score >= 60 AND bit_score < 80                │
│ SILVER:   bit_score >= 40 AND bit_score < 60                │
│ BRONZE:   bit_score >= 20 AND bit_score < 40                │
│ NONE:     bit_score < 20                                    │
└─────────────────────────────────────────────────────────────┘
        │
        ▼
STEP 4: Write to bit_scores
┌─────────────────────────────────────────────────────────────┐
│ INSERT INTO outreach.bit_scores                             │
│ (outreach_id, bit_score, bit_tier, signal_count)            │
│ VALUES ($oid, $score, $tier, $signal_count)                 │
│ ON CONFLICT (outreach_id) DO UPDATE SET ...;                │
└─────────────────────────────────────────────────────────────┘
```

---

## 5. Use Case Query Patterns

### Use Case: Marketing Eligibility Check

```sql
-- AUTHORITATIVE VIEW (FROZEN v1.0)
SELECT * FROM outreach.vw_marketing_eligibility_with_overrides
WHERE outreach_id = $outreach_id;

-- Manual query equivalent:
SELECT
    o.outreach_id,
    ci.company_name,
    ci.eligibility_status,
    ct.outreach_status,
    ct.email_method IS NOT NULL as has_email_pattern,
    bs.bit_tier,
    mo.is_active as has_active_override,
    mo.override_type
FROM outreach.outreach o
JOIN cl.company_identity ci ON ci.outreach_id = o.outreach_id
LEFT JOIN outreach.company_target ct ON ct.outreach_id = o.outreach_id
LEFT JOIN outreach.bit_scores bs ON bs.outreach_id = o.outreach_id
LEFT JOIN outreach.manual_overrides mo ON mo.outreach_id = o.outreach_id
    AND mo.is_active = true
WHERE o.outreach_id = $outreach_id;
```

### Use Case: Get All Contacts for Outreach

```sql
SELECT
    op.email,
    op.slot_type,
    op.email_verified,
    pm.full_name,
    pm.title,
    pm.linkedin_url,
    ct.email_method as pattern_used
FROM outreach.people op
JOIN people.people_master pm ON pm.unique_id = op.person_unique_id::uuid
JOIN outreach.company_target ct ON ct.outreach_id = op.outreach_id
WHERE op.outreach_id = $outreach_id
ORDER BY
    CASE op.slot_type
        WHEN 'CEO' THEN 1
        WHEN 'CFO' THEN 2
        WHEN 'HR' THEN 3
        ELSE 4
    END;
```

### Use Case: DOL Renewal Pipeline

```sql
SELECT
    ci.company_name,
    o.outreach_id,
    od.ein,
    f.sponsor_name,
    f.total_participants,
    rc.renewal_date,
    rc.days_until_renewal,
    bs.bit_tier
FROM dol.renewal_calendar rc
JOIN dol.form_5500 f ON f.filing_id = rc.filing_id
JOIN outreach.dol od ON od.filing_id = f.filing_id
JOIN outreach.outreach o ON o.outreach_id = od.outreach_id
JOIN cl.company_identity ci ON ci.outreach_id = o.outreach_id
LEFT JOIN outreach.bit_scores bs ON bs.outreach_id = o.outreach_id
WHERE rc.renewal_date BETWEEN CURRENT_DATE AND CURRENT_DATE + INTERVAL '90 days'
ORDER BY rc.renewal_date;
```

### Use Case: Slot Coverage Report

```sql
SELECT
    ci.company_name,
    o.outreach_id,
    cs.slot_type,
    cs.is_filled,
    pm.full_name,
    pm.email,
    pm.title
FROM outreach.outreach o
JOIN cl.company_identity ci ON ci.outreach_id = o.outreach_id
LEFT JOIN people.company_slot cs ON cs.outreach_id = o.outreach_id
LEFT JOIN people.people_master pm ON pm.unique_id = cs.person_unique_id
WHERE o.outreach_id = $outreach_id
ORDER BY
    CASE cs.slot_type
        WHEN 'CEO' THEN 1
        WHEN 'CFO' THEN 2
        WHEN 'HR' THEN 3
        ELSE 4
    END;
```

### Use Case: Company Full Profile

```sql
-- COMPLETE company profile with all sub-hub data
SELECT
    -- Identity
    ci.company_unique_id,
    ci.sovereign_company_id,
    ci.company_name,
    ci.company_domain,
    ci.normalized_domain,
    ci.identity_status,
    ci.eligibility_status,
    ci.exclusion_reason,

    -- Outreach spine
    o.outreach_id,
    o.created_at as outreach_initiated,

    -- Company Target (04.04.01)
    ct.email_method,
    ct.method_type,
    ct.confidence_score as email_confidence,
    ct.is_catchall,
    ct.outreach_status,
    ct.execution_status,

    -- DOL (04.04.03)
    od.ein,
    od.form_5500_matched,
    od.schedule_a_matched,
    od.match_confidence as dol_confidence,

    -- Blog (04.04.05)
    b.blog_url,
    b.rss_feed_url,
    b.signal_count as blog_signals,

    -- BIT
    bs.bit_score,
    bs.bit_tier,
    bs.signal_count as total_signals,

    -- Override status
    mo.override_type,
    mo.reason as override_reason,
    mo.is_active as override_active

FROM cl.company_identity ci
LEFT JOIN outreach.outreach o ON o.outreach_id = ci.outreach_id
LEFT JOIN outreach.company_target ct ON ct.outreach_id = o.outreach_id
LEFT JOIN outreach.dol od ON od.outreach_id = o.outreach_id
LEFT JOIN outreach.blog b ON b.outreach_id = o.outreach_id
LEFT JOIN outreach.bit_scores bs ON bs.outreach_id = o.outreach_id
LEFT JOIN outreach.manual_overrides mo ON mo.outreach_id = o.outreach_id AND mo.is_active = true
WHERE ci.company_unique_id = $company_id;
```

---

## 6. Sub-Hub Table Ownership

### Which Tables Belong to Which Sub-Hub?

| Sub-Hub | Doctrine ID | Tables Owned | Primary Table |
|---------|-------------|--------------|---------------|
| **CL Authority** | PARENT | `cl.*` (13 tables) | `cl.company_identity` |
| **Outreach Spine** | SPINE | `outreach.outreach` | `outreach.outreach` |
| **Company Target** | 04.04.01 | `outreach.company_target*` | `outreach.company_target` |
| **DOL Filings** | 04.04.03 | `outreach.dol*`, `dol.*` | `outreach.dol` |
| **People Intelligence** | 04.04.02 | `outreach.people*`, `people.*` | `outreach.people` |
| **Blog Content** | 04.04.05 | `outreach.blog*` | `outreach.blog` |
| **BIT Engine** | BIT | `outreach.bit_*`, `bit.*` | `outreach.bit_scores` |
| **Execution** | 04.04.04 | `outreach.campaigns`, `sequences`, `send_log` | `outreach.campaigns` |
| **Kill Switch** | CONTROL | `outreach.manual_overrides`, `override_audit_log` | `outreach.manual_overrides` |

### Read vs Write Permissions

| Sub-Hub | Can READ | Can WRITE |
|---------|----------|-----------|
| CL Authority | ALL | `cl.*` only |
| Company Target | `cl.*`, own tables | `outreach.company_target*` |
| DOL | `cl.*`, `dol.*`, own tables | `outreach.dol*` |
| People Intelligence | `cl.*`, `outreach.company_target`, `people.*`, own | `outreach.people*`, `people.company_slot` |
| Blog | `cl.*`, own tables | `outreach.blog*` |
| BIT Engine | ALL outreach tables | `outreach.bit_*` |

---

## Quick Reference Card

### Starting Points

| If You Need... | Start Here | Then Join To... |
|----------------|------------|-----------------|
| Company data | `cl.company_identity` | `outreach.outreach` via `outreach_id` |
| Outreach data | `outreach.outreach` | Sub-hub tables via `outreach_id` |
| Person data | `people.people_master` | `outreach.people` via `person_unique_id` |
| DOL filings | `dol.form_5500` | `outreach.dol` via `filing_id` |
| Slots | `people.company_slot` | `people.people_master` via `person_unique_id` |

### Critical Constraints

| Constraint | Location | Rule |
|------------|----------|------|
| WRITE-ONCE | `cl.company_identity.outreach_id` | Never overwrite, check IS NULL |
| FK Required | All sub-hub tables | Must have valid `outreach_id` |
| Spine First | `outreach.outreach` | Must exist before any sub-hub write |
| Waterfall Order | Sub-hubs | CT → DOL → People → Blog → BIT |

---

## Document Control

| Field | Value |
|-------|-------|
| Created | 2026-01-28 |
| Version | 1.0.0 |
| Author | Claude Code (AI Employee) |
| Source | Neon PostgreSQL (live queries) |
| Doctrine | DOCUMENTATION_ERD_DOCTRINE.md v1.0.0 |
