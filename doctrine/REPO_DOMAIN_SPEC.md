# Repository Domain Specification

**Repository**: barton-outreach-core
**Domain**: barton-outreach
**Parent Doctrine**: IMO-Creator
**Status**: CONSTITUTIONAL
**Version**: 2.0.0
**Change Protocol**: ADR + HUMAN APPROVAL REQUIRED

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

## §1 SYSTEM TRANSFORMATION STATEMENT (CONSTITUTIONAL)

> **This system transforms sovereign company identities and external data signals (CONSTANTS) into marketing-ready engagement records with eligibility determination (VARIABLES) through CAPTURE (identity reception from CL and external sources), COMPUTE (enrichment, scoring, and slot assignment), and GOVERN (eligibility enforcement and kill-switch application).**

This statement is the constitutional foundation. All PRDs, ERDs, and Processes must trace to this transformation.

---

## §2 SYSTEM-LEVEL CONSTANTS (Inputs from Outside the System)

Constants are immutable inputs that originate OUTSIDE the Outreach system boundary.

| Constant | Source | Description |
|----------|--------|-------------|
| `sovereign_company_id` | CL (Company Lifecycle) | Immutable company identity minted by CL |
| `company_name` | CL (Company Lifecycle) | Canonical company name from CL |
| `company_domain` | CL (Company Lifecycle) | Primary domain from CL |
| `existence_verified` | CL (Company Lifecycle) | Domain verification status from CL |
| `identity_status` | CL (Company Lifecycle) | Identity verification status (PASS/FAIL) |
| `dol_form_5500_filings` | Federal DOL | Raw Form 5500 filing data |
| `dol_schedule_a_data` | Federal DOL | Raw Schedule A insurance data |
| `linkedin_profile_data` | External Enrichment | LinkedIn profile information |
| `news_content_signals` | External Sources | News and blog content |
| `raw_people_data` | Enrichment Providers | Raw executive/contact data |

**Rule**: Constants CANNOT be modified by Outreach. They are received and consumed.

---

## §3 SYSTEM-LEVEL VARIABLES (Outputs Produced by the System)

Variables are outputs that the Outreach system produces or mutates.

| Variable | Owner | Description |
|----------|-------|-------------|
| `outreach_id` | Outreach | Primary identifier minted by Outreach, registered ONCE in CL |
| `verified_email_pattern` | Company Target | Discovered and verified email pattern |
| `slot_assignments` | People Intelligence | Executive slot assignments (CEO, CFO, HR) |
| `bit_score` | BIT Engine | Buyer Intent Tool score (0-100) |
| `marketing_tier` | Sovereign Completion | Computed marketing eligibility tier (-1 to 3) |
| `engagement_events` | Outreach Execution | Campaign engagement tracking |
| `campaign_state` | Outreach Execution | Campaign workflow state |
| `contact_records` | People Intelligence | Enriched contact records |
| `ein_resolution` | DOL Filings | EIN discovery and linkage |
| `content_signals` | Blog Content | Content-derived timing signals |

**Rule**: Variables are PRODUCED by Outreach passes. They do not exist until transformation occurs.

---

## §4 PASS-TO-IMO MAPPING (MANDATORY)

The three constitutional passes map to IMO layers:

| Pass | IMO Layer | Role | Outreach Domain Binding |
|------|-----------|------|-------------------------|
| **CAPTURE** | **I** (Ingress) | Receive constants from external sources | CL identity reception, DOL data ingestion, enrichment intake |
| **COMPUTE** | **M** (Middle) | Transform constants into variables | Domain resolution, EIN matching, slot assignment, BIT scoring |
| **GOVERN** | **O** (Egress) | Emit governed variables with enforcement | Marketing eligibility, kill-switch application, tier assignment |

**This mapping is mandatory for all PRDs, ERDs, and Processes.**

---

## §5 SYSTEM BOUNDARY (What Outreach Owns vs Does NOT Own)

### Outreach OWNS (In Scope)

| Responsibility | Hub |
|----------------|-----|
| Minting `outreach_id` | Outreach Spine |
| Workflow state within Outreach | Outreach Spine |
| Email pattern discovery | Company Target |
| EIN resolution and linkage | DOL Filings |
| Executive slot assignment | People Intelligence |
| Movement detection | Talent Flow |
| Content signal detection | Blog Content |
| BIT score computation | BIT Engine |
| Marketing tier computation | Sovereign Completion |
| Kill-switch enforcement | Kill Switch System |
| Registering `outreach_id` in CL (WRITE-ONCE) | Outreach Spine |

### Outreach DOES NOT Own (Out of Scope)

| Responsibility | Owner |
|----------------|-------|
| Minting `sovereign_company_id` | CL (Company Lifecycle) |
| Minting `sales_process_id` | Sales Hub (future) |
| Minting `client_id` | Client Hub (future) |
| Company lifecycle transitions | CL (Company Lifecycle) |
| Modifying CL identity records | CL (Company Lifecycle) |
| Sales pipeline management | Sales Hub |
| Client relationship management | Client Hub |
| DOL filing original data | Federal DOL |
| LinkedIn source data | External Provider |

**Boundary Rule**: Outreach receives constants from CL and external sources, transforms them, and emits governed variables. It does NOT cross into CL, Sales, or Client authority.

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

## §6 SUB-HUB PASS OWNERSHIP

Each sub-hub is assigned to a primary pass for constitutional traceability:

| Sub-Hub | Doctrine ID | Primary Pass | Secondary Pass |
|---------|-------------|--------------|----------------|
| Company Target | 04.04.01 | COMPUTE | CAPTURE (domain intake) |
| DOL Filings | 04.04.03 | COMPUTE | CAPTURE (DOL data intake) |
| People Intelligence | 04.04.02 | COMPUTE | — |
| Talent Flow | 04.04.06 | COMPUTE | CAPTURE (movement signals) |
| Blog Content | 04.04.05 | COMPUTE | CAPTURE (content signals) |
| BIT Engine | — | COMPUTE | — |
| Outreach Execution | 04.04.04 | GOVERN | COMPUTE (campaign state) |
| Kill Switch System | — | GOVERN | — |
| Sovereign Completion | — | GOVERN | — |

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
- [x] **TRANSFORMATION STATEMENT present (§1)**
- [x] **CONSTANTS declared (§2)**
- [x] **VARIABLES declared (§3)**
- [x] **PASS-TO-IMO mapping present (§4)**
- [x] **SYSTEM BOUNDARY declared (§5)**
- [x] **SUB-HUB PASS OWNERSHIP declared (§6)**

**ALL CHECKS PASS. This file is CONSTITUTIONALLY VALID.**

---

## Document Control

| Field | Value |
|-------|-------|
| Created | 2026-01-28 |
| Last Modified | 2026-01-29 |
| Version | 2.0.0 |
| Status | CONSTITUTIONAL |
| Parent Doctrine | IMO-Creator |
| Derives From | PRD_CONSTITUTION.md, ERD_CONSTITUTION.md, PROCESS_DOCTRINE.md |
| Change Protocol | ADR + HUMAN APPROVAL REQUIRED |
| Validated | [x] YES |
