# Technical Architecture Specification: Decision Trees

**Repository**: barton-outreach-core
**Version**: 1.0.0
**Generated**: 2026-01-28
**Purpose**: Explicit branching logic for all operations — NO guessing

---

## How to Use This Document

Follow these decision trees when determining:
- Which table to query
- What action to take
- What to check when conditions change

**RULE**: If you encounter a scenario, find the matching tree and follow it exactly.

---

## 1. Company Lookup Decision Tree

```
START: Need company data
    │
    ├─► Do you have company_unique_id?
    │       │
    │       ├─► YES → Query cl.company_identity WHERE company_unique_id = $id
    │       │
    │       └─► NO → Continue below
    │
    ├─► Do you have outreach_id?
    │       │
    │       ├─► YES → Query outreach.outreach WHERE outreach_id = $oid
    │       │         THEN JOIN cl.company_identity ON ci.outreach_id = o.outreach_id
    │       │
    │       └─► NO → Continue below
    │
    ├─► Do you have domain?
    │       │
    │       ├─► YES → Query cl.company_identity WHERE normalized_domain = $domain
    │       │         NOTE: Use normalized_domain, NOT company_domain
    │       │
    │       └─► NO → Continue below
    │
    ├─► Do you have company name?
    │       │
    │       ├─► YES → Query cl.company_identity WHERE company_name ILIKE '%' || $name || '%'
    │       │         WARNING: May return multiple results, verify with domain
    │       │
    │       └─► NO → Continue below
    │
    ├─► Do you have EIN?
    │       │
    │       ├─► YES → Query dol.form_5500 WHERE ein = $ein
    │       │         THEN use sponsor_name to find in cl.company_identity
    │       │
    │       └─► NO → STOP - Insufficient identifiers
    │
    └─► END
```

---

## 2. Outreach Status Decision Tree

```
START: Check if company can receive outreach
    │
    ├─► Query cl.company_identity WHERE company_unique_id = $id
    │
    ├─► Is outreach_id NULL?
    │       │
    │       ├─► YES → Company NOT in outreach
    │       │         │
    │       │         ├─► Is eligibility_status = 'ELIGIBLE'?
    │       │         │       │
    │       │         │       ├─► YES → Can initiate outreach
    │       │         │       │
    │       │         │       └─► NO → Check exclusion_reason for why
    │       │         │
    │       │         └─► END
    │       │
    │       └─► NO → Company IS in outreach, continue below
    │
    ├─► Query outreach.company_target WHERE outreach_id = $oid
    │
    ├─► What is outreach_status?
    │       │
    │       ├─► 'queued' → Waiting to be processed
    │       │
    │       ├─► 'active' → Currently in campaign
    │       │         │
    │       │         └─► Check outreach.manual_overrides WHERE is_active = true
    │       │                 │
    │       │                 ├─► Has active override? → Check override_type
    │       │                 │
    │       │                 └─► No override → Normal operation
    │       │
    │       ├─► 'paused' → Manually paused
    │       │         │
    │       │         └─► Check outreach.manual_overrides for reason
    │       │
    │       ├─► 'completed' → Outreach finished
    │       │
    │       └─► 'failed' → Check outreach.company_target_errors
    │
    └─► END
```

---

## 3. Sub-Hub Execution Decision Tree

```
START: Execute sub-hub for outreach_id
    │
    ├─► GATE 0: Verify outreach_id exists in spine
    │       │
    │       └─► Query: SELECT 1 FROM outreach.outreach WHERE outreach_id = $oid
    │               │
    │               ├─► NOT FOUND → HARD FAIL: Invalid outreach_id
    │               │
    │               └─► FOUND → Continue
    │
    ├─► Which sub-hub?
    │       │
    │       ├─► Company Target (04.04.01)
    │       │       │
    │       │       ├─► Prerequisites: None (first in waterfall)
    │       │       │
    │       │       ├─► Execute: Domain resolution, email pattern discovery
    │       │       │
    │       │       └─► Write to: outreach.company_target
    │       │
    │       ├─► DOL Filings (04.04.03)
    │       │       │
    │       │       ├─► Prerequisites: Company Target must PASS
    │       │       │       │
    │       │       │       └─► Check: SELECT 1 FROM outreach.company_target
    │       │       │                  WHERE outreach_id = $oid AND email_method IS NOT NULL
    │       │       │               │
    │       │       │               ├─► NOT FOUND → WAIT for Company Target
    │       │       │               │
    │       │       │               └─► FOUND → Continue
    │       │       │
    │       │       ├─► Execute: EIN matching, Form 5500 lookup
    │       │       │
    │       │       └─► Write to: outreach.dol
    │       │
    │       ├─► People Intelligence (04.04.02)
    │       │       │
    │       │       ├─► Prerequisites: DOL must PASS (or be skipped)
    │       │       │       │
    │       │       │       └─► Check: SELECT 1 FROM outreach.dol
    │       │       │                  WHERE outreach_id = $oid
    │       │       │
    │       │       ├─► Execute: Slot assignment, email generation
    │       │       │
    │       │       └─► Write to: outreach.people, people.company_slot
    │       │
    │       ├─► Blog Content (04.04.05)
    │       │       │
    │       │       ├─► Prerequisites: People must PASS
    │       │       │
    │       │       ├─► Execute: Blog detection, RSS discovery
    │       │       │
    │       │       └─► Write to: outreach.blog
    │       │
    │       └─► BIT Engine
    │               │
    │               ├─► Prerequisites: All sub-hubs complete
    │               │
    │               ├─► Execute: Signal aggregation, scoring
    │               │
    │               └─► Write to: outreach.bit_scores, outreach.bit_signals
    │
    └─► END
```

---

## 4. Email Pattern Decision Tree

```
START: Get email pattern for company
    │
    ├─► Query outreach.company_target WHERE outreach_id = $oid
    │
    ├─► Is email_method NULL?
    │       │
    │       ├─► YES → Email pattern not yet discovered
    │       │         │
    │       │         └─► Trigger Company Target sub-hub (04.04.01)
    │       │
    │       └─► NO → Continue below
    │
    ├─► What is method_type?
    │       │
    │       ├─► 'PATTERN' → Standard email pattern discovered
    │       │       │
    │       │       └─► Use email_method to generate emails
    │       │           Example: "{first}.{last}@domain.com"
    │       │
    │       ├─► 'CATCHALL' → Domain accepts any email
    │       │       │
    │       │       ├─► is_catchall should be TRUE
    │       │       │
    │       │       └─► Can use any pattern, but deliverability uncertain
    │       │
    │       ├─► 'VERIFIED' → Pattern confirmed via verification
    │       │       │
    │       │       └─► High confidence, use directly
    │       │
    │       └─► 'NONE' → Could not determine pattern
    │               │
    │               └─► May need manual lookup or paid enrichment
    │
    ├─► Check confidence_score
    │       │
    │       ├─► >= 0.8 → High confidence, use pattern
    │       │
    │       ├─► >= 0.5 → Medium confidence, consider verification
    │       │
    │       └─► < 0.5 → Low confidence, manual review recommended
    │
    └─► END
```

---

## 5. Person Lookup Decision Tree

```
START: Find person for outreach
    │
    ├─► Do you have person_unique_id?
    │       │
    │       ├─► YES → Query people.people_master WHERE unique_id = $pid
    │       │
    │       └─► NO → Continue below
    │
    ├─► Do you have outreach_id and slot_type?
    │       │
    │       ├─► YES → Query outreach.people
    │       │         WHERE outreach_id = $oid AND slot_type = $slot
    │       │
    │       └─► NO → Continue below
    │
    ├─► Do you have company_unique_id?
    │       │
    │       ├─► YES → Query people.company_slot
    │       │         WHERE company_unique_id = $cid
    │       │         │
    │       │         ├─► Need specific slot? → AND slot_type = $slot
    │       │         │
    │       │         └─► Get person details:
    │       │             JOIN people.people_master pm
    │       │             ON pm.unique_id = cs.person_unique_id
    │       │
    │       └─► NO → Continue below
    │
    ├─► Do you have email?
    │       │
    │       ├─► YES → Query people.people_master WHERE email = $email
    │       │         WARNING: Email may not be unique
    │       │
    │       └─► NO → Continue below
    │
    ├─► Do you have LinkedIn URL?
    │       │
    │       ├─► YES → Query people.people_master WHERE linkedin_url = $url
    │       │
    │       └─► NO → STOP - Insufficient identifiers
    │
    └─► END
```

---

## 6. DOL Data Decision Tree

```
START: Find DOL data for company
    │
    ├─► Do you have outreach_id?
    │       │
    │       ├─► YES → Query outreach.dol WHERE outreach_id = $oid
    │       │         │
    │       │         ├─► form_5500_matched = true?
    │       │         │       │
    │       │         │       ├─► YES → Get filing details:
    │       │         │       │         JOIN dol.form_5500 f ON f.filing_id = od.filing_id
    │       │         │       │
    │       │         │       └─► NO → DOL match not found
    │       │         │
    │       │         └─► Get Schedule A:
    │       │             JOIN dol.schedule_a sa ON sa.filing_id = od.filing_id
    │       │
    │       └─► NO → Continue below
    │
    ├─► Do you have EIN?
    │       │
    │       ├─► YES → Query dol.form_5500 WHERE ein = $ein
    │       │         │
    │       │         └─► Get latest filing:
    │       │             ORDER BY plan_year DESC LIMIT 1
    │       │
    │       └─► NO → Continue below
    │
    ├─► Do you have company name?
    │       │
    │       ├─► YES → Query dol.form_5500
    │       │         WHERE sponsor_name ILIKE '%' || $name || '%'
    │       │         │
    │       │         └─► WARNING: May return multiple filings
    │       │             Verify with other data points
    │       │
    │       └─► NO → Continue below
    │
    ├─► Do you have domain?
    │       │
    │       ├─► YES → Query dol.ein_urls WHERE url ILIKE '%' || $domain || '%'
    │       │         THEN use EIN to query form_5500
    │       │
    │       └─► NO → STOP - Insufficient identifiers
    │
    └─► END
```

---

## 7. BIT Score Decision Tree

```
START: Get or calculate BIT score
    │
    ├─► Query outreach.bit_scores WHERE outreach_id = $oid
    │
    ├─► Record exists?
    │       │
    │       ├─► YES → Return bit_score, bit_tier
    │       │         │
    │       │         └─► Is score stale? (score_updated_at > 24 hours)
    │       │                 │
    │       │                 ├─► YES → Consider recalculation
    │       │                 │
    │       │                 └─► NO → Use cached score
    │       │
    │       └─► NO → Score not calculated yet
    │               │
    │               └─► Trigger BIT calculation
    │
    ├─► To calculate BIT score:
    │       │
    │       ├─► 1. Get DOL signals
    │       │       SELECT CASE WHEN form_5500_matched THEN 20 ELSE 0 END
    │       │       FROM outreach.dol WHERE outreach_id = $oid
    │       │
    │       ├─► 2. Get Blog signals
    │       │       SELECT COALESCE(signal_count * 5, 0)
    │       │       FROM outreach.blog WHERE outreach_id = $oid
    │       │
    │       ├─► 3. Get Movement signals
    │       │       SELECT COUNT(*) * 15
    │       │       FROM people.person_movement_history pmh
    │       │       JOIN outreach.people op ON op.person_unique_id = pmh.person_unique_id
    │       │       WHERE op.outreach_id = $oid
    │       │
    │       ├─► 4. Sum all signals (max 100)
    │       │
    │       └─► 5. Assign tier:
    │               │
    │               ├─► >= 80 → PLATINUM
    │               ├─► >= 60 → GOLD
    │               ├─► >= 40 → SILVER
    │               ├─► >= 20 → BRONZE
    │               └─► < 20  → NONE
    │
    └─► END
```

---

## 8. Kill Switch Decision Tree

```
START: Check if outreach is blocked
    │
    ├─► Query outreach.manual_overrides
    │   WHERE outreach_id = $oid AND is_active = true
    │
    ├─► Active override exists?
    │       │
    │       ├─► NO → Outreach NOT blocked, proceed normally
    │       │
    │       └─► YES → Check override_type
    │               │
    │               ├─► 'EXCLUDE' → Company excluded from all outreach
    │               │       │
    │               │       └─► STOP all outreach activities
    │               │
    │               ├─► 'INCLUDE' → Force include despite other rules
    │               │       │
    │               │       └─► Override eligibility checks
    │               │
    │               ├─► 'TIER_FORCE' → Override BIT tier
    │               │       │
    │               │       └─► Use override value, not calculated tier
    │               │
    │               ├─► 'PAUSE' → Temporarily paused
    │               │       │
    │               │       └─► Check expires_at
    │               │               │
    │               │               ├─► Expired? → Remove override
    │               │               │
    │               │               └─► Not expired → Remain paused
    │               │
    │               └─► Other → Check reason field for details
    │
    ├─► Log check to override_audit_log
    │
    └─► END
```

---

## 9. Outreach Init Decision Tree

```
START: Initialize outreach for company
    │
    ├─► STEP 1: Verify company exists in CL
    │       │
    │       └─► Query: SELECT company_unique_id, outreach_id, eligibility_status
    │                  FROM cl.company_identity
    │                  WHERE company_unique_id = $cid
    │               │
    │               ├─► NOT FOUND → HARD FAIL: Company not in CL
    │               │
    │               └─► FOUND → Continue
    │
    ├─► STEP 2: Check if already in outreach
    │       │
    │       └─► Is outreach_id NULL?
    │               │
    │               ├─► NO → HARD FAIL: Already in outreach
    │               │        Return existing outreach_id
    │               │
    │               └─► YES → Continue
    │
    ├─► STEP 3: Check eligibility
    │       │
    │       └─► Is eligibility_status = 'ELIGIBLE'?
    │               │
    │               ├─► NO → HARD FAIL: Not eligible
    │               │        Return exclusion_reason
    │               │
    │               └─► YES → Continue
    │
    ├─► STEP 4: Mint outreach_id
    │       │
    │       └─► INSERT INTO outreach.outreach
    │           (outreach_id, sovereign_id, domain)
    │           VALUES (gen_random_uuid(), $sovereign_id, $domain)
    │           RETURNING outreach_id
    │
    ├─► STEP 5: Register in CL (WRITE-ONCE)
    │       │
    │       └─► UPDATE cl.company_identity
    │           SET outreach_id = $new_oid, outreach_attached_at = NOW()
    │           WHERE company_unique_id = $cid AND outreach_id IS NULL
    │               │
    │               ├─► affected_rows = 0 → ROLLBACK, HARD FAIL
    │               │                       (race condition - already claimed)
    │               │
    │               └─► affected_rows = 1 → COMMIT, SUCCESS
    │
    ├─► STEP 6: Return new outreach_id
    │
    └─► END
```

---

## 10. Error Check Decision Tree

```
START: Diagnose error for outreach_id
    │
    ├─► Check each error table in order:
    │
    ├─► 1. Company Target errors
    │       │
    │       └─► SELECT * FROM outreach.company_target_errors
    │           WHERE outreach_id = $oid
    │           ORDER BY created_at DESC LIMIT 5
    │               │
    │               ├─► Errors found → Review error_type, error_message
    │               │
    │               └─► No errors → Continue
    │
    ├─► 2. DOL errors
    │       │
    │       └─► SELECT * FROM outreach.dol_errors
    │           WHERE outreach_id = $oid
    │           ORDER BY created_at DESC LIMIT 5
    │
    ├─► 3. People errors
    │       │
    │       └─► SELECT * FROM outreach.people_errors
    │           WHERE outreach_id = $oid
    │           ORDER BY created_at DESC LIMIT 5
    │
    ├─► 4. Blog errors
    │       │
    │       └─► SELECT * FROM outreach.blog_errors
    │           WHERE outreach_id = $oid
    │           ORDER BY created_at DESC LIMIT 5
    │
    ├─► 5. BIT errors
    │       │
    │       └─► SELECT * FROM outreach.bit_errors
    │           WHERE outreach_id = $oid
    │           ORDER BY created_at DESC LIMIT 5
    │
    ├─► 6. General outreach errors
    │       │
    │       └─► SELECT * FROM outreach.outreach_errors
    │           WHERE outreach_id = $oid
    │           ORDER BY created_at DESC LIMIT 5
    │
    ├─► Aggregate errors found
    │       │
    │       ├─► No errors in any table → Issue may be upstream (CL)
    │       │
    │       └─► Errors found → Address by sub-hub priority
    │
    └─► END
```

---

## Quick Reference: Decision Entry Points

| Scenario | Start At Tree # |
|----------|-----------------|
| Find company data | Tree 1 |
| Check outreach eligibility | Tree 2 |
| Execute sub-hub | Tree 3 |
| Get email pattern | Tree 4 |
| Find person | Tree 5 |
| Get DOL data | Tree 6 |
| Get BIT score | Tree 7 |
| Check kill switch | Tree 8 |
| Start new outreach | Tree 9 |
| Diagnose errors | Tree 10 |

---

## Document Control

| Field | Value |
|-------|-------|
| Created | 2026-01-28 |
| Version | 1.0.0 |
| Author | Claude Code (AI Employee) |
