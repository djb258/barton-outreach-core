# PLE Schema Verification Report

**Date**: 2025-11-26
**Database**: Neon PostgreSQL - Marketing DB
**Status**: Partial Implementation (3/6 Core Tables Exist)

---

## Executive Summary

The current Neon PostgreSQL database has **3 out of 6** PLE specification tables implemented, with existing tables in the `marketing` schema that serve similar purposes but with different column names and additional fields. Three sidecar tables (`person_movement_history`, `person_scores`, `company_events`) are completely missing and need to be created.

---

## 1. Database Overview

### Schemas Present (12 total)
- **BIT** (empty) - Reserved for Buyer Intent Tool
- **PLE** (3 tables: ple_cycle, ple_log, ple_step) - PLE lifecycle tracking
- **archive** (46 tables) - Historical data
- **bit** (3 tables) - bit_company_score, bit_contact_score, bit_signal
- **company** (empty) - Reserved
- **intake** (2 tables) - company_raw_intake, people_raw_intake
- **marketing** (17 tables) - **PRIMARY SCHEMA** for core data
- **neon_auth** (1 table) - users_sync
- **people** (empty) - Reserved
- **ple** (3 tables) - ple_cycle, ple_log, ple_step
- **public** (3 tables) - agent_routing_log, garage_runs, shq_validation_log
- **shq** (1 table) - audit_log

**Total Tables**: 76 across all schemas

---

## 2. PLE Core Tables Status

### ✅ Table 1: `companies` → `marketing.company_master`

**Status**: EXISTS (with column name differences)

#### PLE Specification
```
- id (PK)
- company_uid (Unique ID)
- name
- linkedin_url
- employee_count
- state
- city
- industry
- source
- created_at
- updated_at
```

#### Current Implementation (`marketing.company_master`)
```sql
-- Primary Key
company_unique_id TEXT NOT NULL PRIMARY KEY  -- Equivalent to PLE: company_uid

-- Core Fields (matching PLE intent)
company_name TEXT NOT NULL                   -- Equivalent to PLE: name
linkedin_url TEXT NULL                       -- ✓ Matches PLE
employee_count INTEGER NULL                  -- ✓ Matches PLE
industry TEXT NULL                           -- ✓ Matches PLE
created_at TIMESTAMPTZ DEFAULT now()         -- ✓ Matches PLE
updated_at TIMESTAMPTZ DEFAULT now()         -- ✓ Matches PLE

-- State/City (differently structured)
address_city TEXT NULL                       -- Equivalent to PLE: city
address_state TEXT NULL                      -- Equivalent to PLE: state (full name)
state_abbrev TEXT NULL                       -- ℹ Extra: state abbreviation
address_zip TEXT NULL                        -- ℹ Extra: zip code

-- Source (differently named)
source_system TEXT NOT NULL                  -- Equivalent to PLE: source
source_record_id TEXT NULL                   -- ℹ Extra: original record ID

-- Additional Company Fields (not in PLE spec)
website_url TEXT NOT NULL
company_phone TEXT NULL
address_street TEXT NULL
address_country TEXT NULL
facebook_url TEXT NULL
twitter_url TEXT NULL
sic_codes TEXT NULL
founded_year INTEGER NULL
keywords TEXT[] NULL
description TEXT NULL
promoted_from_intake_at TIMESTAMPTZ NOT NULL DEFAULT now()
promotion_audit_log_id INTEGER NULL
import_batch_id TEXT NULL
validated_at TIMESTAMPTZ NULL
validated_by TEXT NULL
data_quality_score NUMERIC NULL
```

#### Comparison
| PLE Column | Current Column | Status | Notes |
|------------|----------------|--------|-------|
| `id` | `company_unique_id` | ⚠ Different name | Uses TEXT instead of INT |
| `company_uid` | `company_unique_id` | ⚠ Different name | Same semantic meaning |
| `name` | `company_name` | ⚠ Different name | Same semantic meaning |
| `linkedin_url` | `linkedin_url` | ✅ Match | |
| `employee_count` | `employee_count` | ✅ Match | |
| `state` | `address_state` + `state_abbrev` | ⚠ Split/renamed | Two columns instead of one |
| `city` | `address_city` | ⚠ Renamed | Same semantic meaning |
| `industry` | `industry` | ✅ Match | |
| `source` | `source_system` | ⚠ Renamed | Same semantic meaning |
| `created_at` | `created_at` | ✅ Match | |
| `updated_at` | `updated_at` | ✅ Match | |

**Extra Columns**: 18 additional fields for enrichment data, validation tracking, and extended company info

---

### ✅ Table 2: `company_slots` → `marketing.company_slot`

**Status**: EXISTS (with column name differences)

**Note**: There are TWO similar tables:
1. `marketing.company_slot` (active, with person assignments)
2. `marketing.company_slots` (appears to be a simpler reference table)

#### PLE Specification
```
- id (PK)
- slot_uid (Unique ID)
- company_id (FK → companies)
- slot_type (CEO/CFO/HR)
- person_id (FK → people)
- assigned_at
- vacated_at
```

#### Current Implementation (`marketing.company_slot`)
```sql
-- Primary Key
company_slot_unique_id TEXT NOT NULL PRIMARY KEY  -- Equivalent to PLE: slot_uid

-- Foreign Keys
company_unique_id TEXT NOT NULL                   -- Equivalent to PLE: company_id
  FOREIGN KEY → marketing.company_master.company_unique_id
person_unique_id TEXT NULL                        -- Equivalent to PLE: person_id
  FOREIGN KEY → marketing.people_master.unique_id

-- Slot Configuration
slot_type TEXT NOT NULL                           -- ✓ Matches PLE (CEO/CFO/HR)
is_filled BOOLEAN DEFAULT false                   -- ℹ Extra: quick status check
status VARCHAR DEFAULT 'open'                     -- ℹ Extra: open/filled/expired

-- Timestamps
created_at TIMESTAMPTZ DEFAULT now()              -- ℹ Extra: creation timestamp
filled_at TIMESTAMPTZ NULL                        -- Equivalent to PLE: assigned_at
last_refreshed_at TIMESTAMPTZ NULL                -- ℹ Extra: enrichment tracking

-- Enrichment & Quality
confidence_score NUMERIC NULL                     -- ℹ Extra: assignment confidence
filled_by TEXT NULL                               -- ℹ Extra: who/what filled this slot
source_system TEXT DEFAULT 'manual'               -- ℹ Extra: data source
enrichment_attempts INTEGER DEFAULT 0             -- ℹ Extra: retry tracking
```

#### Comparison
| PLE Column | Current Column | Status | Notes |
|------------|----------------|--------|-------|
| `id` | `company_slot_unique_id` | ⚠ Different name | Uses TEXT instead of INT |
| `slot_uid` | `company_slot_unique_id` | ⚠ Different name | Same semantic meaning |
| `company_id` | `company_unique_id` | ⚠ Different name | Same semantic meaning |
| `slot_type` | `slot_type` | ✅ Match | CEO/CFO/HR |
| `person_id` | `person_unique_id` | ⚠ Different name | Same semantic meaning |
| `assigned_at` | `filled_at` | ⚠ Different name | Same semantic meaning |
| `vacated_at` | ❌ Missing | ❌ Missing | Need to add for movement tracking |

**Extra Columns**: 6 additional fields for enrichment tracking, confidence scoring, and status management

**Constraint Notes**:
- Has UNIQUE constraints on `(company_unique_id, slot_type)` - ensures one slot per type per company
- Foreign keys properly enforce referential integrity

---

### ✅ Table 3: `people` → `marketing.people_master`

**Status**: EXISTS (with column name differences)

#### PLE Specification
```
- id (PK)
- person_uid (Unique ID)
- company_id (FK → companies)
- linkedin_url
- email
- first_name
- last_name
- title
- validation_status
- last_verified_at
- last_enrichment_attempt
- created_at
- updated_at
```

#### Current Implementation (`marketing.people_master`)
```sql
-- Primary Key
unique_id TEXT NOT NULL PRIMARY KEY               -- Equivalent to PLE: person_uid

-- Foreign Keys
company_unique_id TEXT NOT NULL                   -- Equivalent to PLE: company_id
company_slot_unique_id TEXT NOT NULL              -- ℹ Extra: direct slot link

-- Core Identity Fields (matching PLE)
first_name TEXT NOT NULL                          -- ✓ Matches PLE
last_name TEXT NOT NULL                           -- ✓ Matches PLE
full_name TEXT NULL                               -- ℹ Extra: computed full name
email TEXT NULL                                   -- ✓ Matches PLE
linkedin_url TEXT NULL                            -- ✓ Matches PLE
title TEXT NULL                                   -- ✓ Matches PLE

-- Timestamps (matching PLE intent)
created_at TIMESTAMPTZ DEFAULT now()              -- ✓ Matches PLE
updated_at TIMESTAMPTZ DEFAULT now()              -- ✓ Matches PLE
email_verified_at TIMESTAMPTZ NULL                -- Similar to PLE: last_verified_at

-- Validation/Enrichment (missing PLE fields)
-- ❌ validation_status - MISSING (critical for PLE)
-- ❌ last_verified_at - MISSING (critical for PLE)
-- ❌ last_enrichment_attempt - MISSING (critical for PLE)

-- Email Verification (replaces PLE validation fields)
email_verified BOOLEAN DEFAULT false              -- ℹ Partial: only email validation
email_verification_source TEXT NULL               -- ℹ Extra: how email was verified

-- Professional Details (not in PLE spec)
seniority TEXT NULL                               -- ℹ Extra: C-Level, Director, etc.
department TEXT NULL                              -- ℹ Extra: Sales, Engineering, etc.
work_phone_e164 TEXT NULL                         -- ℹ Extra: work phone
personal_phone_e164 TEXT NULL                     -- ℹ Extra: personal phone
twitter_url TEXT NULL                             -- ℹ Extra: social media
facebook_url TEXT NULL                            -- ℹ Extra: social media
bio TEXT NULL                                     -- ℹ Extra: professional bio
skills TEXT[] NULL                                -- ℹ Extra: skill tags
education TEXT NULL                               -- ℹ Extra: education history
certifications TEXT[] NULL                        -- ℹ Extra: professional certs

-- Source Tracking (replaces PLE 'source')
source_system TEXT NOT NULL                       -- ℹ Extra: origin system
source_record_id TEXT NULL                        -- ℹ Extra: original ID
promoted_from_intake_at TIMESTAMPTZ NOT NULL DEFAULT now()  -- ℹ Extra: promotion timestamp
promotion_audit_log_id INTEGER NULL               -- ℹ Extra: audit trail

-- Messaging (not in PLE spec)
message_key_scheduled TEXT NULL                   -- ℹ Extra: outreach tracking
```

#### Comparison
| PLE Column | Current Column | Status | Notes |
|------------|----------------|--------|-------|
| `id` | `unique_id` | ⚠ Different name | Uses TEXT instead of INT |
| `person_uid` | `unique_id` | ⚠ Different name | Same semantic meaning |
| `company_id` | `company_unique_id` | ⚠ Different name | Same semantic meaning |
| `linkedin_url` | `linkedin_url` | ✅ Match | |
| `email` | `email` | ✅ Match | |
| `first_name` | `first_name` | ✅ Match | |
| `last_name` | `last_name` | ✅ Match | |
| `title` | `title` | ✅ Match | |
| `validation_status` | ❌ Missing | ❌ Critical | Need: pending/valid/invalid/expired |
| `last_verified_at` | ❌ Missing | ❌ Critical | Only has `email_verified_at` |
| `last_enrichment_attempt` | ❌ Missing | ❌ Critical | No enrichment tracking |
| `created_at` | `created_at` | ✅ Match | |
| `updated_at` | `updated_at` | ✅ Match | |

**Extra Columns**: 16 additional fields for extended contact information, professional details, and source tracking

**Critical Missing Fields**:
1. `validation_status` - Essential for PLE workflow (pending → valid → invalid → expired)
2. `last_verified_at` - Need to track when person data was last verified
3. `last_enrichment_attempt` - Need to track enrichment attempts and cooldowns

---

## 3. PLE Sidecar Tables Status

### ❌ Table 4: `person_movement_history`

**Status**: DOES NOT EXIST

#### PLE Specification
```sql
CREATE TABLE person_movement_history (
    id SERIAL PRIMARY KEY,
    person_id TEXT NOT NULL REFERENCES people(person_uid),
    linkedin_url TEXT,
    company_id_from TEXT REFERENCES companies(company_uid),
    company_id_to TEXT REFERENCES companies(company_uid),
    title_from TEXT,
    title_to TEXT,
    movement_type TEXT,  -- job_change, promotion, departure, new_hire
    detected_at TIMESTAMPTZ DEFAULT NOW(),
    raw_payload JSONB
);
```

**Purpose**: Track career movements and job changes for BIT scoring

**Related Existing Tables**:
- None directly match this specification
- Some movement tracking may exist in `bit.bit_signal` or `marketing.pipeline_events`

**Action Required**: Create this table to enable:
1. Career progression tracking
2. Job change detection
3. Executive movement monitoring
4. Historical employment data

---

### ❌ Table 5: `person_scores`

**Status**: DOES NOT EXIST

#### PLE Specification
```sql
CREATE TABLE person_scores (
    id SERIAL PRIMARY KEY,
    person_id TEXT NOT NULL REFERENCES people(person_uid),
    bit_score NUMERIC,           -- 0-100 buyer intent score
    confidence_score NUMERIC,    -- 0-100 data confidence
    calculated_at TIMESTAMPTZ DEFAULT NOW(),
    score_factors JSONB          -- breakdown of score components
);
```

**Purpose**: Store calculated BIT scores for contacts

**Related Existing Tables**:
- `bit.bit_contact_score` (3 columns) - May serve similar purpose
- `marketing.company_slot.confidence_score` - Slot-level confidence only

**Action Required**: Either:
1. Create `person_scores` table per PLE spec, OR
2. Verify `bit.bit_contact_score` matches PLE requirements and migrate

---

### ❌ Table 6: `company_events`

**Status**: DOES NOT EXIST

#### PLE Specification
```sql
CREATE TABLE company_events (
    id SERIAL PRIMARY KEY,
    company_id TEXT NOT NULL REFERENCES companies(company_uid),
    event_type TEXT NOT NULL,    -- funding, expansion, layoffs, merger, etc.
    event_date DATE,
    source_url TEXT,
    summary TEXT,
    detected_at TIMESTAMPTZ DEFAULT NOW(),
    impacts_bit BOOLEAN DEFAULT false
);
```

**Purpose**: Track significant company events for BIT scoring

**Related Existing Tables**:
- `bit.bit_signal` - May capture some company events
- `marketing.pipeline_events` - Pipeline-specific events only

**Action Required**: Create this table to enable:
1. Funding round detection
2. Expansion/layoff tracking
3. Merger/acquisition monitoring
4. Company news aggregation for BIT scoring

---

## 4. Column Name Mapping Guide

This section provides a mapping between PLE specification names and current implementation names:

### Companies Table Mapping
```
PLE Column          →  Current Column (marketing.company_master)
-----------------------------------------------------------------
id                  →  company_unique_id (PK)
company_uid         →  company_unique_id
name                →  company_name
linkedin_url        →  linkedin_url (✓ same)
employee_count      →  employee_count (✓ same)
state               →  address_state + state_abbrev
city                →  address_city
industry            →  industry (✓ same)
source              →  source_system
created_at          →  created_at (✓ same)
updated_at          →  updated_at (✓ same)
```

### Company Slots Table Mapping
```
PLE Column          →  Current Column (marketing.company_slot)
-----------------------------------------------------------------
id                  →  company_slot_unique_id (PK)
slot_uid            →  company_slot_unique_id
company_id          →  company_unique_id (FK)
slot_type           →  slot_type (✓ same)
person_id           →  person_unique_id (FK)
assigned_at         →  filled_at
vacated_at          →  ❌ MISSING - need to add
```

### People Table Mapping
```
PLE Column              →  Current Column (marketing.people_master)
---------------------------------------------------------------------
id                      →  unique_id (PK)
person_uid              →  unique_id
company_id              →  company_unique_id (FK)
linkedin_url            →  linkedin_url (✓ same)
email                   →  email (✓ same)
first_name              →  first_name (✓ same)
last_name               →  last_name (✓ same)
title                   →  title (✓ same)
validation_status       →  ❌ MISSING - need to add
last_verified_at        →  ❌ MISSING - need to add (has email_verified_at only)
last_enrichment_attempt →  ❌ MISSING - need to add
created_at              →  created_at (✓ same)
updated_at              →  updated_at (✓ same)
```

---

## 5. Compatibility Assessment

### What Works Now (Without Changes)
✅ **Core Entity Structure**: Companies, slots, and people exist and are properly related via foreign keys
✅ **Basic Company Data**: Name, LinkedIn, employee count, industry, location
✅ **Executive Slot System**: CEO/CFO/HR slots with person assignments
✅ **Contact Information**: Name, email, LinkedIn, title
✅ **Timestamps**: Created/updated tracking
✅ **Source Tracking**: Origin system and record IDs
✅ **Enrichment Infrastructure**: Confidence scores, attempt tracking

### What Needs Adjustment
⚠ **Column Name Aliases**: Create views with PLE-compliant column names
⚠ **ID Field Access**: Use TEXT-based IDs instead of SERIAL/INT
⚠ **State/City Access**: Handle split address fields

### What's Missing (Critical for PLE)
❌ **Validation Status Tracking**: `people.validation_status` column
❌ **Verification Timestamps**: `people.last_verified_at` column
❌ **Enrichment Tracking**: `people.last_enrichment_attempt` column
❌ **Slot Vacation Tracking**: `company_slots.vacated_at` column
❌ **Movement History**: Entire `person_movement_history` table
❌ **Person Scoring**: Entire `person_scores` table (or validate `bit.bit_contact_score`)
❌ **Company Events**: Entire `company_events` table

---

## 6. Recommended Implementation Path

### Phase 1: Add Missing Columns to Existing Tables (Minimal Disruption)
```sql
-- Add to marketing.people_master
ALTER TABLE marketing.people_master
ADD COLUMN validation_status TEXT DEFAULT 'pending',
ADD COLUMN last_verified_at TIMESTAMPTZ,
ADD COLUMN last_enrichment_attempt TIMESTAMPTZ;

-- Add to marketing.company_slot
ALTER TABLE marketing.company_slot
ADD COLUMN vacated_at TIMESTAMPTZ;
```

### Phase 2: Create PLE-Compatible Views (Zero Disruption)
```sql
-- View: companies (PLE-compliant)
CREATE VIEW ple.companies AS
SELECT
    company_unique_id AS id,
    company_unique_id AS company_uid,
    company_name AS name,
    linkedin_url,
    employee_count,
    address_state AS state,
    address_city AS city,
    industry,
    source_system AS source,
    created_at,
    updated_at
FROM marketing.company_master;

-- View: company_slots (PLE-compliant)
CREATE VIEW ple.company_slots AS
SELECT
    company_slot_unique_id AS id,
    company_slot_unique_id AS slot_uid,
    company_unique_id AS company_id,
    slot_type,
    person_unique_id AS person_id,
    filled_at AS assigned_at,
    vacated_at
FROM marketing.company_slot;

-- View: people (PLE-compliant)
CREATE VIEW ple.people AS
SELECT
    unique_id AS id,
    unique_id AS person_uid,
    company_unique_id AS company_id,
    linkedin_url,
    email,
    first_name,
    last_name,
    title,
    validation_status,
    last_verified_at,
    last_enrichment_attempt,
    created_at,
    updated_at
FROM marketing.people_master;
```

### Phase 3: Create Missing Sidecar Tables
```sql
-- Create person_movement_history
CREATE TABLE ple.person_movement_history (
    id SERIAL PRIMARY KEY,
    person_id TEXT NOT NULL,
    linkedin_url TEXT,
    company_id_from TEXT,
    company_id_to TEXT,
    title_from TEXT,
    title_to TEXT,
    movement_type TEXT,
    detected_at TIMESTAMPTZ DEFAULT NOW(),
    raw_payload JSONB,
    FOREIGN KEY (person_id) REFERENCES marketing.people_master(unique_id)
);

-- Create person_scores (or validate bit.bit_contact_score matches)
CREATE TABLE ple.person_scores (
    id SERIAL PRIMARY KEY,
    person_id TEXT NOT NULL,
    bit_score NUMERIC,
    confidence_score NUMERIC,
    calculated_at TIMESTAMPTZ DEFAULT NOW(),
    score_factors JSONB,
    FOREIGN KEY (person_id) REFERENCES marketing.people_master(unique_id)
);

-- Create company_events
CREATE TABLE ple.company_events (
    id SERIAL PRIMARY KEY,
    company_id TEXT NOT NULL,
    event_type TEXT NOT NULL,
    event_date DATE,
    source_url TEXT,
    summary TEXT,
    detected_at TIMESTAMPTZ DEFAULT NOW(),
    impacts_bit BOOLEAN DEFAULT false,
    FOREIGN KEY (company_id) REFERENCES marketing.company_master(company_unique_id)
);
```

### Phase 4: Indexes and Optimization
```sql
-- person_movement_history indexes
CREATE INDEX idx_movement_person ON ple.person_movement_history(person_id);
CREATE INDEX idx_movement_detected ON ple.person_movement_history(detected_at DESC);
CREATE INDEX idx_movement_type ON ple.person_movement_history(movement_type);

-- person_scores indexes
CREATE INDEX idx_scores_person ON ple.person_scores(person_id);
CREATE INDEX idx_scores_bit ON ple.person_scores(bit_score DESC);
CREATE INDEX idx_scores_calculated ON ple.person_scores(calculated_at DESC);

-- company_events indexes
CREATE INDEX idx_events_company ON ple.company_events(company_id);
CREATE INDEX idx_events_type ON ple.company_events(event_type);
CREATE INDEX idx_events_detected ON ple.company_events(detected_at DESC);
CREATE INDEX idx_events_bit ON ple.company_events(impacts_bit) WHERE impacts_bit = true;
```

---

## 7. Migration Risk Assessment

### Low Risk (Safe to Implement Now)
✅ **Create PLE Views**: Read-only, no data modification
✅ **Add Missing Columns**: Nullable columns with defaults
✅ **Create Sidecar Tables**: New tables, no existing data affected
✅ **Add Indexes**: Performance improvement, non-blocking

### Medium Risk (Test First)
⚠ **Populate `validation_status`**: Need to backfill existing records
⚠ **Populate `last_verified_at`**: May need to analyze `email_verified_at` or other timestamps
⚠ **Populate `last_enrichment_attempt`**: Need to check enrichment agent logs

### High Risk (Requires Planning)
🔴 **Rename Existing Columns**: Would break existing code
🔴 **Change ID Types**: TEXT → INT or vice versa
🔴 **Merge Tables**: `company_slot` and `company_slots` consolidation

**Recommendation**: Use views (Phase 2) to maintain compatibility with both naming conventions.

---

## 8. Integration Points

### Existing Systems That May Need Updates
1. **Enrichment Agents** (`ctb/sys/enrichment-agents/`) - May reference `company_master`, `people_master` directly
2. **Validation Framework** (`ctb/data/validation-framework/`) - May reference old column names
3. **BIT Scoring Agent** (`ctb/sys/bit-scoring-agent/`) - Needs `person_scores` and `company_events` tables
4. **Talent Flow Agent** (`ctb/sys/talent-flow-agent/`) - Needs `person_movement_history` table
5. **Outreach Phase Registry** (`ctb/sys/toolbox-hub/backend/outreach_phase_registry.py`) - May reference old table/column names

### n8n Workflows
- **n8n Base URL**: https://dbarton.app.n8n.cloud
- Workflows may directly query `marketing.company_master`, `marketing.company_slot`, `marketing.people_master`
- Need to update workflows to use PLE views after Phase 2 implementation

---

## 9. Next Steps

### Immediate Actions (This Week)
1. ✅ **Schema Verification Complete** (this report)
2. 📝 **Review Report with Stakeholders** - Confirm PLE requirements are accurate
3. 🔧 **Phase 1: Add Missing Columns** - Execute ALTER TABLE statements
4. 👁 **Phase 2: Create PLE Views** - Enable dual naming support

### Short-Term (Next 2 Weeks)
5. 🏗 **Phase 3: Create Sidecar Tables** - `person_movement_history`, `person_scores`, `company_events`
6. ⚡ **Phase 4: Add Indexes** - Optimize query performance
7. 🧪 **Test PLE Views** - Verify all columns map correctly
8. 📊 **Backfill `validation_status`** - Set initial values for existing records

### Long-Term (Next Month)
9. 🔄 **Migrate Enrichment Agents** - Update to use PLE views
10. 📈 **Update n8n Workflows** - Switch to PLE-compliant queries
11. 🎯 **Enable BIT Scoring** - Use new `person_scores` and `company_events` tables
12. 🔍 **Enable Movement Tracking** - Populate `person_movement_history` from LinkedIn updates

---

## 10. SQL Scripts Ready for Execution

All SQL migration scripts are available in:
- **File**: `C:\Users\CUSTOM PC\Desktop\Cursor Builds\barton-outreach-core\ctb\sys\enrichment\ple_schema_migration.sql`

This file will contain all Phase 1-4 SQL statements in proper execution order with rollback instructions.

---

## 11. Contact & Support

**Repository**: barton-outreach-core
**Branch**: feature/node1-enrichment-queue
**Database**: Neon PostgreSQL - Marketing DB
**Schema Documentation**: `OUTREACH_DOCTRINE_A_Z_v1.3.2.md`

---

**Report Generated By**: Claude Code (Database Expert Agent)
**Verification Script**: `verify_ple_schema.py`
**Report Date**: 2025-11-26
