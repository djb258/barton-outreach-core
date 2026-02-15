# Data Ingest Documentation

This folder contains ingest specifications for importing data into the Barton Outreach system.

**MASTER REFERENCE**: See `docs/MASTER_ERD.md` for complete database architecture and join paths.

---

## Dual Lane System

**CRITICAL**: The system operates TWO ISOLATED LANES. These lanes have **NO CONNECTION** to the main outreach pipeline.

| Lane | Schema | Connection to Outreach | Connection to Each Other |
|------|--------|------------------------|--------------------------|
| **A** | `sales.*` | **NONE** (optional FKs for analytics) | **NONE** |
| **B** | `partners.*` | **NONE** | **NONE** |

**DO NOT**:
- Create FKs from Lane A/B to outreach.outreach
- Join sales.* to partners.*
- Mix Lane A and Lane B data

| Lane | Purpose | Ingest Doc | Script |
|------|---------|------------|--------|
| **A** | Appointment Reactivation | [APPOINTMENT_HISTORY_INGEST.md](./APPOINTMENT_HISTORY_INGEST.md) | `scripts/ingest/appointment_history_ingest.cjs` |
| **B** | Fractional CFO Partners | [FRACTIONAL_CFO_PARTNER_INGEST.md](./FRACTIONAL_CFO_PARTNER_INGEST.md) | `scripts/ingest/fractional_cfo_ingest.cjs` |

---

## Lane A: Appointment Reactivation

Re-engage stalled/ghosted prospects from past meetings.

### Quick Start

```bash
# Prepare Excel with columns: company_id, people_id, meeting_date, meeting_type, meeting_outcome, stalled_reason, source
doppler run -- node scripts/ingest/appointment_history_ingest.cjs appointments.xlsx
```

### Target Tables
- `sales.appointment_history` (FACT - write-once)
- `bit.reactivation_intent` (SCORING)

### Outreach View
```sql
SELECT * FROM bit.v_reactivation_ready;
```

---

## Lane B: Fractional CFO Partners

Build partner referral network.

### Quick Start

```bash
# Import partners
doppler run -- node scripts/ingest/fractional_cfo_ingest.cjs partners partners.xlsx

# Import partner meetings
doppler run -- node scripts/ingest/fractional_cfo_ingest.cjs appointments meetings.xlsx
```

### Target Tables
- `partners.fractional_cfo_master` (MASTER - updateable)
- `partners.partner_appointments` (FACT - write-once)
- `bit.partner_intent` (SCORING)

### Outreach View
```sql
SELECT * FROM bit.v_partner_outreach_ready;
```

---

## Architecture Reference

See [DUAL_LANE_ARCHITECTURE.md](../architecture/DUAL_LANE_ARCHITECTURE.md) for full ERD and isolation rules.

---

## Common Options

Both ingest scripts support:

| Option | Description |
|--------|-------------|
| `--dry-run` | Validate without inserting |
| `--source=X` | Override source field (Lane A only) |

---

## Excel Template Format

### Lane A: Appointment History

| Column | Required | Type | Notes |
|--------|----------|------|-------|
| company_id | No | UUID | FK to company_master |
| people_id | No | UUID | FK to people_master |
| meeting_date | **Yes** | Date | YYYY-MM-DD |
| meeting_type | **Yes** | Enum | discovery, systems, numbers, other |
| meeting_outcome | **Yes** | Enum | progressed, stalled, ghosted, lost |
| stalled_reason | Conditional | Text | Required if outcome=stalled |
| source | No | Enum | calendar, crm, manual (default: manual) |

### Lane B: Partner Master

| Column | Required | Type | Notes |
|--------|----------|------|-------|
| firm_name | **Yes** | Text | |
| primary_contact_name | **Yes** | Text | |
| linkedin_url | No | URL | Must be linkedin.com |
| email | No | Email | |
| geography | No | Text | e.g., Mid-Atlantic |
| niche_focus | No | Text | e.g., Healthcare |
| source | **Yes** | Text | e.g., LinkedIn, Referral |
| status | No | Enum | prospect (default), contacted, engaged, partner |

### Lane B: Partner Appointments

| Column | Required | Type | Notes |
|--------|----------|------|-------|
| fractional_cfo_id | **Yes** | UUID | FK to partner master |
| meeting_date | **Yes** | Date | YYYY-MM-DD |
| meeting_type | **Yes** | Enum | intro, followup |
| outcome | **Yes** | Enum | warm, neutral, cold |
| notes | No | Text | |

---

*Last Updated: 2026-01-28*
