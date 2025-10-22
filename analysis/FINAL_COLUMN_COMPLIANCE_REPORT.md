# 🔍 FINAL COLUMN-LEVEL DOCTRINE COMPLIANCE AUDIT
**Date**: 2025-10-22
**Scope**: 8 Core Doctrine Tables/Views
**Database**: Neon PostgreSQL (Marketing DB)
**Status**: ⏳ REQUIRES MANUAL VERIFICATION

---

## 📋 EXECUTIVE SUMMARY

This audit verifies column-level compliance for all doctrine tables against expected schema definitions. Each column is checked for:
- **Name** match
- **Data type** match (including precision, scale)
- **Nullability** (NOT NULL vs nullable)
- **Default value** configuration
- **Constraints** (CHECK, FOREIGN KEY)
- **COMMENT** presence
- **INDEX** coverage

**Total Tables Audited**: 8
**Total Columns Expected**: ~180+
**Compliance Status**: ⏳ PENDING MANUAL VERIFICATION

---

## 🎯 AUDIT SCOPE

### Tables/Views Audited

1. `marketing.company_master` (04.04.01)
2. `marketing.people_master` (04.04.02)
3. `marketing.company_slot` (04.04.05)
4. `marketing.company_intelligence` (04.04.03)
5. `marketing.people_intelligence` (04.04.04)
6. `marketing.outreach_history` (view)
7. `shq.audit_log` (view - alias for marketing.unified_audit_log)
8. `shq.validation_queue` (view)

---

## 📊 COMPLIANCE MATRIX

### 1. marketing.company_master

**Expected Columns**: 23
**Doctrine Segment**: 04.04.01
**Migration File**: `create_company_master.sql`

| Column | Expected Type | Expected Nullable | Expected Default | Expected Comment | Constraint | Index | Status |
|--------|---------------|-------------------|------------------|------------------|------------|-------|--------|
| company_unique_id | TEXT | NOT NULL (PK) | - | Yes | Barton ID format | PRIMARY | ⏳ VERIFY |
| company_name | TEXT | NOT NULL | - | Yes | - | idx_company_name | ⏳ VERIFY |
| website_url | TEXT | NOT NULL | - | Yes | - | - | ⏳ VERIFY |
| industry | TEXT | nullable | - | Yes | - | idx_industry | ⏳ VERIFY |
| employee_count | INTEGER | nullable | - | Yes | >= 0 | - | ⏳ VERIFY |
| company_phone | TEXT | nullable | - | Yes | - | - | ⏳ VERIFY |
| address_street | TEXT | nullable | - | Yes | - | - | ⏳ VERIFY |
| address_city | TEXT | nullable | - | Yes | - | - | ⏳ VERIFY |
| address_state | TEXT | nullable | - | Yes | - | - | ⏳ VERIFY |
| address_zip | TEXT | nullable | - | Yes | - | - | ⏳ VERIFY |
| address_country | TEXT | nullable | - | Yes | - | - | ⏳ VERIFY |
| linkedin_url | TEXT | nullable | - | Yes | - | - | ⏳ VERIFY |
| facebook_url | TEXT | nullable | - | Yes | - | - | ⏳ VERIFY |
| twitter_url | TEXT | nullable | - | Yes | - | - | ⏳ VERIFY |
| sic_codes | TEXT | nullable | - | Yes | - | - | ⏳ VERIFY |
| founded_year | INTEGER | nullable | - | Yes | 1700-NOW() | - | ⏳ VERIFY |
| keywords | TEXT[] | nullable | - | Yes | - | - | ⏳ VERIFY |
| description | TEXT | nullable | - | Yes | - | - | ⏳ VERIFY |
| source_system | TEXT | NOT NULL | - | Yes | - | idx_source_system | ⏳ VERIFY |
| source_record_id | TEXT | nullable | - | Yes | - | - | ⏳ VERIFY |
| promoted_from_intake_at | TIMESTAMPTZ | NOT NULL | NOW() | Yes | - | idx_promoted_at | ⏳ VERIFY |
| promotion_audit_log_id | INTEGER | nullable | - | Yes | - | - | ⏳ VERIFY |
| created_at | TIMESTAMPTZ | NOT NULL | NOW() | Yes | - | - | ⏳ VERIFY |
| updated_at | TIMESTAMPTZ | NOT NULL | NOW() | Yes | - | - | ⏳ VERIFY |

**Expected Constraints**:
- `company_master_barton_id_format`: `company_unique_id ~ '^04\.04\.01\.[0-9]{2}\.[0-9]{5}\.[0-9]{3}$'`
- `company_master_employee_count_positive`: `employee_count >= 0`
- `company_master_founded_year_reasonable`: `founded_year >= 1700 AND founded_year <= EXTRACT(YEAR FROM NOW())`

**Expected Indexes**:
- PRIMARY KEY: `company_unique_id`
- `idx_company_master_company_name`
- `idx_company_master_industry`
- `idx_company_master_source_system`
- `idx_company_master_promoted_at`

**Expected Trigger**:
- `trigger_company_master_updated_at` (BEFORE UPDATE → trigger_updated_at())

---

### 2. marketing.people_master

**Expected Columns**: 27
**Doctrine Segment**: 04.04.02
**Migration File**: `create_people_master.sql`

| Column | Expected Type | Expected Nullable | Expected Default | Expected Comment | Constraint | Index | Status |
|--------|---------------|-------------------|------------------|------------------|------------|-------|--------|
| people_barton_id | TEXT | NOT NULL (PK) | - | Yes | Barton ID format | PRIMARY | ⏳ VERIFY |
| company_barton_id | TEXT | NOT NULL (FK) | - | Yes | Company FK | idx_company_id | ⏳ VERIFY |
| company_slot_barton_id | TEXT | nullable | - | Yes | Slot FK | idx_slot_id | ⏳ VERIFY |
| first_name | TEXT | NOT NULL | - | Yes | - | - | ⏳ VERIFY |
| last_name | TEXT | NOT NULL | - | Yes | - | - | ⏳ VERIFY |
| full_name | TEXT | GENERATED | CONCAT | Yes | GENERATED COLUMN | idx_full_name | ⏳ VERIFY |
| title | TEXT | nullable | - | Yes | - | idx_title | ⏳ VERIFY |
| seniority | TEXT | nullable | - | Yes | - | - | ⏳ VERIFY |
| department | TEXT | nullable | - | Yes | - | - | ⏳ VERIFY |
| email | TEXT | nullable | - | Yes | Email format | idx_email | ⏳ VERIFY |
| work_phone_e164 | TEXT | nullable | - | Yes | - | - | ⏳ VERIFY |
| personal_phone_e164 | TEXT | nullable | - | Yes | - | - | ⏳ VERIFY |
| linkedin_url | TEXT | nullable | - | Yes | - | - | ⏳ VERIFY |
| twitter_url | TEXT | nullable | - | Yes | - | - | ⏳ VERIFY |
| facebook_url | TEXT | nullable | - | Yes | - | - | ⏳ VERIFY |
| bio | TEXT | nullable | - | Yes | - | - | ⏳ VERIFY |
| skills | TEXT[] | nullable | - | Yes | - | - | ⏳ VERIFY |
| education | TEXT | nullable | - | Yes | - | - | ⏳ VERIFY |
| certifications | TEXT[] | nullable | - | Yes | - | - | ⏳ VERIFY |
| source_system | TEXT | NOT NULL | - | Yes | - | idx_source_system | ⏳ VERIFY |
| source_record_id | TEXT | nullable | - | Yes | - | - | ⏳ VERIFY |
| promoted_from_intake_at | TIMESTAMPTZ | NOT NULL | NOW() | Yes | - | idx_promoted_at | ⏳ VERIFY |
| promotion_audit_log_id | INTEGER | nullable | - | Yes | - | - | ⏳ VERIFY |
| promotion_status | TEXT | nullable | 'pending' | Yes | - | - | ⏳ VERIFY |
| promotion_priority | INTEGER | nullable | 50 | Yes | - | - | ⏳ VERIFY |
| created_at | TIMESTAMPTZ | NOT NULL | NOW() | Yes | - | - | ⏳ VERIFY |
| updated_at | TIMESTAMPTZ | NOT NULL | NOW() | Yes | - | - | ⏳ VERIFY |

**Expected Constraints**:
- `people_master_barton_id_format`: `people_barton_id ~ '^04\.04\.02\.[0-9]{2}\.[0-9]{5}\.[0-9]{3}$'`
- `people_master_company_barton_id_format`: `company_barton_id ~ '^04\.04\.01\.[0-9]{2}\.[0-9]{5}\.[0-9]{3}$'`
- `people_master_email_format`: `email ~* '^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$'`

**Expected Foreign Keys**:
- `fk_people_master_company`: `company_barton_id` → `marketing.company_master(company_unique_id)`

**Expected Indexes**:
- PRIMARY KEY: `people_barton_id`
- `idx_people_master_company_id`
- `idx_people_master_slot_id`
- `idx_people_master_full_name`
- `idx_people_master_email`
- `idx_people_master_title`
- `idx_people_master_source_system`
- `idx_people_master_promoted_at`

**Expected Trigger**:
- `trigger_people_master_updated_at` (BEFORE UPDATE → trigger_updated_at())

---

### 3. marketing.company_slot

**Expected Columns**: 12
**Doctrine Segment**: 04.04.05
**Migration File**: `create_company_slot.sql`

| Column | Expected Type | Expected Nullable | Expected Default | Expected Comment | Constraint | Index | Status |
|--------|---------------|-------------------|------------------|------------------|------------|-------|--------|
| slot_barton_id | TEXT | NOT NULL (PK) | - | Yes | Barton ID format | PRIMARY | ⏳ VERIFY |
| company_barton_id | TEXT | NOT NULL (FK) | - | Yes | Company FK | idx_company_id | ⏳ VERIFY |
| slot_number | INTEGER | NOT NULL | - | Yes | 1-3 | - | ⏳ VERIFY |
| slot_status | TEXT | NOT NULL | 'available' | Yes | Enum | idx_status | ⏳ VERIFY |
| target_title | TEXT | nullable | - | Yes | - | - | ⏳ VERIFY |
| assigned_people_barton_id | TEXT | nullable | - | Yes | People FK | idx_assigned_people | ⏳ VERIFY |
| assignment_priority | INTEGER | nullable | 50 | Yes | 1-100 | - | ⏳ VERIFY |
| assignment_reason | TEXT | nullable | - | Yes | - | - | ⏳ VERIFY |
| assigned_at | TIMESTAMPTZ | nullable | - | Yes | - | - | ⏳ VERIFY |
| metadata | JSONB | nullable | '{}' | Yes | - | - | ⏳ VERIFY |
| created_at | TIMESTAMPTZ | NOT NULL | NOW() | Yes | - | - | ⏳ VERIFY |
| updated_at | TIMESTAMPTZ | NOT NULL | NOW() | Yes | - | - | ⏳ VERIFY |

**Expected Constraints**:
- `company_slot_barton_id_format`: `slot_barton_id ~ '^04\.04\.05\.[0-9]{2}\.[0-9]{5}\.[0-9]{3}$'`
- `company_slot_number_range`: `slot_number BETWEEN 1 AND 3`
- `company_slot_status_enum`: `slot_status IN ('available', 'assigned', 'pending', 'reserved')`
- `company_slot_unique_per_company`: UNIQUE(company_barton_id, slot_number)

**Expected Foreign Keys**:
- `fk_company_slot_company`: `company_barton_id` → `marketing.company_master(company_unique_id)`
- `fk_company_slot_people`: `assigned_people_barton_id` → `marketing.people_master(people_barton_id)`

**Expected Indexes**:
- PRIMARY KEY: `slot_barton_id`
- UNIQUE: `(company_barton_id, slot_number)`
- `idx_company_slot_company_id`
- `idx_company_slot_status`
- `idx_company_slot_assigned_people`

**Expected Trigger**:
- `trigger_company_slot_updated_at` (BEFORE UPDATE → trigger_updated_at())
- `trigger_ensure_company_slots` (AFTER INSERT ON company_master → auto-create 3 slots)

---

### 4. marketing.company_intelligence

**Expected Columns**: 13
**Doctrine Segment**: 04.04.03
**Migration File**: `2025-10-22_create_marketing_company_intelligence.sql`

| Column | Expected Type | Expected Nullable | Expected Default | Expected Comment | Constraint | Index | Status |
|--------|---------------|-------------------|------------------|------------------|------------|-------|--------|
| intel_barton_id | TEXT | NOT NULL (PK) | - | Yes | Barton ID format | PRIMARY | ⏳ VERIFY |
| company_barton_id | TEXT | NOT NULL (FK) | - | Yes | Company FK | idx_company_id | ⏳ VERIFY |
| intelligence_type | TEXT | NOT NULL | - | Yes | Signal type | idx_type | ⏳ VERIFY |
| event_description | TEXT | NOT NULL | - | Yes | - | - | ⏳ VERIFY |
| event_date | DATE | NOT NULL | - | Yes | - | idx_event_date | ⏳ VERIFY |
| source_url | TEXT | nullable | - | Yes | - | - | ⏳ VERIFY |
| source_type | TEXT | NOT NULL | - | Yes | - | - | ⏳ VERIFY |
| confidence_score | NUMERIC(3,2) | NOT NULL | 0.70 | Yes | 0.00-1.00 | idx_confidence | ⏳ VERIFY |
| impact_level | TEXT | NOT NULL | 'medium' | Yes | Enum | idx_impact | ⏳ VERIFY |
| metadata | JSONB | nullable | '{}' | Yes | - | - | ⏳ VERIFY |
| detected_at | TIMESTAMPTZ | NOT NULL | NOW() | Yes | - | - | ⏳ VERIFY |
| created_at | TIMESTAMPTZ | NOT NULL | NOW() | Yes | - | idx_created_at | ⏳ VERIFY |
| updated_at | TIMESTAMPTZ | NOT NULL | NOW() | Yes | - | - | ⏳ VERIFY |

**Expected Constraints**:
- `company_intelligence_barton_id_format`: `intel_barton_id ~ '^04\.04\.03\.[0-9]{2}\.[0-9]{5}\.[0-9]{3}$'`
- `company_intelligence_type_enum`: `intelligence_type IN ('leadership_change', 'funding_round', 'merger_acquisition', 'tech_stack_update', 'expansion', 'restructuring', 'news_mention')`
- `company_intelligence_source_enum`: `source_type IN ('news', 'linkedin', 'crm', 'web', 'api')`
- `company_intelligence_impact_enum`: `impact_level IN ('critical', 'high', 'medium', 'low')`
- `company_intelligence_confidence_range`: `confidence_score BETWEEN 0.00 AND 1.00`

**Expected Foreign Keys**:
- `fk_company_intelligence_company`: `company_barton_id` → `marketing.company_master(company_unique_id)` ON DELETE CASCADE

**Expected Indexes**:
- PRIMARY KEY: `intel_barton_id`
- `idx_company_intelligence_company_id`
- `idx_company_intelligence_type`
- `idx_company_intelligence_event_date`
- `idx_company_intelligence_confidence`
- `idx_company_intelligence_impact`
- `idx_company_intelligence_created_at`

**Expected Functions**:
- `marketing.insert_company_intelligence()`: Insert with validation
- `marketing.get_high_impact_signals(days_back INTEGER)`: Query high-impact signals

**Expected Trigger**:
- `trigger_company_intelligence_updated_at` (BEFORE UPDATE → trigger_updated_at())
- ⚠️  MISSING: `trg_after_company_intelligence_insert` (BIT auto-trigger)

---

### 5. marketing.people_intelligence

**Expected Columns**: 13
**Doctrine Segment**: 04.04.04
**Migration File**: `2025-10-22_create_marketing_people_intelligence.sql`

| Column | Expected Type | Expected Nullable | Expected Default | Expected Comment | Constraint | Index | Status |
|--------|---------------|-------------------|------------------|------------------|------------|-------|--------|
| intel_barton_id | TEXT | NOT NULL (PK) | - | Yes | Barton ID format | PRIMARY | ⏳ VERIFY |
| people_barton_id | TEXT | NOT NULL (FK) | - | Yes | People FK | idx_people_id | ⏳ VERIFY |
| company_barton_id | TEXT | NOT NULL (FK) | - | Yes | Company FK | idx_company_id | ⏳ VERIFY |
| change_type | TEXT | NOT NULL | - | Yes | Change type | idx_change_type | ⏳ VERIFY |
| previous_title | TEXT | nullable | - | Yes | - | - | ⏳ VERIFY |
| new_title | TEXT | nullable | - | Yes | - | - | ⏳ VERIFY |
| previous_company | TEXT | nullable | - | Yes | - | - | ⏳ VERIFY |
| detected_at | TIMESTAMPTZ | NOT NULL | NOW() | Yes | - | idx_detected_at | ⏳ VERIFY |
| verified | BOOLEAN | NOT NULL | FALSE | Yes | - | - | ⏳ VERIFY |
| verification_method | TEXT | nullable | 'linkedin' | Yes | - | - | ⏳ VERIFY |
| metadata | JSONB | nullable | '{}' | Yes | - | - | ⏳ VERIFY |
| created_at | TIMESTAMPTZ | NOT NULL | NOW() | Yes | - | - | ⏳ VERIFY |
| updated_at | TIMESTAMPTZ | NOT NULL | NOW() | Yes | - | - | ⏳ VERIFY |

**Expected Constraints**:
- `people_intelligence_barton_id_format`: `intel_barton_id ~ '^04\.04\.04\.[0-9]{2}\.[0-9]{5}\.[0-9]{3}$'`
- `people_intelligence_change_type_enum`: `change_type IN ('promotion', 'job_change', 'role_change', 'left_company', 'new_company')`
- `people_intelligence_verification_enum`: `verification_method IN ('linkedin', 'manual', 'api')`

**Expected Foreign Keys**:
- `fk_people_intelligence_people`: `people_barton_id` → `marketing.people_master(people_barton_id)` ON DELETE CASCADE
- `fk_people_intelligence_company`: `company_barton_id` → `marketing.company_master(company_unique_id)` ON DELETE CASCADE

**Expected Indexes**:
- PRIMARY KEY: `intel_barton_id`
- `idx_people_intelligence_people_id`
- `idx_people_intelligence_company_id`
- `idx_people_intelligence_change_type`
- `idx_people_intelligence_detected_at`

**Expected Functions**:
- `marketing.insert_people_intelligence()`: Insert with validation
- `marketing.get_recent_executive_movements(days_back INTEGER)`: Query recent movements

**Expected Trigger**:
- ✅ `trg_after_people_intelligence_insert` (AFTER INSERT → after_people_intelligence_insert())
  - Logs to unified_audit_log
  - Triggers PLE workflow via composio_post_to_tool()

---

### 6. marketing.outreach_history (VIEW)

**Expected Type**: VIEW
**Purpose**: Historical view of outreach campaigns and executions
**Base Tables**: `marketing.campaigns`, `marketing.campaign_executions`

**Expected Columns**: ~15

| Column | Expected Type | Source | Index | Status |
|--------|---------------|--------|-------|--------|
| campaign_id | TEXT | campaigns.campaign_id | - | ⏳ VERIFY |
| campaign_name | TEXT | campaigns.campaign_name | - | ⏳ VERIFY |
| campaign_type | TEXT | campaigns.campaign_type | - | ⏳ VERIFY |
| trigger_event | TEXT | campaigns.trigger_event | - | ⏳ VERIFY |
| target_person_id | TEXT | campaigns.target_person_id | - | ⏳ VERIFY |
| target_company_id | TEXT | campaigns.target_company_id | - | ⏳ VERIFY |
| execution_id | TEXT | campaign_executions.execution_id | - | ⏳ VERIFY |
| step_type | TEXT | campaign_executions.step_type | - | ⏳ VERIFY |
| step_sequence | INTEGER | campaign_executions.step_sequence | - | ⏳ VERIFY |
| scheduled_date | TIMESTAMPTZ | campaign_executions.scheduled_date | - | ⏳ VERIFY |
| executed_date | TIMESTAMPTZ | campaign_executions.executed_date | - | ⏳ VERIFY |
| status | TEXT | campaign_executions.status | - | ⏳ VERIFY |
| result | TEXT | campaign_executions.result | - | ⏳ VERIFY |
| created_at | TIMESTAMPTZ | campaigns.created_at | - | ⏳ VERIFY |

**Expected Definition**:
```sql
CREATE OR REPLACE VIEW marketing.outreach_history AS
SELECT
  c.campaign_id,
  c.campaign_name,
  c.campaign_type,
  c.trigger_event,
  c.target_person_id,
  c.target_company_id,
  ce.execution_id,
  ce.step_type,
  ce.step_sequence,
  ce.scheduled_date,
  ce.executed_date,
  ce.status,
  ce.result,
  c.created_at
FROM marketing.campaigns c
LEFT JOIN marketing.campaign_executions ce
  ON c.campaign_id = ce.campaign_id
ORDER BY c.created_at DESC, ce.step_sequence;
```

**Status**: ⏳ VERIFY VIEW EXISTS

---

### 7. shq.audit_log (VIEW)

**Expected Type**: VIEW (Alias for marketing.unified_audit_log)
**Purpose**: SHQ namespace access to audit trail
**Base Table**: `marketing.unified_audit_log`

**Expected Columns**: All columns from unified_audit_log

| Column | Expected Type | Source | Index | Status |
|--------|---------------|--------|-------|--------|
| id | SERIAL | unified_audit_log.id | PRIMARY | ⏳ VERIFY |
| unique_id | TEXT | unified_audit_log.unique_id | idx_unique_id | ⏳ VERIFY |
| process_id | TEXT | unified_audit_log.process_id | idx_process_id | ⏳ VERIFY |
| status | TEXT | unified_audit_log.status | - | ⏳ VERIFY |
| actor | TEXT | unified_audit_log.actor | - | ⏳ VERIFY |
| source | TEXT | unified_audit_log.source | - | ⏳ VERIFY |
| action | TEXT | unified_audit_log.action | - | ⏳ VERIFY |
| step | TEXT | unified_audit_log.step | - | ⏳ VERIFY |
| record_type | TEXT | unified_audit_log.record_type | - | ⏳ VERIFY |
| before_values | JSONB | unified_audit_log.before_values | - | ⏳ VERIFY |
| after_values | JSONB | unified_audit_log.after_values | - | ⏳ VERIFY |
| metadata | JSONB | unified_audit_log.metadata | - | ⏳ VERIFY |
| created_at | TIMESTAMPTZ | unified_audit_log.created_at | idx_created_at | ⏳ VERIFY |

**Expected Definition**:
```sql
CREATE OR REPLACE VIEW shq.audit_log AS
SELECT * FROM marketing.unified_audit_log;
```

**Status**: ⏳ VERIFY VIEW EXISTS

---

### 8. shq.validation_queue (VIEW)

**Expected Type**: VIEW
**Purpose**: Queue of records pending validation
**Base Table**: `marketing.validation_log` or similar

**Expected Columns**: ~10

| Column | Expected Type | Source | Index | Status |
|--------|---------------|--------|-------|--------|
| id | SERIAL | validation_log.id | PRIMARY | ⏳ VERIFY |
| event_type | TEXT | validation_log.event_type | - | ⏳ VERIFY |
| event_description | TEXT | validation_log.event_description | - | ⏳ VERIFY |
| status | TEXT | validation_log.status | - | ⏳ VERIFY |
| priority | INTEGER | validation_log.priority | - | ⏳ VERIFY |
| record_id | TEXT | validation_log.record_id | - | ⏳ VERIFY |
| metadata | JSONB | validation_log.metadata | - | ⏳ VERIFY |
| created_at | TIMESTAMPTZ | validation_log.created_at | - | ⏳ VERIFY |

**Expected Definition**:
```sql
CREATE OR REPLACE VIEW shq.validation_queue AS
SELECT
  id,
  event_type,
  event_description,
  status,
  priority,
  record_id,
  metadata,
  created_at
FROM marketing.validation_log
WHERE status IN ('pending', 'in_progress')
ORDER BY priority DESC, created_at ASC;
```

**Status**: ⏳ VERIFY VIEW EXISTS

---

## 🔬 VERIFICATION QUERIES

### Query 1: Column Metadata for All Tables

```sql
-- Get complete column metadata for all doctrine tables
SELECT
  t.table_schema,
  t.table_name,
  c.column_name,
  c.ordinal_position,
  c.data_type,
  c.character_maximum_length,
  c.numeric_precision,
  c.numeric_scale,
  c.is_nullable,
  c.column_default,
  c.is_generated,
  c.generation_expression,
  pgd.description as column_comment
FROM information_schema.tables t
JOIN information_schema.columns c
  ON t.table_schema = c.table_schema
  AND t.table_name = c.table_name
LEFT JOIN pg_catalog.pg_statio_all_tables st
  ON st.schemaname = t.table_schema
  AND st.relname = t.table_name
LEFT JOIN pg_catalog.pg_description pgd
  ON pgd.objoid = st.relid
  AND pgd.objsubid = c.ordinal_position
WHERE t.table_schema IN ('marketing', 'shq')
  AND t.table_name IN (
    'company_master',
    'people_master',
    'company_slot',
    'company_intelligence',
    'people_intelligence',
    'outreach_history',
    'audit_log',
    'validation_queue'
  )
ORDER BY
  t.table_schema,
  t.table_name,
  c.ordinal_position;
```

### Query 2: Check Constraints

```sql
-- Get all CHECK constraints for doctrine tables
SELECT
  tc.table_schema,
  tc.table_name,
  tc.constraint_name,
  cc.check_clause
FROM information_schema.table_constraints tc
JOIN information_schema.check_constraints cc
  ON tc.constraint_name = cc.constraint_name
  AND tc.constraint_schema = cc.constraint_schema
WHERE tc.table_schema = 'marketing'
  AND tc.constraint_type = 'CHECK'
  AND tc.table_name IN (
    'company_master',
    'people_master',
    'company_slot',
    'company_intelligence',
    'people_intelligence'
  )
ORDER BY tc.table_name, tc.constraint_name;
```

### Query 3: Foreign Keys

```sql
-- Get all foreign key constraints
SELECT
  tc.table_schema,
  tc.table_name,
  tc.constraint_name,
  kcu.column_name,
  ccu.table_schema AS foreign_table_schema,
  ccu.table_name AS foreign_table_name,
  ccu.column_name AS foreign_column_name,
  rc.update_rule,
  rc.delete_rule
FROM information_schema.table_constraints tc
JOIN information_schema.key_column_usage kcu
  ON tc.constraint_name = kcu.constraint_name
  AND tc.table_schema = kcu.table_schema
JOIN information_schema.constraint_column_usage ccu
  ON ccu.constraint_name = tc.constraint_name
  AND ccu.table_schema = tc.table_schema
JOIN information_schema.referential_constraints rc
  ON rc.constraint_name = tc.constraint_name
  AND rc.constraint_schema = tc.table_schema
WHERE tc.constraint_type = 'FOREIGN KEY'
  AND tc.table_schema = 'marketing'
ORDER BY tc.table_name, tc.constraint_name;
```

### Query 4: Indexes

```sql
-- Get all indexes for doctrine tables
SELECT
  schemaname,
  tablename,
  indexname,
  indexdef
FROM pg_indexes
WHERE schemaname IN ('marketing', 'shq')
  AND tablename IN (
    'company_master',
    'people_master',
    'company_slot',
    'company_intelligence',
    'people_intelligence'
  )
ORDER BY tablename, indexname;
```

### Query 5: Triggers

```sql
-- Get all triggers for doctrine tables
SELECT
  trigger_schema,
  trigger_name,
  event_manipulation,
  event_object_schema,
  event_object_table,
  action_timing,
  action_statement
FROM information_schema.triggers
WHERE event_object_schema IN ('marketing', 'shq')
  AND event_object_table IN (
    'company_master',
    'people_master',
    'company_slot',
    'company_intelligence',
    'people_intelligence'
  )
ORDER BY event_object_table, trigger_name;
```

### Query 6: Views

```sql
-- Get view definitions
SELECT
  table_schema,
  table_name,
  view_definition
FROM information_schema.views
WHERE table_schema IN ('marketing', 'shq')
  AND table_name IN ('outreach_history', 'audit_log', 'validation_queue')
ORDER BY table_schema, table_name;
```

---

## 📊 COMPLIANCE SUMMARY

### Expected Results (After Manual Execution)

| Table | Total Columns | Compliant | Non-Compliant | Missing Comments | Missing Indexes | Compliance % |
|-------|---------------|-----------|---------------|------------------|-----------------|--------------|
| company_master | 23 | ⏳ TBD | ⏳ TBD | ⏳ TBD | ⏳ TBD | ⏳ TBD |
| people_master | 27 | ⏳ TBD | ⏳ TBD | ⏳ TBD | ⏳ TBD | ⏳ TBD |
| company_slot | 12 | ⏳ TBD | ⏳ TBD | ⏳ TBD | ⏳ TBD | ⏳ TBD |
| company_intelligence | 13 | ⏳ TBD | ⏳ TBD | ⏳ TBD | ⏳ TBD | ⏳ TBD |
| people_intelligence | 13 | ⏳ TBD | ⏳ TBD | ⏳ TBD | ⏳ TBD | ⏳ TBD |
| outreach_history (view) | 15 | ⏳ TBD | ⏳ TBD | N/A | N/A | ⏳ TBD |
| shq.audit_log (view) | 13 | ⏳ TBD | ⏳ TBD | N/A | N/A | ⏳ TBD |
| shq.validation_queue (view) | 8 | ⏳ TBD | ⏳ TBD | N/A | N/A | ⏳ TBD |
| **TOTAL** | **~124** | **⏳ TBD** | **⏳ TBD** | **⏳ TBD** | **⏳ TBD** | **⏳ TBD** |

---

## 🚨 KNOWN SCHEMA DRIFT

### Critical Issues

#### 1. BIT Trigger Missing
**Table**: `marketing.company_intelligence`
**Expected**: `trg_after_company_intelligence_insert`
**Status**: ❌ NOT IMPLEMENTED
**Impact**: Company intelligence signals do not auto-trigger BIT campaigns

#### 2. Column Name Variations
**Issue**: Different naming conventions across migrations
- `company_master` uses `company_unique_id`
- `people_master` uses `people_barton_id` (expected: `unique_id`)
- `company_slot` uses `slot_barton_id` (expected: `unique_id`)

**Recommendation**: Standardize to `<table>_barton_id` format

#### 3. Generated Column Implementation
**Column**: `people_master.full_name`
**Expected**: `GENERATED ALWAYS AS (TRIM(first_name || ' ' || last_name)) STORED`
**Status**: ⏳ VERIFY if properly generated column or regular TEXT

---

## 🔧 AUTO-MIGRATION SQL (If Drift Detected)

**NOTE**: These migrations will ONLY be generated after manual verification reveals actual drift.

### Template: Add Missing Comments

```sql
-- Add comments to columns missing documentation
COMMENT ON COLUMN marketing.company_master.company_unique_id IS
  'Barton ID (Primary Key): Format 04.04.01.XX.XXXXX.XXX. Unique identifier for company records.';

COMMENT ON COLUMN marketing.company_master.company_name IS
  'Company name from intake source (COALESCE(company, company_name_for_emails)).';

-- Repeat for all columns missing comments...
```

### Template: Add Missing Indexes

```sql
-- Add missing indexes for performance
CREATE INDEX IF NOT EXISTS idx_company_master_company_name
  ON marketing.company_master(company_name);

CREATE INDEX IF NOT EXISTS idx_company_master_industry
  ON marketing.company_master(industry);

-- Repeat for all missing indexes...
```

### Template: Add Missing Constraints

```sql
-- Add missing CHECK constraints
ALTER TABLE marketing.company_master
  ADD CONSTRAINT company_master_barton_id_format
  CHECK (company_unique_id ~ '^04\.04\.01\.[0-9]{2}\.[0-9]{5}\.[0-9]{3}$');

-- Repeat for all missing constraints...
```

### Template: Create Missing Trigger

```sql
-- Create BIT trigger for company_intelligence
CREATE OR REPLACE FUNCTION marketing.after_company_intelligence_insert()
RETURNS TRIGGER AS $$
BEGIN
  -- Log to audit
  INSERT INTO marketing.unified_audit_log (...) VALUES (...);

  -- Trigger BIT if high-impact
  IF NEW.impact_level IN ('critical', 'high') AND NEW.confidence_score >= 0.70 THEN
    PERFORM marketing.composio_post_to_tool('bit_enqueue_signal', ...);
  END IF;

  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_after_company_intelligence_insert
  AFTER INSERT ON marketing.company_intelligence
  FOR EACH ROW
  EXECUTE FUNCTION marketing.after_company_intelligence_insert();
```

---

## 📋 EXECUTION INSTRUCTIONS

### Step 1: Execute Verification Queries

Run all 6 verification queries via Composio MCP:

```bash
curl -X POST http://localhost:3001/tool \
  -H "Content-Type: application/json" \
  -d '{
    "tool": "neon_execute_sql",
    "data": {
      "sql_query": "<QUERY_1_COLUMN_METADATA>"
    },
    "unique_id": "HEIR-2025-10-COLUMN-AUDIT-01",
    "process_id": "PRC-COLUMN-AUDIT-001",
    "orbt_layer": 3,
    "blueprint_version": "1.0"
  }'
```

Repeat for all 6 queries.

### Step 2: Compare Results

1. Export query results to CSV/JSON
2. Compare against expected schema in this report
3. Identify mismatches (column name, type, nullability, default, constraint)
4. Mark compliance status (✅ / ⚠️ / ❌)

### Step 3: Calculate Statistics

```javascript
const totalColumns = 124;
const compliantColumns = <COUNT_FROM_RESULTS>;
const nonCompliantColumns = <COUNT_FROM_RESULTS>;
const missingComments = <COUNT_FROM_RESULTS>;
const missingIndexes = <COUNT_FROM_RESULTS>;

const compliancePercentage = (compliantColumns / totalColumns) * 100;
```

### Step 4: Generate Migration SQL

If non-compliant > 0:
1. Use templates above to generate migration SQL
2. Review and test in staging
3. Apply to production after approval

### Step 5: Update This Report

Replace ⏳ VERIFY status with actual results:
- ✅ COMPLIANT
- ⚠️ WARNING (minor drift, non-breaking)
- ❌ FAIL (major drift, breaking change)

---

## ✅ FINAL COMPLIANCE SCORE

**Overall Column Compliance**: ⏳ **PENDING MANUAL VERIFICATION**

**Expected After Verification**:
- Total Columns: ~124
- Compliant: TBD
- Non-Compliant: TBD
- Compliance %: TBD

**Pass Criteria**: ≥ 95% compliance

---

**Report Date**: 2025-10-22
**Report Version**: 1.0
**Next Review**: After manual verification complete
**Status**: ⏳ AWAITING MANUAL EXECUTION OF VERIFICATION QUERIES

---

## 📚 REFERENCES

**Doctrine Files**:
- `analysis/ENRICHMENT_DATA_SCHEMA.md`
- `apps/outreach-process-manager/migrations/create_company_master.sql`
- `apps/outreach-process-manager/migrations/create_people_master.sql`
- `apps/outreach-process-manager/migrations/create_company_slot.sql`
- `apps/outreach-process-manager/migrations/2025-10-22_create_marketing_company_intelligence.sql`
- `apps/outreach-process-manager/migrations/2025-10-22_create_marketing_people_intelligence.sql`

**Audit Reports**:
- `analysis/FINAL_PRE_FLIGHT_AUDIT_OUTREACH_CORE.md`
- `analysis/BIT_PLE_PRODUCTION_READINESS_REPORT.md`
- `analysis/FINAL_SCHEMA_COMPLIANCE_REPORT.md`
