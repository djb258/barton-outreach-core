# Form 5500 Import Guide - DOL Dataset to Neon PostgreSQL

**Date:** 2025-11-27
**Status:** ✅ Schema Ready for Import
**Dataset Source:** DOL EBSA Form 5500 Research Files

---

## Schema Readiness Summary

✅ **Tables Created:**
- `marketing.form_5500` - Main Form 5500 data
- `marketing.form_5500_staging` - CSV import staging
- `marketing.dol_violations` - DOL violations tracking

✅ **Indexes Created (10):**
- `idx_5500_ein` - Fast EIN lookups
- `idx_5500_company` - Company matching
- `idx_5500_state` - Geographic filtering
- `idx_5500_year` - Temporal queries
- `idx_5500_sponsor_state` - Sponsor name + state composite
- `idx_5500_date_received` - Date-based queries
- `idx_5500_participant_count` - Participant filtering (partial)
- `idx_5500_raw_payload_gin` - JSONB queries
- `uq_form_5500_ack_id` - Unique constraint on DOL filing ID

✅ **Constraints Added:**
- `uq_form_5500_ack_id` - Prevents duplicate filings
- `chk_form_5500_ein_format` - Validates 9-digit EIN format
- NOT NULL on `ein` - EIN required

✅ **Functions & Procedures:**
- `marketing.match_5500_to_company()` - Automatic company matching
- `marketing.process_5500_staging()` - Batch import processor

---

## DOL Dataset Structure

### Dataset Types

**Two versions available from DOL:**

1. **"All" datasets** - Include all filings (amendments, duplicates)
   - Larger file size
   - Historical versions of each plan
   - Multiple ACK_IDs per plan per year

2. **"Latest" datasets** ⭐ **RECOMMENDED**
   - Most recent filing per plan per year
   - Cleaner data (one record per plan)
   - Faster processing

**Recommendation:** Start with "Latest" datasets for current year.

### File Format

- **Format:** Zipped CSV (comma-delimited)
- **Text Qualifier:** Double quotes (")
- **Header Row:** Yes (field names in first row)
- **Date Format:** mm/dd/yyyy (stored as Text)
- **Numeric Format:** Standard (counts end in _CNT)

### Key Identifiers (from DOL Dataset Guide)

| Identifier | Purpose | Usage in Your Schema |
|------------|---------|----------------------|
| **ACK_ID** | Unique filing identifier | Unique constraint added (primary key for joins) |
| EIN | Employer ID Number | Indexed, NOT NULL, 9-digit format check |
| FORM_ID | Schedule identifier | Not used (schedules future enhancement) |
| ROW_ORDER | Repeating element ID | Not used |
| CODE_ORDER | Service code ID | Not used |

---

## Field Mapping: DOL CSV → Neon Schema

### Core Form 5500 Fields

Your `marketing.form_5500_staging` table maps to DOL fields as follows:

| Your Column | DOL CSV Field | Data Type | Notes |
|-------------|---------------|-----------|-------|
| `ack_id` | ACK_ID | VARCHAR(30) | DOL unique filing ID |
| `ein` | SPONSOR_DFE_EIN | VARCHAR(9) | Employer ID (required) |
| `plan_number` | SPONSOR_DFE_PN | VARCHAR(3) | Plan number (001, 002, etc.) |
| `plan_name` | PLAN_NAME | VARCHAR(140) | Full plan name |
| `sponsor_name` | SPONSOR_DFE_NAME | VARCHAR(70) | Company name |
| `address` | SPONS_DFE_MAIL_US_ADDRESS1 | VARCHAR(35) | Street address |
| `city` | SPONS_DFE_MAIL_US_CITY | VARCHAR(22) | City |
| `state` | SPONS_DFE_MAIL_US_STATE | VARCHAR(2) | State abbreviation |
| `zip` | SPONS_DFE_MAIL_US_ZIP | VARCHAR(12) | ZIP code |
| `date_received` | RECEIPT_DATE | VARCHAR(10) | Date as mm/dd/yyyy string |
| `plan_codes` | (multiple fields) | VARCHAR(59) | Plan type codes (composite) |
| `participant_count` | TOT_PARTCP_BOY_CNT | VARCHAR(20) | Participant count as string |
| `total_assets` | TOT_ASSETS_EOY_AMT | VARCHAR(30) | Total assets as string |

### Additional Useful DOL Fields (for future enhancement)

| DOL Field | Description | Potential Use |
|-----------|-------------|---------------|
| BUSINESS_CODE | NAICS/SIC code | Industry classification |
| ADMIN_NAME | Plan administrator | Contact information |
| ADMIN_PHONE | Admin phone | Direct contact |
| TYPE_PENSION_BNFT_CODE | Benefit type | Plan classification |
| TYPE_WELFARE_BNFT_CODE | Welfare type | Benefit classification |
| FUNDING_ARRANGEMENT | Funding type | Financial structure |

---

## Import Process

### Step 1: Download DOL Data

**Source:** https://www.dol.gov/agencies/ebsa/researchers/data/retirement-bulletin

**Recommended Files:**
- **2024 Form 5500 Latest Filing** (most recent year)
- File name: `f_5500_2024_latest.csv` (or similar)
- Size: ~500MB zipped, ~2GB unzipped

**Alternative:** Historical years available (2010-2023)

### Step 2: Extract and Prepare CSV

```bash
# Extract ZIP
unzip f_5500_2024_latest.zip

# Check file structure
head -n 2 f_5500_2024_latest.csv

# Expected header format:
# "ACK_ID","SPONSOR_DFE_EIN","SPONSOR_DFE_PN","PLAN_NAME",...
```

### Step 3: Map CSV Columns to Your Schema

**Create column mapping file:** `5500_column_map.txt`

```
# DOL CSV Column -> Your Staging Column
ACK_ID -> ack_id
SPONSOR_DFE_EIN -> ein
SPONSOR_DFE_PN -> plan_number
PLAN_NAME -> plan_name
SPONSOR_DFE_NAME -> sponsor_name
SPONS_DFE_MAIL_US_ADDRESS1 -> address
SPONS_DFE_MAIL_US_CITY -> city
SPONS_DFE_MAIL_US_STATE -> state
SPONS_DFE_MAIL_US_ZIP -> zip
RECEIPT_DATE -> date_received
TOT_PARTCP_BOY_CNT -> participant_count
TOT_ASSETS_EOY_AMT -> total_assets
```

### Step 4: Import to Staging (Option A: COPY Command)

**Direct COPY from CSV:**

```sql
-- Option A: Direct COPY (if column order matches)
COPY marketing.form_5500_staging (
    ack_id,
    ein,
    plan_number,
    plan_name,
    sponsor_name,
    address,
    city,
    state,
    zip,
    date_received,
    participant_count,
    total_assets
)
FROM '/path/to/f_5500_2024_latest.csv'
CSV HEADER
DELIMITER ','
QUOTE '"'
NULL ''
WHERE ein ~ '^[0-9]{9}$';  -- Only import valid EINs
```

**Important Notes:**
- File path must be accessible to PostgreSQL server
- Use absolute path
- Neon may require alternative approach (see Option B)

### Step 4: Import to Staging (Option B: psql Client)

**Using psql client (more reliable for Neon):**

```bash
# Set environment variable
export NEON_CONNECTION_STRING="postgresql://user:pass@host:5432/db?sslmode=require"

# Import via psql
psql $NEON_CONNECTION_STRING << 'EOF'
\COPY marketing.form_5500_staging (
    ack_id,
    ein,
    plan_number,
    plan_name,
    sponsor_name,
    address,
    city,
    state,
    zip,
    date_received,
    participant_count,
    total_assets
)
FROM '/local/path/to/f_5500_2024_latest.csv'
CSV HEADER
DELIMITER ','
QUOTE '"'
NULL '';
EOF
```

**Note:** `\COPY` runs on client side (your machine), works with Neon.

### Step 4: Import to Staging (Option C: Node.js Script)

**For programmatic import with validation:**

```javascript
const { Client } = require('pg');
const fs = require('fs');
const csv = require('csv-parser');
require('dotenv').config();

const client = new Client({ connectionString: process.env.NEON_CONNECTION_STRING });

async function importCSV(filePath) {
    await client.connect();

    let imported = 0;
    let skipped = 0;

    const stream = fs.createReadStream(filePath)
        .pipe(csv())
        .on('data', async (row) => {
            // Validate EIN format
            if (!/^\d{9}$/.test(row.SPONSOR_DFE_EIN)) {
                skipped++;
                return;
            }

            try {
                await client.query(`
                    INSERT INTO marketing.form_5500_staging (
                        ack_id, ein, plan_number, plan_name,
                        sponsor_name, address, city, state, zip,
                        date_received, participant_count, total_assets
                    ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12)
                `, [
                    row.ACK_ID,
                    row.SPONSOR_DFE_EIN,
                    row.SPONSOR_DFE_PN,
                    row.PLAN_NAME,
                    row.SPONSOR_DFE_NAME,
                    row.SPONS_DFE_MAIL_US_ADDRESS1,
                    row.SPONS_DFE_MAIL_US_CITY,
                    row.SPONS_DFE_MAIL_US_STATE,
                    row.SPONS_DFE_MAIL_US_ZIP,
                    row.RECEIPT_DATE,
                    row.TOT_PARTCP_BOY_CNT,
                    row.TOT_ASSETS_EOY_AMT
                ]);
                imported++;

                if (imported % 1000 === 0) {
                    console.log(`Imported ${imported} records...`);
                }
            } catch (err) {
                console.error(`Error importing ${row.ACK_ID}:`, err.message);
                skipped++;
            }
        })
        .on('end', () => {
            console.log(`Complete: ${imported} imported, ${skipped} skipped`);
            client.end();
        });
}

importCSV('/path/to/f_5500_2024_latest.csv');
```

### Step 5: Process Staging Data

**After CSV import to staging:**

```sql
-- Check staging row count
SELECT COUNT(*) FROM marketing.form_5500_staging;

-- Sample staging data
SELECT * FROM marketing.form_5500_staging LIMIT 5;

-- Process staging → main table (matches companies, updates EINs)
CALL marketing.process_5500_staging();

-- Expected output:
-- NOTICE: Processed 150000 records, matched 45000 to existing companies
```

**What `process_5500_staging()` does:**
1. Loops through each staging record
2. Tries to match sponsor_name + city + state to `company_master`
3. Inserts into `form_5500` with matched `company_unique_id` (or NULL)
4. Updates `company_master.ein` if matched and EIN was NULL
5. Clears staging table

### Step 6: Verify Import

```sql
-- Check total records imported
SELECT COUNT(*) FROM marketing.form_5500;

-- Check records matched to companies
SELECT
    COUNT(*) as total,
    COUNT(company_unique_id) as matched,
    ROUND(100.0 * COUNT(company_unique_id) / COUNT(*), 1) as match_rate
FROM marketing.form_5500;

-- Check EIN distribution by state
SELECT
    state,
    COUNT(*) as filing_count,
    COUNT(DISTINCT ein) as unique_employers
FROM marketing.form_5500
GROUP BY state
ORDER BY filing_count DESC
LIMIT 10;

-- Check participant count distribution
SELECT
    CASE
        WHEN participant_count < 100 THEN '<100'
        WHEN participant_count < 500 THEN '100-500'
        WHEN participant_count < 1000 THEN '500-1000'
        WHEN participant_count < 5000 THEN '1000-5000'
        ELSE '5000+'
    END as size_range,
    COUNT(*) as plan_count
FROM marketing.form_5500
WHERE participant_count IS NOT NULL
GROUP BY size_range
ORDER BY
    CASE size_range
        WHEN '<100' THEN 1
        WHEN '100-500' THEN 2
        WHEN '500-1000' THEN 3
        WHEN '1000-5000' THEN 4
        ELSE 5
    END;

-- Find unmatched companies with largest plans
SELECT
    sponsor_name,
    city,
    state,
    participant_count,
    total_assets,
    ein
FROM marketing.form_5500
WHERE company_unique_id IS NULL
AND participant_count > 500
ORDER BY participant_count DESC
LIMIT 20;
```

---

## Data Quality Checks

### Check 1: Duplicate ACK_IDs (Should be 0)

```sql
SELECT ack_id, COUNT(*)
FROM marketing.form_5500
GROUP BY ack_id
HAVING COUNT(*) > 1;

-- Expected: 0 rows (unique constraint prevents duplicates)
```

### Check 2: Invalid EINs (Should be 0)

```sql
SELECT ein, COUNT(*)
FROM marketing.form_5500
WHERE ein !~ '^[0-9]{9}$'
GROUP BY ein;

-- Expected: 0 rows (check constraint enforces format)
```

### Check 3: State Distribution

```sql
-- Your target states: PA, VA, MD, OH, WV, KY
SELECT
    state,
    COUNT(*) as filings,
    COUNT(DISTINCT ein) as employers
FROM marketing.form_5500
WHERE state IN ('PA', 'VA', 'MD', 'OH', 'WV', 'KY')
GROUP BY state
ORDER BY filings DESC;
```

### Check 4: Company Match Rate

```sql
-- Goal: >60% match rate to existing companies
SELECT
    ROUND(100.0 * COUNT(company_unique_id) / COUNT(*), 1) as match_rate_pct,
    COUNT(*) as total_records,
    COUNT(company_unique_id) as matched,
    COUNT(*) - COUNT(company_unique_id) as unmatched
FROM marketing.form_5500;
```

---

## Post-Import Optimization

### Update Company EINs

```sql
-- Update companies that matched but didn't have EIN
UPDATE marketing.company_master cm
SET ein = f.ein
FROM marketing.form_5500 f
WHERE f.company_unique_id = cm.company_unique_id
AND cm.ein IS NULL;

-- Check updated count
SELECT COUNT(*)
FROM marketing.company_master
WHERE ein IS NOT NULL;
```

### Analyze Tables for Query Performance

```sql
-- Update PostgreSQL statistics
ANALYZE marketing.form_5500;
ANALYZE marketing.company_master;
```

### Check Enrichment Score Impact

```sql
-- Companies should now have higher enrichment scores
SELECT
    CASE
        WHEN enrichment_score < 50 THEN '<50'
        WHEN enrichment_score < 70 THEN '50-70'
        WHEN enrichment_score < 85 THEN '70-85'
        ELSE '85+'
    END as score_range,
    COUNT(*) as company_count
FROM marketing.v_company_enrichment_status
GROUP BY score_range
ORDER BY
    CASE score_range
        WHEN '<50' THEN 1
        WHEN '50-70' THEN 2
        WHEN '70-85' THEN 3
        ELSE 4
    END;
```

---

## Troubleshooting

### Issue: COPY command fails with permission error

**Solution:** Use `\COPY` (client-side) instead of `COPY` (server-side)

```bash
# Instead of COPY (server-side)
COPY marketing.form_5500_staging FROM '/path/file.csv' CSV HEADER;

# Use \COPY (client-side)
\COPY marketing.form_5500_staging FROM '/local/path/file.csv' CSV HEADER;
```

### Issue: "Column count mismatch" error

**Solution:** Specify exact columns in COPY command

```sql
-- Don't rely on column order, specify explicitly
COPY marketing.form_5500_staging (
    ack_id,
    ein,
    plan_number,
    -- ... list all columns
)
FROM '/path/file.csv' CSV HEADER;
```

### Issue: Date parsing errors

**Solution:** Import as VARCHAR (already done in staging), convert during processing

```sql
-- Already handled in process_5500_staging() procedure
-- Converts: TO_DATE(date_received, 'MM/DD/YYYY')
```

### Issue: Numeric parsing errors (participant_count, total_assets)

**Solution:** Already handled with REGEXP_REPLACE in processing procedure

```sql
-- Already in process_5500_staging()
NULLIF(REGEXP_REPLACE(participant_count, '[^0-9]', '', 'g'), '')::INT
NULLIF(REGEXP_REPLACE(total_assets, '[^0-9.]', '', 'g'), '')::NUMERIC
```

### Issue: Low company match rate (<40%)

**Solution:** Manual matching for high-value unmatched records

```sql
-- Find unmatched with largest plans
SELECT
    id,
    sponsor_name,
    city,
    state,
    participant_count
FROM marketing.form_5500
WHERE company_unique_id IS NULL
ORDER BY participant_count DESC
LIMIT 50;

-- Manual match (after verifying company exists)
UPDATE marketing.form_5500
SET company_unique_id = '04.04.01.01.XXXXX.XXX'
WHERE id = 12345;
```

---

## Expected Performance

### Dataset Size Estimates (2024 Latest)

- **Total records:** ~700,000 filings
- **Unique employers (EINs):** ~150,000
- **Your target states:** ~80,000 filings (PA, VA, MD, OH, WV, KY)
- **Expected match rate:** 50-70% to existing companies

### Import Time Estimates

| Method | Speed | Time for 700K records |
|--------|-------|----------------------|
| COPY command | ~50K rows/sec | 14 seconds |
| \COPY client | ~10K rows/sec | 70 seconds |
| Node.js script | ~1K rows/sec | 12 minutes |
| Process staging | ~500 rows/sec | 23 minutes |

**Recommendation:** Use `\COPY` for reliability, accept 1-2 minute import time.

---

## Success Criteria

✅ **Data Import:**
- [ ] CSV downloaded from DOL
- [ ] Data imported to staging without errors
- [ ] Processing completed successfully
- [ ] Zero duplicate ACK_IDs
- [ ] Zero invalid EINs

✅ **Company Matching:**
- [ ] Match rate >50% to existing companies
- [ ] Top 100 unmatched manually reviewed
- [ ] Companies updated with EINs

✅ **Enrichment Impact:**
- [ ] Average enrichment score increased by 10+ points
- [ ] Companies with has_5500=1 increased to >60%
- [ ] EIN coverage increased to >70%

---

## Next Steps After Import

1. **Set up annual refresh workflow** (DOL releases data yearly)
2. **Create Grafana dashboard** showing Form 5500 metrics
3. **Build BIT scoring model** using plan participant trends
4. **Add Schedule C import** (service provider data) - future enhancement
5. **Integrate with DOL violations** data feed

---

**Status:** ✅ Schema ready, import guide complete
**Action Required:** Download 2024 Form 5500 "Latest" CSV from DOL
**Estimated Import Time:** 2-25 minutes (depending on method)
