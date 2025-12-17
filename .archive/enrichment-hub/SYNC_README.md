# Enrichment Hub Sync - Quick Start

> **Quick reference for barton-outreach-core integration**

## What is This?

This repo provides a **universal enrichment receiver** that pulls invalid/failed records from your Neon production database into Supabase for manual review and enrichment, then pushes clean data back.

**Current Status:** 124 invalid records ready (119 companies, 5 people)

## Files You Need

| File | Purpose | Use For |
|------|---------|---------|
| `sync_manifest.json` | Complete machine-readable specs | Automated scripts |
| `NEON_SUPABASE_SYNC_GUIDE.md` | 15K+ word human guide | Understanding the system |
| `SYNC_README.md` | This file | Quick start |
| `n8n/pull_from_external_source.json` | n8n workflow | Automated sync |
| `config/source_bridge.env` | Neon source config | Database connection |
| `config/enrichment_bridge.env` | Supabase config | Enrichment hub |

## 4-Stage Pipeline

```
┌────────────────────────────────────────────────────────────┐
│ Stage 1: Pull Invalid Records                              │
│ Neon (barton-outreach-core) → Supabase (enricha-vision)   │
│ Trigger: Every 30 min                                      │
│ Script: 01_pull_invalid_to_supabase.py                    │
└────────────────────────────────────────────────────────────┘
                           ↓
┌────────────────────────────────────────────────────────────┐
│ Stage 2: Manual Enrichment                                 │
│ Supabase Dashboard - Manual review & data entry           │
│ Trigger: Manual                                            │
│ Interface: Supabase Table Editor                          │
└────────────────────────────────────────────────────────────┘
                           ↓
┌────────────────────────────────────────────────────────────┐
│ Stage 3: Push Enriched Data                               │
│ Supabase (enricha-vision) → Neon (barton-outreach-core)   │
│ Trigger: Daily 2 AM or manual                             │
│ Script: 02_push_enriched_to_neon.py                       │
└────────────────────────────────────────────────────────────┘
                           ↓
┌────────────────────────────────────────────────────────────┐
│ Stage 4: Cleanup & Archive                                │
│ Supabase - Delete processed records (7-day retention)     │
│ Trigger: Daily                                             │
│ Script: 03_cleanup_supabase.py                            │
└────────────────────────────────────────────────────────────┘
```

## Quick Start (5 Minutes)

### Step 1: Get the Manifest

**Option A: Git Submodule (Recommended)**

```bash
cd barton-outreach-core
git submodule add https://github.com/djb258/enricha-vision.git enrichment-hub
```

**Option B: Direct Download**

```bash
curl -O https://raw.githubusercontent.com/djb258/enricha-vision/main/sync_manifest.json
```

**Option C: Clone**

```bash
git clone https://github.com/djb258/enricha-vision.git
```

### Step 2: Read the Manifest (Python)

```python
import json

# Load manifest
with open('sync_manifest.json', 'r') as f:
    manifest = json.load(f)

# Get schema for Supabase tables
company_schema = manifest['schemas']['supabase_company_enrichment']
people_schema = manifest['schemas']['supabase_people_enrichment']

# Print fields
for field in company_schema['fields']:
    print(f"{field['name']}: {field['type']} {'REQUIRED' if field['required'] else 'OPTIONAL'}")
```

### Step 3: Create Supabase Tables

```sql
-- In your Supabase SQL Editor

-- Company enrichment table
CREATE TABLE public.company_needs_enrichment (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  company_name TEXT NOT NULL,
  domain TEXT,
  industry TEXT,
  employee_count INTEGER,
  revenue NUMERIC,
  location TEXT,
  linkedin_url TEXT,
  enrichment_data JSONB,
  validation_status TEXT NOT NULL DEFAULT 'PENDING',
  source_repo TEXT NOT NULL,
  source_id TEXT NOT NULL,
  source_table TEXT NOT NULL,
  source_environment TEXT,
  batch_id TEXT NOT NULL,
  entity_type TEXT NOT NULL,
  state_code TEXT,
  priority TEXT DEFAULT 'medium',
  needs_review BOOLEAN DEFAULT true,
  enrichment_source TEXT,
  pulled_at TIMESTAMP,
  imported_at TIMESTAMP,
  enriched_at TIMESTAMP,
  enriched_by TEXT,
  promoted_at TIMESTAMP,
  promoted_to_neon BOOLEAN DEFAULT false,
  created_at TIMESTAMP DEFAULT NOW(),
  updated_at TIMESTAMP DEFAULT NOW()
);

-- People enrichment table
CREATE TABLE public.people_needs_enrichment (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  first_name TEXT,
  last_name TEXT,
  email TEXT,
  phone TEXT,
  title TEXT,
  company_id UUID,
  company_name TEXT,
  linkedin_url TEXT,
  enrichment_data JSONB,
  validation_status TEXT NOT NULL DEFAULT 'PENDING',
  source_repo TEXT NOT NULL,
  source_id TEXT NOT NULL,
  source_table TEXT NOT NULL,
  source_environment TEXT,
  batch_id TEXT NOT NULL,
  entity_type TEXT NOT NULL,
  state_code TEXT,
  priority TEXT DEFAULT 'medium',
  needs_review BOOLEAN DEFAULT true,
  enrichment_source TEXT,
  pulled_at TIMESTAMP,
  imported_at TIMESTAMP,
  enriched_at TIMESTAMP,
  enriched_by TEXT,
  promoted_at TIMESTAMP,
  promoted_to_neon BOOLEAN DEFAULT false,
  created_at TIMESTAMP DEFAULT NOW(),
  updated_at TIMESTAMP DEFAULT NOW()
);

-- Indexes for performance
CREATE INDEX idx_company_enrichment_status ON public.company_needs_enrichment(validation_status);
CREATE INDEX idx_company_enrichment_batch ON public.company_needs_enrichment(batch_id);
CREATE INDEX idx_company_enrichment_source ON public.company_needs_enrichment(source_repo, source_id);

CREATE INDEX idx_people_enrichment_status ON public.people_needs_enrichment(validation_status);
CREATE INDEX idx_people_enrichment_batch ON public.people_needs_enrichment(batch_id);
CREATE INDEX idx_people_enrichment_source ON public.people_needs_enrichment(source_repo, source_id);
```

### Step 4: Share Supabase Credentials

Create `.env` file in barton-outreach-core:

```bash
# Supabase connection
SUPABASE_DB_URL="postgresql://postgres:PASSWORD@db.PROJECT.supabase.co:5432/postgres?sslmode=require"
SUPABASE_PROJECT_ID="your-project-id"
SUPABASE_ANON_KEY="your-anon-key"
```

Send these back to enricha-vision team so they can configure the sync.

### Step 5: Test Connection

```python
import psycopg2
import os
from dotenv import load_dotenv

load_dotenv()

# Test Supabase connection
conn = psycopg2.connect(os.getenv('SUPABASE_DB_URL'))
cursor = conn.cursor()
cursor.execute("SELECT COUNT(*) FROM public.company_needs_enrichment")
count = cursor.fetchone()[0]
print(f"Company records: {count}")
conn.close()
```

## Understanding the Data

### What Gets Pulled (Neon → Supabase)

```sql
-- From your Neon database
SELECT * FROM marketing.company_invalid
WHERE promoted_to IS NULL
  AND validation_status IN ('FAILED', 'PENDING')
ORDER BY created_at ASC
LIMIT 1000;
```

**Transformed to include:**
- `batch_id` - Unique batch identifier (e.g., "EXT-2025-11-07-abc123")
- `source_repo` - "barton-outreach-core"
- `source_id` - Original Neon record ID
- `source_table` - "marketing.company_invalid"
- `entity_type` - "company" or "people"
- `needs_review` - Always `true` for imported records

### What Gets Pushed Back (Supabase → Neon)

**Company fields pushed back:**
- `domain` ⭐ (required)
- `industry`
- `employee_count`
- `revenue`
- `location`
- `linkedin_url`
- `enrichment_data` (JSON)

**People fields pushed back:**
- `email` ⭐ (required)
- `phone`
- `title`
- `linkedin_url`
- `enrichment_data` (JSON)

**Also sets in Neon:**
- `validation_status = 'READY'`
- `promoted_to = 'marketing.company_master'`
- `promoted_at = NOW()`

## Enrichment Checklist

When reviewing records in Supabase:

### For Companies (119 records)

- [ ] **Domain** - Add website URL (required)
- [ ] **Industry** - Classify industry
- [ ] **Location** - City, State, Country
- [ ] **LinkedIn URL** - Company LinkedIn page
- [ ] **Employee Count** - Approximate headcount
- [ ] **Revenue** - Annual revenue (if known)

**After enriching:**
1. Verify `domain` is filled
2. Set `validation_status = 'READY'`
3. Set `enriched_by = 'your-name'`
4. Set `enriched_at = NOW()`

### For People (5 records)

- [ ] **Email** - Valid email address (required)
- [ ] **Phone** - Phone number
- [ ] **Title** - Job title
- [ ] **LinkedIn URL** - Personal LinkedIn
- [ ] **Company Name** - Employer

**After enriching:**
1. Verify `email` is filled
2. Set `validation_status = 'READY'`
3. Set `enriched_by = 'your-name'`
4. Set `enriched_at = NOW()`

## Validation Rules

From `sync_manifest.json`:

**Company - Required:**
- `company_name`
- `domain`

**Company - Recommended:**
- `industry`
- `location`
- `linkedin_url`

**People - Required:**
- `first_name`
- `last_name`
- `email`

**People - Recommended:**
- `title`
- `company_name`
- `linkedin_url`

## Example Queries

### Check Pending Records

```sql
-- In Supabase
SELECT
  source_repo,
  batch_id,
  COUNT(*) as records,
  validation_status
FROM public.company_needs_enrichment
WHERE source_repo = 'barton-outreach-core'
GROUP BY source_repo, batch_id, validation_status;
```

### Check Ready for Push

```sql
-- In Supabase
SELECT COUNT(*)
FROM public.company_needs_enrichment
WHERE validation_status = 'READY'
  AND promoted_to_neon = FALSE;
```

### Mark as Ready (After Enrichment)

```sql
-- In Supabase
UPDATE public.company_needs_enrichment
SET
  validation_status = 'READY',
  enriched_at = NOW(),
  enriched_by = 'your-name'
WHERE id = 'uuid-here';
```

## Automation Options

### Option 1: n8n Workflows (Recommended)

1. Import `n8n/pull_from_external_source.json`
2. Import `n8n/pull_from_enrichment_hub.json`
3. Configure credentials
4. Activate schedules

**Pros:** Visual, easy to monitor, no code
**Cons:** Requires n8n instance

### Option 2: Python Scripts

1. Install dependencies: `pip install psycopg2-binary python-dotenv`
2. Run scripts from manifest
3. Schedule with cron or Task Scheduler

**Pros:** No external tools, flexible
**Cons:** Requires Python environment

### Option 3: Manual Queries

1. Copy SQL from `sync_manifest.json`
2. Run manually when needed
3. Use Supabase + Neon dashboards

**Pros:** Simple, no setup
**Cons:** Manual effort, error-prone

## Field Mapping Reference

### Neon → Supabase (Pull)

| Neon Field | Supabase Field | Transform |
|------------|----------------|-----------|
| `id` | `source_id` | to_string |
| `company_name` | `company_name` | direct |
| `domain` | `domain` | direct |
| `validation_status` | `validation_status` | → 'PENDING' |
| (generated) | `batch_id` | generate |
| (constant) | `source_repo` | 'barton-outreach-core' |
| (constant) | `entity_type` | 'company' |

### Supabase → Neon (Push)

| Supabase Field | Neon Field | Transform |
|----------------|------------|-----------|
| `domain` | `domain` | direct |
| `industry` | `industry` | direct |
| `enrichment_data` | `enrichment_data` | merge_jsonb |
| (constant) | `validation_status` | 'READY' |
| (constant) | `promoted_to` | 'enrichment-hub' |
| (now) | `promoted_at` | NOW() |

## Monitoring

### Check Sync Status

```sql
-- In Neon (shq.audit_log)
SELECT
  workflow_name,
  entity_type,
  record_count,
  status,
  timestamp
FROM shq.audit_log
WHERE workflow_name = 'Pull from External Source'
ORDER BY timestamp DESC
LIMIT 10;
```

### Success Metrics

- ✅ All 124 records pulled to Supabase
- ✅ 100% enrichment completion
- ✅ All enriched records pushed back to Neon
- ✅ 0 validation errors on push-back
- ✅ Audit trail complete

## Troubleshooting

**No records appearing in Supabase?**
- Check `promoted_to IS NULL` in Neon
- Verify credentials in config
- Check n8n execution logs

**Can't push back to Neon?**
- Verify `validation_status = 'READY'`
- Check required fields are filled
- Ensure `promoted_to_neon = FALSE`

**Duplicate records?**
- Workflow uses `skipOnConflict` by default
- Check unique constraints on `source_id`

## Support & Documentation

**Full Documentation:**
- Complete guide: `NEON_SUPABASE_SYNC_GUIDE.md`
- Machine specs: `sync_manifest.json`
- n8n setup: `n8n/EXTERNAL_SOURCE_GUIDE.md`

**CTB Integration:**
- Project ID: `4.svg.marketing.enricha-vision`
- Full audit compliance
- Doctrine enforced

**Contact:**
- GitHub Issues: enricha-vision repo
- CTB Documentation: `CTB_README.md`

---

**Version:** 1.0.0
**Last Updated:** 2025-11-07
**Total Records:** 124 (119 companies + 5 people)
**Status:** Ready for sync
