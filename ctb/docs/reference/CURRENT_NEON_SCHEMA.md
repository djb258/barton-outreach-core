# Neon Database Schema - Current State

**Database**: Neon PostgreSQL
**Generated**: 2025-11-06
**Total Migration Files**: 29
**Primary Schema**: `marketing`

---

## 📊 Schema Overview

The Barton Outreach Core database consists of multiple schemas with the **marketing** schema being the primary operational schema for production data.

### Schema Hierarchy

```
Neon Database
├── marketing (Primary - Production data)
│   ├── company_master
│   ├── people_master
│   ├── company_slot
│   ├── company_intelligence
│   ├── people_intelligence
│   ├── pipeline_events
│   └── outreach_history
├── company (Legacy - Deprecated)
│   ├── company
│   └── company_slot
├── people (Legacy - Deprecated)
│   ├── contact
│   └── contact_verification
├── intake (Data ingestion)
│   ├── raw_loads
│   └── audit_log
├── vault (Promoted contacts)
│   └── contacts
├── bit (Buyer Intent Tool)
│   └── signal
└── public (Utilities)
    ├── shq_error_log
    ├── linkedin_refresh_jobs
    └── actor_usage_log
```

---

## 🏢 MARKETING Schema (Primary)

### 1. marketing.company_master

**Purpose**: Master table for validated and promoted company records

**Barton ID Format**: `04.04.01.XX.XXXXX.XXX`

#### Columns

| Column | Type | Nullable | Description |
|--------|------|----------|-------------|
| `company_unique_id` | TEXT | PRIMARY KEY | Barton ID (immutable) |
| `company_name` | TEXT | NOT NULL | Company name |
| `website_url` | TEXT | NOT NULL | Company website |
| `industry` | TEXT | NULL | Industry classification |
| `employee_count` | INTEGER | NULL | Number of employees (≥ 0) |
| `company_phone` | TEXT | NULL | Company phone number |
| `address_street` | TEXT | NULL | Street address |
| `address_city` | TEXT | NULL | City |
| `address_state` | TEXT | NULL | State/region |
| `address_zip` | TEXT | NULL | ZIP/postal code |
| `address_country` | TEXT | NULL | Country |
| `linkedin_url` | TEXT | NULL | LinkedIn company page |
| `facebook_url` | TEXT | NULL | Facebook page |
| `twitter_url` | TEXT | NULL | Twitter/X handle |
| `sic_codes` | TEXT | NULL | SIC codes |
| `founded_year` | INTEGER | NULL | Year founded (1700-current) |
| `keywords` | TEXT[] | NULL | Industry keywords array |
| `description` | TEXT | NULL | Company description |
| `source_system` | TEXT | NOT NULL | Source system identifier |
| `source_record_id` | TEXT | NULL | Source record ID |
| `promoted_from_intake_at` | TIMESTAMPTZ | NOT NULL | Promotion timestamp |
| `promotion_audit_log_id` | INTEGER | NULL | Audit log reference |
| `created_at` | TIMESTAMPTZ | DEFAULT NOW() | Record creation |
| `updated_at` | TIMESTAMPTZ | DEFAULT NOW() | Last update (auto-updated) |

#### Indexes
- `idx_company_master_company_name` ON (company_name)
- `idx_company_master_industry` ON (industry)
- `idx_company_master_source_system` ON (source_system)
- `idx_company_master_promoted_at` ON (promoted_from_intake_at)

#### Triggers
- `trigger_company_master_updated_at` - Auto-updates `updated_at` on UPDATE

#### Constraints
- Barton ID format validation
- Employee count must be ≥ 0 if not NULL
- Founded year between 1700 and current year

---

### 2. marketing.people_master

**Purpose**: Master table for validated and promoted people records

**Barton ID Format**: `04.04.02.XX.XXXXX.XXX`

#### Columns

| Column | Type | Nullable | Description |
|--------|------|----------|-------------|
| `unique_id` | TEXT | PRIMARY KEY | Barton ID (immutable) |
| `company_unique_id` | TEXT | NOT NULL | Reference to company (04.04.01) |
| `company_slot_unique_id` | TEXT | NOT NULL | Reference to slot (04.04.05) |
| `first_name` | TEXT | NOT NULL | First name |
| `last_name` | TEXT | NOT NULL | Last name |
| `full_name` | TEXT | GENERATED | Computed: first + last name |
| `title` | TEXT | NULL | Job title |
| `seniority` | TEXT | NULL | Seniority level |
| `department` | TEXT | NULL | Department |
| `email` | TEXT | NULL | Email address (validated format) |
| `work_phone_e164` | TEXT | NULL | Work phone (E.164 format) |
| `personal_phone_e164` | TEXT | NULL | Personal phone (E.164 format) |
| `linkedin_url` | TEXT | NULL | LinkedIn profile |
| `twitter_url` | TEXT | NULL | Twitter/X profile |
| `facebook_url` | TEXT | NULL | Facebook profile |
| `bio` | TEXT | NULL | Professional bio |
| `skills` | TEXT[] | NULL | Skills array |
| `education` | TEXT | NULL | Education info |
| `certifications` | TEXT[] | NULL | Certifications array |
| `source_system` | TEXT | NOT NULL | Source system identifier |
| `source_record_id` | TEXT | NULL | Source record ID |
| `promoted_from_intake_at` | TIMESTAMPTZ | NOT NULL | Promotion timestamp |
| `promotion_audit_log_id` | INTEGER | NULL | Audit log reference |
| `created_at` | TIMESTAMPTZ | DEFAULT NOW() | Record creation |
| `updated_at` | TIMESTAMPTZ | DEFAULT NOW() | Last update (auto-updated) |

#### Indexes
- `idx_people_master_company_id` ON (company_unique_id)
- `idx_people_master_slot_id` ON (company_slot_unique_id)
- `idx_people_master_full_name` ON (full_name)
- `idx_people_master_email` ON (email)
- `idx_people_master_title` ON (title)
- `idx_people_master_source_system` ON (source_system)
- `idx_people_master_promoted_at` ON (promoted_from_intake_at)

#### Triggers
- `trigger_people_master_updated_at` - Auto-updates `updated_at` on UPDATE

#### Constraints
- Barton ID format validation for unique_id (04.04.02)
- Barton ID format validation for company_unique_id (04.04.01)
- Barton ID format validation for company_slot_unique_id (04.04.05)
- Email format validation (RFC-compliant regex)

---

### 3. marketing.company_slot

**Purpose**: Role-based slots (CEO/CFO/HR) for company contacts

**Barton ID Format**: `04.04.05.XX.XXXXX.XXX`

#### Columns

| Column | Type | Nullable | Description |
|--------|------|----------|-------------|
| `company_slot_unique_id` | TEXT | PRIMARY KEY | Barton ID (immutable) |
| `company_unique_id` | TEXT | NOT NULL | Reference to company |
| `slot_type` | TEXT | NOT NULL | Role: CEO, CFO, or HR |
| `person_unique_id` | TEXT | NULL | Reference to assigned person |
| `is_filled` | BOOLEAN | DEFAULT FALSE | Slot filled status |
| `filled_at` | TIMESTAMPTZ | NULL | Slot fill timestamp |
| `last_refreshed_at` | TIMESTAMPTZ | NULL | Last data refresh |
| `created_at` | TIMESTAMPTZ | DEFAULT NOW() | Record creation |
| `updated_at` | TIMESTAMPTZ | DEFAULT NOW() | Last update |

#### Indexes
- `idx_company_slot_company_id` ON (company_unique_id)
- `idx_company_slot_type` ON (slot_type)
- `idx_company_slot_is_filled` ON (is_filled)

#### Constraints
- Unique constraint on (company_unique_id, slot_type) - one slot per role per company
- slot_type must be in ('CEO', 'CFO', 'HR')

---

### 4. marketing.company_intelligence

**Purpose**: Intelligence data about companies (signals, events, scores)

#### Columns

| Column | Type | Nullable | Description |
|--------|------|----------|-------------|
| `intelligence_id` | SERIAL | PRIMARY KEY | Auto-increment ID |
| `company_unique_id` | TEXT | NOT NULL | Reference to company |
| `intelligence_type` | TEXT | NOT NULL | Type: news, signal, event, score |
| `source` | TEXT | NULL | Data source |
| `title` | TEXT | NULL | Intelligence title |
| `description` | TEXT | NULL | Full description |
| `url` | TEXT | NULL | Source URL |
| `score` | NUMERIC(5,2) | NULL | Relevance score (0-100) |
| `detected_at` | TIMESTAMPTZ | NULL | Detection timestamp |
| `payload` | JSONB | NULL | Additional data |
| `created_at` | TIMESTAMPTZ | DEFAULT NOW() | Record creation |

#### Indexes
- ON (company_unique_id)
- ON (intelligence_type)
- ON (detected_at DESC)
- ON (score DESC)

---

### 5. marketing.people_intelligence

**Purpose**: Intelligence data about people (LinkedIn updates, job changes)

#### Columns

| Column | Type | Nullable | Description |
|--------|------|----------|-------------|
| `intelligence_id` | SERIAL | PRIMARY KEY | Auto-increment ID |
| `person_unique_id` | TEXT | NOT NULL | Reference to person |
| `intelligence_type` | TEXT | NOT NULL | Type: linkedin_update, job_change, etc |
| `previous_value` | TEXT | NULL | Old value (for changes) |
| `new_value` | TEXT | NULL | New value (for changes) |
| `detected_at` | TIMESTAMPTZ | NULL | Detection timestamp |
| `payload` | JSONB | NULL | Additional data |
| `created_at` | TIMESTAMPTZ | DEFAULT NOW() | Record creation |

#### Indexes
- ON (person_unique_id)
- ON (intelligence_type)
- ON (detected_at DESC)

---

### 6. marketing.pipeline_events

**Purpose**: Event tracking for the outreach pipeline

#### Columns

| Column | Type | Nullable | Description |
|--------|------|----------|-------------|
| `event_id` | SERIAL | PRIMARY KEY | Auto-increment ID |
| `event_type` | TEXT | NOT NULL | Event type identifier |
| `entity_type` | TEXT | NULL | company or person |
| `entity_id` | TEXT | NULL | Barton ID of entity |
| `event_data` | JSONB | NULL | Event payload |
| `created_at` | TIMESTAMPTZ | DEFAULT NOW() | Event timestamp |

#### Indexes
- ON (event_type)
- ON (entity_type, entity_id)
- ON (created_at DESC)

---

### 7. marketing.outreach_history

**Purpose**: Comprehensive view of all outreach activities

**Type**: VIEW (not a table)

**Definition**: Joins company, people, slots with enrichment and messaging data

---

## 📥 INTAKE Schema (Data Ingestion)

### 1. intake.raw_loads

**Purpose**: Raw JSON data ingestion with duplicate detection

**Security**: Row Level Security (RLS) enabled - INSERT/UPDATE/DELETE via functions only

#### Columns

| Column | Type | Nullable | Description |
|--------|------|----------|-------------|
| `load_id` | BIGSERIAL | PRIMARY KEY | Auto-increment ID |
| `batch_id` | TEXT | NOT NULL | Batch identifier |
| `source` | TEXT | NOT NULL | Data source |
| `raw_data` | JSONB | NOT NULL | Raw JSON payload |
| `status` | TEXT | DEFAULT 'pending' | pending/promoted/failed/duplicate |
| `created_at` | TIMESTAMPTZ | DEFAULT NOW() | Record creation |
| `promoted_at` | TIMESTAMPTZ | NULL | Promotion timestamp |
| `metadata` | JSONB | DEFAULT '{}' | Additional metadata |

#### Indexes
- `idx_raw_loads_batch_id` ON (batch_id)
- `idx_raw_loads_source` ON (source)
- `idx_raw_loads_status` ON (status)
- `idx_raw_loads_created_at` ON (created_at DESC)
- `idx_raw_loads_raw_data_email` ON ((raw_data->>'email')) - Expression index

#### RLS Policies
- `no_direct_insert` - Blocks direct INSERT
- `no_direct_update` - Blocks direct UPDATE
- `no_direct_delete` - Blocks direct DELETE
- `allow_select` - Allows SELECT for all

#### Access Functions
- `intake.f_ingest_json(p_rows jsonb[], p_source text, p_batch_id text)` - SECURITY DEFINER

---

### 2. intake.audit_log

**Purpose**: Audit trail for intake operations

#### Columns

| Column | Type | Nullable | Description |
|--------|------|----------|-------------|
| `audit_id` | BIGSERIAL | PRIMARY KEY | Auto-increment ID |
| `operation` | TEXT | NOT NULL | Operation type |
| `user_name` | TEXT | DEFAULT CURRENT_USER | User who performed operation |
| `batch_id` | TEXT | NULL | Batch identifier |
| `record_count` | INT | NULL | Number of records affected |
| `result` | JSONB | NULL | Operation result data |
| `created_at` | TIMESTAMPTZ | DEFAULT NOW() | Operation timestamp |

---

## 🔐 VAULT Schema (Promoted Contacts)

### 1. vault.contacts

**Purpose**: Promoted contacts from intake pipeline

**Security**: Row Level Security (RLS) enabled - INSERT/UPDATE/DELETE via functions only

#### Columns

| Column | Type | Nullable | Description |
|--------|------|----------|-------------|
| `contact_id` | BIGSERIAL | PRIMARY KEY | Auto-increment ID |
| `email` | TEXT | UNIQUE, NOT NULL | Email address (unique) |
| `name` | TEXT | NULL | Contact name |
| `phone` | TEXT | NULL | Phone number |
| `company` | TEXT | NULL | Company name |
| `title` | TEXT | NULL | Job title |
| `source` | TEXT | NOT NULL | Data source |
| `tags` | JSONB | DEFAULT '[]' | Contact tags array |
| `custom_fields` | JSONB | DEFAULT '{}' | Custom field data |
| `load_id` | BIGINT | NULL | Reference to intake.raw_loads |
| `created_at` | TIMESTAMPTZ | DEFAULT NOW() | Record creation |
| `updated_at` | TIMESTAMPTZ | DEFAULT NOW() | Last update |
| `last_activity_at` | TIMESTAMPTZ | NULL | Last activity timestamp |
| `score` | NUMERIC(5,2) | DEFAULT 0 | Lead score (0-100) |
| `status` | TEXT | DEFAULT 'active' | active/inactive/bounced/unsubscribed |

#### Indexes
- `idx_contacts_email` ON (email)
- `idx_contacts_source` ON (source)
- `idx_contacts_created_at` ON (created_at DESC)
- `idx_contacts_score` ON (score DESC)
- `idx_contacts_status` ON (status)
- `idx_contacts_company` ON (company)

#### Access Functions
- `vault.f_promote_contacts(p_load_ids bigint[])` - SECURITY DEFINER

---

## 🎯 BIT Schema (Buyer Intent Tool)

### 1. bit.signal

**Purpose**: Track buying intent signals for companies

#### Columns

| Column | Type | Nullable | Description |
|--------|------|----------|-------------|
| `signal_id` | BIGSERIAL | PRIMARY KEY | Auto-increment ID |
| `company_id` | BIGINT | NULL | Reference to company (if migrated) |
| `reason` | TEXT | NULL | Signal type (e.g., renewal_window, exec_movement) |
| `payload` | JSONB | NULL | Additional signal data |
| `created_at` | TIMESTAMPTZ | NULL | Signal detection time |
| `processed_at` | TIMESTAMPTZ | NULL | Signal processing time |

---

## 🔧 PUBLIC Schema (Utilities)

### 1. public.shq_error_log

**Purpose**: System-wide error logging

**Barton ID**: Errors tracked with unique IDs

#### Columns

| Column | Type | Nullable | Description |
|--------|------|----------|-------------|
| `id` | SERIAL | PRIMARY KEY | Auto-increment ID |
| `unique_id` | TEXT | UNIQUE | Barton-style error ID |
| `error_type` | TEXT | NULL | Error classification |
| `error_message` | TEXT | NULL | Error message |
| `stack_trace` | TEXT | NULL | Full stack trace |
| `context` | JSONB | DEFAULT '{}' | Error context data |
| `severity` | TEXT | NULL | critical/high/medium/low |
| `resolved` | BOOLEAN | DEFAULT FALSE | Resolution status |
| `resolved_at` | TIMESTAMPTZ | NULL | Resolution timestamp |
| `created_at` | TIMESTAMPTZ | DEFAULT NOW() | Error timestamp |
| `updated_at` | TIMESTAMPTZ | DEFAULT NOW() | Last update |

#### Indexes
- ON (unique_id)
- ON (error_type)
- ON (severity)
- ON (resolved)
- ON (created_at DESC)

---

### 2. public.linkedin_refresh_jobs

**Purpose**: Track LinkedIn profile refresh jobs via Apify

#### Columns

| Column | Type | Nullable | Description |
|--------|------|----------|-------------|
| `job_id` | SERIAL | PRIMARY KEY | Auto-increment ID |
| `person_unique_id` | TEXT | NOT NULL | Reference to person |
| `linkedin_url` | TEXT | NOT NULL | LinkedIn profile URL |
| `apify_run_id` | TEXT | NULL | Apify actor run ID |
| `status` | TEXT | DEFAULT 'pending' | pending/running/completed/failed |
| `requested_at` | TIMESTAMPTZ | DEFAULT NOW() | Job request time |
| `started_at` | TIMESTAMPTZ | NULL | Job start time |
| `completed_at` | TIMESTAMPTZ | NULL | Job completion time |
| `result_data` | JSONB | NULL | Scraped data result |
| `error_message` | TEXT | NULL | Error if failed |

#### Indexes
- ON (person_unique_id)
- ON (status)
- ON (requested_at DESC)

---

### 3. public.actor_usage_log

**Purpose**: Track Apify actor usage and costs

#### Columns

| Column | Type | Nullable | Description |
|--------|------|----------|-------------|
| `log_id` | SERIAL | PRIMARY KEY | Auto-increment ID |
| `actor_id` | TEXT | NOT NULL | Apify actor identifier |
| `run_id` | TEXT | NOT NULL | Apify run ID |
| `started_at` | TIMESTAMPTZ | NULL | Run start time |
| `finished_at` | TIMESTAMPTZ | NULL | Run finish time |
| `status` | TEXT | NULL | SUCCEEDED/FAILED/TIMED-OUT |
| `compute_units` | NUMERIC(10,4) | NULL | Compute units consumed |
| `dataset_items` | INTEGER | NULL | Number of items scraped |
| `error_message` | TEXT | NULL | Error if failed |
| `metadata` | JSONB | DEFAULT '{}' | Additional metadata |
| `created_at` | TIMESTAMPTZ | DEFAULT NOW() | Log timestamp |

#### Indexes
- ON (actor_id)
- ON (run_id)
- ON (status)
- ON (started_at DESC)

---

## 🔐 Security & Access

### Roles

1. **mcp_ingest** - Data ingestion operations
   - `EXECUTE ON FUNCTION intake.f_ingest_json`
   - `SELECT ON intake.latest_100`

2. **mcp_promote** - Data promotion operations
   - `EXECUTE ON FUNCTION vault.f_promote_contacts`
   - `SELECT ON intake.latest_100`

### Row Level Security (RLS)

RLS is **enabled** on:
- `intake.raw_loads` - All DML blocked, only functions allowed
- `vault.contacts` - All DML blocked, only functions allowed

### Security Definer Functions

Functions that bypass RLS:
- `intake.f_ingest_json()` - Secure data ingestion
- `vault.f_promote_contacts()` - Secure data promotion

---

## 📊 Views

### marketing.outreach_history
Comprehensive view joining:
- company_master
- people_master
- company_slot
- company_intelligence
- people_intelligence
- Message logs
- Booking events

### intake.latest_100
Latest 100 ingested records for monitoring

---

## 🔧 Global Functions

### trigger_updated_at()
**Purpose**: Automatically update `updated_at` column on row UPDATE
**Type**: TRIGGER FUNCTION
**Language**: PL/pgSQL

### generate_barton_id()
**Purpose**: Generate Barton ID format: `NN.NN.NN.NN.NNNNN.NNN`
**Returns**: VARCHAR(23)
**Language**: PL/pgSQL

---

## 📝 Barton Doctrine Compliance

### ID Formats

| Entity | Barton ID Pattern | Example |
|--------|------------------|---------|
| Company | 04.04.01.XX.XXXXX.XXX | 04.04.01.25.12345.678 |
| Person | 04.04.02.XX.XXXXX.XXX | 04.04.02.25.54321.234 |
| Company Slot | 04.04.05.XX.XXXXX.XXX | 04.04.05.25.98765.432 |
| Error Log | Custom format | ERR-2025-11-06-001 |

### Audit Trail

All tables include:
- `created_at` - Record creation timestamp
- `updated_at` - Last update timestamp (auto-updated via trigger)

Specific audit fields:
- `promoted_from_intake_at` - When record was promoted
- `promotion_audit_log_id` - Reference to audit log

---

## 📈 Migration Files (29 total)

Key migrations in `ctb/data/migrations/outreach-process-manager/`:

1. `create_company_master.sql` - Company master table
2. `create_people_master.sql` - People master table
3. `create_company_slot.sql` - Company slots
4. `2025-10-22_create_marketing_company_intelligence.sql` - Intelligence tracking
5. `2025-10-22_create_marketing_people_intelligence.sql` - People intelligence
6. `2025-10-23_create_linkedin_refresh_jobs.sql` - LinkedIn refresh system
7. `2025-10-24_create_actor_usage_log.sql` - Apify usage tracking
8. `apify_integration_helpers.sql` - Apify helper functions
9. `create_attribution_tables.sql` - Attribution tracking
10. `create_campaign_tables.sql` - Campaign management

---

## 🔄 Data Flow

```
External Sources (Apify, Apollo, etc.)
          ↓
   intake.raw_loads (JSONB staging)
          ↓
   intake.f_ingest_json() [SECURITY DEFINER]
          ↓
   Validation & Enrichment
          ↓
   vault.f_promote_contacts() [SECURITY DEFINER]
          ↓
   marketing.company_master + people_master
          ↓
   marketing.company_slot (role assignment)
          ↓
   Outreach campaigns & messaging
```

---

## 📊 Current Statistics

- **Total Schemas**: 7 (marketing, intake, vault, company, people, bit, public)
- **Active Tables**: 15+ production tables
- **Indexes**: 50+ for query performance
- **Views**: 10+ for data analysis
- **Functions**: 10+ (including triggers)
- **RLS Policies**: 8 policies on 2 tables

---

## 🎯 Ready for Configuration

The schema is fully documented and ready for your adjustments. Key areas you may want to modify:

1. **Column additions/removals** in company_master or people_master
2. **New tables** for additional features
3. **Index optimization** for specific queries
4. **View adjustments** for reporting
5. **Constraint modifications** for data validation

---

**Document Version**: 1.0
**Last Updated**: 2025-11-06
**Schema Version**: Production (v2.0)
**Compliance**: 100% Barton Doctrine
