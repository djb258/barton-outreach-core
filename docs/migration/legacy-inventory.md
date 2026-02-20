# Legacy Collapse Playbook — Phase 1: Inventory

**Date**: 2026-02-20
**Repo**: barton-outreach-core
**Playbook**: `templates/doctrine/LEGACY_COLLAPSE_PLAYBOOK.md`
**Mode**: READ-ONLY (Phase 1 & 2 — no changes made)

---

## 1. Database Inventory

### 1.1 Summary

| Category | Count |
|----------|-------|
| **Total base tables** | **254** |
| Archive tables | 119 |
| Non-archive tables | 135 |
| Views | 57 |
| Materialized views | 1 (`lcs.v_company_intelligence` — DROP candidate) |
| CTB-registered tables | 214 |
| **UNREGISTERED tables** | **40** |
| Phantom tables (in CTB, not in DB) | 0 |

### 1.2 Registration Status

| Leaf Type | Count |
|-----------|-------|
| ARCHIVE | 119 |
| UNREGISTERED | 40 |
| SYSTEM | 25 |
| CANONICAL | 23 |
| DEPRECATED | 13 |
| STAGING | 12 |
| ERROR | 9 |
| REGISTRY | 7 |
| SUPPORTING | 3 |
| MV | 3 |

### 1.3 Tables by Schema (Non-Archive)

#### cl (20 tables — 14 registered, 2 unregistered, 4 archive)

| Table | Leaf Type | Frozen | Rows | Notes |
|-------|-----------|--------|------|-------|
| company_identity | CANONICAL | FROZEN | 117,151 | Authority registry — DO NOT TOUCH |
| company_domains | CANONICAL | | 46,583 | Vendor data (CL identity) |
| company_names | CANONICAL | | 70,843 | Vendor data (CL identity) |
| company_candidate | STAGING | | 76,215 | Vendor data (CL staging) |
| company_identity_bridge | CANONICAL | | 74,641 | Domain bridge |
| company_identity_excluded | CANONICAL | | 5,327 | Exclusion registry |
| company_domains_excluded | CANONICAL | | 5,327 | Excluded domains |
| company_names_excluded | CANONICAL | | 7,361 | Excluded names |
| identity_confidence | CANONICAL | | 46,583 | Vendor data (confidence scores) |
| identity_confidence_excluded | CANONICAL | | 5,327 | Excluded confidence |
| domain_hierarchy | CANONICAL | | 4,705 | Domain hierarchy |
| cl_err_existence | ERROR | | 9,328 | CL error table |
| cl_errors_archive | ERROR | | 0 | Error archive |
| movement_code_registry | **UNREGISTERED** | | 15 | Registry seed data |
| sovereign_mint_backup_20260218 | **UNREGISTERED** | | 0 | One-time backup — DROP candidate |
| company_domains_archive | ARCHIVE | | — | |
| company_identity_archive | ARCHIVE | | — | |
| company_names_archive | ARCHIVE | | — | |
| domain_hierarchy_archive | ARCHIVE | | — | |
| identity_confidence_archive | ARCHIVE | | — | |

#### company (5 tables — ALL DEPRECATED)

| Table | Leaf Type | Rows | Notes |
|-------|-----------|------|-------|
| company_master | DEPRECATED | 74,641 | Has LinkedIn data — MIGRATE TO VENDOR before drop |
| company_source_urls | DEPRECATED | 114,736 | Has URL data — MIGRATE TO VENDOR before drop |
| company_slots | DEPRECATED | 1,359 | Legacy slot data |
| message_key_reference | DEPRECATED | 8 | Legacy reference |
| pipeline_events | DEPRECATED | 2,185 | Legacy events |

#### coverage (2 tables)

| Table | Leaf Type | Rows | Notes |
|-------|-----------|------|-------|
| service_agent | CANONICAL | 3 | Agent management |
| service_agent_coverage | CANONICAL | 7 | Market definitions |

#### ctb (2 tables — UNREGISTERED, self-referential)

| Table | Leaf Type | Rows | Notes |
|-------|-----------|------|-------|
| table_registry | UNREGISTERED | 214 | CTB infrastructure — cannot self-register |
| violation_log | UNREGISTERED | 0 | CTB infrastructure |

#### dol (31 tables — 7 registered, 22 unregistered filing tables, 2 registered other)

| Table | Leaf Type | Rows | Notes |
|-------|-----------|------|-------|
| form_5500 | CANONICAL | 432,582 | VENDOR — DOL filings |
| form_5500_sf | CANONICAL | 1,535,999 | VENDOR — DOL filings |
| form_5500_sf_part7 | **UNREGISTERED** | 10,613 | VENDOR — DOL filings |
| schedule_a | CANONICAL | 625,520 | VENDOR — DOL filings |
| schedule_a_part1 | **UNREGISTERED** | 380,509 | VENDOR — DOL filings |
| schedule_c | **UNREGISTERED** | 241,556 | VENDOR — DOL filings |
| schedule_c_part1_item1 | **UNREGISTERED** | 396,838 | VENDOR — DOL filings |
| schedule_c_part1_item2 | **UNREGISTERED** | 754,802 | VENDOR — DOL filings |
| schedule_c_part1_item2_codes | **UNREGISTERED** | 1,848,202 | VENDOR — DOL filings |
| schedule_c_part1_item3 | **UNREGISTERED** | 383,338 | VENDOR — DOL filings |
| schedule_c_part1_item3_codes | **UNREGISTERED** | 707,007 | VENDOR — DOL filings |
| schedule_c_part2 | **UNREGISTERED** | 4,593 | VENDOR — DOL filings |
| schedule_c_part2_codes | **UNREGISTERED** | 2,352 | VENDOR — DOL filings |
| schedule_c_part3 | **UNREGISTERED** | 15,514 | VENDOR — DOL filings |
| schedule_d | **UNREGISTERED** | 121,813 | VENDOR — DOL filings |
| schedule_d_part1 | **UNREGISTERED** | 808,051 | VENDOR — DOL filings |
| schedule_d_part2 | **UNREGISTERED** | 2,392,112 | VENDOR — DOL filings |
| schedule_dcg | **UNREGISTERED** | 235 | VENDOR — DOL filings |
| schedule_g | **UNREGISTERED** | 568 | VENDOR — DOL filings |
| schedule_g_part1 | **UNREGISTERED** | 784 | VENDOR — DOL filings |
| schedule_g_part2 | **UNREGISTERED** | 97 | VENDOR — DOL filings |
| schedule_g_part3 | **UNREGISTERED** | 469 | VENDOR — DOL filings |
| schedule_h | **UNREGISTERED** | 169,276 | VENDOR — DOL filings |
| schedule_h_part1 | **UNREGISTERED** | 20,359 | VENDOR — DOL filings |
| schedule_i | **UNREGISTERED** | 116,493 | VENDOR — DOL filings |
| schedule_i_part1 | **UNREGISTERED** | 944 | VENDOR — DOL filings |
| ein_urls | CANONICAL | 127,909 | SUPPORTING — EIN-to-domain bridge |
| form_5500_icp_filtered | MV | 24,892 | Materialized view candidate |
| renewal_calendar | CANONICAL | 0 | Empty — renewal calendar |
| pressure_signals | MV | 0 | Empty — DOL pressure signals |
| column_metadata | REGISTRY | 1,081 | Column metadata |

#### enrichment (3 tables — SYSTEM)

| Table | Leaf Type | Rows | Notes |
|-------|-----------|------|-------|
| hunter_company | SYSTEM | 88,554 | VENDOR — Hunter company data |
| hunter_contact | SYSTEM | 583,828 | VENDOR — Hunter contact data |
| column_registry | SYSTEM | 53 | Enrichment column metadata |

#### intake (6 tables — ALL STAGING)

| Table | Leaf Type | Rows | Notes |
|-------|-----------|------|-------|
| people_raw_intake | STAGING | 120,045 | VENDOR — Clay CSV import |
| people_staging | STAGING | 139,861 | VENDOR — scraped names |
| company_raw_wv | STAGING | 62,146 | VENDOR — WV CSV import |
| company_raw_intake | STAGING | 563 | VENDOR — company CSV import |
| people_raw_wv | STAGING | 10 | VENDOR — WV people CSV |
| quarantine | STAGING | 2 | Quarantine holding |

#### lcs (4 tables — ALL UNREGISTERED, seed data only)

| Table | Leaf Type | Rows | Notes |
|-------|-----------|------|-------|
| adapter_registry | UNREGISTERED | 3 | Seed data — lifecycle system scaffolding |
| domain_pool | UNREGISTERED | 10 | Seed data |
| frame_registry | UNREGISTERED | 10 | Seed data |
| signal_registry | UNREGISTERED | 9 | Seed data |

#### marketing (8 tables — ALL DEPRECATED)

| Table | Leaf Type | Rows | Notes |
|-------|-----------|------|-------|
| company_master | DEPRECATED | 512 | Legacy marketing data |
| people_master | DEPRECATED | 149 | Legacy marketing people |
| review_queue | DEPRECATED | 516 | Legacy review |
| failed_company_match | DEPRECATED | 32 | Legacy errors |
| failed_email_verification | DEPRECATED | 310 | Legacy errors |
| failed_low_confidence | DEPRECATED | 5 | Legacy errors |
| failed_no_pattern | DEPRECATED | 6 | Legacy errors |
| failed_slot_assignment | DEPRECATED | 222 | Legacy errors |

#### outreach (38 tables — 13 archive, 25 operational)

| Table | Leaf Type | Frozen | Rows | Notes |
|-------|-----------|--------|------|-------|
| outreach | CANONICAL | FROZEN | 114,137 | Operational spine |
| company_target | CANONICAL | FROZEN | 114,137 | CT sub-hub |
| dol | CANONICAL | FROZEN | 89,247 | DOL sub-hub |
| blog | CANONICAL | FROZEN | 93,596 | Blog sub-hub |
| bit_scores | CANONICAL | FROZEN | 12,602 | CLS sub-hub |
| people | SUPPORTING | FROZEN | 335,097 | People operational |
| appointments | SUPPORTING | | 702 | Lane: appointments |
| company_hub_status | MV | | 68,908 | Hub status MV |
| hub_registry | REGISTRY | | 6 | Hub definitions |
| blog_ingress_control | REGISTRY | | 1 | Blog config |
| column_registry | REGISTRY | | 48 | Outreach columns |
| company_target_errors | ERROR | | 4,108 | CT errors |
| dol_errors | ERROR | | 28,572 | DOL errors |
| blog_errors | ERROR | | 41 | Blog errors |
| bit_errors | ERROR | | 0 | CLS errors |
| url_discovery_failures | ERROR | | 42,348 | URL errors |
| company_target_dead_ends | **UNREGISTERED** | | 4,427 | Dead-end companies |
| sitemap_discovery | **UNREGISTERED** | | 93,596 | VENDOR — sitemap data |
| source_urls | **UNREGISTERED** | | 81,292 | VENDOR — discovered URLs |
| ctb_queue | STAGING | | 33,217 | CTB intake queue |
| dol_url_enrichment | STAGING | | 16 | DOL URL enrichment |
| entity_resolution_queue | STAGING | | 2 | Entity resolution |
| ctb_audit_log | SYSTEM | | 1,534 | CTB audit |
| dol_audit_log | SYSTEM | | 0 | DOL audit |
| mv_credit_usage | SYSTEM | | 2 | Credit tracking |
| outreach_excluded | ARCHIVE | | 5,483 | |
| outreach_legacy_quarantine | ARCHIVE | | 1,698 | |
| + 11 other archives | ARCHIVE | | — | |

#### partners (2 tables — UNREGISTERED)

| Table | Leaf Type | Rows | Notes |
|-------|-----------|------|-------|
| fractional_cfo_master | **UNREGISTERED** | 833 | Lane: Fractional CFO |
| partner_appointments | **UNREGISTERED** | 0 | Partner tracking — empty |

#### people (16 tables — 6 archive, 10 operational)

| Table | Leaf Type | Frozen | Rows | Notes |
|-------|-----------|--------|------|-------|
| company_slot | CANONICAL | FROZEN | 340,815 | Slot assignments |
| people_master | SUPPORTING | FROZEN | 183,397 | People records |
| people_errors | ERROR | | 9,982 | People errors |
| people_invalid | ERROR | | 21 | Invalid records |
| slot_ingress_control | REGISTRY | | 1 | Slot config |
| title_slot_mapping | REGISTRY | | 43 | Title mapping |
| paid_enrichment_queue | STAGING | | 32,011 | Enrichment queue |
| people_resolution_queue | STAGING | | 1,206 | Resolution queue |
| company_resolution_log | SYSTEM | | 155 | Resolution log |
| people_promotion_audit | SYSTEM | | 9 | Promotion audit |
| slot_assignment_history | SYSTEM | | 1,370 | Assignment history |

#### public (11 tables)

| Table | Leaf Type | Rows | Notes |
|-------|-----------|------|-------|
| migration_log | SYSTEM | 29 | Migration tracking |
| garage_runs | SYSTEM | 3 | Garage runs |
| shq_validation_log | SYSTEM | 9 | Validation |
| agent_routing_log | SYSTEM | 0 | Agent routing |
| sn_meeting | SYSTEM | 0 | Sales Navigator — not active |
| sn_meeting_outcome | SYSTEM | 0 | Sales Navigator — not active |
| sn_prospect | SYSTEM | 0 | Sales Navigator — not active |
| sn_sales_process | SYSTEM | 0 | Sales Navigator — not active |
| v_bit_tables | **UNREGISTERED** | 1 | Config table |
| v_lane_b_tables | **UNREGISTERED** | 1 | Config table |
| v_triggers | **UNREGISTERED** | 1 | Config table |

#### Other schemas

| Schema.Table | Leaf Type | Rows | Notes |
|-------------|-----------|------|-------|
| ref.county_fips | SYSTEM | 3,222 | Reference data |
| ref.zip_county_map | SYSTEM | 46,641 | Reference data |
| reference.us_zip_codes | REGISTRY | 41,551 | Reference data |
| outreach_ctx.context | SYSTEM | 3 | Context tracking |
| sales.appointments_already_had | **UNREGISTERED** | 771 | Lane: Appointments |
| shq.audit_log | SYSTEM | 1,609 | SHQ audit |
| shq.error_master | SYSTEM | 93,915 | Error aggregation |
| catalog.columns | SYSTEM | 725 | Schema catalog |
| catalog.schemas | SYSTEM | 6 | Schema catalog |
| catalog.tables | SYSTEM | 31 | Schema catalog |

### 1.4 Views (57 total)

| Schema | Count | Notes |
|--------|-------|-------|
| people | 10 | Slot coverage, extraction progress, monitoring |
| outreach | 8 | BIT tiers, eligibility, sovereign, CT repair |
| shq | 6 | Error governance, resolution, promotion |
| cl | 6 | Lifecycle, identity gate, orphan detection |
| marketing | 6 | CEO/CFO/HR views, enrichment needs, phase stats |
| company | 5 | Renewal, staleness, enrichment needs |
| enrichment | 4 | Hunter source analysis |
| catalog | 3 | AI reference, schema summary, searchable |
| public | 3 | Duplicates of people views (due_email, next_company, next_profile) |
| coverage | 1 | Service agent coverage ZIPs |
| company_target | 1 | Company authorization |

---

## 2. File System Inventory

### 2.1 Prohibited Directories: CLEAN

All 13 prohibited directories absent. No violations.

### 2.2 Execution Surfaces

| Surface | File Count | In CTB? | Status |
|---------|-----------|---------|--------|
| `hubs/` | 181 | YES (hub M-layers) | VALID |
| `spokes/` | 15 | YES (I/O connectors) | VALID |
| `ops/` | 44 | NO — outside CTB branches | **VIOLATION** |
| `scripts/` | 32 | NO — support surface only | NEEDS AUDIT |
| `src/sys/` | 35 | YES (CTB branch) | VALID |
| `tests/` | 23 | YES (test surface) | VALID |
| `migrations/` | 77 | YES (support surface) | VALID |

### 2.3 Banned DB Client Usage

Direct `psycopg2`/`asyncpg` imports found throughout:
- `hubs/` — All hub M-layers use `psycopg2` directly
- `ops/` — Operations scripts use `psycopg2` directly
- `scripts/` — Utility scripts use `psycopg2` directly

**Note**: This is expected for a Python/PostgreSQL codebase. The Gatekeeper module template is TypeScript (Deno). A Python Gatekeeper equivalent would need to be created. This is a Phase 3 consideration, not a blocking issue.

### 2.4 Migration Files: 77 SQL files

Legacy migrations span from early numbered (`0001-0010`) through date-stamped (`2025-11 through 2026-02`). All in `migrations/` directory (correct location per Execution Surface Law).

---

## 3. Key Findings

| # | Finding | Severity | Impact |
|---|---------|----------|--------|
| 1 | 40 UNREGISTERED tables | HIGH | Must register in CTB before any enforcement migrations |
| 2 | 22 DOL filing tables unregistered | HIGH | Vendor tables need STAGING leaf_type registration |
| 3 | 13 DEPRECATED tables (company.*, marketing.*) | MEDIUM | Need vendor data migration then drop |
| 4 | 119 ARCHIVE tables in single schema | LOW | Organized, no action needed |
| 5 | `ops/` directory is outside CTB branches | MEDIUM | Execution Surface Law violation (future) |
| 6 | Direct psycopg2 throughout codebase | INFO | Expected — Python Gatekeeper not yet created |
| 7 | 57 views across 11 schemas | MEDIUM | Need audit for stale/orphaned views |
| 8 | `company.company_master` (74K LinkedIn) + `company.company_source_urls` (115K URLs) marked DEPRECATED | **CRITICAL** | Vendor data MUST migrate to vendor.* BEFORE drop |
