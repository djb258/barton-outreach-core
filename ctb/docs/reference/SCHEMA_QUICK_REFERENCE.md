# Neon Schema - Quick Reference

**For Configuration Adjustments** | 2025-11-06

---

## 🎯 Primary Tables

### marketing.company_master (Barton ID: 04.04.01)
```sql
company_unique_id TEXT PRIMARY KEY
company_name TEXT NOT NULL
website_url TEXT NOT NULL
industry TEXT
employee_count INTEGER
linkedin_url TEXT
address_* (street, city, state, zip, country)
founded_year INTEGER
keywords TEXT[]
description TEXT
source_system TEXT NOT NULL
created_at, updated_at TIMESTAMPTZ
```

### marketing.people_master (Barton ID: 04.04.02)
```sql
unique_id TEXT PRIMARY KEY
company_unique_id TEXT NOT NULL (→ company_master)
company_slot_unique_id TEXT NOT NULL (→ company_slot)
first_name, last_name TEXT NOT NULL
full_name TEXT GENERATED
title, seniority, department TEXT
email TEXT (validated)
work_phone_e164, personal_phone_e164 TEXT
linkedin_url, twitter_url, facebook_url TEXT
bio TEXT
skills TEXT[]
education TEXT
certifications TEXT[]
source_system TEXT NOT NULL
created_at, updated_at TIMESTAMPTZ
```

### marketing.company_slot (Barton ID: 04.04.05)
```sql
company_slot_unique_id TEXT PRIMARY KEY
company_unique_id TEXT NOT NULL (→ company_master)
slot_type TEXT NOT NULL CHECK ('CEO', 'CFO', 'HR')
person_unique_id TEXT (→ people_master)
is_filled BOOLEAN DEFAULT FALSE
filled_at TIMESTAMPTZ
last_refreshed_at TIMESTAMPTZ
created_at, updated_at TIMESTAMPTZ
```

---

## 📊 Intelligence Tables

### marketing.company_intelligence
```sql
intelligence_id SERIAL PRIMARY KEY
company_unique_id TEXT NOT NULL
intelligence_type TEXT NOT NULL (news/signal/event/score)
source, title, description, url TEXT
score NUMERIC(5,2)
detected_at TIMESTAMPTZ
payload JSONB
```

### marketing.people_intelligence
```sql
intelligence_id SERIAL PRIMARY KEY
person_unique_id TEXT NOT NULL
intelligence_type TEXT NOT NULL
previous_value, new_value TEXT
detected_at TIMESTAMPTZ
payload JSONB
```

---

## 📥 Data Ingestion

### intake.raw_loads (RLS protected)
```sql
load_id BIGSERIAL PRIMARY KEY
batch_id TEXT NOT NULL
source TEXT NOT NULL
raw_data JSONB NOT NULL
status TEXT DEFAULT 'pending' (pending/promoted/failed/duplicate)
created_at, promoted_at TIMESTAMPTZ
metadata JSONB
```

### vault.contacts (RLS protected)
```sql
contact_id BIGSERIAL PRIMARY KEY
email TEXT UNIQUE NOT NULL
name, phone, company, title TEXT
source TEXT NOT NULL
tags JSONB DEFAULT '[]'
custom_fields JSONB DEFAULT '{}'
score NUMERIC(5,2) DEFAULT 0
status TEXT DEFAULT 'active'
created_at, updated_at, last_activity_at TIMESTAMPTZ
```

---

## 🔧 Utility Tables

### public.shq_error_log
```sql
id SERIAL PRIMARY KEY
unique_id TEXT UNIQUE
error_type, error_message, stack_trace TEXT
context JSONB
severity TEXT (critical/high/medium/low)
resolved BOOLEAN DEFAULT FALSE
created_at, updated_at, resolved_at TIMESTAMPTZ
```

### public.linkedin_refresh_jobs
```sql
job_id SERIAL PRIMARY KEY
person_unique_id TEXT NOT NULL
linkedin_url TEXT NOT NULL
apify_run_id TEXT
status TEXT DEFAULT 'pending'
requested_at, started_at, completed_at TIMESTAMPTZ
result_data JSONB
error_message TEXT
```

### public.actor_usage_log
```sql
log_id SERIAL PRIMARY KEY
actor_id TEXT NOT NULL
run_id TEXT NOT NULL
started_at, finished_at TIMESTAMPTZ
status TEXT (SUCCEEDED/FAILED/TIMED-OUT)
compute_units NUMERIC(10,4)
dataset_items INTEGER
error_message TEXT
metadata JSONB
```

### marketing.pipeline_events
```sql
event_id SERIAL PRIMARY KEY
event_type TEXT NOT NULL
entity_type TEXT (company/person)
entity_id TEXT (Barton ID)
event_data JSONB
created_at TIMESTAMPTZ
```

---

## 🔑 Key Relationships

```
company_master (04.04.01)
    ├── company_slot (04.04.05) [1:3 - CEO/CFO/HR]
    │   └── people_master (04.04.02) [assigned to slot]
    ├── company_intelligence [1:many]
    └── pipeline_events [1:many]

people_master (04.04.02)
    ├── people_intelligence [1:many]
    ├── linkedin_refresh_jobs [1:many]
    └── pipeline_events [1:many]

intake.raw_loads
    ↓ f_ingest_json()
    ↓ validation
    ↓ f_promote_contacts()
vault.contacts
    ↓ manual promotion
marketing.company_master + people_master
```

---

## 📝 Common Adjustments Checklist

### Adding New Column
```sql
-- 1. Add column
ALTER TABLE marketing.company_master
ADD COLUMN new_column TEXT;

-- 2. Add index if searchable
CREATE INDEX idx_company_master_new_column
ON marketing.company_master(new_column);

-- 3. Add comment
COMMENT ON COLUMN marketing.company_master.new_column IS 'Description';
```

### Adding New Table
```sql
-- 1. Create table with Barton ID
CREATE TABLE marketing.new_table (
    unique_id TEXT PRIMARY KEY,
    -- Add columns
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    CONSTRAINT new_table_barton_id_format
        CHECK (unique_id ~ '^04\.04\.XX\.[0-9]{2}\.[0-9]{5}\.[0-9]{3}$')
);

-- 2. Add indexes
CREATE INDEX idx_new_table_column ON marketing.new_table(column);

-- 3. Add updated_at trigger
CREATE TRIGGER trigger_new_table_updated_at
    BEFORE UPDATE ON marketing.new_table
    FOR EACH ROW
    EXECUTE FUNCTION trigger_updated_at();
```

### Modifying Constraint
```sql
-- 1. Drop old constraint
ALTER TABLE marketing.people_master
DROP CONSTRAINT IF EXISTS old_constraint_name;

-- 2. Add new constraint
ALTER TABLE marketing.people_master
ADD CONSTRAINT new_constraint_name
    CHECK (condition);
```

### Adding Foreign Key
```sql
ALTER TABLE marketing.child_table
ADD CONSTRAINT fk_child_parent
FOREIGN KEY (parent_id)
REFERENCES marketing.parent_table(unique_id)
ON DELETE CASCADE;
```

---

## 🎯 Ready for Your Configuration

Tell me what you'd like to adjust:

1. **Add/Remove Columns** - Which table? What columns?
2. **New Tables** - What data? What relationships?
3. **Modify Constraints** - Which validation rules?
4. **Add Indexes** - For which queries?
5. **Create Views** - What data aggregations?
6. **New Functions** - What business logic?

---

**Schema Files**:
- Full Documentation: [CURRENT_NEON_SCHEMA.md](./CURRENT_NEON_SCHEMA.md)
- Migration Files: `ctb/data/migrations/outreach-process-manager/`
- Schema Map: `ctb/docs/schema_map.json`

**Total Tables**: 15+ production tables
**Total Indexes**: 50+ indexes
**Total Functions**: 10+ functions
**RLS Protected**: 2 tables (intake.raw_loads, vault.contacts)
