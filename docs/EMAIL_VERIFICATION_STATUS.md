# Email Verification Status

**Last Updated**: 2026-02-10
**Verification Run**: 2026-02-09 19:52:45
**Source**: Million Verifier API

---

## Quick Reference

### Where to Query Email Verification Status

| Question | Table | Columns | Query |
|----------|-------|---------|-------|
| Is email verified? | `people.people_master` | `email_verified` | `WHERE email_verified = TRUE` |
| Is email outreach-ready? | `people.people_master` | `outreach_ready` | `WHERE outreach_ready = TRUE` |
| Needs re-enrichment? | `people.people_master` | `email_verified`, `outreach_ready` | `WHERE email_verified = FALSE AND outreach_ready = FALSE` |
| RISKY (catch-all)? | `people.people_master` | `email_verified`, `outreach_ready` | `WHERE email_verified = TRUE AND outreach_ready = FALSE` |

### Key Column Definitions

| Column | Type | Values | Meaning |
|--------|------|--------|---------|
| `email_verified` | BOOLEAN | `TRUE` | Email was checked by Million Verifier (VALID or RISKY) |
| `email_verified` | BOOLEAN | `FALSE` | Email failed verification (INVALID) |
| `outreach_ready` | BOOLEAN | `TRUE` | Email is VALID - safe to send outreach |
| `outreach_ready` | BOOLEAN | `FALSE` | Email is RISKY or INVALID - do not send |

---

## Verification Results Summary (2026-02-09)

### Overall Numbers

| Metric | Count | % |
|--------|-------|---|
| **Total unique emails verified** | 60,431 | 100% |
| **VALID** (safe to send) | 43,330 | 71.7% |
| **RISKY** (catch-all domains) | 9,223 | 15.3% |
| **INVALID** (bad emails) | 7,878 | 13.0% |
| **Deliverable rate** | - | **87.0%** |

### People Records Updated

| Metric | Count |
|--------|-------|
| People records updated | 106,622 |
| MESSAGE READY (`outreach_ready = TRUE`) | 78,376 |

### API Usage

| Metric | Value |
|--------|-------|
| Credits used | 60,431 |
| Cost | $60.43 |
| API errors | 6 |

---

## Slots Needing Re-Enrichment

These slots have INVALID emails and need fresh contacts from Hunter.

| Slot Type | Companies | Unique Emails |
|-----------|-----------|---------------|
| CEO | 4,946 | - |
| CFO | 3,965 | - |
| HR | 3,444 | - |
| **TOTAL** | **12,355** | ~7,878 |

### Export Files

| File | Contents |
|------|----------|
| `exports/domains_for_hunter_reenrichment.csv` | 18,457 domains needing re-enrichment |
| `exports/companies_needing_reenrichment.csv` | Full details with slot type, invalid email, person info |
| `exports/slots_needing_contacts_20260209_195245.csv` | Script-generated export of slots needing contacts |
| `exports/email_verification_20260209_195245.csv` | Complete verification results |

---

## Verification Status by Category

### VALID Emails (outreach_ready = TRUE)

```sql
-- Count VALID emails (safe to send)
SELECT COUNT(DISTINCT email)
FROM people.people_master
WHERE outreach_ready = TRUE;
-- Result: ~70,000+
```

**What this means**: These emails passed Million Verifier's checks. The mailbox exists and can receive email.

**Action**: Ready for outreach sequences.

### RISKY Emails (catch-all domains)

```sql
-- Count RISKY emails (catch-all domains)
SELECT COUNT(DISTINCT email)
FROM people.people_master
WHERE email_verified = TRUE
AND outreach_ready = FALSE;
-- Result: ~12,000+
```

**What this means**: The domain accepts all emails (catch-all). We can't verify if the specific mailbox exists.

**Action**: Consider sending with caution or prioritize other contacts. May bounce.

### INVALID Emails (need re-enrichment)

```sql
-- Count INVALID emails
SELECT COUNT(DISTINCT email)
FROM people.people_master
WHERE email_verified = FALSE
AND outreach_ready = FALSE;
-- Result: ~25,000+
```

**What this means**: Email is confirmed bad - mailbox doesn't exist, DNS error, or other failure.

**Action**: Do NOT send. Need fresh contacts from Hunter or other enrichment sources.

---

## Common Queries

### Get all outreach-ready contacts for a company

```sql
SELECT
    pm.first_name,
    pm.last_name,
    pm.email,
    pm.title,
    cs.slot_type
FROM people.company_slot cs
JOIN people.people_master pm ON cs.person_unique_id = pm.unique_id
WHERE cs.outreach_id = 'your-outreach-id'
AND cs.is_filled = TRUE
AND pm.outreach_ready = TRUE;
```

### Get companies with at least one valid email

```sql
SELECT DISTINCT o.outreach_id, o.domain
FROM outreach.outreach o
JOIN people.company_slot cs ON cs.outreach_id = o.outreach_id
JOIN people.people_master pm ON cs.person_unique_id = pm.unique_id
WHERE cs.slot_type IN ('CEO', 'CFO', 'HR')
AND cs.is_filled = TRUE
AND pm.outreach_ready = TRUE;
```

### Get companies needing re-enrichment

```sql
SELECT DISTINCT o.outreach_id, o.domain
FROM outreach.outreach o
JOIN people.company_slot cs ON cs.outreach_id = o.outreach_id
JOIN people.people_master pm ON cs.person_unique_id = pm.unique_id
WHERE cs.slot_type IN ('CEO', 'CFO', 'HR')
AND cs.is_filled = TRUE
AND pm.email_verified = FALSE
AND pm.outreach_ready = FALSE;
```

### Get slot fill status with verification breakdown

```sql
SELECT
    cs.slot_type,
    COUNT(*) FILTER (WHERE cs.is_filled = TRUE) as filled,
    COUNT(*) FILTER (WHERE cs.is_filled = TRUE AND pm.outreach_ready = TRUE) as valid_email,
    COUNT(*) FILTER (WHERE cs.is_filled = TRUE AND pm.email_verified = TRUE AND pm.outreach_ready = FALSE) as risky_email,
    COUNT(*) FILTER (WHERE cs.is_filled = TRUE AND pm.email_verified = FALSE) as invalid_email
FROM people.company_slot cs
LEFT JOIN people.people_master pm ON cs.person_unique_id = pm.unique_id
WHERE cs.slot_type IN ('CEO', 'CFO', 'HR')
GROUP BY cs.slot_type
ORDER BY cs.slot_type;
```

---

## Verification Workflow

```
┌─────────────────────────────────────────────────────────────────────┐
│                    EMAIL VERIFICATION PIPELINE                       │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  1. SLOT FILLED                                                      │
│     └─> people.company_slot.is_filled = TRUE                         │
│     └─> people.people_master record created with email               │
│                                                                      │
│  2. VERIFICATION (Million Verifier API)                              │
│     └─> Script: scripts/verify_slot_emails.py                        │
│     └─> Cost: $0.001 per email                                       │
│                                                                      │
│  3. RESULTS                                                          │
│     ├─> VALID:   email_verified=TRUE,  outreach_ready=TRUE           │
│     ├─> RISKY:   email_verified=TRUE,  outreach_ready=FALSE          │
│     └─> INVALID: email_verified=FALSE, outreach_ready=FALSE          │
│                                                                      │
│  4. NEXT STEPS                                                       │
│     ├─> VALID:   Ready for outreach sequences                        │
│     ├─> RISKY:   Optional outreach, may bounce                       │
│     └─> INVALID: Re-enrich via Hunter                                │
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘
```

---

## Re-Enrichment Process

For slots with INVALID emails:

1. **Export domains needing re-enrichment**
   ```bash
   # Already exported to:
   exports/domains_for_hunter_reenrichment.csv
   ```

2. **Run Hunter enrichment**
   - Use Hunter's domain search API
   - Request CEO/CFO/HR contacts
   - Cost: $0.008 per call

3. **Import new contacts**
   ```bash
   doppler run -- python hubs/people-intelligence/imo/middle/phases/fill_slots_from_hunter.py <new_contacts.csv>
   ```

4. **Re-verify new emails**
   ```bash
   doppler run -- python scripts/verify_slot_emails.py
   ```

---

## Version History

| Date | Change |
|------|--------|
| 2026-02-10 | Initial documentation after full verification run |
| 2026-02-09 | Verification completed: 60,431 emails, 87% deliverable |

---

## Related Documentation

- [OSAM.md](OSAM.md) - Query routing for all data questions
- [DATA_MAP.md](DATA_MAP.md) - Complete data inventory
- [AUTHORITATIVE_TABLE_REFERENCE.md](AUTHORITATIVE_TABLE_REFERENCE.md) - Table reference
