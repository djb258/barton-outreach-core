# Database Schema Reference

Quick reference for all database tables and functions in Neon PostgreSQL.

## Connection

```bash
DATABASE_URL="postgresql://user:pass@host:5432/db?sslmode=require&channel_binding=require"
```

---

## Schemas

- `intake` - Raw data ingestion and staging
- `vault` - Promoted, validated contacts
- `company` - Company master data
- `people` - People master data
- `marketing` - Campaigns and outreach
- `bit` - Business Intelligence Tables
- `ple` - People Lead Enrichment

---

## Tables

### intake.raw_loads

Staging area for raw ingested data.

| Column | Type | Nullable | Description |
|--------|------|----------|-------------|
| `load_id` | bigserial | NO | Primary key |
| `batch_id` | text | NO | Batch identifier |
| `source` | text | NO | Data source (apollo, apify, manual) |
| `raw_data` | jsonb | NO | Raw JSON data payload |
| `status` | text | NO | Status (pending, promoted, failed, duplicate) |
| `created_at` | timestamptz | NO | Ingestion timestamp |
| `promoted_at` | timestamptz | YES | Promotion timestamp |
| `metadata` | jsonb | NO | Additional metadata |

**Indexes**:
- `idx_raw_loads_batch_id` on `batch_id`
- `idx_raw_loads_source` on `source`
- `idx_raw_loads_status` on `status`
- `idx_raw_loads_created_at` on `created_at DESC`
- `idx_raw_loads_raw_data_email` on `(raw_data->>'email')`

**Row Level Security**: Enabled
- Direct INSERT/UPDATE/DELETE blocked
- SELECT allowed for monitoring
- Use `intake.f_ingest_json()` function

---

### vault.contacts

Validated, promoted contacts.

| Column | Type | Nullable | Description |
|--------|------|----------|-------------|
| `contact_id` | bigserial | NO | Primary key |
| `email` | text | NO | Email (unique) |
| `name` | text | YES | Full name |
| `phone` | text | YES | Phone number |
| `company` | text | YES | Company name |
| `title` | text | YES | Job title |
| `source` | text | NO | Original source |
| `tags` | jsonb | NO | Tags array (default: []) |
| `custom_fields` | jsonb | NO | Custom fields object (default: {}) |
| `load_id` | bigint | YES | FK to intake.raw_loads |
| `created_at` | timestamptz | NO | Creation timestamp |
| `updated_at` | timestamptz | NO | Last update timestamp |
| `last_activity_at` | timestamptz | YES | Last activity timestamp |
| `score` | numeric(5,2) | NO | Lead score (0-100, default: 0) |
| `status` | text | NO | Status (active, inactive, bounced, unsubscribed) |

**Indexes**:
- `idx_contacts_email` on `email` (unique)
- `idx_contacts_source` on `source`
- `idx_contacts_created_at` on `created_at DESC`
- `idx_contacts_score` on `score DESC`
- `idx_contacts_status` on `status`
- `idx_contacts_company` on `company`

**Row Level Security**: Enabled
- Direct INSERT/UPDATE/DELETE blocked
- SELECT allowed for monitoring
- Use `vault.f_promote_contacts()` function

---

### intake.audit_log

Audit trail for all data operations.

| Column | Type | Nullable | Description |
|--------|------|----------|-------------|
| `log_id` | bigserial | NO | Primary key |
| `action` | text | NO | Action performed |
| `load_id` | bigint | YES | Related load_id |
| `contact_id` | bigint | YES | Related contact_id |
| `details` | jsonb | NO | Action details |
| `timestamp` | timestamptz | NO | Action timestamp |

**Common Actions**:
- `contact_ingested` - Contact added to raw_loads
- `contact_promoted` - Contact promoted to vault
- `contact_updated` - Contact fields updated
- `contact_deleted` - Contact marked as deleted
- `batch_processed` - Batch ingestion completed

---

### company.master

Company master data (golden records).

| Column | Type | Nullable | Description |
|--------|------|----------|-------------|
| `id` | uuid | NO | Primary key |
| `domain` | text | NO | Company domain (unique) |
| `name` | text | YES | Company name |
| `industry` | text | YES | Industry category |
| `employee_count` | integer | YES | Employee count |
| `revenue` | numeric | YES | Annual revenue |
| `location` | text | YES | HQ location |
| `linkedin_url` | text | YES | LinkedIn company page |
| `website` | text | YES | Company website |
| `created_at` | timestamptz | NO | Creation timestamp |
| `updated_at` | timestamptz | NO | Last update |
| `enriched_at` | timestamptz | YES | Last enrichment |
| `status` | text | NO | Status (active, inactive, archived) |

**Indexes**:
- `idx_company_domain` on `domain` (unique)
- `idx_company_name` on `name`
- `idx_company_industry` on `industry`

---

### company.slot

Staging area for company data before promotion.

| Column | Type | Nullable | Description |
|--------|------|----------|-------------|
| `id` | uuid | NO | Primary key |
| `domain` | text | NO | Company domain |
| `raw_data` | jsonb | NO | Raw company data |
| `validation_status` | text | NO | Status (pending, validated, rejected) |
| `created_at` | timestamptz | NO | Creation timestamp |
| `promoted_at` | timestamptz | YES | Promotion timestamp |

---

### company.history

Change tracking for company records.

| Column | Type | Nullable | Description |
|--------|------|----------|-------------|
| `history_id` | bigserial | NO | Primary key |
| `company_id` | uuid | NO | FK to company.master |
| `changed_fields` | jsonb | NO | Changed fields |
| `old_values` | jsonb | NO | Previous values |
| `new_values` | jsonb | NO | New values |
| `changed_by` | text | YES | User/system identifier |
| `changed_at` | timestamptz | NO | Change timestamp |

---

### people.master

People master data (golden records).

| Column | Type | Nullable | Description |
|--------|------|----------|-------------|
| `id` | uuid | NO | Primary key |
| `email` | text | NO | Email (unique) |
| `name` | text | YES | Full name |
| `first_name` | text | YES | First name |
| `last_name` | text | YES | Last name |
| `title` | text | YES | Job title |
| `company_id` | uuid | YES | FK to company.master |
| `linkedin_url` | text | YES | LinkedIn profile |
| `phone` | text | YES | Phone number |
| `location` | text | YES | Location |
| `seniority` | text | YES | Seniority level |
| `department` | text | YES | Department |
| `created_at` | timestamptz | NO | Creation timestamp |
| `updated_at` | timestamptz | NO | Last update |
| `enriched_at` | timestamptz | YES | Last enrichment |
| `status` | text | NO | Status (active, inactive, bounced) |

**Indexes**:
- `idx_people_email` on `email` (unique)
- `idx_people_company_id` on `company_id`
- `idx_people_linkedin_url` on `linkedin_url`

---

### people.slot

Staging area for people data before promotion.

| Column | Type | Nullable | Description |
|--------|------|----------|-------------|
| `id` | uuid | NO | Primary key |
| `email` | text | NO | Email |
| `raw_data` | jsonb | NO | Raw person data |
| `validation_status` | text | NO | Status (pending, validated, rejected) |
| `created_at` | timestamptz | NO | Creation timestamp |
| `promoted_at` | timestamptz | YES | Promotion timestamp |

---

### people.intelligence

LinkedIn enrichment data.

| Column | Type | Nullable | Description |
|--------|------|----------|-------------|
| `id` | uuid | NO | Primary key |
| `person_id` | uuid | NO | FK to people.master |
| `linkedin_data` | jsonb | NO | LinkedIn profile data |
| `skills` | text[] | YES | Skills array |
| `experience` | jsonb | YES | Work experience |
| `education` | jsonb | YES | Education history |
| `fetched_at` | timestamptz | NO | Data fetch timestamp |
| `stale_at` | timestamptz | NO | When data becomes stale (30 days) |

**TTL**: Data auto-expires after 30 days

---

### people.history

Change tracking for people records.

| Column | Type | Nullable | Description |
|--------|------|----------|-------------|
| `history_id` | bigserial | NO | Primary key |
| `person_id` | uuid | NO | FK to people.master |
| `changed_fields` | jsonb | NO | Changed fields |
| `old_values` | jsonb | NO | Previous values |
| `new_values` | jsonb | NO | New values |
| `changed_by` | text | YES | User/system identifier |
| `changed_at` | timestamptz | NO | Change timestamp |

---

### marketing.campaigns

Marketing campaign definitions.

| Column | Type | Nullable | Description |
|--------|------|----------|-------------|
| `campaign_id` | uuid | NO | Primary key |
| `name` | text | NO | Campaign name |
| `type` | text | NO | Type (cold_outreach, nurture, follow_up) |
| `status` | text | NO | Status (draft, active, paused, completed) |
| `target_count` | integer | YES | Target contact count |
| `sent_count` | integer | NO | Messages sent (default: 0) |
| `response_count` | integer | NO | Responses received (default: 0) |
| `created_at` | timestamptz | NO | Creation timestamp |
| `started_at` | timestamptz | YES | Campaign start |
| `ended_at` | timestamptz | YES | Campaign end |

---

### marketing.outreach_history

Contact history and campaign tracking.

| Column | Type | Nullable | Description |
|--------|------|----------|-------------|
| `id` | uuid | NO | Primary key |
| `person_id` | uuid | NO | FK to people.master |
| `campaign_id` | uuid | YES | FK to marketing.campaigns |
| `channel` | text | NO | Channel (email, linkedin, phone) |
| `message_type` | text | NO | Type (initial, follow_up, reply) |
| `sent_at` | timestamptz | NO | Send timestamp |
| `opened_at` | timestamptz | YES | Open timestamp |
| `replied_at` | timestamptz | YES | Reply timestamp |
| `status` | text | NO | Status (sent, opened, replied, bounced) |

---

### marketing.attribution

Conversion tracking and attribution.

| Column | Type | Nullable | Description |
|--------|------|----------|-------------|
| `id` | uuid | NO | Primary key |
| `person_id` | uuid | NO | FK to people.master |
| `campaign_id` | uuid | YES | FK to marketing.campaigns |
| `conversion_type` | text | NO | Type (meeting, demo, signup, sale) |
| `converted_at` | timestamptz | NO | Conversion timestamp |
| `value` | numeric | YES | Deal value |
| `source_touchpoint` | text | YES | First touch channel |
| `final_touchpoint` | text | YES | Last touch channel |

---

### marketing.feedback_reports

Campaign feedback and insights.

| Column | Type | Nullable | Description |
|--------|------|----------|-------------|
| `id` | uuid | NO | Primary key |
| `campaign_id` | uuid | NO | FK to marketing.campaigns |
| `report_date` | date | NO | Report date |
| `metrics` | jsonb | NO | Performance metrics |
| `insights` | text | YES | AI-generated insights |
| `created_at` | timestamptz | NO | Creation timestamp |

---

## Database Functions

### intake.f_ingest_json()

Ingest JSON data with duplicate detection.

```sql
SELECT * FROM intake.f_ingest_json(
  p_rows := ARRAY['{"email":"john@example.com","name":"John Doe"}'::jsonb],
  p_source := 'apollo',
  p_batch_id := 'batch-123'
);
```

**Parameters**:
- `p_rows` - Array of JSONB objects
- `p_source` - Data source identifier
- `p_batch_id` - Batch identifier

**Returns**:
- `load_id` - Load ID (or NULL for summary)
- `status` - Status (success/error)
- `message` - Result message

**Behavior**:
- Checks for duplicates in last 30 days
- Marks duplicates with status='duplicate'
- Validates email presence
- Returns summary of inserted/skipped

---

### vault.f_promote_contacts()

Promote contacts from intake to vault.

```sql
SELECT * FROM vault.f_promote_contacts(
  p_load_ids := ARRAY[123, 456, 789]
);
```

**Parameters**:
- `p_load_ids` - Array of load IDs (NULL = promote all pending)

**Returns**:
- `promoted_count` - New contacts created
- `updated_count` - Existing contacts updated
- `failed_count` - Failed promotions
- `message` - Result message

**Behavior**:
- Only processes pending loads
- Upserts based on email
- Updates `promoted_at` timestamp
- Logs to audit_log

---

## Common Queries

### Get all pending contacts
```sql
SELECT load_id, batch_id, raw_data->>'email' as email, created_at
FROM intake.raw_loads
WHERE status = 'pending'
ORDER BY created_at DESC
LIMIT 100;
```

### Get recent promotions
```sql
SELECT c.contact_id, c.email, c.name, c.created_at
FROM vault.contacts c
WHERE c.created_at > NOW() - INTERVAL '1 day'
ORDER BY c.created_at DESC;
```

### Find high-value leads
```sql
SELECT email, name, company, score, status
FROM vault.contacts
WHERE score >= 80
  AND status = 'active'
ORDER BY score DESC
LIMIT 50;
```

### Campaign performance
```sql
SELECT
  c.name,
  c.sent_count,
  c.response_count,
  ROUND(100.0 * c.response_count / NULLIF(c.sent_count, 0), 2) as response_rate
FROM marketing.campaigns c
WHERE c.status = 'active'
ORDER BY response_rate DESC;
```

---

## Migrations

Migrations are in `ctb/data/migrations/`.

### Run migrations
```bash
# Using psql
psql $DATABASE_URL -f ctb/data/migrations/2025-10-23_my_migration.sql

# Using Node.js script
node ctb/ai/scripts/run_migrations.js
```

### Create migration
```bash
cd ctb/data/migrations
cat > $(date +%Y-%m-%d)_description.sql << 'EOF'
-- CTB Metadata
-- Barton ID: 05.01.02
-- ...

BEGIN;
-- Your SQL here
COMMIT;
EOF
```

---

## Row Level Security

Tables have RLS enabled:
- `intake.raw_loads` - SELECT allowed, DML via functions only
- `vault.contacts` - SELECT allowed, DML via functions only

**Why**: Ensures data integrity and audit trail.

**Bypass** (for admin):
```sql
SET ROLE postgres;  -- or other superuser
-- Do admin operations
RESET ROLE;
```

---

## Indexes & Performance

### Key indexes for performance:
- Email lookups: `idx_contacts_email`, `idx_people_email`
- Time-based queries: `idx_raw_loads_created_at`, `idx_contacts_created_at`
- Filtering: `idx_contacts_status`, `idx_raw_loads_status`
- JSONB queries: `idx_raw_loads_raw_data_email`

### Query optimization:
```sql
-- Use indexes
EXPLAIN ANALYZE SELECT * FROM vault.contacts WHERE email = 'john@example.com';

-- Avoid full table scans
SELECT * FROM vault.contacts WHERE created_at > NOW() - INTERVAL '7 days';
```

---

**Last Updated**: 2025-10-23
**Schema Version**: 1.0
**Maintained By**: Data Engineering Team

For API usage, see: `ctb/sys/api/API.md`
For migrations, see: `ctb/data/migrations/`
