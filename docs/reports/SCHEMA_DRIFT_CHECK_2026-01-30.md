# Schema Drift Check Report
**Date**: 2026-01-30
**Database**: Neon PostgreSQL (Marketing DB)
**Schemas Analyzed**: outreach, cl, people, bit, blog, dol, talent_flow
**Status**: v1.0 OPERATIONAL BASELINE (Post-Sovereign Cleanup)

---

## Executive Summary

**Total Tables**: 94
**Standard Operational**: 39 (41.5%)
**Archive Tables**: 15 (16.0%) - Expected after 2026-01-21 cleanup
**Orphan/Quarantine**: 9 (9.6%) - Data hygiene storage
**Error Tables**: 8 (8.5%) - Error tracking
**Audit/History**: 12 (12.8%) - Audit trails
**Control/Registry**: 5 (5.3%) - System control
**Candidate/Staging**: 6 (6.4%) - Pipeline staging

---

## Schema Breakdown

### 1. OUTREACH Schema - 39 tables (Largest)

#### Core Operational (12 tables)
| Table | Size | Purpose | Status |
|-------|------|---------|--------|
| `outreach.outreach` | 26 MB | Operational spine (FK anchor) | ACTIVE |
| `outreach.company_target` | 34 MB | Company intelligence hub | ACTIVE |
| `outreach.company_hub_status` | 41 MB | Hub status tracking | ACTIVE |
| `outreach.bit_scores` | 11 MB | BIT scoring engine | ACTIVE |
| `outreach.bit_signals` | 112 kB | Signal tracking | ACTIVE |
| `outreach.blog` | 12 MB | Blog content signals | ACTIVE |
| `outreach.dol` | 6.8 MB | DOL filings hub | ACTIVE |
| `outreach.people` | 432 kB | People intelligence hub | ACTIVE |
| `outreach.campaigns` | 40 kB | Campaign definitions | ACTIVE |
| `outreach.sequences` | 40 kB | Sequence definitions | ACTIVE |
| `outreach.engagement_events` | 72 kB | Engagement tracking | ACTIVE |
| `outreach.manual_overrides` | 32 kB | Kill switch system | ACTIVE |

#### Archive Tables (7 tables - Expected post-cleanup)
| Table | Size | Origin Date | Purpose |
|-------|------|-------------|---------|
| `outreach.outreach_archive` | 6.3 MB | 2026-01-21 | Sovereign cleanup archive |
| `outreach.company_target_archive` | 10 MB | 2026-01-21 | Sovereign cleanup archive |
| `outreach.people_archive` | 192 kB | 2026-01-21 | Sovereign cleanup archive |
| `outreach.blog_archive` | 1 MB | 2026-01-21 | Sovereign cleanup archive |
| `outreach.dol_archive` | 520 kB | 2026-01-21 | Sovereign cleanup archive |
| `outreach.bit_scores_archive` | 512 kB | 2026-01-21 | Sovereign cleanup archive |
| `outreach.outreach_orphan_archive` | 552 kB | 2026-01-21 | Orphan records archive |

#### Error Tables (6 tables)
| Table | Size | Purpose |
|-------|------|---------|
| `outreach.dol_errors` | 14 MB | DOL enrichment failures |
| `outreach.company_target_errors` | 1.9 MB | Company target failures |
| `outreach.blog_errors` | 64 kB | Blog ingestion failures |
| `outreach.bit_errors` | 48 kB | BIT scoring failures |
| `outreach.outreach_errors` | 112 kB | Outreach init failures |
| `outreach.people_errors` | 32 kB | People hub failures |

#### Audit/History (5 tables)
| Table | Size | Purpose |
|-------|------|---------|
| `outreach.pipeline_audit_log` | 264 kB | Pipeline execution audit |
| `outreach.dol_audit_log` | 224 kB | DOL enrichment audit |
| `outreach.override_audit_log` | 80 kB | Kill switch audit |
| `outreach.bit_input_history` | 64 kB | BIT input versioning |
| `outreach.blog_source_history` | 104 kB | Blog source tracking |
| `outreach.send_log` | 80 kB | Email send log |

#### Control/Quarantine (5 tables)
| Table | Size | Purpose |
|-------|------|---------|
| `outreach.outreach_excluded` | 528 kB | Excluded from marketing |
| `outreach.outreach_legacy_quarantine` | 288 kB | Legacy migration quarantine |
| `outreach.hub_registry` | 32 kB | Hub definitions |
| `outreach.column_registry` | 96 kB | Column metadata |
| `outreach.blog_ingress_control` | 48 kB | Blog ingress control |

#### Staging/Queue (3 tables)
| Table | Size | Purpose |
|-------|------|---------|
| `outreach.entity_resolution_queue` | 32 kB | Entity resolution queue |
| `outreach.mv_credit_usage` | 72 kB | Materialized view credits |
| `outreach.dol_url_enrichment` | 32 kB | DOL URL enrichment queue |

---

### 2. CL Schema - 18 tables (Authority Registry)

#### Core Operational (6 tables)
| Table | Size | Records | Purpose |
|-------|------|---------|---------|
| `cl.company_identity` | 125 MB | 296,296 | Authority registry (PARENT) |
| `cl.company_domains` | 21 MB | 245,837 | Domain registry |
| `cl.company_names` | 32 MB | 1,056,863 | Name variations |
| `cl.company_identity_bridge` | 30 MB | 579,816 | Identity bridge table |
| `cl.identity_confidence` | 16 MB | 542,978 | Confidence scoring |
| `cl.domain_hierarchy` | 2.4 MB | 31,881 | Domain relationships |

#### Archive Tables (6 tables - Expected post-cleanup)
| Table | Size | Origin Date | Purpose |
|-------|------|-------------|---------|
| `cl.cl_errors_archive` | 23 MB | 2026-01-21 | Error archive |
| `cl.company_identity_archive` | 18 MB | 2026-01-21 | Sovereign cleanup archive |
| `cl.company_names_archive` | 6.9 MB | 2026-01-21 | Name variations archive |
| `cl.company_domains_archive` | 6 MB | 2026-01-21 | Domain archive |
| `cl.identity_confidence_archive` | 2.8 MB | 2026-01-21 | Confidence archive |
| `cl.domain_hierarchy_archive` | 760 kB | 2026-01-21 | Hierarchy archive |

#### Excluded Tables (4 tables)
| Table | Size | Purpose |
|-------|------|---------|
| `cl.company_identity_excluded` | 11 MB | Excluded identities |
| `cl.company_names_excluded` | 2.6 MB | Excluded names |
| `cl.company_domains_excluded` | 1.8 MB | Excluded domains |
| `cl.identity_confidence_excluded` | 696 kB | Excluded confidence |

#### Error Tables (1 table)
| Table | Size | Purpose |
|-------|------|---------|
| `cl.cl_err_existence` | 3.3 MB | Existence check errors |

#### Staging (1 table)
| Table | Size | Purpose |
|-------|------|---------|
| `cl.company_candidate` | 54 MB | Company candidate pool |

---

### 3. PEOPLE Schema - 22 tables

#### Core Operational (8 tables)
| Table | Size | Records | Purpose |
|-------|------|---------|---------|
| `people.company_slot` | 59 MB | 153,444 | Slot assignments (CEO/CFO/HR) |
| `people.people_master` | 49 MB | 148,661 | Master contact records |
| `people.people_staging` | 65 MB | 273,028 | Staging/import queue |
| `people.people_sidecar` | 72 kB | - | Additional contact data |
| `people.person_scores` | 32 kB | - | Person scoring |
| `people.pressure_signals` | 112 kB | - | Movement signals |
| `people.people_promotion_audit` | 32 kB | - | Promotion audit |
| `people.title_slot_mapping` | 40 kB | - | Title-to-slot mapping |

#### Archive Tables (2 tables - Expected post-cleanup)
| Table | Size | Origin Date | Purpose |
|-------|------|-------------|---------|
| `people.company_slot_archive` | 25 MB | 2026-01-21 | Sovereign cleanup archive |
| `people.people_master_archive` | 2 MB | 2026-01-21 | Sovereign cleanup archive |

#### Queue/Staging (4 tables)
| Table | Size | Purpose |
|-------|------|---------|
| `people.paid_enrichment_queue` | 7.7 MB | Paid enrichment queue |
| `people.people_resolution_queue` | 488 kB | Resolution queue |
| `people.people_candidate` | 56 kB | Candidate pool |
| `people.people_invalid` | 144 kB | Invalid records |

#### Orphan/Quarantine (2 tables)
| Table | Size | Purpose |
|-------|------|---------|
| `people.slot_orphan_snapshot_r0_002` | 200 kB | Orphan snapshot (R0-002) |
| `people.slot_quarantine_r0_002` | 64 kB | Quarantine (R0-002) |

#### Audit/History (4 tables)
| Table | Size | Purpose |
|-------|------|---------|
| `people.slot_assignment_history` | 1.1 MB | Slot assignment history |
| `people.people_resolution_history` | 64 kB | Resolution history |
| `people.person_movement_history` | 40 kB | Movement tracking |
| `people.company_resolution_log` | 88 kB | Company resolution log |

#### Error Tables (1 table)
| Table | Size | Purpose |
|-------|------|---------|
| `people.people_errors` | 1.2 MB | People enrichment errors |

---

### 4. DOL Schema - 8 tables

#### Core Operational (6 tables)
| Table | Size | Records | Purpose |
|-------|------|---------|---------|
| `dol.form_5500_sf` | 630 MB | 950,619 | Form 5500 (short form) |
| `dol.schedule_a` | 297 MB | 716,821 | Schedule A (insurance) |
| `dol.form_5500` | 110 MB | 334,485 | Form 5500 (full) |
| `dol.ein_urls` | 57 MB | 738,479 | EIN-to-URL mappings |
| `dol.form_5500_icp_filtered` | 4.7 MB | - | ICP-filtered filings |
| `dol.renewal_calendar` | 56 kB | - | Renewal calendar |

#### Control (1 table)
| Table | Size | Purpose |
|-------|------|---------|
| `dol.column_metadata` | 576 kB | Column metadata registry |

#### Signals (1 table)
| Table | Size | Purpose |
|-------|------|---------|
| `dol.pressure_signals` | 56 kB | DOL pressure signals |

---

### 5. BIT Schema - 4 tables

#### Core Operational (4 tables)
| Table | Size | Purpose |
|-------|------|---------|
| `bit.proof_lines` | 48 kB | Proof line tracking |
| `bit.phase_state` | 40 kB | Phase state machine |
| `bit.movement_events` | 64 kB | Movement event tracking |
| `bit.authorization_log` | 48 kB | Authorization audit |

---

### 6. BLOG Schema - 1 table

#### Core Operational (1 table)
| Table | Size | Purpose |
|-------|------|---------|
| `blog.pressure_signals` | 56 kB | Blog content signals |

---

### 7. TALENT_FLOW Schema - 2 tables

#### Core Operational (2 tables)
| Table | Size | Purpose |
|-------|------|---------|
| `talent_flow.movements` | 120 kB | Movement tracking |
| `talent_flow.movement_history` | 64 kB | Movement history |

---

## Potential Issues & Recommendations

### 1. Archive Tables (15 total) - EXPECTED POST-CLEANUP
**Status**: All archive tables are from 2026-01-21 sovereign cleanup (23,025 records archived)
**Action**: KEEP - Required for audit compliance and potential rollback
**Retention Policy**: Recommend 90-day retention, then archive to cold storage
**Total Size**: ~100 MB across all schemas

### 2. Orphan/Quarantine Tables (9 total) - DATA HYGIENE
**Status**: Expected data hygiene storage
**Notable**:
- `people.slot_orphan_snapshot_r0_002` (200 kB) - Orphan snapshot from R0-002 cleanup
- `people.slot_quarantine_r0_002` (64 kB) - Quarantine from R0-002 cleanup
- `outreach.outreach_legacy_quarantine` (288 kB) - Legacy migration quarantine

**Action**: KEEP - Active data hygiene system
**Recommendation**: Review R0-002 snapshots for potential deletion (if older than 90 days)

### 3. Error Tables (8 total) - ERROR TRACKING
**Status**: Active error tracking system
**Notable**:
- `outreach.dol_errors` (14 MB) - Largest error table (DOL enrichment failures)
- `outreach.company_target_errors` (1.9 MB) - Company target failures

**Action**: KEEP - Required for debugging and retry logic
**Recommendation**: Implement 180-day rolling retention policy

### 4. Audit/History Tables (12 total) - AUDIT TRAILS
**Status**: Active audit trail system
**Total Size**: ~2.5 MB
**Action**: KEEP - Required for compliance and debugging
**Recommendation**: Implement 365-day rolling retention policy

### 5. Control/Registry Tables (5 total) - SYSTEM CONTROL
**Status**: Active system control tables
**Action**: KEEP - Core system metadata

### 6. Candidate/Staging Tables (6 total) - PIPELINE STAGING
**Status**: Active pipeline staging
**Notable**:
- `people.people_staging` (65 MB) - Largest staging table
- `people.paid_enrichment_queue` (7.7 MB) - Paid enrichment queue
- `cl.company_candidate` (54 MB) - Company candidate pool

**Action**: KEEP - Active pipeline tables
**Recommendation**: Monitor staging table growth (consider periodic archival)

---

## Undocumented or Suspicious Tables

### None Found - All Tables Are Documented

All 94 tables are either:
1. Core operational tables (documented in schema_map.json)
2. Archive tables from 2026-01-21 sovereign cleanup (expected)
3. Error/audit tables (system-generated)
4. Control/staging tables (pipeline infrastructure)

**No test tables, temp tables, or orphaned tables detected.**

---

## Schema Health Metrics

### Table Distribution by Schema
| Schema | Tables | % of Total | Total Size |
|--------|--------|------------|------------|
| outreach | 39 | 41.5% | ~170 MB |
| people | 22 | 23.4% | ~210 MB |
| cl | 18 | 19.1% | ~270 MB |
| dol | 8 | 8.5% | ~1.1 GB |
| bit | 4 | 4.3% | ~200 kB |
| talent_flow | 2 | 2.1% | ~180 kB |
| blog | 1 | 1.1% | ~56 kB |

### Archive Table Footprint
| Schema | Archive Tables | Archive Size | % of Schema |
|--------|----------------|--------------|-------------|
| outreach | 7 | ~18 MB | 10.6% |
| cl | 6 | ~57 MB | 21.1% |
| people | 2 | ~27 MB | 12.9% |

### Error Table Footprint
| Schema | Error Tables | Error Size | Largest Error Table |
|--------|--------------|------------|---------------------|
| outreach | 6 | ~16 MB | dol_errors (14 MB) |
| cl | 1 | 3.3 MB | cl_err_existence (3.3 MB) |
| people | 1 | 1.2 MB | people_errors (1.2 MB) |

---

## Alignment Check: CL → Outreach

**CL Authority Registry**:
- `cl.company_identity` (outreach_id NOT NULL): 51,148 records

**Outreach Operational Spine**:
- `outreach.outreach`: 51,148 records

**Alignment Status**: 51,148 = 51,148 ✓ ALIGNED

**Sub-Hub Coverage** (FK: outreach_id):
| Sub-Hub | Table | Records | Coverage |
|---------|-------|---------|----------|
| Company Target | outreach.company_target | 51,148 | 100.0% |
| DOL Filings | outreach.dol | 13,829 | 27.0% |
| People | outreach.people | 426 | 0.8% |
| Blog | outreach.blog | 51,148 | 100.0% |
| BIT Scores | outreach.bit_scores | 17,227 | 33.7% |

---

## Retention Policy Recommendations

### Archive Tables (15 tables, ~100 MB)
- **Retention**: 90 days
- **Action**: After 90 days, export to cold storage (S3/Glacier)
- **Reason**: Audit compliance, rollback capability

### Error Tables (8 tables, ~20 MB)
- **Retention**: 180 days (rolling)
- **Action**: Implement automated cleanup job
- **Reason**: Debugging history, pattern detection

### Audit/History Tables (12 tables, ~2.5 MB)
- **Retention**: 365 days (rolling)
- **Action**: Implement automated archival job
- **Reason**: Compliance, forensic analysis

### Staging Tables (6 tables, ~127 MB)
- **Retention**: 30 days (rolling)
- **Action**: Implement automated cleanup after promotion
- **Reason**: Pipeline staging, should be transient

### Orphan/Quarantine Tables (9 tables, ~5 MB)
- **Retention**: Review R0-002 snapshots (if older than 90 days, consider deletion)
- **Action**: Keep active quarantine tables
- **Reason**: Data hygiene system

---

## Conclusion

**Schema Health**: HEALTHY ✓
**Total Tables**: 94
**Undocumented Tables**: 0
**Test/Temp Tables**: 0
**Orphaned Tables**: 0

**Key Findings**:
1. All archive tables are expected from 2026-01-21 sovereign cleanup
2. Error tracking system is well-structured (8 tables, ~20 MB)
3. Audit trail system is comprehensive (12 tables, ~2.5 MB)
4. No schema drift detected - all tables are documented
5. CL-Outreach alignment is maintained: 51,148 = 51,148 ✓

**Recommendations**:
1. Implement retention policies for archive, error, and audit tables
2. Monitor staging table growth (people_staging: 65 MB, company_candidate: 54 MB)
3. Review R0-002 orphan snapshots for potential cleanup
4. Consider cold storage for 90-day+ archive tables
5. Implement automated cleanup jobs for error/audit tables

**Next Steps**:
1. Create retention policy automation (ADR recommended)
2. Set up monitoring alerts for staging table growth
3. Document retention policies in `docs/operations/retention-policy.md`
4. Schedule quarterly schema drift checks

---

**Report Generated**: 2026-01-30
**Database**: Neon PostgreSQL (Marketing DB)
**Baseline**: v1.0 OPERATIONAL BASELINE
**Status**: POST-SOVEREIGN CLEANUP (2026-01-21)
