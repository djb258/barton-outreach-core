# Barton Doctrine Pipeline - Step 4 Promotion Console

## Pipeline Overview

The Barton Doctrine Pipeline is a 4-step data ingestion and validation process that transforms raw source data into clean, validated master records.

### ASCII Pipeline Diagram

```
[ Source CSVs / Apify JSON / Apollo ]
                |
                v
        Mapping Application
     (Headers → Master File)
                |
                v
   [Optional Staging Tables (TEXT)]
                |
                v
         Step 2A Validators
   - Companies → company_raw_intake
   - People → people_raw_intake
                |
        +-------------------+
        |    Failed Rows    |
        v                   v
 Step 2B Enrichment      Audit Logs
 (Repair/Infer Fields)   (Full Trace)
                |
                v
        Step 3 Adjuster Console
  (Human Review + Corrections)
                |
                v
        Step 4 Promotion Console
   - Validated Rows → Master Tables
   - company_master + people_master
   - Audit trail for every promotion
```

## Step 4 Promotion Console Implementation

### Core Components

1. **Database Master Tables**
   - `marketing.company_master` - Final destination for validated company records
   - `marketing.people_master` - Final destination for validated people records

2. **API Endpoints**
   - `/api/promotion-eligible` - Get counts of records ready for promotion
   - `/api/promote` - Execute promotion batch with full audit logging

3. **UI Components**
   - `PromotionConsole` - Main console interface
   - `PromotionSummaryCard` - Shows promotion statistics
   - `PromotionResultsTable` - Displays batch promotion results

### Barton Doctrine Rules

✅ **Rule 1: Validation Required**
- Only records with `validation_status = 'passed'` can be promoted
- Records must have successfully completed Steps 2A, 2B (if needed), and 3 (if needed)

✅ **Rule 2: Barton ID Preservation**
- All Barton IDs remain intact during promotion
- Company IDs: `04.04.01.XX.XXXXX.XXX`
- People IDs: `04.04.02.XX.XXXXX.XXX`

✅ **Rule 3: Audit Trail**
- Every promotion attempt logged to `company_audit_log` or `people_audit_log`
- Includes full record snapshot, timestamps, and batch tracking

✅ **Rule 4: MCP-Only Execution**
- All database operations use Standard Composio MCP bridge
- No direct Neon database connections

✅ **Rule 5: Atomic Batch Processing**
- Promotions processed in transactions
- Rollback on any failure to maintain consistency

### Data Flow

```
Step 4 Promotion Process:

1. Query Eligible Records
   company_raw_intake WHERE validation_status = 'passed'
   AND (promotion_status IS NULL OR != 'promoted')

2. Execute Promotion Batch
   FOR EACH eligible_record:
     a) Copy to company_master/people_master
     b) Log promotion in audit table
     c) Update intake record: promotion_status = 'promoted'

3. Handle Results
   - Success: Record promoted, audit logged
   - Failure: Batch rolled back, errors reported
```

### Master Table Schema

#### company_master
```sql
CREATE TABLE marketing.company_master (
    company_unique_id TEXT PRIMARY KEY,      -- Barton ID (immutable)
    company_name TEXT NOT NULL,
    website_url TEXT NOT NULL,
    industry TEXT,
    employee_count INTEGER,
    -- ... additional fields
    promoted_from_intake_at TIMESTAMPTZ,     -- Promotion timestamp
    promotion_audit_log_id INTEGER           -- Reference to audit log
);
```

#### people_master
```sql
CREATE TABLE marketing.people_master (
    unique_id TEXT PRIMARY KEY,              -- Barton ID (immutable)
    company_unique_id TEXT NOT NULL,
    company_slot_unique_id TEXT NOT NULL,
    first_name TEXT NOT NULL,
    last_name TEXT NOT NULL,
    -- ... additional fields
    promoted_from_intake_at TIMESTAMPTZ,     -- Promotion timestamp
    promotion_audit_log_id INTEGER           -- Reference to audit log
);
```

## JSON Blueprint

```json
{
  "pipeline": {
    "step_1_ingest": {
      "sources": ["CSV (DBeaver)", "Apify JSON", "Apollo"],
      "output": "Master File",
      "description": "Raw data collection and initial formatting"
    },
    "step_2A_validate": {
      "inputs": ["Master File"],
      "outputs": {
        "company": "marketing.company_raw_intake",
        "people": "marketing.people_raw_intake"
      },
      "audit_logs": ["company_audit_log", "people_audit_log"],
      "validation_rules": [
        "Required field validation",
        "Data type validation",
        "Format validation (emails, phones, URLs)",
        "Barton ID assignment and validation"
      ]
    },
    "step_2B_enrich": {
      "inputs": ["failed validation records"],
      "actions": [
        "repair fields",
        "normalize data",
        "infer missing data",
        "external API enrichment"
      ],
      "outputs": "re-validated intake rows",
      "audit_table": "enrichment_audit_log"
    },
    "step_3_adjust": {
      "console": "Adjuster Console",
      "inputs": ["failed enrichment records"],
      "actions": [
        "manual field corrections",
        "audit before/after values",
        "trigger re-validation"
      ],
      "guardrails": [
        "Barton IDs cannot be modified",
        "All changes logged to audit tables"
      ]
    },
    "step_4_promote": {
      "console": "Promotion Console",
      "inputs": ["validated records only"],
      "targets": {
        "company": "marketing.company_master",
        "people": "marketing.people_master"
      },
      "process": [
        "Select records with validation_status='passed'",
        "Copy to master table with intact Barton IDs",
        "Log promotion to audit table",
        "Update intake record promotion_status"
      ],
      "guardrails": [
        "Only validated records can be promoted",
        "Barton IDs remain immutable",
        "Full audit trail required",
        "Atomic batch processing with rollback"
      ]
    }
  },
  "master_tables": {
    "company_master": {
      "primary_key": "company_unique_id",
      "barton_id_format": "04.04.01.XX.XXXXX.XXX",
      "source": "company_raw_intake",
      "constraints": [
        "company_name NOT NULL",
        "website_url NOT NULL",
        "employee_count >= 0",
        "founded_year BETWEEN 1800 AND CURRENT_YEAR"
      ]
    },
    "people_master": {
      "primary_key": "unique_id",
      "barton_id_format": "04.04.02.XX.XXXXX.XXX",
      "source": "people_raw_intake",
      "constraints": [
        "first_name NOT NULL",
        "last_name NOT NULL",
        "email format validation",
        "company_unique_id reference"
      ]
    }
  },
  "audit_system": {
    "promotion_tracking": {
      "company_audit_log": {
        "action": "promote",
        "status": ["success", "failed"],
        "metadata": ["batch_id", "session_id", "target_table"]
      },
      "people_audit_log": {
        "action": "promote",
        "status": ["success", "failed"],
        "metadata": ["batch_id", "session_id", "target_table"]
      }
    },
    "traceability": "Full record snapshots in audit logs"
  }
}
```

## Implementation Checklist

- [x] **Database Migrations**
  - [x] `create_company_master.sql`
  - [x] `create_people_master.sql`

- [x] **API Endpoints**
  - [x] `/api/promotion-eligible.ts` - Get eligible record counts
  - [x] `/api/promote.ts` - Execute promotion batches

- [x] **UI Components**
  - [x] `pages/promotion-console/index.jsx` - Main console
  - [x] `PromotionSummaryCard.jsx` - Statistics display
  - [x] `PromotionResultsTable.jsx` - Batch results

- [x] **Doctrine Compliance**
  - [x] Only validated records can be promoted
  - [x] Barton ID preservation during promotion
  - [x] Full audit logging for all promotions
  - [x] Standard Composio MCP usage
  - [x] Atomic batch processing with rollback

## Success Metrics

1. **Data Quality**: 100% of promoted records have validation_status='passed'
2. **Traceability**: Every promotion logged with full audit trail
3. **ID Integrity**: Zero Barton ID changes during promotion
4. **Batch Reliability**: Failed batches rolled back completely
5. **Master Table Accuracy**: Promoted records match intake source data

The Step 4 Promotion Console completes the Barton Doctrine pipeline by moving validated, clean data into the final master tables while maintaining complete traceability and audit compliance.