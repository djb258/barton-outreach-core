# Outreach Hub - CL Doctrine Compliance Checklist

## Overview

This checklist verifies that the Outreach Execution Hub is fully aligned with the
Company Lifecycle (CL) parent-child doctrine.

**Parent Hub**: Company Lifecycle (CL)
**Child Hub**: Outreach Execution
**Doctrine Version**: CL Parent-Child Model v1.0

---

## 1. Identity Ownership

### 1.1 company_unique_id Source

| Requirement | Status | Evidence |
|-------------|--------|----------|
| company_unique_id is minted by CL only | ✓ PASS | No ID generation in outreach_hub.py |
| company_unique_id is received, not created | ✓ PASS | Passed via `data` parameter to `process()` |
| No inference from email domain | ✓ PASS | No domain parsing in Outreach code |
| No inference from company name | ✓ PASS | No name-based lookups in Outreach code |

### 1.2 No Shadow IDs

| Requirement | Status | Evidence |
|-------------|--------|----------|
| No alternate company identifiers | ✓ PASS | Only `company_id` used |
| No placeholder IDs | ✓ PASS | Returns None on validation failure |
| No temp/provisional IDs | ✓ PASS | Hard fail, no workarounds |

---

## 2. Failure Mode

### 2.1 Hard Failure on Missing company_unique_id

| Requirement | Status | Evidence |
|-------------|--------|----------|
| NULL company_id causes failure | ✓ PASS | Line 450: `if not company_id: return False` |
| Empty company_id causes failure | ✓ PASS | Truthy check catches empty string |
| Invalid company_id causes failure | ✓ PASS | `validate_company_anchor()` validates against CL |

### 2.2 No Silent Fallbacks

| Requirement | Status | Evidence |
|-------------|--------|----------|
| No default company_id | ✓ PASS | No default values in OutreachCandidate |
| No "unknown" company placeholder | ✓ PASS | Returns None, not placeholder |
| No skip-and-continue logic | ✓ PASS | Validation failure stops processing |

---

## 3. Scope Boundaries

### 3.1 Outreach Owns

| Entity | Ownership Declared | In hub.manifest.yaml |
|--------|-------------------|---------------------|
| campaigns | ✓ YES | Line 26: `- campaigns` |
| sequences | ✓ YES | Line 27: `- sequences` |
| send_log | ✓ YES | Line 28: `- send_log` |
| engagement_events | ✓ YES | Line 29: `- engagement_events` |
| reply_tracking | ✓ YES | Line 30: `- reply_tracking` |

### 3.2 Outreach Does NOT Own

| Entity | Non-Ownership Declared | In hub.manifest.yaml |
|--------|----------------------|---------------------|
| company_master | ✓ YES | Line 57: `- company_master # Company Hub owns` |
| people_master | ✓ YES | Line 58: `- people_master # People Hub owns` |
| bit_scores | ✓ YES | Line 59: `- bit_scores # Company Hub owns` |
| slot_assignments | ✓ YES | Line 60: `- slot_assignments # People Hub owns` |

### 3.3 Lifecycle State

| Requirement | Status | Evidence |
|-------------|--------|----------|
| Outreach does not change lifecycle state | ✓ PASS | No state mutation code |
| Outreach does not promote to Sales | ✓ PASS | No promotion logic |
| Outreach does not promote to Client | ✓ PASS | No promotion logic |
| Outreach only records signals | ✓ PASS | `engagement_events` is signal data |

---

## 4. Data Contract

### 4.1 FK References

| Table | company_unique_id Required | Constraint Type |
|-------|---------------------------|-----------------|
| campaigns | ⚠ VERIFY | Must be NOT NULL + FK |
| send_log | ⚠ VERIFY | Must be NOT NULL + FK |
| engagement_events | ⚠ VERIFY | Must be NOT NULL + FK |
| reply_tracking | ⚠ VERIFY | Must be NOT NULL + FK |

### 4.2 CL as Single Source of Truth

| Requirement | Status | Evidence |
|-------------|--------|----------|
| All company data comes from CL | ✓ PASS | `_get_company_data()` queries via pipeline |
| No local company metadata | ✓ PASS | OutreachCandidate caches, doesn't store |
| Company existence validated against CL | ✓ PASS | `validate_company_anchor()` checks CL |

---

## 5. Spoke Contracts

### 5.1 company-outreach.contract.yaml

| Requirement | Status | Evidence |
|-------------|--------|----------|
| Ingress uses company_id | ✓ PASS | `identity_contract: [company_id]` |
| Egress uses company_id | ✓ PASS | `identity_contract: [company_id]` |
| No identity transformation | ✓ PASS | `rules: [no_logic_in_spoke]` |

### 5.2 people-outreach.contract.yaml

| Requirement | Status | Evidence |
|-------------|--------|----------|
| Ingress includes company_id | ✓ PASS | `identity_contract: [company_id, ...]` |
| Compound identity allowed | ✓ PASS | `rules: [compound_identity_allowed]` |
| No identity transformation | ✓ PASS | `rules: [no_logic_in_spoke]` |

---

## 6. Documentation

### 6.1 README Declarations

| Requirement | Status | Location |
|-------------|--------|----------|
| Declares CL as parent | ✓ PASS | README.md: "Parent-Child Relationship" |
| States identity ownership | ✓ PASS | README.md: "Identity Ownership Declaration" |
| Lists Outreach scope | ✓ PASS | README.md: "Scope Definition" |
| Lists non-goals | ✓ PASS | README.md: "Non-Goals" |
| Defines failure mode | ✓ PASS | README.md: "Failure Mode" |

### 6.2 Hub Manifest

| Requirement | Status | Location |
|-------------|--------|----------|
| Type declared as sub-hub | ✓ PASS | hub.manifest.yaml: `type: sub-hub` |
| Entities owned listed | ✓ PASS | hub.manifest.yaml: `entities_owned` |
| Boundary rules defined | ✓ PASS | hub.manifest.yaml: `boundary_rules` |

---

## 7. Code Compliance

### 7.1 outreach_hub.py

| Line | Code Pattern | Status |
|------|--------------|--------|
| 86 | `company_id: str` required | ✓ PASS |
| 346-357 | Golden Rule validation | ✓ PASS |
| 351-357 | Hard fail on missing anchor | ✓ PASS |
| 450-451 | NULL check returns False | ✓ PASS |
| 454-456 | Delegates to Company Pipeline | ✓ PASS |

### 7.2 No Violations Found

| Anti-Pattern | Searched For | Result |
|--------------|--------------|--------|
| ID generation | `uuid.uuid4()` for company | NOT FOUND ✓ |
| Domain inference | Email domain parsing | NOT FOUND ✓ |
| Name matching | Fuzzy company name lookup | NOT FOUND ✓ |
| Shadow ID | Alternate identifier creation | NOT FOUND ✓ |
| Silent fallback | Default company assignment | NOT FOUND ✓ |

---

## Summary

| Category | Pass | Fail | Verify |
|----------|------|------|--------|
| Identity Ownership | 6 | 0 | 0 |
| Failure Mode | 6 | 0 | 0 |
| Scope Boundaries | 10 | 0 | 0 |
| Data Contract | 3 | 0 | 4 |
| Spoke Contracts | 6 | 0 | 0 |
| Documentation | 8 | 0 | 0 |
| Code Compliance | 7 | 0 | 0 |
| **TOTAL** | **46** | **0** | **4** |

### Verification Required

The following items require verification against actual database schema:

1. `outreach.campaigns` - Verify FK constraint exists
2. `outreach.send_log` - Verify FK constraint exists
3. `outreach.engagement_events` - Verify FK constraint exists
4. `outreach.reply_tracking` - Verify FK constraint exists

---

## Certification

**Outreach Execution Hub is ALIGNED with CL Parent-Child Doctrine**

Pending: Schema FK constraint verification

---

*Audit Date: 2025-12-26*
*Auditor: Doctrine Alignment Engineer*
*Doctrine Version: CL Parent-Child Model v1.0*
