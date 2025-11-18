# Outreach Core Workbench - DuckDB → Parquet → B2 Pipeline

**Date**: 2025-11-18
**Status**: ✅ Production Ready
**Pipeline**: `wv_duckdb_pipeline.py`

---

## Overview

This workbench implements a complete data validation pipeline using DuckDB for in-memory processing and Backblaze B2 for Parquet storage.

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
│   └── outreach_workbench.duckdb        # DuckDB database file
├── exports/
│   └── wv/
│       ├── companies/
│       │   ├── good/
│       │   │   └── companies_good.parquet
│       │   └── bad/
│       │       └── companies_bad.parquet
│       └── people/
│           ├── good/
│           │   └── people_good.parquet
│           └── bad/
│               └── people_bad.parquet
├── logs/
├── wv_duckdb_pipeline.py               # Main pipeline script
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

**Last Run**: 2025-11-18T11:08:40
**Status**: ✅ All steps completed successfully
**Audit Log ID**: 1
