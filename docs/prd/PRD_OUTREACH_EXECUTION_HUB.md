# PRD — Outreach Execution Hub (Operational Spine) v1.0

**Version:** 1.0 (Constitutional Compliance)
**Constitutional Date:** 2026-01-29
**Changes:** Initial creation per audit compliance requirement

---

## Conformance

| Field | Value |
|-------|-------|
| **Doctrine Version** | IMO-Creator v1.0 |
| **Domain Spec Reference** | `doctrine/REPO_DOMAIN_SPEC.md` |
| **CC Layer** | CC-02 |
| **PRD Constitution** | `templates/doctrine/PRD_CONSTITUTION.md` |
| **CTB Governance** | `docs/CTB_GOVERNANCE.md` |

---

## 1. Sovereign Reference (CC-01)

| Field | Value |
|-------|-------|
| **Sovereign ID** | CL-01 (Company Lifecycle) |
| **Sovereign Boundary** | Company identity minting and lifecycle state |

---

## 2. Hub Identity (CC-02)

| Field | Value |
|-------|-------|
| **Hub Name** | Outreach Execution |
| **Hub ID** | HUB-OUTREACH-EXECUTION |
| **Doctrine ID** | 04.04.04 |
| **Owner** | Barton Outreach Core |
| **Version** | 1.0 |
| **Role** | **SPINE OWNER** - All sub-hubs FK to this hub |

---

## 3. Purpose & Transformation Declaration

### Transformation Statement (REQUIRED)

> **"This hub transforms sovereign company identities from CL (CONSTANTS) into marketing-ready outreach records with campaign execution state, BIT scores, and engagement tracking (VARIABLES) through CAPTURE (identity binding from CL), COMPUTE (BIT scoring and campaign orchestration), and GOVERN (marketing safety gate and kill switch enforcement)."**

| Field | Value |
|-------|-------|
| **Transformation Summary** | Sovereign identity → Marketing-ready outreach record with engagement state |

### Constants (Inputs)

_Immutable inputs received from outside this hub. Reference: `doctrine/REPO_DOMAIN_SPEC.md §2`_

| Constant | Source | Description |
|----------|--------|-------------|
| `sovereign_company_id` | CL (Company Lifecycle) | Immutable company identity from CL |
| `eligibility_status` | CL (Company Lifecycle) | Commercial eligibility (ELIGIBLE/INELIGIBLE) |
| `identity_status` | CL (Company Lifecycle) | Identity verification status |

### Variables (Outputs)

_Outputs this hub produces. Reference: `doctrine/REPO_DOMAIN_SPEC.md §3`_

| Variable | Destination | Description |
|----------|-------------|-------------|
| `outreach_id` | All Sub-Hubs, CL (WRITE-ONCE) | Primary outreach identifier (minted here) |
| `bit_score` | Campaign Selection | Buyer intent score |
| `score_tier` | Marketing Gates | Tier classification (COLD/WARM/HOT/BURNING) |
| `campaign_state` | Execution Engine | Campaign execution status |
| `engagement_metrics` | Analytics | Open/click/reply counts |

### Pass Structure

_Constitutional pass mapping per `PRD_CONSTITUTION.md §Pass-to-IMO Mapping`_

| Pass | Type | IMO Layer | Description |
|------|------|-----------|-------------|
| Identity Binding | **CAPTURE** | I (Ingress) | Receive sovereign_company_id, mint outreach_id, write to CL |
| BIT Computation | **COMPUTE** | M (Middle) | Aggregate signals, compute score, assign tier |
| Campaign Orchestration | **COMPUTE** | M (Middle) | Select campaigns, build sequences, schedule sends |
| Marketing Safety Gate | **GOVERN** | O (Egress) | Enforce kill switch, block ineligible, audit all sends |

### Scope Boundary

| Scope | Description |
|-------|-------------|
| **IN SCOPE** | Outreach_id minting, BIT scoring, campaign management, send logging, engagement tracking, kill switch enforcement, marketing safety gate |
| **OUT OF SCOPE** | Sovereign identity minting (CL owns), email pattern discovery (Company Target owns), slot assignment (People owns), DOL filing data (DOL owns) |

---

## Hub Ownership Statement

```
╔═══════════════════════════════════════════════════════════════════════════════╗
║                    OUTREACH EXECUTION HUB OWNERSHIP                           ║
║                                                                               ║
║   This hub OWNS:                                                              ║
║   ├── outreach.outreach (THE SPINE - all sub-hubs FK here)                   ║
║   ├── outreach_id minting and CL registration                                ║
║   ├── BIT scoring (bit_scores, bit_signals)                                  ║
║   ├── Campaign orchestration (campaigns, sequences)                          ║
║   ├── Send logging (send_log, engagement_events)                             ║
║   ├── Kill switch system (manual_overrides, override_audit_log)              ║
║   └── Marketing safety gate (HARD_FAIL enforcement)                          ║
║                                                                               ║
║   This hub DOES NOT OWN:                                                      ║
║   ├── sovereign_company_id (CL owns)                                         ║
║   ├── Email pattern discovery (Company Target owns)                          ║
║   ├── Slot assignment (People Intelligence owns)                             ║
║   ├── DOL filing data (DOL Filings owns)                                     ║
║   └── Content signals (Blog Content owns)                                    ║
║                                                                               ║
║   All sub-hubs FK to outreach.outreach via outreach_id.                      ║
║   This hub defines the cascade deletion order for cleanup.                   ║
║                                                                               ║
╚═══════════════════════════════════════════════════════════════════════════════╝
```

---

## 4. The Golden Rule

```
IF outreach_id IS NULL:
    STOP. DO NOT PROCEED.
    1. Mint outreach_id in outreach.outreach (operational spine)
    2. Write outreach_id ONCE to cl.company_identity (authority registry)
    3. If CL write fails (already claimed) → HARD FAIL

ALIGNMENT RULE:
outreach.outreach count = cl.company_identity (outreach_id NOT NULL) count
Current: 95,004 = 95,004 ✓ ALIGNED
```

---

## 5. Tables Owned

### Primary Tables

| Schema | Table | Purpose | Records |
|--------|-------|---------|---------|
| `outreach` | `outreach` | **THE SPINE** - Root records | 95,004 |
| `outreach` | `outreach_archive` | Archived spine records | — |
| `outreach` | `outreach_orphan_archive` | Unfixable orphans | 2,709 |
| `outreach` | `campaigns` | Campaign definitions | — |
| `outreach` | `sequences` | Email sequence templates | — |
| `outreach` | `send_log` | Individual send tracking | — |
| `outreach` | `engagement_events` | All engagement events | — |
| `outreach` | `bit_scores` | BIT scores by outreach | 13,226 |
| `outreach` | `bit_signals` | BIT signal events | — |
| `outreach` | `manual_overrides` | Kill switch overrides | — |
| `outreach` | `override_audit_log` | Kill switch audit trail | — |
| `outreach` | `hub_registry` | Hub definitions | 6 |

### Views Owned

| View | Purpose |
|------|---------|
| `vw_marketing_eligibility_with_overrides` | **AUTHORITATIVE** marketing eligibility |
| `vw_sovereign_completion` | Sovereign completion status |
| `vw_tier_distribution` | Tier breakdown analytics |

---

## 6. BIT Scoring System

### Score Tiers

| Tier | Score Range | Description |
|------|-------------|-------------|
| COLD | 0-24 | No significant intent signals |
| WARM | 25-49 | Some intent signals detected |
| HOT | 50-74 | Strong intent signals |
| BURNING | 75+ | Very high intent, prioritize |

### Signal Sources

| Source Hub | Signal Type | Weight |
|------------|-------------|--------|
| Company Target | Domain verified | Base |
| DOL Filings | Renewal proximity | High |
| People Intelligence | Slot filled | Medium |
| Blog Content | News mention | Low |
| Talent Flow | Executive movement | Medium |

---

## 7. Kill Switch System

### Override Types

| Type | Effect | Duration |
|------|--------|----------|
| `BLOCK_OUTREACH` | Prevents all outreach | Until removed |
| `BLOCK_EMAIL` | Prevents email only | Until removed |
| `BLOCK_PHONE` | Prevents phone only | Until removed |
| `FORCE_TIER` | Override computed tier | Until expiry |

### Audit Requirements

**ALL override actions MUST be logged to `override_audit_log`.**

No exceptions. Audit bypass = system failure.

---

## 8. Marketing Safety Gate

### HARD_FAIL Conditions

| Condition | Action |
|-----------|--------|
| `tier = -1` | HARD_FAIL - Do not proceed |
| `marketing_disabled = true` | HARD_FAIL - Do not proceed |
| `eligibility_status = 'INELIGIBLE'` | HARD_FAIL - Do not proceed |
| Kill switch active | HARD_FAIL - Do not proceed |

### Gate Enforcement

```python
def marketing_safety_gate(outreach_id):
    record = get_marketing_eligibility(outreach_id)

    if record.tier == -1:
        HARD_FAIL("Tier -1: Marketing blocked")

    if record.marketing_disabled:
        HARD_FAIL("Marketing disabled flag set")

    if record.eligibility_status == 'INELIGIBLE':
        HARD_FAIL("Company is commercially ineligible")

    if has_active_kill_switch(outreach_id):
        HARD_FAIL("Kill switch active")

    return PROCEED
```

---

## 9. Cascade Deletion Order (AUTHORITATIVE)

When cleaning up orphaned records, delete in this order:

```
1. outreach.send_log          (FK: person_id, target_id)
2. outreach.sequences         (FK: campaign_id)
3. outreach.campaigns         (standalone)
4. outreach.manual_overrides  (FK: outreach_id)
5. outreach.bit_signals       (FK: outreach_id)
6. outreach.bit_scores        (FK: outreach_id)
7. outreach.blog              (FK: outreach_id) → Blog Hub
8. people.people_master       (FK: company_slot) → People Hub
9. people.company_slot        (FK: outreach_id) → People Hub
10. outreach.people           (FK: outreach_id) → People Hub
11. outreach.dol              (FK: outreach_id) → DOL Hub
12. outreach.company_target   (FK: outreach_id) → Company Target Hub
13. outreach.outreach         (SPINE - deleted LAST)
```

---

## 10. Explicit Exclusions

This hub does **NOT**:

- Mint sovereign_company_id (CL owns this)
- Discover email patterns (Company Target owns this)
- Assign people to slots (People Intelligence owns this)
- Import DOL filings (DOL Filings owns this)
- Collect blog signals (Blog Content owns this)
- Detect talent movement (Talent Flow owns this)
- Modify CL authority data (read-only after outreach_id write)

---

## 11. Dependencies

### Upstream (Receives From)

| Source | Data | Frequency |
|--------|------|-----------|
| CL | sovereign_company_id, eligibility_status | On company creation |
| Company Target | target_status, email_pattern | On target completion |
| DOL Filings | filing_signals, renewal_dates | On DOL processing |
| People Intelligence | slot_fill_status | On slot assignment |
| Blog Content | content_signals | On signal detection |

### Downstream (Sends To)

| Destination | Data | Trigger |
|-------------|------|---------|
| CL | outreach_id (WRITE-ONCE) | On outreach init |
| Email Provider | Send requests | On campaign execution |
| Analytics | Engagement events | On event capture |

---

## 12. ERD Reference

See: `hubs/outreach-execution/SCHEMA.md`

---

## 13. Traceability

| Document | Location |
|----------|----------|
| SCHEMA.md | `hubs/outreach-execution/SCHEMA.md` |
| Hub Manifest | `hubs/outreach-execution/hub.manifest.yaml` |
| Kill Switch PRD | `docs/prd/PRD_KILL_SWITCH_SYSTEM.md` |
| BIT Engine PRD | `docs/prd/PRD_BIT_ENGINE.md` |
| ADR | `docs/adr/ADR-011_CL_Authority_Registry_Outreach_Spine.md` |

---

## Document Control

| Field | Value |
|-------|-------|
| Created | 2026-01-29 |
| Last Modified | 2026-01-29 |
| Version | 1.0 |
| Status | ACTIVE |
| Authority | OPERATIONAL |
| Change Protocol | ADR + HUMAN APPROVAL REQUIRED |
