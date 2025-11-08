# Neon ↔ Supabase Two-Way Sync Pipeline

**Purpose**: Pull invalid records from Neon to Supabase for enrichment, then push back for re-validation and promotion to master tables.

**Date**: 2025-11-07
**Status**: Ready for Implementation

---

## 📊 Overview

### The Complete Pipeline

```
┌─────────────────────────────────────────────────────────────────┐
│                    STAGE 1: PULL TO WORKSPACE                    │
├─────────────────────────────────────────────────────────────────┤
│  Neon: marketing.company_invalid (119 records)                  │
│  Neon: marketing.people_invalid (5 records)                     │
│                           ↓                                      │
│  Supabase: company_needs_enrichment (119 records)               │
│  Supabase: people_needs_enrichment (5 records)                  │
└─────────────────────────────────────────────────────────────────┘
                              ↓
                    [Enrichment Work]
                    - Add missing websites
                    - Fix validation errors
                    - Complete incomplete data
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│                  STAGE 2: PUSH ENRICHED BACK                     │
├─────────────────────────────────────────────────────────────────┤
│  Supabase: company_needs_enrichment                             │
│  WHERE enrichment_status = 'complete'                           │
│                           ↓                                      │
│  Neon: marketing.company_invalid (UPDATE)                       │
│  Neon: marketing.people_invalid (UPDATE)                        │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│                  STAGE 3: RE-VALIDATE                            │
├─────────────────────────────────────────────────────────────────┤
│  Run validation rules on updated invalid records                │
│                                                                  │
│  Result:                                                         │
│    - PASSED: 85 companies (estimate)                            │
│    - FAILED: 34 companies (still need work)                     │
└─────────────────────────────────────────────────────────────────┘
                              ↓
                        ┌─────┴─────┐
                        ↓           ↓
                   [PASSED]      [FAILED]
                        ↓           ↓
┌────────────────────────────────┐ ┌──────────────────────────────┐
│  STAGE 4A: PROMOTE TO MASTER   │ │  STAGE 4B: KEEP IN INVALID   │
├────────────────────────────────┤ ├──────────────────────────────┤
│  DELETE from company_invalid   │ │  UPDATE company_invalid      │
│  INSERT into company_master    │ │  SET still_invalid = TRUE    │
│                                │ │                              │
│  85 records promoted ✓         │ │  34 records need more work   │
└────────────────────────────────┘ └──────────────────────────────┘
```

---

## 🗄️ Tables & Schemas

### Source Tables (Neon)

#### `marketing.company_invalid`

**Current Count**: 119 records
**Location**: Neon PostgreSQL (Marketing DB)

```sql
CREATE TABLE marketing.company_invalid (
  id BIGSERIAL PRIMARY KEY,
  company_unique_id TEXT UNIQUE NOT NULL,
  company_name TEXT,
  domain TEXT,
  industry TEXT,
  employee_count INTEGER,
  website TEXT,                      -- MOSTLY NULL - needs enrichment
  phone TEXT,
  address TEXT,
  city TEXT,
  state TEXT,
  zip TEXT,
  validation_status TEXT DEFAULT 'FAILED',
  reason_code TEXT NOT NULL,         -- e.g., 'EMPTY_WEBSITE'
  validation_errors JSONB NOT NULL,  -- {"website": "empty or blank"}
  validation_warnings JSONB,
  failed_at TIMESTAMP DEFAULT now(),
  reviewed BOOLEAN DEFAULT false,
  batch_id TEXT,                     -- e.g., 'INTAKE-20251107-163209-b26be042'
  source_table TEXT DEFAULT 'marketing.company_raw_wv',
  created_at TIMESTAMP DEFAULT now(),
  updated_at TIMESTAMP DEFAULT now()
);
```

**Key Records**:
- 114 records from batch: `INTAKE-20251107-163209-b26be042`
- 5 records from previous validations
- Primary failure reason: Missing `website` field

#### `marketing.people_invalid`

**Current Count**: 5 records
**Location**: Neon PostgreSQL (Marketing DB)

```sql
CREATE TABLE marketing.people_invalid (
  id BIGSERIAL PRIMARY KEY,
  unique_id TEXT UNIQUE NOT NULL,
  full_name TEXT,
  first_name TEXT,
  last_name TEXT,
  email TEXT,
  phone TEXT,
  title TEXT,
  company_name TEXT,
  company_unique_id TEXT,
  linkedin_url TEXT,
  city TEXT,
  state TEXT,
  validation_status TEXT DEFAULT 'FAILED',
  reason_code TEXT NOT NULL,
  validation_errors JSONB NOT NULL,
  validation_warnings JSONB,
  failed_at TIMESTAMP DEFAULT now(),
  reviewed BOOLEAN DEFAULT false,
  batch_id TEXT,
  source_table TEXT DEFAULT 'marketing.people_raw_wv',
  created_at TIMESTAMP DEFAULT now(),
  updated_at TIMESTAMP DEFAULT now()
);
```

---

### Target Tables (Supabase)

#### `company_needs_enrichment`

**Purpose**: Workspace for enriching invalid company records

```sql
CREATE TABLE company_needs_enrichment (
  id BIGSERIAL PRIMARY KEY,

  -- Source tracking
  neon_id BIGINT,                    -- Original id from company_invalid
  company_unique_id TEXT UNIQUE NOT NULL,
  source_batch_id TEXT,

  -- Company data
  company_name TEXT,
  domain TEXT,
  industry TEXT,
  employee_count INTEGER,
  website TEXT,                      -- TO BE ENRICHED
  phone TEXT,
  address TEXT,
  city TEXT,
  state TEXT,
  zip TEXT,

  -- Validation tracking
  original_validation_errors JSONB, -- Errors from Neon
  original_validation_warnings JSONB,
  reason_code TEXT,

  -- Enrichment workflow
  enrichment_status TEXT DEFAULT 'pending',
  -- Values: 'pending', 'in_progress', 'complete', 'failed'

  enrichment_notes TEXT,             -- Manual notes during enrichment
  enriched_by TEXT,                  -- Who enriched it
  enriched_at TIMESTAMP,

  -- Sync tracking
  pulled_from_neon_at TIMESTAMP DEFAULT now(),
  pushed_to_neon_at TIMESTAMP,
  last_sync_hash TEXT,               -- MD5 hash of data for change detection

  -- Timestamps
  created_at TIMESTAMP DEFAULT now(),
  updated_at TIMESTAMP DEFAULT now()
);

-- Indexes for performance
CREATE INDEX idx_company_enrichment_status ON company_needs_enrichment(enrichment_status);
CREATE INDEX idx_company_unique_id ON company_needs_enrichment(company_unique_id);
CREATE INDEX idx_company_sync_status ON company_needs_enrichment(enrichment_status, pushed_to_neon_at);
```

#### `people_needs_enrichment`

**Purpose**: Workspace for enriching invalid people records

```sql
CREATE TABLE people_needs_enrichment (
  id BIGSERIAL PRIMARY KEY,

  -- Source tracking
  neon_id BIGINT,
  unique_id TEXT UNIQUE NOT NULL,
  source_batch_id TEXT,

  -- Person data
  full_name TEXT,
  first_name TEXT,
  last_name TEXT,
  email TEXT,
  phone TEXT,
  title TEXT,
  company_name TEXT,
  company_unique_id TEXT,
  linkedin_url TEXT,
  city TEXT,
  state TEXT,

  -- Validation tracking
  original_validation_errors JSONB,
  original_validation_warnings JSONB,
  reason_code TEXT,

  -- Enrichment workflow
  enrichment_status TEXT DEFAULT 'pending',
  enrichment_notes TEXT,
  enriched_by TEXT,
  enriched_at TIMESTAMP,

  -- Sync tracking
  pulled_from_neon_at TIMESTAMP DEFAULT now(),
  pushed_to_neon_at TIMESTAMP,
  last_sync_hash TEXT,

  -- Timestamps
  created_at TIMESTAMP DEFAULT now(),
  updated_at TIMESTAMP DEFAULT now()
);

-- Indexes
CREATE INDEX idx_people_enrichment_status ON people_needs_enrichment(enrichment_status);
CREATE INDEX idx_people_unique_id ON people_needs_enrichment(unique_id);
CREATE INDEX idx_people_sync_status ON people_needs_enrichment(enrichment_status, pushed_to_neon_at);
```

---

## 📦 What Gets Pulled

### Initial Pull Query (Companies)

```sql
-- Pull all company_invalid records to Supabase
SELECT
  id as neon_id,
  company_unique_id,
  company_name,
  domain,
  industry,
  employee_count,
  website,
  phone,
  address,
  city,
  state,
  zip,
  validation_errors as original_validation_errors,
  validation_warnings as original_validation_warnings,
  reason_code,
  batch_id as source_batch_id,
  created_at,
  updated_at
FROM marketing.company_invalid
WHERE 1=1
  -- Optional: Only pull records not yet synced
  -- AND synced_to_supabase IS NULL
ORDER BY created_at DESC;
```

**Expected Result**: 119 records

### Initial Pull Query (People)

```sql
-- Pull all people_invalid records to Supabase
SELECT
  id as neon_id,
  unique_id,
  full_name,
  first_name,
  last_name,
  email,
  phone,
  title,
  company_name,
  company_unique_id,
  linkedin_url,
  city,
  state,
  validation_errors as original_validation_errors,
  validation_warnings as original_validation_warnings,
  reason_code,
  batch_id as source_batch_id,
  created_at,
  updated_at
FROM marketing.people_invalid
WHERE 1=1
ORDER BY created_at DESC;
```

**Expected Result**: 5 records

---

## 🔄 What Gets Pushed Back

### Push Back Query (Companies)

After enrichment in Supabase, push updated data back to Neon:

```sql
-- Update company_invalid with enriched data
UPDATE marketing.company_invalid
SET
  website = %s,                  -- Now filled with valid URL
  phone = %s,
  industry = %s,
  employee_count = %s,
  domain = %s,
  validation_errors = %s,        -- Updated/cleared errors
  validation_warnings = %s,
  updated_at = now(),
  enrichment_status = 'complete',
  enriched_at = now(),
  enriched_by = %s
WHERE company_unique_id = %s;
```

**Fields to Update**:
- `website` (primary enrichment field)
- `phone` (if found)
- `industry` (if missing)
- `employee_count` (if missing)
- `domain` (extracted from website)
- `validation_errors` (cleared if fixed)
- `enrichment_status` (set to 'complete')

### Push Back Query (People)

```sql
-- Update people_invalid with enriched data
UPDATE marketing.people_invalid
SET
  email = %s,
  phone = %s,
  linkedin_url = %s,
  title = %s,
  validation_errors = %s,
  validation_warnings = %s,
  updated_at = now(),
  enrichment_status = 'complete',
  enriched_at = now(),
  enriched_by = %s
WHERE unique_id = %s;
```

---

## 🔧 Scripts to Build

### 1. Pull Script: `pull-invalid-to-supabase.py`

**Purpose**: Copy invalid records from Neon → Supabase

**Location**: `ctb/data/validation-framework/scripts/python/`

**Key Features**:
- Connect to both Neon and Supabase
- Pull all records from `marketing.company_invalid`
- Pull all records from `marketing.people_invalid`
- Insert into Supabase workspace tables
- Track sync with `pulled_from_neon_at` timestamp
- Calculate `last_sync_hash` for change detection

**Usage**:
```bash
python pull-invalid-to-supabase.py

# Options:
python pull-invalid-to-supabase.py --batch-size 50
python pull-invalid-to-supabase.py --entity company  # Only companies
python pull-invalid-to-supabase.py --entity people   # Only people
python pull-invalid-to-supabase.py --dry-run         # Test without changes
```

---

### 2. Push Script: `push-enriched-to-neon.py`

**Purpose**: Push enriched records from Supabase → Neon invalid tables

**Location**: `ctb/data/validation-framework/scripts/python/`

**Key Features**:
- Connect to both databases
- Find records with `enrichment_status = 'complete'`
- Update corresponding records in Neon invalid tables
- Track push with `pushed_to_neon_at` timestamp
- Log push operations to `shq_validation_log`

**Usage**:
```bash
python push-enriched-to-neon.py

# Options:
python push-enriched-to-neon.py --batch-size 50
python push-enriched-to-neon.py --entity company
python push-enriched-to-neon.py --dry-run
```

---

### 3. Re-Validation Script: `revalidate-enriched.py`

**Purpose**: Re-run validation rules on enriched records in Neon

**Location**: `ctb/data/validation-framework/scripts/python/`

**Key Features**:
- Query `marketing.company_invalid` WHERE `enrichment_status = 'complete'`
- Run same validation rules as initial validation
- Classify as PASSED or FAILED
- Update `validation_errors` JSONB
- Return lists of passed/failed record IDs

**Usage**:
```bash
python revalidate-enriched.py

# Output:
# PASSED: 85 companies
# FAILED: 34 companies (validation_errors still present)
```

---

### 4. Promotion Script: `promote-validated.py`

**Purpose**: Move PASSED records to master, keep FAILED in invalid

**Location**: `ctb/data/validation-framework/scripts/python/`

**Key Features**:
- Accept list of PASSED company_unique_ids
- DELETE from `marketing.company_invalid`
- INSERT into `marketing.company_master`
- Preserve Barton IDs
- Log promotion to `shq_validation_log`
- Keep FAILED records in invalid with updated status

**Usage**:
```bash
python promote-validated.py --passed-ids-file passed_companies.txt

# Or integrate with re-validation:
python revalidate-enriched.py | python promote-validated.py
```

---

### 5. Complete Pipeline Orchestrator: `run-enrichment-pipeline.py`

**Purpose**: Run all 4 stages in sequence

**Location**: `ctb/data/validation-framework/scripts/python/`

**Workflow**:
```python
# Stage 1: Pull to Supabase
pull_invalid_to_supabase()
print("✓ Pulled 124 records to Supabase")

# [PAUSE - Manual enrichment happens in Supabase]
input("Complete enrichment in Supabase, then press Enter...")

# Stage 2: Push enriched back to Neon
push_enriched_to_neon()
print("✓ Pushed enriched records back to Neon")

# Stage 3: Re-validate
passed_ids, failed_ids = revalidate_enriched()
print(f"✓ PASSED: {len(passed_ids)}, FAILED: {len(failed_ids)}")

# Stage 4: Promote validated
promote_validated(passed_ids)
print(f"✓ Promoted {len(passed_ids)} records to master")
```

**Usage**:
```bash
python run-enrichment-pipeline.py

# Or automated with n8n:
# - Stage 1: Pull on schedule (every hour)
# - Stage 2: Push when enrichment_status = 'complete'
# - Stage 3-4: Auto-validate and promote
```

---

## 📋 Enrichment Workflow (Manual Steps)

### In Supabase UI/Dashboard:

1. **View pending records**:
```sql
SELECT * FROM company_needs_enrichment
WHERE enrichment_status = 'pending'
ORDER BY created_at DESC;
```

2. **Enrich a record** (example):
```sql
UPDATE company_needs_enrichment
SET
  website = 'https://monongaliacounty.com',
  domain = 'monongaliacounty.com',
  enrichment_status = 'complete',
  enrichment_notes = 'Found via Google search',
  enriched_by = 'david@svg.agency',
  enriched_at = now(),
  updated_at = now()
WHERE company_unique_id = '04.04.01.01.00101.101';
```

3. **Mark as complete**:
```sql
-- Mark multiple as complete
UPDATE company_needs_enrichment
SET enrichment_status = 'complete', enriched_at = now()
WHERE id IN (1, 2, 3, 4, 5);
```

4. **Trigger push back**:
```bash
# Run push script or let n8n automation trigger
python push-enriched-to-neon.py
```

---

## 🔑 Environment Variables Needed

Add to `.env`:

```bash
# Existing Neon credentials
NEON_DATABASE_URL=postgresql://Marketing_DB_owner:npg_OsE4Z2oPCpiT@ep-ancient-waterfall-a42vy0du-pooler.us-east-1.aws.neon.tech:5432/Marketing_DB?sslmode=require

# NEW: Supabase credentials
SUPABASE_DATABASE_URL=postgresql://postgres:[YOUR_PASSWORD]@db.[YOUR_PROJECT].supabase.co:5432/postgres
SUPABASE_API_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.[YOUR_KEY]
SUPABASE_URL=https://[YOUR_PROJECT].supabase.co

# Optional: n8n webhook for automation
N8N_WEBHOOK_URL=https://your-n8n.app.n8n.cloud/webhook/enrichment-trigger
```

---

## 📊 Success Metrics

### Initial Pull
- ✅ 119 companies in `company_needs_enrichment`
- ✅ 5 people in `people_needs_enrichment`
- ✅ All `enrichment_status = 'pending'`

### After Enrichment
- ✅ 100+ records with `enrichment_status = 'complete'`
- ✅ `website` field populated
- ✅ `enriched_by` and `enriched_at` tracked

### After Push Back
- ✅ 100+ records in `marketing.company_invalid` updated
- ✅ `enrichment_status = 'complete'` in Neon
- ✅ `pushed_to_neon_at` timestamp in Supabase

### After Re-Validation
- ✅ 85+ records PASSED (estimate)
- ✅ 34 records FAILED (need more work)

### After Promotion
- ✅ 85+ records moved to `marketing.company_master`
- ✅ 85+ records deleted from `marketing.company_invalid`
- ✅ 34 records remain in `company_invalid` for re-enrichment

---

## 🚀 Next Steps

1. **Pull Supabase config** from other repo
2. **Create Supabase workspace tables** (run SQL above)
3. **Build pull script** (`pull-invalid-to-supabase.py`)
4. **Test pull** with dry-run
5. **Execute pull** (124 records → Supabase)
6. **Enrich data** manually in Supabase
7. **Build push script** (`push-enriched-to-neon.py`)
8. **Test push** with dry-run
9. **Execute push** (enriched data → Neon)
10. **Run re-validation** (`revalidate-enriched.py`)
11. **Promote validated** (`promote-validated.py`)

---

## 📝 Notes

- **Idempotency**: All scripts support `--dry-run` for testing
- **Conflict Resolution**: Use `updated_at` timestamp (newest wins)
- **Batch Processing**: Process in batches of 50-100 to prevent timeouts
- **Logging**: All operations logged to `shq_validation_log`
- **Rollback**: Keep backups before promotion step
- **n8n Automation**: Optional - can run all stages manually first

---

**Status**: Ready for Supabase credentials
**Next**: Pull config from other repo, then run Stage 1

---

*Generated: 2025-11-07*
*Pipeline: Neon ↔ Supabase Two-Way Sync*
*Records: 124 (119 companies + 5 people)*
