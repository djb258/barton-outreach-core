# Company Validation Pipeline - Usage Guide

**Script**: `validate_and_promote_companies.py v2.0`
**Updated**: 2025-11-18

---

## Quick Start

### 1. Validate Only (Dry Run)

Check what would happen without making changes:

```bash
cd outreach_core/workbench
python validate_and_promote_companies.py --validate-only
```

**Output**:
- Shows which companies would pass/fail
- Does NOT promote to master
- Does NOT delete from intake
- Does NOT upload to B2
- Exit code 0 (always)

---

### 2. Validate & Promote (Full Pipeline)

Run the complete workflow:

```bash
python validate_and_promote_companies.py --validate-and-promote
```

**What happens**:
- ✅ Valid companies → Promoted to `marketing.company_master` + deleted from intake
- ❌ Invalid companies → Uploaded to B2 (grouped by state) + kept in intake
- 📊 Logs created in `garage_runs` and `agent_routing_log`
- Exit code 0 if intake is empty, 1 if records remain

---

### 3. Production Mode (with DNS Checks)

Enable live DNS/HTTP validation:

```bash
python validate_and_promote_companies.py --validate-and-promote --check-dns
```

**Additional checks**:
- DNS resolution (`socket.gethostbyname()`)
- HTTP HEAD request to domain
- Failures → Bay B (contradiction)

**Warning**: This is slower due to network calls. Use in production only.

---

## CLI Flags

| Flag | Description | Default |
|------|-------------|---------|
| `--validate-only` | Only validate, don't promote or delete | No |
| `--validate-and-promote` | Full pipeline (promote valid, route invalid to B2) | **Yes** (if no flags) |
| `--check-dns` | Enable live DNS/HTTP checks (prod mode) | No |

---

## Exit Codes

| Code | Meaning | Action |
|------|---------|--------|
| `0` | Success - Intake is empty | All records processed ✅ |
| `1` | Incomplete - Records remain in intake | Re-run after enrichment |

---

## Output Example

```
================================================================================
COMPANY INTAKE VALIDATION & PROMOTION PIPELINE v2.0
================================================================================

Mode: VALIDATE & PROMOTE
DNS Validation: FORMAT VALIDATION ONLY
Snapshot Version: 20251118133500
B2 Bucket: svg-enrichment

STEP 1: Connecting to Neon PostgreSQL
--------------------------------------------------------------------------------
[OK] Connected to Neon PostgreSQL

[OK] Created garage_run ID: 42

STEP 2: Pulling ALL Companies from intake.company_raw_intake
--------------------------------------------------------------------------------
[OK] Pulled 453 companies from intake

STEP 3: Validating Companies (Barton Doctrine)
--------------------------------------------------------------------------------

  [1/453] PROMOTED: Acme Corp -> 04.04.01.01.00001.001
  [2/453] FAILED (bay_a, attempt 1): TechCo Inc
  [3/453] FAILED (bay_b, attempt 1): XYZ University
  [4/453] PROMOTED: Widget Factory -> 04.04.01.02.00002.002
  ...

[OK] Validation Complete

STEP 4: Uploading Failed Companies to B2 (Grouped by State)
--------------------------------------------------------------------------------
  [B2] Uploaded 15 companies to companies_bad/WV/2025-11-18/bay_a.json
  [B2] Uploaded 8 companies to companies_bad/WV/2025-11-18/bay_b.json
  [B2] Uploaded 12 companies to companies_bad/CA/2025-11-18/bay_a.json
[OK] Uploaded 3 B2 files

STEP 5: Deleting Promoted Companies from Intake
--------------------------------------------------------------------------------
[OK] Deleted 324 promoted companies from intake

================================================================================
COMPANY VALIDATION & PROMOTION SUMMARY
================================================================================

Snapshot Version: 20251118133500
Mode: VALIDATE & PROMOTE

PROCESSING RESULTS:
  Total Companies Scanned: 453
  Promoted to Master: 324 (71.5%)
  Failed - Bay A (missing): 114 (25.2%)
  Failed - Bay B (contradictions): 15 (3.3%)
  Chronic Bad (2+ attempts): 0

DATABASE OPERATIONS:
  Deleted from intake: 324 records
  Remaining in intake: 129 records

GARAGE 2.0 LOGGING:
  Garage Run ID: 42
  Agent routing logs: 129 records

B2 STORAGE:
  Uploaded files: 3 (grouped by state)
  B2 Bucket: svg-enrichment

NEXT STEPS:
  1. 129 companies remain in intake (awaiting enrichment)
  2. Run Garage 2.0 enrichment agents:
     python enrichment_garage_2_0.py --snapshot 20251118133500
  3. After enrichment, re-run this validation pipeline

================================================================================
[INCOMPLETE] PIPELINE COMPLETE - RECORDS REMAIN IN INTAKE
================================================================================
```

Exit code: `1` (records remain)

---

## B2 File Structure

Failed companies are uploaded grouped by **state** and **bay**:

```
companies_bad/
├── WV/
│   └── 2025-11-18/
│       ├── bay_a.json  (15 companies with missing fields)
│       └── bay_b.json  (8 companies with contradictions)
├── CA/
│   └── 2025-11-18/
│       ├── bay_a.json  (12 companies)
│       └── bay_b.json  (3 companies)
└── UNKNOWN/
    └── 2025-11-18/
        └── bay_a.json  (Companies with no state)
```

**File Contents**:
```json
{
  "snapshot_version": "20251118133500",
  "state": "WV",
  "bay": "bay_a",
  "total_companies": 15,
  "validated_at": "2025-11-18T13:35:00",
  "validated_by": "validate_and_promote_companies.py v2.0",
  "companies": [
    {
      "id": 13,
      "company": "Example Corp",
      "website": null,
      "validation_errors": ["domain_missing", "industry_missing"],
      ...
    },
    ...
  ]
}
```

---

## Database Logging

### garage_runs

Tracks each validation run:

```sql
SELECT * FROM public.garage_runs ORDER BY run_started_at DESC LIMIT 5;
```

| run_id | snapshot_version | total_records_processed | bay_a_count | bay_b_count | run_status |
|--------|-----------------|-------------------------|-------------|-------------|------------|
| 42 | 20251118133500 | 453 | 114 | 15 | completed |
| 41 | 20251118120000 | 453 | 120 | 18 | completed |

### agent_routing_log

Tracks agent assignments for failed records:

```sql
SELECT * FROM public.agent_routing_log
WHERE garage_run_id = 42
ORDER BY routed_at DESC
LIMIT 10;
```

| record_id | garage_bay | agent_name | routing_reason | status |
|-----------|------------|------------|----------------|--------|
| 13 | bay_a | firecrawl | domain_missing, industry_missing | pending |
| 17 | bay_b | abacus | domain_edu_but_industry_Software | pending |

---

## Validation Rules Applied

See `outreach_core/validation/company_validator.py` for complete rules.

### Required Fields

- `company_name` (not null, not placeholder)
- `domain` (valid format with TLD)
- `linkedin_url` (contains `/company/`)
- `employee_count` (numeric or range like "11-50")
- `industry` (≥3 characters)
- `location` (city/state minimum)
- `apollo_id` (optional, warning only)

### Bay A (Missing Parts)

- Missing required fields
- Invalid format (bad domain, bad LinkedIn URL)
- Placeholder values ("N/A", "TBD", etc.)

**Agent**: Firecrawl or Apify ($0.05-0.10/record)

### Bay B (Contradictions)

- `.edu` domain but industry ≠ Education
- `.org` domain but industry ≠ Nonprofit
- `.gov` domain but industry ≠ Government
- Employee count < 10 but corporate domain (raytheon.com)
- Company name contains "School"/"Church" but wrong industry

**Agent**: Abacus or Claude ($0.50-1.00/record)

### Chronic Bad

After **2 failed enrichment attempts**, record is marked `chronic_bad = TRUE`.

---

## Workflow Example

### Initial Run (Fresh Data)

```bash
python validate_and_promote_companies.py --validate-and-promote
```

**Result**: 324 promoted, 129 failed (in B2 for enrichment)
**Exit code**: 1 (incomplete)

### After Agent Enrichment

Agents have updated records in `intake.company_raw_intake`.

Re-run validation:

```bash
python validate_and_promote_companies.py --validate-and-promote
```

**Result**: 100 more promoted, 29 still failing (chronic_bad)
**Exit code**: 1 (incomplete)

### Third Run (Manual Review)

After manual fixes to chronic_bad records:

```bash
python validate_and_promote_companies.py --validate-and-promote
```

**Result**: All 29 promoted
**Exit code**: 0 (intake empty!) ✅

---

## Monitoring Queries

### Check Intake Status

```sql
-- Overall status
SELECT
    COUNT(*) as total,
    COUNT(*) FILTER (WHERE validated = TRUE) as validated,
    COUNT(*) FILTER (WHERE validated = FALSE) as failed,
    COUNT(*) FILTER (WHERE chronic_bad = TRUE) as chronic
FROM intake.company_raw_intake;
```

### Failure Breakdown

```sql
-- Top failure reasons
SELECT
    UNNEST(string_to_array(validation_reasons, ',')) as reason,
    COUNT(*) as count
FROM intake.company_raw_intake
WHERE validated = FALSE
GROUP BY reason
ORDER BY count DESC;
```

### Bay Distribution

```sql
-- Companies by bay
SELECT
    garage_bay,
    enrichment_attempt,
    COUNT(*) as count
FROM intake.company_raw_intake
WHERE validated = FALSE
GROUP BY garage_bay, enrichment_attempt
ORDER BY garage_bay, enrichment_attempt;
```

---

## Troubleshooting

### Issue: No companies promoted

**Cause**: All companies failing validation
**Solution**: Run `--validate-only` to see failure reasons

```bash
python validate_and_promote_companies.py --validate-only
```

### Issue: B2 upload fails

**Cause**: Network issues or invalid credentials
**Solution**: Check `.env` file for correct B2 credentials

```bash
grep B2 .env
```

### Issue: Exit code 1 even after multiple runs

**Cause**: Chronic bad records (failed 2+ times)
**Solution**: Query chronic_bad records for manual review

```sql
SELECT * FROM intake.company_raw_intake WHERE chronic_bad = TRUE;
```

---

## Next Steps

1. **Review this guide**: Understand the workflow
2. **Run validate-only**: See current state without changes
3. **Run full pipeline**: Process all companies
4. **Check B2 uploads**: Verify failed companies in Backblaze
5. **Run agents**: Use Garage 2.0 to enrich failed records
6. **Re-run pipeline**: Validate enriched records
7. **Monitor**: Track success rates and chronic failures

---

**Questions?** See `VALIDATION_PIPELINE_COMPLETE.md` for full documentation.
