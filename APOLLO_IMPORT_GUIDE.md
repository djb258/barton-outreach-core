# Apollo to Neon Import Guide

Complete guide for importing Apollo company data into Neon Marketing DB.

## 📋 Prerequisites

1. Apollo CSV export file (e.g., `apollo-accounts-export.csv`)
2. Python 3.7+ with pandas installed
3. NEON_DATABASE_URL environment variable set

## 🚀 Quick Start

### Step 1: Install Dependencies

```bash
pip install pandas psycopg2-binary
```

### Step 2: Place Your Apollo CSV

Put your Apollo export file in the `barton-outreach-core` directory:
- `apollo-accounts-export.csv`

### Step 3: Run the Import Script

```bash
# Set environment variable (Windows PowerShell)
$env:NEON_DATABASE_URL="postgresql://Marketing%20DB_owner:npg_OsE4Z2oPCpiT@ep-ancient-waterfall-a42vy0du-pooler.us-east-1.aws.neon.tech/Marketing%20DB?channel_binding=require&sslmode=require"

# Run import
python import_apollo_to_neon.py apollo-accounts-export.csv
```

### Step 4: Confirm Import

When prompted, type `YES` to proceed with database import.

## 📊 What the Script Does

### 1. **CSV Transformation**
   - Maps Apollo column names to Neon schema
   - Adds required fields (batch_id, validation flags)
   - Cleans and validates data
   - Saves cleaned CSV

### 2. **Column Mapping**

| Apollo Column | Neon Column | Type | Required |
|--------------|-------------|------|----------|
| Company Name | company | text | ✅ YES |
| Company Name for Emails | company_name_for_emails | text | No |
| # Employees | num_employees | integer | No |
| Industry | industry | text | No |
| Website | website | text | No |
| Company Linkedin Url | company_linkedin_url | text | No |
| Facebook Url | facebook_url | text | No |
| Twitter Url | twitter_url | text | No |
| Company Street | company_street | text | No |
| Company City | company_city | text | No |
| Company State | company_state | text | No |
| Company Postal Code | company_postal_code | text | No |
| Company Address | company_address | text | No |
| Company Phone | company_phone | text | No |
| SIC Codes | sic_codes | text | No |
| Founded Year | founded_year | integer | No |
| Company Country | company_country | text | No |

### 3. **Auto-Generated Fields**

- `state_abbrev` - Extracted from company_state
- `import_batch_id` - Unique identifier (e.g., `apollo_upload_20251103_143025`)
- `validated` - Set to `false`
- `validation_notes` - Set to `null`
- `validated_at` - Set to `null`
- `validated_by` - Set to `null`
- `created_at` - Auto-set by database

### 4. **Database Import**
   - Bulk inserts into `intake.company_raw_intake`
   - Transaction safety (all or nothing)
   - Verification and sample display

## 📁 Output Files

The script creates:
1. `cleaned_apollo_company_raw_intake.csv` - Cleaned data matching Neon schema

## 🔍 After Import

Check your import:

```bash
# Run the column checker
python get_table_columns.py intake company_raw_intake

# Check row count
python check_all_neon_schemas.py
```

Query in database:

```sql
-- Count companies in your batch
SELECT 
    import_batch_id,
    COUNT(*) as company_count
FROM intake.company_raw_intake
GROUP BY import_batch_id
ORDER BY MAX(created_at) DESC;

-- View sample companies
SELECT 
    company,
    website,
    company_city,
    company_state,
    num_employees,
    industry
FROM intake.company_raw_intake
WHERE import_batch_id = 'apollo_upload_20251103_143025'
LIMIT 10;
```

## 🎯 Next Steps After Import

1. **Validate Companies**
   ```sql
   UPDATE intake.company_raw_intake
   SET validated = true,
       validated_at = NOW(),
       validated_by = 'manual_review'
   WHERE import_batch_id = 'YOUR_BATCH_ID'
     AND company IS NOT NULL;
   ```

2. **Promote to Marketing Schema**
   - Companies move from `intake.company_raw_intake` → `marketing.company_master`
   - Use promotion script (to be created)

3. **Generate Company Slots**
   - Create CEO/CFO/HR slots in `marketing.company_slots`
   - Link to companies via `company_unique_id`

4. **Begin Enrichment**
   - Enrich contacts via LinkedIn
   - Validate emails
   - Promote to `marketing.people_master`

## 🛠️ Troubleshooting

### Error: "NEON_DATABASE_URL not set"
```bash
# Set the environment variable
$env:NEON_DATABASE_URL="postgresql://..."
```

### Error: "File not found: apollo-accounts-export.csv"
- Make sure CSV is in the same directory as the script
- Or provide full path: `python import_apollo_to_neon.py "C:\path\to\file.csv"`

### Error: "Module 'pandas' not found"
```bash
pip install pandas psycopg2-binary
```

### Duplicate Companies
- The script doesn't check for duplicates by default
- Clear table first if re-importing: `python clear_and_reset_database.py`

## 📋 Sample Apollo CSV Format

Your CSV should have these columns (any subset works):

```csv
Company Name,Website,# Employees,Industry,Company City,Company State
Acme Corp,acme.com,150,Software,San Francisco,CA
TechStart Inc,techstart.io,25,Technology,Austin,TX
```

## 🔐 Security Notes

- Never commit CSV files with real company data to Git
- Keep database credentials in environment variables only
- Use `.gitignore` to exclude CSV files

## ✅ Success Indicators

You'll see:
```
IMPORT COMPLETE!
=============================
  Batch ID: apollo_upload_20251103_143025
  Companies imported: 708
  Status: SUCCESS
=============================
```

---

**Created:** 2025-11-03  
**Script:** `import_apollo_to_neon.py`  
**Database:** Neon Marketing DB  
**Schema:** `intake.company_raw_intake`

