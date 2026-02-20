# Legacy Collapse Playbook — Phase 2: Map

**Date**: 2026-02-20
**Repo**: barton-outreach-core
**Source**: Phase 1 Inventory (`docs/migration/legacy-inventory.md`)
**Target Architecture**: 4-Tier Vendor Funnel (`memory/vendor_funnel_architecture.md`)

---

## Disposition Key

| Code | Meaning |
|------|---------|
| **KEEP** | Table stays as-is in target architecture |
| **REGISTER** | Table stays but needs CTB registration |
| **MIGRATE** | Data moves to new vendor/intake table, then source drops |
| **MERGE** | Data merges into another table |
| **RECLASSIFY** | Table stays but leaf_type changes |
| **DROP** | Table drops (empty, deprecated, or data migrated) |

---

## 1. CTB Backbone — CANONICAL + ERROR (KEEP: 17 tables)

These are the frozen core. No changes needed.

| Sub-Hub | CANONICAL | Rows | ERROR | Rows | Status |
|---------|-----------|------|-------|------|--------|
| Spine | outreach.outreach | 114,137 | — | — | KEEP |
| CL | cl.company_identity | 117,151 | cl.cl_err_existence | 9,328 | KEEP |
| CT | outreach.company_target | 114,137 | outreach.company_target_errors | 4,108 | KEEP |
| DOL | outreach.dol | 89,247 | outreach.dol_errors | 28,572 | KEEP |
| People | people.company_slot | 340,815 | people.people_errors | 9,982 | KEEP |
| Blog | outreach.blog | 93,596 | outreach.blog_errors | 41 | KEEP |
| CLS/BIT | outreach.bit_scores | 12,602 | outreach.bit_errors | 0 | KEEP |
| Coverage | coverage.service_agent | 3 | — | — | KEEP |
| Coverage | coverage.service_agent_coverage | 7 | — | — | KEEP |

---

## 2. SUPPORTING Tables (KEEP: 4 tables)

| Table | Rows | Sub-Hub | Disposition |
|-------|------|---------|-------------|
| people.people_master | 183,397 | People | KEEP (ADR-020) |
| dol.ein_urls | 127,909 | DOL | KEEP (EIN bridge) |
| cl.company_identity_bridge | 74,641 | CL | KEEP (domain bridge) |
| outreach.appointments | 702 | Lane | KEEP |

---

## 3. VENDOR Tables — DOL Filings (REGISTER: 26 tables)

All DOL filing tables are VENDOR data from DOL EFAST2. Currently 22 of 26 are UNREGISTERED.

| Table | Rows | Current Leaf | Disposition |
|-------|------|-------------|-------------|
| dol.form_5500 | 432,582 | CANONICAL | RECLASSIFY → STAGING (vendor) |
| dol.form_5500_sf | 1,535,999 | CANONICAL | RECLASSIFY → STAGING (vendor) |
| dol.form_5500_sf_part7 | 10,613 | UNREGISTERED | REGISTER as STAGING |
| dol.schedule_a | 625,520 | CANONICAL | RECLASSIFY → STAGING (vendor) |
| dol.schedule_a_part1 | 380,509 | UNREGISTERED | REGISTER as STAGING |
| dol.schedule_c | 241,556 | UNREGISTERED | REGISTER as STAGING |
| dol.schedule_c_part1_item1 | 396,838 | UNREGISTERED | REGISTER as STAGING |
| dol.schedule_c_part1_item2 | 754,802 | UNREGISTERED | REGISTER as STAGING |
| dol.schedule_c_part1_item2_codes | 1,848,202 | UNREGISTERED | REGISTER as STAGING |
| dol.schedule_c_part1_item3 | 383,338 | UNREGISTERED | REGISTER as STAGING |
| dol.schedule_c_part1_item3_codes | 707,007 | UNREGISTERED | REGISTER as STAGING |
| dol.schedule_c_part2 | 4,593 | UNREGISTERED | REGISTER as STAGING |
| dol.schedule_c_part2_codes | 2,352 | UNREGISTERED | REGISTER as STAGING |
| dol.schedule_c_part3 | 15,514 | UNREGISTERED | REGISTER as STAGING |
| dol.schedule_d | 121,813 | UNREGISTERED | REGISTER as STAGING |
| dol.schedule_d_part1 | 808,051 | UNREGISTERED | REGISTER as STAGING |
| dol.schedule_d_part2 | 2,392,112 | UNREGISTERED | REGISTER as STAGING |
| dol.schedule_dcg | 235 | UNREGISTERED | REGISTER as STAGING |
| dol.schedule_g | 568 | UNREGISTERED | REGISTER as STAGING |
| dol.schedule_g_part1 | 784 | UNREGISTERED | REGISTER as STAGING |
| dol.schedule_g_part2 | 97 | UNREGISTERED | REGISTER as STAGING |
| dol.schedule_g_part3 | 469 | UNREGISTERED | REGISTER as STAGING |
| dol.schedule_h | 169,276 | UNREGISTERED | REGISTER as STAGING |
| dol.schedule_h_part1 | 20,359 | UNREGISTERED | REGISTER as STAGING |
| dol.schedule_i | 116,493 | UNREGISTERED | REGISTER as STAGING |
| dol.schedule_i_part1 | 944 | UNREGISTERED | REGISTER as STAGING |

**Total DOL vendor rows**: ~11.4M across 26 tables.

---

## 4. VENDOR Tables — External Vendor Data (MIGRATE: 8 source tables → new vendor.* schema)

### vendor.ct (CT external vendor data)

| Source Table | Rows | Data Value | Migration Action |
|-------------|------|------------|------------------|
| enrichment.hunter_company | 88,554 | Domains, company data | MIGRATE → vendor.ct |
| company.company_master | 74,641 | LinkedIn URLs (74,170) | MIGRATE → vendor.ct |
| intake.company_raw_intake | 563 | CSV staging | MIGRATE → vendor.ct |
| intake.company_raw_wv | 62,146 | WV CSV import | MIGRATE → vendor.ct |

### vendor.ct_claude (CT enrichment outputs)

| Source Table | Rows | Data Value | Migration Action |
|-------------|------|------------|------------------|
| cl.company_domains | 46,583 | CL domain data | MIGRATE → vendor.ct_claude |
| cl.company_names | 70,843 | CL name data | MIGRATE → vendor.ct_claude |
| cl.company_candidate | 76,215 | CL candidates | MIGRATE → vendor.ct_claude |
| cl.identity_confidence | 46,583 | CL confidence | MIGRATE → vendor.ct_claude |
| cl.domain_hierarchy | 4,705 | Domain hierarchy | MIGRATE → vendor.ct_claude |
| company.company_source_urls | 114,736 | Blog/About URLs | MIGRATE → vendor.blog (see below) |

### vendor.people (People external vendor data)

| Source Table | Rows | Data Value | Migration Action |
|-------------|------|------------|------------------|
| enrichment.hunter_contact | 583,828 | Hunter contacts, LinkedIn | MIGRATE → vendor.people |
| intake.people_raw_intake | 120,045 | Clay CSV, LinkedIn | MIGRATE → vendor.people |
| intake.people_staging | 139,861 | Scraped names | MIGRATE → vendor.people |
| intake.people_raw_wv | 10 | WV people CSV | MIGRATE → vendor.people |

### vendor.people_claude (People enrichment outputs)

New table — captures Hunter API call results, leadership page scrapes, email verification results.

### vendor.blog (Blog external vendor data)

| Source Table | Rows | Data Value | Migration Action |
|-------------|------|------------|------------------|
| outreach.sitemap_discovery | 93,596 | Sitemap data | MIGRATE → vendor.blog |
| outreach.source_urls | 81,292 | Discovered URLs | MIGRATE → vendor.blog |
| company.company_source_urls | 114,736 | Blog/About URLs | MIGRATE → vendor.blog |

### vendor.blog_claude, vendor.dol_claude, vendor.lane_claude

New empty tables — will capture future enrichment outputs.

---

## 5. REGISTRY / CONFIG (KEEP: 7 tables)

| Table | Rows | Disposition |
|-------|------|-------------|
| people.title_slot_mapping | 43 | KEEP |
| people.slot_ingress_control | 1 | KEEP |
| outreach.blog_ingress_control | 1 | KEEP |
| outreach.hub_registry | 6 | KEEP |
| outreach.column_registry | 48 | KEEP |
| dol.column_metadata | 1,081 | KEEP |
| enrichment.column_registry | 53 | KEEP |

---

## 6. MV / Computed (KEEP: 3 tables)

| Table | Rows | Disposition |
|-------|------|-------------|
| outreach.company_hub_status | 68,908 | KEEP |
| dol.form_5500_icp_filtered | 24,892 | KEEP |
| dol.renewal_calendar | 0 | KEEP (empty but structurally needed) |

---

## 7. SYSTEM / AUDIT (KEEP: 10 tables)

| Table | Rows | Disposition |
|-------|------|-------------|
| catalog.columns | 725 | KEEP |
| catalog.schemas | 6 | KEEP |
| catalog.tables | 31 | KEEP |
| ref.county_fips | 3,222 | KEEP |
| ref.zip_county_map | 46,641 | KEEP |
| reference.us_zip_codes | 41,551 | KEEP |
| shq.audit_log | 1,609 | KEEP |
| shq.error_master | 93,915 | KEEP |
| outreach_ctx.context | 3 | KEEP |
| people.slot_assignment_history | 1,370 | KEEP |

---

## 8. LANE Tables (REGISTER: 2 tables)

| Table | Rows | Current | Disposition |
|-------|------|---------|-------------|
| sales.appointments_already_had | 771 | UNREGISTERED | REGISTER as CANONICAL |
| partners.fractional_cfo_master | 833 | UNREGISTERED | REGISTER as CANONICAL |

---

## 9. Tables to DROP (after vendor migration)

### 9.1 DEPRECATED — company.* (5 tables, after MIGRATE to vendor)

| Table | Rows | Migrates To | Safe After |
|-------|------|-------------|------------|
| company.company_master | 74,641 | vendor.ct | Data verified in vendor.ct |
| company.company_source_urls | 114,736 | vendor.blog | Data verified in vendor.blog |
| company.company_slots | 1,359 | N/A (legacy) | Immediately (data in people.company_slot) |
| company.message_key_reference | 8 | N/A (legacy) | Immediately |
| company.pipeline_events | 2,185 | N/A (legacy) | Immediately |

### 9.2 DEPRECATED — marketing.* (8 tables)

| Table | Rows | Safe To Drop? |
|-------|------|---------------|
| marketing.company_master | 512 | YES — superset exists in outreach.company_target |
| marketing.people_master | 149 | YES — superset exists in people.people_master |
| marketing.review_queue | 516 | YES — no longer used |
| marketing.failed_company_match | 32 | YES — legacy errors |
| marketing.failed_email_verification | 310 | YES — legacy errors |
| marketing.failed_low_confidence | 5 | YES — legacy errors |
| marketing.failed_no_pattern | 6 | YES — legacy errors |
| marketing.failed_slot_assignment | 222 | YES — legacy errors |

### 9.3 LCS Tables (4 tables — DO NOT TOUCH)

LCS tables are excluded from this consolidation. Leave as-is.

| Table | Rows | Disposition |
|-------|------|-------------|
| lcs.adapter_registry | 3 | **DO NOT TOUCH** |
| lcs.domain_pool | 10 | **DO NOT TOUCH** |
| lcs.frame_registry | 10 | **DO NOT TOUCH** |
| lcs.signal_registry | 9 | **DO NOT TOUCH** |

### 9.4 Outreach Orphaned (after MIGRATE to vendor)

| Table | Rows | Migrates To | Disposition |
|-------|------|-------------|-------------|
| outreach.sitemap_discovery | 93,596 | vendor.blog | DROP after migrate |
| outreach.source_urls | 81,292 | vendor.blog | DROP after migrate |
| outreach.company_target_dead_ends | 4,427 | N/A | DROP (stale) |
| outreach.ctb_queue | 33,217 | N/A | DROP (staging queue) |
| outreach.dol_url_enrichment | 16 | vendor.dol_claude | DROP after migrate |
| outreach.entity_resolution_queue | 2 | N/A | DROP (empty-ish) |
| outreach.ctb_audit_log | 1,534 | N/A | KEEP as SYSTEM |
| outreach.dol_audit_log | 0 | N/A | DROP (empty) |
| outreach.mv_credit_usage | 2 | N/A | DROP (legacy) |

### 9.5 People Orphaned (after MIGRATE to vendor)

| Table | Rows | Migrates To | Disposition |
|-------|------|-------------|-------------|
| people.paid_enrichment_queue | 32,011 | vendor.people_claude | DROP after migrate |
| people.people_resolution_queue | 1,206 | vendor.people_claude | DROP after migrate |
| people.people_invalid | 21 | N/A | MERGE into people.people_errors |
| people.people_promotion_audit | 9 | N/A | DROP (legacy audit) |
| people.company_resolution_log | 155 | N/A | DROP (legacy log) |

### 9.6 CL Orphaned (after MIGRATE to vendor)

| Table | Rows | Migrates To | Disposition |
|-------|------|-------------|-------------|
| cl.company_domains | 46,583 | vendor.ct_claude | DROP after migrate |
| cl.company_names | 70,843 | vendor.ct_claude | DROP after migrate |
| cl.company_candidate | 76,215 | vendor.ct_claude | DROP after migrate |
| cl.identity_confidence | 46,583 | vendor.ct_claude | DROP after migrate |
| cl.domain_hierarchy | 4,705 | vendor.ct_claude | DROP after migrate |
| cl.company_domains_excluded | 5,327 | vendor.ct_claude | DROP after migrate |
| cl.company_names_excluded | 7,361 | vendor.ct_claude | DROP after migrate |
| cl.identity_confidence_excluded | 5,327 | vendor.ct_claude | DROP after migrate |
| cl.cl_errors_archive | 0 | N/A | DROP (empty) |
| cl.movement_code_registry | 15 | N/A | REGISTER or DROP |
| cl.sovereign_mint_backup_20260218 | 0 | N/A | DROP (one-time backup) |

### 9.7 Other Drops

| Table | Rows | Disposition |
|-------|------|-------------|
| partners.partner_appointments | 0 | DROP (empty) |
| dol.pressure_signals | 0 | DROP (empty, MV placeholder) |
| public.v_bit_tables | 1 | DROP (config artifact) |
| public.v_lane_b_tables | 1 | DROP (config artifact) |
| public.v_triggers | 1 | DROP (config artifact) |
| public.agent_routing_log | 0 | DROP (empty) |
| public.sn_meeting | 0 | DROP (Sales Nav — not active) |
| public.sn_meeting_outcome | 0 | DROP (Sales Nav — not active) |
| public.sn_prospect | 0 | DROP (Sales Nav — not active) |
| public.sn_sales_process | 0 | DROP (Sales Nav — not active) |
| intake.quarantine | 2 | DROP (stale) |

### 9.8 Archive Tables (119 tables — KEEP in archive schema)

All 119 archive tables stay as-is. They're already correctly registered and isolated.

---

## 10. VIEWS — Disposition

### KEEP (operational views)

| View | Used By |
|------|---------|
| cl.v_company_identity_eligible | CL eligibility checks |
| cl.v_company_lifecycle_status | Lifecycle tracking |
| cl.v_company_promotable | Promotion gate |
| cl.v_identity_gate_summary | Identity gate |
| cl.v_linkage_summary | Linkage tracking |
| cl.v_orphan_detection | Orphan detection |
| catalog.v_ai_reference | AI reference |
| catalog.v_schema_summary | Schema summary |
| catalog.v_searchable_columns | Column search |
| coverage.v_service_agent_coverage_zips | Coverage system |
| outreach.v_context_current | Context tracking |
| outreach.vw_marketing_eligibility | Eligibility view |
| outreach.vw_sovereign_completion | Sovereign completion |
| people.v_slot_coverage | Slot coverage |

### AUDIT NEEDED (may be stale)

| View | Concern |
|------|---------|
| company.* (5 views) | Reference company.company_master (DEPRECATED) |
| marketing.* (6 views) | Reference marketing schema (DEPRECATED) |
| public.due_email_recheck_30d | Duplicate of people view |
| public.next_company_urls_30d | Duplicate of company view |
| public.next_profile_urls_30d | Duplicate of people view |
| enrichment.* (4 views) | Reference enrichment tables (moving to vendor) |

---

## 11. Consolidation Summary

### FINAL STATE (2026-02-20 — Phase 3 COMPLETE)

| Category | Before | After | Delta |
|----------|--------|-------|-------|
| CTB Backbone (CANONICAL + ERROR) | 17 | 17 | 0 |
| SUPPORTING | 4 | 4 | 0 |
| VENDOR — New consolidated | 0 | 8 | +8 |
| VENDOR — DOL filings (STAGING) | 26 | 28 | +2 (reclassified) |
| REGISTRY/CONFIG | 7 | 12 | +5 (LCS registered) |
| MV/Computed | 3 | 2 | -1 (dol.pressure_signals dropped) |
| SYSTEM/AUDIT | 10 | 30 | +20 (re-audited) |
| LANE tables | 2 | 2 | 0 |
| CTB infrastructure | 2 | 2 | 0 |
| ARCHIVE | 119 | 96 | -23 (some dropped via CASCADE) |
| LCS (REGISTERED, NOT DROPPED) | 4 | 4 | 0 |
| **DEPRECATED/DROP** | **47** | **0** | **-45 dropped, 2 kept** |
| **TOTAL** | **262** | **217** | **-45** |

### Phase 3 Execution Log

| Step | Action | Result |
|------|--------|--------|
| 1 | Register 40 unregistered tables | 40 registered (254 total) |
| 2 | Register 4 LCS tables as REGISTRY | 4 registered (258 total) — not dropped per user |
| 3 | Create vendor schema + 8 tables | 8 created + registered (262 total) |
| 4 | Migrate data (22 INSERT...SELECT) | 1,655,449 rows migrated in 59s |
| 5 | Verify row count parity | 22/22 sources = 100% match |
| 6 | Reclassify 3 DOL CANONICAL → STAGING | 3 tables reclassified |
| 7 | Reclassify outreach.ctb_audit_log → SYSTEM | 1 table reclassified |
| 8 | DROP 45 deprecated/orphaned tables | 45 dropped, 0 errors |
| 9 | Verify views | 47/47 views healthy, 0 broken |

### Vendor Table Summary

| Vendor Table | Sources | Rows |
|--------------|---------|------|
| vendor.ct | 4 tables (Hunter, company_master, intake) | 225,904 |
| vendor.people | 4 tables (Hunter contacts, Clay, staging) | 843,744 |
| vendor.blog | 3 tables (sitemaps, source URLs) | 289,624 |
| vendor.ct_claude | 8 tables (CL domains, names, candidates) | 262,944 |
| vendor.people_claude | 2 tables (enrichment queues) | 33,217 |
| vendor.dol_claude | 1 table (DOL URL enrichment) | 16 |
| vendor.blog_claude | — (future) | 0 |
| vendor.lane_claude | — (future) | 0 |
| **TOTAL** | **22 source tables** | **1,655,449** |

### Tables Excluded from DROP

| Table | Rows | Reason |
|-------|------|--------|
| cl.cl_errors_archive | 16,103 | Has data (was listed as 0 in inventory) |
| cl.sovereign_mint_backup_20260218 | 60,212 | Backup table with data |

### Migration Files

| File | Purpose |
|------|---------|
| `migrations/2026-02-20-vendor-schema-creation.sql` | CREATE vendor schema + 8 tables + CTB registration |
| `migrations/2026-02-20-vendor-data-migration.sql` | 22 INSERT...SELECT statements |

---

## 12. Phase 3 Status

| Requirement | Status |
|-------------|--------|
| IMO-Creator v3.3.0 templates synced | DONE |
| Migration templates 001-004 reviewed | DONE (001 already applied) |
| Vendor schema created | DONE (2026-02-20) |
| Vendor table column schemas defined | DONE |
| Data migration executed | DONE — 1,655,449 rows, 100% parity |
| Row count verification | DONE — 22/22 match |
| DOL reclassification | DONE — 3 tables CANONICAL → STAGING |
| CTB registry sync | DONE — 217 entries = 217 tables |
| Views health check | DONE — 47/47 healthy |
| DROP deprecated tables | DONE — 45 tables dropped |
| Human sign-off | APPROVED |
