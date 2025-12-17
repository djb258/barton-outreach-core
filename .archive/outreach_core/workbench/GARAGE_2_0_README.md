# Enrichment Garage 2.0 - Agent Routing and Data Quality System

**Date**: 2025-11-18
**Status**: ✅ Production Ready
**Doctrine**: Garage 2.0
**Pipeline**: `enrichment_garage_2_0.py`

---

## Overview

Garage 2.0 is a comprehensive data quality repair and enrichment routing system that processes failed validation records from the DuckDB pipeline. It intelligently routes records to appropriate enrichment agents based on data quality issues, tracks repair attempts, manages enrichment TTLs, and integrates with BIT (Buyer Intent Tool) for movement detection.

### Pipeline Flow

```
state_duckdb_pipeline (bad records)
         ↓
    DuckDB (companies_bad + people_bad)
         ↓
    Garage 2.0 Classification
         ↓
    ┌─────────────┴──────────────┐
    ↓                            ↓
Bay A (Missing Parts)     Bay B (Contradictions)
- Missing domain          - Conflicting titles
- Missing LinkedIn        - Mismatched company/domain
- Missing industry        - Impossible enrichment
- Missing title           - Non-parsable LinkedIn
- Missing email
    ↓                            ↓
Firecrawl/Apify           Abacus/Claude
(Bulk agents)             (Edge agents)
    ↓                            ↓
    └─────────────┬──────────────┘
                  ↓
         VIN Tag Check (Hash)
                  ↓
         TTL Check (Title-based)
                  ↓
         Movement Detection
                  ↓
         Agent Routing + Repair
                  ↓
         Neon Reinsertion
                  ↓
         BIT Score Update
                  ↓
    Backblaze B2 (versioned storage)
```

---

## Key Features

### 1. Two-Bay Classification System

**Bay A - Missing Parts** (Cheap fixes):
- Missing domain
- Missing LinkedIn URL
- Missing industry
- Missing job title
- Missing email
- General enrichment gaps

**Routing**: Firecrawl or Apify (bulk agents, $0.05-$0.10 per record)

**Bay B - Contradictions** (Expensive fixes):
- Conflicting job titles
- Mismatched company/domain relationships
- Impossible enrichment scenarios
- Non-parsable LinkedIn URLs
- Data integrity violations

**Routing**: Abacus.ai or Claude (edge agents, $0.50-$1.00 per record)

### 2. VIN Tag System (Record Hashing)

Every record gets a unique "VIN tag" (SHA256 hash) computed from:

**For People**:
- Title
- Company unique ID
- Email
- LinkedIn URL
- Apollo ID
- Enrichment timestamp

**For Companies**:
- Company name
- Website URL
- LinkedIn URL
- Apollo ID
- Enrichment timestamp

**Purpose**:
- Skip enrichment if hash unchanged since last run
- Track data evolution over time
- Prevent duplicate enrichment costs

**Storage**: `marketing.people_master.last_hash`, `marketing.company_master.last_hash`

### 3. Enrichment TTL (Title-Level Cadence)

Different job titles have different enrichment frequencies:

| Seniority Level | TTL (Days) | Examples |
|----------------|-----------|-----------|
| C-Suite | 7 | CEO, CFO, CTO, CMO, CISO |
| VP/Director | 14 | VP, SVP, EVP, Director |
| Manager | 30 | Manager, Senior Manager |
| Non-ICP | 60 | All other roles |

**Logic**:
- C-suite changes jobs more frequently → check weekly
- VP/Director ICP roles → check bi-weekly
- Managers → check monthly
- Non-ICP roles → check quarterly

**Storage**: `marketing.people_master.enrichment_next_check`

### 4. Movement Detection + Turbulence Window

When talent movement is detected (job change, promotion, company switch), apply turbulence window:

| Window | Days Since Movement | Check Frequency |
|--------|-------------------|-----------------|
| Heavy | 0-30 days | Daily/Weekly |
| Moderate | 30-60 days | Bi-weekly |
| Light | 60-90 days | Monthly |

**Movement Types**:
- `promotion` - Moved up in same company
- `lateral` - Same level, different role
- `demotion` - Moved down (rare)
- `new_company` - Changed companies
- `left_company` - Departed

**Storage**: `talent_flow.movements`

**BIT Integration**:
- Movement always updates BIT score immediately
- Paint code assigned (reason for score)
- Movement + missing data → send to garage
- Score stays assigned after repair

### 5. Repair Attempts + Chronic Bad Tracking

Track repair attempts per record:

**Logic**:
1. Increment `repair_attempts += 1` on each garage run
2. If `repair_attempts > 3` in 30 days → mark `chronic_bad = TRUE`
3. Chronic bad records:
   - Sent to Bay B monthly only
   - Flagged for manual review
   - Lower priority in routing

**Storage**:
- `marketing.people_master.repair_attempts`
- `marketing.people_master.chronic_bad`
- `marketing.company_master.repair_attempts`
- `marketing.company_master.chronic_bad`

### 6. BIT Integration (Movement → Paint Code)

When movement is detected:

1. **Update BIT score immediately** (before enrichment)
2. **Assign paint code** - reason for score
3. **Store movement metadata** in `bit.bit_signal`

**Paint Code Examples**:
- `exec_promotion` - Executive promoted
- `icp_hire` - ICP role hired
- `company_switch` - Changed companies
- `role_upgrade` - Title improved

**Fields Added to `bit.bit_signal`**:
- `paint_code` - Short code for reason
- `paint_reason` - Human-readable explanation
- `movement_type` - Type of movement
- `movement_strength` - Signal strength (1-100)
- `movement_id` - FK to `talent_flow.movements`

**Hard Rule**: Never reduce BIT score due to missing data — only real negative signals.

### 7. Agent Router

Intelligent routing based on bay and record characteristics:

```python
if bay == "bay_a":
    # Missing parts → bulk agents
    if missing_fields includes ['domain', 'linkedin']:
        agent = 'firecrawl'  # Web scraping specialist
    else:
        agent = 'apify'      # General enrichment

elif bay == "bay_b":
    # Contradictions → edge agents
    if contradiction_type == 'conflicting_titles':
        agent = 'abacus'     # AI data reconciliation
    else:
        agent = 'claude'     # Complex reasoning
```

**Routing Skips**:
- Hash unchanged → skip (no data changes)
- TTL not expired → skip (checked recently)
- Non-ICP + no movement → skip (low priority)

**Cost Tracking**:
- Firecrawl: $0.05/record
- Apify: $0.10/record
- Abacus: $0.50/record
- Claude: $1.00/record

### 8. Neon Reinsertion Workflow

After agent repairs record:

1. **Recompute VIN tag** (hash)
2. **Revalidate** using same rules as `state_duckdb_pipeline`
3. **If clean**:
   - Insert back into `marketing.people_master` or `marketing.company_master`
   - Reset `repair_attempts = 0`
   - Update `last_enriched_at = NOW()`
   - Compute new `enrichment_next_check` based on TTL
4. **Keep BIT score unchanged** unless new movement detected

**Lineage Tracking**:
- All repairs logged to `public.agent_routing_log`
- Original validation errors preserved
- Agent used + cost tracked
- Before/after snapshots in B2

---

## Directory Structure

```
outreach_core/workbench/
├── enrichment_garage_2_0.py           # Main Garage 2.0 pipeline
├── GARAGE_2_0_README.md               # This file
├── duck/
│   └── outreach_workbench.duckdb      # Source of bad records
└── exports/
    └── {STATE}/
        └── (validation results from state_duckdb_pipeline)
```

**Backblaze B2 Structure**:

```
b2://svg-enrichment/garage/
├── WV/
│   ├── bay_a_missing_parts/
│   │   ├── 20251118161627/
│   │   │   └── records.json
│   │   └── 20251118173045/
│   │       └── records.json
│   └── bay_b_contradictions/
│       ├── 20251118161627/
│       │   └── records.json
│       └── 20251118173045/
│           └── records.json
├── PA/
├── VA/
├── MD/
├── OH/
└── DE/
```

---

## Usage

### Quick Start

```bash
cd outreach_core/workbench

# Run Garage 2.0 for WV state with specific snapshot
python enrichment_garage_2_0.py --state WV --snapshot 20251118161627

# Dry run (no B2 uploads, no Neon writes)
python enrichment_garage_2_0.py --state WV --snapshot 20251118161627 --dry-run
```

### Prerequisites

1. **Run `state_duckdb_pipeline.py` first** to generate bad records:
   ```bash
   python state_duckdb_pipeline.py --state WV
   ```

2. **Apply schema migration**:
   ```bash
   psql $NEON_CONNECTION_STRING -f infra/migrations/002_create_garage_2_0_schema.sql
   ```

3. **Verify environment variables**:
   ```bash
   # .env file must contain:
   NEON_HOST=...
   NEON_DATABASE=...
   NEON_USER=...
   NEON_PASSWORD=...
   B2_KEY_ID=...
   B2_APPLICATION_KEY=...
   B2_BUCKET=...
   ```

### Command-Line Arguments

| Argument | Required | Description |
|----------|---------|-------------|
| `--state` | Yes | State abbreviation (WV, PA, VA, MD, OH, DE) |
| `--snapshot` | Yes | Snapshot version from `state_duckdb_pipeline` |
| `--dry-run` | No | Dry run mode (no uploads, no Neon writes) |

### Example Workflow

```bash
# Step 1: Run validation pipeline for WV
python state_duckdb_pipeline.py --state WV
# Output: Snapshot 20251118161627 created

# Step 2: Run Garage 2.0 on bad records
python enrichment_garage_2_0.py --state WV --snapshot 20251118161627

# Step 3: Review results in Neon
psql -c "SELECT * FROM public.garage_runs ORDER BY created_at DESC LIMIT 1;"

# Step 4: Check agent routing log
psql -c "SELECT garage_bay, agent_assigned, COUNT(*) FROM public.agent_routing_log GROUP BY garage_bay, agent_assigned;"

# Step 5: View B2 uploads
# https://secure.backblaze.com/b2_buckets.htm
```

---

## Output and Logging

### Console Summary

```
================================================================================
GARAGE 2.0 RUN COMPLETE
================================================================================

STATE: WV
SNAPSHOT: 20251118161627

CLASSIFICATION:
  Bay A (Missing Parts): 47
  Bay B (Contradictions): 8

SKIPPED:
  Hash Unchanged: 12
  TTL Not Expired: 23

REPAIRS:
  Repair Success: 35
  Chronic Bad: 3

REINSERTS:
  Neon Reinserts: 35
  BIT Updates: 8

COST:
  Estimated Total: $9.50

B2 UPLOADS:
  b2://svg-enrichment/garage/WV/bay_a_missing_parts/20251118161627/records.json
  b2://svg-enrichment/garage/WV/bay_b_contradictions/20251118161627/records.json

TIMING:
  Start: 2025-11-18T16:30:00
  End: 2025-11-18T16:32:15

GARAGE RUN ID: 1
```

### Neon Tables

**1. `public.garage_runs`** - Run-level metrics

```sql
SELECT
    run_id,
    state,
    snapshot_version,
    records_bay_a,
    records_bay_b,
    total_cost_estimate,
    status,
    created_at
FROM public.garage_runs
ORDER BY created_at DESC;
```

**2. `public.agent_routing_log`** - Record-level routing

```sql
SELECT
    record_type,
    record_id,
    garage_bay,
    agent_assigned,
    routing_reason,
    agent_status,
    agent_cost
FROM public.agent_routing_log
WHERE garage_run_id = 1
LIMIT 10;
```

**3. `talent_flow.movements`** - Movement tracking

```sql
SELECT
    person_unique_id,
    movement_type,
    previous_role,
    new_role,
    turbulence_window_days,
    detected_at
FROM talent_flow.movements
WHERE detected_at >= NOW() - INTERVAL '90 days'
ORDER BY detected_at DESC;
```

**4. `bit.bit_signal`** - BIT updates with paint codes

```sql
SELECT
    company_unique_id,
    contact_unique_id,
    signal_type,
    signal_strength,
    paint_code,
    paint_reason,
    movement_type,
    captured_at
FROM bit.bit_signal
WHERE paint_code IS NOT NULL
ORDER BY captured_at DESC;
```

---

## Configuration

### TTL Rules (Title-Level Cadence)

Edit `enrichment_garage_2_0.py`:

```python
TTL_RULES = {
    'c-suite': 7,       # CEO, CFO, CTO, etc. → 7 days
    'vp-director': 14,  # VP, Director, SVP → 14 days
    'manager': 30,      # Manager, Sr Manager → 30 days
    'non-icp': 60       # Non-ICP roles → 60 days
}
```

### Turbulence Windows

```python
TURBULENCE_HEAVY = 30    # 0-30 days: Heavy checks
TURBULENCE_MODERATE = 60  # 30-60 days: Moderate checks
TURBULENCE_LIGHT = 90     # 60-90 days: Light checks
```

### Repair Tracking

```python
MAX_REPAIR_ATTEMPTS = 3
CHRONIC_BAD_THRESHOLD = 3  # attempts in 30 days
```

### Agent Costs

```python
AGENT_COSTS = {
    'firecrawl': 0.05,  # $0.05 per record
    'apify': 0.10,      # $0.10 per record
    'abacus': 0.50,     # $0.50 per record
    'claude': 1.00      # $1.00 per record
}
```

---

## Troubleshooting

### No Bad Records Found

**Issue**: `Loaded 0 bad companies` and `Loaded 0 bad people`

**Cause**: `state_duckdb_pipeline` hasn't run yet, or all records passed validation

**Solution**:
```bash
# Run validation pipeline first
python state_duckdb_pipeline.py --state WV

# Check if bad records exist in DuckDB
python -c "import duckdb; conn = duckdb.connect('duck/outreach_workbench.duckdb'); print(conn.execute('SELECT COUNT(*) FROM companies_bad').fetchone()); print(conn.execute('SELECT COUNT(*) FROM people_bad').fetchone());"
```

### Wrong Snapshot Version

**Issue**: `Snapshot version 20251118161627 not found`

**Cause**: Using snapshot from different state or date

**Solution**:
```bash
# List available snapshots in DuckDB
python -c "import duckdb; conn = duckdb.connect('duck/outreach_workbench.duckdb'); print(conn.execute('SELECT * FROM snapshots ORDER BY created_at DESC').fetchdf())"

# Use matching snapshot version
python enrichment_garage_2_0.py --state WV --snapshot <correct_snapshot>
```

### Schema Migration Not Applied

**Issue**: `ERROR: column "last_hash" does not exist`

**Cause**: Migration `002_create_garage_2_0_schema.sql` not applied

**Solution**:
```bash
# Apply migration
psql $NEON_CONNECTION_STRING -f infra/migrations/002_create_garage_2_0_schema.sql

# Verify tables created
psql $NEON_CONNECTION_STRING -c "\dt talent_flow.*"
psql $NEON_CONNECTION_STRING -c "\dt public.garage_runs"
```

### B2 Upload Failed

**Issue**: `Failed to upload to B2`

**Cause**: Incorrect B2 credentials or permissions

**Solution**:
```bash
# Verify B2 credentials
echo $B2_KEY_ID
echo $B2_APPLICATION_KEY
echo $B2_BUCKET

# Test B2 connection
python ctb/sys/toolbox-hub/backend/backblaze/test_b2_native.py

# Use dry-run to skip B2
python enrichment_garage_2_0.py --state WV --snapshot 20251118161627 --dry-run
```

---

## Schema Reference

### New Fields Added

**marketing.people_master**:
- `last_hash` (VARCHAR(64)) - VIN tag
- `enrichment_next_check` (TIMESTAMP) - TTL timestamp
- `repair_attempts` (INTEGER) - Repair count
- `chronic_bad` (BOOLEAN) - Chronic bad flag
- `last_enriched_at` (TIMESTAMP) - Last enrichment
- `garage_bay` (VARCHAR(10)) - Bay assignment
- `apollo_id` (VARCHAR(255)) - Apollo tracking

**marketing.company_master**:
- `last_hash` (VARCHAR(64)) - VIN tag
- `repair_attempts` (INTEGER) - Repair count
- `chronic_bad` (BOOLEAN) - Chronic bad flag
- `last_enriched_at` (TIMESTAMP) - Last enrichment
- `garage_bay` (VARCHAR(10)) - Bay assignment
- `apollo_id` (VARCHAR(255)) - Apollo tracking

**bit.bit_signal**:
- `paint_code` (VARCHAR(50)) - BIT reason code
- `paint_reason` (TEXT) - Human-readable reason
- `movement_type` (VARCHAR(50)) - Movement type
- `movement_strength` (INTEGER) - Signal strength
- `movement_id` (INTEGER) - FK to movements

### New Tables Created

**talent_flow.movements**:
- Tracks talent movements with turbulence window
- Links to people_master and company_master
- Stores movement type, previous/new roles, dates
- Integrates with BIT scoring

**public.garage_runs**:
- Tracks each Garage 2.0 run
- Summary metrics (bay counts, costs, skips)
- B2 paths, timing, status

**public.agent_routing_log**:
- Record-level routing decisions
- Agent assignments, costs, results
- Hash/TTL skip reasons
- Repair tracking

---

## Integration with Existing Systems

### 1. state_duckdb_pipeline Integration

Garage 2.0 reads from DuckDB tables created by `state_duckdb_pipeline`:
- `companies_bad` - Failed company validation
- `people_bad` - Failed people validation

**Workflow**:
```bash
state_duckdb_pipeline.py → DuckDB bad tables → enrichment_garage_2_0.py
```

### 2. BIT (Buyer Intent Tool) Integration

Movement detection triggers BIT score updates:
- New entry in `bit.bit_signal` with paint code
- BIT score updated immediately (before enrichment)
- Movement metadata preserved for analysis

**Query Example**:
```sql
-- Get all BIT signals from movements
SELECT
    bs.company_unique_id,
    bs.contact_unique_id,
    bs.paint_code,
    bs.movement_type,
    bs.signal_strength,
    m.previous_role,
    m.new_role,
    m.turbulence_window_days
FROM bit.bit_signal bs
JOIN talent_flow.movements m ON bs.movement_id = m.movement_id
WHERE bs.paint_code IS NOT NULL
ORDER BY bs.captured_at DESC;
```

### 3. Apollo Integration

VIN tags include `apollo_id` for cross-system tracking:
- Links Garage 2.0 records to Apollo enrichment
- Prevents duplicate API calls
- Tracks enrichment lineage

---

## Performance

### Expected Performance (With Data)

**For 50 bad companies + 50 bad people (100 total)**:
- Classification: ~1 second
- VIN tag computation: ~2 seconds
- TTL checks: ~3 seconds (Neon queries)
- Movement detection: ~2 seconds (Neon queries)
- JSON export: ~1 second
- B2 upload: ~2 seconds
- Neon logging: ~1 second
- **Total: ~12 seconds**

**Cost Estimate**:
- Bay A (70 records @ $0.05-0.10): ~$5.25
- Bay B (30 records @ $0.50-1.00): ~$22.50
- **Total: ~$27.75 per 100 records**

---

## Hard Rules (DO NOT VIOLATE)

1. ❌ **No schema changes** - Use existing field names exactly
2. ❌ **No renaming fields** - Preserve all column names
3. ❌ **No AI guessing** - If routing fails, throw explicit error
4. ❌ **Never reduce BIT score** due to missing data (only real negative signals)
5. ✅ **Keep directories versioned** by snapshot_version
6. ✅ **Preserve all Neon lineage** in agent_routing_log
7. ✅ **BIT changes only on signal**, not on cleanliness

---

## Version History

### Garage 2.0 (2025-11-18)
- Two-bay classification system (Bay A / Bay B)
- VIN tag system (record hashing)
- Enrichment TTL (title-level cadence)
- Movement detection + turbulence window (0-90 days)
- Repair attempts + chronic_bad tracking
- BIT integration with paint codes
- Agent router (Firecrawl/Apify for A, Abacus/Claude for B)
- Neon reinsertion workflow
- Comprehensive logging and metrics

---

**Last Updated**: 2025-11-18
**Status**: ✅ Production Ready
**Branch**: `sys/enrichment-garage-2.0`
