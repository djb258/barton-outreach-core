# Fractional CFO Partner Ingest Specification

**Lane**: B - Fractional CFO Partner Outreach
**Target Tables**:
- `partners.fractional_cfo_master` (Master records, updateable)
- `partners.partner_appointments` (Fact table, write-once)

---

## Overview

This document specifies the Excel/CSV format for ingesting fractional CFO partner data into the Partner Outreach pipeline.

**IMPORTANT**:
- `fractional_cfo_master` allows updates (status changes, contact info updates)
- `partner_appointments` is a FACT table - write-once enforced

---

## Part 1: Fractional CFO Master

### Column Mapping

| Excel Column | DB Column | Type | Required | Notes |
|--------------|-----------|------|----------|-------|
| `firm_name` | `firm_name` | TEXT | **Yes** | Partner firm name |
| `primary_contact_name` | `primary_contact_name` | TEXT | **Yes** | Main contact at firm |
| `linkedin_url` | `linkedin_url` | TEXT | No | Must be valid LinkedIn URL |
| `email` | `email` | TEXT | No | Must be valid email format |
| `geography` | `geography` | TEXT | No | e.g., 'Mid-Atlantic', 'Northeast' |
| `niche_focus` | `niche_focus` | TEXT | No | e.g., 'Healthcare', 'SaaS' |
| `source` | `source` | TEXT | **Yes** | Where we found them |
| `status` | `status` | ENUM | No | Default: 'prospect' |

### Status Enum Values

| Value | Description |
|-------|-------------|
| `prospect` | Initial identification (default) |
| `contacted` | Outreach initiated |
| `engaged` | Active dialogue ongoing |
| `partner` | Formal partnership established |

### Sample Excel Template

| firm_name | primary_contact_name | linkedin_url | email | geography | niche_focus | source |
|-----------|---------------------|--------------|-------|-----------|-------------|--------|
| Strategic CFO Partners | John Smith | https://linkedin.com/in/johnsmith | john@strategiccfo.com | Mid-Atlantic | Healthcare | LinkedIn |
| Fractional Finance Group | Jane Doe | https://linkedin.com/in/janedoe | jane@fracfin.com | Northeast | SaaS | Referral |
| Outsourced CFO Services | Bob Johnson | | bob@outsourcedcfo.com | National | Manufacturing | Conference |

### Validation Rules

1. **firm_name**: Required, non-empty
2. **primary_contact_name**: Required, non-empty
3. **linkedin_url**: If provided, must start with `https://linkedin.com/` or `https://www.linkedin.com/`
4. **email**: If provided, must match standard email format
5. **source**: Required (e.g., 'LinkedIn', 'Referral', 'Conference', 'Cold Outreach')
6. **status**: If blank, defaults to 'prospect'

---

## Part 2: Partner Appointments

### Column Mapping

| Excel Column | DB Column | Type | Required | Notes |
|--------------|-----------|------|----------|-------|
| `fractional_cfo_id` | `fractional_cfo_id` | UUID | **Yes** | FK to fractional_cfo_master |
| `meeting_date` | `meeting_date` | DATE | **Yes** | Format: YYYY-MM-DD |
| `meeting_type` | `meeting_type` | ENUM | **Yes** | intro or followup |
| `outcome` | `outcome` | ENUM | **Yes** | warm, neutral, or cold |
| `notes` | `notes` | TEXT | No | Meeting notes/summary |

### Meeting Type Enum

| Value | Description |
|-------|-------------|
| `intro` | Introduction call |
| `followup` | Follow-up meeting |

### Meeting Outcome Enum

| Value | Description |
|-------|-------------|
| `warm` | Positive reception, interest shown |
| `neutral` | No clear direction either way |
| `cold` | Negative reception, unlikely to progress |

### Primary Key Generation

The `partner_appointment_uid` is generated using:

```
{fractional_cfo_id}|{meeting_date}|{sequence}
```

Example: `550e8400-e29b-41d4-a716-446655440000|2025-06-15|1`

### Sample Excel Template

| fractional_cfo_id | meeting_date | meeting_type | outcome | notes |
|-------------------|--------------|--------------|---------|-------|
| 550e8400-e29b-41d4-a716-446655440000 | 2025-06-15 | intro | warm | Interested in healthcare vertical |
| 550e8400-e29b-41d4-a716-446655440000 | 2025-07-01 | followup | warm | Discussing referral agreement |
| 661e8400-e29b-41d4-a716-446655440001 | 2025-06-20 | intro | neutral | Busy this quarter, revisit Q4 |

---

## Ingest Script Usage

```bash
# Ingest partner master records
doppler run -- node scripts/ingest/fractional_cfo_ingest.cjs partners <excel_file.xlsx>

# Ingest partner appointments
doppler run -- node scripts/ingest/fractional_cfo_ingest.cjs appointments <excel_file.xlsx>
```

---

## Post-Ingest: BIT Intent Initialization

After ingesting partners, initialize intent records:

```sql
-- Initialize BIT intent for all new partners without intent
INSERT INTO bit.partner_intent (fractional_cfo_id, status)
SELECT fcm.fractional_cfo_id, 'pending'
FROM partners.fractional_cfo_master fcm
LEFT JOIN bit.partner_intent pi ON fcm.fractional_cfo_id = pi.fractional_cfo_id
WHERE pi.partner_bit_id IS NULL;
```

Or use the helper function:

```sql
SELECT bit.fn_init_partner_intent(fractional_cfo_id)
FROM partners.fractional_cfo_master
WHERE status = 'prospect';
```

---

## Workflow: Partner Lifecycle

```
1. PROSPECT (Initial import)
   ↓
2. CONTACTED (First outreach sent)
   ↓
3. ENGAGED (Active dialogue)
   ↓
4. PARTNER (Formal agreement)
```

### Status Transitions

```sql
-- Move partner from prospect to contacted
UPDATE partners.fractional_cfo_master
SET status = 'contacted'
WHERE fractional_cfo_id = $1
AND status = 'prospect';

-- Move partner to engaged
UPDATE partners.fractional_cfo_master
SET status = 'engaged'
WHERE fractional_cfo_id = $1
AND status = 'contacted';
```

---

## Views for Outreach

### LinkedIn Outreach Queue

```sql
SELECT * FROM bit.v_partner_outreach_ready
WHERE linkedin_url IS NOT NULL
  AND partner_status = 'prospect';
```

### Email Outreach Queue

```sql
SELECT * FROM bit.v_partner_outreach_ready
WHERE email IS NOT NULL
  AND partner_status IN ('prospect', 'contacted');
```

---

## Audit Trail

All operations are logged to `shq.audit_log`:

```sql
-- View partner insert/update history
SELECT * FROM shq.audit_log
WHERE schema_name = 'partners'
ORDER BY performed_at DESC;
```

---

## Doctrine Compliance

- **Master Table Updateable**: Status changes allowed with full audit
- **Appointment Facts Immutable**: Write-once enforced via trigger
- **Scores in BIT Only**: Leverage scores live in `bit.partner_intent`
- **Full Auditability**: All changes logged to `shq.audit_log`
- **Kill Switch Ready**: Intent status supports pausing/completing

---

## Geography Standardization

Recommended geography values for consistency:

| Value | Description |
|-------|-------------|
| `Mid-Atlantic` | PA, NJ, DE, MD, DC, VA, WV |
| `Northeast` | NY, CT, MA, RI, VT, NH, ME |
| `Southeast` | NC, SC, GA, FL, AL, MS, TN, KY |
| `Midwest` | OH, MI, IN, IL, WI, MN, IA, MO |
| `Southwest` | TX, OK, AR, LA, NM, AZ |
| `West` | CA, NV, OR, WA, ID, MT, WY, CO, UT |
| `National` | Operates nationwide |

---

## Niche Focus Standardization

Recommended niche values for consistency:

| Value | Description |
|-------|-------------|
| `Healthcare` | Hospitals, practices, health services |
| `SaaS` | Software-as-a-service companies |
| `Manufacturing` | Industrial and manufacturing |
| `Professional Services` | Consulting, legal, accounting |
| `Construction` | Contractors, construction firms |
| `Retail` | Retail and e-commerce |
| `Nonprofit` | Nonprofit organizations |
| `Generalist` | No specific industry focus |

---

*Last Updated: 2026-01-28*
