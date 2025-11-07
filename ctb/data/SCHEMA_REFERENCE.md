# Neon Database Schema Reference

**Database**: Marketing DB
**Host**: ep-ancient-waterfall-a42vy0du-pooler.us-east-1.aws.neon.tech
**Last Updated**: 2025-11-07
**Total Schemas**: 11
**Total Tables**: 64

---

## 📊 Schema Overview

### Production Schemas (Active)

#### 1. **marketing** Schema (Primary Data)

**company_master** (453 rows)
- Primary company records with 29 columns
- Includes company_name, industry, employee_count, revenue, website
- 5 indexes for performance
- Main source of truth for company data

**company_slots** (1,359 rows)
- Executive position tracking (CEO, CFO, HR, etc.)
- Links companies to people via slots
- 1 index, 1 foreign key to company_master

**people_master** (170 rows)
- Contact/executive records with 29 columns
- Includes full_name, email, linkedin_url, title, phone
- 10 indexes for fast lookups
- Central people database

**people_resolution_queue** (1,206 rows)
- Duplicate detection and merging queue
- 17 columns for resolution tracking
- 6 indexes, 2 foreign keys

**pipeline_events** (1,890 rows)
- Event tracking for data pipeline
- 8 columns: event_id, company_unique_id, event_type, payload, created_at
- 3 indexes for fast queries

**pipeline_errors** (0 rows)
- Error tracking for pipeline operations
- 11 columns including error_code, message, severity, resolution_status
- 5 indexes

**contact_enrichment** (0 rows)
- Enrichment job tracking
- Links to external APIs (Apify, Abacus, Firecrawl)
- 11 columns, 3 indexes

**email_verification** (0 rows)
- Email verification results
- 8 columns, 3 indexes, 1 foreign key

**message_key_reference** (8 rows)
- Message tracking for outreach campaigns
- 13 columns, 4 indexes

---

#### 2. **intake** Schema (Data Ingestion)

**company_raw_intake** (453 rows)
- CSV upload staging area
- 25 columns for raw company data
- No validation, just raw ingestion
- Promoted to marketing.company_master after validation

---

#### 3. **bit** Schema (Buyer Intent Tracking)

**bit_signal** (0 rows)
- Buyer intent signals
- 11 columns: signal_id, company_unique_id, signal_type, score, detected_at
- 6 indexes

**bit_company_score** (0 rows)
- Aggregated company intent scores
- 9 columns, 4 indexes

**bit_contact_score** (0 rows)
- Individual contact intent scores
- 10 columns, 4 indexes

---

#### 4. **ple** Schema (Product-Led Enrichment)

**ple_cycle** (0 rows)
- Enrichment cycle tracking
- 16 columns, 6 indexes

**ple_step** (0 rows)
- Individual enrichment steps
- 16 columns, 5 indexes, 1 foreign key to ple_cycle

**ple_log** (0 rows)
- Enrichment operation logs
- 8 columns, 5 indexes, 1 foreign key

---

#### 5. **public** Schema (System Tables)

**shq_validation_log** (0 rows)
- Validation operation logs
- 9 columns, 1 index

---

### Archive Schemas

#### 6. **archive** Schema (46 tables)

Contains archived/deprecated tables from previous migrations:
- Old company, contact, and people tables
- Historical marketing tables
- Archived validation and enrichment tables
- Storage evaluation data (41,551+ rows of geographic data)

Notable archived tables:
- `public_storage_evaluation_state_county_zip_v2` - 41,551 rows of location data
- `public_storage_evaluation_focus_states` - 6,337 rows
- `shq_schema_registry` - 688 rows of schema metadata

---

### Utility Schemas

#### 7. **BIT** Schema (empty - uppercase variant)
- Empty schema, possibly for future use

#### 8. **PLE** Schema (empty - uppercase variant)
- Empty schema, possibly for future use

#### 9. **company** Schema (empty)
- Reserved for future use

#### 10. **people** Schema (empty)
- Reserved for future use

#### 11. **neon_auth** Schema

**users_sync** (0 rows)
- User authentication sync table
- 7 columns, 2 indexes

---

## 🔗 Key Relationships

### Company → People Flow

```
intake.company_raw_intake (453 rows)
    ↓ [validation & promotion]
marketing.company_master (453 rows)
    ↓ [slot creation]
marketing.company_slots (1,359 rows)
    ↓ [filled with]
marketing.people_master (170 rows)
```

### Enrichment Flow

```
marketing.people_master
    ↓ [enrichment needed]
marketing.contact_enrichment (job tracking)
    ↓ [external APIs: Apify, Abacus, Firecrawl]
marketing.people_master (updated with enriched data)
```

### Intent Tracking Flow

```
bit.bit_signal (detected signals)
    ↓ [aggregation]
bit.bit_company_score (company-level scores)
bit.bit_contact_score (contact-level scores)
```

---

## 📈 Data Volume Summary

| Schema | Tables | Total Rows | Status |
|--------|--------|-----------|--------|
| **marketing** | 9 | ~5,087 | ✅ Active |
| **intake** | 1 | 453 | ✅ Active |
| **bit** | 3 | 0 | 🔄 Ready |
| **ple** | 3 | 0 | 🔄 Ready |
| **archive** | 46 | ~48,000+ | 📦 Archived |
| **public** | 1 | 0 | ✅ Active |
| **neon_auth** | 1 | 0 | ✅ Active |
| **Others** | 0 | 0 | 📝 Reserved |

---

## 🔍 Index Summary

**Total Indexes Across Database**: 200+

Most heavily indexed tables:
- `marketing.people_master` - 10 indexes
- `archive.public_storage_evaluation_state_county_zip_v2` - Multiple indexes for location queries

---

## 🛠️ Schema Management

### Update Schema Documentation

```bash
# Run schema export script
python ctb/ops/scripts/export-neon-schema.py

# Or via npm
npm run schema:export
```

This will:
1. Connect to Neon database
2. Query all schemas, tables, columns, indexes, foreign keys
3. Generate JSON schema maps:
   - `ctb/docs/schema_map.json` (primary)
   - `.gitingest/schema_map.json` (secondary)
4. Display comprehensive summary

### View Schema Map

```bash
# Pretty-print the schema map
cat ctb/docs/schema_map.json | jq .

# View specific schema
cat ctb/docs/schema_map.json | jq '.schemas.marketing'
```

---

## 📝 Schema Design Notes

### Barton ID Format

All tables use Barton Doctrine ID format: `NN.NN.NN.NN.NNNNN.NNN`

Examples:
- Company Master: `04.04.02.04.30000.###`
- Company Slots: `04.04.02.04.10000.###`
- People Master: `04.04.02.04.20000.###`
- Error Log: `04.04.02.04.40000.###`

### Column Naming Convention

- **Primary Keys**: `{table}_id` or `unique_id`
- **Foreign Keys**: `{referenced_table}_unique_id`
- **Timestamps**: `created_at`, `updated_at`, `deleted_at`
- **Status Fields**: `is_active`, `is_verified`, `is_filled`

### Triggers

- Auto-update `updated_at` triggers on most tables
- Validation triggers on intake tables
- Event logging triggers on critical tables

---

## 🔒 Security Notes

- All connections require SSL (`sslmode=require`)
- Row-level security (RLS) enabled on sensitive tables
- API keys and credentials stored in environment variables
- Database credentials never committed to git

---

## 📚 Related Documentation

- **Full Schema Map JSON**: `ctb/docs/schema_map.json`
- **SQL Schema Files**: `ctb/data/infra/*.sql`
- **Migration Files**: `ctb/data/infra/migrations/*.sql`
- **Environment Setup**: `.env.example`
- **Grafana Dashboards**: `grafana/provisioning/dashboards/`

---

**For Questions**: Refer to schema_map.json for complete column definitions, types, and constraints.
