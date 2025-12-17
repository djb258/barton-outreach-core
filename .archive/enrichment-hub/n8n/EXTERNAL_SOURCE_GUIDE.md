# Pull from External Source - Setup Guide

## Overview

The **Pull from External Source** workflow transforms Enrichment Hub into a **universal enrichment receiver** that can pull failed or pending validation records from any Neon/Postgres database into its Supabase workspace for review, repair, and enrichment.

## Mission

Make Enrichment Hub a plug-and-play receiver for data quality issues from any production database, enabling centralized data enrichment and validation workflows.

## Workflow Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    External Source (Neon/Postgres)              │
│  ┌──────────────────────┐      ┌──────────────────────┐        │
│  │ company_invalid      │      │ people_invalid       │        │
│  │ (failed/pending)     │      │ (failed/pending)     │        │
│  └──────────────────────┘      └──────────────────────┘        │
└────────────────┬────────────────────────┬───────────────────────┘
                 │                        │
                 │   n8n Workflow         │
                 │   (Every 30 min)       │
                 ▼                        ▼
        ┌─────────────────┐     ┌─────────────────┐
        │ Transform +     │     │ Transform +     │
        │ Add Metadata    │     │ Add Metadata    │
        └────────┬────────┘     └────────┬────────┘
                 │                        │
                 ▼                        ▼
┌─────────────────────────────────────────────────────────────────┐
│            Enrichment Hub (Supabase)                            │
│  ┌──────────────────────┐      ┌──────────────────────┐        │
│  │ company_needs_       │      │ people_needs_        │        │
│  │ enrichment           │      │ enrichment           │        │
│  └──────────────────────┘      └──────────────────────┘        │
└─────────────────────────────────────────────────────────────────┘
                 │
                 ▼
         ┌───────────────┐
         │  Audit Log    │
         │  (Neon)       │
         └───────────────┘
```

## Features

✅ **Universal Compatibility** - Works with any Postgres/Neon database
✅ **Automated Sync** - Scheduled every 30 minutes (configurable)
✅ **Metadata Enrichment** - Adds source tracking, batch IDs, timestamps
✅ **Audit Logging** - Full CTB doctrine compliance with audit trail
✅ **Optional Source Updates** - Mark source records as promoted
✅ **Incremental Sync** - Only pulls unprocessed records
✅ **Multi-Entity Support** - Company, people, clients, vendors
✅ **Error Handling** - Duplicate detection and skip logic

## Prerequisites

### 1. Database Access

**External Source (Neon/Postgres):**
- PostgreSQL connection string
- Read permissions on source tables
- (Optional) Update permissions if `AUTO_UPDATE_SOURCE=true`

**Enrichment Hub (Supabase):**
- Supabase project credentials
- Write permissions on enrichment tables

**Audit Database (Neon):**
- Neon connection string
- Write permissions on `shq.audit_log` table

### 2. Required Tables

**Source Database:**
```sql
-- Example structure (can be any schema)
CREATE TABLE company_invalid (
  id SERIAL PRIMARY KEY,
  company_name TEXT,
  domain TEXT,
  industry TEXT,
  employee_count INTEGER,
  revenue NUMERIC,
  location TEXT,
  linkedin_url TEXT,
  enrichment_data JSONB,
  validation_status TEXT,
  promoted_to TEXT,        -- For tracking promotion
  promoted_at TIMESTAMP,   -- For tracking promotion
  created_at TIMESTAMP DEFAULT NOW(),
  updated_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE people_invalid (
  id SERIAL PRIMARY KEY,
  first_name TEXT,
  last_name TEXT,
  email TEXT,
  phone TEXT,
  title TEXT,
  company_id INTEGER,
  company_name TEXT,
  linkedin_url TEXT,
  enrichment_data JSONB,
  validation_status TEXT,
  promoted_to TEXT,
  promoted_at TIMESTAMP,
  created_at TIMESTAMP DEFAULT NOW(),
  updated_at TIMESTAMP DEFAULT NOW()
);
```

**Enrichment Hub (Supabase):**
```sql
-- Should already exist from CTB setup
-- See: ctb/data/migrations/ for full schema

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
  validation_status TEXT DEFAULT 'PENDING',
  source_repo TEXT,           -- Metadata field
  source_id TEXT,             -- Original source record ID
  source_table TEXT,          -- Source table name
  batch_id TEXT,              -- Batch identifier
  entity_type TEXT,           -- 'company'
  state_code TEXT,            -- Optional region
  priority TEXT DEFAULT 'medium',
  needs_review BOOLEAN DEFAULT true,
  enrichment_source TEXT,
  pulled_at TIMESTAMP,
  imported_at TIMESTAMP,
  created_at TIMESTAMP DEFAULT NOW(),
  updated_at TIMESTAMP DEFAULT NOW()
);

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
  validation_status TEXT DEFAULT 'PENDING',
  source_repo TEXT,
  source_id TEXT,
  source_table TEXT,
  batch_id TEXT,
  entity_type TEXT,
  state_code TEXT,
  priority TEXT DEFAULT 'medium',
  needs_review BOOLEAN DEFAULT true,
  enrichment_source TEXT,
  pulled_at TIMESTAMP,
  imported_at TIMESTAMP,
  created_at TIMESTAMP DEFAULT NOW(),
  updated_at TIMESTAMP DEFAULT NOW()
);
```

**Audit Database (Neon):**
```sql
-- Should already exist from CTB setup
CREATE TABLE shq.audit_log (
  id SERIAL PRIMARY KEY,
  workflow_name TEXT,
  entity_type TEXT,
  action TEXT,
  record_count INTEGER,
  status TEXT,
  batch_id TEXT,
  source_repo TEXT,
  source_table TEXT,
  destination_table TEXT,
  timestamp TIMESTAMP DEFAULT NOW(),
  metadata JSONB
);
```

## Installation

### Step 1: Configure Source Connection

Edit `/config/source_bridge.env`:

```bash
# External source database (Neon/Postgres with failed records)
SOURCE_DB_URL="postgresql://user:pass@ep-example.us-east-2.aws.neon.tech/marketing?sslmode=require"

# Tables containing records to pull
SOURCE_TABLE_COMPANY="company_invalid"
SOURCE_TABLE_PEOPLE="people_invalid"

# Filter for records to pull (only unpromoted records)
SOURCE_FILTER="WHERE promoted_to IS NULL"

# Source identifier
SOURCE_REPO="4.svg.marketing.main-db"
SOURCE_ENVIRONMENT="production"

# Auto-update source after successful import
AUTO_UPDATE_SOURCE="true"
SOURCE_UPDATE_COLUMN="promoted_to"
SOURCE_UPDATE_VALUE="enrichment-hub"
SOURCE_UPDATE_TIMESTAMP_COLUMN="promoted_at"

# Batch settings
BATCH_SIZE="1000"
```

### Step 2: Configure Enrichment Hub Connection

Edit `/config/enrichment_bridge.env`:

```bash
# Supabase Enrichment Hub
SUPABASE_DB_URL="postgresql://postgres:yourpass@db.abc123.supabase.co:5432/postgres?sslmode=require"
SUPABASE_SCHEMA="public"

# Destination tables
DEST_TABLE_COMPANY="company_needs_enrichment"
DEST_TABLE_PEOPLE="people_needs_enrichment"

# Default values for imported records
DEFAULT_VALIDATION_STATUS="PENDING"
DEFAULT_PRIORITY="medium"

# Audit logging (Neon)
AUDIT_DB_URL="postgresql://user:pass@neon-audit.region.neon.tech/marketing?sslmode=require"
AUDIT_SCHEMA="shq"
AUDIT_TABLE="audit_log"

# CTB integration
CTB_PROJECT_ID="4.svg.marketing.enricha-vision"

# Batch settings
BATCH_ID_PREFIX="EXT"
```

### Step 3: Load Environment Variables in n8n

**Option A: n8n Environment Variables**

Add to your n8n environment (docker-compose.yml or .env):

```yaml
environment:
  # Source Bridge
  - SOURCE_DB_URL=postgresql://...
  - SOURCE_TABLE_COMPANY=company_invalid
  - SOURCE_TABLE_PEOPLE=people_invalid
  - SOURCE_FILTER=WHERE promoted_to IS NULL
  - SOURCE_REPO=4.svg.marketing.main-db
  - SOURCE_ENVIRONMENT=production
  - AUTO_UPDATE_SOURCE=true
  - SOURCE_UPDATE_COLUMN=promoted_to
  - SOURCE_UPDATE_VALUE=enrichment-hub
  - SOURCE_UPDATE_TIMESTAMP_COLUMN=promoted_at
  - BATCH_SIZE=1000

  # Enrichment Bridge
  - SUPABASE_DB_URL=postgresql://...
  - SUPABASE_SCHEMA=public
  - DEST_TABLE_COMPANY=company_needs_enrichment
  - DEST_TABLE_PEOPLE=people_needs_enrichment
  - DEFAULT_VALIDATION_STATUS=PENDING
  - DEFAULT_PRIORITY=medium
  - AUDIT_DB_URL=postgresql://...
  - AUDIT_SCHEMA=shq
  - AUDIT_TABLE=audit_log
  - CTB_PROJECT_ID=4.svg.marketing.enricha-vision
  - BATCH_ID_PREFIX=EXT
```

**Option B: n8n Variables**

In n8n UI:
1. Settings → Variables
2. Add each variable manually

### Step 4: Import Workflow

1. Open n8n
2. Go to **Workflows**
3. Click **Import from File**
4. Select `n8n/pull_from_external_source.json`
5. Click **Import**

### Step 5: Configure Credentials

The workflow requires **3 PostgreSQL credentials**:

#### A. External Source PostgreSQL

1. Go to **Credentials** → **Add Credential** → **Postgres**
2. Name: `External Source PostgreSQL`
3. Configure:
   - **Connection Type:** Connection String
   - **Connection String:** `{{$env.SOURCE_DB_URL}}`
   - **SSL:** Require
4. **Test Connection**
5. **Save** and note the credential ID
6. Replace `{{SOURCE_DB_CREDENTIALS_ID}}` in workflow nodes

#### B. Supabase PostgreSQL

1. Go to **Credentials** → **Add Credential** → **Postgres**
2. Name: `Supabase PostgreSQL`
3. Configure:
   - **Connection Type:** Connection String
   - **Connection String:** `{{$env.SUPABASE_DB_URL}}`
   - **SSL:** Require
4. **Test Connection**
5. **Save** and note the credential ID
6. Replace `{{SUPABASE_CREDENTIALS_ID}}` in workflow nodes

#### C. Neon Audit PostgreSQL

1. Go to **Credentials** → **Add Credential** → **Postgres**
2. Name: `Neon Audit PostgreSQL`
3. Configure:
   - **Connection Type:** Connection String
   - **Connection String:** `{{$env.AUDIT_DB_URL}}`
   - **SSL:** Require
4. **Test Connection**
5. **Save** and note the credential ID
6. Replace `{{AUDIT_DB_CREDENTIALS_ID}}` in workflow nodes

### Step 6: Update Credential IDs in Workflow

Open the workflow and find these nodes, replace credential IDs:

**Nodes using External Source:**
- Query Company Records
- Query People Records
- Update Company Source Status
- Update People Source Status

**Nodes using Supabase:**
- Insert Companies to Supabase
- Insert People to Supabase

**Nodes using Neon Audit:**
- Log Company Audit to Neon
- Log People Audit to Neon

### Step 7: Test Workflow

**Manual Test:**
1. Ensure source database has records matching `SOURCE_FILTER`
2. Click **Execute Workflow**
3. Select **Manual Trigger**
4. Review execution log
5. Verify records in Supabase
6. Check audit log in Neon

**Test Query (Source Database):**
```sql
-- Check records available for pulling
SELECT COUNT(*)
FROM company_invalid
WHERE promoted_to IS NULL;

SELECT COUNT(*)
FROM people_invalid
WHERE promoted_to IS NULL;
```

**Test Query (Enrichment Hub - Supabase):**
```sql
-- Check imported records
SELECT
  source_repo,
  batch_id,
  COUNT(*) as records,
  validation_status
FROM public.company_needs_enrichment
WHERE source_repo = '4.svg.marketing.main-db'
GROUP BY source_repo, batch_id, validation_status;
```

**Test Query (Audit Log - Neon):**
```sql
-- Check audit trail
SELECT * FROM shq.audit_log
WHERE workflow_name = 'Pull from External Source'
ORDER BY timestamp DESC
LIMIT 5;
```

### Step 8: Activate Scheduled Sync

1. Toggle workflow to **Active**
2. Workflow will run every 30 minutes
3. Monitor executions in n8n dashboard

## Usage

### Manual Execution

**When to use:**
- Initial migration of existing failed records
- Testing after configuration changes
- On-demand sync when needed

**How to execute:**
1. Open workflow in n8n
2. Click **Execute Workflow**
3. Select **Manual Trigger**
4. Wait for completion
5. Review summary output

### Scheduled Execution

**Default:** Every 30 minutes

**To change schedule:**
1. Edit **Schedule Trigger (Every 30 min)** node
2. Modify `interval` setting:
   - Every 15 min: `{"field": "minutes", "minutesInterval": 15}`
   - Every hour: `{"field": "hours", "hoursInterval": 1}`
   - Custom cron: Use cron expression

### Monitoring

**Execution History:**
```
n8n → Executions → Filter by "Pull from External Source"
```

**Success Criteria:**
- ✅ All nodes executed successfully
- ✅ Records inserted to Supabase
- ✅ Audit logs created
- ✅ Source records updated (if `AUTO_UPDATE_SOURCE=true`)

**Audit Queries:**
```sql
-- Daily import stats
SELECT
  DATE(timestamp) as date,
  entity_type,
  SUM(record_count) as total_records,
  COUNT(*) as executions
FROM shq.audit_log
WHERE workflow_name = 'Pull from External Source'
  AND timestamp >= NOW() - INTERVAL '7 days'
GROUP BY DATE(timestamp), entity_type
ORDER BY date DESC;

-- Latest batch details
SELECT * FROM shq.audit_log
WHERE workflow_name = 'Pull from External Source'
ORDER BY timestamp DESC
LIMIT 1;
```

## Workflow Nodes Explained

### 1. Triggers

**Manual Trigger** - For on-demand execution
**Schedule Trigger** - Automated every 30 minutes

### 2. Query Nodes

**Query Company Records** - Pull company records from source
**Query People Records** - Pull people records from source

Queries include:
- All source fields
- Added metadata (source_repo, source_environment)
- Timestamp (pulled_at)
- Filter by `SOURCE_FILTER`
- Limited by `BATCH_SIZE`

### 3. Transform Nodes

**Transform Company Data** - Enriches records with metadata
**Transform People Data** - Enriches records with metadata

Added fields:
- `batch_id` - Unique batch identifier
- `entity_type` - 'company' or 'people'
- `source_repo` - Source identifier
- `source_id` - Original record ID
- `source_table` - Source table name
- `validation_status` - 'PENDING' by default
- `priority` - 'medium' by default
- `needs_review` - true
- `imported_at` - Import timestamp

### 4. Insert Nodes

**Insert Companies to Supabase** - Write to Supabase
**Insert People to Supabase** - Write to Supabase

Features:
- Auto-map fields
- Skip on conflict (duplicate protection)

### 5. Audit Nodes

**Generate Company Audit Log** - Create audit record
**Generate People Audit Log** - Create audit record
**Log Company Audit to Neon** - Write audit to Neon
**Log People Audit to Neon** - Write audit to Neon

Logged data:
- Workflow name
- Entity type
- Record count
- Batch ID
- Source/destination tables
- Metadata (JSON)

### 6. Update Nodes (Conditional)

**Auto Update Source?** - Check if `AUTO_UPDATE_SOURCE=true`
**Update Company Source Status** - Mark source records
**Update People Source Status** - Mark source records

Updates:
- Set `promoted_to = 'enrichment-hub'`
- Set `promoted_at = NOW()`

### 7. Summary Node

**Generate Import Summary** - Create markdown report
**Output Summary** - Display in execution log

Output example:
```markdown
# External Source → Enrichment Hub Import Summary

**Workflow:** Pull from External Source
**Source Repository:** 4.svg.marketing.main-db
**Batch ID:** EXT-2025-11-07-abc123
**Timestamp:** 2025-11-07T14:30:00Z
**Status:** ✅ Completed

## Records Pulled

| Entity Type | Source Table | Rows Pulled | Destination | Status |
|-------------|--------------|-------------|-------------|--------|
| Companies   | company_invalid | 145 | public.company_needs_enrichment | ✅ Success |
| People      | people_invalid | 523 | public.people_needs_enrichment | ✅ Success |
| **TOTAL**   | - | **668** | Enrichment Hub (Supabase) | ✅ Success |
```

## Customization

### Different Source Tables

To pull from different tables, update environment variables:

```bash
SOURCE_TABLE_COMPANY="marketing.failed_companies"
SOURCE_TABLE_PEOPLE="sales.invalid_contacts"
```

### Custom Filters

Change what records get pulled:

```bash
# Only records from last 7 days
SOURCE_FILTER="WHERE promoted_to IS NULL AND updated_at > NOW() - INTERVAL '7 days'"

# Only failed validation
SOURCE_FILTER="WHERE validation_status = 'FAILED'"

# Multiple conditions
SOURCE_FILTER="WHERE promoted_to IS NULL AND needs_review = TRUE AND priority = 'high'"
```

### Additional Entity Types

To add support for clients, vendors, etc.:

1. Add environment variables:
```bash
SOURCE_TABLE_CLIENT="client_invalid"
DEST_TABLE_CLIENT="client_needs_enrichment"
```

2. Duplicate node chain in workflow:
   - Query node
   - Transform node
   - Insert node
   - Audit nodes

3. Update connections and field mappings

### Field Mapping

If source fields have different names, modify Transform nodes:

```javascript
// In Transform Company Data node
company_name: data.name,              // Map 'name' → 'company_name'
domain: data.website,                 // Map 'website' → 'domain'
employee_count: data.headcount,       // Map 'headcount' → 'employee_count'
```

### Batch Size

Adjust for performance:

```bash
# Small batches (safer, slower)
BATCH_SIZE="100"

# Large batches (faster, more resource intensive)
BATCH_SIZE="5000"
```

## Troubleshooting

### No Records Pulled

**Check:**
1. Are there records matching `SOURCE_FILTER`?
   ```sql
   SELECT COUNT(*) FROM company_invalid WHERE promoted_to IS NULL;
   ```
2. Are credentials valid?
3. Is source database accessible?

### Duplicate Records

**Solution:**
Workflow uses `skipOnConflict: true` to skip duplicates.

To handle differently:
1. Edit Insert nodes
2. Change `skipOnConflict` to `false`
3. Or add custom duplicate detection logic

### Source Not Updating

**Check:**
1. Is `AUTO_UPDATE_SOURCE=true`?
2. Do source credentials have UPDATE permission?
3. Are `SOURCE_UPDATE_COLUMN` and `SOURCE_UPDATE_TIMESTAMP_COLUMN` correct?

### Audit Log Not Writing

**Check:**
1. Does `shq.audit_log` table exist?
2. Are audit credentials valid?
3. Check Neon connection string

### Performance Issues

**Solutions:**
1. Reduce `BATCH_SIZE`
2. Increase schedule interval
3. Add indexes to source tables:
   ```sql
   CREATE INDEX idx_company_promoted ON company_invalid(promoted_to);
   CREATE INDEX idx_people_promoted ON people_invalid(promoted_to);
   ```

## Security Considerations

### Credentials

- ✅ Store in n8n credential manager
- ✅ Never hardcode in workflow
- ✅ Use environment variables
- ✅ Rotate regularly

### Data Privacy

- ⚠️ PII data is transferred
- ✅ Use SSL/TLS for all connections
- ✅ Ensure GDPR compliance
- ✅ Audit all operations

### Access Control

- ✅ Limit source database to read-only (if `AUTO_UPDATE_SOURCE=false`)
- ✅ Limit Supabase access to enrichment tables only
- ✅ Protect n8n workflow from unauthorized edits

## Integration with Existing Workflows

This workflow complements the existing **Pull from Enrichment Hub** workflow:

```
External DB → [Pull from External Source] → Supabase Enrichment Hub
                                                    ↓
                                            Review & Enrich
                                                    ↓
                                            Mark as READY
                                                    ↓
Neon Production ← [Pull from Enrichment Hub] ← Supabase Enrichment Hub
```

**Full data flow:**
1. Failed records pulled from external Neon/Postgres → Supabase
2. Manual review and enrichment in Supabase
3. Mark records as READY
4. Promote to Neon production via existing workflow

## CTB Compliance

This workflow follows CTB doctrine:

- ✅ Full audit logging to `shq.audit_log`
- ✅ Batch tracking with unique IDs
- ✅ Source traceability
- ✅ Metadata enrichment
- ✅ Compliance scoring
- ✅ Data lineage tracking

**CTB Project:** `4.svg.marketing.enricha-vision`
**CTB Branch:** `ctb/data`

## Support

**Issues:**
- Check n8n execution logs
- Review audit logs: `SELECT * FROM shq.audit_log ORDER BY timestamp DESC`
- Verify credentials and connections
- Test database connectivity

**Documentation:**
- n8n Docs: https://docs.n8n.io
- CTB System: `../CTB_README.md`
- Database Schemas: `../ctb/data/migrations/`
- Configuration: `/config/source_bridge.env` & `/config/enrichment_bridge.env`

---

**Version:** 1.0.0
**Last Updated:** 2025-11-07
**Project:** Enricha Vision (4.svg.marketing.enricha-vision)
**Workflow ID:** pull-from-external-source
