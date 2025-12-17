# Outreach Core Workbench - DuckDB → Parquet → B2 Pipeline

**Date**: 2025-11-18
**Status**: ✅ Production Ready
**Pipelines**:
- `wv_duckdb_pipeline.py` (Phase 1: Single-state, basic validation)
- `state_duckdb_pipeline.py` (Phase 2B: Multi-state, versioned, with kill switches)

---

## Overview

This workbench implements a complete data validation pipeline using DuckDB for in-memory processing and Backblaze B2 for Parquet storage.

### Phase 2B (Recommended)

**Script**: `state_duckdb_pipeline.py`

**Key Features**:
- Multi-state execution (WV, PA, VA, MD, OH, DE)
- Snapshot versioning with UTC timestamps
- Linked people validation (only validate people from good companies)
- 3 Kill switches for data quality anomalies
- Versioned Parquet filenames
- B2 metadata tagging
- Enhanced audit logging with snapshot tracking
- DuckDB snapshots table for historical comparison

### Phase 1 (Legacy)

**Script**: `wv_duckdb_pipeline.py`

Basic single-state (WV only) pipeline without versioning or kill switches. Documentation preserved below for reference.

---

## Phase 2B Usage (Recommended)

### Quick Start

```bash
cd outreach_core/workbench

# Run for WV
python state_duckdb_pipeline.py --state WV

# Run for other states
python state_duckdb_pipeline.py --state PA
python state_duckdb_pipeline.py --state VA
python state_duckdb_pipeline.py --state MD
python state_duckdb_pipeline.py --state OH
python state_duckdb_pipeline.py --state DE
```

### Phase 2B Pipeline Flow

```
Neon PostgreSQL (state-filtered companies + people)
         ↓
    DuckDB (load + retrieve previous snapshot)
         ↓
    Validation (SQL logic + linked people)
         ↓
    Kill Switch Checks (K1, K2, K3)
         ↓
    Versioned Parquet files (with timestamp)
         ↓
   Backblaze B2 (with metadata tags)
         ↓
  DuckDB snapshots table + Neon audit log
```

### Phase 2B Features Explained

#### 1. Multi-State Execution

Use `--state` argument to process any of 6 supported states:

```bash
python state_duckdb_pipeline.py --state WV
```

Dynamic filtering:
- Companies: `WHERE address_state = '{STATE}'`
- People: Linked via `company_unique_id` from filtered companies
- Exports: Organized by state (`exports/WV/`, `exports/PA/`, etc.)
- B2 paths: State-specific (`outreach/WV/`, `outreach/PA/`, etc.)

#### 2. Snapshot Versioning

Every run creates a UTC timestamp version: `YYYYMMDDHHmmss`

Example: `20251118161627`

**Versioned Filenames**:
```
companies_good_20251118161627.parquet
companies_bad_20251118161627.parquet
people_good_20251118161627.parquet
people_bad_20251118161627.parquet
```

**Benefits**:
- Historical tracking
- Rollback capability
- Comparison across runs
- No file overwrites

#### 3. Linked People Validation

People are only marked as "good" if their company passed validation:

```sql
-- People good: email + title valid AND company is good
SELECT p.*
FROM people_raw p
JOIN companies_good cg
    ON p.company_unique_id = cg.company_unique_id
WHERE
    p.email ~ '^[^@]+@[^@]+\\.[^@]+'
    AND p.title IS NOT NULL;
```

People marked as "bad" if:
- Invalid email format (`email_invalid`)
- Missing title (`title_missing`)
- Company failed validation (`company_not_valid`)

#### 4. Kill Switches

Three automated data quality checks that abort the pipeline on anomalies:

**K1: Bad Ratio Spike** (Threshold: 15%)
```
If (companies_bad / total_companies) > 15%:
    ABORT with K1_TRIGGERED
```
Protects against: Mass validation failures, schema changes, data corruption

**K2: Row Count Delta Drift** (Threshold: 30%)
```
If abs(current_total - previous_total) / previous_total > 30%:
    ABORT with K2_TRIGGERED
```
Protects against: Unexpected data loss, duplicate loads, source data issues

**K3: Company ID Integrity**
```
If any company_unique_id IS NULL:
    ABORT with K3_TRIGGERED
```
Protects against: Primary key violations, data pipeline errors

**Customization**:
Edit thresholds in `state_duckdb_pipeline.py`:
```python
KILL_SWITCH_BAD_RATIO = 0.15  # 15%
KILL_SWITCH_ROW_DELTA = 0.30  # 30%
```

#### 5. B2 Metadata Tagging

Each uploaded file includes metadata:

```python
file_infos = {
    'snapshot-version': '20251118161627',
    'state': 'WV',
    'table_name': 'companies_good',
    'upload_timestamp': '2025-11-18T16:16:27',
    'pipeline': 'state_duckdb_pipeline'
}
```

**Benefits**:
- Searchable by version
- Identify file purpose without downloading
- Track upload timing
- Pipeline attribution

#### 6. DuckDB Snapshots Table

Historical tracking within DuckDB:

```sql
CREATE TABLE snapshots (
    id INTEGER PRIMARY KEY,
    state VARCHAR,
    snapshot_version VARCHAR,
    companies_good INTEGER,
    companies_bad INTEGER,
    people_good INTEGER,
    people_bad INTEGER,
    created_at TIMESTAMP
);
```

**Query Examples**:
```python
import duckdb

conn = duckdb.connect('duck/outreach_workbench.duckdb')

# Latest snapshot for WV
conn.execute("""
    SELECT * FROM snapshots
    WHERE state = 'WV'
    ORDER BY created_at DESC
    LIMIT 1;
""").fetchall()

# Compare last 2 runs
conn.execute("""
    SELECT
        snapshot_version,
        companies_good,
        companies_bad,
        people_good,
        people_bad
    FROM snapshots
    WHERE state = 'WV'
    ORDER BY created_at DESC
    LIMIT 2;
""").fetchall()
```

#### 7. Enhanced Audit Log

Neon `shq.audit_log` includes Phase 2B fields:

```json
{
  "state": "WV",
  "snapshot_version": "20251118161627",
  "companies_good": 453,
  "companies_bad": 12,
  "people_good": 170,
  "people_bad": 8,
  "kill_switch_status": "OK",
  "row_delta": 0.023,
  "snapshot_id": 15,
  "parquet_paths": [...],
  "b2_urls": [...],
  "start_time": "2025-11-18T16:16:15",
  "end_time": "2025-11-18T16:16:32"
}
```

**Query Example**:
```sql
-- Latest runs by state
SELECT
    details->>'state' as state,
    details->>'snapshot_version' as version,
    details->>'kill_switch_status' as kill_switch,
    details->>'row_delta' as delta,
    created_at
FROM shq.audit_log
WHERE event_type = 'outreach_snapshot'
ORDER BY created_at DESC
LIMIT 10;
```

### Phase 2B Output Structure

```
exports/
├── WV/
│   ├── companies/
│   │   ├── good/
│   │   │   ├── companies_good_20251118161627.parquet
│   │   │   └── companies_good_20251118173045.parquet
│   │   └── bad/
│   │       ├── companies_bad_20251118161627.parquet
│   │       └── companies_bad_20251118173045.parquet
│   └── people/
│       ├── good/
│       │   ├── people_good_20251118161627.parquet
│       │   └── people_good_20251118173045.parquet
│       └── bad/
│           ├── people_bad_20251118161627.parquet
│           └── people_bad_20251118173045.parquet
├── PA/
│   └── (same structure)
└── VA/
    └── (same structure)
```

### Phase 2B Troubleshooting

#### Kill Switch Triggered

**K1 Triggered (Bad Ratio Spike)**:
```
❌ K1 TRIGGERED: Company bad ratio 18.2% > 15.0%
```

**Investigation**:
1. Check validation rules still match schema:
   ```sql
   SELECT * FROM marketing.company_master LIMIT 5;
   ```
2. Review recent schema changes in Neon
3. Examine bad records:
   ```python
   conn.execute("SELECT validation_errors, COUNT(*) FROM companies_bad GROUP BY validation_errors;").fetchall()
   ```

**Resolution**:
- If schema changed: Update validation rules in pipeline
- If data quality degraded: Review source data
- If threshold too strict: Adjust `KILL_SWITCH_BAD_RATIO`

**K2 Triggered (Row Delta Drift)**:
```
❌ K2 TRIGGERED: Row delta 35.4% > 30.0%
```

**Investigation**:
1. Compare last 2 snapshots:
   ```python
   conn.execute("SELECT * FROM snapshots WHERE state = 'WV' ORDER BY created_at DESC LIMIT 2;").fetchall()
   ```
2. Check for duplicate loads or mass deletions in Neon
3. Verify state filter is correct

**Resolution**:
- If legitimate growth: Increase `KILL_SWITCH_ROW_DELTA` temporarily
- If duplicate load: Clear duplicate data in Neon
- If mass deletion: Investigate source data pipeline

**K3 Triggered (ID Integrity)**:
```
❌ K3 TRIGGERED: 5 null company_unique_id values
```

**Investigation**:
1. Find null IDs in source:
   ```sql
   SELECT * FROM marketing.company_master
   WHERE company_unique_id IS NULL
   AND address_state = 'WV';
   ```
2. Check ID generation pipeline in Neon

**Resolution**:
- Fix null IDs in source table
- Investigate why ID generation failed
- Re-run pipeline after fix

#### No Previous Snapshot

**Message**: `K2 skip (no previous snapshot)`

**Explanation**: First run for this state - no historical comparison possible.

**Action**: None required - K2 will activate on subsequent runs.

---

## Phase 1 Usage (Legacy)

### Pipeline Flow

```
Neon PostgreSQL (WV companies + people)
         ↓
    DuckDB (in-memory validation)
         ↓
    Parquet files (with headers)
         ↓
   Backblaze B2 (organized storage)
         ↓
  shq.audit_log (Neon tracking)
```

---

## Directory Structure

```
outreach_core/workbench/
├── duck/
│   └── outreach_workbench.duckdb        # DuckDB database (includes snapshots table)
├── exports/
│   ├── WV/                              # Phase 2B: State-organized
│   │   ├── companies/
│   │   │   ├── good/
│   │   │   │   ├── companies_good_20251118161627.parquet
│   │   │   │   └── companies_good_20251118173045.parquet
│   │   │   └── bad/
│   │   │       ├── companies_bad_20251118161627.parquet
│   │   │       └── companies_bad_20251118173045.parquet
│   │   └── people/
│   │       ├── good/
│   │       │   ├── people_good_20251118161627.parquet
│   │       │   └── people_good_20251118173045.parquet
│   │       └── bad/
│   │           ├── people_bad_20251118161627.parquet
│   │           └── people_bad_20251118173045.parquet
│   ├── PA/, VA/, MD/, OH/, DE/          # Other states (same structure)
│   └── wv/                              # Phase 1: Legacy WV exports
│       └── (non-versioned files)
├── logs/
├── wv_duckdb_pipeline.py               # Phase 1: Single-state pipeline (legacy)
├── state_duckdb_pipeline.py            # Phase 2B: Multi-state with versioning (recommended)
└── README.md                           # This file
```

---

## Usage

### Quick Start

```bash
cd outreach_core/workbench
python wv_duckdb_pipeline.py
```

### What It Does

1. **Pulls Data from Neon**
   - Companies: `SELECT * FROM marketing.company_master WHERE address_state = 'WV'`
   - People: `SELECT * FROM marketing.people_master WHERE company_unique_id IN (WV companies)`

2. **Validates in DuckDB**
   - **Companies Good**: `company_name IS NOT NULL AND website_url IS NOT NULL AND website_url LIKE '%.%'`
   - **Companies Bad**: Records that fail validation + `validation_errors` array
   - **People Good**: `email ~ regex AND title IS NOT NULL`
   - **People Bad**: Records that fail validation + `validation_errors` array

3. **Exports to Parquet**
   - Preserves all column headers
   - Preserves data types
   - Organized by good/bad split
   - Compressed Parquet format

4. **Uploads to Backblaze B2**
   - Bucket: `svg-enrichment`
   - Path: `outreach/wv/{companies|people}/{good|bad}/*.parquet`
   - Metadata: table_name, upload_timestamp, pipeline

5. **Logs to Neon**
   - Table: `shq.audit_log`
   - Event: `outreach_validation_run`
   - Details: Record counts, file paths, B2 URLs, timing

---

## Configuration

### Environment Variables Required

```bash
# Neon PostgreSQL
NEON_HOST=ep-ancient-waterfall-a42vy0du-pooler.us-east-1.aws.neon.tech
NEON_DATABASE=Marketing DB
NEON_USER=Marketing DB_owner
NEON_PASSWORD=<password>

# Backblaze B2
B2_KEY_ID=<key_id>
B2_APPLICATION_KEY=<app_key>
B2_BUCKET=svg-enrichment
```

---

## Validation Rules

### Companies

**Good Criteria:**
- `company_name IS NOT NULL`
- `website_url IS NOT NULL`
- `website_url LIKE '%.%'` (contains domain)

**Bad Records Get:**
- `validation_errors` array with specific failure reasons:
  - `company_name_missing`
  - `website_url_missing`
  - `website_url_invalid`

### People

**Good Criteria:**
- `email ~ '^[^@]+@[^@]+\.[^@]+'` (valid email format)
- `title IS NOT NULL` (job title required)

**Bad Records Get:**
- `validation_errors` array with specific failure reasons:
  - `email_invalid`
  - `title_missing`

---

## Output Files

### Parquet Files (Local)

All exported with full schema preservation:

```
exports/wv/companies/good/companies_good.parquet    (all valid companies)
exports/wv/companies/bad/companies_bad.parquet      (invalid companies + errors)
exports/wv/people/good/people_good.parquet          (all valid people)
exports/wv/people/bad/people_bad.parquet            (invalid people + errors)
```

### Backblaze B2 Storage

Uploaded to: `b2://svg-enrichment/outreach/wv/`

```
outreach/wv/companies/good/companies_good.parquet
outreach/wv/companies/bad/companies_bad.parquet
outreach/wv/people/good/people_good.parquet
outreach/wv/people/bad/people_bad.parquet
```

### Audit Log (Neon)

Logged to: `shq.audit_log`

```sql
SELECT * FROM shq.audit_log
WHERE event_type = 'outreach_validation_run'
ORDER BY created_at DESC;
```

Details include:
- Record counts (good/bad for companies/people)
- Parquet file paths
- B2 upload URLs
- Start/end timestamps

---

## Performance

### Test Run (2025-11-18)

```
Total Records: 0 (no WV data in database yet)
Pipeline Duration: ~5 seconds
Files Created: 4 Parquet files
B2 Uploads: 4 files
Audit Log: 1 entry (ID: 1)
```

### Expected Performance (With Data)

```
For 453 companies + 170 people (623 total):
- Data Pull: ~2 seconds
- Validation: ~1 second
- Parquet Export: ~1 second
- B2 Upload: ~2 seconds
- Total: ~6 seconds
```

---

## Troubleshooting

### No Data Retrieved

**Issue**: `✅ Loaded 0 WV companies`

**Cause**: No records in `marketing.company_master` with `address_state = 'WV'`

**Solution**:
- Verify data exists: `SELECT COUNT(*) FROM marketing.company_master WHERE address_state = 'WV';`
- Check if state column has different values
- Load test data if needed

### DuckDB Extension Error

**Issue**: `Failed to load PostgreSQL extension`

**Solution**:
```python
duck_conn.execute("INSTALL postgres;")
duck_conn.execute("LOAD postgres;")
```

### B2 Upload Failed

**Issue**: `Failed to upload to B2`

**Solution**:
- Verify B2 credentials in `.env`
- Test connection: `python ctb/sys/toolbox-hub/backend/backblaze/test_b2_native.py`
- Check bucket exists: `svg-enrichment`

### Audit Log Error

**Issue**: `table shq.audit_log does not exist`

**Solution**: Pipeline auto-creates the table on first run:
```sql
CREATE SCHEMA IF NOT EXISTS shq;
CREATE TABLE IF NOT EXISTS shq.audit_log (...);
```

---

## Schema Information

### Companies Schema (marketing.company_master)

Key columns used:
- `company_unique_id` (PK)
- `company_name`
- `website_url`
- `address_state` (filter: 'WV')
- Plus 15+ other columns (all preserved in Parquet)

### People Schema (marketing.people_master)

Key columns used:
- `unique_id` (PK)
- `company_unique_id` (FK to companies)
- `email`
- `title`
- `first_name`, `last_name`, `full_name`
- Plus 10+ other columns (all preserved in Parquet)

---

## Next Steps

### For Production Use

1. **Load WV Data**
   ```sql
   -- Verify data exists
   SELECT COUNT(*) FROM marketing.company_master WHERE address_state = 'WV';
   ```

2. **Run Pipeline**
   ```bash
   python wv_duckdb_pipeline.py
   ```

3. **Verify Results**
   - Check Parquet files in `exports/wv/`
   - Verify B2 uploads: https://secure.backblaze.com/b2_buckets.htm
   - Check audit log: `SELECT * FROM shq.audit_log;`

4. **Analyze Validation Errors**
   ```python
   import duckdb

   conn = duckdb.connect('duck/outreach_workbench.duckdb')

   # Check bad companies
   errors = conn.execute("""
       SELECT validation_errors, COUNT(*) as count
       FROM companies_bad
       GROUP BY validation_errors
   """).fetchall()
   ```

### For Scale Testing

To process larger datasets:
1. Remove `WHERE address_state = 'WV'` filter
2. Process all states
3. Monitor DuckDB memory usage
4. Batch B2 uploads if needed

---

## Technical Details

### DuckDB Configuration

- Database: `duck/outreach_workbench.duckdb`
- Extension: PostgreSQL scanner
- Memory: In-memory processing (no disk limits)
- Tables: 6 total (raw + good/bad for companies/people)

### Parquet Configuration

- Format: Apache Parquet (columnar)
- Compression: Snappy (default)
- Headers: Preserved
- Schema: Exact match from Neon
- Size: ~800-900 bytes per file (empty data)

### B2 Configuration

- Endpoint: us-east-003
- Bucket: svg-enrichment
- Prefix: outreach/wv/
- Metadata: table_name, upload_timestamp, pipeline
- Access: Private

---

## Dependencies

```bash
pip install duckdb psycopg2 python-dotenv b2sdk
```

All dependencies already installed.

---

## Contact & Support

For issues or questions:
- Check audit log: `SELECT * FROM shq.audit_log;`
- Review Parquet files: `ls -lh exports/wv/**/*.parquet`
- Verify B2 uploads: https://secure.backblaze.com/b2_buckets.htm

---

**Last Run (Phase 2B)**: 2025-11-18T16:16:27
**Status**: ✅ All 11 steps completed successfully
**State**: WV
**Snapshot Version**: 20251118161627
**Audit Log ID**: 2
**DuckDB Snapshot ID**: 1

---

## Version History

### Phase 2B (2025-11-18)
- Multi-state execution with `--state` argument
- Snapshot versioning (UTC timestamps)
- Linked people validation (JOIN with companies_good)
- 3 Kill switches (K1, K2, K3)
- Versioned Parquet filenames
- B2 metadata tagging
- Enhanced audit logging
- DuckDB snapshots table

### Phase 1 (2025-11-18)
- Initial single-state (WV) implementation
- Basic validation pipeline
- Parquet export with headers
- B2 upload with basic metadata
- Neon audit logging
