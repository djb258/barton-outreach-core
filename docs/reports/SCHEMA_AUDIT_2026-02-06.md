# Schema Audit Report — Outreach Database

**Date**: 2026-02-06
**Type**: READ-ONLY AUDIT
**Scope**: Outreach Hub + Sub-Hubs + Supporting Schemas

---

## Executive Summary

| Schema | Tables | Views | Classification |
|--------|--------|-------|----------------|
| **outreach** | 43 | 10 | HUB SPINE (BLOATED) |
| **people** | 23 | 10 | SUB-HUB |
| **dol** | 8 | 0 | SUB-HUB |
| **company** | 13 | 6 | SUB-HUB (LEGACY?) |
| **company_target** | 0 | 2 | SUB-HUB (VIEWS ONLY) |
| **blog** | 1 | 0 | SUB-HUB |
| **bit** | 4 | 2 | SUB-HUB |
| **cl** | 18 | 6 | AUTHORITY REGISTRY |
| **enrichment** | 3 | 4 | SOURCE (Hunter/Apollo) |
| **intake** | 5 | 0 | STAGING |
| **marketing** | 8 | 10 | LEGACY/REVIEW |
| **shq** | 3 | 8 | ERROR TRACKING |
| **archive** | 46 | 0 | ARCHIVE |
| **public** | 8 | 3 | MISC |
| **ref** | 2 | 0 | REFERENCE DATA |
| **catalog** | 4 | 3 | METADATA |
| **talent_flow** | 2 | 0 | ISOLATED LANE |

**CRITICAL FINDING**: `outreach` schema has 43 tables — far exceeds the "leaves can sprawl, trunk cannot" doctrine.

---

## PART 1: OUTREACH SCHEMA (HUB SPINE) — 43 Tables

### Classification

| Table | Rows | Type | Sub-Hub | Recommended Action |
|-------|------|------|---------|-------------------|
| **outreach** | 95,004 | CANONICAL | SPINE | KEEP (spine table) |
| **outreach_archive** | 27,416 | ARCHIVE | SPINE | KEEP |
| **outreach_errors** | 0 | ERROR | SPINE | KEEP |
| **outreach_excluded** | 3,775 | EXCLUSION | SPINE | KEEP |
| **outreach_legacy_quarantine** | 1,698 | QUARANTINE | SPINE | DEPRECATE |
| **outreach_orphan_archive** | 2,709 | ARCHIVE | SPINE | MERGE → outreach_archive |
| | | | | |
| **company_target** | 95,004 | CANONICAL | CT | MOVE → company_target schema |
| **company_target_archive** | 27,416 | ARCHIVE | CT | MOVE → company_target schema |
| **company_target_errors** | 4,404 | ERROR | CT | MOVE → company_target schema |
| **company_target_errors_archive** | 0 | ARCHIVE | CT | DEPRECATE (empty) |
| **company_target_orphaned_archive** | 52,812 | ARCHIVE | CT | MERGE → company_target_archive |
| **company_hub_status** | 68,908 | STATUS | CT | MOVE → company_target schema |
| | | | | |
| **dol** | 70,150 | CANONICAL | DOL | MOVE → dol schema |
| **dol_archive** | 1,623 | ARCHIVE | DOL | MOVE → dol schema |
| **dol_errors** | 29,740 | ERROR | DOL | MOVE → dol schema |
| **dol_errors_archive** | 0 | ARCHIVE | DOL | DEPRECATE (empty) |
| **dol_audit_log** | 0 | AUDIT | DOL | MOVE → dol schema |
| **dol_url_enrichment** | 16 | STAGING | DOL | MOVE → dol schema |
| | | | | |
| **blog** | 95,004 | CANONICAL | BLOG | MOVE → blog schema |
| **blog_archive** | 4,391 | ARCHIVE | BLOG | MOVE → blog schema |
| **blog_errors** | 2 | ERROR | BLOG | MOVE → blog schema |
| **blog_ingress_control** | 1 | REGISTRY | BLOG | MOVE → blog schema |
| **blog_source_history** | 0 | AUDIT | BLOG | MOVE → blog schema |
| | | | | |
| **people** | 324 | CANONICAL | PEOPLE | MOVE → people schema OR DEPRECATE |
| **people_archive** | 175 | ARCHIVE | PEOPLE | MOVE → people schema |
| **people_errors** | 0 | ERROR | PEOPLE | MOVE → people schema |
| | | | | |
| **bit_scores** | 13,226 | CANONICAL | BIT | MOVE → bit schema |
| **bit_scores_archive** | 1,806 | ARCHIVE | BIT | MOVE → bit schema |
| **bit_errors** | 0 | ERROR | BIT | MOVE → bit schema |
| **bit_signals** | 0 | STAGING | BIT | MOVE → bit schema |
| **bit_input_history** | 0 | AUDIT | BIT | DEPRECATE (empty) |
| | | | | |
| **appointments** | 130 | CANONICAL | EXECUTION | KEEP or MOVE → outreach_exec |
| **campaigns** | 0 | CANONICAL | EXECUTION | KEEP or MOVE → outreach_exec |
| **send_log** | 0 | AUDIT | EXECUTION | KEEP or MOVE → outreach_exec |
| **sequences** | 0 | CANONICAL | EXECUTION | KEEP or MOVE → outreach_exec |
| **engagement_events** | 0 | AUDIT | EXECUTION | KEEP or MOVE → outreach_exec |
| | | | | |
| **hub_registry** | 6 | REGISTRY | SPINE | KEEP |
| **column_registry** | 48 | REGISTRY | SPINE | KEEP |
| **manual_overrides** | 0 | REGISTRY | SPINE | KEEP |
| **override_audit_log** | 0 | AUDIT | SPINE | KEEP |
| **pipeline_audit_log** | 0 | AUDIT | SPINE | KEEP |
| **mv_credit_usage** | 2 | AUDIT | SPINE | KEEP |
| **entity_resolution_queue** | 2 | QUEUE | SPINE | KEEP |

### Outreach Schema Summary

| Category | Count | Action |
|----------|-------|--------|
| KEEP in outreach | 13 | Spine + registry + audit |
| MOVE to sub-hub schemas | 26 | CT, DOL, Blog, People, BIT |
| DEPRECATE | 4 | Empty or duplicate archives |

---

## PART 2: PEOPLE SCHEMA — 23 Tables

| Table | Rows | Type | Recommended Action |
|-------|------|------|-------------------|
| **company_slot** | 285,012 | CANONICAL | KEEP |
| **company_slot_archive** | 82,248 | ARCHIVE | KEEP |
| **people_master** | 201,181 | CANONICAL | KEEP |
| **people_master_archive** | 5,675 | ARCHIVE | KEEP |
| **people_errors** | 1,053 | ERROR | KEEP |
| **people_errors_archive** | 0 | ARCHIVE | DEPRECATE |
| **people_staging** | 139,861 | STAGING | KEEP |
| **people_candidate** | 0 | STAGING | DEPRECATE |
| **people_invalid** | 21 | ERROR | MERGE → people_errors |
| **people_promotion_audit** | 9 | AUDIT | KEEP |
| **people_resolution_history** | 0 | AUDIT | KEEP |
| **people_resolution_queue** | 1,206 | QUEUE | KEEP |
| **people_sidecar** | 0 | SIDECAR | DEPRECATE |
| **company_resolution_log** | 155 | AUDIT | KEEP |
| **paid_enrichment_queue** | 32,011 | QUEUE | KEEP |
| **person_movement_history** | 0 | AUDIT | KEEP |
| **person_scores** | 0 | SCORING | KEEP |
| **pressure_signals** | 0 | STAGING | DEPRECATE |
| **slot_assignment_history** | 1,370 | AUDIT | KEEP |
| **slot_ingress_control** | 1 | REGISTRY | KEEP |
| **slot_orphan_snapshot_r0_002** | 1,053 | SNAPSHOT | DEPRECATE after review |
| **slot_quarantine_r0_002** | 75 | QUARANTINE | DEPRECATE after review |
| **title_slot_mapping** | 43 | REGISTRY | KEEP |

### People Schema Summary

| Category | Count |
|----------|-------|
| KEEP | 16 |
| DEPRECATE | 7 |

---

## PART 3: DOL SCHEMA — 8 Tables

| Table | Rows | Type | Recommended Action |
|-------|------|------|-------------------|
| **form_5500** | 230,482 | SOURCE | KEEP |
| **form_5500_sf** | 760,839 | SOURCE | KEEP |
| **form_5500_icp_filtered** | 24,892 | DERIVED | KEEP (filtered view) |
| **schedule_a** | 337,476 | SOURCE | KEEP |
| **ein_urls** | 127,909 | ENRICHMENT | KEEP |
| **column_metadata** | 441 | REGISTRY | KEEP |
| **renewal_calendar** | 0 | DERIVED | KEEP |
| **pressure_signals** | 0 | STAGING | DEPRECATE |

### DOL Schema: Needs These from outreach.*

| Table to Move | Current Location |
|---------------|------------------|
| dol (canonical) | outreach.dol |
| dol_archive | outreach.dol_archive |
| dol_errors | outreach.dol_errors |
| dol_audit_log | outreach.dol_audit_log |

---

## PART 4: CL SCHEMA (Authority Registry) — 18 Tables

| Table | Rows | Type | Recommended Action |
|-------|------|------|-------------------|
| **company_identity** | 101,503 | CANONICAL | KEEP (authority) |
| **company_identity_archive** | 22,263 | ARCHIVE | KEEP |
| **company_identity_bridge** | 74,641 | IDENTITY MAP | KEEP |
| **company_identity_excluded** | 5,327 | EXCLUSION | KEEP |
| **company_candidate** | 62,162 | STAGING | KEEP |
| **company_domains** | 46,583 | CANONICAL | KEEP |
| **company_domains_archive** | 18,328 | ARCHIVE | KEEP |
| **company_domains_excluded** | 5,327 | EXCLUSION | KEEP |
| **company_names** | 70,843 | CANONICAL | KEEP |
| **company_names_archive** | 17,764 | ARCHIVE | KEEP |
| **company_names_excluded** | 7,361 | EXCLUSION | KEEP |
| **identity_confidence** | 46,583 | SCORING | KEEP |
| **identity_confidence_archive** | 19,850 | ARCHIVE | KEEP |
| **identity_confidence_excluded** | 5,327 | EXCLUSION | KEEP |
| **domain_hierarchy** | 4,705 | HIERARCHY | KEEP |
| **domain_hierarchy_archive** | 1,878 | ARCHIVE | KEEP |
| **cl_err_existence** | 7,985 | ERROR | KEEP |
| **cl_errors_archive** | 16,103 | ARCHIVE | KEEP |

**CL Status**: Clean. Follows doctrine.

---

## PART 5: ENRICHMENT SCHEMA — 3 Tables

| Table | Rows | Type | Recommended Action |
|-------|------|------|-------------------|
| **hunter_company** | 88,405 | SOURCE | KEEP |
| **hunter_contact** | 583,433 | SOURCE | KEEP |
| **column_registry** | 53 | REGISTRY | KEEP |

**Enrichment Status**: Clean. SOURCE tables only.

---

## PART 6: INTAKE SCHEMA — 5 Tables

| Table | Rows | Type | Recommended Action |
|-------|------|------|-------------------|
| **company_raw_intake** | 563 | STAGING | KEEP |
| **company_raw_wv** | 62,146 | STAGING | KEEP |
| **people_raw_intake** | 120,045 | STAGING | KEEP |
| **people_raw_wv** | 10 | STAGING | KEEP |
| **quarantine** | 2 | QUARANTINE | KEEP |

**Intake Status**: Clean. Staging only.

---

## PART 7: MARKETING SCHEMA — 8 Tables (REVIEW NEEDED)

| Table | Rows | Type | Recommended Action |
|-------|------|------|-------------------|
| **company_master** | 512 | UNKNOWN | REVIEW - duplicate of company.company_master? |
| **people_master** | 149 | UNKNOWN | REVIEW - duplicate of people.people_master? |
| **failed_company_match** | 32 | ERROR | MOVE → appropriate error table |
| **failed_email_verification** | 310 | ERROR | MOVE → people.people_errors |
| **failed_low_confidence** | 5 | ERROR | MOVE → appropriate error table |
| **failed_no_pattern** | 6 | ERROR | MOVE → company_target errors |
| **failed_slot_assignment** | 222 | ERROR | MOVE → people.people_errors |
| **review_queue** | 516 | QUEUE | KEEP or MOVE |

**Marketing Status**: LEGACY. Needs consolidation.

---

## PART 8: COMPANY SCHEMA — 13 Tables (LEGACY?)

| Table | Rows | Type | Recommended Action |
|-------|------|------|-------------------|
| **company_master** | 74,641 | CANONICAL? | REVIEW - relationship to CL? |
| **company_slots** | 1,359 | SLOTS | REVIEW - relationship to people.company_slot? |
| **company_source_urls** | 104,012 | ENRICHMENT | KEEP |
| **company_events** | 0 | AUDIT | DEPRECATE |
| **company_sidecar** | 0 | SIDECAR | DEPRECATE |
| **contact_enrichment** | 0 | STAGING | DEPRECATE |
| **email_verification** | 0 | STAGING | DEPRECATE |
| **message_key_reference** | 8 | REGISTRY | KEEP |
| **pipeline_errors** | 0 | ERROR | DEPRECATE |
| **pipeline_events** | 2,185 | AUDIT | KEEP |
| **url_discovery_failures** | 42,348 | ERROR | KEEP |
| **url_discovery_failures_archive** | 0 | ARCHIVE | DEPRECATE |
| **validation_failures_log** | 0 | ERROR | DEPRECATE |

**Company Status**: NEEDS REVIEW. Possible legacy schema.

---

## STEP 3: BORING & CLEAN TARGET MODEL

### Per Sub-Hub Structure (Doctrine Compliant)

#### SPINE (outreach schema)
```
CANONICAL:    outreach.outreach (95,004)
ERROR:        outreach.outreach_errors
ARCHIVE:      outreach.outreach_archive
REGISTRY:     outreach.hub_registry
              outreach.column_registry
              outreach.manual_overrides
AUDIT:        outreach.override_audit_log
              outreach.pipeline_audit_log
IDENTITY_MAP: outreach.outreach ↔ cl.company_identity (via sovereign_company_id)
```

#### COMPANY TARGET (company_target schema)
```
CANONICAL:    company_target.company_target
ERROR:        company_target.errors
ARCHIVE:      company_target.archive
REGISTRY:     company_target.hub_status
IDENTITY_MAP: company_target ↔ outreach.outreach (via outreach_id)
```

#### DOL (dol schema)
```
CANONICAL:    dol.dol_match (renamed from outreach.dol)
ERROR:        dol.errors
ARCHIVE:      dol.archive
AUDIT:        dol.audit_log
SOURCE:       dol.form_5500
              dol.form_5500_sf
              dol.schedule_a
              dol.ein_urls
REGISTRY:     dol.column_metadata
IDENTITY_MAP: dol_match ↔ outreach.outreach (via outreach_id)
              dol_match ↔ dol.ein_urls (via ein)
```

#### PEOPLE (people schema)
```
CANONICAL:    people.people_master (201,181)
              people.company_slot (285,012)
ERROR:        people.errors
ARCHIVE:      people.people_master_archive
              people.company_slot_archive
STAGING:      people.people_staging
QUEUE:        people.paid_enrichment_queue
              people.people_resolution_queue
AUDIT:        people.slot_assignment_history
              people.people_promotion_audit
REGISTRY:     people.title_slot_mapping
              people.slot_ingress_control
IDENTITY_MAP: people_master ↔ outreach.outreach (via outreach_id)
              company_slot ↔ people_master (via people_master_id)
```

#### BLOG (blog schema)
```
CANONICAL:    blog.blog (moved from outreach.blog)
ERROR:        blog.errors
ARCHIVE:      blog.archive
REGISTRY:     blog.ingress_control
IDENTITY_MAP: blog ↔ outreach.outreach (via outreach_id)
```

#### BIT (bit schema)
```
CANONICAL:    bit.bit_scores (moved from outreach.bit_scores)
ERROR:        bit.errors
ARCHIVE:      bit.archive
AUDIT:        bit.authorization_log
IDENTITY_MAP: bit_scores ↔ outreach.outreach (via outreach_id)
```

---

## STEP 4: GAP REPORT

### Missing Canonical Tables
- `blog` schema has only `pressure_signals` — needs `blog.blog` moved from outreach
- `company_target` schema has NO tables — needs canonicals moved from outreach
- `bit` schema has no `bit_scores` — needs moved from outreach

### Multiple Competing Canonicals
| Entity | Candidates | Winner |
|--------|------------|--------|
| Company Master | company.company_master, marketing.company_master, cl.company_identity | cl.company_identity (authority) |
| People Master | people.people_master, marketing.people_master, outreach.people | people.people_master |
| Company Slots | people.company_slot, company.company_slots | people.company_slot |

### Staging Tables Being Used as Truth
| Table | Issue |
|-------|-------|
| intake.company_raw_wv | 62K rows — should be processed |
| intake.people_raw_intake | 120K rows — should be processed |
| people.people_staging | 139K rows — needs promotion |

### Tables Without Clear Owner
| Table | Issue |
|-------|-------|
| company.company_master | Overlaps with CL |
| marketing.* | All tables need review |
| outreach.people | Only 324 rows — duplicate of people.people_master? |

### Illegal Sideways Dependencies
None detected in schema structure. Views may have cross-schema joins — needs code audit.

---

## STEP 5: REORG PLAN (NO EXECUTION)

### Phase 1: Schema Moves (Rename/Move)

```sql
-- Move CT tables to company_target schema
ALTER TABLE outreach.company_target SET SCHEMA company_target;
ALTER TABLE outreach.company_target_archive SET SCHEMA company_target;
ALTER TABLE outreach.company_target_errors SET SCHEMA company_target;
ALTER TABLE outreach.company_hub_status SET SCHEMA company_target;

-- Move DOL tables to dol schema
ALTER TABLE outreach.dol SET SCHEMA dol;
ALTER TABLE outreach.dol_archive SET SCHEMA dol;
ALTER TABLE outreach.dol_errors SET SCHEMA dol;
ALTER TABLE outreach.dol_audit_log SET SCHEMA dol;

-- Move Blog tables to blog schema
ALTER TABLE outreach.blog SET SCHEMA blog;
ALTER TABLE outreach.blog_archive SET SCHEMA blog;
ALTER TABLE outreach.blog_errors SET SCHEMA blog;
ALTER TABLE outreach.blog_ingress_control SET SCHEMA blog;

-- Move BIT tables to bit schema
ALTER TABLE outreach.bit_scores SET SCHEMA bit;
ALTER TABLE outreach.bit_scores_archive SET SCHEMA bit;
ALTER TABLE outreach.bit_errors SET SCHEMA bit;
```

### Phase 2: Consolidate Truth

```sql
-- Merge duplicate archives
INSERT INTO outreach.outreach_archive SELECT * FROM outreach.outreach_orphan_archive;
DROP TABLE outreach.outreach_orphan_archive;

INSERT INTO company_target.archive SELECT * FROM outreach.company_target_orphaned_archive;
DROP TABLE outreach.company_target_orphaned_archive;

-- Consolidate people errors
INSERT INTO people.errors SELECT * FROM people.people_invalid;
DROP TABLE people.people_invalid;
```

### Phase 3: Deprecate Empty/Unused Tables

```sql
-- Empty tables to drop after verification
DROP TABLE IF EXISTS outreach.company_target_errors_archive;  -- 0 rows
DROP TABLE IF EXISTS outreach.dol_errors_archive;             -- 0 rows
DROP TABLE IF EXISTS people.people_errors_archive;            -- 0 rows
DROP TABLE IF EXISTS people.people_candidate;                 -- 0 rows
DROP TABLE IF EXISTS people.people_sidecar;                   -- 0 rows
DROP TABLE IF EXISTS people.pressure_signals;                 -- 0 rows
DROP TABLE IF EXISTS dol.pressure_signals;                    -- 0 rows
DROP TABLE IF EXISTS bit.bit_input_history;                   -- 0 rows
DROP TABLE IF EXISTS company.company_events;                  -- 0 rows
DROP TABLE IF EXISTS company.company_sidecar;                 -- 0 rows
DROP TABLE IF EXISTS company.contact_enrichment;              -- 0 rows
DROP TABLE IF EXISTS company.email_verification;              -- 0 rows
DROP TABLE IF EXISTS company.pipeline_errors;                 -- 0 rows
DROP TABLE IF EXISTS company.validation_failures_log;         -- 0 rows
DROP TABLE IF EXISTS company.url_discovery_failures_archive;  -- 0 rows
```

### Phase 4: Define Identity Maps

```sql
-- Ensure FK constraints exist for identity maps
-- outreach ↔ CL
ALTER TABLE outreach.outreach
  ADD CONSTRAINT fk_outreach_cl
  FOREIGN KEY (sovereign_company_id)
  REFERENCES cl.company_identity(sovereign_company_id);

-- Sub-hubs ↔ Outreach
-- (After schema moves, add FKs to outreach_id)
```

### Phase 5: Rename for Clarity

```sql
-- Standardize error table names
ALTER TABLE company_target.company_target_errors RENAME TO errors;
ALTER TABLE dol.dol_errors RENAME TO errors;
ALTER TABLE blog.blog_errors RENAME TO errors;
ALTER TABLE bit.bit_errors RENAME TO errors;

-- Standardize archive table names
ALTER TABLE company_target.company_target_archive RENAME TO archive;
ALTER TABLE dol.dol_archive RENAME TO archive;
ALTER TABLE blog.blog_archive RENAME TO archive;
ALTER TABLE bit.bit_scores_archive RENAME TO archive;
```

---

## Summary: Before vs After

### Before (Current State)
```
outreach: 43 tables (BLOATED)
people: 23 tables
dol: 8 tables (missing hub tables)
blog: 1 table (missing hub tables)
bit: 4 tables (missing hub tables)
company_target: 0 tables (EMPTY!)
```

### After (Target State)
```
outreach: 13 tables (spine + registry + audit only)
company_target: 4 tables (canonical + error + archive + status)
dol: 10 tables (hub tables + source data)
blog: 4 tables (canonical + error + archive + registry)
bit: 4 tables (canonical + error + archive + audit)
people: 16 tables (after deprecations)
```

**Net Reduction**: 43 → 13 tables in outreach schema (70% reduction)

---

## Document Control

| Field | Value |
|-------|-------|
| Created | 2026-02-06 |
| Type | READ-ONLY AUDIT |
| Status | PROPOSED |
| Execution | REQUIRES APPROVAL |
