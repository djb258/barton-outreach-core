# Appointment History Ingest Specification

**Lane**: A - Appointment Reactivation
**Target Table**: `sales.appointment_history`
**Status**: FACT TABLE (Write-Once)

---

## Overview

This document specifies the Excel/CSV format for ingesting past appointment data into the Appointment Reactivation pipeline.

**IMPORTANT**: This is a FACT table. Records cannot be updated or deleted after insertion. All changes must be new records.

---

## Column Mapping

| Excel Column | DB Column | Type | Required | Notes |
|--------------|-----------|------|----------|-------|
| `company_id` | `company_id` | UUID | No | FK to company_master if available |
| `people_id` | `people_id` | UUID | No | FK to people_master if available |
| `outreach_id` | `outreach_id` | UUID | No | FK to outreach if available |
| `meeting_date` | `meeting_date` | DATE | **Yes** | Format: YYYY-MM-DD |
| `meeting_type` | `meeting_type` | ENUM | **Yes** | See enum values below |
| `meeting_outcome` | `meeting_outcome` | ENUM | **Yes** | See enum values below |
| `stalled_reason` | `stalled_reason` | TEXT | Conditional | Required if outcome = 'stalled' |
| `source` | `source` | ENUM | No | Default: 'manual' |
| `source_record_id` | `source_record_id` | TEXT | No | External ID from CRM/calendar |

---

## Enum Values

### `meeting_type`
| Value | Description |
|-------|-------------|
| `discovery` | Initial discovery call |
| `systems` | Systems/process review meeting |
| `numbers` | Numbers/pricing discussion |
| `other` | Other meeting type |

### `meeting_outcome`
| Value | Description |
|-------|-------------|
| `progressed` | Moved to next stage |
| `stalled` | Stuck, no movement (requires stalled_reason) |
| `ghosted` | Lost contact, no response |
| `lost` | Closed-lost, explicit rejection |

### `source`
| Value | Description |
|-------|-------------|
| `calendar` | Imported from calendar sync |
| `crm` | Imported from CRM (HubSpot, ActiveCampaign, etc.) |
| `manual` | Manual entry via Excel/CSV |

---

## Primary Key Generation

The `appointment_uid` is generated automatically using:

```
{company_id}|{people_id}|{meeting_date}
```

Example: `550e8400-e29b-41d4-a716-446655440000|661e8400-e29b-41d4-a716-446655440001|2025-06-15`

**Deduplication**: If an appointment with the same company_id, people_id, and meeting_date already exists, the insert will fail (duplicate key). This prevents accidental re-imports.

---

## Sample Excel Template

| company_id | people_id | meeting_date | meeting_type | meeting_outcome | stalled_reason | source |
|------------|-----------|--------------|--------------|-----------------|----------------|--------|
| 550e8400-e29b-41d4-a716-446655440000 | 661e8400-e29b-41d4-a716-446655440001 | 2025-06-15 | discovery | stalled | Decision maker on vacation | crm |
| 550e8400-e29b-41d4-a716-446655440002 | 661e8400-e29b-41d4-a716-446655440003 | 2025-07-20 | systems | ghosted | | crm |
| 550e8400-e29b-41d4-a716-446655440004 | 661e8400-e29b-41d4-a716-446655440005 | 2025-08-10 | numbers | lost | | manual |

---

## Validation Rules

1. **meeting_date**: Must be valid date in YYYY-MM-DD format
2. **meeting_type**: Must be one of: discovery, systems, numbers, other
3. **meeting_outcome**: Must be one of: progressed, stalled, ghosted, lost
4. **stalled_reason**: REQUIRED if meeting_outcome = 'stalled'
5. **source**: If blank, defaults to 'manual'
6. **UUIDs**: If company_id or people_id provided, must be valid UUID format

---

## Ingest Script Usage

```bash
# Using the ingest script
doppler run -- node scripts/ingest/appointment_history_ingest.cjs <excel_file.xlsx>

# With explicit source override
doppler run -- node scripts/ingest/appointment_history_ingest.cjs <excel_file.xlsx> --source=crm
```

---

## Post-Ingest: BIT Intent Initialization

After ingest, initialize reactivation intent records:

```sql
-- Initialize BIT intent for all new appointments without intent
INSERT INTO bit.reactivation_intent (appointment_uid)
SELECT ah.appointment_uid
FROM sales.appointment_history ah
LEFT JOIN bit.reactivation_intent ri ON ah.appointment_uid = ri.appointment_uid
WHERE ri.reactivation_bit_id IS NULL;
```

Or use the helper function:

```sql
SELECT bit.fn_init_reactivation_intent(appointment_uid)
FROM sales.appointment_history
WHERE meeting_outcome IN ('stalled', 'ghosted');
```

---

## Audit Trail

All inserts are automatically logged to `shq.audit_log`:

```sql
SELECT * FROM shq.audit_log
WHERE schema_name = 'sales'
  AND table_name = 'appointment_history'
ORDER BY performed_at DESC;
```

---

## Doctrine Compliance

- **Immutable Fact Table**: Write-once enforced via trigger
- **No Scores in Fact Table**: Intent/scoring lives in `bit.reactivation_intent`
- **Full Auditability**: All inserts logged to `shq.audit_log`
- **Kill Switch Ready**: `eligibility_status` in BIT table supports exclusions

---

*Last Updated: 2026-01-28*
