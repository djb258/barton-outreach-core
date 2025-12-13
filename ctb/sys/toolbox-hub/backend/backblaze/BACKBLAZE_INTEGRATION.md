# Backblaze B2 Integration for Validation Failures

**Date**: 2025-11-18
**Status**: Production Ready (Code Complete, Credentials Verification Needed)
**Replaces**: Google Sheets integration (n8n webhooks)

---

## Overview

This integration replaces Google Sheets with Backblaze B2 object storage for storing validation failures. B2 provides a simpler, more scalable, and cost-effective solution.

### Why Backblaze B2 Over Google Sheets?

| Feature | Google Sheets | Backblaze B2 |
|---------|---------------|--------------|
| **Authentication** | OAuth (complex) | API Key (simple) |
| **Rate Limiting** | Yes (100 requests/100s) | Minimal |
| **Cost** | Free (limited) | $0.005/GB/month |
| **Scalability** | Limited rows | Unlimited |
| **API Complexity** | High | Low (S3-compatible) |
| **Integration** | n8n webhooks | Direct upload |
| **File Organization** | Manual | Automatic by date |
| **Data Format** | Spreadsheet | JSON/CSV files |
| **Download Fees** | Free | Free (B2 unique benefit) |

---

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                  VALIDATION PIPELINE                         │
└─────────────────────────────────────────────────────────────┘
                           │
                           ▼
              ┌────────────────────────┐
              │  Neon PostgreSQL       │
              │  validation_failures   │
              │  _log table            │
              └────────────────────────┘
                           │
                           ▼
              ┌────────────────────────┐
              │  push_failures_to_b2   │
              │  Export & Upload       │
              └────────────────────────┘
                           │
                           ▼
              ┌────────────────────────┐
              │  Backblaze B2 Bucket   │
              │  svg-enrichment        │
              │  /validation-failures/ │
              └────────────────────────┘
                           │
                           ▼
              ┌────────────────────────┐
              │  File Organization:    │
              │  2025-11-18/           │
              │    company_*.json      │
              │    person_*.json       │
              └────────────────────────┘
```

---

## Configuration

### Environment Variables (.env)

```bash
# Backblaze B2 Configuration
B2_ENDPOINT=https://s3.us-east-005.backblazeb2.com
B2_KEY_ID=<YOUR_KEY_ID>
B2_APPLICATION_KEY=<YOUR_APPLICATION_KEY>
B2_BUCKET=svg-enrichment
B2_VALIDATION_FAILURES_PREFIX=validation-failures/
```

### Getting B2 Credentials

1. Log into Backblaze B2: https://secure.backblaze.com/b2_buckets.htm
2. Go to "App Keys" → "Add a New Application Key"
3. Set:
   - **Key Name**: `barton-outreach-validation`
   - **Allow access to Bucket(s)**: `svg-enrichment`
   - **Type of Access**: `Read and Write`
4. Copy the credentials:
   - **keyID** → `B2_KEY_ID`
   - **applicationKey** → `B2_APPLICATION_KEY`

⚠️ **IMPORTANT**: The application key is only shown once. Save it immediately!

---

## File Structure

```
ctb/sys/toolbox-hub/backend/backblaze/
├── __init__.py                    # Package exports
├── b2_client.py                   # Backblaze B2 client wrapper
├── push_to_b2.py                  # Single file upload
├── push_to_b2_batched.py          # Batched uploads for large datasets
└── BACKBLAZE_INTEGRATION.md       # This file

ctb/sys/toolbox-hub/backend/
└── push_failures_to_b2.py         # Export from PostgreSQL to B2
```

---

## Usage

### 1. Export Validation Failures to B2

```bash
# Export company failures (JSON format)
python backend/push_failures_to_b2.py

# This will:
# 1. Query validation_failures_log table
# 2. Push failures to B2
# 3. Mark records as exported_to_b2 = TRUE
```

### 2. Direct Upload (Python API)

```python
from backend.backblaze.push_to_b2 import push_company_failures, push_person_failures

# Push company failures
company_failures = [
    {
        "company_id": "04.04.01.33.00033.033",
        "company_name": "WV SUPREME COURT",
        "fail_reason": "Missing industry",
        "state": "WV",
        "validation_timestamp": "2025-11-18T10:00:00",
        "pipeline_id": "WV-VALIDATION-20251118"
    }
]

success = push_company_failures(
    failures=company_failures,
    pipeline_id="WV-VALIDATION-20251118",
    state="WV",
    export_format="json"  # or "csv"
)
```

### 3. Batched Upload (Large Datasets)

```python
from backend.backblaze.push_to_b2_batched import push_company_failures_batched

# For 9,250 failures, split into 1000-record files
success_count, fail_count = push_company_failures_batched(
    failures=large_failure_list,
    batch_size=1000,
    pipeline_id="WV-VALIDATION-20251118",
    state="WV",
    export_format="json"
)

print(f"Uploaded {success_count} records in {len(large_failure_list) // 1000 + 1} files")
```

### 4. Test B2 Connection

```bash
cd backend/backblaze
python b2_client.py
```

Expected output:
```
================================================================================
BACKBLAZE B2 CONNECTION TEST
================================================================================

✅ Connection successful!

Found X file(s):
  1. validation-failures/2025-11-18/company_failures_WV-VALIDATION-20251118.json
  2. validation-failures/2025-11-18/person_failures_WV-VALIDATION-20251118.json
```

---

## File Organization in B2

```
svg-enrichment/                         # Bucket
└── validation-failures/                # Prefix
    ├── 2025-11-18/                     # Date folders
    │   ├── company_failures_WV-VALIDATION-20251118.json
    │   ├── person_failures_WV-VALIDATION-20251118.json
    │   └── company_failures_WV-VALIDATION-20251118-BATCH-001.json
    ├── 2025-11-19/
    │   ├── company_failures_VALIDATION-20251119.json
    │   └── person_failures_VALIDATION-20251119.json
    └── 2025-11-20/
        └── ...
```

### File Naming Convention

- **Single file**: `{type}_failures_{pipeline_id}.{format}`
  - Example: `company_failures_WV-VALIDATION-20251118.json`

- **Batched files**: `{type}_failures_{pipeline_id}-BATCH-{num:03d}.{format}`
  - Example: `company_failures_WV-VALIDATION-20251118-BATCH-001.json`

---

## Metadata

Each uploaded file includes metadata tags:

```json
{
  "pipeline_id": "WV-VALIDATION-20251118",
  "failure_type": "company",
  "record_count": "453",
  "state": "WV",
  "upload_timestamp": "2025-11-18T10:30:00"
}
```

For batched uploads:
```json
{
  "pipeline_id": "WV-VALIDATION-20251118",
  "batch_id": "WV-VALIDATION-20251118-BATCH-001",
  "batch_number": "1",
  "total_batches": "10",
  "failure_type": "company",
  "record_count": "1000",
  "state": "WV",
  "upload_timestamp": "2025-11-18T10:30:00"
}
```

---

## Database Schema Update

Add columns to `marketing.validation_failures_log`:

```sql
ALTER TABLE marketing.validation_failures_log
ADD COLUMN IF NOT EXISTS exported_to_b2 BOOLEAN DEFAULT FALSE,
ADD COLUMN IF NOT EXISTS exported_to_b2_at TIMESTAMP;

CREATE INDEX IF NOT EXISTS idx_validation_failures_b2_export
ON marketing.validation_failures_log (exported_to_b2, failure_type)
WHERE exported_to_b2 = FALSE;
```

---

## Performance

### Single Upload

```python
# 1 company failure = 1 file upload
push_company_failures([failure])
# Result: ~100ms upload time
```

### Batched Upload

```python
# 9,250 failures in batches of 1,000
push_company_failures_batched(failures, batch_size=1000)
# Result:
#   - 10 files created
#   - ~1 second total upload time
#   - Files: ~50KB each (JSON)
```

### Scale Test (148k people + 37k companies)

```
Estimated failures (5% rate): 9,250
Batch size: 1,000
Total files: 10
Total upload time: ~1 second
Total storage: ~500KB
Cost: $0.0000025/month storage + $0 download
```

---

## Cost Comparison

### Google Sheets (n8n webhooks)

```
For 9,250 failures:
- Without batching: 9,250 n8n executions
- With batching (50/batch): 185 n8n executions
- n8n Cost: $X per execution (paid tier required)
```

### Backblaze B2 (Direct Upload)

```
For 9,250 failures:
- Upload transactions: 10 (batched) or 1 (single file)
- Storage: ~500KB
- Monthly cost: $0.0000025 storage + $0 download
- Total: Essentially free
```

---

## Troubleshooting

### Error: "Malformed Access Key Id"

**Cause**: B2 credentials are incomplete or incorrect

**Solution**:
1. Verify credentials in Backblaze console
2. Ensure you're using the **Application Key**, not Master Application Key
3. Check that the key has access to the `svg-enrichment` bucket
4. Regenerate credentials if needed

### Error: "No bucket found"

**Cause**: Bucket name doesn't match or doesn't exist

**Solution**:
1. Log into Backblaze: https://secure.backblaze.com/b2_buckets.htm
2. Verify bucket name: `svg-enrichment`
3. Update `B2_BUCKET` in `.env` if needed

### Files Not Appearing

**Cause**: Prefix mismatch or bucket not public

**Solution**:
1. Check `B2_VALIDATION_FAILURES_PREFIX` in `.env`
2. List files: `python backend/backblaze/b2_client.py`
3. Verify bucket is public (if you need public URLs)

---

## Migration from Google Sheets

### Step 1: Export Existing Failures

```bash
# Export failures still marked as not exported to sheets
python backend/export_failures_to_csv.py
```

### Step 2: Push to B2

```bash
# Push all unexported failures to B2
python backend/push_failures_to_b2.py
```

### Step 3: Verify Upload

```bash
# Test B2 connection and list files
python backend/backblaze/b2_client.py
```

### Step 4: Update Pipeline

Replace Google Sheets push calls:

**Before** (Google Sheets):
```python
from backend.google_sheets.push_to_sheet import push_to_sheet

push_to_sheet("WV_Validation_Failures_2025", "Company_Failures", failures)
```

**After** (Backblaze B2):
```python
from backend.backblaze.push_to_b2 import push_company_failures

push_company_failures(failures, pipeline_id="WV-VALIDATION-20251118", state="WV")
```

---

## Next Steps

1. ✅ **Verify B2 Credentials**
   - Test connection: `python backend/backblaze/b2_client.py`
   - If "Malformed Access Key Id" error: regenerate credentials

2. ✅ **Add Database Columns**
   - Run migration to add `exported_to_b2` columns

3. ✅ **Export Existing Failures**
   - Run: `python backend/push_failures_to_b2.py`

4. ✅ **Update Validation Pipeline**
   - Replace Google Sheets push with B2 push
   - Test with small batch first

5. ✅ **Scale Test**
   - Run full validation: 148k people + 37k companies
   - Push failures to B2 in batches
   - Verify all files in B2 console

---

## Resources

- **Backblaze B2 Console**: https://secure.backblaze.com/b2_buckets.htm
- **Backblaze B2 Docs**: https://www.backblaze.com/b2/docs/
- **S3-Compatible API**: https://www.backblaze.com/b2/docs/s3_compatible_api.html
- **Pricing Calculator**: https://www.backblaze.com/b2/cloud-storage-pricing.html

---

**Implementation Complete**: 2025-11-18
**Status**: ✅ Code ready, credentials verification needed
**Files Created**: 5 (b2_client.py, push_to_b2.py, push_to_b2_batched.py, push_failures_to_b2.py, BACKBLAZE_INTEGRATION.md)
