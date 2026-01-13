# Slot Tracker Doctrine — SlotWatch Module
## Barton Doctrine Framework | SVG-PLE Marketing Core

**Document ID**: `04.04.02.04.15000.001`
**Module Name**: SlotWatch
**Version**: 1.0.0
**Last Updated**: 2025-11-10
**Module Type**: Self-Contained Executive Role Tracker
**Role**: Marketing Automation + BIT Integration
**Status**: Active | Production Ready
**Future Extraction**: barton-slotwatch (standalone repo)

---

## 📋 Section 1: Purpose & Architecture

### Module Purpose

The **SlotWatch module** (`svg_marketing.slot_tracker`) tracks executive-level role vacancies and fills across target companies. When a CEO, CFO, or HR executive slot is filled, the module automatically triggers BIT (Buyer Intent Tool) scoring events and marketing automation workflows.

### Module Boundary & Dependencies

**Self-Contained**: Yes

**External Dependencies**:
- `marketing.company_master` (company reference)
- `marketing.people_master` (contact reference)
- `bit.events` (BIT integration, optional)

**Future Extraction**: Ready for `barton-slotwatch` repo with minimal changes

---

## 📂 Section 2: Schema & Data Model

### Primary Table: `svg_marketing.slot_tracker`

**Barton ID**: `04.04.02.04.15000.001`

#### Key Columns

- `slot_id` BIGSERIAL PRIMARY KEY
- `company_id` TEXT FK → company_master
- `role` TEXT (CEO, CFO, HR)
- `contact_id` TEXT FK → people_master (NULL if vacant)
- `status` TEXT (filled, vacant)
- `filled_at` TIMESTAMPTZ
- `vacated_at` TIMESTAMPTZ
- `marketing_triggered` BOOLEAN

#### Unique Constraint

- One slot per company/role: `UNIQUE (company_id, role)`

#### Indexes (9 total)

Performance-optimized for company lookup, status filtering, and date-based queries.

---

## ⚙️ Section 3: Trigger Logic & BIT Integration

### Slot Fill Trigger Flow

```
UPDATE slot_tracker SET status = 'filled'
  → TRIGGER: trg_slot_filled_to_bit
    → FUNCTION: fn_marketing_on_slot_filled()
      → Map role to BIT rule
      → INSERT INTO bit.events
      → SET marketing_triggered = true
```

### BIT Rule Mapping

| Role | BIT Rule | Weight |
|------|----------|--------|
| CEO | ceo_slot_filled | 30 |
| CFO | cfo_slot_filled | 25 |
| HR | hr_slot_filled | 20 |

### Vacancy Reset

```
UPDATE slot_tracker SET status = 'vacant'
  → TRIGGER: trg_reset_marketing_on_vacancy
    → FUNCTION: fn_reset_marketing_on_vacancy()
      → SET marketing_triggered = false
      → SET contact_id = NULL
```

---

## 🎯 Section 4: Use Cases

### Use Case 1: Track New Executive Hire

```sql
-- Fill slot (auto-triggers BIT event)
UPDATE svg_marketing.slot_tracker
SET status = 'filled',
    contact_id = '04.04.02.04.20001.005',
    filled_at = NOW()
WHERE company_id = '04.04.01.01.00001.001'
  AND role = 'CFO';

-- Verify BIT event created
SELECT st.marketing_triggered, e.event_id, r.rule_name
FROM svg_marketing.slot_tracker st
LEFT JOIN bit.events e ON e.company_unique_id = st.company_id
LEFT JOIN bit.rule_reference r ON e.rule_id = r.rule_id
WHERE st.company_id = '04.04.01.01.00001.001'
  AND st.role = 'CFO';
```

### Use Case 2: Query Vacant Slots

```sql
SELECT cm.company_name, st.role, st.vacated_at
FROM svg_marketing.slot_tracker st
JOIN marketing.company_master cm ON st.company_id = cm.company_unique_id
WHERE st.status = 'vacant'
ORDER BY st.vacated_at ASC;
```

### Use Case 3: Monitor Fill Rate

```sql
SELECT
    role,
    COUNT(*) AS total_slots,
    COUNT(*) FILTER (WHERE status = 'filled') AS filled_slots,
    ROUND(100.0 * COUNT(*) FILTER (WHERE status = 'filled') / COUNT(*), 1) AS fill_rate_pct
FROM svg_marketing.slot_tracker
GROUP BY role;
```

---

## 📚 Appendix

### Related Files

- `infra/migrations/2025-11-10-slot-tracker.sql`
- `infra/migrations/2025-11-10-slot-filled-trigger.sql`
- `infra/VERIFICATION_QUERIES.sql` (Section 12)
- `doctrine/ple/BIT-Doctrine.md`

### Barton Audit Log

```sql
SELECT * FROM shq.audit_log
WHERE audit_id IN ('04.04.02.04.15000.001', '04.04.02.04.15000.002');
```

---

**End of Slot Tracker Doctrine**
