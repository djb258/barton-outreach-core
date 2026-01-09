# Outreach Hub - Schema Alignment Notes

## Purpose

This document describes the schema alignment for Outreach Execution's four internal
sub-hubs and their join relationships to Company Lifecycle (CL).

---

## Join Hierarchy

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              JOIN HIERARCHY                                  │
└─────────────────────────────────────────────────────────────────────────────┘

    COMPANY LIFECYCLE (CL)
    ──────────────────────
    marketing.company_master
        │
        │ company_unique_id (PK)
        │
        ▼
    ┌─────────────────────────────────────────────────────────────────────────┐
    │                         COMPANY TARGET                                   │
    │                    outreach.company_target                               │
    │                                                                         │
    │   company_unique_id (FK to CL) ◄──── THE JOIN POINT TO CL              │
    │   target_id (PK)               ◄──── Local Outreach identifier          │
    │   outreach_status                                                       │
    └───────────────────────────────┬─────────────────────────────────────────┘
                                    │
            ┌───────────────────────┼───────────────────────┐
            │                       │                       │
            ▼                       ▼                       ▼
    ┌───────────────┐       ┌───────────────┐       ┌───────────────┐
    │    PEOPLE     │       │      DOL      │       │     BLOG      │
    │               │       │               │       │   / Content   │
    │ target_id (FK)│       │ target_id (FK)│       │ target_id (FK)│
    │ company_uid   │       │ company_uid   │       │ company_uid   │
    └───────────────┘       └───────────────┘       └───────────────┘

    ⚠️  People, DOL, Blog join to Company Target, NOT directly to CL
```

---

## 1. Company Target ↔ CL Join

### Join Definition

```sql
-- Company Target is the ONLY Outreach table that joins directly to CL
SELECT
    ct.target_id,
    ct.company_unique_id,
    ct.outreach_status,
    cm.company_name,
    cm.domain,
    cm.lifecycle_state  -- Read-only from CL
FROM outreach.company_target ct
INNER JOIN marketing.company_master cm
    ON ct.company_unique_id = cm.company_unique_id;
```

### Schema

```sql
CREATE TABLE outreach.company_target (
    -- Primary key (Outreach-local)
    target_id TEXT PRIMARY KEY,

    -- Foreign key to CL (MANDATORY)
    company_unique_id TEXT NOT NULL,

    -- Outreach-specific status (not lifecycle state)
    outreach_status TEXT NOT NULL DEFAULT 'queued',
    -- Values: queued, active, exhausted, paused, opted_out

    -- Targeting context
    bit_score_snapshot NUMERIC,           -- Cached BIT score
    first_targeted_at TIMESTAMP,
    last_targeted_at TIMESTAMP,
    sequence_count INTEGER DEFAULT 0,
    total_sends INTEGER DEFAULT 0,
    total_opens INTEGER DEFAULT 0,
    total_replies INTEGER DEFAULT 0,

    -- Metadata
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),

    -- CONSTRAINT: Must reference CL
    CONSTRAINT fk_company_lifecycle
        FOREIGN KEY (company_unique_id)
        REFERENCES marketing.company_master(company_unique_id)
        ON DELETE RESTRICT  -- Cannot delete company with active target
);

-- Indexes
CREATE UNIQUE INDEX idx_target_company ON outreach.company_target(company_unique_id);
CREATE INDEX idx_target_status ON outreach.company_target(outreach_status);
```

### Join Rules

| Rule | Enforcement |
|------|-------------|
| company_unique_id is NOT NULL | CONSTRAINT |
| company_unique_id must exist in CL | FOREIGN KEY |
| One target per company | UNIQUE INDEX |
| Cannot delete CL company with active target | ON DELETE RESTRICT |

---

## 2. People ↔ Company Target Join

### Join Definition

```sql
-- People join to Company Target, NOT directly to CL
SELECT
    p.person_id,
    p.target_id,
    p.company_unique_id,  -- Denormalized for query convenience
    ct.outreach_status
FROM outreach.people p
INNER JOIN outreach.company_target ct
    ON p.target_id = ct.target_id;
```

### Schema

```sql
CREATE TABLE outreach.people (
    -- Primary key
    person_id TEXT PRIMARY KEY,

    -- Foreign key to Company Target (MANDATORY)
    target_id TEXT NOT NULL,

    -- CL identity (denormalized, must match target's company_unique_id)
    company_unique_id TEXT NOT NULL,

    -- Person data (Outreach context)
    slot_type TEXT,                       -- CHRO, HR_MANAGER, etc.
    email TEXT,
    email_verified BOOLEAN DEFAULT FALSE,
    contact_status TEXT DEFAULT 'active', -- active, bounced, opted_out
    last_contacted_at TIMESTAMP,
    contact_count INTEGER DEFAULT 0,

    -- Metadata
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),

    -- CONSTRAINTS
    CONSTRAINT fk_target
        FOREIGN KEY (target_id)
        REFERENCES outreach.company_target(target_id)
        ON DELETE CASCADE,

    -- Ensure company_unique_id matches target's
    CONSTRAINT fk_company_match
        FOREIGN KEY (company_unique_id)
        REFERENCES marketing.company_master(company_unique_id)
);

-- Indexes
CREATE INDEX idx_people_target ON outreach.people(target_id);
CREATE INDEX idx_people_company ON outreach.people(company_unique_id);
```

### Join Rules

| Rule | Enforcement |
|------|-------------|
| target_id is NOT NULL | CONSTRAINT |
| target_id must exist in company_target | FOREIGN KEY |
| company_unique_id must match target's | Application logic |
| Cascade delete when target deleted | ON DELETE CASCADE |

---

## 3. DOL ↔ Company Target Join

### Join Definition

```sql
-- DOL joins to Company Target, NOT directly to CL
SELECT
    d.filing_id,
    d.target_id,
    d.company_unique_id,
    d.plan_year_end,
    d.renewal_approaching
FROM outreach.dol_filings d
INNER JOIN outreach.company_target ct
    ON d.target_id = ct.target_id;
```

### Schema

```sql
CREATE TABLE outreach.dol_filings (
    -- Primary key
    filing_id TEXT PRIMARY KEY,

    -- Foreign key to Company Target (MANDATORY)
    target_id TEXT NOT NULL,

    -- CL identity (denormalized)
    company_unique_id TEXT NOT NULL,

    -- DOL data (Outreach context)
    form_type TEXT,                       -- 5500, 5500-SF
    plan_year_end DATE,
    renewal_approaching BOOLEAN DEFAULT FALSE,
    days_until_renewal INTEGER,
    participant_count INTEGER,
    total_assets NUMERIC,

    -- Signal flags
    is_new_filing BOOLEAN DEFAULT FALSE,
    is_plan_change BOOLEAN DEFAULT FALSE,

    -- Metadata
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),

    -- CONSTRAINTS
    CONSTRAINT fk_target
        FOREIGN KEY (target_id)
        REFERENCES outreach.company_target(target_id)
        ON DELETE CASCADE
);

-- Indexes
CREATE INDEX idx_dol_target ON outreach.dol_filings(target_id);
CREATE INDEX idx_dol_renewal ON outreach.dol_filings(renewal_approaching, days_until_renewal);
```

---

## 4. Blog / Content ↔ Company Target Join

### Join Definition

```sql
-- Blog/Content joins to Company Target, NOT directly to CL
SELECT
    b.signal_id,
    b.target_id,
    b.company_unique_id,
    b.signal_type,
    b.detected_at
FROM outreach.blog_signals b
INNER JOIN outreach.company_target ct
    ON b.target_id = ct.target_id;
```

### Schema

```sql
CREATE TABLE outreach.blog_signals (
    -- Primary key
    signal_id TEXT PRIMARY KEY,

    -- Foreign key to Company Target (MANDATORY)
    target_id TEXT NOT NULL,

    -- CL identity (denormalized)
    company_unique_id TEXT NOT NULL,

    -- Signal data
    signal_type TEXT NOT NULL,           -- news, blog_mention, press_release
    source_url TEXT,
    headline TEXT,
    sentiment TEXT,                       -- positive, neutral, negative
    relevance_score NUMERIC,
    detected_at TIMESTAMP NOT NULL,

    -- BIT impact
    bit_impact INTEGER DEFAULT 0,         -- -100 to +100

    -- Metadata
    created_at TIMESTAMP DEFAULT NOW(),

    -- CONSTRAINTS
    CONSTRAINT fk_target
        FOREIGN KEY (target_id)
        REFERENCES outreach.company_target(target_id)
        ON DELETE CASCADE
);

-- Indexes
CREATE INDEX idx_blog_target ON outreach.blog_signals(target_id);
CREATE INDEX idx_blog_detected ON outreach.blog_signals(detected_at);
CREATE INDEX idx_blog_type ON outreach.blog_signals(signal_type);
```

---

## Prohibited Joins

### Direct CL Joins (PROHIBITED)

```sql
-- ❌ PROHIBITED: People joining directly to CL
SELECT p.*
FROM outreach.people p
INNER JOIN marketing.company_master cm  -- VIOLATION!
    ON p.company_unique_id = cm.company_unique_id;

-- ❌ PROHIBITED: DOL joining directly to CL
SELECT d.*
FROM outreach.dol_filings d
INNER JOIN marketing.company_master cm  -- VIOLATION!
    ON d.company_unique_id = cm.company_unique_id;

-- ❌ PROHIBITED: Blog joining directly to CL
SELECT b.*
FROM outreach.blog_signals b
INNER JOIN marketing.company_master cm  -- VIOLATION!
    ON b.company_unique_id = cm.company_unique_id;
```

### Why Prohibited

1. **Violates hierarchy** - Sub-hubs must route through Company Target
2. **Bypasses target context** - Loses outreach_status, targeting data
3. **Breaks cascade deletes** - Records orphaned if target removed
4. **Violates doctrine** - CL is not directly accessible to sub-hubs

---

## Correct Join Patterns

### Full Chain Join

```sql
-- ✅ CORRECT: Full chain from sub-hub through Target to CL
SELECT
    p.person_id,
    p.email,
    ct.target_id,
    ct.outreach_status,
    cm.company_name,
    cm.domain
FROM outreach.people p
INNER JOIN outreach.company_target ct ON p.target_id = ct.target_id
INNER JOIN marketing.company_master cm ON ct.company_unique_id = cm.company_unique_id;
```

### Aggregating Across Sub-Hubs

```sql
-- ✅ CORRECT: Joining multiple sub-hubs through Company Target
SELECT
    ct.target_id,
    ct.company_unique_id,
    COUNT(DISTINCT p.person_id) AS people_count,
    COUNT(DISTINCT d.filing_id) AS filing_count,
    COUNT(DISTINCT b.signal_id) AS signal_count
FROM outreach.company_target ct
LEFT JOIN outreach.people p ON ct.target_id = p.target_id
LEFT JOIN outreach.dol_filings d ON ct.target_id = d.target_id
LEFT JOIN outreach.blog_signals b ON ct.target_id = b.target_id
GROUP BY ct.target_id, ct.company_unique_id;
```

---

## Denormalization Note

### Why company_unique_id is Denormalized

Sub-hub tables include `company_unique_id` even though it can be derived via `target_id`:

```sql
-- Technically redundant but included for:
-- 1. Query performance (avoid join for common lookups)
-- 2. Audit trail (know which CL company at insert time)
-- 3. Data integrity checks (can verify against target's company_unique_id)
```

### Integrity Check

```sql
-- Verify denormalized company_unique_id matches target
SELECT p.person_id, p.company_unique_id, ct.company_unique_id
FROM outreach.people p
INNER JOIN outreach.company_target ct ON p.target_id = ct.target_id
WHERE p.company_unique_id != ct.company_unique_id;
-- Expected result: 0 rows (no mismatches)
```

---

## Summary Table

| Sub-Hub | Joins To | Via Column | Direct CL Join |
|---------|----------|------------|----------------|
| Company Target | CL | company_unique_id | ✅ YES (only one) |
| People | Company Target | target_id | ❌ PROHIBITED |
| DOL | Company Target | target_id | ❌ PROHIBITED |
| Blog / Content | Company Target | target_id | ❌ PROHIBITED |

---

*Last Updated: 2025-12-26*
*Doctrine Version: CL Parent-Child Model v1.1*
