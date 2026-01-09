# Neon PostgreSQL Table Ownership

## Overview

This document defines which repository/hub owns which tables in the shared
Neon PostgreSQL database. Table ownership determines write authority.

**Database**: Neon PostgreSQL
**Host**: `ep-ancient-waterfall-a42vy0du-pooler.us-east-1.aws.neon.tech`

---

## Ownership Matrix

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         NEON TABLE OWNERSHIP                                 │
└─────────────────────────────────────────────────────────────────────────────┘

COMPANY LIFECYCLE (CL)                    OUTREACH EXECUTION
https://github.com/djb258/                https://github.com/djb258/
company-lifecycle-cl.git                  barton-outreach-core.git
─────────────────────────                 ─────────────────────────
cl.company_identity ◄────────────────────┐
cl.lifecycle_state                       │ company_unique_id (FK)
cl.lifecycle_history                     │
cl.external_id_mapping                   │
cl.merge_records                         │
cl.retirement_records                    │
                                         │
                                    outreach.company_target ────────────┐
                                    outreach.people ◄───────────────────┤
                                    outreach.dol_filings ◄──────────────┤
                                    outreach.blog_signals ◄─────────────┤
                                    outreach.campaigns                  │
                                    outreach.sequences                  │
                                    outreach.send_log                   │
                                    outreach.engagement_events          │
                                                                        │
                                                                        │
SITE SCOUT PRO (UI)                                                     │
https://github.com/djb258/site-scout-pro.git                           │
─────────────────────────                                               │
READ-ONLY ACCESS TO ALL TABLES ◄────────────────────────────────────────┘
```

---

## Schema: cl (Company Lifecycle)

**Owner**: company-lifecycle-cl
**GitHub**: https://github.com/djb258/company-lifecycle-cl.git

| Table | Write | Read | Purpose |
|-------|-------|------|---------|
| `cl.company_identity` | CL only | All | Sovereign company records |
| `cl.lifecycle_state` | CL only | All | Current lifecycle truth |
| `cl.lifecycle_history` | CL only | All | Append-only audit trail |
| `cl.external_id_mapping` | CL only | All | External system aliases |
| `cl.merge_records` | CL only | All | Identity consolidation audit |
| `cl.retirement_records` | CL only | All | Identity retirement audit |

### Primary Key

```sql
-- The sovereign identifier
company_unique_id TEXT PRIMARY KEY  -- Minted by CL only
```

### Schema Definition

```sql
CREATE SCHEMA IF NOT EXISTS cl;

-- Company Identity (sovereign record)
CREATE TABLE cl.company_identity (
    company_unique_id TEXT PRIMARY KEY,
    legal_name TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT NOW(),
    created_by TEXT NOT NULL
);

-- Lifecycle State (current truth)
CREATE TABLE cl.lifecycle_state (
    company_unique_id TEXT PRIMARY KEY REFERENCES cl.company_identity(company_unique_id),
    cl_stage TEXT NOT NULL CHECK (cl_stage IN ('OUTREACH', 'SALES', 'CLIENT', 'RETIRED')),
    outreach_uid TEXT,
    sales_uid TEXT,
    client_uid TEXT,
    promoted_at TIMESTAMP,
    promoted_by TEXT,
    retired_at TIMESTAMP,
    retired_by TEXT
);

-- Lifecycle History (append-only)
CREATE TABLE cl.lifecycle_history (
    history_id TEXT PRIMARY KEY,
    company_unique_id TEXT NOT NULL REFERENCES cl.company_identity(company_unique_id),
    event_type TEXT NOT NULL,
    from_state TEXT,
    to_state TEXT NOT NULL,
    triggered_by_event TEXT,
    actor TEXT NOT NULL,
    timestamp TIMESTAMP DEFAULT NOW(),
    evidence TEXT
);

-- External ID Mapping
CREATE TABLE cl.external_id_mapping (
    mapping_id TEXT PRIMARY KEY,
    company_unique_id TEXT NOT NULL REFERENCES cl.company_identity(company_unique_id),
    source_system TEXT NOT NULL,
    external_id TEXT NOT NULL,
    confidence TEXT CHECK (confidence IN ('HIGH', 'MEDIUM', 'LOW')),
    linked_at TIMESTAMP DEFAULT NOW(),
    linked_by TEXT,
    status TEXT DEFAULT 'active'
);
```

---

## Schema: outreach (Outreach Execution)

**Owner**: barton-outreach-core
**GitHub**: https://github.com/djb258/barton-outreach-core.git

| Table | Write | Read | Purpose |
|-------|-------|------|---------|
| `outreach.company_target` | Outreach | All | Internal anchor (FK to CL) |
| `outreach.people` | Outreach | All | Contact records |
| `outreach.dol_filings` | Outreach | All | DOL filing data |
| `outreach.blog_signals` | Outreach | All | News/content signals |
| `outreach.campaigns` | Outreach | All | Campaign definitions |
| `outreach.sequences` | Outreach | All | Sequence definitions |
| `outreach.send_log` | Outreach | All | Email send history |
| `outreach.engagement_events` | Outreach | All | Opens, clicks, replies |

### Foreign Key to CL

```sql
-- Company Target joins to CL (ONLY Outreach table with direct CL FK)
company_unique_id TEXT NOT NULL REFERENCES cl.company_identity(company_unique_id)
```

### Schema Definition

```sql
CREATE SCHEMA IF NOT EXISTS outreach;

-- Company Target (internal anchor)
CREATE TABLE outreach.company_target (
    target_id TEXT PRIMARY KEY,
    company_unique_id TEXT NOT NULL,
    outreach_status TEXT NOT NULL DEFAULT 'queued',
    bit_score_snapshot NUMERIC,
    first_targeted_at TIMESTAMP,
    last_targeted_at TIMESTAMP,
    sequence_count INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),

    CONSTRAINT fk_company_lifecycle
        FOREIGN KEY (company_unique_id)
        REFERENCES cl.company_identity(company_unique_id)
        ON DELETE RESTRICT
);

CREATE UNIQUE INDEX idx_target_company ON outreach.company_target(company_unique_id);

-- People (attaches to Company Target)
CREATE TABLE outreach.people (
    person_id TEXT PRIMARY KEY,
    target_id TEXT NOT NULL REFERENCES outreach.company_target(target_id) ON DELETE CASCADE,
    company_unique_id TEXT NOT NULL,
    slot_type TEXT,
    email TEXT,
    email_verified BOOLEAN DEFAULT FALSE,
    contact_status TEXT DEFAULT 'active',
    created_at TIMESTAMP DEFAULT NOW()
);

-- DOL Filings (attaches to Company Target)
CREATE TABLE outreach.dol_filings (
    filing_id TEXT PRIMARY KEY,
    target_id TEXT NOT NULL REFERENCES outreach.company_target(target_id) ON DELETE CASCADE,
    company_unique_id TEXT NOT NULL,
    form_type TEXT,
    plan_year_end DATE,
    renewal_approaching BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Blog Signals (attaches to Company Target)
CREATE TABLE outreach.blog_signals (
    signal_id TEXT PRIMARY KEY,
    target_id TEXT NOT NULL REFERENCES outreach.company_target(target_id) ON DELETE CASCADE,
    company_unique_id TEXT NOT NULL,
    signal_type TEXT NOT NULL,
    source_url TEXT,
    detected_at TIMESTAMP NOT NULL,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Campaigns
CREATE TABLE outreach.campaigns (
    campaign_id TEXT PRIMARY KEY,
    company_unique_id TEXT NOT NULL,
    campaign_name TEXT,
    status TEXT DEFAULT 'draft',
    created_at TIMESTAMP DEFAULT NOW()
);

-- Send Log
CREATE TABLE outreach.send_log (
    send_id TEXT PRIMARY KEY,
    campaign_id TEXT REFERENCES outreach.campaigns(campaign_id),
    company_unique_id TEXT NOT NULL,
    person_id TEXT,
    sent_at TIMESTAMP,
    status TEXT
);

-- Engagement Events
CREATE TABLE outreach.engagement_events (
    event_id TEXT PRIMARY KEY,
    send_id TEXT REFERENCES outreach.send_log(send_id),
    company_unique_id TEXT NOT NULL,
    event_type TEXT NOT NULL,  -- open, click, reply
    event_at TIMESTAMP DEFAULT NOW()
);
```

---

## Schema: marketing (Legacy/Shared)

**Owner**: Mixed (being migrated)
**GitHub**: barton-outreach-core (legacy location)

| Table | Current Owner | Target Owner | Notes |
|-------|---------------|--------------|-------|
| `marketing.company_master` | Legacy | CL | Migrate to cl.company_identity |
| `marketing.people_master` | People Hub | People Hub | Stays in People Hub |
| `marketing.company_slot` | People Hub | People Hub | Stays in People Hub |
| `marketing.data_enrichment_log` | Enrichment | Enrichment | Stays in Enrichment |

### Migration Path

```sql
-- Step 1: Create CL schema and tables (in CL repo)
-- Step 2: Migrate company_master data to cl.company_identity
-- Step 3: Update FKs in Outreach to point to cl.company_identity
-- Step 4: Deprecate marketing.company_master
```

---

## Schema: public (System)

**Owner**: Shared
**GitHub**: All repos

| Table | Write | Read | Purpose |
|-------|-------|------|---------|
| `public.shq_error_log` | All | All | System-wide error tracking |

---

## Access Control Summary

### By Repository

| Repository | Schemas | Write Access | Read Access |
|------------|---------|--------------|-------------|
| company-lifecycle-cl | cl | ✅ Full | ✅ Full |
| company-lifecycle-cl | outreach | ❌ None | ✅ Full |
| barton-outreach-core | cl | ❌ None | ✅ Full |
| barton-outreach-core | outreach | ✅ Full | ✅ Full |
| site-scout-pro | cl | ❌ None | ✅ Full |
| site-scout-pro | outreach | ❌ None | ✅ Full |
| site-scout-pro | marketing | ❌ None | ✅ Full |

### By Operation

| Operation | CL | Outreach | UI |
|-----------|-----|----------|-----|
| INSERT to cl.* | ✅ | ❌ | ❌ |
| UPDATE to cl.* | ✅ | ❌ | ❌ |
| DELETE from cl.* | ✅ | ❌ | ❌ |
| INSERT to outreach.* | ❌ | ✅ | ❌ |
| UPDATE to outreach.* | ❌ | ✅ | ❌ |
| DELETE from outreach.* | ❌ | ✅ | ❌ |
| SELECT from all | ✅ | ✅ | ✅ |

---

## Foreign Key Relationships

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                       FOREIGN KEY CHAIN                                      │
└─────────────────────────────────────────────────────────────────────────────┘

cl.company_identity
    │
    │ company_unique_id (PK)
    │
    ├──────► cl.lifecycle_state (1:1)
    ├──────► cl.lifecycle_history (1:many)
    ├──────► cl.external_id_mapping (1:many)
    │
    └──────► outreach.company_target (1:1)
                  │
                  │ target_id (PK)
                  │
                  ├──────► outreach.people (1:many)
                  ├──────► outreach.dol_filings (1:many)
                  └──────► outreach.blog_signals (1:many)
```

---

## Neon Connection Strings

### For CL Repository

```bash
# Write access to cl.* schema
DATABASE_URL=postgresql://cl_writer:${CL_PASSWORD}@ep-ancient-waterfall-a42vy0du-pooler.us-east-1.aws.neon.tech:5432/Marketing%20DB?sslmode=require
```

### For Outreach Repository

```bash
# Write access to outreach.* schema, read access to cl.*
DATABASE_URL=postgresql://outreach_writer:${OUTREACH_PASSWORD}@ep-ancient-waterfall-a42vy0du-pooler.us-east-1.aws.neon.tech:5432/Marketing%20DB?sslmode=require
```

### For UI Repository

```bash
# Read-only access to all schemas
DATABASE_URL=postgresql://ui_reader:${UI_PASSWORD}@ep-ancient-waterfall-a42vy0du-pooler.us-east-1.aws.neon.tech:5432/Marketing%20DB?sslmode=require
```

---

## Enforcement

### Row-Level Security (RLS)

```sql
-- CL tables: Only CL service account can write
ALTER TABLE cl.company_identity ENABLE ROW LEVEL SECURITY;
CREATE POLICY cl_write_policy ON cl.company_identity
    FOR ALL TO cl_writer USING (true);

-- Outreach tables: Only Outreach service account can write
ALTER TABLE outreach.company_target ENABLE ROW LEVEL SECURITY;
CREATE POLICY outreach_write_policy ON outreach.company_target
    FOR ALL TO outreach_writer USING (true);

-- UI: Read-only
GRANT SELECT ON ALL TABLES IN SCHEMA cl TO ui_reader;
GRANT SELECT ON ALL TABLES IN SCHEMA outreach TO ui_reader;
REVOKE INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA cl FROM ui_reader;
REVOKE INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA outreach FROM ui_reader;
```

---

## Summary

| Schema | Owner Repo | Owner Hub | GitHub URL |
|--------|------------|-----------|------------|
| `cl` | company-lifecycle-cl | HUB-CL-001 | https://github.com/djb258/company-lifecycle-cl.git |
| `outreach` | barton-outreach-core | HUB-OUTREACH | https://github.com/djb258/barton-outreach-core.git |
| `marketing` | Mixed (legacy) | Various | https://github.com/djb258/barton-outreach-core.git |
| `public` | Shared | System | All |

---

*Last Updated: 2025-12-26*
*Doctrine Version: CL Parent-Child Model v1.1*
