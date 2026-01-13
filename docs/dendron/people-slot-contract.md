---
id: people-slot-contract
title: People Slot Contract
desc: Minimal contract defining when a slot is FILLED - full_name + title + linkedin_url
updated: 2026-01-09
created: 2026-01-09
tags:
  - doctrine
  - people
  - slots
  - contract
  - enforcement
  - imo-creator
---

# People Slot Contract

## Overview

The **People Slot Contract** defines the minimal requirements for a slot to be considered **FILLED**. This is a core doctrine governing the People Intelligence Sub-Hub.

> **DOCTRINE:** Slots are containers, not people records. Vendors propose candidates. The system decides truth.

## Quick Reference

| Field | Value |
|-------|-------|
| **Contract ID** | SLOT-CONTRACT-001 |
| **Version** | 1.0.0 |
| **Status** | ✅ ENFORCED |
| **Enforcement Date** | 2026-01-09 |
| **Commit** | `8561ad8` |
| **Hub** | People Intelligence (04.04.02) |

## Contract Definition

### Required Fields (MUST ALL BE PRESENT)

| Field | Type | Constraint | Purpose |
|-------|------|------------|---------|
| `full_name` | TEXT | NOT NULL, non-empty | Person's full name |
| `title` | TEXT | NOT NULL, non-empty | Job title |
| `linkedin_url` | TEXT | NOT NULL, contains `linkedin.com/in/` | Identity anchor |

### A Slot is FILLED If and Only If

```
full_name IS NOT NULL AND full_name != ''
AND title IS NOT NULL AND title != ''
AND linkedin_url IS NOT NULL AND linkedin_url LIKE '%linkedin.com/in/%'
```

### Optional Enrichment (NEVER BLOCKS)

| Field | Purpose | Severity if Missing |
|-------|---------|---------------------|
| `email` | Outreach delivery | ⚠️ WARNING only |
| `phone` | Secondary contact | ⚠️ WARNING only |
| `socials` | Additional channels | ℹ️ INFO only |

## Doctrine Principles

### 1. Email is Enrichment, Not Identity

```
❌ WRONG: Email required to fill slot
✅ RIGHT: Email enhances filled slot (downstream enrichment)
```

Email may be added after a slot is filled. It MUST NOT gate slot fill operations.

### 2. LinkedIn URL is the Identity Anchor

LinkedIn is the **primary external identity anchor** for people records. It provides:
- Unique identification across job changes
- Verification of employment history
- Public profile for enrichment

### 3. Three Fields = Minimal Viable Person

The contract is intentionally minimal:
- **Name** → Who is this person?
- **Title** → What role do they hold?
- **LinkedIn** → How do we verify identity?

## Enforcement Artifacts

### Code Enforcement

| File | Purpose |
|------|---------|
| [[ops/validation/validation_rules.py]] | `validate_slot_contract()` function |
| [[ops/tests/test_people_slot_contract.py]] | 15 regression tests |
| [[contracts/people-outreach.contract.yaml]] | Spoke contract with slot_contract section |

### Validation Function

```python
def validate_slot_contract(record: Dict) -> Tuple[bool, List[ValidationFailure]]:
    """
    DOCTRINE: A slot is FILLED if and only if:
      1. full_name IS NOT NULL AND != ''
      2. title IS NOT NULL AND != ''
      3. linkedin_url IS NOT NULL AND != ''
    """
    # Checks only contract fields, returns (meets_contract, failures)
```

### Test Coverage

| Test Case | Assertion |
|-----------|-----------|
| `test_slot_contract_valid_without_email` | ✅ Slot fills without email |
| `test_slot_contract_fails_with_email_only` | ✅ Email-only is rejected |
| `test_email_missing_is_warning_not_error` | ✅ Email missing = WARNING |
| `test_full_validation_passes_without_email` | ✅ Full flow works |

## Schema Implications

### Current State (2026-01-09)

| Table | Compliance |
|-------|------------|
| `people.people_master` | ✅ 170/170 (100%) meet contract |
| `people.company_slot` | ⬜ Container only (slots, not people) |
| `people.people_candidate` | ⬜ Staging area |

### Deferred Schema Changes

| Change | Priority | Reason for Deferral |
|--------|----------|---------------------|
| Replace `chk_contact_required` with `chk_slot_contract` | P2 | Requires migration coordination |
| Mark phone fields on `company_slot` deprecated | P3 | Phone belongs on people_master |
| Make `full_name` NOT NULL at schema level | P2 | Data backfill needed |

## Violations Addressed

### V-001: Email Required as ERROR (FIXED)

- **Before:** `validate_email()` returned `ERROR` severity
- **After:** Returns `WARNING` severity
- **Location:** [validation_rules.py#L451](ops/validation/validation_rules.py#L451)

### V-002: CHECK Constraint Allows Email-Only (DEFERRED)

- **Issue:** `chk_contact_required` allows `email IS NOT NULL OR linkedin_url IS NOT NULL`
- **Fix:** Replace with `chk_slot_contract` requiring all three fields
- **Status:** Deferred to P2 migration

### V-003: Phone Fields on Slot Container (DEFERRED)

- **Issue:** `company_slot` has `phone`, `phone_extension`, `phone_verified_at`
- **Fix:** Mark as deprecated, move to people_master
- **Status:** Deferred to P3

## Data Inventory

### Current Slot Statistics

| Metric | Value |
|--------|-------|
| Total Slots | 191,808 |
| Filled Slots | 154 |
| Open Slots | 191,654 |
| Fill Rate | 0.08% |

### people_master Contract Compliance

| Metric | Value |
|--------|-------|
| Total Records | 170 |
| Has full_name | 170 (100%) |
| Has title | 170 (100%) |
| Has linkedin_url | 170 (100%) |
| **Meets Contract** | **170 (100%)** |

## Related

- [[people-intelligence]] - Parent hub
- [[talent-flow]] - Movement tracking uses same identity anchor
- [[company-people.contract]] - Upstream spoke contract
- [[people-outreach.contract]] - Downstream spoke contract

---

**Last Updated:** 2026-01-09
**Author:** Claude Code (IMO-Creator)
**Authority:** imo-creator
**Doctrine Version:** Barton IMO v1.2
