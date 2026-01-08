# DOL Sub-Hub — IMO Compliance Checklist (v3.0)

**DOCTRINE LOCK**: This checklist enforces the DOL Sub-Hub IMO gate.
No code ships unless every box is checked. No exceptions. No partial compliance.

**Architecture**: Single-Pass IMO Gate
**PRD**: DOL Sub-Hub (EIN Lock-In) v3.0
**ADR**: ADR-DOL-002
**Tag**: `dol-ein-lock-v1.0`

---

## 0. Spine-First Gate (FIRST CHECK)

> DOL Sub-Hub operates on `outreach_id` from the Outreach Spine via Company Target.
> It joins through CL Bridge to get `company_unique_id`.

### Gate Enforcement

- [x] `outreach_id` exists in `outreach.outreach` spine
- [x] Join via `cl.company_identity_bridge` to get `company_unique_id`
- [x] `company_unique_id` resolved before EIN matching
- [x] Target state filter applied (WV, VA, PA, MD, OH, KY, DE, NC)

### Explicit Prohibitions

- [x] Does NOT mint company IDs
- [x] Does NOT use fuzzy matching
- [x] Does NOT retry failures
- [x] Does NOT read from CL tables directly (uses bridge join)
- [x] Does NOT perform AIR (Automated Intelligence Resolution)

---

## 1. IMO Input Stage (I)

### Required Inputs

- [x] `outreach_id` received via spine join (MANDATORY)
- [x] `sovereign_id` used for CL bridge join
- [x] `company_unique_id` resolved from CL bridge
- [x] `company_name` loaded for Form 5500 matching

### Input Validation

- [x] FAIL IMMEDIATELY if join path breaks → error logged
- [x] SKIP if company not in target states (expected)
- [x] Check idempotency: if already linked, skip

### Join Path Verification

- [x] `outreach.outreach.sovereign_id` → `cl.company_identity_bridge.company_sov_id`
- [x] `cl.company_identity_bridge.source_company_id` → `company.company_master.company_unique_id`

---

## 2. IMO Middle Stage (M)

### M1 — Priority 1: Direct EIN Lookup

- [x] Check `company.company_master.ein` for the company
- [x] If EIN exists and valid → use this EIN
- [x] If EIN is NULL → proceed to Priority 2

### M2 — Priority 2: Form 5500 Exact Name Match

- [x] Normalize company name (uppercase, strip punctuation)
- [x] Query `dol.form_5500` for exact `sponsor_dfe_name` match
- [x] Filter by target states (`spons_dfe_mail_us_state`)
- [x] If exactly 1 EIN found → use this EIN
- [x] If 0 EINs found → FAIL (DOL_EIN_MISSING)
- [x] If 2+ EINs found → FAIL (DOL_EIN_AMBIGUOUS)

### M3 — Canonical Rule Enforcement

- [x] 0 EIN = FAIL → `shq.error_master`
- [x] 1 EIN = PASS → `dol.ein_linkage`
- [x] 2+ EIN = FAIL → `shq.error_master`

### Forbidden Patterns

- [x] **NO** fuzzy name matching
- [x] **NO** Levenshtein distance
- [x] **NO** partial matches
- [x] **NO** retry loops
- [x] **NO** rescue patterns

---

## 3. IMO Output Stage (O)

### PASS Output

- [x] Write to `dol.ein_linkage`
- [x] `linkage_id` populated (UUID)
- [x] `company_unique_id` populated
- [x] `ein` populated
- [x] `source` = 'BACKFILL_5500_V1'
- [x] `source_url` populated (github ref)
- [x] `filing_year` populated
- [x] `hash_fingerprint` populated (dedup key)
- [x] `outreach_context_id` populated
- [x] `created_at` timestamp set

### FAIL Output

- [x] Write to `shq.error_master`
- [x] `error_id` populated (UUID)
- [x] `process_id` = '01.04.02.04.22000'
- [x] `agent_id` = 'DOL_EIN_BACKFILL_V1'
- [x] `severity` populated (INFO/WARN/ERROR)
- [x] `error_type` populated (DOL_EIN_MISSING/DOL_EIN_AMBIGUOUS)
- [x] `message` populated
- [x] `company_unique_id` populated
- [x] `context` populated (JSONB with details)
- [x] `created_at` timestamp set

---

## 4. Write Hygiene (HARD LAW)

### Allowed Writes

- [x] `dol.ein_linkage` (PASS)
- [x] `shq.error_master` (FAIL)

### Forbidden Writes

- [x] **NO** writes to `outreach.*` tables
- [x] **NO** writes to `company.*` tables
- [x] **NO** writes to `cl.*` tables
- [x] **NO** writes to `marketing.*` tables
- [x] **NO** writes upstream

---

## 5. Tool Registry Compliance

### Tier 0 (FREE) — USED

| Tool ID | Name | Purpose |
|---------|------|---------|
| DOL-001 | CSV Ingestion | Form 5500 data load |
| DOL-002 | EIN Resolution | Priority cascade |
| DOL-003 | Form 5500 Parser | Exact name matching |

### Tier 2 (PAID) — NOT USED

- [x] No paid tools in backfill
- [x] No external API calls
- [x] No enrichment services

### Forbidden Tools

- [x] No tools outside DOL registry
- [x] No bulk enrichment
- [x] No AIR tools

---

## 6. Forbidden Patterns (DEPRECATED)

The following are **permanently forbidden** in DOL Sub-Hub:

- [x] **NO** fuzzy EIN matching
- [x] **NO** fuzzy name matching
- [x] **NO** Levenshtein/Soundex/Metaphone
- [x] **NO** retry/backoff logic
- [x] **NO** hold queues
- [x] **NO** rescue patterns
- [x] **NO** ID minting
- [x] **NO** AIR resolution

---

## 7. Error Codes (v3.0)

### Input Stage Errors

| Code | Stage | Description |
|------|-------|-------------|
| `DOL-I-NO-COMPANY` | I | company_unique_id not resolved |
| `DOL-I-WRONG-STATE` | I | Company not in target states |

### Middle Stage Errors

| Code | Stage | Description |
|------|-------|-------------|
| `DOL_EIN_MISSING` | M | No EIN found (0 matches) |
| `DOL_EIN_AMBIGUOUS` | M | Multiple EINs found (2+ matches) |

---

## 8. Logging (MANDATORY)

Every IMO run MUST log:

- [x] `outreach_id` processed
- [x] IMO stage transitions (I → M → O)
- [x] EIN resolution outcome
- [x] Target table written
- [x] Error details (if FAIL)

---

## 9. Sovereign ID Compliance

- [x] Uses `sovereign_id` only for CL bridge join
- [x] Never exposes `sovereign_id` downstream
- [x] Filings attached to existing companies only
- [x] No company minting from DOL data

---

## 10. Geographic Filter Compliance

### Target States

- [x] WV (West Virginia)
- [x] VA (Virginia)
- [x] PA (Pennsylvania)
- [x] MD (Maryland)
- [x] OH (Ohio)
- [x] KY (Kentucky)
- [x] DE (Delaware)
- [x] NC (North Carolina)

### Filter Enforcement

- [x] Filter applied at input stage
- [x] Companies outside target states skipped (expected)
- [x] No errors logged for state filtering

---

## 11. Signal Validity Compliance

### Execution Order

- [x] Executes SECOND in canonical order (after CT)
- [x] Verifies Company Target must PASS before DOL
- [x] Verifies company_unique_id exists via CL bridge

### Signal Origin

- [x] `outreach_id` sourced via Outreach Spine
- [x] `company_unique_id` sourced via CL Bridge
- [x] EIN sourced via company_master or Form 5500
- [x] No signals consumed from downstream hubs

---

## 12. Kill-Switch Compliance

### Failure Doctrine

- [x] EIN not found → FAIL (no retry)
- [x] EIN ambiguous → FAIL (no retry)
- [x] All failures logged to `shq.error_master`
- [x] Human resolution required for ambiguous cases

### Cross-Hub Repair Rules

| Error Type | Resolution |
|------------|------------|
| `DOL_EIN_MISSING` | Enrichment Hub (future) |
| `DOL_EIN_AMBIGUOUS` | Manual resolution |

---

## 13. Repair Doctrine Compliance

### History Immutability

- [x] Error rows are never deleted (only `resolved_at` set)
- [x] Linkage rows once written are never modified
- [x] Prior contexts are never edited or reopened
- [x] Dedup hash prevents duplicate writes

### Repair Scope

- [x] This hub repairs only DOL_* errors
- [x] Does NOT repair CT_*, PI_*, OE_*, BC_* errors
- [x] Repairs unblock, they do not rewrite

---

## 14. CI Doctrine Compliance

### Tool Usage (DG-001, DG-002)

- [x] No paid tools in this hub
- [x] All tools listed in tool registry

### Hub Boundaries (DG-003)

- [x] No imports from downstream hubs (People, Blog)
- [x] No lateral hub-to-hub imports (only spoke imports)

### Doctrine Sync (DG-005, DG-006)

- [x] PRD changes accompanied by CHECKLIST changes
- [x] Error codes registered

### Signal Validity (DG-007, DG-008)

- [x] No old/prior context signal usage
- [x] No signal refresh patterns

### Immutability (DG-009, DG-010, DG-011, DG-012)

- [x] No lifecycle state mutations
- [x] No error row deletions
- [x] No context resurrection
- [x] No signal mutations

---

## 15. External CL + Program Scope Compliance

### CL is External

- [x] Understands CL is NOT part of Outreach program
- [x] Uses CL bridge table for joins only
- [x] Does NOT invoke Company Lifecycle directly
- [x] Receives company_unique_id via bridge join

### Outreach Context Authority

- [x] `outreach_id` sourced from Outreach Spine
- [x] All operations bound by `outreach_id`
- [x] Does NOT mint `outreach_id`

### Program Boundary Compliance

| Boundary | This Hub | Action |
|----------|----------|--------|
| CL (external) | DOL Filings | JOIN via bridge only |
| Company Target (upstream) | DOL Filings | CONSUME company_unique_id |
| People Intelligence (downstream) | DOL Filings | EMIT filing_signals, ein |
| Blog Content (downstream) | DOL Filings | EMIT filing_signals |

---

## 16. Backfill Verification (v1.0)

### Execution Verified

- [x] Dry run completed successfully
- [x] Production run completed successfully
- [x] All safety assertions passed

### Results Verified

- [x] `dol.ein_linkage` = 9,365 rows
- [x] `shq.error_master` = 51,212 rows
- [x] Source = 'BACKFILL_5500_V1'
- [x] Agent = 'DOL_EIN_BACKFILL_V1'

### Tag Verified

- [x] Git tag created: `dol-ein-lock-v1.0`
- [x] Commit: `c4fa5ad`

---

## Compliance Rule

**If any box is unchecked, this hub may not ship.**

---

**Last Updated**: 2026-01-08
**Hub**: DOL Filings (04.04.03)
**Doctrine Version**: External CL + Outreach Program v1.0
**Tag**: `dol-ein-lock-v1.0`
