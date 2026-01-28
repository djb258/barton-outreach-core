# Repository Domain Specification

**Repository**: barton-outreach-core
**Domain**: barton-outreach
**Parent**: IMO-Creator
**Status**: ACTIVE

---

## CRITICAL: What This File MUST NOT Contain

- NO SQL statements
- NO code snippets or functions
- NO workflow logic or decision trees
- NO scoring formulas or calculations
- NO implementation details
- NO prose descriptions of "how it works"

This file contains BINDINGS ONLY — mapping generic roles to domain-specific names.

---

## Domain Identity

| Field | Value |
|-------|-------|
| Domain Name | barton-outreach |
| Sovereign Reference | CL-01 |
| Hub ID | HUB-OUTREACH-001 |

---

## Fact Schema Bindings

Map generic FACT role to your domain's source-of-truth tables.

| Generic Role | Domain Table | Owner Schema | Description (10 words max) |
|--------------|--------------|--------------|---------------------------|
| OPERATIONAL_SPINE | outreach.outreach | outreach | Primary operational spine for outreach workflow |
| COMPANY_TARGET_FACT | outreach.company_target | outreach | Company targeting and domain resolution facts |
| DOL_FILING_FACT | outreach.dol | outreach | DOL Form 5500 filing reference data |
| PEOPLE_FACT | outreach.people | outreach | People intelligence and slot assignments |
| BLOG_FACT | outreach.blog | outreach | Blog content signal facts |
| APPOINTMENT_HISTORY_FACT | sales.appointment_history | sales | Lane A: Past meeting records (write-once) |
| PARTNER_MASTER | partners.fractional_cfo_master | partners | Lane B: Fractional CFO partner records |
| PARTNER_APPOINTMENT_FACT | partners.partner_appointments | partners | Lane B: Partner meeting records (write-once) |

**Validation**: 8 rows present. No brackets in final values. ✓

---

## Intent Layer Bindings

Map generic concepts to your domain's implementation.

| Generic Role | Domain Column/Table | Data Type | Description (10 words max) |
|--------------|---------------------|-----------|---------------------------|
| LIFECYCLE_STATE | outreach.outreach.status | ENUM | Workflow state for outreach record |
| BIT_SCORE | outreach.bit_scores.bit_score | INTEGER | Buyer intent score for prioritization |
| REACTIVATION_INTENT | bit.reactivation_intent.intent_score | INTEGER | Lane A: Reactivation priority score |
| PARTNER_INTENT | bit.partner_intent.engagement_score | INTEGER | Lane B: Partner engagement score |

**Validation**: LIFECYCLE_STATE required. ✓ Domain-specific scores present. No brackets in final values. ✓

---

## Lane Definitions

Define data isolation boundaries within this domain.

| Lane Name | Tables Included | Isolation Rule |
|-----------|-----------------|----------------|
| Main Outreach | outreach.*, people.*, company.*, bit.bit_scores | Primary operational spine, FK to cl.company_identity |
| Lane A (Appointment Reactivation) | sales.*, bit.reactivation_intent | NO FK to outreach.outreach, NO FK to partners.* |
| Lane B (Fractional CFO Partners) | partners.*, bit.partner_intent | NO FK to outreach.outreach, NO FK to sales.* |

**Validation**: 3 lanes defined. Isolation rules explicit. ✓

---

## Downstream Consumers (Read-Only)

| Consumer | Access Level | Tables Exposed |
|----------|--------------|----------------|
| LinkedIn Outreach Tool | READ | bit.v_reactivation_ready, bit.v_partner_outreach_ready |
| Marketing Dashboard | READ | outreach.vw_marketing_eligibility_with_overrides |
| Reporting Layer | READ | outreach.vw_sovereign_completion |

**Validation**: 3 consumers listed. ✓

---

## Forbidden Joins

| Source Table | Target Table | Reason |
|--------------|--------------|--------|
| sales.* | partners.* | Lane A and Lane B are fully isolated |
| sales.* | outreach.outreach | Lane A has no connection to main spine |
| partners.* | outreach.outreach | Lane B has no connection to main spine |
| sales.appointment_history | people.people_master | Cross-lane people reference forbidden |
| partners.fractional_cfo_master | company.company_master | Partners are external, not in company registry |

**Validation**: Required. 5 forbidden join rules defined. ✓

---

## Domain Lifecycle States

| State | Maps To Canonical | Description |
|-------|-------------------|-------------|
| INIT | DRAFT | Outreach record created, not yet processed |
| ACTIVE | ACTIVE | Outreach in active campaign |
| PAUSED | SUSPENDED | Temporarily halted by kill switch |
| COMPLETED | TERMINATED | Outreach cycle complete |
| FAILED | TERMINATED | Outreach failed validation gate |

**Validation**: All states map to canonical states. ✓

---

## Binding Completeness Check

Before this file is valid, verify:

- [x] Domain Name: Non-placeholder value
- [x] Sovereign Reference: Valid CC-01 ID
- [x] Hub ID: Valid CC-02 ID
- [x] At least 1 Fact Schema binding
- [x] LIFECYCLE_STATE binding present
- [x] At least 1 Lane definition (if multiple data contexts)
- [x] All Lifecycle States map to canonical
- [x] NO SQL, code, or logic present
- [x] NO brackets [ ] remain in values

**ALL CHECKS PASS. This file is VALID.**

---

## Document Control

| Field | Value |
|-------|-------|
| Created | 2026-01-28 |
| Last Modified | 2026-01-28 |
| Version | 1.0.0 |
| Status | ACTIVE |
| Parent Doctrine | IMO-Creator |
| Validated | [x] YES |
