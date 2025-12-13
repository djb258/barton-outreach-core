# Form 5500 Import Checklist

**Date:** 2025-11-27
**Purpose:** Pre-flight checklist before importing DOL Form 5500 data

---

## ✅ Schema Readiness

- [x] **Tables created**
  - [x] marketing.form_5500
  - [x] marketing.form_5500_staging
  - [x] marketing.dol_violations

- [x] **Indexes created (10)**
  - [x] idx_5500_ein
  - [x] idx_5500_company
  - [x] idx_5500_state
  - [x] idx_5500_year
  - [x] idx_5500_sponsor_state
  - [x] idx_5500_date_received
  - [x] idx_5500_participant_count
  - [x] idx_5500_raw_payload_gin
  - [x] uq_form_5500_ack_id (unique constraint)
  - [x] form_5500_pkey (primary key)

- [x] **Constraints added**
  - [x] uq_form_5500_ack_id (prevents duplicate filings)
  - [x] chk_form_5500_ein_format (9-digit EIN validation)
  - [x] NOT NULL on ein column

- [x] **Functions & procedures**
  - [x] marketing.match_5500_to_company()
  - [x] marketing.process_5500_staging()

- [x] **Column comments added** (documentation)

---

## 🔽 Data Download

- [ ] **Navigate to DOL website**
  - URL: https://www.dol.gov/agencies/ebsa/researchers/data/retirement-bulletin

- [ ] **Download 2024 Form 5500 "Latest" dataset**
  - File: f_5500_2024_latest.zip (or similar name)
  - Size: ~500MB compressed, ~2GB uncompressed
  - Description: "Most recent filing per plan"

- [ ] **Verify file integrity**
  - Check file size matches DOL documentation
  - Verify ZIP extracts without errors

- [ ] **Extract CSV**
  ```bash
  unzip f_5500_2024_latest.zip
  ```

- [ ] **Inspect CSV structure**
  ```bash
  head -n 2 f_5500_2024_latest.csv
  ```
  - Verify header row exists
  - Check delimiter is comma
  - Verify text qualifier is double-quote

---

## 📋 Column Mapping Verification

Required DOL columns (verify these exist in CSV header):

- [ ] `ACK_ID` - Unique filing identifier
- [ ] `SPONSOR_DFE_EIN` - Employer ID
- [ ] `SPONSOR_DFE_PN` - Plan number
- [ ] `PLAN_NAME` - Plan name
- [ ] `SPONSOR_DFE_NAME` - Company/sponsor name
- [ ] `SPONS_DFE_MAIL_US_ADDRESS1` - Address
- [ ] `SPONS_DFE_MAIL_US_CITY` - City
- [ ] `SPONS_DFE_MAIL_US_STATE` - State
- [ ] `SPONS_DFE_MAIL_US_ZIP` - ZIP code
- [ ] `RECEIPT_DATE` - Date received
- [ ] `TOT_PARTCP_BOY_CNT` - Participant count
- [ ] `TOT_ASSETS_EOY_AMT` - Total assets

If column names differ, update mapping in import script.

---

## 🚀 Import Method Selection

Choose ONE import method:

### Option A: Direct COPY (Fastest)
- [ ] File accessible to PostgreSQL server
- [ ] Have absolute file path
- [ ] Neon supports server-side COPY

### Option B: \COPY Client (Recommended for Neon)
- [ ] psql installed locally
- [ ] Have NEON_CONNECTION_STRING in .env
- [ ] File on local machine

### Option C: Node.js Script (Most Control)
- [ ] Node.js installed
- [ ] csv-parser package installed (`npm install csv-parser`)
- [ ] Want row-by-row validation

---

## 💾 Pre-Import Preparation

- [ ] **Clear staging table** (if previous import exists)
  ```sql
  TRUNCATE marketing.form_5500_staging;
  ```

- [ ] **Verify database connection**
  ```bash
  psql $NEON_CONNECTION_STRING -c "SELECT 'Connected' as status;"
  ```

- [ ] **Check available disk space** (Neon storage)
  ```sql
  SELECT pg_size_pretty(pg_database_size('Marketing DB'));
  ```

- [ ] **Backup existing form_5500 data** (if any)
  ```sql
  CREATE TABLE marketing.form_5500_backup AS
  SELECT * FROM marketing.form_5500;
  ```

---

## 📥 Import Execution

### Using \COPY (Recommended)

1. [ ] **Set connection string**
   ```bash
   export NEON_CONNECTION_STRING="postgresql://user:pass@host:5432/db?sslmode=require"
   ```

2. [ ] **Run import command**
   ```bash
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
   FROM '/absolute/path/to/f_5500_2024_latest.csv'
   CSV HEADER
   DELIMITER ','
   QUOTE '"'
   NULL '';
   EOF
   ```

3. [ ] **Verify staging row count**
   ```sql
   SELECT COUNT(*) FROM marketing.form_5500_staging;
   ```
   Expected: 700,000+ rows

4. [ ] **Sample staging data**
   ```sql
   SELECT * FROM marketing.form_5500_staging LIMIT 5;
   ```
   Verify data looks correct

---

## ⚙️ Process Staging Data

1. [ ] **Run processing procedure**
   ```sql
   CALL marketing.process_5500_staging();
   ```
   Expected output: `NOTICE: Processed XXXXX records, matched YYYY to existing companies`

2. [ ] **Verify main table row count**
   ```sql
   SELECT COUNT(*) FROM marketing.form_5500;
   ```
   Should match staging count

3. [ ] **Check match rate**
   ```sql
   SELECT
       COUNT(*) as total,
       COUNT(company_unique_id) as matched,
       ROUND(100.0 * COUNT(company_unique_id) / COUNT(*), 1) as match_rate_pct
   FROM marketing.form_5500;
   ```
   Target: >50% match rate

---

## ✔️ Data Quality Verification

### Check 1: Duplicate ACK_IDs
- [ ] **Run check**
  ```sql
  SELECT ack_id, COUNT(*)
  FROM marketing.form_5500
  GROUP BY ack_id
  HAVING COUNT(*) > 1;
  ```
  Expected: 0 rows

### Check 2: Invalid EINs
- [ ] **Run check**
  ```sql
  SELECT ein, COUNT(*)
  FROM marketing.form_5500
  WHERE ein !~ '^[0-9]{9}$'
  GROUP BY ein;
  ```
  Expected: 0 rows

### Check 3: Target State Coverage
- [ ] **Run check**
  ```sql
  SELECT
      state,
      COUNT(*) as filings,
      COUNT(DISTINCT ein) as unique_employers
  FROM marketing.form_5500
  WHERE state IN ('PA', 'VA', 'MD', 'OH', 'WV', 'KY')
  GROUP BY state
  ORDER BY filings DESC;
  ```
  Expected: 80,000+ total filings across target states

### Check 4: Participant Count Distribution
- [ ] **Run check**
  ```sql
  SELECT
      CASE
          WHEN participant_count < 100 THEN '<100'
          WHEN participant_count < 500 THEN '100-500'
          WHEN participant_count < 1000 THEN '500-1000'
          ELSE '1000+'
      END as size_range,
      COUNT(*) as plan_count
  FROM marketing.form_5500
  WHERE participant_count IS NOT NULL
  GROUP BY size_range;
  ```
  Expected: Distribution across all ranges

---

## 🔄 Post-Import Updates

1. [ ] **Update company EINs**
   ```sql
   UPDATE marketing.company_master cm
   SET ein = f.ein
   FROM marketing.form_5500 f
   WHERE f.company_unique_id = cm.company_unique_id
   AND cm.ein IS NULL;
   ```
   Check rows updated:
   ```sql
   SELECT COUNT(*) FROM marketing.company_master WHERE ein IS NOT NULL;
   ```

2. [ ] **Update table statistics**
   ```sql
   ANALYZE marketing.form_5500;
   ANALYZE marketing.company_master;
   ```

3. [ ] **Check enrichment score improvement**
   ```sql
   SELECT
       AVG(enrichment_score) as avg_score,
       COUNT(*) FILTER (WHERE has_5500 = 1) as with_5500
   FROM marketing.v_company_enrichment_status;
   ```
   Expected: Average score increase by 10+ points

---

## 📊 Success Metrics

### Data Volume
- [ ] **Form 5500 records imported:** _________ (target: 700,000+)
- [ ] **Unique EINs:** _________ (target: 150,000+)
- [ ] **Target state records:** _________ (target: 80,000+)

### Matching Performance
- [ ] **Companies matched:** _________ (target: >50%)
- [ ] **Companies updated with EIN:** _________ (target: >1,000)
- [ ] **Avg enrichment score increase:** _________ (target: +10 points)

### Data Quality
- [ ] **Duplicate ACK_IDs:** 0 ✓
- [ ] **Invalid EINs:** 0 ✓
- [ ] **Processing errors:** _________ (target: <1%)

---

## 🚨 Troubleshooting Reference

### Import fails with "permission denied"
→ Use `\COPY` (client-side) instead of `COPY` (server-side)

### "Column count mismatch" error
→ Verify CSV columns match staging table columns exactly
→ Use explicit column list in COPY command

### Low match rate (<40%)
→ Review unmatched high-value records
→ Manually match top companies
→ Check sponsor_name variations (Inc vs Incorporated, etc.)

### Processing takes >30 minutes
→ Normal for 700K+ records
→ Monitor progress: `SELECT COUNT(*) FROM marketing.form_5500;`
→ Check for database connection issues

### "Transaction aborted" errors
→ Break import into smaller batches
→ Use ON CONFLICT DO NOTHING in insert statements
→ Check Neon connection limits

---

## 📝 Documentation

After successful import:

- [ ] **Update ENRICHMENT_SUMMARY.md** with actual metrics
- [ ] **Document any custom mappings** used
- [ ] **Note any data quality issues** encountered
- [ ] **Record processing time** for future reference
- [ ] **Update repo-data-diagrams/** if schema changed

---

## 🎯 Next Steps After Import

1. [ ] Set up annual refresh workflow (DOL releases yearly)
2. [ ] Create Grafana dashboard for Form 5500 metrics
3. [ ] Build BIT scoring model using participant trends
4. [ ] Manual match top 50 unmatched companies
5. [ ] Consider Schedule C import (service provider data)

---

**Status:** Ready to import ✅
**Estimated Time:** 2-25 minutes (depending on method)
**Risk Level:** Low (schema validated, procedures tested)
**Rollback Plan:** Restore from form_5500_backup table if needed
