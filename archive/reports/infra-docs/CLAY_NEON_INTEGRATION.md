# Clay.com + Neon PostgreSQL Integration Guide

**Date:** 2025-11-27
**Status:** Ready for Configuration

---

## Overview

Clay.com has native PostgreSQL integration that connects directly to Neon, eliminating the need for middleware like n8n. This guide shows how to configure Clay to:

1. **READ** from `marketing.company_master` and `marketing.people_master`
2. **WRITE** enriched data to `intake.company_raw_from_clay` and `intake.people_raw_from_clay`

---

## Architecture

```
┌─────────────────┐       ┌─────────────────┐       ┌─────────────────┐
│   Clay.com      │──────▶│  Neon PostgreSQL │──────▶│  PLE Pipeline   │
│  (Enrichment)   │       │   (Database)     │       │  (Promotion)    │
└─────────────────┘       └─────────────────┘       └─────────────────┘
        │                         │
        │  SELECT from views      │
        │  INSERT to intake       │
        │                         │
        ▼                         ▼
  v_companies_for_clay     company_raw_from_clay
  v_people_for_clay        people_raw_from_clay
```

---

## Neon Connection Details (For Clay)

**Copy these into Clay's PostgreSQL integration:**

```
Host:     ep-ancient-waterfall-a42vy0du-pooler.us-east-1.aws.neon.tech
Port:     5432
Database: Marketing DB
User:     Marketing DB_owner
Password: npg_OsE4Z2oPCpiT
SSL:      require
```

**Full Connection String:**
```
postgresql://Marketing%20DB_owner:npg_OsE4Z2oPCpiT@ep-ancient-waterfall-a42vy0du-pooler.us-east-1.aws.neon.tech:5432/Marketing%20DB?sslmode=require
```

---

## Database Objects Created

### Tables (for Clay to WRITE to)

#### `intake.company_raw_from_clay`
Receives enriched company data from Clay.

**Key Columns:**
- `company_unique_id` - Reference to source company
- `company_name` - Original company name
- `website_original` - Original website (if any)
- `website_enriched` - Enriched website from Clay
- `employee_count_enriched` - Enriched employee count
- `industry_enriched` - Enriched industry
- `linkedin_company_url` - Company LinkedIn URL
- `clay_enriched_at` - When Clay enriched the record
- `clay_credits_used` - Credits consumed
- `enrichment_status` - received | processing | promoted | failed | duplicate

#### `intake.people_raw_from_clay`
Receives enriched people/contact data from Clay.

**Key Columns:**
- `person_unique_id` - Reference to existing person (may be NULL for new discoveries)
- `company_unique_id` - Reference to company
- `slot_type` - CEO | CFO | HR (if from company_slot)
- `work_email` - Enriched work email
- `work_email_verified` - Email verification status
- `linkedin_url_enriched` - Enriched LinkedIn URL
- `phone_direct` - Direct phone number
- `clay_enriched_at` - When Clay enriched the record
- `clay_credits_used` - Credits consumed

### Views (for Clay to READ from)

#### `intake.v_companies_for_clay`
Returns companies that need enrichment (not enriched in last 30 days).

**Use this in Clay table as source.**

**Columns provided:**
- `company_unique_id` - PK for reference
- `company_name`
- `website_url`
- `address_city`
- `address_state`
- `employee_count`
- `industry`
- `company_linkedin`
- `created_at`
- `updated_at`

**Current count:** ~453 companies

#### `intake.v_people_for_clay`
Returns people that need enrichment.

**Columns provided:**
- `person_unique_id` - PK for reference
- `company_unique_id` - FK to company
- `slot_type` - CEO | CFO | HR
- `full_name`
- `title`
- `linkedin_url`
- `email`
- `created_at`
- `updated_at`

**Current count:** ~1,300+ people

#### `intake.v_clay_enrichment_stats`
Monitoring view for enrichment pipeline health.

**Columns:**
- `table_type` - 'companies' or 'people'
- `total_records` - Total enriched
- `pending` - Awaiting promotion
- `promoted` - Promoted to master
- `failed` - Failed enrichment
- `total_credits_used` - Total Clay credits
- `last_enrichment` - Most recent enrichment timestamp

---

## Clay Configuration Steps

### Step 1: Add PostgreSQL Integration in Clay

1. Go to Clay → Settings → Integrations
2. Click "Add Integration" → PostgreSQL
3. Enter the Neon connection details (above)
4. Test connection
5. Save

### Step 2: Create Company Enrichment Table

1. Create new table in Clay
2. Click "Import from Database"
3. Select your Neon connection
4. Enter query: `SELECT * FROM intake.v_companies_for_clay`
5. Clay will import the 453+ companies
6. Add enrichment columns/workflows

### Step 3: Configure Company Enrichment Output

After enrichment, export back to Neon:

1. Add "Write to PostgreSQL" action
2. Target table: `intake.company_raw_from_clay`
3. Map columns:
   - `company_unique_id` → source.company_unique_id
   - `company_name` → source.company_name
   - `website_original` → source.website_url
   - `website_enriched` → enriched.website
   - `employee_count_enriched` → enriched.employee_count
   - `industry_enriched` → enriched.industry
   - `linkedin_company_url` → enriched.linkedin_url
   - `clay_enriched_at` → NOW()
   - `clay_credits_used` → clay.credits_used

### Step 4: Create People Enrichment Table

Repeat steps 2-3 for people:

- Source query: `SELECT * FROM intake.v_people_for_clay`
- Target table: `intake.people_raw_from_clay`
- Map columns appropriately

---

## Enrichment Provider Recommendations

Based on PLE requirements:

### For Companies
1. **Clearbit Company** - Industry, employee count, revenue
2. **Apollo Company** - LinkedIn URL, tech stack
3. **PeopleDataLabs Company** - Funding info

### For People (CEO/CFO/HR)
1. **Apollo People** - Work email, phone
2. **Hunter.io** - Email verification
3. **Clearbit Person** - Title standardization
4. **ContactOut** - Personal email (backup)

### Waterfall Order
```
1. Apollo (cheapest, decent coverage)
2. Clearbit (expensive, high quality)
3. PeopleDataLabs (good for bulk)
4. Hunter.io (email verification only)
5. ContactOut (last resort for contacts)
```

---

## Monitoring Queries

### Check enrichment pipeline health
```sql
SELECT * FROM intake.v_clay_enrichment_stats;
```

### See recent enrichments
```sql
SELECT company_name, website_enriched, clay_enriched_at, enrichment_status
FROM intake.company_raw_from_clay
ORDER BY created_at DESC
LIMIT 20;
```

### Find pending records for promotion
```sql
-- Companies ready to promote
SELECT COUNT(*)
FROM intake.company_raw_from_clay
WHERE enrichment_status = 'received';

-- People ready to promote
SELECT COUNT(*)
FROM intake.people_raw_from_clay
WHERE enrichment_status = 'received';
```

### Credit tracking
```sql
SELECT
    DATE(clay_enriched_at) as date,
    SUM(clay_credits_used) as credits_used,
    COUNT(*) as records_enriched
FROM intake.company_raw_from_clay
WHERE clay_enriched_at IS NOT NULL
GROUP BY DATE(clay_enriched_at)
ORDER BY date DESC;
```

---

## Promotion Pipeline (Future)

After Clay writes to intake tables, a promotion job will:

1. Validate enriched data
2. Merge with existing `company_master` / `people_master`
3. Update `enrichment_status` to 'promoted'
4. Log to `marketing.data_enrichment_log`

**This can be triggered via:**
- n8n workflow (webhook)
- Cron job
- Manual script

---

## Migration File

The tables/views were created by:
```
infra/migrations/002_create_clay_intake_tables.sql
```

To re-run migration:
```bash
psql "$DATABASE_URL" -f infra/migrations/002_create_clay_intake_tables.sql
```

---

## Related Files

- `infra/migrations/002_create_clay_intake_tables.sql` - Migration SQL
- `.env` - Database connection credentials
- `ctb/sys/enrichment/` - Enrichment waterfall code
- `repo-data-diagrams/` - Schema documentation

---

## Cost Optimization Tips

1. **Use views to limit enrichment** - Only enriches records not touched in 30 days
2. **Track credits** - `clay_credits_used` column enables ROI analysis
3. **Batch enrichments** - Run daily/weekly rather than real-time
4. **Skip if data exists** - Check if website_url already present before enriching

---

## Troubleshooting

### "Permission denied" in Clay
- Verify `Marketing DB_owner` user has INSERT on `intake` schema
- Run: `GRANT ALL ON SCHEMA intake TO "Marketing DB_owner";`

### "Connection refused"
- Check if Neon project is active (auto-suspends after inactivity)
- Use pooler URL (contains `-pooler` in hostname)
- Verify SSL mode is `require`

### "Column not found"
- Ensure migration was run successfully
- Check column names (Clay is case-sensitive)

---

**Last Updated:** 2025-11-27
**Status:** Tables created, ready for Clay configuration
**Companies Available:** 453
**People Available:** 1,300+
