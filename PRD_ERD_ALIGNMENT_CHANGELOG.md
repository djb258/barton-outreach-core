# PRD ↔ ERD Alignment Changelog

**Alignment Date**: 2026-02-02
**Source of Truth**: Neon PostgreSQL (Production) via ERD Documentation
**Reference**: `hubs/*/SCHEMA.md`, `NEON_SCHEMA_REFERENCE_FOR_ERD.md`

---

## Summary

PRD documentation aligned with ERD documentation. ERD is authoritative (Neon > ERD > PRD).

| Metric | Value |
|--------|-------|
| PRDs Scanned | 29 |
| PRDs Updated | 4 |
| Stale References Fixed | 12 |
| ERD Citations Added | 4 |

---

## Critical Fixes

### 1. Marketing Schema Removal (DROPPED)

**Issue**: Multiple PRDs referenced `marketing.*` tables that no longer exist
**Fix**: Updated to current schema locations

**Files Updated**:
- `docs/prd/PRD_BIT_ENGINE.md`
- `docs/prd/PRD_OUTREACH_SPOKE.md`
- `docs/prd/PRD_COMPANY_HUB_PIPELINE.md`

**Stale References Removed**:

| Stale Reference | Replaced With |
|-----------------|---------------|
| `marketing.company_master` | `outreach.outreach` (spine) / `cl.company_identity` (registry) |
| `marketing.people_master` | `people.people_master` / `outreach.people` |
| `marketing.company_slot` | `people.company_slot` |
| `marketing.outreach_log` | `outreach.send_log` |
| `marketing.data_enrichment_log` | Removed (not in current schema) |

### 2. BIT Events Table Correction

**Issue**: PRDs referenced `bit.events` which doesn't exist
**Fix**: Changed to `outreach.bit_signals` (actual table)

**Files Updated**:
- `docs/prd/PRD_BIT_ENGINE.md`
- `docs/prd/PRD_TALENT_FLOW_SPOKE.md`

**Before**:
```sql
CREATE TABLE bit.events (
    event_id UUID PRIMARY KEY,
    company_id VARCHAR(25) REFERENCES marketing.company_master,
    ...
);
```

**After**:
```sql
CREATE TABLE outreach.bit_signals (
    signal_id UUID PRIMARY KEY,
    outreach_id UUID REFERENCES outreach.outreach(outreach_id),
    signal_type VARCHAR(50) NOT NULL,
    signal_impact NUMERIC NOT NULL,
    ...
);
```

### 3. Outreach Log Schema Correction

**Issue**: `marketing.outreach_log` doesn't exist
**Fix**: Changed to `outreach.send_log` with correct schema

**File Updated**: `docs/prd/PRD_OUTREACH_SPOKE.md`

**Key Changes**:
- Table name: `marketing.outreach_log` → `outreach.send_log`
- FK references updated to current outreach schema
- Column names aligned with ERD

### 4. People Tables Correction

**Issue**: `marketing.people_master`, `marketing.company_slot` don't exist
**Fix**: Changed to `people.*` schema tables

**File Updated**: `docs/prd/PRD_COMPANY_HUB_PIPELINE.md`

**Corrections**:
- `marketing.people_master` → `people.people_master`
- `marketing.company_slot` → `people.company_slot`
- Added `outreach.people` reference (outreach-attached people)

---

## ERD Citations Added

Each updated PRD now includes ERD reference comments:

| PRD File | ERD Citation Added |
|----------|-------------------|
| `PRD_BIT_ENGINE.md` | `> **ERD Reference**: hubs/outreach-execution/SCHEMA.md` |
| `PRD_OUTREACH_SPOKE.md` | `> **ERD Reference**: hubs/outreach-execution/SCHEMA.md` |
| `PRD_COMPANY_HUB_PIPELINE.md` | `> **ERD Reference**: hubs/people-intelligence/SCHEMA.md` |
| `PRD_TALENT_FLOW_SPOKE.md` | `(ERD: outreach.bit_signals)` inline comment |

---

## Files Updated

| File | Changes |
|------|---------|
| `docs/prd/PRD_BIT_ENGINE.md` | Replaced `bit.events` with `outreach.bit_signals`, removed marketing schema refs, added ERD citation |
| `docs/prd/PRD_OUTREACH_SPOKE.md` | Replaced `marketing.outreach_log` with `outreach.send_log`, updated FKs, added ERD citation |
| `docs/prd/PRD_COMPANY_HUB_PIPELINE.md` | Updated people/slot table references to `people.*` schema, added ERD citation |
| `docs/prd/PRD_TALENT_FLOW_SPOKE.md` | Replaced `bit.events` with `outreach.bit_signals` in dedup check |

---

## PRDs Verified (No Changes Needed)

These PRDs were scanned and contain no stale schema references:

| PRD File | Status |
|----------|--------|
| `PRD_KILL_SWITCH_SYSTEM.md` | ALIGNED (correct `manual_overrides`, `override_audit_log` refs) |
| `PRD_DOL_SUBHUB.md` | ALIGNED (correct `dol.*` schema refs) |
| `PRD_OUTREACH_EXECUTION_HUB.md` | ALIGNED (correct outreach schema refs) |

---

## Remaining Gaps (Lower Priority)

These items exist in PRDs but don't have direct ERD table mappings:

| Item | PRD | Notes |
|------|-----|-------|
| `public.shq_error_log` | Multiple PRDs | Global error table - exists but not in hub ERDs |

---

## Verification

Run this to verify no stale `marketing.*` references remain:

```bash
grep -r "marketing\." docs/prd/ --include="*.md"
```

Expected: No results (or only historical context references)

---

## Document Control

| Field | Value |
|-------|-------|
| Alignment Date | 2026-02-02 |
| Performed By | claude-code |
| ERD Source | `hubs/*/SCHEMA.md` |
| Schema Source | Neon PostgreSQL (Production) |
| CL-Outreach Alignment | 42,192 = 42,192 (ALIGNED) |
