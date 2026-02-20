# DATABASE AUDIT -- Complete Table & Column Inventory

> **Source**: Neon PostgreSQL (live query)
> **Generated**: 2026-02-20
> **Cross-referenced**: `ctb.table_registry` + `column_registry.yml`
> **Authority**: This document is a PROJECTION of the live database. Regenerate with:
> `doppler run -- python scripts/generate_database_audit.py`

---

## Executive Summary

| Metric | Count |
|--------|-------|
| **Total tables** | **296** |
| Total columns | 5,635 |
| CTB registered | 241 |
| **UNREGISTERED** | **55** |
| Unregistered WITH data | 34 |
| Deprecated WITH data | 13 |
| Frozen core tables | 9 |
| Columns in column_registry.yml | 55 |
| **Column documentation gap** | **5,580 columns undocumented** |
| Views | 64 |
| Schemas | 22 |

---

## Critical Issues

### 1. UNREGISTERED Tables with Data

These tables exist in the database but are NOT in `ctb.table_registry`.
They need to be registered with a leaf type or retired.

| Schema | Table | Rows | Recommended Action |
|--------|-------|------|--------------------|
| dol | schedule_d_part2 | 2,392,252 | Register as CANONICAL (DOL filing data from EFAST2) |
| dol | schedule_c_part1_item2_codes | 1,848,202 | Register as CANONICAL (DOL filing data from EFAST2) |
| dol | schedule_d_part1 | 808,051 | Register as CANONICAL (DOL filing data from EFAST2) |
| dol | schedule_c_part1_item2 | 754,802 | Register as CANONICAL (DOL filing data from EFAST2) |
| dol | schedule_c_part1_item3_codes | 707,007 | Register as CANONICAL (DOL filing data from EFAST2) |
| dol | schedule_c_part1_item1 | 396,838 | Register as CANONICAL (DOL filing data from EFAST2) |
| dol | schedule_c_part1_item3 | 383,338 | Register as CANONICAL (DOL filing data from EFAST2) |
| dol | schedule_a_part1 | 380,509 | Register as CANONICAL (DOL filing data from EFAST2) |
| dol | schedule_c | 241,556 | Register as CANONICAL (DOL filing data from EFAST2) |
| dol | schedule_h | 169,276 | Register as CANONICAL (DOL filing data from EFAST2) |
| dol | schedule_d | 121,813 | Register as CANONICAL (DOL filing data from EFAST2) |
| dol | schedule_i | 116,493 | Register as CANONICAL (DOL filing data from EFAST2) |
| outreach | sitemap_discovery | 93,596 | Register as SYSTEM or migrate to outreach.blog |
| outreach | source_urls | 81,292 | Migrate data to outreach.blog, then DROP |
| cl | sovereign_mint_backup_20260218 | 60,212 | Register as ARCHIVE (backup table) |
| dol | schedule_h_part1 | 20,359 | Register as CANONICAL (DOL filing data from EFAST2) |
| dol | schedule_c_part3 | 15,514 | Register as CANONICAL (DOL filing data from EFAST2) |
| dol | form_5500_sf_part7 | 10,613 | Register as CANONICAL (DOL filing data) |
| dol | schedule_c_part2 | 4,593 | Register as CANONICAL (DOL filing data from EFAST2) |
| outreach | company_target_dead_ends | 4,427 | Register as ERROR or ARCHIVE |
| dol | schedule_c_part2_codes | 2,352 | Register as CANONICAL (DOL filing data from EFAST2) |
| dol | schedule_i_part1 | 944 | Register as CANONICAL (DOL filing data from EFAST2) |
| partners | fractional_cfo_master | 833 | Register as CANONICAL (messaging lane) |
| dol | schedule_g_part1 | 784 | Register as CANONICAL (DOL filing data from EFAST2) |
| sales | appointments_already_had | 771 | Register as CANONICAL (messaging lane) |
| dol | schedule_g | 568 | Register as CANONICAL (DOL filing data from EFAST2) |
| dol | schedule_g_part3 | 469 | Register as CANONICAL (DOL filing data from EFAST2) |
| dol | schedule_dcg | 235 | Register as CANONICAL (DOL filing data from EFAST2) |
| dol | schedule_g_part2 | 97 | Register as CANONICAL (DOL filing data from EFAST2) |
| cl | movement_code_registry | 15 | Register as REGISTRY |
| lcs | domain_pool | 10 | Register as SYSTEM (lifecycle signals) |
| lcs | frame_registry | 10 | Register as SYSTEM (lifecycle signals) |
| lcs | signal_registry | 9 | Register as SYSTEM (lifecycle signals) |
| lcs | adapter_registry | 3 | Register as SYSTEM (lifecycle signals) |

### 2. DEPRECATED Tables with Data

These are marked DEPRECATED in CTB but still contain data.
Data should be migrated to canonical tables before dropping.

| Schema | Table | Rows | Canonical Replacement |
|--------|-------|------|-----------------------|
| company | company_source_urls | 114,736 | outreach.blog (about_url, news_url) + migration needed for other page types |
| company | company_master | 92,116 | cl.company_identity + outreach.company_target |
| company | pipeline_events | 2,185 | outreach.pipeline_audit_log |
| company | company_slots | 1,359 | people.company_slot |
| marketing | review_queue | 516 | None (legacy) |
| marketing | company_master | 512 | outreach.company_target |
| marketing | failed_email_verification | 310 | people.people_errors |
| marketing | failed_slot_assignment | 222 | people.people_errors |
| marketing | people_master | 149 | people.people_master |
| marketing | failed_company_match | 32 | outreach.company_target_errors |
| company | message_key_reference | 8 | None (legacy) |
| marketing | failed_no_pattern | 6 | outreach.company_target_errors |
| marketing | failed_low_confidence | 5 | outreach.company_target_errors |

### 3. Column Documentation Gap

The `column_registry.yml` documents **55 columns** across 13 tables.
The database has **5,635 columns** across 296 tables.
**5,580 columns (99%) have NO description, semantic_role, or format.**

Every column should have:
- `description`: What the column stores
- `semantic_role`: identifier | foreign_key | attribute | metric
- `format`: UUID | STRING | EMAIL | ENUM | BOOLEAN | INTEGER | ISO-8601 | NUMERIC

---

## Schema-by-Schema Inventory

### `cl` -- Authority Registry -- sovereign company identity, lifecycle pointers

**Tables**: 20 | **Total rows**: 625,804
**Views**: 6 -- v_company_identity_eligible, v_company_lifecycle_status, v_company_promotable, v_identity_gate_summary, v_linkage_summary, v_orphan_detection

| Table | Leaf Type | Frozen | Rows | Columns | Documented |
|-------|-----------|--------|------|---------|------------|
| `cl_err_existence` | ERROR |  | 9,328 | 18 | 0 |
| `cl_errors_archive` | ERROR |  | 16,103 | 19 | 0 |
| `company_candidate` | STAGING |  | 76,215 | 11 | 0 |
| `company_domains` | CANONICAL |  | 46,583 | 7 | 0 |
| `company_domains_archive` | ARCHIVE |  | 18,328 | 9 | 0 |
| `company_domains_excluded` | CANONICAL |  | 5,327 | 7 | 0 |
| `company_identity` | CANONICAL | YES | 117,151 | 35 | 0 |
| `company_identity_archive` | ARCHIVE |  | 22,263 | 28 | 0 |
| `company_identity_bridge` | CANONICAL |  | 74,641 | 7 | 0 |
| `company_identity_excluded` | CANONICAL |  | 5,327 | 33 | 0 |
| `company_names` | CANONICAL |  | 70,843 | 5 | 0 |
| `company_names_archive` | ARCHIVE |  | 17,764 | 7 | 0 |
| `company_names_excluded` | CANONICAL |  | 7,361 | 5 | 0 |
| `domain_hierarchy` | CANONICAL |  | 4,705 | 8 | 0 |
| `domain_hierarchy_archive` | ARCHIVE |  | 1,878 | 10 | 0 |
| `identity_confidence` | CANONICAL |  | 46,583 | 4 | 0 |
| `identity_confidence_archive` | ARCHIVE |  | 19,850 | 6 | 0 |
| `identity_confidence_excluded` | CANONICAL |  | 5,327 | 4 | 0 |
| `movement_code_registry` | UNREGISTERED |  | 15 | 5 | 0 |
| `sovereign_mint_backup_20260218` | UNREGISTERED |  | 60,212 | 4 | 0 |

#### `cl.cl_err_existence` -- ERROR -- 9,328 rows

Column registry: **UNDOCUMENTED**

| # | Column | Type | Null | Description | Role | Format |
|---|--------|------|------|-------------|------|--------|
| 1 | `error_id` | uuid | N | **MISSING** | -- | -- |
| 2 | `company_unique_id` | uuid | N | **MISSING** | -- | -- |
| 3 | `company_name` | text | Y | **MISSING** | -- | -- |
| 4 | `company_domain` | text | Y | **MISSING** | -- | -- |
| 5 | `linkedin_company_url` | text | Y | **MISSING** | -- | -- |
| 6 | `reason_code` | text | N | **MISSING** | -- | -- |
| 7 | `domain_status_code` | integer | Y | **MISSING** | -- | -- |
| 8 | `domain_redirect_chain` | ARRAY | Y | **MISSING** | -- | -- |
| 9 | `domain_final_url` | text | Y | **MISSING** | -- | -- |
| 10 | `domain_error` | text | Y | **MISSING** | -- | -- |
| 11 | `extracted_name` | text | Y | **MISSING** | -- | -- |
| 12 | `name_match_score` | integer | Y | **MISSING** | -- | -- |
| 13 | `extracted_state` | text | Y | **MISSING** | -- | -- |
| 14 | `state_match_result` | text | Y | **MISSING** | -- | -- |
| 15 | `evidence` | jsonb | Y | **MISSING** | -- | -- |
| 16 | `verification_run_id` | text | N | **MISSING** | -- | -- |
| 17 | `created_at` | timestamp with time zone | Y | **MISSING** | -- | -- |
| 18 | `error_type` | character varying(100) | Y | **MISSING** | -- | -- |

#### `cl.cl_errors_archive` -- ERROR -- 16,103 rows

Column registry: **UNDOCUMENTED**

| # | Column | Type | Null | Description | Role | Format |
|---|--------|------|------|-------------|------|--------|
| 1 | `error_id` | uuid | N | **MISSING** | -- | -- |
| 2 | `company_unique_id` | uuid | Y | **MISSING** | -- | -- |
| 3 | `lifecycle_run_id` | text | N | **MISSING** | -- | -- |
| 4 | `pass_name` | text | N | **MISSING** | -- | -- |
| 5 | `failure_reason_code` | text | N | **MISSING** | -- | -- |
| 6 | `inputs_snapshot` | jsonb | Y | **MISSING** | -- | -- |
| 7 | `created_at` | timestamp with time zone | Y | **MISSING** | -- | -- |
| 8 | `resolved_at` | timestamp with time zone | Y | **MISSING** | -- | -- |
| 9 | `retry_count` | integer | Y | **MISSING** | -- | -- |
| 10 | `retry_ceiling` | integer | Y | **MISSING** | -- | -- |
| 11 | `retry_after` | timestamp with time zone | Y | **MISSING** | -- | -- |
| 12 | `tool_used` | text | Y | **MISSING** | -- | -- |
| 13 | `tool_tier` | integer | Y | **MISSING** | -- | -- |
| 14 | `expires_at` | timestamp with time zone | Y | **MISSING** | -- | -- |
| 15 | `archived_at` | timestamp with time zone | Y | **MISSING** | -- | -- |
| 16 | `archive_reason` | text | Y | **MISSING** | -- | -- |
| 17 | `final_outcome` | text | Y | **MISSING** | -- | -- |
| 18 | `final_reason` | text | Y | **MISSING** | -- | -- |
| 19 | `error_type` | character varying(100) | N | **MISSING** | -- | -- |

#### `cl.company_candidate` -- STAGING -- 76,215 rows

Column registry: **UNDOCUMENTED**

| # | Column | Type | Null | Description | Role | Format |
|---|--------|------|------|-------------|------|--------|
| 1 | `candidate_id` | uuid | N | **MISSING** | -- | -- |
| 2 | `source_system` | text | N | **MISSING** | -- | -- |
| 3 | `source_record_id` | text | N | **MISSING** | -- | -- |
| 4 | `state_code` | character(2) | N | **MISSING** | -- | -- |
| 5 | `raw_payload` | jsonb | N | **MISSING** | -- | -- |
| 6 | `ingestion_run_id` | text | Y | **MISSING** | -- | -- |
| 7 | `verification_status` | text | N | **MISSING** | -- | -- |
| 8 | `verification_error` | text | Y | **MISSING** | -- | -- |
| 9 | `verified_at` | timestamp with time zone | Y | **MISSING** | -- | -- |
| 10 | `company_unique_id` | uuid | Y | **MISSING** | -- | -- |
| 11 | `created_at` | timestamp with time zone | N | **MISSING** | -- | -- |

#### `cl.company_domains` -- CANONICAL -- 46,583 rows

Column registry: **UNDOCUMENTED**

| # | Column | Type | Null | Description | Role | Format |
|---|--------|------|------|-------------|------|--------|
| 1 | `domain_id` | uuid | N | **MISSING** | -- | -- |
| 2 | `company_unique_id` | uuid | N | **MISSING** | -- | -- |
| 3 | `domain` | text | N | **MISSING** | -- | -- |
| 4 | `domain_health` | text | Y | **MISSING** | -- | -- |
| 5 | `mx_present` | boolean | Y | **MISSING** | -- | -- |
| 6 | `domain_name_confidence` | integer | Y | **MISSING** | -- | -- |
| 7 | `checked_at` | timestamp with time zone | Y | **MISSING** | -- | -- |

#### `cl.company_domains_archive` -- ARCHIVE -- 18,328 rows

Column registry: **UNDOCUMENTED**

| # | Column | Type | Null | Description | Role | Format |
|---|--------|------|------|-------------|------|--------|
| 1 | `domain_id` | uuid | N | **MISSING** | -- | -- |
| 2 | `company_unique_id` | uuid | N | **MISSING** | -- | -- |
| 3 | `domain` | text | N | **MISSING** | -- | -- |
| 4 | `domain_health` | text | Y | **MISSING** | -- | -- |
| 5 | `mx_present` | boolean | Y | **MISSING** | -- | -- |
| 6 | `domain_name_confidence` | integer | Y | **MISSING** | -- | -- |
| 7 | `checked_at` | timestamp with time zone | Y | **MISSING** | -- | -- |
| 8 | `archived_at` | timestamp with time zone | Y | **MISSING** | -- | -- |
| 9 | `archive_reason` | text | Y | **MISSING** | -- | -- |

#### `cl.company_domains_excluded` -- CANONICAL -- 5,327 rows

Column registry: **UNDOCUMENTED**

| # | Column | Type | Null | Description | Role | Format |
|---|--------|------|------|-------------|------|--------|
| 1 | `domain_id` | uuid | N | **MISSING** | -- | -- |
| 2 | `company_unique_id` | uuid | N | **MISSING** | -- | -- |
| 3 | `domain` | text | N | **MISSING** | -- | -- |
| 4 | `domain_health` | text | Y | **MISSING** | -- | -- |
| 5 | `mx_present` | boolean | Y | **MISSING** | -- | -- |
| 6 | `domain_name_confidence` | integer | Y | **MISSING** | -- | -- |
| 7 | `checked_at` | timestamp with time zone | Y | **MISSING** | -- | -- |

#### `cl.company_identity` -- CANONICAL FROZEN -- 117,151 rows

Column registry: **UNDOCUMENTED**

| # | Column | Type | Null | Description | Role | Format |
|---|--------|------|------|-------------|------|--------|
| 1 | `company_unique_id` | uuid | N | **MISSING** | -- | -- |
| 2 | `company_name` | text | N | **MISSING** | -- | -- |
| 3 | `company_domain` | text | Y | **MISSING** | -- | -- |
| 4 | `linkedin_company_url` | text | Y | **MISSING** | -- | -- |
| 5 | `source_system` | text | N | **MISSING** | -- | -- |
| 6 | `created_at` | timestamp with time zone | N | **MISSING** | -- | -- |
| 7 | `company_fingerprint` | text | Y | **MISSING** | -- | -- |
| 8 | `lifecycle_run_id` | text | Y | **MISSING** | -- | -- |
| 9 | `existence_verified` | boolean | Y | **MISSING** | -- | -- |
| 10 | `verification_run_id` | text | Y | **MISSING** | -- | -- |
| 11 | `verified_at` | timestamp with time zone | Y | **MISSING** | -- | -- |
| 12 | `domain_status_code` | integer | Y | **MISSING** | -- | -- |
| 13 | `name_match_score` | integer | Y | **MISSING** | -- | -- |
| 14 | `state_match_result` | text | Y | **MISSING** | -- | -- |
| 15 | `canonical_name` | text | Y | **MISSING** | -- | -- |
| 16 | `state_verified` | text | Y | **MISSING** | -- | -- |
| 17 | `employee_count_band` | text | Y | **MISSING** | -- | -- |
| 18 | `identity_pass` | integer | Y | **MISSING** | -- | -- |
| 19 | `identity_status` | text | Y | **MISSING** | -- | -- |
| 20 | `last_pass_at` | timestamp with time zone | Y | **MISSING** | -- | -- |
| 21 | `eligibility_status` | text | Y | **MISSING** | -- | -- |
| 22 | `exclusion_reason` | text | Y | **MISSING** | -- | -- |
| 23 | `entity_role` | text | Y | **MISSING** | -- | -- |
| 24 | `sovereign_company_id` | uuid | Y | **MISSING** | -- | -- |
| 25 | `final_outcome` | text | Y | **MISSING** | -- | -- |
| 26 | `final_reason` | text | Y | **MISSING** | -- | -- |
| 27 | `outreach_id` | uuid | Y | **MISSING** | -- | -- |
| 28 | `sales_process_id` | uuid | Y | **MISSING** | -- | -- |
| 29 | `client_id` | uuid | Y | **MISSING** | -- | -- |
| 30 | `outreach_attached_at` | timestamp with time zone | Y | **MISSING** | -- | -- |
| 31 | `sales_opened_at` | timestamp with time zone | Y | **MISSING** | -- | -- |
| 32 | `client_promoted_at` | timestamp with time zone | Y | **MISSING** | -- | -- |
| 33 | `normalized_domain` | text | Y | **MISSING** | -- | -- |
| 34 | `updated_at` | timestamp with time zone | Y | **MISSING** | -- | -- |
| 35 | `state_code` | character(2) | Y | **MISSING** | -- | -- |

#### `cl.company_identity_archive` -- ARCHIVE -- 22,263 rows

Column registry: **UNDOCUMENTED**

| # | Column | Type | Null | Description | Role | Format |
|---|--------|------|------|-------------|------|--------|
| 1 | `company_unique_id` | uuid | N | **MISSING** | -- | -- |
| 2 | `company_name` | text | N | **MISSING** | -- | -- |
| 3 | `company_domain` | text | Y | **MISSING** | -- | -- |
| 4 | `linkedin_company_url` | text | Y | **MISSING** | -- | -- |
| 5 | `source_system` | text | N | **MISSING** | -- | -- |
| 6 | `created_at` | timestamp with time zone | N | **MISSING** | -- | -- |
| 7 | `company_fingerprint` | text | Y | **MISSING** | -- | -- |
| 8 | `lifecycle_run_id` | text | Y | **MISSING** | -- | -- |
| 9 | `existence_verified` | boolean | Y | **MISSING** | -- | -- |
| 10 | `verification_run_id` | text | Y | **MISSING** | -- | -- |
| 11 | `verified_at` | timestamp with time zone | Y | **MISSING** | -- | -- |
| 12 | `domain_status_code` | integer | Y | **MISSING** | -- | -- |
| 13 | `name_match_score` | integer | Y | **MISSING** | -- | -- |
| 14 | `state_match_result` | text | Y | **MISSING** | -- | -- |
| 15 | `canonical_name` | text | Y | **MISSING** | -- | -- |
| 16 | `state_verified` | text | Y | **MISSING** | -- | -- |
| 17 | `employee_count_band` | text | Y | **MISSING** | -- | -- |
| 18 | `identity_pass` | integer | Y | **MISSING** | -- | -- |
| 19 | `identity_status` | text | Y | **MISSING** | -- | -- |
| 20 | `last_pass_at` | timestamp with time zone | Y | **MISSING** | -- | -- |
| 21 | `eligibility_status` | text | Y | **MISSING** | -- | -- |
| 22 | `exclusion_reason` | text | Y | **MISSING** | -- | -- |
| 23 | `entity_role` | text | Y | **MISSING** | -- | -- |
| 24 | `sovereign_company_id` | uuid | Y | **MISSING** | -- | -- |
| 25 | `final_outcome` | text | Y | **MISSING** | -- | -- |
| 26 | `final_reason` | text | Y | **MISSING** | -- | -- |
| 27 | `archived_at` | timestamp with time zone | Y | **MISSING** | -- | -- |
| 28 | `archive_reason` | text | Y | **MISSING** | -- | -- |

#### `cl.company_identity_bridge` -- CANONICAL -- 74,641 rows

Column registry: **UNDOCUMENTED**

| # | Column | Type | Null | Description | Role | Format |
|---|--------|------|------|-------------|------|--------|
| 1 | `bridge_id` | uuid | N | **MISSING** | -- | -- |
| 2 | `source_company_id` | text | N | **MISSING** | -- | -- |
| 3 | `company_sov_id` | uuid | N | **MISSING** | -- | -- |
| 4 | `source_system` | text | N | **MISSING** | -- | -- |
| 5 | `minted_at` | timestamp with time zone | N | **MISSING** | -- | -- |
| 6 | `minted_by` | text | N | **MISSING** | -- | -- |
| 7 | `lifecycle_run_id` | text | Y | **MISSING** | -- | -- |

#### `cl.company_identity_excluded` -- CANONICAL -- 5,327 rows

Column registry: **UNDOCUMENTED**

| # | Column | Type | Null | Description | Role | Format |
|---|--------|------|------|-------------|------|--------|
| 1 | `company_unique_id` | uuid | N | **MISSING** | -- | -- |
| 2 | `company_name` | text | N | **MISSING** | -- | -- |
| 3 | `company_domain` | text | Y | **MISSING** | -- | -- |
| 4 | `linkedin_company_url` | text | Y | **MISSING** | -- | -- |
| 5 | `source_system` | text | N | **MISSING** | -- | -- |
| 6 | `created_at` | timestamp with time zone | N | **MISSING** | -- | -- |
| 7 | `company_fingerprint` | text | Y | **MISSING** | -- | -- |
| 8 | `lifecycle_run_id` | text | Y | **MISSING** | -- | -- |
| 9 | `existence_verified` | boolean | Y | **MISSING** | -- | -- |
| 10 | `verification_run_id` | text | Y | **MISSING** | -- | -- |
| 11 | `verified_at` | timestamp with time zone | Y | **MISSING** | -- | -- |
| 12 | `domain_status_code` | integer | Y | **MISSING** | -- | -- |
| 13 | `name_match_score` | integer | Y | **MISSING** | -- | -- |
| 14 | `state_match_result` | text | Y | **MISSING** | -- | -- |
| 15 | `canonical_name` | text | Y | **MISSING** | -- | -- |
| 16 | `state_verified` | text | Y | **MISSING** | -- | -- |
| 17 | `employee_count_band` | text | Y | **MISSING** | -- | -- |
| 18 | `identity_pass` | integer | Y | **MISSING** | -- | -- |
| 19 | `identity_status` | text | Y | **MISSING** | -- | -- |
| 20 | `last_pass_at` | timestamp with time zone | Y | **MISSING** | -- | -- |
| 21 | `eligibility_status` | text | Y | **MISSING** | -- | -- |
| 22 | `exclusion_reason` | text | Y | **MISSING** | -- | -- |
| 23 | `entity_role` | text | Y | **MISSING** | -- | -- |
| 24 | `sovereign_company_id` | uuid | Y | **MISSING** | -- | -- |
| 25 | `final_outcome` | text | Y | **MISSING** | -- | -- |
| 26 | `final_reason` | text | Y | **MISSING** | -- | -- |
| 27 | `outreach_id` | uuid | Y | **MISSING** | -- | -- |
| 28 | `sales_process_id` | uuid | Y | **MISSING** | -- | -- |
| 29 | `client_id` | uuid | Y | **MISSING** | -- | -- |
| 30 | `outreach_attached_at` | timestamp with time zone | Y | **MISSING** | -- | -- |
| 31 | `sales_opened_at` | timestamp with time zone | Y | **MISSING** | -- | -- |
| 32 | `client_promoted_at` | timestamp with time zone | Y | **MISSING** | -- | -- |
| 33 | `normalized_domain` | text | Y | **MISSING** | -- | -- |

#### `cl.company_names` -- CANONICAL -- 70,843 rows

Column registry: **UNDOCUMENTED**

| # | Column | Type | Null | Description | Role | Format |
|---|--------|------|------|-------------|------|--------|
| 1 | `name_id` | uuid | N | **MISSING** | -- | -- |
| 2 | `company_unique_id` | uuid | N | **MISSING** | -- | -- |
| 3 | `name_value` | text | N | **MISSING** | -- | -- |
| 4 | `name_type` | text | N | **MISSING** | -- | -- |
| 5 | `created_at` | timestamp with time zone | Y | **MISSING** | -- | -- |

#### `cl.company_names_archive` -- ARCHIVE -- 17,764 rows

Column registry: **UNDOCUMENTED**

| # | Column | Type | Null | Description | Role | Format |
|---|--------|------|------|-------------|------|--------|
| 1 | `name_id` | uuid | N | **MISSING** | -- | -- |
| 2 | `company_unique_id` | uuid | N | **MISSING** | -- | -- |
| 3 | `name_value` | text | N | **MISSING** | -- | -- |
| 4 | `name_type` | text | N | **MISSING** | -- | -- |
| 5 | `created_at` | timestamp with time zone | Y | **MISSING** | -- | -- |
| 6 | `archived_at` | timestamp with time zone | Y | **MISSING** | -- | -- |
| 7 | `archive_reason` | text | Y | **MISSING** | -- | -- |

#### `cl.company_names_excluded` -- CANONICAL -- 7,361 rows

Column registry: **UNDOCUMENTED**

| # | Column | Type | Null | Description | Role | Format |
|---|--------|------|------|-------------|------|--------|
| 1 | `name_id` | uuid | N | **MISSING** | -- | -- |
| 2 | `company_unique_id` | uuid | N | **MISSING** | -- | -- |
| 3 | `name_value` | text | N | **MISSING** | -- | -- |
| 4 | `name_type` | text | N | **MISSING** | -- | -- |
| 5 | `created_at` | timestamp with time zone | Y | **MISSING** | -- | -- |

#### `cl.domain_hierarchy` -- CANONICAL -- 4,705 rows

Column registry: **UNDOCUMENTED**

| # | Column | Type | Null | Description | Role | Format |
|---|--------|------|------|-------------|------|--------|
| 1 | `hierarchy_id` | uuid | N | **MISSING** | -- | -- |
| 2 | `domain` | text | N | **MISSING** | -- | -- |
| 3 | `parent_company_id` | uuid | Y | **MISSING** | -- | -- |
| 4 | `child_company_id` | uuid | Y | **MISSING** | -- | -- |
| 5 | `relationship_type` | text | N | **MISSING** | -- | -- |
| 6 | `confidence_score` | integer | Y | **MISSING** | -- | -- |
| 7 | `resolution_method` | text | Y | **MISSING** | -- | -- |
| 8 | `created_at` | timestamp with time zone | Y | **MISSING** | -- | -- |

#### `cl.domain_hierarchy_archive` -- ARCHIVE -- 1,878 rows

Column registry: **UNDOCUMENTED**

| # | Column | Type | Null | Description | Role | Format |
|---|--------|------|------|-------------|------|--------|
| 1 | `hierarchy_id` | uuid | N | **MISSING** | -- | -- |
| 2 | `domain` | text | N | **MISSING** | -- | -- |
| 3 | `parent_company_id` | uuid | Y | **MISSING** | -- | -- |
| 4 | `child_company_id` | uuid | Y | **MISSING** | -- | -- |
| 5 | `relationship_type` | text | N | **MISSING** | -- | -- |
| 6 | `confidence_score` | integer | Y | **MISSING** | -- | -- |
| 7 | `resolution_method` | text | Y | **MISSING** | -- | -- |
| 8 | `created_at` | timestamp with time zone | Y | **MISSING** | -- | -- |
| 9 | `archived_at` | timestamp with time zone | Y | **MISSING** | -- | -- |
| 10 | `archive_reason` | text | Y | **MISSING** | -- | -- |

#### `cl.identity_confidence` -- CANONICAL -- 46,583 rows

Column registry: **UNDOCUMENTED**

| # | Column | Type | Null | Description | Role | Format |
|---|--------|------|------|-------------|------|--------|
| 1 | `company_unique_id` | uuid | N | **MISSING** | -- | -- |
| 2 | `confidence_score` | integer | N | **MISSING** | -- | -- |
| 3 | `confidence_bucket` | text | N | **MISSING** | -- | -- |
| 4 | `computed_at` | timestamp with time zone | Y | **MISSING** | -- | -- |

#### `cl.identity_confidence_archive` -- ARCHIVE -- 19,850 rows

Column registry: **UNDOCUMENTED**

| # | Column | Type | Null | Description | Role | Format |
|---|--------|------|------|-------------|------|--------|
| 1 | `company_unique_id` | uuid | N | **MISSING** | -- | -- |
| 2 | `confidence_score` | integer | N | **MISSING** | -- | -- |
| 3 | `confidence_bucket` | text | N | **MISSING** | -- | -- |
| 4 | `computed_at` | timestamp with time zone | Y | **MISSING** | -- | -- |
| 5 | `archived_at` | timestamp with time zone | Y | **MISSING** | -- | -- |
| 6 | `archive_reason` | text | Y | **MISSING** | -- | -- |

#### `cl.identity_confidence_excluded` -- CANONICAL -- 5,327 rows

Column registry: **UNDOCUMENTED**

| # | Column | Type | Null | Description | Role | Format |
|---|--------|------|------|-------------|------|--------|
| 1 | `company_unique_id` | uuid | N | **MISSING** | -- | -- |
| 2 | `confidence_score` | integer | N | **MISSING** | -- | -- |
| 3 | `confidence_bucket` | text | N | **MISSING** | -- | -- |
| 4 | `computed_at` | timestamp with time zone | Y | **MISSING** | -- | -- |

#### `cl.movement_code_registry` -- UNREGISTERED -- 15 rows

Column registry: **UNDOCUMENTED**

| # | Column | Type | Null | Description | Role | Format |
|---|--------|------|------|-------------|------|--------|
| 1 | `subhub` | character varying | N | **MISSING** | -- | -- |
| 2 | `code` | integer | N | **MISSING** | -- | -- |
| 3 | `description` | text | N | **MISSING** | -- | -- |
| 4 | `active` | boolean | N | **MISSING** | -- | -- |
| 5 | `created_at` | timestamp with time zone | N | **MISSING** | -- | -- |

#### `cl.sovereign_mint_backup_20260218` -- UNREGISTERED -- 60,212 rows

Column registry: **UNDOCUMENTED**

| # | Column | Type | Null | Description | Role | Format |
|---|--------|------|------|-------------|------|--------|
| 1 | `company_unique_id` | uuid | Y | **MISSING** | -- | -- |
| 2 | `source_system` | text | Y | **MISSING** | -- | -- |
| 3 | `company_name` | text | Y | **MISSING** | -- | -- |
| 4 | `old_sovereign_id` | uuid | Y | **MISSING** | -- | -- |

### `outreach` -- Operational Spine + Sub-Hub Data -- all outreach workflow state and sub-hub tables

**Tables**: 50 | **Total rows**: 1,355,286
**Views**: 12 -- v_bit_hot_companies, v_bit_recent_signals, v_bit_tier_distribution, v_blog_ingestion_queue, v_blog_ready, v_context_current, v_ct_zip_repair_candidates, v_dol_zip_evidence, v_outreach_diagnostic, vw_marketing_eligibility, vw_marketing_eligibility_with_overrides, vw_sovereign_completion

| Table | Leaf Type | Frozen | Rows | Columns | Documented |
|-------|-----------|--------|------|---------|------------|
| `appointments` | SUPPORTING |  | 702 | 22 | 0 |
| `bit_errors` | ERROR |  | 0 | 13 | 4/13 |
| `bit_input_history` | SYSTEM |  | 0 | 13 | 0 |
| `bit_scores` | CANONICAL | YES | 12,602 | 12 | 1/12 |
| `bit_scores_archive` | ARCHIVE |  | 1,806 | 14 | 0 |
| `bit_signals` | MV |  | 0 | 14 | 0 |
| `blog` | CANONICAL | YES | 93,596 | 13 | 1/13 |
| `blog_archive` | ARCHIVE |  | 4,391 | 10 | 0 |
| `blog_errors` | ERROR |  | 41 | 15 | 4/15 |
| `blog_ingress_control` | REGISTRY |  | 1 | 14 | 0 |
| `blog_source_history` | SYSTEM |  | 0 | 13 | 0 |
| `campaigns` | DEPRECATED |  | 0 | 18 | 0 |
| `column_registry` | REGISTRY |  | 48 | 12 | 0 |
| `company_hub_status` | MV |  | 68,908 | 8 | 0 |
| `company_target` | CANONICAL | YES | 114,137 | 27 | 3/27 |
| `company_target_archive` | ARCHIVE |  | 81,753 | 20 | 0 |
| `company_target_dead_ends` | UNREGISTERED |  | 4,427 | 8 | 0 |
| `company_target_errors` | ERROR |  | 4,108 | 28 | 4/28 |
| `company_target_errors_archive` | ARCHIVE |  | 0 | 30 | 0 |
| `company_target_orphaned_archive` | ARCHIVE |  | 52,812 | 29 | 0 |
| `ctb_audit_log` | SYSTEM |  | 1,534 | 7 | 0 |
| `ctb_queue` | STAGING |  | 33,217 | 9 | 0 |
| `dol` | CANONICAL | YES | 147,031 | 12 | 6/12 |
| `dol_archive` | ARCHIVE |  | 1,623 | 11 | 0 |
| `dol_audit_log` | SYSTEM |  | 0 | 9 | 0 |
| `dol_errors` | ERROR |  | 28,572 | 27 | 4/27 |
| `dol_errors_archive` | ARCHIVE |  | 0 | 29 | 0 |
| `dol_url_enrichment` | STAGING |  | 16 | 14 | 0 |
| `engagement_events` | MV |  | 0 | 19 | 0 |
| `entity_resolution_queue` | STAGING |  | 2 | 15 | 0 |
| `hub_registry` | REGISTRY |  | 6 | 12 | 0 |
| `manual_overrides` | SYSTEM |  | 0 | 12 | 0 |
| `mv_credit_usage` | SYSTEM |  | 2 | 6 | 0 |
| `outreach` | CANONICAL | YES | 114,137 | 7 | 3/7 |
| `outreach_archive` | ARCHIVE |  | 27,416 | 7 | 0 |
| `outreach_errors` | ERROR |  | 0 | 9 | 0 |
| `outreach_excluded` | ARCHIVE |  | 5,483 | 10 | 0 |
| `outreach_legacy_quarantine` | ARCHIVE |  | 1,698 | 5 | 0 |
| `outreach_orphan_archive` | ARCHIVE |  | 2,709 | 7 | 0 |
| `override_audit_log` | SYSTEM |  | 0 | 9 | 0 |
| `people` | SUPPORTING | YES | 335,097 | 20 | 0 |
| `people_archive` | ARCHIVE |  | 175 | 22 | 0 |
| `people_errors` | ERROR |  | 0 | 14 | 0 |
| `pipeline_audit_log` | SYSTEM |  | 0 | 9 | 0 |
| `send_log` | DEPRECATED |  | 0 | 25 | 0 |
| `sequences` | DEPRECATED |  | 0 | 13 | 0 |
| `sitemap_discovery` | UNREGISTERED |  | 93,596 | 9 | 0 |
| `source_urls` | UNREGISTERED |  | 81,292 | 6 | 0 |
| `url_discovery_failures` | ERROR |  | 42,348 | 20 | 0 |
| `url_discovery_failures_archive` | ARCHIVE |  | 0 | 21 | 0 |

#### `outreach.appointments` -- SUPPORTING -- 702 rows

Column registry: **UNDOCUMENTED**

| # | Column | Type | Null | Description | Role | Format |
|---|--------|------|------|-------------|------|--------|
| 1 | `appointment_id` | uuid | N | **MISSING** | -- | -- |
| 2 | `outreach_id` | uuid | Y | **MISSING** | -- | -- |
| 3 | `domain` | character varying(255) | Y | **MISSING** | -- | -- |
| 4 | `prospect_keycode_id` | bigint | Y | **MISSING** | -- | -- |
| 5 | `appt_number` | character varying(50) | Y | **MISSING** | -- | -- |
| 6 | `appt_date` | date | Y | **MISSING** | -- | -- |
| 7 | `contact_first_name` | character varying(100) | Y | **MISSING** | -- | -- |
| 8 | `contact_last_name` | character varying(100) | Y | **MISSING** | -- | -- |
| 9 | `contact_title` | character varying(200) | Y | **MISSING** | -- | -- |
| 10 | `contact_email` | character varying(255) | Y | **MISSING** | -- | -- |
| 11 | `contact_phone` | character varying(20) | Y | **MISSING** | -- | -- |
| 12 | `company_name` | character varying(255) | N | **MISSING** | -- | -- |
| 13 | `address_1` | character varying(255) | Y | **MISSING** | -- | -- |
| 14 | `address_2` | character varying(255) | Y | **MISSING** | -- | -- |
| 15 | `city` | character varying(100) | Y | **MISSING** | -- | -- |
| 16 | `state` | character varying(10) | Y | **MISSING** | -- | -- |
| 17 | `zip` | character varying(20) | Y | **MISSING** | -- | -- |
| 18 | `county` | character varying(100) | Y | **MISSING** | -- | -- |
| 19 | `notes` | text | Y | **MISSING** | -- | -- |
| 20 | `source_file` | character varying(255) | Y | **MISSING** | -- | -- |
| 21 | `created_at` | timestamp with time zone | Y | **MISSING** | -- | -- |
| 22 | `updated_at` | timestamp with time zone | Y | **MISSING** | -- | -- |

#### `outreach.bit_errors` -- ERROR -- 0 rows

Column registry: **4/13 documented**

| # | Column | Type | Null | Description | Role | Format |
|---|--------|------|------|-------------|------|--------|
| 1 | `error_id` | uuid | N | Primary key for error record | identifier | UUID |
| 2 | `outreach_id` | uuid | Y | FK to spine (nullable — error may occur before entity exists) | foreign_key | UUID |
| 3 | `pipeline_stage` | character varying(20) | N | **MISSING** | -- | -- |
| 4 | `failure_code` | character varying(30) | N | **MISSING** | -- | -- |
| 5 | `blocking_reason` | text | N | **MISSING** | -- | -- |
| 6 | `severity` | character varying(10) | N | **MISSING** | -- | -- |
| 7 | `retry_allowed` | boolean | N | **MISSING** | -- | -- |
| 8 | `correlation_id` | uuid | Y | **MISSING** | -- | -- |
| 9 | `process_id` | uuid | Y | **MISSING** | -- | -- |
| 10 | `raw_input` | jsonb | Y | **MISSING** | -- | -- |
| 11 | `stack_trace` | text | Y | **MISSING** | -- | -- |
| 12 | `created_at` | timestamp with time zone | N | When the error was recorded | attribute | ISO-8601 |
| 13 | `error_type` | character varying(100) | Y | Discriminator column — classifies the scoring error | attribute | ENUM |

#### `outreach.bit_input_history` -- SYSTEM -- 0 rows

Column registry: **UNDOCUMENTED**

| # | Column | Type | Null | Description | Role | Format |
|---|--------|------|------|-------------|------|--------|
| 1 | `history_id` | uuid | N | **MISSING** | -- | -- |
| 2 | `outreach_id` | uuid | N | **MISSING** | -- | -- |
| 3 | `signal_type` | character varying(50) | N | **MISSING** | -- | -- |
| 4 | `source` | character varying(50) | N | **MISSING** | -- | -- |
| 5 | `signal_fingerprint` | text | N | **MISSING** | -- | -- |
| 6 | `signal_payload` | jsonb | Y | **MISSING** | -- | -- |
| 7 | `first_seen_at` | timestamp with time zone | Y | **MISSING** | -- | -- |
| 8 | `last_used_at` | timestamp with time zone | Y | **MISSING** | -- | -- |
| 9 | `use_count` | integer | Y | **MISSING** | -- | -- |
| 10 | `score_contribution` | integer | Y | **MISSING** | -- | -- |
| 11 | `correlation_id` | uuid | Y | **MISSING** | -- | -- |
| 12 | `process_id` | uuid | Y | **MISSING** | -- | -- |
| 13 | `created_at` | timestamp with time zone | Y | **MISSING** | -- | -- |

#### `outreach.bit_scores` -- CANONICAL FROZEN -- 12,602 rows

Column registry: **1/12 documented**

| # | Column | Type | Null | Description | Role | Format |
|---|--------|------|------|-------------|------|--------|
| 1 | `outreach_id` | uuid | N | FK to outreach.outreach spine table | foreign_key | UUID |
| 2 | `score` | numeric | N | **MISSING** | -- | -- |
| 3 | `score_tier` | character varying(10) | N | **MISSING** | -- | -- |
| 4 | `signal_count` | integer | N | **MISSING** | -- | -- |
| 5 | `people_score` | numeric | N | **MISSING** | -- | -- |
| 6 | `dol_score` | numeric | N | **MISSING** | -- | -- |
| 7 | `blog_score` | numeric | N | **MISSING** | -- | -- |
| 8 | `talent_flow_score` | numeric | N | **MISSING** | -- | -- |
| 9 | `last_signal_at` | timestamp with time zone | Y | **MISSING** | -- | -- |
| 10 | `last_scored_at` | timestamp with time zone | Y | **MISSING** | -- | -- |
| 11 | `created_at` | timestamp with time zone | N | **MISSING** | -- | -- |
| 12 | `updated_at` | timestamp with time zone | N | **MISSING** | -- | -- |

#### `outreach.bit_scores_archive` -- ARCHIVE -- 1,806 rows

Column registry: **UNDOCUMENTED**

| # | Column | Type | Null | Description | Role | Format |
|---|--------|------|------|-------------|------|--------|
| 1 | `outreach_id` | uuid | N | **MISSING** | -- | -- |
| 2 | `score` | numeric | N | **MISSING** | -- | -- |
| 3 | `score_tier` | character varying(10) | N | **MISSING** | -- | -- |
| 4 | `signal_count` | integer | N | **MISSING** | -- | -- |
| 5 | `people_score` | numeric | N | **MISSING** | -- | -- |
| 6 | `dol_score` | numeric | N | **MISSING** | -- | -- |
| 7 | `blog_score` | numeric | N | **MISSING** | -- | -- |
| 8 | `talent_flow_score` | numeric | N | **MISSING** | -- | -- |
| 9 | `last_signal_at` | timestamp with time zone | Y | **MISSING** | -- | -- |
| 10 | `last_scored_at` | timestamp with time zone | Y | **MISSING** | -- | -- |
| 11 | `created_at` | timestamp with time zone | N | **MISSING** | -- | -- |
| 12 | `updated_at` | timestamp with time zone | N | **MISSING** | -- | -- |
| 13 | `archived_at` | timestamp with time zone | Y | **MISSING** | -- | -- |
| 14 | `archive_reason` | text | Y | **MISSING** | -- | -- |

#### `outreach.bit_signals` -- MV -- 0 rows

Column registry: **UNDOCUMENTED**

| # | Column | Type | Null | Description | Role | Format |
|---|--------|------|------|-------------|------|--------|
| 1 | `signal_id` | uuid | N | **MISSING** | -- | -- |
| 2 | `outreach_id` | uuid | N | **MISSING** | -- | -- |
| 3 | `signal_type` | character varying(50) | N | **MISSING** | -- | -- |
| 4 | `signal_impact` | numeric | N | **MISSING** | -- | -- |
| 5 | `source_spoke` | character varying(50) | N | **MISSING** | -- | -- |
| 6 | `correlation_id` | uuid | N | **MISSING** | -- | -- |
| 7 | `process_id` | uuid | Y | **MISSING** | -- | -- |
| 8 | `signal_metadata` | jsonb | Y | **MISSING** | -- | -- |
| 9 | `decay_period_days` | integer | N | **MISSING** | -- | -- |
| 10 | `decayed_impact` | numeric | Y | **MISSING** | -- | -- |
| 11 | `signal_timestamp` | timestamp with time zone | N | **MISSING** | -- | -- |
| 12 | `processed_at` | timestamp with time zone | Y | **MISSING** | -- | -- |
| 13 | `created_at` | timestamp with time zone | N | **MISSING** | -- | -- |
| 14 | `signal_source` | character varying(50) | Y | **MISSING** | -- | -- |

#### `outreach.blog` -- CANONICAL FROZEN -- 93,596 rows

Column registry: **1/13 documented**

| # | Column | Type | Null | Description | Role | Format |
|---|--------|------|------|-------------|------|--------|
| 1 | `blog_id` | uuid | N | **MISSING** | -- | -- |
| 2 | `outreach_id` | uuid | N | FK to outreach.outreach spine table | foreign_key | UUID |
| 3 | `context_summary` | text | Y | **MISSING** | -- | -- |
| 4 | `source_type` | text | Y | **MISSING** | -- | -- |
| 5 | `source_url` | text | Y | **MISSING** | -- | -- |
| 6 | `context_timestamp` | timestamp with time zone | Y | **MISSING** | -- | -- |
| 7 | `created_at` | timestamp with time zone | Y | **MISSING** | -- | -- |
| 8 | `source_type_enum` | USER-DEFINED | Y | **MISSING** | -- | -- |
| 9 | `about_url` | text | Y | **MISSING** | -- | -- |
| 10 | `news_url` | text | Y | **MISSING** | -- | -- |
| 11 | `extraction_method` | text | Y | **MISSING** | -- | -- |
| 12 | `last_extracted_at` | timestamp with time zone | Y | **MISSING** | -- | -- |
| 13 | `updated_at` | timestamp with time zone | Y | **MISSING** | -- | -- |

#### `outreach.blog_archive` -- ARCHIVE -- 4,391 rows

Column registry: **UNDOCUMENTED**

| # | Column | Type | Null | Description | Role | Format |
|---|--------|------|------|-------------|------|--------|
| 1 | `blog_id` | uuid | N | **MISSING** | -- | -- |
| 2 | `outreach_id` | uuid | N | **MISSING** | -- | -- |
| 3 | `context_summary` | text | Y | **MISSING** | -- | -- |
| 4 | `source_type` | text | Y | **MISSING** | -- | -- |
| 5 | `source_url` | text | Y | **MISSING** | -- | -- |
| 6 | `context_timestamp` | timestamp with time zone | Y | **MISSING** | -- | -- |
| 7 | `created_at` | timestamp with time zone | Y | **MISSING** | -- | -- |
| 8 | `source_type_enum` | USER-DEFINED | Y | **MISSING** | -- | -- |
| 9 | `archived_at` | timestamp with time zone | Y | **MISSING** | -- | -- |
| 10 | `archive_reason` | text | Y | **MISSING** | -- | -- |

#### `outreach.blog_errors` -- ERROR -- 41 rows

Column registry: **4/15 documented**

| # | Column | Type | Null | Description | Role | Format |
|---|--------|------|------|-------------|------|--------|
| 1 | `error_id` | uuid | N | Primary key for error record | identifier | UUID |
| 2 | `outreach_id` | uuid | N | FK to spine (nullable — error may occur before entity exists) | foreign_key | UUID |
| 3 | `pipeline_stage` | character varying(100) | N | **MISSING** | -- | -- |
| 4 | `failure_code` | character varying(50) | N | **MISSING** | -- | -- |
| 5 | `blocking_reason` | text | N | **MISSING** | -- | -- |
| 6 | `severity` | character varying(20) | N | **MISSING** | -- | -- |
| 7 | `retry_allowed` | boolean | N | **MISSING** | -- | -- |
| 8 | `created_at` | timestamp with time zone | N | When the error was recorded | attribute | ISO-8601 |
| 9 | `resolved_at` | timestamp with time zone | Y | **MISSING** | -- | -- |
| 10 | `resolution_note` | text | Y | **MISSING** | -- | -- |
| 11 | `raw_input` | jsonb | Y | **MISSING** | -- | -- |
| 12 | `stack_trace` | text | Y | **MISSING** | -- | -- |
| 13 | `process_id` | uuid | Y | **MISSING** | -- | -- |
| 14 | `requeue_attempts` | integer | Y | **MISSING** | -- | -- |
| 15 | `error_type` | character varying(100) | N | Discriminator column — classifies the blog error (e.g., BLOG_MISSING) | attribute | ENUM |

#### `outreach.blog_ingress_control` -- REGISTRY -- 1 rows

Column registry: **UNDOCUMENTED**

| # | Column | Type | Null | Description | Role | Format |
|---|--------|------|------|-------------|------|--------|
| 1 | `control_id` | uuid | N | **MISSING** | -- | -- |
| 2 | `enabled` | boolean | N | **MISSING** | -- | -- |
| 3 | `enabled_at` | timestamp with time zone | Y | **MISSING** | -- | -- |
| 4 | `enabled_by` | text | Y | **MISSING** | -- | -- |
| 5 | `disabled_at` | timestamp with time zone | Y | **MISSING** | -- | -- |
| 6 | `disabled_by` | text | Y | **MISSING** | -- | -- |
| 7 | `max_urls_per_hour` | integer | Y | **MISSING** | -- | -- |
| 8 | `max_urls_per_company` | integer | Y | **MISSING** | -- | -- |
| 9 | `url_ttl_days` | integer | Y | **MISSING** | -- | -- |
| 10 | `content_ttl_days` | integer | Y | **MISSING** | -- | -- |
| 11 | `notes` | text | Y | **MISSING** | -- | -- |
| 12 | `singleton_key` | integer | Y | **MISSING** | -- | -- |
| 13 | `created_at` | timestamp with time zone | Y | **MISSING** | -- | -- |
| 14 | `updated_at` | timestamp with time zone | Y | **MISSING** | -- | -- |

#### `outreach.blog_source_history` -- SYSTEM -- 0 rows

Column registry: **UNDOCUMENTED**

| # | Column | Type | Null | Description | Role | Format |
|---|--------|------|------|-------------|------|--------|
| 1 | `history_id` | uuid | N | **MISSING** | -- | -- |
| 2 | `outreach_id` | uuid | N | **MISSING** | -- | -- |
| 3 | `source_type` | character varying(50) | N | **MISSING** | -- | -- |
| 4 | `source_url` | text | N | **MISSING** | -- | -- |
| 5 | `first_seen_at` | timestamp with time zone | N | **MISSING** | -- | -- |
| 6 | `last_checked_at` | timestamp with time zone | Y | **MISSING** | -- | -- |
| 7 | `status` | character varying(20) | Y | **MISSING** | -- | -- |
| 8 | `http_status` | integer | Y | **MISSING** | -- | -- |
| 9 | `redirect_url` | text | Y | **MISSING** | -- | -- |
| 10 | `checksum` | text | Y | **MISSING** | -- | -- |
| 11 | `process_id` | uuid | Y | **MISSING** | -- | -- |
| 12 | `correlation_id` | uuid | Y | **MISSING** | -- | -- |
| 13 | `created_at` | timestamp with time zone | Y | **MISSING** | -- | -- |

#### `outreach.campaigns` -- DEPRECATED -- 0 rows

Column registry: **UNDOCUMENTED**

| # | Column | Type | Null | Description | Role | Format |
|---|--------|------|------|-------------|------|--------|
| 1 | `campaign_id` | uuid | N | **MISSING** | -- | -- |
| 2 | `campaign_name` | character varying(255) | N | **MISSING** | -- | -- |
| 3 | `campaign_type` | character varying(50) | N | **MISSING** | -- | -- |
| 4 | `campaign_status` | character varying(50) | N | **MISSING** | -- | -- |
| 5 | `target_bit_score_min` | integer | Y | **MISSING** | -- | -- |
| 6 | `target_outreach_state` | character varying(50) | Y | **MISSING** | -- | -- |
| 7 | `daily_send_limit` | integer | Y | **MISSING** | -- | -- |
| 8 | `total_send_limit` | integer | Y | **MISSING** | -- | -- |
| 9 | `total_targeted` | integer | N | **MISSING** | -- | -- |
| 10 | `total_sent` | integer | N | **MISSING** | -- | -- |
| 11 | `total_opened` | integer | N | **MISSING** | -- | -- |
| 12 | `total_clicked` | integer | N | **MISSING** | -- | -- |
| 13 | `total_replied` | integer | N | **MISSING** | -- | -- |
| 14 | `start_date` | date | Y | **MISSING** | -- | -- |
| 15 | `end_date` | date | Y | **MISSING** | -- | -- |
| 16 | `created_by` | character varying(100) | Y | **MISSING** | -- | -- |
| 17 | `created_at` | timestamp with time zone | N | **MISSING** | -- | -- |
| 18 | `updated_at` | timestamp with time zone | N | **MISSING** | -- | -- |

#### `outreach.column_registry` -- REGISTRY -- 48 rows

Column registry: **UNDOCUMENTED**

| # | Column | Type | Null | Description | Role | Format |
|---|--------|------|------|-------------|------|--------|
| 1 | `registry_id` | integer | N | **MISSING** | -- | -- |
| 2 | `schema_name` | character varying(50) | N | **MISSING** | -- | -- |
| 3 | `table_name` | character varying(100) | N | **MISSING** | -- | -- |
| 4 | `column_name` | character varying(100) | N | **MISSING** | -- | -- |
| 5 | `column_unique_id` | character varying(50) | N | **MISSING** | -- | -- |
| 6 | `column_description` | text | N | **MISSING** | -- | -- |
| 7 | `column_format` | character varying(200) | N | **MISSING** | -- | -- |
| 8 | `is_nullable` | boolean | N | **MISSING** | -- | -- |
| 9 | `default_value` | text | Y | **MISSING** | -- | -- |
| 10 | `fk_reference` | text | Y | **MISSING** | -- | -- |
| 11 | `created_at` | timestamp with time zone | Y | **MISSING** | -- | -- |
| 12 | `updated_at` | timestamp with time zone | Y | **MISSING** | -- | -- |

#### `outreach.company_hub_status` -- MV -- 68,908 rows

Column registry: **UNDOCUMENTED**

| # | Column | Type | Null | Description | Role | Format |
|---|--------|------|------|-------------|------|--------|
| 1 | `company_unique_id` | text | N | **MISSING** | -- | -- |
| 2 | `hub_id` | character varying(50) | N | **MISSING** | -- | -- |
| 3 | `status` | USER-DEFINED | N | **MISSING** | -- | -- |
| 4 | `status_reason` | text | Y | **MISSING** | -- | -- |
| 5 | `metric_value` | numeric | Y | **MISSING** | -- | -- |
| 6 | `last_processed_at` | timestamp with time zone | Y | **MISSING** | -- | -- |
| 7 | `created_at` | timestamp with time zone | N | **MISSING** | -- | -- |
| 8 | `updated_at` | timestamp with time zone | N | **MISSING** | -- | -- |

#### `outreach.company_target` -- CANONICAL FROZEN -- 114,137 rows

Column registry: **3/27 documented**

| # | Column | Type | Null | Description | Role | Format |
|---|--------|------|------|-------------|------|--------|
| 1 | `target_id` | uuid | N | **MISSING** | -- | -- |
| 2 | `company_unique_id` | text | Y | Barton company identifier (04.04.01.YY.NNNNNN format) | identifier | STRING |
| 3 | `outreach_status` | text | N | **MISSING** | -- | -- |
| 4 | `bit_score_snapshot` | integer | Y | **MISSING** | -- | -- |
| 5 | `first_targeted_at` | timestamp with time zone | Y | **MISSING** | -- | -- |
| 6 | `last_targeted_at` | timestamp with time zone | Y | **MISSING** | -- | -- |
| 7 | `sequence_count` | integer | N | **MISSING** | -- | -- |
| 8 | `active_sequence_id` | text | Y | **MISSING** | -- | -- |
| 9 | `source` | text | Y | CL source system that originated this company record | attribute | STRING |
| 10 | `created_at` | timestamp with time zone | N | **MISSING** | -- | -- |
| 11 | `updated_at` | timestamp with time zone | N | **MISSING** | -- | -- |
| 12 | `outreach_id` | uuid | Y | FK to outreach.outreach spine table | foreign_key | UUID |
| 13 | `email_method` | character varying(100) | Y | **MISSING** | -- | -- |
| 14 | `method_type` | character varying(50) | Y | **MISSING** | -- | -- |
| 15 | `confidence_score` | numeric | Y | **MISSING** | -- | -- |
| 16 | `execution_status` | character varying(50) | Y | **MISSING** | -- | -- |
| 17 | `imo_completed_at` | timestamp with time zone | Y | **MISSING** | -- | -- |
| 18 | `is_catchall` | boolean | Y | **MISSING** | -- | -- |
| 19 | `industry` | character varying(255) | Y | **MISSING** | -- | -- |
| 20 | `employees` | integer | Y | **MISSING** | -- | -- |
| 21 | `country` | character varying(10) | Y | **MISSING** | -- | -- |
| 22 | `state` | character varying(50) | Y | **MISSING** | -- | -- |
| 23 | `city` | character varying(100) | Y | **MISSING** | -- | -- |
| 24 | `postal_code` | character varying(20) | Y | **MISSING** | -- | -- |
| 25 | `data_year` | integer | Y | **MISSING** | -- | -- |
| 26 | `postal_code_source` | text | Y | **MISSING** | -- | -- |
| 27 | `postal_code_updated_at` | timestamp with time zone | Y | **MISSING** | -- | -- |

#### `outreach.company_target_archive` -- ARCHIVE -- 81,753 rows

Column registry: **UNDOCUMENTED**

| # | Column | Type | Null | Description | Role | Format |
|---|--------|------|------|-------------|------|--------|
| 1 | `target_id` | uuid | N | **MISSING** | -- | -- |
| 2 | `company_unique_id` | text | Y | **MISSING** | -- | -- |
| 3 | `outreach_status` | text | N | **MISSING** | -- | -- |
| 4 | `bit_score_snapshot` | integer | Y | **MISSING** | -- | -- |
| 5 | `first_targeted_at` | timestamp with time zone | Y | **MISSING** | -- | -- |
| 6 | `last_targeted_at` | timestamp with time zone | Y | **MISSING** | -- | -- |
| 7 | `sequence_count` | integer | N | **MISSING** | -- | -- |
| 8 | `active_sequence_id` | text | Y | **MISSING** | -- | -- |
| 9 | `source` | text | Y | **MISSING** | -- | -- |
| 10 | `created_at` | timestamp with time zone | N | **MISSING** | -- | -- |
| 11 | `updated_at` | timestamp with time zone | N | **MISSING** | -- | -- |
| 12 | `outreach_id` | uuid | Y | **MISSING** | -- | -- |
| 13 | `email_method` | character varying(100) | Y | **MISSING** | -- | -- |
| 14 | `method_type` | character varying(50) | Y | **MISSING** | -- | -- |
| 15 | `confidence_score` | numeric | Y | **MISSING** | -- | -- |
| 16 | `execution_status` | character varying(50) | Y | **MISSING** | -- | -- |
| 17 | `imo_completed_at` | timestamp with time zone | Y | **MISSING** | -- | -- |
| 18 | `is_catchall` | boolean | Y | **MISSING** | -- | -- |
| 19 | `archived_at` | timestamp with time zone | Y | **MISSING** | -- | -- |
| 20 | `archive_reason` | text | Y | **MISSING** | -- | -- |

#### `outreach.company_target_dead_ends` -- UNREGISTERED -- 4,427 rows

Column registry: **UNDOCUMENTED**

| # | Column | Type | Null | Description | Role | Format |
|---|--------|------|------|-------------|------|--------|
| 1 | `archive_id` | uuid | N | **MISSING** | -- | -- |
| 2 | `outreach_id` | uuid | N | **MISSING** | -- | -- |
| 3 | `domain` | text | Y | **MISSING** | -- | -- |
| 4 | `email_method` | text | Y | **MISSING** | -- | -- |
| 5 | `method_type` | text | Y | **MISSING** | -- | -- |
| 6 | `confidence_score` | numeric | Y | **MISSING** | -- | -- |
| 7 | `archived_at` | timestamp with time zone | Y | **MISSING** | -- | -- |
| 8 | `archive_reason` | text | Y | **MISSING** | -- | -- |

#### `outreach.company_target_errors` -- ERROR -- 4,108 rows

Column registry: **4/28 documented**

| # | Column | Type | Null | Description | Role | Format |
|---|--------|------|------|-------------|------|--------|
| 1 | `error_id` | uuid | N | Primary key for error record | identifier | UUID |
| 2 | `outreach_id` | uuid | N | FK to spine (nullable — error may occur before entity exists) | foreign_key | UUID |
| 3 | `pipeline_stage` | character varying(100) | N | **MISSING** | -- | -- |
| 4 | `failure_code` | character varying(50) | N | **MISSING** | -- | -- |
| 5 | `blocking_reason` | text | N | **MISSING** | -- | -- |
| 6 | `severity` | character varying(20) | N | **MISSING** | -- | -- |
| 7 | `retry_allowed` | boolean | N | **MISSING** | -- | -- |
| 8 | `created_at` | timestamp with time zone | N | When the error was recorded | attribute | ISO-8601 |
| 9 | `resolved_at` | timestamp with time zone | Y | **MISSING** | -- | -- |
| 10 | `resolution_note` | text | Y | **MISSING** | -- | -- |
| 11 | `raw_input` | jsonb | Y | **MISSING** | -- | -- |
| 12 | `stack_trace` | text | Y | **MISSING** | -- | -- |
| 13 | `imo_stage` | character varying(10) | Y | **MISSING** | -- | -- |
| 14 | `requeue_attempts` | integer | Y | **MISSING** | -- | -- |
| 15 | `disposition` | USER-DEFINED | Y | **MISSING** | -- | -- |
| 16 | `retry_count` | integer | Y | **MISSING** | -- | -- |
| 17 | `max_retries` | integer | Y | **MISSING** | -- | -- |
| 18 | `archived_at` | timestamp with time zone | Y | **MISSING** | -- | -- |
| 19 | `parked_at` | timestamp with time zone | Y | **MISSING** | -- | -- |
| 20 | `parked_by` | text | Y | **MISSING** | -- | -- |
| 21 | `park_reason` | text | Y | **MISSING** | -- | -- |
| 22 | `escalation_level` | integer | Y | **MISSING** | -- | -- |
| 23 | `escalated_at` | timestamp with time zone | Y | **MISSING** | -- | -- |
| 24 | `ttl_tier` | USER-DEFINED | Y | **MISSING** | -- | -- |
| 25 | `last_retry_at` | timestamp with time zone | Y | **MISSING** | -- | -- |
| 26 | `next_retry_at` | timestamp with time zone | Y | **MISSING** | -- | -- |
| 27 | `retry_exhausted` | boolean | Y | **MISSING** | -- | -- |
| 28 | `error_type` | character varying(100) | Y | Discriminator column — classifies the error | attribute | ENUM |

#### `outreach.company_target_errors_archive` -- ARCHIVE -- 0 rows

Column registry: **UNDOCUMENTED**

| # | Column | Type | Null | Description | Role | Format |
|---|--------|------|------|-------------|------|--------|
| 1 | `error_id` | uuid | N | **MISSING** | -- | -- |
| 2 | `outreach_id` | uuid | Y | **MISSING** | -- | -- |
| 3 | `pipeline_stage` | character varying(50) | Y | **MISSING** | -- | -- |
| 4 | `imo_stage` | character varying(50) | Y | **MISSING** | -- | -- |
| 5 | `failure_code` | character varying(50) | Y | **MISSING** | -- | -- |
| 6 | `blocking_reason` | text | Y | **MISSING** | -- | -- |
| 7 | `severity` | character varying(20) | Y | **MISSING** | -- | -- |
| 8 | `retry_allowed` | boolean | Y | **MISSING** | -- | -- |
| 9 | `raw_input` | jsonb | Y | **MISSING** | -- | -- |
| 10 | `stack_trace` | text | Y | **MISSING** | -- | -- |
| 11 | `created_at` | timestamp with time zone | Y | **MISSING** | -- | -- |
| 12 | `resolved_at` | timestamp with time zone | Y | **MISSING** | -- | -- |
| 13 | `resolution_note` | text | Y | **MISSING** | -- | -- |
| 14 | `disposition` | USER-DEFINED | Y | **MISSING** | -- | -- |
| 15 | `retry_count` | integer | Y | **MISSING** | -- | -- |
| 16 | `max_retries` | integer | Y | **MISSING** | -- | -- |
| 17 | `parked_at` | timestamp with time zone | Y | **MISSING** | -- | -- |
| 18 | `parked_by` | text | Y | **MISSING** | -- | -- |
| 19 | `park_reason` | text | Y | **MISSING** | -- | -- |
| 20 | `escalation_level` | integer | Y | **MISSING** | -- | -- |
| 21 | `escalated_at` | timestamp with time zone | Y | **MISSING** | -- | -- |
| 22 | `ttl_tier` | USER-DEFINED | Y | **MISSING** | -- | -- |
| 23 | `last_retry_at` | timestamp with time zone | Y | **MISSING** | -- | -- |
| 24 | `retry_exhausted` | boolean | Y | **MISSING** | -- | -- |
| 25 | `archived_at` | timestamp with time zone | N | **MISSING** | -- | -- |
| 26 | `archived_by` | text | Y | **MISSING** | -- | -- |
| 27 | `archive_reason` | text | Y | **MISSING** | -- | -- |
| 28 | `final_disposition` | USER-DEFINED | Y | **MISSING** | -- | -- |
| 29 | `retention_expires_at` | timestamp with time zone | Y | **MISSING** | -- | -- |
| 30 | `error_type` | character varying(100) | Y | **MISSING** | -- | -- |

#### `outreach.company_target_orphaned_archive` -- ARCHIVE -- 52,812 rows

Column registry: **UNDOCUMENTED**

| # | Column | Type | Null | Description | Role | Format |
|---|--------|------|------|-------------|------|--------|
| 1 | `archived_at` | timestamp with time zone | N | **MISSING** | -- | -- |
| 2 | `archive_reason` | text | Y | **MISSING** | -- | -- |
| 3 | `target_id` | uuid | N | **MISSING** | -- | -- |
| 4 | `company_unique_id` | text | Y | **MISSING** | -- | -- |
| 5 | `outreach_id` | uuid | Y | **MISSING** | -- | -- |
| 6 | `email_method` | character varying(255) | Y | **MISSING** | -- | -- |
| 7 | `method_type` | character varying(50) | Y | **MISSING** | -- | -- |
| 8 | `confidence_score` | numeric | Y | **MISSING** | -- | -- |
| 9 | `execution_status` | character varying(50) | Y | **MISSING** | -- | -- |
| 10 | `outreach_status` | text | Y | **MISSING** | -- | -- |
| 11 | `bit_score_snapshot` | integer | Y | **MISSING** | -- | -- |
| 12 | `first_targeted_at` | timestamp with time zone | Y | **MISSING** | -- | -- |
| 13 | `last_targeted_at` | timestamp with time zone | Y | **MISSING** | -- | -- |
| 14 | `sequence_count` | integer | Y | **MISSING** | -- | -- |
| 15 | `active_sequence_id` | text | Y | **MISSING** | -- | -- |
| 16 | `source` | text | Y | **MISSING** | -- | -- |
| 17 | `imo_completed_at` | timestamp with time zone | Y | **MISSING** | -- | -- |
| 18 | `is_catchall` | boolean | Y | **MISSING** | -- | -- |
| 19 | `industry` | character varying(100) | Y | **MISSING** | -- | -- |
| 20 | `employees` | integer | Y | **MISSING** | -- | -- |
| 21 | `country` | character varying(100) | Y | **MISSING** | -- | -- |
| 22 | `state` | character varying(100) | Y | **MISSING** | -- | -- |
| 23 | `city` | character varying(100) | Y | **MISSING** | -- | -- |
| 24 | `postal_code` | character varying(20) | Y | **MISSING** | -- | -- |
| 25 | `data_year` | integer | Y | **MISSING** | -- | -- |
| 26 | `created_at` | timestamp with time zone | Y | **MISSING** | -- | -- |
| 27 | `updated_at` | timestamp with time zone | Y | **MISSING** | -- | -- |
| 28 | `sovereign_id` | uuid | Y | **MISSING** | -- | -- |
| 29 | `domain` | character varying(255) | Y | **MISSING** | -- | -- |

#### `outreach.ctb_audit_log` -- SYSTEM -- 1,534 rows

Column registry: **UNDOCUMENTED**

| # | Column | Type | Null | Description | Role | Format |
|---|--------|------|------|-------------|------|--------|
| 1 | `audit_id` | integer | N | **MISSING** | -- | -- |
| 2 | `source_hub` | character varying(50) | N | **MISSING** | -- | -- |
| 3 | `source_table` | character varying(100) | N | **MISSING** | -- | -- |
| 4 | `log_data` | jsonb | N | **MISSING** | -- | -- |
| 5 | `original_id` | text | Y | **MISSING** | -- | -- |
| 6 | `original_created_at` | timestamp with time zone | Y | **MISSING** | -- | -- |
| 7 | `ctb_merged_at` | timestamp with time zone | Y | **MISSING** | -- | -- |

#### `outreach.ctb_queue` -- STAGING -- 33,217 rows

Column registry: **UNDOCUMENTED**

| # | Column | Type | Null | Description | Role | Format |
|---|--------|------|------|-------------|------|--------|
| 1 | `queue_id` | integer | N | **MISSING** | -- | -- |
| 2 | `queue_type` | character varying(50) | N | **MISSING** | -- | -- |
| 3 | `source_table` | character varying(100) | N | **MISSING** | -- | -- |
| 4 | `queue_data` | jsonb | N | **MISSING** | -- | -- |
| 5 | `company_unique_id` | text | Y | **MISSING** | -- | -- |
| 6 | `status` | character varying(50) | Y | **MISSING** | -- | -- |
| 7 | `priority` | integer | Y | **MISSING** | -- | -- |
| 8 | `original_created_at` | timestamp with time zone | Y | **MISSING** | -- | -- |
| 9 | `ctb_merged_at` | timestamp with time zone | Y | **MISSING** | -- | -- |

#### `outreach.dol` -- CANONICAL FROZEN -- 147,031 rows

Column registry: **6/12 documented**

| # | Column | Type | Null | Description | Role | Format |
|---|--------|------|------|-------------|------|--------|
| 1 | `dol_id` | uuid | N | **MISSING** | -- | -- |
| 2 | `outreach_id` | uuid | N | FK to outreach.outreach spine table | foreign_key | UUID |
| 3 | `ein` | text | Y | Employer Identification Number (9-digit, no dashes) | identifier | STRING |
| 4 | `filing_present` | boolean | Y | Whether a Form 5500 filing exists for this EIN | attribute | BOOLEAN |
| 5 | `funding_type` | text | Y | Benefit funding classification (pension_only, fully_insured, self_funded) | attribute | ENUM |
| 6 | `broker_or_advisor` | text | Y | **MISSING** | -- | -- |
| 7 | `carrier` | text | Y | **MISSING** | -- | -- |
| 8 | `created_at` | timestamp with time zone | Y | **MISSING** | -- | -- |
| 9 | `updated_at` | timestamp with time zone | Y | **MISSING** | -- | -- |
| 10 | `url_enrichment_data` | jsonb | Y | **MISSING** | -- | -- |
| 11 | `renewal_month` | integer | Y | Plan year begin month (1-12) | metric | INTEGER |
| 12 | `outreach_start_month` | integer | Y | 5 months before renewal month (1-12) — when to begin outreach | metric | INTEGER |

#### `outreach.dol_archive` -- ARCHIVE -- 1,623 rows

Column registry: **UNDOCUMENTED**

| # | Column | Type | Null | Description | Role | Format |
|---|--------|------|------|-------------|------|--------|
| 1 | `dol_id` | uuid | N | **MISSING** | -- | -- |
| 2 | `outreach_id` | uuid | N | **MISSING** | -- | -- |
| 3 | `ein` | text | Y | **MISSING** | -- | -- |
| 4 | `filing_present` | boolean | Y | **MISSING** | -- | -- |
| 5 | `funding_type` | text | Y | **MISSING** | -- | -- |
| 6 | `broker_or_advisor` | text | Y | **MISSING** | -- | -- |
| 7 | `carrier` | text | Y | **MISSING** | -- | -- |
| 8 | `created_at` | timestamp with time zone | Y | **MISSING** | -- | -- |
| 9 | `updated_at` | timestamp with time zone | Y | **MISSING** | -- | -- |
| 10 | `archived_at` | timestamp with time zone | Y | **MISSING** | -- | -- |
| 11 | `archive_reason` | text | Y | **MISSING** | -- | -- |

#### `outreach.dol_audit_log` -- SYSTEM -- 0 rows

Column registry: **UNDOCUMENTED**

| # | Column | Type | Null | Description | Role | Format |
|---|--------|------|------|-------------|------|--------|
| 1 | `log_id` | integer | N | **MISSING** | -- | -- |
| 2 | `company_id` | text | N | **MISSING** | -- | -- |
| 3 | `state` | text | Y | **MISSING** | -- | -- |
| 4 | `attempted` | boolean | Y | **MISSING** | -- | -- |
| 5 | `outcome` | text | N | **MISSING** | -- | -- |
| 6 | `ein` | text | Y | **MISSING** | -- | -- |
| 7 | `fail_reason` | text | Y | **MISSING** | -- | -- |
| 8 | `run_id` | text | N | **MISSING** | -- | -- |
| 9 | `created_at` | timestamp with time zone | Y | **MISSING** | -- | -- |

#### `outreach.dol_errors` -- ERROR -- 28,572 rows

Column registry: **4/27 documented**

| # | Column | Type | Null | Description | Role | Format |
|---|--------|------|------|-------------|------|--------|
| 1 | `error_id` | uuid | N | Primary key for error record | identifier | UUID |
| 2 | `outreach_id` | uuid | N | FK to spine (nullable — error may occur before entity exists) | foreign_key | UUID |
| 3 | `pipeline_stage` | character varying(100) | N | **MISSING** | -- | -- |
| 4 | `failure_code` | character varying(50) | N | **MISSING** | -- | -- |
| 5 | `blocking_reason` | text | N | **MISSING** | -- | -- |
| 6 | `severity` | character varying(20) | N | **MISSING** | -- | -- |
| 7 | `retry_allowed` | boolean | N | **MISSING** | -- | -- |
| 8 | `created_at` | timestamp with time zone | N | When the error was recorded | attribute | ISO-8601 |
| 9 | `resolved_at` | timestamp with time zone | Y | **MISSING** | -- | -- |
| 10 | `resolution_note` | text | Y | **MISSING** | -- | -- |
| 11 | `raw_input` | jsonb | Y | **MISSING** | -- | -- |
| 12 | `stack_trace` | text | Y | **MISSING** | -- | -- |
| 13 | `requeue_attempts` | integer | Y | **MISSING** | -- | -- |
| 14 | `disposition` | USER-DEFINED | Y | **MISSING** | -- | -- |
| 15 | `retry_count` | integer | Y | **MISSING** | -- | -- |
| 16 | `max_retries` | integer | Y | **MISSING** | -- | -- |
| 17 | `archived_at` | timestamp with time zone | Y | **MISSING** | -- | -- |
| 18 | `parked_at` | timestamp with time zone | Y | **MISSING** | -- | -- |
| 19 | `parked_by` | text | Y | **MISSING** | -- | -- |
| 20 | `park_reason` | text | Y | **MISSING** | -- | -- |
| 21 | `escalation_level` | integer | Y | **MISSING** | -- | -- |
| 22 | `escalated_at` | timestamp with time zone | Y | **MISSING** | -- | -- |
| 23 | `ttl_tier` | USER-DEFINED | Y | **MISSING** | -- | -- |
| 24 | `last_retry_at` | timestamp with time zone | Y | **MISSING** | -- | -- |
| 25 | `next_retry_at` | timestamp with time zone | Y | **MISSING** | -- | -- |
| 26 | `retry_exhausted` | boolean | Y | **MISSING** | -- | -- |
| 27 | `error_type` | character varying(100) | N | Discriminator column — classifies the DOL error | attribute | ENUM |

#### `outreach.dol_errors_archive` -- ARCHIVE -- 0 rows

Column registry: **UNDOCUMENTED**

| # | Column | Type | Null | Description | Role | Format |
|---|--------|------|------|-------------|------|--------|
| 1 | `error_id` | uuid | N | **MISSING** | -- | -- |
| 2 | `outreach_id` | uuid | Y | **MISSING** | -- | -- |
| 3 | `pipeline_stage` | character varying(50) | Y | **MISSING** | -- | -- |
| 4 | `failure_code` | character varying(50) | Y | **MISSING** | -- | -- |
| 5 | `blocking_reason` | text | Y | **MISSING** | -- | -- |
| 6 | `severity` | character varying(20) | Y | **MISSING** | -- | -- |
| 7 | `retry_allowed` | boolean | Y | **MISSING** | -- | -- |
| 8 | `raw_input` | jsonb | Y | **MISSING** | -- | -- |
| 9 | `stack_trace` | text | Y | **MISSING** | -- | -- |
| 10 | `created_at` | timestamp with time zone | Y | **MISSING** | -- | -- |
| 11 | `resolved_at` | timestamp with time zone | Y | **MISSING** | -- | -- |
| 12 | `resolution_note` | text | Y | **MISSING** | -- | -- |
| 13 | `disposition` | USER-DEFINED | Y | **MISSING** | -- | -- |
| 14 | `retry_count` | integer | Y | **MISSING** | -- | -- |
| 15 | `max_retries` | integer | Y | **MISSING** | -- | -- |
| 16 | `parked_at` | timestamp with time zone | Y | **MISSING** | -- | -- |
| 17 | `parked_by` | text | Y | **MISSING** | -- | -- |
| 18 | `park_reason` | text | Y | **MISSING** | -- | -- |
| 19 | `escalation_level` | integer | Y | **MISSING** | -- | -- |
| 20 | `escalated_at` | timestamp with time zone | Y | **MISSING** | -- | -- |
| 21 | `ttl_tier` | USER-DEFINED | Y | **MISSING** | -- | -- |
| 22 | `last_retry_at` | timestamp with time zone | Y | **MISSING** | -- | -- |
| 23 | `retry_exhausted` | boolean | Y | **MISSING** | -- | -- |
| 24 | `archived_at` | timestamp with time zone | N | **MISSING** | -- | -- |
| 25 | `archived_by` | text | Y | **MISSING** | -- | -- |
| 26 | `archive_reason` | text | Y | **MISSING** | -- | -- |
| 27 | `final_disposition` | USER-DEFINED | Y | **MISSING** | -- | -- |
| 28 | `retention_expires_at` | timestamp with time zone | Y | **MISSING** | -- | -- |
| 29 | `error_type` | character varying(100) | Y | **MISSING** | -- | -- |

#### `outreach.dol_url_enrichment` -- STAGING -- 16 rows

Column registry: **UNDOCUMENTED**

| # | Column | Type | Null | Description | Role | Format |
|---|--------|------|------|-------------|------|--------|
| 1 | `id` | uuid | N | **MISSING** | -- | -- |
| 2 | `ein` | character varying(9) | N | **MISSING** | -- | -- |
| 3 | `legal_name` | text | N | **MISSING** | -- | -- |
| 4 | `dba_name` | text | Y | **MISSING** | -- | -- |
| 5 | `city` | text | Y | **MISSING** | -- | -- |
| 6 | `state` | character varying(2) | Y | **MISSING** | -- | -- |
| 7 | `zip` | character varying(10) | Y | **MISSING** | -- | -- |
| 8 | `participants` | integer | Y | **MISSING** | -- | -- |
| 9 | `enriched_url` | text | Y | **MISSING** | -- | -- |
| 10 | `search_query` | text | Y | **MISSING** | -- | -- |
| 11 | `confidence` | character varying(10) | Y | **MISSING** | -- | -- |
| 12 | `matched_company_unique_id` | text | Y | **MISSING** | -- | -- |
| 13 | `match_status` | character varying(20) | Y | **MISSING** | -- | -- |
| 14 | `created_at` | timestamp with time zone | Y | **MISSING** | -- | -- |

#### `outreach.engagement_events` -- MV -- 0 rows

Column registry: **UNDOCUMENTED**

| # | Column | Type | Null | Description | Role | Format |
|---|--------|------|------|-------------|------|--------|
| 1 | `event_id` | uuid | N | **MISSING** | -- | -- |
| 2 | `person_id` | uuid | N | **MISSING** | -- | -- |
| 3 | `target_id` | uuid | N | **MISSING** | -- | -- |
| 4 | `company_unique_id` | text | N | **MISSING** | -- | -- |
| 5 | `event_type` | USER-DEFINED | N | **MISSING** | -- | -- |
| 6 | `event_subtype` | text | Y | **MISSING** | -- | -- |
| 7 | `event_ts` | timestamp with time zone | N | **MISSING** | -- | -- |
| 8 | `source_system` | text | Y | **MISSING** | -- | -- |
| 9 | `source_campaign_id` | text | Y | **MISSING** | -- | -- |
| 10 | `source_email_id` | text | Y | **MISSING** | -- | -- |
| 11 | `metadata` | jsonb | N | **MISSING** | -- | -- |
| 12 | `is_processed` | boolean | N | **MISSING** | -- | -- |
| 13 | `processed_at` | timestamp with time zone | Y | **MISSING** | -- | -- |
| 14 | `triggered_transition` | boolean | N | **MISSING** | -- | -- |
| 15 | `transition_to_state` | USER-DEFINED | Y | **MISSING** | -- | -- |
| 16 | `event_hash` | character varying(64) | Y | **MISSING** | -- | -- |
| 17 | `is_duplicate` | boolean | N | **MISSING** | -- | -- |
| 18 | `created_at` | timestamp with time zone | N | **MISSING** | -- | -- |
| 19 | `outreach_id` | uuid | Y | **MISSING** | -- | -- |

#### `outreach.entity_resolution_queue` -- STAGING -- 2 rows

Column registry: **UNDOCUMENTED**

| # | Column | Type | Null | Description | Role | Format |
|---|--------|------|------|-------------|------|--------|
| 1 | `id` | uuid | N | **MISSING** | -- | -- |
| 2 | `company_unique_id` | text | N | **MISSING** | -- | -- |
| 3 | `candidate_ein` | character varying(9) | Y | **MISSING** | -- | -- |
| 4 | `candidate_name` | text | Y | **MISSING** | -- | -- |
| 5 | `candidate_city` | text | Y | **MISSING** | -- | -- |
| 6 | `candidate_state` | character varying(2) | Y | **MISSING** | -- | -- |
| 7 | `candidate_zip` | character varying(10) | Y | **MISSING** | -- | -- |
| 8 | `clay_domain` | text | Y | **MISSING** | -- | -- |
| 9 | `match_score` | numeric | Y | **MISSING** | -- | -- |
| 10 | `match_tier` | character varying(10) | Y | **MISSING** | -- | -- |
| 11 | `resolution_status` | character varying(20) | Y | **MISSING** | -- | -- |
| 12 | `resolution_method` | text | Y | **MISSING** | -- | -- |
| 13 | `resolved_at` | timestamp with time zone | Y | **MISSING** | -- | -- |
| 14 | `created_at` | timestamp with time zone | Y | **MISSING** | -- | -- |
| 15 | `queue_type` | character varying(50) | Y | **MISSING** | -- | -- |

#### `outreach.hub_registry` -- REGISTRY -- 6 rows

Column registry: **UNDOCUMENTED**

| # | Column | Type | Null | Description | Role | Format |
|---|--------|------|------|-------------|------|--------|
| 1 | `hub_id` | character varying(50) | N | **MISSING** | -- | -- |
| 2 | `hub_name` | character varying(100) | N | **MISSING** | -- | -- |
| 3 | `doctrine_id` | character varying(20) | N | **MISSING** | -- | -- |
| 4 | `classification` | character varying(20) | N | **MISSING** | -- | -- |
| 5 | `gates_completion` | boolean | N | **MISSING** | -- | -- |
| 6 | `waterfall_order` | integer | N | **MISSING** | -- | -- |
| 7 | `core_metric` | character varying(50) | N | **MISSING** | -- | -- |
| 8 | `metric_healthy_threshold` | numeric | Y | **MISSING** | -- | -- |
| 9 | `metric_critical_threshold` | numeric | Y | **MISSING** | -- | -- |
| 10 | `description` | text | Y | **MISSING** | -- | -- |
| 11 | `created_at` | timestamp with time zone | N | **MISSING** | -- | -- |
| 12 | `updated_at` | timestamp with time zone | N | **MISSING** | -- | -- |

#### `outreach.manual_overrides` -- SYSTEM -- 0 rows

Column registry: **UNDOCUMENTED**

| # | Column | Type | Null | Description | Role | Format |
|---|--------|------|------|-------------|------|--------|
| 1 | `override_id` | uuid | N | **MISSING** | -- | -- |
| 2 | `company_unique_id` | text | N | **MISSING** | -- | -- |
| 3 | `override_type` | USER-DEFINED | N | **MISSING** | -- | -- |
| 4 | `reason` | text | N | **MISSING** | -- | -- |
| 5 | `metadata` | jsonb | Y | **MISSING** | -- | -- |
| 6 | `created_at` | timestamp with time zone | N | **MISSING** | -- | -- |
| 7 | `created_by` | text | N | **MISSING** | -- | -- |
| 8 | `expires_at` | timestamp with time zone | Y | **MISSING** | -- | -- |
| 9 | `is_active` | boolean | N | **MISSING** | -- | -- |
| 10 | `deactivated_at` | timestamp with time zone | Y | **MISSING** | -- | -- |
| 11 | `deactivated_by` | text | Y | **MISSING** | -- | -- |
| 12 | `deactivation_reason` | text | Y | **MISSING** | -- | -- |

#### `outreach.mv_credit_usage` -- SYSTEM -- 2 rows

Column registry: **UNDOCUMENTED**

| # | Column | Type | Null | Description | Role | Format |
|---|--------|------|------|-------------|------|--------|
| 1 | `id` | integer | N | **MISSING** | -- | -- |
| 2 | `usage_date` | date | N | **MISSING** | -- | -- |
| 3 | `credits_used` | integer | N | **MISSING** | -- | -- |
| 4 | `cost_estimate` | numeric | Y | **MISSING** | -- | -- |
| 5 | `created_at` | timestamp with time zone | Y | **MISSING** | -- | -- |
| 6 | `updated_at` | timestamp with time zone | Y | **MISSING** | -- | -- |

#### `outreach.outreach` -- CANONICAL FROZEN -- 114,137 rows

Column registry: **3/7 documented**

| # | Column | Type | Null | Description | Role | Format |
|---|--------|------|------|-------------|------|--------|
| 1 | `outreach_id` | uuid | N | Universal join key — minted here, propagated to all sub-hub tables | identifier | UUID |
| 2 | `sovereign_id` | uuid | N | **MISSING** | -- | -- |
| 3 | `created_at` | timestamp with time zone | N | When the outreach record was created | attribute | ISO-8601 |
| 4 | `updated_at` | timestamp with time zone | N | When the outreach record was last updated | attribute | ISO-8601 |
| 5 | `domain` | character varying(255) | Y | **MISSING** | -- | -- |
| 6 | `ein` | character varying(20) | Y | **MISSING** | -- | -- |
| 7 | `has_appointment` | boolean | Y | **MISSING** | -- | -- |

#### `outreach.outreach_archive` -- ARCHIVE -- 27,416 rows

Column registry: **UNDOCUMENTED**

| # | Column | Type | Null | Description | Role | Format |
|---|--------|------|------|-------------|------|--------|
| 1 | `outreach_id` | uuid | N | **MISSING** | -- | -- |
| 2 | `sovereign_id` | uuid | N | **MISSING** | -- | -- |
| 3 | `created_at` | timestamp with time zone | N | **MISSING** | -- | -- |
| 4 | `updated_at` | timestamp with time zone | N | **MISSING** | -- | -- |
| 5 | `domain` | character varying(255) | Y | **MISSING** | -- | -- |
| 6 | `archived_at` | timestamp with time zone | Y | **MISSING** | -- | -- |
| 7 | `archive_reason` | text | Y | **MISSING** | -- | -- |

#### `outreach.outreach_errors` -- ERROR -- 0 rows

Column registry: **UNDOCUMENTED**

| # | Column | Type | Null | Description | Role | Format |
|---|--------|------|------|-------------|------|--------|
| 1 | `error_id` | uuid | N | **MISSING** | -- | -- |
| 2 | `company_unique_id` | text | N | **MISSING** | -- | -- |
| 3 | `outreach_id` | text | Y | **MISSING** | -- | -- |
| 4 | `pipeline_stage` | text | N | **MISSING** | -- | -- |
| 5 | `failure_code` | text | N | **MISSING** | -- | -- |
| 6 | `details` | text | Y | **MISSING** | -- | -- |
| 7 | `run_id` | text | N | **MISSING** | -- | -- |
| 8 | `created_at` | timestamp with time zone | Y | **MISSING** | -- | -- |
| 9 | `error_type` | character varying(100) | Y | **MISSING** | -- | -- |

#### `outreach.outreach_excluded` -- ARCHIVE -- 5,483 rows

Column registry: **UNDOCUMENTED**

| # | Column | Type | Null | Description | Role | Format |
|---|--------|------|------|-------------|------|--------|
| 1 | `outreach_id` | uuid | N | **MISSING** | -- | -- |
| 2 | `company_name` | text | Y | **MISSING** | -- | -- |
| 3 | `domain` | text | Y | **MISSING** | -- | -- |
| 4 | `exclusion_reason` | text | Y | **MISSING** | -- | -- |
| 5 | `excluded_at` | timestamp with time zone | Y | **MISSING** | -- | -- |
| 6 | `created_at` | timestamp with time zone | Y | **MISSING** | -- | -- |
| 7 | `updated_at` | timestamp with time zone | Y | **MISSING** | -- | -- |
| 8 | `sovereign_id` | uuid | Y | **MISSING** | -- | -- |
| 9 | `cl_status` | text | Y | **MISSING** | -- | -- |
| 10 | `excluded_by` | text | Y | **MISSING** | -- | -- |

#### `outreach.outreach_legacy_quarantine` -- ARCHIVE -- 1,698 rows

Column registry: **UNDOCUMENTED**

| # | Column | Type | Null | Description | Role | Format |
|---|--------|------|------|-------------|------|--------|
| 1 | `outreach_id` | uuid | N | **MISSING** | -- | -- |
| 2 | `sovereign_id` | uuid | Y | **MISSING** | -- | -- |
| 3 | `quarantine_reason` | text | N | **MISSING** | -- | -- |
| 4 | `original_created_at` | timestamp with time zone | Y | **MISSING** | -- | -- |
| 5 | `quarantined_at` | timestamp with time zone | Y | **MISSING** | -- | -- |

#### `outreach.outreach_orphan_archive` -- ARCHIVE -- 2,709 rows

Column registry: **UNDOCUMENTED**

| # | Column | Type | Null | Description | Role | Format |
|---|--------|------|------|-------------|------|--------|
| 1 | `outreach_id` | uuid | N | **MISSING** | -- | -- |
| 2 | `sovereign_id` | uuid | N | **MISSING** | -- | -- |
| 3 | `created_at` | timestamp with time zone | N | **MISSING** | -- | -- |
| 4 | `updated_at` | timestamp with time zone | N | **MISSING** | -- | -- |
| 5 | `domain` | character varying | Y | **MISSING** | -- | -- |
| 6 | `archived_at` | timestamp with time zone | Y | **MISSING** | -- | -- |
| 7 | `archive_reason` | character varying | Y | **MISSING** | -- | -- |

#### `outreach.override_audit_log` -- SYSTEM -- 0 rows

Column registry: **UNDOCUMENTED**

| # | Column | Type | Null | Description | Role | Format |
|---|--------|------|------|-------------|------|--------|
| 1 | `audit_id` | uuid | N | **MISSING** | -- | -- |
| 2 | `company_unique_id` | text | N | **MISSING** | -- | -- |
| 3 | `override_id` | uuid | Y | **MISSING** | -- | -- |
| 4 | `action` | text | N | **MISSING** | -- | -- |
| 5 | `override_type` | USER-DEFINED | Y | **MISSING** | -- | -- |
| 6 | `old_value` | jsonb | Y | **MISSING** | -- | -- |
| 7 | `new_value` | jsonb | Y | **MISSING** | -- | -- |
| 8 | `performed_by` | text | N | **MISSING** | -- | -- |
| 9 | `performed_at` | timestamp with time zone | N | **MISSING** | -- | -- |

#### `outreach.people` -- SUPPORTING FROZEN -- 335,097 rows

Column registry: **UNDOCUMENTED**

| # | Column | Type | Null | Description | Role | Format |
|---|--------|------|------|-------------|------|--------|
| 1 | `person_id` | uuid | N | **MISSING** | -- | -- |
| 2 | `target_id` | uuid | N | **MISSING** | -- | -- |
| 3 | `company_unique_id` | text | N | **MISSING** | -- | -- |
| 4 | `slot_type` | text | Y | **MISSING** | -- | -- |
| 5 | `email` | text | N | **MISSING** | -- | -- |
| 6 | `email_verified` | boolean | N | **MISSING** | -- | -- |
| 7 | `email_verified_at` | timestamp with time zone | Y | **MISSING** | -- | -- |
| 8 | `contact_status` | text | N | **MISSING** | -- | -- |
| 9 | `lifecycle_state` | USER-DEFINED | N | **MISSING** | -- | -- |
| 10 | `funnel_membership` | USER-DEFINED | N | **MISSING** | -- | -- |
| 11 | `email_open_count` | integer | N | **MISSING** | -- | -- |
| 12 | `email_click_count` | integer | N | **MISSING** | -- | -- |
| 13 | `email_reply_count` | integer | N | **MISSING** | -- | -- |
| 14 | `current_bit_score` | integer | N | **MISSING** | -- | -- |
| 15 | `last_event_ts` | timestamp with time zone | Y | **MISSING** | -- | -- |
| 16 | `last_state_change_ts` | timestamp with time zone | Y | **MISSING** | -- | -- |
| 17 | `source` | text | Y | **MISSING** | -- | -- |
| 18 | `created_at` | timestamp with time zone | N | **MISSING** | -- | -- |
| 19 | `updated_at` | timestamp with time zone | N | **MISSING** | -- | -- |
| 20 | `outreach_id` | uuid | Y | **MISSING** | -- | -- |

#### `outreach.people_archive` -- ARCHIVE -- 175 rows

Column registry: **UNDOCUMENTED**

| # | Column | Type | Null | Description | Role | Format |
|---|--------|------|------|-------------|------|--------|
| 1 | `person_id` | uuid | N | **MISSING** | -- | -- |
| 2 | `target_id` | uuid | N | **MISSING** | -- | -- |
| 3 | `company_unique_id` | text | N | **MISSING** | -- | -- |
| 4 | `slot_type` | text | Y | **MISSING** | -- | -- |
| 5 | `email` | text | N | **MISSING** | -- | -- |
| 6 | `email_verified` | boolean | N | **MISSING** | -- | -- |
| 7 | `email_verified_at` | timestamp with time zone | Y | **MISSING** | -- | -- |
| 8 | `contact_status` | text | N | **MISSING** | -- | -- |
| 9 | `lifecycle_state` | USER-DEFINED | N | **MISSING** | -- | -- |
| 10 | `funnel_membership` | USER-DEFINED | N | **MISSING** | -- | -- |
| 11 | `email_open_count` | integer | N | **MISSING** | -- | -- |
| 12 | `email_click_count` | integer | N | **MISSING** | -- | -- |
| 13 | `email_reply_count` | integer | N | **MISSING** | -- | -- |
| 14 | `current_bit_score` | integer | N | **MISSING** | -- | -- |
| 15 | `last_event_ts` | timestamp with time zone | Y | **MISSING** | -- | -- |
| 16 | `last_state_change_ts` | timestamp with time zone | Y | **MISSING** | -- | -- |
| 17 | `source` | text | Y | **MISSING** | -- | -- |
| 18 | `created_at` | timestamp with time zone | N | **MISSING** | -- | -- |
| 19 | `updated_at` | timestamp with time zone | N | **MISSING** | -- | -- |
| 20 | `outreach_id` | uuid | Y | **MISSING** | -- | -- |
| 21 | `archived_at` | timestamp with time zone | Y | **MISSING** | -- | -- |
| 22 | `archive_reason` | text | Y | **MISSING** | -- | -- |

#### `outreach.people_errors` -- ERROR -- 0 rows

Column registry: **UNDOCUMENTED**

| # | Column | Type | Null | Description | Role | Format |
|---|--------|------|------|-------------|------|--------|
| 1 | `error_id` | uuid | N | **MISSING** | -- | -- |
| 2 | `outreach_id` | uuid | N | **MISSING** | -- | -- |
| 3 | `pipeline_stage` | character varying(100) | N | **MISSING** | -- | -- |
| 4 | `failure_code` | character varying(50) | N | **MISSING** | -- | -- |
| 5 | `blocking_reason` | text | N | **MISSING** | -- | -- |
| 6 | `severity` | character varying(20) | N | **MISSING** | -- | -- |
| 7 | `retry_allowed` | boolean | N | **MISSING** | -- | -- |
| 8 | `created_at` | timestamp with time zone | N | **MISSING** | -- | -- |
| 9 | `resolved_at` | timestamp with time zone | Y | **MISSING** | -- | -- |
| 10 | `resolution_note` | text | Y | **MISSING** | -- | -- |
| 11 | `raw_input` | jsonb | Y | **MISSING** | -- | -- |
| 12 | `stack_trace` | text | Y | **MISSING** | -- | -- |
| 13 | `requeue_attempts` | integer | Y | **MISSING** | -- | -- |
| 14 | `error_type` | character varying(100) | Y | **MISSING** | -- | -- |

#### `outreach.pipeline_audit_log` -- SYSTEM -- 0 rows

Column registry: **UNDOCUMENTED**

| # | Column | Type | Null | Description | Role | Format |
|---|--------|------|------|-------------|------|--------|
| 1 | `log_id` | integer | N | **MISSING** | -- | -- |
| 2 | `company_unique_id` | text | N | **MISSING** | -- | -- |
| 3 | `outreach_id` | text | Y | **MISSING** | -- | -- |
| 4 | `hub` | text | N | **MISSING** | -- | -- |
| 5 | `outcome` | text | N | **MISSING** | -- | -- |
| 6 | `failure_code` | text | Y | **MISSING** | -- | -- |
| 7 | `run_id` | text | N | **MISSING** | -- | -- |
| 8 | `created_at` | timestamp with time zone | Y | **MISSING** | -- | -- |
| 9 | `source_hub` | character varying(50) | Y | **MISSING** | -- | -- |

#### `outreach.send_log` -- DEPRECATED -- 0 rows

Column registry: **UNDOCUMENTED**

| # | Column | Type | Null | Description | Role | Format |
|---|--------|------|------|-------------|------|--------|
| 1 | `send_id` | uuid | N | **MISSING** | -- | -- |
| 2 | `campaign_id` | uuid | Y | **MISSING** | -- | -- |
| 3 | `sequence_id` | uuid | Y | **MISSING** | -- | -- |
| 4 | `person_id` | uuid | Y | **MISSING** | -- | -- |
| 5 | `target_id` | uuid | Y | **MISSING** | -- | -- |
| 6 | `company_unique_id` | text | Y | **MISSING** | -- | -- |
| 7 | `email_to` | character varying(255) | N | **MISSING** | -- | -- |
| 8 | `email_subject` | text | Y | **MISSING** | -- | -- |
| 9 | `sequence_step` | integer | N | **MISSING** | -- | -- |
| 10 | `send_status` | character varying(50) | N | **MISSING** | -- | -- |
| 11 | `scheduled_at` | timestamp with time zone | Y | **MISSING** | -- | -- |
| 12 | `sent_at` | timestamp with time zone | Y | **MISSING** | -- | -- |
| 13 | `delivered_at` | timestamp with time zone | Y | **MISSING** | -- | -- |
| 14 | `bounced_at` | timestamp with time zone | Y | **MISSING** | -- | -- |
| 15 | `opened_at` | timestamp with time zone | Y | **MISSING** | -- | -- |
| 16 | `clicked_at` | timestamp with time zone | Y | **MISSING** | -- | -- |
| 17 | `replied_at` | timestamp with time zone | Y | **MISSING** | -- | -- |
| 18 | `open_count` | integer | N | **MISSING** | -- | -- |
| 19 | `click_count` | integer | N | **MISSING** | -- | -- |
| 20 | `error_message` | text | Y | **MISSING** | -- | -- |
| 21 | `retry_count` | integer | N | **MISSING** | -- | -- |
| 22 | `source_system` | character varying(100) | Y | **MISSING** | -- | -- |
| 23 | `external_id` | character varying(255) | Y | **MISSING** | -- | -- |
| 24 | `created_at` | timestamp with time zone | N | **MISSING** | -- | -- |
| 25 | `updated_at` | timestamp with time zone | N | **MISSING** | -- | -- |

#### `outreach.sequences` -- DEPRECATED -- 0 rows

Column registry: **UNDOCUMENTED**

| # | Column | Type | Null | Description | Role | Format |
|---|--------|------|------|-------------|------|--------|
| 1 | `sequence_id` | uuid | N | **MISSING** | -- | -- |
| 2 | `campaign_id` | uuid | Y | **MISSING** | -- | -- |
| 3 | `sequence_name` | character varying(255) | N | **MISSING** | -- | -- |
| 4 | `sequence_order` | integer | N | **MISSING** | -- | -- |
| 5 | `subject_template` | text | Y | **MISSING** | -- | -- |
| 6 | `body_template` | text | Y | **MISSING** | -- | -- |
| 7 | `template_type` | character varying(50) | Y | **MISSING** | -- | -- |
| 8 | `delay_days` | integer | N | **MISSING** | -- | -- |
| 9 | `delay_hours` | integer | N | **MISSING** | -- | -- |
| 10 | `send_time_preference` | character varying(20) | Y | **MISSING** | -- | -- |
| 11 | `sequence_status` | character varying(50) | N | **MISSING** | -- | -- |
| 12 | `created_at` | timestamp with time zone | N | **MISSING** | -- | -- |
| 13 | `updated_at` | timestamp with time zone | N | **MISSING** | -- | -- |

#### `outreach.sitemap_discovery` -- UNREGISTERED -- 93,596 rows

Column registry: **UNDOCUMENTED**

| # | Column | Type | Null | Description | Role | Format |
|---|--------|------|------|-------------|------|--------|
| 1 | `outreach_id` | uuid | N | **MISSING** | -- | -- |
| 2 | `domain` | character varying | N | **MISSING** | -- | -- |
| 3 | `sitemap_url` | text | Y | **MISSING** | -- | -- |
| 4 | `sitemap_source` | character varying(10) | Y | **MISSING** | -- | -- |
| 5 | `has_sitemap` | boolean | N | **MISSING** | -- | -- |
| 6 | `discovered_at` | timestamp with time zone | N | **MISSING** | -- | -- |
| 7 | `domain_reachable` | boolean | Y | **MISSING** | -- | -- |
| 8 | `http_status` | smallint | Y | **MISSING** | -- | -- |
| 9 | `reachable_checked_at` | timestamp with time zone | Y | **MISSING** | -- | -- |

#### `outreach.source_urls` -- UNREGISTERED -- 81,292 rows

Column registry: **UNDOCUMENTED**

| # | Column | Type | Null | Description | Role | Format |
|---|--------|------|------|-------------|------|--------|
| 1 | `id` | bigint | N | **MISSING** | -- | -- |
| 2 | `outreach_id` | uuid | N | **MISSING** | -- | -- |
| 3 | `source_type` | text | N | **MISSING** | -- | -- |
| 4 | `source_url` | text | N | **MISSING** | -- | -- |
| 5 | `discovered_from` | text | Y | **MISSING** | -- | -- |
| 6 | `discovered_at` | timestamp with time zone | Y | **MISSING** | -- | -- |

#### `outreach.url_discovery_failures` -- ERROR -- 42,348 rows

Column registry: **UNDOCUMENTED**

| # | Column | Type | Null | Description | Role | Format |
|---|--------|------|------|-------------|------|--------|
| 1 | `failure_id` | uuid | N | **MISSING** | -- | -- |
| 2 | `company_unique_id` | text | N | **MISSING** | -- | -- |
| 3 | `website_url` | text | Y | **MISSING** | -- | -- |
| 4 | `failure_reason` | character varying(100) | N | **MISSING** | -- | -- |
| 5 | `retry_count` | integer | Y | **MISSING** | -- | -- |
| 6 | `last_attempt_at` | timestamp with time zone | Y | **MISSING** | -- | -- |
| 7 | `next_retry_at` | timestamp with time zone | Y | **MISSING** | -- | -- |
| 8 | `resolved_at` | timestamp with time zone | Y | **MISSING** | -- | -- |
| 9 | `created_at` | timestamp with time zone | Y | **MISSING** | -- | -- |
| 10 | `disposition` | USER-DEFINED | Y | **MISSING** | -- | -- |
| 11 | `max_retries` | integer | Y | **MISSING** | -- | -- |
| 12 | `archived_at` | timestamp with time zone | Y | **MISSING** | -- | -- |
| 13 | `parked_at` | timestamp with time zone | Y | **MISSING** | -- | -- |
| 14 | `parked_by` | text | Y | **MISSING** | -- | -- |
| 15 | `park_reason` | text | Y | **MISSING** | -- | -- |
| 16 | `escalation_level` | integer | Y | **MISSING** | -- | -- |
| 17 | `escalated_at` | timestamp with time zone | Y | **MISSING** | -- | -- |
| 18 | `ttl_tier` | USER-DEFINED | Y | **MISSING** | -- | -- |
| 19 | `last_retry_at` | timestamp with time zone | Y | **MISSING** | -- | -- |
| 20 | `retry_exhausted` | boolean | Y | **MISSING** | -- | -- |

#### `outreach.url_discovery_failures_archive` -- ARCHIVE -- 0 rows

Column registry: **UNDOCUMENTED**

| # | Column | Type | Null | Description | Role | Format |
|---|--------|------|------|-------------|------|--------|
| 1 | `failure_id` | uuid | N | **MISSING** | -- | -- |
| 2 | `company_unique_id` | text | Y | **MISSING** | -- | -- |
| 3 | `failure_reason` | character varying(50) | Y | **MISSING** | -- | -- |
| 4 | `created_at` | timestamp with time zone | Y | **MISSING** | -- | -- |
| 5 | `disposition` | USER-DEFINED | Y | **MISSING** | -- | -- |
| 6 | `retry_count` | integer | Y | **MISSING** | -- | -- |
| 7 | `max_retries` | integer | Y | **MISSING** | -- | -- |
| 8 | `parked_at` | timestamp with time zone | Y | **MISSING** | -- | -- |
| 9 | `parked_by` | text | Y | **MISSING** | -- | -- |
| 10 | `park_reason` | text | Y | **MISSING** | -- | -- |
| 11 | `escalation_level` | integer | Y | **MISSING** | -- | -- |
| 12 | `escalated_at` | timestamp with time zone | Y | **MISSING** | -- | -- |
| 13 | `ttl_tier` | USER-DEFINED | Y | **MISSING** | -- | -- |
| 14 | `last_retry_at` | timestamp with time zone | Y | **MISSING** | -- | -- |
| 15 | `retry_exhausted` | boolean | Y | **MISSING** | -- | -- |
| 16 | `archived_at` | timestamp with time zone | N | **MISSING** | -- | -- |
| 17 | `archived_by` | text | Y | **MISSING** | -- | -- |
| 18 | `archive_reason` | text | Y | **MISSING** | -- | -- |
| 19 | `final_disposition` | USER-DEFINED | Y | **MISSING** | -- | -- |
| 20 | `retention_expires_at` | timestamp with time zone | Y | **MISSING** | -- | -- |
| 21 | `website_url` | text | Y | **MISSING** | -- | -- |

### `outreach_ctx` -- Outreach Context -- API context tracking and spend logging

**Tables**: 3 | **Total rows**: 3

| Table | Leaf Type | Frozen | Rows | Columns | Documented |
|-------|-----------|--------|------|---------|------------|
| `context` | SYSTEM |  | 3 | 4 | 0 |
| `spend_log` | SYSTEM |  | 0 | 7 | 0 |
| `tool_attempts` | SYSTEM |  | 0 | 5 | 0 |

#### `outreach_ctx.context` -- SYSTEM -- 3 rows

Column registry: **UNDOCUMENTED**

| # | Column | Type | Null | Description | Role | Format |
|---|--------|------|------|-------------|------|--------|
| 1 | `outreach_context_id` | text | N | **MISSING** | -- | -- |
| 2 | `created_at` | timestamp with time zone | N | **MISSING** | -- | -- |
| 3 | `status` | text | N | **MISSING** | -- | -- |
| 4 | `notes` | text | Y | **MISSING** | -- | -- |

#### `outreach_ctx.spend_log` -- SYSTEM -- 0 rows

Column registry: **UNDOCUMENTED**

| # | Column | Type | Null | Description | Role | Format |
|---|--------|------|------|-------------|------|--------|
| 1 | `id` | bigint | N | **MISSING** | -- | -- |
| 2 | `outreach_context_id` | text | N | **MISSING** | -- | -- |
| 3 | `company_sov_id` | uuid | N | **MISSING** | -- | -- |
| 4 | `tool_name` | text | N | **MISSING** | -- | -- |
| 5 | `tier` | integer | N | **MISSING** | -- | -- |
| 6 | `cost_credits` | numeric | Y | **MISSING** | -- | -- |
| 7 | `attempted_at` | timestamp with time zone | N | **MISSING** | -- | -- |

#### `outreach_ctx.tool_attempts` -- SYSTEM -- 0 rows

Column registry: **UNDOCUMENTED**

| # | Column | Type | Null | Description | Role | Format |
|---|--------|------|------|-------------|------|--------|
| 1 | `id` | bigint | N | **MISSING** | -- | -- |
| 2 | `outreach_context_id` | text | N | **MISSING** | -- | -- |
| 3 | `tool_name` | text | N | **MISSING** | -- | -- |
| 4 | `tier` | integer | N | **MISSING** | -- | -- |
| 5 | `attempted_at` | timestamp with time zone | N | **MISSING** | -- | -- |

### `people` -- People Intelligence Sub-Hub -- executive slots, contact data, enrichment

**Tables**: 21 | **Total rows**: 699,317
**Views**: 10 -- contact_enhanced_view, due_email_recheck_30d, next_profile_urls_30d, v_extraction_progress, v_paid_queue_summary, v_slot_coverage, v_slot_tenure_summary, v_staging_summary, vw_profile_monitoring, vw_profile_staleness

| Table | Leaf Type | Frozen | Rows | Columns | Documented |
|-------|-----------|--------|------|---------|------------|
| `company_resolution_log` | SYSTEM |  | 155 | 8 | 0 |
| `company_slot` | CANONICAL | YES | 340,815 | 14 | 5/14 |
| `company_slot_archive` | ARCHIVE |  | 82,248 | 13 | 0 |
| `paid_enrichment_queue` | STAGING |  | 32,011 | 13 | 0 |
| `people_errors` | ERROR |  | 9,982 | 28 | 7/28 |
| `people_errors_archive` | ARCHIVE |  | 0 | 30 | 0 |
| `people_invalid` | ERROR |  | 21 | 26 | 0 |
| `people_master` | SUPPORTING | YES | 182,842 | 35 | 7/35 |
| `people_master_archive` | ARCHIVE |  | 47,486 | 35 | 0 |
| `people_promotion_audit` | SYSTEM |  | 9 | 6 | 0 |
| `people_resolution_history` | SYSTEM |  | 0 | 13 | 0 |
| `people_resolution_queue` | STAGING |  | 1,206 | 17 | 0 |
| `people_sidecar` | SUPPORTING |  | 0 | 10 | 0 |
| `person_movement_history` | SYSTEM |  | 0 | 11 | 0 |
| `person_scores` | SUPPORTING |  | 0 | 8 | 0 |
| `pressure_signals` | MV |  | 0 | 12 | 0 |
| `slot_assignment_history` | SYSTEM |  | 1,370 | 15 | 0 |
| `slot_ingress_control` | REGISTRY |  | 1 | 9 | 0 |
| `slot_orphan_snapshot_r0_002` | ARCHIVE |  | 1,053 | 8 | 0 |
| `slot_quarantine_r0_002` | ARCHIVE |  | 75 | 6 | 0 |
| `title_slot_mapping` | REGISTRY |  | 43 | 5 | 0 |

#### `people.company_resolution_log` -- SYSTEM -- 155 rows

Column registry: **UNDOCUMENTED**

| # | Column | Type | Null | Description | Role | Format |
|---|--------|------|------|-------------|------|--------|
| 1 | `log_id` | integer | N | **MISSING** | -- | -- |
| 2 | `person_intake_id` | text | N | **MISSING** | -- | -- |
| 3 | `resolution_status` | text | N | **MISSING** | -- | -- |
| 4 | `company_id` | text | Y | **MISSING** | -- | -- |
| 5 | `normalized_role` | text | Y | **MISSING** | -- | -- |
| 6 | `reason` | text | Y | **MISSING** | -- | -- |
| 7 | `run_id` | text | N | **MISSING** | -- | -- |
| 8 | `created_at` | timestamp with time zone | Y | **MISSING** | -- | -- |

#### `people.company_slot` -- CANONICAL FROZEN -- 340,815 rows

Column registry: **5/14 documented**

| # | Column | Type | Null | Description | Role | Format |
|---|--------|------|------|-------------|------|--------|
| 1 | `slot_id` | uuid | N | Primary key for the slot record | identifier | UUID |
| 2 | `outreach_id` | uuid | N | FK to outreach.outreach spine table | foreign_key | UUID |
| 3 | `company_unique_id` | text | N | **MISSING** | -- | -- |
| 4 | `slot_type` | text | N | Executive role type (CEO, CFO, HR, CTO, CMO, COO) | attribute | ENUM |
| 5 | `person_unique_id` | text | Y | FK to people.people_master.unique_id (Barton ID format 04.04.02.YY.NNNNNN.NNN) | foreign_key | STRING |
| 6 | `is_filled` | boolean | Y | Whether this slot has an assigned person (TRUE = people record linked) | attribute | BOOLEAN |
| 7 | `filled_at` | timestamp with time zone | Y | **MISSING** | -- | -- |
| 8 | `confidence_score` | numeric | Y | **MISSING** | -- | -- |
| 9 | `source_system` | text | Y | **MISSING** | -- | -- |
| 10 | `created_at` | timestamp with time zone | Y | **MISSING** | -- | -- |
| 11 | `updated_at` | timestamp with time zone | Y | **MISSING** | -- | -- |
| 12 | `slot_phone` | text | Y | **MISSING** | -- | -- |
| 13 | `slot_phone_source` | text | Y | **MISSING** | -- | -- |
| 14 | `slot_phone_updated_at` | timestamp with time zone | Y | **MISSING** | -- | -- |

#### `people.company_slot_archive` -- ARCHIVE -- 82,248 rows

Column registry: **UNDOCUMENTED**

| # | Column | Type | Null | Description | Role | Format |
|---|--------|------|------|-------------|------|--------|
| 1 | `slot_id` | uuid | N | **MISSING** | -- | -- |
| 2 | `outreach_id` | uuid | N | **MISSING** | -- | -- |
| 3 | `company_unique_id` | text | N | **MISSING** | -- | -- |
| 4 | `slot_type` | text | N | **MISSING** | -- | -- |
| 5 | `person_unique_id` | text | Y | **MISSING** | -- | -- |
| 6 | `is_filled` | boolean | Y | **MISSING** | -- | -- |
| 7 | `filled_at` | timestamp with time zone | Y | **MISSING** | -- | -- |
| 8 | `confidence_score` | numeric | Y | **MISSING** | -- | -- |
| 9 | `source_system` | text | Y | **MISSING** | -- | -- |
| 10 | `created_at` | timestamp with time zone | Y | **MISSING** | -- | -- |
| 11 | `updated_at` | timestamp with time zone | Y | **MISSING** | -- | -- |
| 12 | `archived_at` | timestamp with time zone | Y | **MISSING** | -- | -- |
| 13 | `archive_reason` | text | Y | **MISSING** | -- | -- |

#### `people.paid_enrichment_queue` -- STAGING -- 32,011 rows

Column registry: **UNDOCUMENTED**

| # | Column | Type | Null | Description | Role | Format |
|---|--------|------|------|-------------|------|--------|
| 1 | `id` | integer | N | **MISSING** | -- | -- |
| 2 | `source_url_id` | uuid | N | **MISSING** | -- | -- |
| 3 | `company_unique_id` | text | N | **MISSING** | -- | -- |
| 4 | `company_name` | character varying(255) | Y | **MISSING** | -- | -- |
| 5 | `source_url` | text | N | **MISSING** | -- | -- |
| 6 | `url_type` | character varying(50) | Y | **MISSING** | -- | -- |
| 7 | `failure_reason` | text | Y | **MISSING** | -- | -- |
| 8 | `empty_slots` | ARRAY | Y | **MISSING** | -- | -- |
| 9 | `priority` | integer | Y | **MISSING** | -- | -- |
| 10 | `queued_at` | timestamp without time zone | Y | **MISSING** | -- | -- |
| 11 | `processed_at` | timestamp without time zone | Y | **MISSING** | -- | -- |
| 12 | `processed_via` | character varying(50) | Y | **MISSING** | -- | -- |
| 13 | `status` | character varying(20) | Y | **MISSING** | -- | -- |

#### `people.people_errors` -- ERROR -- 9,982 rows

Column registry: **7/28 documented**

| # | Column | Type | Null | Description | Role | Format |
|---|--------|------|------|-------------|------|--------|
| 1 | `error_id` | uuid | N | Primary key for error record | identifier | UUID |
| 2 | `outreach_id` | uuid | N | FK to spine (nullable — error may occur before entity exists) | foreign_key | UUID |
| 3 | `slot_id` | uuid | Y | **MISSING** | -- | -- |
| 4 | `person_id` | uuid | Y | **MISSING** | -- | -- |
| 5 | `error_stage` | text | N | Pipeline stage where error occurred (slot_creation, slot_fill, etc.) | attribute | ENUM |
| 6 | `error_type` | text | N | Discriminator column (validation, ambiguity, conflict, missing_data, stale_data, external_fail) | attribute | ENUM |
| 7 | `error_code` | text | N | **MISSING** | -- | -- |
| 8 | `error_message` | text | N | Human-readable error description | attribute | STRING |
| 9 | `source_hints_used` | jsonb | Y | **MISSING** | -- | -- |
| 10 | `raw_payload` | jsonb | N | **MISSING** | -- | -- |
| 11 | `retry_strategy` | text | N | How to handle retry (manual_fix, auto_retry, discard) | attribute | ENUM |
| 12 | `retry_after` | timestamp with time zone | Y | **MISSING** | -- | -- |
| 13 | `status` | text | N | **MISSING** | -- | -- |
| 14 | `created_at` | timestamp with time zone | N | When the error was recorded | attribute | ISO-8601 |
| 15 | `last_updated_at` | timestamp with time zone | N | **MISSING** | -- | -- |
| 16 | `disposition` | USER-DEFINED | Y | **MISSING** | -- | -- |
| 17 | `retry_count` | integer | Y | **MISSING** | -- | -- |
| 18 | `max_retries` | integer | Y | **MISSING** | -- | -- |
| 19 | `archived_at` | timestamp with time zone | Y | **MISSING** | -- | -- |
| 20 | `parked_at` | timestamp with time zone | Y | **MISSING** | -- | -- |
| 21 | `parked_by` | text | Y | **MISSING** | -- | -- |
| 22 | `park_reason` | text | Y | **MISSING** | -- | -- |
| 23 | `escalation_level` | integer | Y | **MISSING** | -- | -- |
| 24 | `escalated_at` | timestamp with time zone | Y | **MISSING** | -- | -- |
| 25 | `ttl_tier` | USER-DEFINED | Y | **MISSING** | -- | -- |
| 26 | `last_retry_at` | timestamp with time zone | Y | **MISSING** | -- | -- |
| 27 | `next_retry_at` | timestamp with time zone | Y | **MISSING** | -- | -- |
| 28 | `retry_exhausted` | boolean | Y | **MISSING** | -- | -- |

#### `people.people_errors_archive` -- ARCHIVE -- 0 rows

Column registry: **UNDOCUMENTED**

| # | Column | Type | Null | Description | Role | Format |
|---|--------|------|------|-------------|------|--------|
| 1 | `error_id` | uuid | N | **MISSING** | -- | -- |
| 2 | `outreach_id` | uuid | Y | **MISSING** | -- | -- |
| 3 | `person_id` | uuid | Y | **MISSING** | -- | -- |
| 4 | `slot_id` | uuid | Y | **MISSING** | -- | -- |
| 5 | `error_stage` | character varying(50) | Y | **MISSING** | -- | -- |
| 6 | `error_type` | character varying(50) | Y | **MISSING** | -- | -- |
| 7 | `error_code` | character varying(50) | Y | **MISSING** | -- | -- |
| 8 | `error_message` | text | Y | **MISSING** | -- | -- |
| 9 | `raw_payload` | jsonb | Y | **MISSING** | -- | -- |
| 10 | `retry_strategy` | character varying(50) | Y | **MISSING** | -- | -- |
| 11 | `source_hints_used` | jsonb | Y | **MISSING** | -- | -- |
| 12 | `status` | character varying(20) | Y | **MISSING** | -- | -- |
| 13 | `created_at` | timestamp with time zone | Y | **MISSING** | -- | -- |
| 14 | `last_updated_at` | timestamp with time zone | Y | **MISSING** | -- | -- |
| 15 | `disposition` | USER-DEFINED | Y | **MISSING** | -- | -- |
| 16 | `retry_count` | integer | Y | **MISSING** | -- | -- |
| 17 | `max_retries` | integer | Y | **MISSING** | -- | -- |
| 18 | `parked_at` | timestamp with time zone | Y | **MISSING** | -- | -- |
| 19 | `parked_by` | text | Y | **MISSING** | -- | -- |
| 20 | `park_reason` | text | Y | **MISSING** | -- | -- |
| 21 | `escalation_level` | integer | Y | **MISSING** | -- | -- |
| 22 | `escalated_at` | timestamp with time zone | Y | **MISSING** | -- | -- |
| 23 | `ttl_tier` | USER-DEFINED | Y | **MISSING** | -- | -- |
| 24 | `last_retry_at` | timestamp with time zone | Y | **MISSING** | -- | -- |
| 25 | `retry_exhausted` | boolean | Y | **MISSING** | -- | -- |
| 26 | `archived_at` | timestamp with time zone | N | **MISSING** | -- | -- |
| 27 | `archived_by` | text | Y | **MISSING** | -- | -- |
| 28 | `archive_reason` | text | Y | **MISSING** | -- | -- |
| 29 | `final_disposition` | USER-DEFINED | Y | **MISSING** | -- | -- |
| 30 | `retention_expires_at` | timestamp with time zone | Y | **MISSING** | -- | -- |

#### `people.people_invalid` -- ERROR -- 21 rows

Column registry: **UNDOCUMENTED**

| # | Column | Type | Null | Description | Role | Format |
|---|--------|------|------|-------------|------|--------|
| 1 | `id` | bigint | N | **MISSING** | -- | -- |
| 2 | `unique_id` | text | N | **MISSING** | -- | -- |
| 3 | `full_name` | text | Y | **MISSING** | -- | -- |
| 4 | `first_name` | text | Y | **MISSING** | -- | -- |
| 5 | `last_name` | text | Y | **MISSING** | -- | -- |
| 6 | `email` | text | Y | **MISSING** | -- | -- |
| 7 | `phone` | text | Y | **MISSING** | -- | -- |
| 8 | `title` | text | Y | **MISSING** | -- | -- |
| 9 | `company_name` | text | Y | **MISSING** | -- | -- |
| 10 | `company_unique_id` | text | Y | **MISSING** | -- | -- |
| 11 | `linkedin_url` | text | Y | **MISSING** | -- | -- |
| 12 | `city` | text | Y | **MISSING** | -- | -- |
| 13 | `state` | text | Y | **MISSING** | -- | -- |
| 14 | `validation_status` | text | Y | **MISSING** | -- | -- |
| 15 | `reason_code` | text | N | **MISSING** | -- | -- |
| 16 | `validation_errors` | jsonb | N | **MISSING** | -- | -- |
| 17 | `validation_warnings` | jsonb | Y | **MISSING** | -- | -- |
| 18 | `failed_at` | timestamp without time zone | Y | **MISSING** | -- | -- |
| 19 | `reviewed` | boolean | Y | **MISSING** | -- | -- |
| 20 | `batch_id` | text | Y | **MISSING** | -- | -- |
| 21 | `source_table` | text | Y | **MISSING** | -- | -- |
| 22 | `created_at` | timestamp without time zone | Y | **MISSING** | -- | -- |
| 23 | `updated_at` | timestamp without time zone | Y | **MISSING** | -- | -- |
| 24 | `promoted_to` | text | Y | **MISSING** | -- | -- |
| 25 | `promoted_at` | timestamp without time zone | Y | **MISSING** | -- | -- |
| 26 | `enrichment_data` | jsonb | Y | **MISSING** | -- | -- |

#### `people.people_master` -- SUPPORTING FROZEN -- 182,842 rows

Column registry: **7/35 documented**

| # | Column | Type | Null | Description | Role | Format |
|---|--------|------|------|-------------|------|--------|
| 1 | `unique_id` | text | N | Barton person identifier (04.04.02.YY.NNNNNN.NNN format, immutable) | identifier | STRING |
| 2 | `company_unique_id` | text | N | **MISSING** | -- | -- |
| 3 | `company_slot_unique_id` | text | N | **MISSING** | -- | -- |
| 4 | `first_name` | text | N | Person first name from Hunter, Clay, or manual enrichment | attribute | STRING |
| 5 | `last_name` | text | N | Person last name from Hunter, Clay, or manual enrichment | attribute | STRING |
| 6 | `full_name` | text | Y | **MISSING** | -- | -- |
| 7 | `title` | text | Y | **MISSING** | -- | -- |
| 8 | `seniority` | text | Y | **MISSING** | -- | -- |
| 9 | `department` | text | Y | **MISSING** | -- | -- |
| 10 | `email` | text | Y | Person email address | attribute | EMAIL |
| 11 | `work_phone_e164` | text | Y | **MISSING** | -- | -- |
| 12 | `personal_phone_e164` | text | Y | **MISSING** | -- | -- |
| 13 | `linkedin_url` | text | Y | Person LinkedIn profile URL | attribute | STRING |
| 14 | `twitter_url` | text | Y | **MISSING** | -- | -- |
| 15 | `facebook_url` | text | Y | **MISSING** | -- | -- |
| 16 | `bio` | text | Y | **MISSING** | -- | -- |
| 17 | `skills` | ARRAY | Y | **MISSING** | -- | -- |
| 18 | `education` | text | Y | **MISSING** | -- | -- |
| 19 | `certifications` | ARRAY | Y | **MISSING** | -- | -- |
| 20 | `source_system` | text | N | **MISSING** | -- | -- |
| 21 | `source_record_id` | text | Y | **MISSING** | -- | -- |
| 22 | `promoted_from_intake_at` | timestamp with time zone | N | **MISSING** | -- | -- |
| 23 | `promotion_audit_log_id` | integer | Y | **MISSING** | -- | -- |
| 24 | `created_at` | timestamp with time zone | Y | **MISSING** | -- | -- |
| 25 | `updated_at` | timestamp with time zone | Y | **MISSING** | -- | -- |
| 26 | `email_verified` | boolean | Y | Whether email was checked via Million Verifier (TRUE = checked) | attribute | BOOLEAN |
| 27 | `message_key_scheduled` | text | Y | **MISSING** | -- | -- |
| 28 | `email_verification_source` | text | Y | **MISSING** | -- | -- |
| 29 | `email_verified_at` | timestamp with time zone | Y | **MISSING** | -- | -- |
| 30 | `validation_status` | character varying | Y | **MISSING** | -- | -- |
| 31 | `last_verified_at` | timestamp without time zone | N | **MISSING** | -- | -- |
| 32 | `last_enrichment_attempt` | timestamp without time zone | Y | **MISSING** | -- | -- |
| 33 | `is_decision_maker` | boolean | Y | **MISSING** | -- | -- |
| 34 | `outreach_ready` | boolean | Y | Whether email is safe to send outreach (TRUE = VALID verified) | attribute | BOOLEAN |
| 35 | `outreach_ready_at` | timestamp with time zone | Y | **MISSING** | -- | -- |

#### `people.people_master_archive` -- ARCHIVE -- 47,486 rows

Column registry: **UNDOCUMENTED**

| # | Column | Type | Null | Description | Role | Format |
|---|--------|------|------|-------------|------|--------|
| 1 | `archived_at` | timestamp without time zone | N | **MISSING** | -- | -- |
| 2 | `archive_reason` | text | Y | **MISSING** | -- | -- |
| 3 | `unique_id` | text | Y | **MISSING** | -- | -- |
| 4 | `company_unique_id` | text | Y | **MISSING** | -- | -- |
| 5 | `company_slot_unique_id` | text | Y | **MISSING** | -- | -- |
| 6 | `first_name` | text | Y | **MISSING** | -- | -- |
| 7 | `last_name` | text | Y | **MISSING** | -- | -- |
| 8 | `full_name` | text | Y | **MISSING** | -- | -- |
| 9 | `title` | text | Y | **MISSING** | -- | -- |
| 10 | `seniority` | text | Y | **MISSING** | -- | -- |
| 11 | `department` | text | Y | **MISSING** | -- | -- |
| 12 | `email` | text | Y | **MISSING** | -- | -- |
| 13 | `work_phone_e164` | text | Y | **MISSING** | -- | -- |
| 14 | `personal_phone_e164` | text | Y | **MISSING** | -- | -- |
| 15 | `linkedin_url` | text | Y | **MISSING** | -- | -- |
| 16 | `twitter_url` | text | Y | **MISSING** | -- | -- |
| 17 | `facebook_url` | text | Y | **MISSING** | -- | -- |
| 18 | `bio` | text | Y | **MISSING** | -- | -- |
| 19 | `skills` | ARRAY | Y | **MISSING** | -- | -- |
| 20 | `education` | text | Y | **MISSING** | -- | -- |
| 21 | `certifications` | ARRAY | Y | **MISSING** | -- | -- |
| 22 | `source_system` | text | Y | **MISSING** | -- | -- |
| 23 | `source_record_id` | text | Y | **MISSING** | -- | -- |
| 24 | `promoted_from_intake_at` | timestamp without time zone | Y | **MISSING** | -- | -- |
| 25 | `promotion_audit_log_id` | integer | Y | **MISSING** | -- | -- |
| 26 | `created_at` | timestamp without time zone | Y | **MISSING** | -- | -- |
| 27 | `updated_at` | timestamp without time zone | Y | **MISSING** | -- | -- |
| 28 | `email_verified` | boolean | Y | **MISSING** | -- | -- |
| 29 | `message_key_scheduled` | text | Y | **MISSING** | -- | -- |
| 30 | `email_verification_source` | text | Y | **MISSING** | -- | -- |
| 31 | `email_verified_at` | timestamp without time zone | Y | **MISSING** | -- | -- |
| 32 | `validation_status` | character varying | Y | **MISSING** | -- | -- |
| 33 | `last_verified_at` | timestamp without time zone | Y | **MISSING** | -- | -- |
| 34 | `last_enrichment_attempt` | timestamp without time zone | Y | **MISSING** | -- | -- |
| 35 | `is_decision_maker` | boolean | Y | **MISSING** | -- | -- |

#### `people.people_promotion_audit` -- SYSTEM -- 9 rows

Column registry: **UNDOCUMENTED**

| # | Column | Type | Null | Description | Role | Format |
|---|--------|------|------|-------------|------|--------|
| 1 | `audit_id` | integer | N | **MISSING** | -- | -- |
| 2 | `run_id` | text | N | **MISSING** | -- | -- |
| 3 | `resolution_status` | text | N | **MISSING** | -- | -- |
| 4 | `role` | text | Y | **MISSING** | -- | -- |
| 5 | `count` | integer | Y | **MISSING** | -- | -- |
| 6 | `created_at` | timestamp with time zone | Y | **MISSING** | -- | -- |

#### `people.people_resolution_history` -- SYSTEM -- 0 rows

Column registry: **UNDOCUMENTED**

| # | Column | Type | Null | Description | Role | Format |
|---|--------|------|------|-------------|------|--------|
| 1 | `history_id` | uuid | N | **MISSING** | -- | -- |
| 2 | `outreach_id` | uuid | N | **MISSING** | -- | -- |
| 3 | `slot_type` | character varying(20) | N | **MISSING** | -- | -- |
| 4 | `person_identifier` | text | N | **MISSING** | -- | -- |
| 5 | `resolution_outcome` | character varying(30) | N | **MISSING** | -- | -- |
| 6 | `rejection_reason` | text | Y | **MISSING** | -- | -- |
| 7 | `confidence_score` | numeric | Y | **MISSING** | -- | -- |
| 8 | `source` | character varying(50) | Y | **MISSING** | -- | -- |
| 9 | `source_response` | jsonb | Y | **MISSING** | -- | -- |
| 10 | `checked_at` | timestamp with time zone | Y | **MISSING** | -- | -- |
| 11 | `process_id` | uuid | Y | **MISSING** | -- | -- |
| 12 | `correlation_id` | uuid | Y | **MISSING** | -- | -- |
| 13 | `created_at` | timestamp with time zone | Y | **MISSING** | -- | -- |

#### `people.people_resolution_queue` -- STAGING -- 1,206 rows

Column registry: **UNDOCUMENTED**

| # | Column | Type | Null | Description | Role | Format |
|---|--------|------|------|-------------|------|--------|
| 1 | `queue_id` | integer | N | **MISSING** | -- | -- |
| 2 | `company_unique_id` | text | N | **MISSING** | -- | -- |
| 3 | `company_slot_unique_id` | text | N | **MISSING** | -- | -- |
| 4 | `slot_type` | text | Y | **MISSING** | -- | -- |
| 5 | `existing_email` | text | Y | **MISSING** | -- | -- |
| 6 | `issue_type` | text | N | **MISSING** | -- | -- |
| 7 | `priority` | integer | Y | **MISSING** | -- | -- |
| 8 | `status` | text | Y | **MISSING** | -- | -- |
| 9 | `resolved_contact_id` | text | Y | **MISSING** | -- | -- |
| 10 | `created_at` | timestamp without time zone | Y | **MISSING** | -- | -- |
| 11 | `last_touched_at` | timestamp without time zone | Y | **MISSING** | -- | -- |
| 12 | `resolved_at` | timestamp without time zone | Y | **MISSING** | -- | -- |
| 13 | `touched_by` | text | Y | **MISSING** | -- | -- |
| 14 | `assigned_to` | text | Y | **MISSING** | -- | -- |
| 15 | `notes` | text | Y | **MISSING** | -- | -- |
| 16 | `error_details` | jsonb | Y | **MISSING** | -- | -- |
| 17 | `attempt_count` | integer | Y | **MISSING** | -- | -- |

#### `people.people_sidecar` -- SUPPORTING -- 0 rows

Column registry: **UNDOCUMENTED**

| # | Column | Type | Null | Description | Role | Format |
|---|--------|------|------|-------------|------|--------|
| 1 | `person_unique_id` | character varying(50) | N | **MISSING** | -- | -- |
| 2 | `clay_insight_summary` | text | Y | **MISSING** | -- | -- |
| 3 | `clay_segments` | ARRAY | Y | **MISSING** | -- | -- |
| 4 | `social_profiles` | jsonb | Y | **MISSING** | -- | -- |
| 5 | `enrichment_payload` | jsonb | Y | **MISSING** | -- | -- |
| 6 | `last_enriched_at` | timestamp without time zone | Y | **MISSING** | -- | -- |
| 7 | `enrichment_source` | text | Y | **MISSING** | -- | -- |
| 8 | `confidence_score` | numeric | Y | **MISSING** | -- | -- |
| 9 | `created_at` | timestamp without time zone | Y | **MISSING** | -- | -- |
| 10 | `updated_at` | timestamp without time zone | Y | **MISSING** | -- | -- |

#### `people.person_movement_history` -- SYSTEM -- 0 rows

Column registry: **UNDOCUMENTED**

| # | Column | Type | Null | Description | Role | Format |
|---|--------|------|------|-------------|------|--------|
| 1 | `id` | integer | N | **MISSING** | -- | -- |
| 2 | `person_unique_id` | text | N | **MISSING** | -- | -- |
| 3 | `linkedin_url` | text | Y | **MISSING** | -- | -- |
| 4 | `company_from_id` | text | N | **MISSING** | -- | -- |
| 5 | `company_to_id` | text | Y | **MISSING** | -- | -- |
| 6 | `title_from` | text | N | **MISSING** | -- | -- |
| 7 | `title_to` | text | Y | **MISSING** | -- | -- |
| 8 | `movement_type` | text | N | **MISSING** | -- | -- |
| 9 | `detected_at` | timestamp without time zone | N | **MISSING** | -- | -- |
| 10 | `raw_payload` | jsonb | Y | **MISSING** | -- | -- |
| 11 | `created_at` | timestamp without time zone | Y | **MISSING** | -- | -- |

#### `people.person_scores` -- SUPPORTING -- 0 rows

Column registry: **UNDOCUMENTED**

| # | Column | Type | Null | Description | Role | Format |
|---|--------|------|------|-------------|------|--------|
| 1 | `id` | integer | N | **MISSING** | -- | -- |
| 2 | `person_unique_id` | text | N | **MISSING** | -- | -- |
| 3 | `bit_score` | integer | Y | **MISSING** | -- | -- |
| 4 | `confidence_score` | integer | Y | **MISSING** | -- | -- |
| 5 | `calculated_at` | timestamp without time zone | N | **MISSING** | -- | -- |
| 6 | `score_factors` | jsonb | Y | **MISSING** | -- | -- |
| 7 | `created_at` | timestamp without time zone | Y | **MISSING** | -- | -- |
| 8 | `updated_at` | timestamp without time zone | Y | **MISSING** | -- | -- |

#### `people.pressure_signals` -- MV -- 0 rows

Column registry: **UNDOCUMENTED**

| # | Column | Type | Null | Description | Role | Format |
|---|--------|------|------|-------------|------|--------|
| 1 | `signal_id` | uuid | N | **MISSING** | -- | -- |
| 2 | `company_unique_id` | text | N | **MISSING** | -- | -- |
| 3 | `signal_type` | character varying(50) | N | **MISSING** | -- | -- |
| 4 | `pressure_domain` | USER-DEFINED | N | **MISSING** | -- | -- |
| 5 | `pressure_class` | USER-DEFINED | Y | **MISSING** | -- | -- |
| 6 | `signal_value` | jsonb | N | **MISSING** | -- | -- |
| 7 | `magnitude` | integer | N | **MISSING** | -- | -- |
| 8 | `detected_at` | timestamp with time zone | N | **MISSING** | -- | -- |
| 9 | `expires_at` | timestamp with time zone | N | **MISSING** | -- | -- |
| 10 | `correlation_id` | uuid | Y | **MISSING** | -- | -- |
| 11 | `source_record_id` | text | Y | **MISSING** | -- | -- |
| 12 | `created_at` | timestamp with time zone | N | **MISSING** | -- | -- |

#### `people.slot_assignment_history` -- SYSTEM -- 1,370 rows

Column registry: **UNDOCUMENTED**

| # | Column | Type | Null | Description | Role | Format |
|---|--------|------|------|-------------|------|--------|
| 1 | `history_id` | bigint | N | **MISSING** | -- | -- |
| 2 | `event_type` | text | N | **MISSING** | -- | -- |
| 3 | `company_slot_unique_id` | text | N | **MISSING** | -- | -- |
| 4 | `company_unique_id` | text | N | **MISSING** | -- | -- |
| 5 | `slot_type` | text | N | **MISSING** | -- | -- |
| 6 | `person_unique_id` | text | Y | **MISSING** | -- | -- |
| 7 | `confidence_score` | numeric | Y | **MISSING** | -- | -- |
| 8 | `displaced_by_person_id` | text | Y | **MISSING** | -- | -- |
| 9 | `displacement_reason` | text | Y | **MISSING** | -- | -- |
| 10 | `source_system` | text | N | **MISSING** | -- | -- |
| 11 | `event_ts` | timestamp with time zone | N | **MISSING** | -- | -- |
| 12 | `created_at` | timestamp with time zone | N | **MISSING** | -- | -- |
| 13 | `original_filled_at` | timestamp with time zone | Y | **MISSING** | -- | -- |
| 14 | `tenure_days` | integer | Y | **MISSING** | -- | -- |
| 15 | `event_metadata` | jsonb | N | **MISSING** | -- | -- |

#### `people.slot_ingress_control` -- REGISTRY -- 1 rows

Column registry: **UNDOCUMENTED**

| # | Column | Type | Null | Description | Role | Format |
|---|--------|------|------|-------------|------|--------|
| 1 | `switch_id` | uuid | N | **MISSING** | -- | -- |
| 2 | `switch_name` | character varying(50) | N | **MISSING** | -- | -- |
| 3 | `is_enabled` | boolean | N | **MISSING** | -- | -- |
| 4 | `description` | text | Y | **MISSING** | -- | -- |
| 5 | `enabled_by` | character varying(100) | Y | **MISSING** | -- | -- |
| 6 | `enabled_at` | timestamp with time zone | Y | **MISSING** | -- | -- |
| 7 | `disabled_by` | character varying(100) | Y | **MISSING** | -- | -- |
| 8 | `disabled_at` | timestamp with time zone | Y | **MISSING** | -- | -- |
| 9 | `created_at` | timestamp with time zone | N | **MISSING** | -- | -- |

#### `people.slot_orphan_snapshot_r0_002` -- ARCHIVE -- 1,053 rows

Column registry: **UNDOCUMENTED**

| # | Column | Type | Null | Description | Role | Format |
|---|--------|------|------|-------------|------|--------|
| 1 | `snapshot_id` | integer | N | **MISSING** | -- | -- |
| 2 | `company_slot_unique_id` | text | N | **MISSING** | -- | -- |
| 3 | `company_unique_id` | text | N | **MISSING** | -- | -- |
| 4 | `slot_type` | text | N | **MISSING** | -- | -- |
| 5 | `original_outreach_id` | uuid | Y | **MISSING** | -- | -- |
| 6 | `derived_outreach_id` | uuid | Y | **MISSING** | -- | -- |
| 7 | `derivation_status` | text | Y | **MISSING** | -- | -- |
| 8 | `snapshot_at` | timestamp with time zone | Y | **MISSING** | -- | -- |

#### `people.slot_quarantine_r0_002` -- ARCHIVE -- 75 rows

Column registry: **UNDOCUMENTED**

| # | Column | Type | Null | Description | Role | Format |
|---|--------|------|------|-------------|------|--------|
| 1 | `quarantine_id` | integer | N | **MISSING** | -- | -- |
| 2 | `company_slot_unique_id` | text | N | **MISSING** | -- | -- |
| 3 | `company_unique_id` | text | N | **MISSING** | -- | -- |
| 4 | `slot_type` | text | N | **MISSING** | -- | -- |
| 5 | `quarantine_reason` | text | N | **MISSING** | -- | -- |
| 6 | `quarantined_at` | timestamp with time zone | Y | **MISSING** | -- | -- |

#### `people.title_slot_mapping` -- REGISTRY -- 43 rows

Column registry: **UNDOCUMENTED**

| # | Column | Type | Null | Description | Role | Format |
|---|--------|------|------|-------------|------|--------|
| 1 | `id` | integer | N | **MISSING** | -- | -- |
| 2 | `title_pattern` | character varying(100) | N | **MISSING** | -- | -- |
| 3 | `slot_type` | character varying(20) | N | **MISSING** | -- | -- |
| 4 | `priority` | integer | Y | **MISSING** | -- | -- |
| 5 | `created_at` | timestamp without time zone | Y | **MISSING** | -- | -- |

### `dol` -- DOL Filings -- Form 5500, Schedule A/C/D/G/H/I data from EFAST2

**Tables**: 31 | **Total rows**: 11,124,376

| Table | Leaf Type | Frozen | Rows | Columns | Documented |
|-------|-----------|--------|------|---------|------------|
| `column_metadata` | REGISTRY |  | 1,081 | 14 | 0 |
| `ein_urls` | CANONICAL |  | 127,909 | 9 | 0 |
| `form_5500` | CANONICAL |  | 432,582 | 147 | 0 |
| `form_5500_icp_filtered` | MV |  | 24,892 | 7 | 0 |
| `form_5500_sf` | CANONICAL |  | 1,535,727 | 196 | 0 |
| `form_5500_sf_part7` | UNREGISTERED |  | 10,613 | 8 | 0 |
| `pressure_signals` | MV |  | 0 | 12 | 0 |
| `renewal_calendar` | CANONICAL |  | 0 | 13 | 0 |
| `schedule_a` | CANONICAL |  | 625,520 | 98 | 0 |
| `schedule_a_part1` | UNREGISTERED |  | 380,509 | 22 | 0 |
| `schedule_c` | UNREGISTERED |  | 241,556 | 5 | 0 |
| `schedule_c_part1_item1` | UNREGISTERED |  | 396,838 | 18 | 0 |
| `schedule_c_part1_item2` | UNREGISTERED |  | 754,802 | 25 | 0 |
| `schedule_c_part1_item2_codes` | UNREGISTERED |  | 1,848,202 | 7 | 0 |
| `schedule_c_part1_item3` | UNREGISTERED |  | 383,338 | 22 | 0 |
| `schedule_c_part1_item3_codes` | UNREGISTERED |  | 707,007 | 7 | 0 |
| `schedule_c_part2` | UNREGISTERED |  | 4,593 | 20 | 0 |
| `schedule_c_part2_codes` | UNREGISTERED |  | 2,352 | 7 | 0 |
| `schedule_c_part3` | UNREGISTERED |  | 15,514 | 22 | 0 |
| `schedule_d` | UNREGISTERED |  | 121,813 | 8 | 0 |
| `schedule_d_part1` | UNREGISTERED |  | 808,051 | 11 | 0 |
| `schedule_d_part2` | UNREGISTERED |  | 2,392,252 | 9 | 0 |
| `schedule_dcg` | UNREGISTERED |  | 235 | 121 | 0 |
| `schedule_g` | UNREGISTERED |  | 568 | 8 | 0 |
| `schedule_g_part1` | UNREGISTERED |  | 784 | 25 | 0 |
| `schedule_g_part2` | UNREGISTERED |  | 97 | 15 | 0 |
| `schedule_g_part3` | UNREGISTERED |  | 469 | 15 | 0 |
| `schedule_h` | UNREGISTERED |  | 169,276 | 169 | 0 |
| `schedule_h_part1` | UNREGISTERED |  | 20,359 | 8 | 0 |
| `schedule_i` | UNREGISTERED |  | 116,493 | 80 | 0 |
| `schedule_i_part1` | UNREGISTERED |  | 944 | 8 | 0 |

#### `dol.column_metadata` -- REGISTRY -- 1,081 rows

Column registry: **UNDOCUMENTED**

| # | Column | Type | Null | Description | Role | Format |
|---|--------|------|------|-------------|------|--------|
| 1 | `id` | integer | N | **MISSING** | -- | -- |
| 2 | `table_name` | character varying(50) | N | **MISSING** | -- | -- |
| 3 | `column_name` | character varying(100) | N | **MISSING** | -- | -- |
| 4 | `column_id` | character varying(100) | N | **MISSING** | -- | -- |
| 5 | `description` | text | N | **MISSING** | -- | -- |
| 6 | `category` | character varying(50) | Y | **MISSING** | -- | -- |
| 7 | `data_type` | character varying(50) | N | **MISSING** | -- | -- |
| 8 | `format_pattern` | character varying(100) | Y | **MISSING** | -- | -- |
| 9 | `max_length` | integer | Y | **MISSING** | -- | -- |
| 10 | `search_keywords` | ARRAY | Y | **MISSING** | -- | -- |
| 11 | `is_pii` | boolean | Y | **MISSING** | -- | -- |
| 12 | `is_searchable` | boolean | Y | **MISSING** | -- | -- |
| 13 | `example_values` | ARRAY | Y | **MISSING** | -- | -- |
| 14 | `created_at` | timestamp without time zone | Y | **MISSING** | -- | -- |

#### `dol.ein_urls` -- CANONICAL -- 127,909 rows

Column registry: **UNDOCUMENTED**

| # | Column | Type | Null | Description | Role | Format |
|---|--------|------|------|-------------|------|--------|
| 1 | `ein` | character varying(9) | N | **MISSING** | -- | -- |
| 2 | `company_name` | text | N | **MISSING** | -- | -- |
| 3 | `city` | text | Y | **MISSING** | -- | -- |
| 4 | `state` | character varying(2) | Y | **MISSING** | -- | -- |
| 5 | `domain` | text | Y | **MISSING** | -- | -- |
| 6 | `url` | text | Y | **MISSING** | -- | -- |
| 7 | `discovered_at` | timestamp without time zone | Y | **MISSING** | -- | -- |
| 8 | `discovery_method` | text | Y | **MISSING** | -- | -- |
| 9 | `normalized_domain` | text | Y | **MISSING** | -- | -- |

#### `dol.form_5500` -- CANONICAL -- 432,582 rows

Column registry: **UNDOCUMENTED**

| # | Column | Type | Null | Description | Role | Format |
|---|--------|------|------|-------------|------|--------|
| 1 | `filing_id` | uuid | N | **MISSING** | -- | -- |
| 2 | `ack_id` | character varying(255) | N | **MISSING** | -- | -- |
| 3 | `company_unique_id` | text | Y | **MISSING** | -- | -- |
| 4 | `sponsor_dfe_ein` | character varying(20) | N | **MISSING** | -- | -- |
| 5 | `sponsor_dfe_name` | character varying(500) | N | **MISSING** | -- | -- |
| 6 | `spons_dfe_dba_name` | character varying(500) | Y | **MISSING** | -- | -- |
| 7 | `plan_name` | character varying(500) | Y | **MISSING** | -- | -- |
| 8 | `plan_number` | character varying(20) | Y | **MISSING** | -- | -- |
| 9 | `plan_eff_date` | character varying(20) | Y | **MISSING** | -- | -- |
| 10 | `spons_dfe_mail_us_city` | character varying(100) | Y | **MISSING** | -- | -- |
| 11 | `spons_dfe_mail_us_state` | character varying(10) | Y | **MISSING** | -- | -- |
| 12 | `spons_dfe_mail_us_zip` | character varying(20) | Y | **MISSING** | -- | -- |
| 13 | `tot_active_partcp_cnt` | integer | Y | **MISSING** | -- | -- |
| 14 | `tot_partcp_boy_cnt` | integer | Y | **MISSING** | -- | -- |
| 15 | `sch_a_attached_ind` | character varying(5) | Y | **MISSING** | -- | -- |
| 16 | `num_sch_a_attached_cnt` | integer | Y | **MISSING** | -- | -- |
| 17 | `admin_name` | character varying(255) | Y | **MISSING** | -- | -- |
| 18 | `admin_ein` | character varying(20) | Y | **MISSING** | -- | -- |
| 19 | `form_plan_year_begin_date` | character varying(20) | Y | **MISSING** | -- | -- |
| 20 | `form_year` | character varying(10) | Y | **MISSING** | -- | -- |
| 21 | `filing_status` | character varying(50) | Y | **MISSING** | -- | -- |
| 22 | `date_received` | character varying(30) | Y | **MISSING** | -- | -- |
| 23 | `created_at` | timestamp with time zone | N | **MISSING** | -- | -- |
| 24 | `updated_at` | timestamp with time zone | N | **MISSING** | -- | -- |
| 25 | `form_tax_prd` | character varying(255) | Y | **MISSING** | -- | -- |
| 26 | `type_plan_entity_cd` | character varying(255) | Y | **MISSING** | -- | -- |
| 27 | `type_dfe_plan_entity_cd` | character varying(255) | Y | **MISSING** | -- | -- |
| 28 | `initial_filing_ind` | character varying(5) | Y | **MISSING** | -- | -- |
| 29 | `amended_ind` | character varying(5) | Y | **MISSING** | -- | -- |
| 30 | `final_filing_ind` | character varying(5) | Y | **MISSING** | -- | -- |
| 31 | `short_plan_yr_ind` | character varying(5) | Y | **MISSING** | -- | -- |
| 32 | `collective_bargain_ind` | character varying(5) | Y | **MISSING** | -- | -- |
| 33 | `f5558_application_filed_ind` | character varying(5) | Y | **MISSING** | -- | -- |
| 34 | `ext_automatic_ind` | character varying(5) | Y | **MISSING** | -- | -- |
| 35 | `dfvc_program_ind` | character varying(5) | Y | **MISSING** | -- | -- |
| 36 | `ext_special_ind` | character varying(5) | Y | **MISSING** | -- | -- |
| 37 | `ext_special_text` | text | Y | **MISSING** | -- | -- |
| 38 | `spons_dfe_pn` | character varying(255) | Y | **MISSING** | -- | -- |
| 39 | `spons_dfe_care_of_name` | character varying(255) | Y | **MISSING** | -- | -- |
| 40 | `spons_dfe_mail_us_address1` | character varying(255) | Y | **MISSING** | -- | -- |
| 41 | `spons_dfe_mail_us_address2` | character varying(255) | Y | **MISSING** | -- | -- |
| 42 | `spons_dfe_mail_foreign_addr1` | character varying(255) | Y | **MISSING** | -- | -- |
| 43 | `spons_dfe_mail_foreign_addr2` | character varying(255) | Y | **MISSING** | -- | -- |
| 44 | `spons_dfe_mail_foreign_city` | character varying(100) | Y | **MISSING** | -- | -- |
| 45 | `spons_dfe_mail_forgn_prov_st` | character varying(255) | Y | **MISSING** | -- | -- |
| 46 | `spons_dfe_mail_foreign_cntry` | character varying(100) | Y | **MISSING** | -- | -- |
| 47 | `spons_dfe_mail_forgn_postal_cd` | character varying(255) | Y | **MISSING** | -- | -- |
| 48 | `spons_dfe_loc_us_address1` | character varying(255) | Y | **MISSING** | -- | -- |
| 49 | `spons_dfe_loc_us_address2` | character varying(255) | Y | **MISSING** | -- | -- |
| 50 | `spons_dfe_loc_us_city` | character varying(100) | Y | **MISSING** | -- | -- |
| 51 | `spons_dfe_loc_us_state` | character varying(10) | Y | **MISSING** | -- | -- |
| 52 | `spons_dfe_loc_us_zip` | character varying(20) | Y | **MISSING** | -- | -- |
| 53 | `spons_dfe_loc_foreign_address1` | character varying(255) | Y | **MISSING** | -- | -- |
| 54 | `spons_dfe_loc_foreign_address2` | character varying(255) | Y | **MISSING** | -- | -- |
| 55 | `spons_dfe_loc_foreign_city` | character varying(100) | Y | **MISSING** | -- | -- |
| 56 | `spons_dfe_loc_forgn_prov_st` | character varying(255) | Y | **MISSING** | -- | -- |
| 57 | `spons_dfe_loc_foreign_cntry` | character varying(100) | Y | **MISSING** | -- | -- |
| 58 | `spons_dfe_loc_forgn_postal_cd` | character varying(255) | Y | **MISSING** | -- | -- |
| 59 | `spons_dfe_ein` | character varying(20) | Y | **MISSING** | -- | -- |
| 60 | `spons_dfe_phone_num` | character varying(30) | Y | **MISSING** | -- | -- |
| 61 | `business_code` | character varying(50) | Y | **MISSING** | -- | -- |
| 62 | `admin_care_of_name` | character varying(255) | Y | **MISSING** | -- | -- |
| 63 | `admin_us_address1` | character varying(255) | Y | **MISSING** | -- | -- |
| 64 | `admin_us_address2` | character varying(255) | Y | **MISSING** | -- | -- |
| 65 | `admin_us_city` | character varying(100) | Y | **MISSING** | -- | -- |
| 66 | `admin_us_state` | character varying(10) | Y | **MISSING** | -- | -- |
| 67 | `admin_us_zip` | character varying(20) | Y | **MISSING** | -- | -- |
| 68 | `admin_foreign_address1` | character varying(255) | Y | **MISSING** | -- | -- |
| 69 | `admin_foreign_address2` | character varying(255) | Y | **MISSING** | -- | -- |
| 70 | `admin_foreign_city` | character varying(100) | Y | **MISSING** | -- | -- |
| 71 | `admin_foreign_prov_state` | character varying(255) | Y | **MISSING** | -- | -- |
| 72 | `admin_foreign_cntry` | character varying(100) | Y | **MISSING** | -- | -- |
| 73 | `admin_foreign_postal_cd` | character varying(255) | Y | **MISSING** | -- | -- |
| 74 | `admin_phone_num` | character varying(30) | Y | **MISSING** | -- | -- |
| 75 | `last_rpt_spons_name` | character varying(255) | Y | **MISSING** | -- | -- |
| 76 | `last_rpt_spons_ein` | character varying(20) | Y | **MISSING** | -- | -- |
| 77 | `last_rpt_plan_num` | character varying(255) | Y | **MISSING** | -- | -- |
| 78 | `admin_signed_date` | character varying(30) | Y | **MISSING** | -- | -- |
| 79 | `admin_signed_name` | character varying(255) | Y | **MISSING** | -- | -- |
| 80 | `spons_signed_date` | character varying(30) | Y | **MISSING** | -- | -- |
| 81 | `spons_signed_name` | character varying(255) | Y | **MISSING** | -- | -- |
| 82 | `dfe_signed_date` | character varying(30) | Y | **MISSING** | -- | -- |
| 83 | `dfe_signed_name` | character varying(255) | Y | **MISSING** | -- | -- |
| 84 | `rtd_sep_partcp_rcvg_cnt` | numeric | Y | **MISSING** | -- | -- |
| 85 | `rtd_sep_partcp_fut_cnt` | numeric | Y | **MISSING** | -- | -- |
| 86 | `subtl_act_rtd_sep_cnt` | numeric | Y | **MISSING** | -- | -- |
| 87 | `benef_rcvg_bnft_cnt` | numeric | Y | **MISSING** | -- | -- |
| 88 | `tot_act_rtd_sep_benef_cnt` | numeric | Y | **MISSING** | -- | -- |
| 89 | `partcp_account_bal_cnt` | numeric | Y | **MISSING** | -- | -- |
| 90 | `sep_partcp_partl_vstd_cnt` | numeric | Y | **MISSING** | -- | -- |
| 91 | `contrib_emplrs_cnt` | numeric | Y | **MISSING** | -- | -- |
| 92 | `type_pension_bnft_code` | character varying(50) | Y | **MISSING** | -- | -- |
| 93 | `type_welfare_bnft_code` | character varying(50) | Y | **MISSING** | -- | -- |
| 94 | `funding_insurance_ind` | character varying(5) | Y | **MISSING** | -- | -- |
| 95 | `funding_sec412_ind` | character varying(5) | Y | **MISSING** | -- | -- |
| 96 | `funding_trust_ind` | character varying(5) | Y | **MISSING** | -- | -- |
| 97 | `funding_gen_asset_ind` | character varying(5) | Y | **MISSING** | -- | -- |
| 98 | `benefit_insurance_ind` | character varying(5) | Y | **MISSING** | -- | -- |
| 99 | `benefit_sec412_ind` | character varying(5) | Y | **MISSING** | -- | -- |
| 100 | `benefit_trust_ind` | character varying(5) | Y | **MISSING** | -- | -- |
| 101 | `benefit_gen_asset_ind` | character varying(5) | Y | **MISSING** | -- | -- |
| 102 | `sch_r_attached_ind` | character varying(5) | Y | **MISSING** | -- | -- |
| 103 | `sch_mb_attached_ind` | character varying(5) | Y | **MISSING** | -- | -- |
| 104 | `sch_sb_attached_ind` | character varying(5) | Y | **MISSING** | -- | -- |
| 105 | `sch_h_attached_ind` | character varying(5) | Y | **MISSING** | -- | -- |
| 106 | `sch_i_attached_ind` | character varying(5) | Y | **MISSING** | -- | -- |
| 107 | `sch_c_attached_ind` | character varying(5) | Y | **MISSING** | -- | -- |
| 108 | `sch_d_attached_ind` | character varying(5) | Y | **MISSING** | -- | -- |
| 109 | `sch_g_attached_ind` | character varying(5) | Y | **MISSING** | -- | -- |
| 110 | `valid_admin_signature` | character varying(255) | Y | **MISSING** | -- | -- |
| 111 | `valid_dfe_signature` | character varying(255) | Y | **MISSING** | -- | -- |
| 112 | `valid_sponsor_signature` | character varying(255) | Y | **MISSING** | -- | -- |
| 113 | `admin_phone_num_foreign` | character varying(255) | Y | **MISSING** | -- | -- |
| 114 | `spons_dfe_phone_num_foreign` | character varying(255) | Y | **MISSING** | -- | -- |
| 115 | `admin_name_same_spon_ind` | character varying(5) | Y | **MISSING** | -- | -- |
| 116 | `admin_address_same_spon_ind` | character varying(5) | Y | **MISSING** | -- | -- |
| 117 | `preparer_name` | character varying(255) | Y | **MISSING** | -- | -- |
| 118 | `preparer_firm_name` | character varying(255) | Y | **MISSING** | -- | -- |
| 119 | `preparer_us_address1` | character varying(255) | Y | **MISSING** | -- | -- |
| 120 | `preparer_us_address2` | character varying(255) | Y | **MISSING** | -- | -- |
| 121 | `preparer_us_city` | character varying(100) | Y | **MISSING** | -- | -- |
| 122 | `preparer_us_state` | character varying(10) | Y | **MISSING** | -- | -- |
| 123 | `preparer_us_zip` | character varying(20) | Y | **MISSING** | -- | -- |
| 124 | `preparer_foreign_address1` | character varying(255) | Y | **MISSING** | -- | -- |
| 125 | `preparer_foreign_address2` | character varying(255) | Y | **MISSING** | -- | -- |
| 126 | `preparer_foreign_city` | character varying(100) | Y | **MISSING** | -- | -- |
| 127 | `preparer_foreign_prov_state` | character varying(255) | Y | **MISSING** | -- | -- |
| 128 | `preparer_foreign_cntry` | character varying(100) | Y | **MISSING** | -- | -- |
| 129 | `preparer_foreign_postal_cd` | character varying(255) | Y | **MISSING** | -- | -- |
| 130 | `preparer_phone_num` | character varying(30) | Y | **MISSING** | -- | -- |
| 131 | `preparer_phone_num_foreign` | character varying(255) | Y | **MISSING** | -- | -- |
| 132 | `tot_act_partcp_boy_cnt` | numeric | Y | **MISSING** | -- | -- |
| 133 | `subj_m1_filing_req_ind` | character varying(5) | Y | **MISSING** | -- | -- |
| 134 | `compliance_m1_filing_req_ind` | character varying(5) | Y | **MISSING** | -- | -- |
| 135 | `m1_receipt_confirmation_code` | character varying(50) | Y | **MISSING** | -- | -- |
| 136 | `admin_manual_signed_date` | character varying(30) | Y | **MISSING** | -- | -- |
| 137 | `admin_manual_signed_name` | character varying(255) | Y | **MISSING** | -- | -- |
| 138 | `last_rpt_plan_name` | character varying(255) | Y | **MISSING** | -- | -- |
| 139 | `spons_manual_signed_date` | character varying(30) | Y | **MISSING** | -- | -- |
| 140 | `spons_manual_signed_name` | character varying(255) | Y | **MISSING** | -- | -- |
| 141 | `dfe_manual_signed_date` | character varying(30) | Y | **MISSING** | -- | -- |
| 142 | `dfe_manual_signed_name` | character varying(255) | Y | **MISSING** | -- | -- |
| 143 | `adopted_plan_perm_sec_act` | character varying(255) | Y | **MISSING** | -- | -- |
| 144 | `partcp_account_bal_cnt_boy` | numeric | Y | **MISSING** | -- | -- |
| 145 | `sch_dcg_attached_ind` | character varying(5) | Y | **MISSING** | -- | -- |
| 146 | `num_sch_dcg_attached_cnt` | numeric | Y | **MISSING** | -- | -- |
| 147 | `sch_mep_attached_ind` | character varying(5) | Y | **MISSING** | -- | -- |

#### `dol.form_5500_icp_filtered` -- MV -- 24,892 rows

Column registry: **UNDOCUMENTED**

| # | Column | Type | Null | Description | Role | Format |
|---|--------|------|------|-------------|------|--------|
| 1 | `sponsor_dfe_ein` | character varying(20) | Y | **MISSING** | -- | -- |
| 2 | `sponsor_dfe_name` | character varying(500) | Y | **MISSING** | -- | -- |
| 3 | `spons_dfe_mail_us_state` | character varying(10) | Y | **MISSING** | -- | -- |
| 4 | `spons_dfe_mail_us_city` | character varying(100) | Y | **MISSING** | -- | -- |
| 5 | `tot_active_partcp_cnt` | integer | Y | **MISSING** | -- | -- |
| 6 | `normalized_name` | text | Y | **MISSING** | -- | -- |
| 7 | `filter_id` | integer | N | **MISSING** | -- | -- |

#### `dol.form_5500_sf` -- CANONICAL -- 1,535,727 rows

Column registry: **UNDOCUMENTED**

| # | Column | Type | Null | Description | Role | Format |
|---|--------|------|------|-------------|------|--------|
| 1 | `filing_id` | uuid | N | **MISSING** | -- | -- |
| 2 | `company_unique_id` | text | Y | **MISSING** | -- | -- |
| 3 | `ack_id` | character varying(255) | Y | **MISSING** | -- | -- |
| 4 | `sf_plan_year_begin_date` | character varying(255) | Y | **MISSING** | -- | -- |
| 5 | `sf_tax_prd` | character varying(255) | Y | **MISSING** | -- | -- |
| 6 | `sf_plan_entity_cd` | character varying(255) | Y | **MISSING** | -- | -- |
| 7 | `sf_initial_filing_ind` | character varying(5) | Y | **MISSING** | -- | -- |
| 8 | `sf_amended_ind` | character varying(5) | Y | **MISSING** | -- | -- |
| 9 | `sf_final_filing_ind` | character varying(5) | Y | **MISSING** | -- | -- |
| 10 | `sf_short_plan_yr_ind` | character varying(5) | Y | **MISSING** | -- | -- |
| 11 | `sf_5558_application_filed_ind` | character varying(5) | Y | **MISSING** | -- | -- |
| 12 | `sf_ext_automatic_ind` | character varying(5) | Y | **MISSING** | -- | -- |
| 13 | `sf_dfvc_program_ind` | character varying(5) | Y | **MISSING** | -- | -- |
| 14 | `sf_ext_special_ind` | character varying(5) | Y | **MISSING** | -- | -- |
| 15 | `sf_ext_special_text` | text | Y | **MISSING** | -- | -- |
| 16 | `sf_plan_name` | character varying(255) | Y | **MISSING** | -- | -- |
| 17 | `sf_plan_num` | character varying(255) | Y | **MISSING** | -- | -- |
| 18 | `sf_plan_eff_date` | character varying(255) | Y | **MISSING** | -- | -- |
| 19 | `sf_sponsor_name` | character varying(255) | Y | **MISSING** | -- | -- |
| 20 | `sf_sponsor_dfe_dba_name` | character varying(255) | Y | **MISSING** | -- | -- |
| 21 | `sf_spons_us_address1` | character varying(255) | Y | **MISSING** | -- | -- |
| 22 | `sf_spons_us_address2` | character varying(255) | Y | **MISSING** | -- | -- |
| 23 | `sf_spons_us_city` | character varying(255) | Y | **MISSING** | -- | -- |
| 24 | `sf_spons_us_state` | character varying(255) | Y | **MISSING** | -- | -- |
| 25 | `sf_spons_us_zip` | character varying(255) | Y | **MISSING** | -- | -- |
| 26 | `sf_spons_foreign_address1` | character varying(255) | Y | **MISSING** | -- | -- |
| 27 | `sf_spons_foreign_address2` | character varying(255) | Y | **MISSING** | -- | -- |
| 28 | `sf_spons_foreign_city` | character varying(255) | Y | **MISSING** | -- | -- |
| 29 | `sf_spons_foreign_prov_state` | character varying(255) | Y | **MISSING** | -- | -- |
| 30 | `sf_spons_foreign_cntry` | character varying(255) | Y | **MISSING** | -- | -- |
| 31 | `sf_spons_foreign_postal_cd` | character varying(255) | Y | **MISSING** | -- | -- |
| 32 | `sf_spons_ein` | character varying(255) | Y | **MISSING** | -- | -- |
| 33 | `sf_spons_phone_num` | character varying(255) | Y | **MISSING** | -- | -- |
| 34 | `sf_business_code` | character varying(255) | Y | **MISSING** | -- | -- |
| 35 | `sf_admin_name` | character varying(255) | Y | **MISSING** | -- | -- |
| 36 | `sf_admin_care_of_name` | character varying(255) | Y | **MISSING** | -- | -- |
| 37 | `sf_admin_us_address1` | character varying(255) | Y | **MISSING** | -- | -- |
| 38 | `sf_admin_us_address2` | character varying(255) | Y | **MISSING** | -- | -- |
| 39 | `sf_admin_us_city` | character varying(255) | Y | **MISSING** | -- | -- |
| 40 | `sf_admin_us_state` | character varying(255) | Y | **MISSING** | -- | -- |
| 41 | `sf_admin_us_zip` | character varying(255) | Y | **MISSING** | -- | -- |
| 42 | `sf_admin_foreign_address1` | character varying(255) | Y | **MISSING** | -- | -- |
| 43 | `sf_admin_foreign_address2` | character varying(255) | Y | **MISSING** | -- | -- |
| 44 | `sf_admin_foreign_city` | character varying(255) | Y | **MISSING** | -- | -- |
| 45 | `sf_admin_foreign_prov_state` | character varying(255) | Y | **MISSING** | -- | -- |
| 46 | `sf_admin_foreign_cntry` | character varying(255) | Y | **MISSING** | -- | -- |
| 47 | `sf_admin_foreign_postal_cd` | character varying(255) | Y | **MISSING** | -- | -- |
| 48 | `sf_admin_ein` | character varying(255) | Y | **MISSING** | -- | -- |
| 49 | `sf_admin_phone_num` | character varying(255) | Y | **MISSING** | -- | -- |
| 50 | `sf_last_rpt_spons_name` | character varying(255) | Y | **MISSING** | -- | -- |
| 51 | `sf_last_rpt_spons_ein` | character varying(255) | Y | **MISSING** | -- | -- |
| 52 | `sf_last_rpt_plan_num` | character varying(255) | Y | **MISSING** | -- | -- |
| 53 | `sf_tot_partcp_boy_cnt` | numeric | Y | **MISSING** | -- | -- |
| 54 | `sf_tot_act_rtd_sep_benef_cnt` | numeric | Y | **MISSING** | -- | -- |
| 55 | `sf_partcp_account_bal_cnt` | numeric | Y | **MISSING** | -- | -- |
| 56 | `sf_eligible_assets_ind` | character varying(5) | Y | **MISSING** | -- | -- |
| 57 | `sf_iqpa_waiver_ind` | character varying(5) | Y | **MISSING** | -- | -- |
| 58 | `sf_tot_assets_boy_amt` | numeric | Y | **MISSING** | -- | -- |
| 59 | `sf_tot_liabilities_boy_amt` | numeric | Y | **MISSING** | -- | -- |
| 60 | `sf_net_assets_boy_amt` | numeric | Y | **MISSING** | -- | -- |
| 61 | `sf_tot_assets_eoy_amt` | numeric | Y | **MISSING** | -- | -- |
| 62 | `sf_tot_liabilities_eoy_amt` | numeric | Y | **MISSING** | -- | -- |
| 63 | `sf_net_assets_eoy_amt` | numeric | Y | **MISSING** | -- | -- |
| 64 | `sf_emplr_contrib_income_amt` | numeric | Y | **MISSING** | -- | -- |
| 65 | `sf_particip_contrib_income_amt` | numeric | Y | **MISSING** | -- | -- |
| 66 | `sf_oth_contrib_rcvd_amt` | numeric | Y | **MISSING** | -- | -- |
| 67 | `sf_other_income_amt` | numeric | Y | **MISSING** | -- | -- |
| 68 | `sf_tot_income_amt` | numeric | Y | **MISSING** | -- | -- |
| 69 | `sf_tot_distrib_bnft_amt` | numeric | Y | **MISSING** | -- | -- |
| 70 | `sf_corrective_deemed_distr_amt` | numeric | Y | **MISSING** | -- | -- |
| 71 | `sf_admin_srvc_providers_amt` | numeric | Y | **MISSING** | -- | -- |
| 72 | `sf_oth_expenses_amt` | numeric | Y | **MISSING** | -- | -- |
| 73 | `sf_tot_expenses_amt` | numeric | Y | **MISSING** | -- | -- |
| 74 | `sf_net_income_amt` | numeric | Y | **MISSING** | -- | -- |
| 75 | `sf_tot_plan_transfers_amt` | numeric | Y | **MISSING** | -- | -- |
| 76 | `sf_type_pension_bnft_code` | character varying(255) | Y | **MISSING** | -- | -- |
| 77 | `sf_type_welfare_bnft_code` | character varying(255) | Y | **MISSING** | -- | -- |
| 78 | `sf_fail_transmit_contrib_ind` | character varying(5) | Y | **MISSING** | -- | -- |
| 79 | `sf_fail_transmit_contrib_amt` | numeric | Y | **MISSING** | -- | -- |
| 80 | `sf_party_in_int_not_rptd_ind` | character varying(5) | Y | **MISSING** | -- | -- |
| 81 | `sf_party_in_int_not_rptd_amt` | numeric | Y | **MISSING** | -- | -- |
| 82 | `sf_plan_ins_fdlty_bond_ind` | character varying(5) | Y | **MISSING** | -- | -- |
| 83 | `sf_plan_ins_fdlty_bond_amt` | numeric | Y | **MISSING** | -- | -- |
| 84 | `sf_loss_discv_dur_year_ind` | character varying(5) | Y | **MISSING** | -- | -- |
| 85 | `sf_loss_discv_dur_year_amt` | numeric | Y | **MISSING** | -- | -- |
| 86 | `sf_broker_fees_paid_ind` | character varying(5) | Y | **MISSING** | -- | -- |
| 87 | `sf_broker_fees_paid_amt` | numeric | Y | **MISSING** | -- | -- |
| 88 | `sf_fail_provide_benef_due_ind` | character varying(5) | Y | **MISSING** | -- | -- |
| 89 | `sf_fail_provide_benef_due_amt` | numeric | Y | **MISSING** | -- | -- |
| 90 | `sf_partcp_loans_ind` | character varying(5) | Y | **MISSING** | -- | -- |
| 91 | `sf_partcp_loans_eoy_amt` | numeric | Y | **MISSING** | -- | -- |
| 92 | `sf_plan_blackout_period_ind` | character varying(5) | Y | **MISSING** | -- | -- |
| 93 | `sf_comply_blackout_notice_ind` | character varying(5) | Y | **MISSING** | -- | -- |
| 94 | `sf_db_plan_funding_reqd_ind` | character varying(5) | Y | **MISSING** | -- | -- |
| 95 | `sf_dc_plan_funding_reqd_ind` | character varying(5) | Y | **MISSING** | -- | -- |
| 96 | `sf_ruling_letter_grant_date` | character varying(255) | Y | **MISSING** | -- | -- |
| 97 | `sf_sec_412_req_contrib_amt` | numeric | Y | **MISSING** | -- | -- |
| 98 | `sf_emplr_contrib_paid_amt` | numeric | Y | **MISSING** | -- | -- |
| 99 | `sf_funding_deficiency_amt` | numeric | Y | **MISSING** | -- | -- |
| 100 | `sf_funding_deadline_ind` | character varying(5) | Y | **MISSING** | -- | -- |
| 101 | `sf_res_term_plan_adpt_ind` | character varying(5) | Y | **MISSING** | -- | -- |
| 102 | `sf_res_term_plan_adpt_amt` | numeric | Y | **MISSING** | -- | -- |
| 103 | `sf_all_plan_ast_distrib_ind` | character varying(5) | Y | **MISSING** | -- | -- |
| 104 | `sf_admin_signed_date` | character varying(255) | Y | **MISSING** | -- | -- |
| 105 | `sf_admin_signed_name` | character varying(255) | Y | **MISSING** | -- | -- |
| 106 | `sf_spons_signed_date` | character varying(255) | Y | **MISSING** | -- | -- |
| 107 | `sf_spons_signed_name` | character varying(255) | Y | **MISSING** | -- | -- |
| 108 | `filing_status` | character varying(255) | Y | **MISSING** | -- | -- |
| 109 | `date_received` | character varying(255) | Y | **MISSING** | -- | -- |
| 110 | `valid_admin_signature` | character varying(255) | Y | **MISSING** | -- | -- |
| 111 | `valid_sponsor_signature` | character varying(255) | Y | **MISSING** | -- | -- |
| 112 | `sf_admin_phone_num_foreign` | character varying(255) | Y | **MISSING** | -- | -- |
| 113 | `sf_spons_care_of_name` | character varying(255) | Y | **MISSING** | -- | -- |
| 114 | `sf_spons_loc_foreign_address1` | character varying(255) | Y | **MISSING** | -- | -- |
| 115 | `sf_spons_loc_foreign_address2` | character varying(255) | Y | **MISSING** | -- | -- |
| 116 | `sf_spons_loc_foreign_city` | character varying(255) | Y | **MISSING** | -- | -- |
| 117 | `sf_spons_loc_foreign_cntry` | character varying(255) | Y | **MISSING** | -- | -- |
| 118 | `sf_spons_loc_foreign_postal_cd` | character varying(255) | Y | **MISSING** | -- | -- |
| 119 | `sf_spons_loc_foreign_prov_stat` | character varying(255) | Y | **MISSING** | -- | -- |
| 120 | `sf_spons_loc_us_address1` | character varying(255) | Y | **MISSING** | -- | -- |
| 121 | `sf_spons_loc_us_address2` | character varying(255) | Y | **MISSING** | -- | -- |
| 122 | `sf_spons_loc_us_city` | character varying(255) | Y | **MISSING** | -- | -- |
| 123 | `sf_spons_loc_us_state` | character varying(255) | Y | **MISSING** | -- | -- |
| 124 | `sf_spons_loc_us_zip` | character varying(255) | Y | **MISSING** | -- | -- |
| 125 | `sf_spons_phone_num_foreign` | character varying(255) | Y | **MISSING** | -- | -- |
| 126 | `sf_admin_name_same_spon_ind` | character varying(5) | Y | **MISSING** | -- | -- |
| 127 | `sf_admin_addrss_same_spon_ind` | character varying(5) | Y | **MISSING** | -- | -- |
| 128 | `sf_preparer_name` | character varying(255) | Y | **MISSING** | -- | -- |
| 129 | `sf_preparer_firm_name` | character varying(255) | Y | **MISSING** | -- | -- |
| 130 | `sf_preparer_us_address1` | character varying(255) | Y | **MISSING** | -- | -- |
| 131 | `sf_preparer_us_address2` | character varying(255) | Y | **MISSING** | -- | -- |
| 132 | `sf_preparer_us_city` | character varying(255) | Y | **MISSING** | -- | -- |
| 133 | `sf_preparer_us_state` | character varying(255) | Y | **MISSING** | -- | -- |
| 134 | `sf_preparer_us_zip` | character varying(255) | Y | **MISSING** | -- | -- |
| 135 | `sf_preparer_foreign_address1` | character varying(255) | Y | **MISSING** | -- | -- |
| 136 | `sf_preparer_foreign_address2` | character varying(255) | Y | **MISSING** | -- | -- |
| 137 | `sf_preparer_foreign_city` | character varying(255) | Y | **MISSING** | -- | -- |
| 138 | `sf_preparer_foreign_prov_state` | character varying(255) | Y | **MISSING** | -- | -- |
| 139 | `sf_preparer_foreign_cntry` | character varying(255) | Y | **MISSING** | -- | -- |
| 140 | `sf_preparer_foreign_postal_cd` | character varying(255) | Y | **MISSING** | -- | -- |
| 141 | `sf_preparer_phone_num` | character varying(255) | Y | **MISSING** | -- | -- |
| 142 | `sf_preparer_phone_num_foreign` | character varying(255) | Y | **MISSING** | -- | -- |
| 143 | `sf_fdcry_trust_name` | character varying(255) | Y | **MISSING** | -- | -- |
| 144 | `sf_fdcry_trust_ein` | character varying(255) | Y | **MISSING** | -- | -- |
| 145 | `sf_unp_min_cont_cur_yrtot_amt` | numeric | Y | **MISSING** | -- | -- |
| 146 | `sf_covered_pbgc_insurance_ind` | character varying(5) | Y | **MISSING** | -- | -- |
| 147 | `sf_tot_act_partcp_boy_cnt` | numeric | Y | **MISSING** | -- | -- |
| 148 | `sf_tot_act_partcp_eoy_cnt` | numeric | Y | **MISSING** | -- | -- |
| 149 | `sf_sep_partcp_partl_vstd_cnt` | numeric | Y | **MISSING** | -- | -- |
| 150 | `sf_trus_inc_unrel_tax_inc_ind` | character varying(5) | Y | **MISSING** | -- | -- |
| 151 | `sf_trus_inc_unrel_tax_inc_amt` | numeric | Y | **MISSING** | -- | -- |
| 152 | `sf_fdcry_truste_cust_name` | character varying(255) | Y | **MISSING** | -- | -- |
| 153 | `sf_fdcry_truste_cust_phone_num` | character varying(255) | Y | **MISSING** | -- | -- |
| 154 | `sf_fdcry_trus_cus_phon_numfore` | character varying(255) | Y | **MISSING** | -- | -- |
| 155 | `sf_401k_plan_ind` | character varying(5) | Y | **MISSING** | -- | -- |
| 156 | `sf_401k_satisfy_rqmts_ind` | character varying(5) | Y | **MISSING** | -- | -- |
| 157 | `sf_adp_acp_test_ind` | character varying(5) | Y | **MISSING** | -- | -- |
| 158 | `sf_mthd_used_satisfy_rqmts_ind` | character varying(5) | Y | **MISSING** | -- | -- |
| 159 | `sf_plan_satisfy_tests_ind` | character varying(5) | Y | **MISSING** | -- | -- |
| 160 | `sf_plan_timely_amended_ind` | character varying(5) | Y | **MISSING** | -- | -- |
| 161 | `sf_last_plan_amendment_date` | character varying(255) | Y | **MISSING** | -- | -- |
| 162 | `sf_tax_code` | character varying(255) | Y | **MISSING** | -- | -- |
| 163 | `sf_last_opin_advi_date` | character varying(255) | Y | **MISSING** | -- | -- |
| 164 | `sf_last_opin_advi_serial_num` | character varying(255) | Y | **MISSING** | -- | -- |
| 165 | `sf_fav_determ_ltr_date` | character varying(255) | Y | **MISSING** | -- | -- |
| 166 | `sf_plan_maintain_us_terri_ind` | character varying(5) | Y | **MISSING** | -- | -- |
| 167 | `sf_in_service_distrib_ind` | character varying(5) | Y | **MISSING** | -- | -- |
| 168 | `sf_in_service_distrib_amt` | numeric | Y | **MISSING** | -- | -- |
| 169 | `sf_min_req_distrib_ind` | character varying(5) | Y | **MISSING** | -- | -- |
| 170 | `sf_admin_manual_sign_date` | character varying(255) | Y | **MISSING** | -- | -- |
| 171 | `sf_admin_manual_signed_name` | character varying(255) | Y | **MISSING** | -- | -- |
| 172 | `sf_401k_design_based_safe_ind` | character varying(5) | Y | **MISSING** | -- | -- |
| 173 | `sf_401k_prior_year_adp_ind` | character varying(5) | Y | **MISSING** | -- | -- |
| 174 | `sf_401k_current_year_adp_ind` | character varying(5) | Y | **MISSING** | -- | -- |
| 175 | `sf_401k_na_ind` | character varying(5) | Y | **MISSING** | -- | -- |
| 176 | `sf_mthd_ratio_prcnt_test_ind` | character varying(5) | Y | **MISSING** | -- | -- |
| 177 | `sf_mthd_avg_bnft_test_ind` | character varying(5) | Y | **MISSING** | -- | -- |
| 178 | `sf_mthd_na_ind` | character varying(5) | Y | **MISSING** | -- | -- |
| 179 | `sf_distrib_made_employe_62_ind` | character varying(5) | Y | **MISSING** | -- | -- |
| 180 | `sf_last_rpt_plan_name` | character varying(255) | Y | **MISSING** | -- | -- |
| 181 | `sf_premium_filing_confirm_no` | character varying(255) | Y | **MISSING** | -- | -- |
| 182 | `sf_spons_manual_signed_date` | character varying(255) | Y | **MISSING** | -- | -- |
| 183 | `sf_spons_manual_signed_name` | character varying(255) | Y | **MISSING** | -- | -- |
| 184 | `sf_pbgc_notified_cd` | character varying(255) | Y | **MISSING** | -- | -- |
| 185 | `sf_pbgc_notified_explan_text` | text | Y | **MISSING** | -- | -- |
| 186 | `sf_adopted_plan_perm_sec_act` | character varying(255) | Y | **MISSING** | -- | -- |
| 187 | `collectively_bargained` | character varying(255) | Y | **MISSING** | -- | -- |
| 188 | `sf_partcp_account_bal_cnt_boy` | character varying(255) | Y | **MISSING** | -- | -- |
| 189 | `sf_401k_design_based_safe_harbor_ind` | character varying(5) | Y | **MISSING** | -- | -- |
| 190 | `sf_401k_prior_year_adp_test_ind` | character varying(5) | Y | **MISSING** | -- | -- |
| 191 | `sf_401k_current_year_adp_test_ind` | character varying(5) | Y | **MISSING** | -- | -- |
| 192 | `sf_opin_letter_date` | character varying(255) | Y | **MISSING** | -- | -- |
| 193 | `sf_opin_letter_serial_num` | character varying(255) | Y | **MISSING** | -- | -- |
| 194 | `form_year` | character varying(10) | Y | **MISSING** | -- | -- |
| 195 | `created_at` | timestamp with time zone | Y | **MISSING** | -- | -- |
| 196 | `updated_at` | timestamp with time zone | Y | **MISSING** | -- | -- |

#### `dol.form_5500_sf_part7` -- UNREGISTERED -- 10,613 rows

Column registry: **UNDOCUMENTED**

| # | Column | Type | Null | Description | Role | Format |
|---|--------|------|------|-------------|------|--------|
| 1 | `id` | bigint | N | **MISSING** | -- | -- |
| 2 | `ack_id` | character varying(50) | N | **MISSING** | -- | -- |
| 3 | `row_order` | integer | Y | **MISSING** | -- | -- |
| 4 | `sf_plan_transfer_name` | character varying(500) | Y | **MISSING** | -- | -- |
| 5 | `sf_plan_transfer_ein` | character varying(20) | Y | **MISSING** | -- | -- |
| 6 | `sf_plan_transfer_pn` | character varying(10) | Y | **MISSING** | -- | -- |
| 7 | `form_year` | character varying(10) | Y | **MISSING** | -- | -- |
| 8 | `created_at` | timestamp with time zone | N | **MISSING** | -- | -- |

#### `dol.pressure_signals` -- MV -- 0 rows

Column registry: **UNDOCUMENTED**

| # | Column | Type | Null | Description | Role | Format |
|---|--------|------|------|-------------|------|--------|
| 1 | `signal_id` | uuid | N | **MISSING** | -- | -- |
| 2 | `company_unique_id` | text | N | **MISSING** | -- | -- |
| 3 | `signal_type` | character varying(50) | N | **MISSING** | -- | -- |
| 4 | `pressure_domain` | USER-DEFINED | N | **MISSING** | -- | -- |
| 5 | `pressure_class` | USER-DEFINED | Y | **MISSING** | -- | -- |
| 6 | `signal_value` | jsonb | N | **MISSING** | -- | -- |
| 7 | `magnitude` | integer | N | **MISSING** | -- | -- |
| 8 | `detected_at` | timestamp with time zone | N | **MISSING** | -- | -- |
| 9 | `expires_at` | timestamp with time zone | N | **MISSING** | -- | -- |
| 10 | `correlation_id` | uuid | Y | **MISSING** | -- | -- |
| 11 | `source_record_id` | text | Y | **MISSING** | -- | -- |
| 12 | `created_at` | timestamp with time zone | N | **MISSING** | -- | -- |

#### `dol.renewal_calendar` -- CANONICAL -- 0 rows

Column registry: **UNDOCUMENTED**

| # | Column | Type | Null | Description | Role | Format |
|---|--------|------|------|-------------|------|--------|
| 1 | `renewal_id` | uuid | N | **MISSING** | -- | -- |
| 2 | `company_unique_id` | text | N | **MISSING** | -- | -- |
| 3 | `schedule_id` | uuid | Y | **MISSING** | -- | -- |
| 4 | `filing_id` | uuid | Y | **MISSING** | -- | -- |
| 5 | `renewal_month` | integer | Y | **MISSING** | -- | -- |
| 6 | `renewal_year` | integer | Y | **MISSING** | -- | -- |
| 7 | `renewal_date` | date | Y | **MISSING** | -- | -- |
| 8 | `plan_name` | character varying(500) | Y | **MISSING** | -- | -- |
| 9 | `carrier_name` | character varying(500) | Y | **MISSING** | -- | -- |
| 10 | `is_upcoming` | boolean | N | **MISSING** | -- | -- |
| 11 | `days_until_renewal` | integer | Y | **MISSING** | -- | -- |
| 12 | `created_at` | timestamp with time zone | N | **MISSING** | -- | -- |
| 13 | `updated_at` | timestamp with time zone | N | **MISSING** | -- | -- |

#### `dol.schedule_a` -- CANONICAL -- 625,520 rows

Column registry: **UNDOCUMENTED**

| # | Column | Type | Null | Description | Role | Format |
|---|--------|------|------|-------------|------|--------|
| 1 | `schedule_id` | uuid | N | **MISSING** | -- | -- |
| 2 | `filing_id` | uuid | Y | **MISSING** | -- | -- |
| 3 | `company_unique_id` | text | Y | **MISSING** | -- | -- |
| 4 | `sponsor_state` | character varying(10) | Y | **MISSING** | -- | -- |
| 5 | `sponsor_name` | character varying(255) | Y | **MISSING** | -- | -- |
| 6 | `ack_id` | character varying(255) | Y | **MISSING** | -- | -- |
| 7 | `form_id` | character varying(255) | Y | **MISSING** | -- | -- |
| 8 | `sch_a_plan_year_begin_date` | character varying(30) | Y | **MISSING** | -- | -- |
| 9 | `sch_a_plan_year_end_date` | character varying(30) | Y | **MISSING** | -- | -- |
| 10 | `sch_a_plan_num` | character varying(255) | Y | **MISSING** | -- | -- |
| 11 | `sch_a_ein` | character varying(20) | Y | **MISSING** | -- | -- |
| 12 | `ins_carrier_name` | character varying(255) | Y | **MISSING** | -- | -- |
| 13 | `ins_carrier_ein` | character varying(20) | Y | **MISSING** | -- | -- |
| 14 | `ins_carrier_naic_code` | character varying(255) | Y | **MISSING** | -- | -- |
| 15 | `ins_contract_num` | character varying(255) | Y | **MISSING** | -- | -- |
| 16 | `ins_prsn_covered_eoy_cnt` | numeric | Y | **MISSING** | -- | -- |
| 17 | `ins_policy_from_date` | character varying(30) | Y | **MISSING** | -- | -- |
| 18 | `ins_policy_to_date` | character varying(30) | Y | **MISSING** | -- | -- |
| 19 | `ins_broker_comm_tot_amt` | numeric | Y | **MISSING** | -- | -- |
| 20 | `ins_broker_fees_tot_amt` | numeric | Y | **MISSING** | -- | -- |
| 21 | `pension_eoy_gen_acct_amt` | numeric | Y | **MISSING** | -- | -- |
| 22 | `pension_eoy_sep_acct_amt` | numeric | Y | **MISSING** | -- | -- |
| 23 | `pension_basis_rates_text` | text | Y | **MISSING** | -- | -- |
| 24 | `pension_prem_paid_tot_amt` | numeric | Y | **MISSING** | -- | -- |
| 25 | `pension_unpaid_premium_amt` | numeric | Y | **MISSING** | -- | -- |
| 26 | `pension_contract_cost_amt` | numeric | Y | **MISSING** | -- | -- |
| 27 | `pension_cost_text` | text | Y | **MISSING** | -- | -- |
| 28 | `alloc_contracts_indiv_ind` | character varying(5) | Y | **MISSING** | -- | -- |
| 29 | `alloc_contracts_group_ind` | character varying(5) | Y | **MISSING** | -- | -- |
| 30 | `alloc_contracts_other_ind` | character varying(5) | Y | **MISSING** | -- | -- |
| 31 | `alloc_contracts_other_text` | text | Y | **MISSING** | -- | -- |
| 32 | `pens_distr_bnft_term_pln_ind` | character varying(5) | Y | **MISSING** | -- | -- |
| 33 | `unalloc_contracts_dep_adm_ind` | character varying(5) | Y | **MISSING** | -- | -- |
| 34 | `unal_contrac_imm_part_guar_ind` | character varying(5) | Y | **MISSING** | -- | -- |
| 35 | `unal_contracts_guar_invest_ind` | character varying(5) | Y | **MISSING** | -- | -- |
| 36 | `unalloc_contracts_other_ind` | character varying(5) | Y | **MISSING** | -- | -- |
| 37 | `unalloc_contracts_other_text` | text | Y | **MISSING** | -- | -- |
| 38 | `pension_end_prev_bal_amt` | numeric | Y | **MISSING** | -- | -- |
| 39 | `pension_contrib_dep_amt` | numeric | Y | **MISSING** | -- | -- |
| 40 | `pension_divnd_cr_dep_amt` | numeric | Y | **MISSING** | -- | -- |
| 41 | `pension_int_cr_dur_yr_amt` | numeric | Y | **MISSING** | -- | -- |
| 42 | `pension_transfer_from_amt` | numeric | Y | **MISSING** | -- | -- |
| 43 | `pension_other_amt` | numeric | Y | **MISSING** | -- | -- |
| 44 | `pension_other_text` | text | Y | **MISSING** | -- | -- |
| 45 | `pension_tot_additions_amt` | numeric | Y | **MISSING** | -- | -- |
| 46 | `pension_tot_bal_addn_amt` | numeric | Y | **MISSING** | -- | -- |
| 47 | `pension_bnfts_dsbrsd_amt` | numeric | Y | **MISSING** | -- | -- |
| 48 | `pension_admin_chrg_amt` | numeric | Y | **MISSING** | -- | -- |
| 49 | `pension_transfer_to_amt` | numeric | Y | **MISSING** | -- | -- |
| 50 | `pension_oth_ded_amt` | numeric | Y | **MISSING** | -- | -- |
| 51 | `pension_oth_ded_text` | text | Y | **MISSING** | -- | -- |
| 52 | `pension_tot_ded_amt` | numeric | Y | **MISSING** | -- | -- |
| 53 | `pension_eoy_bal_amt` | numeric | Y | **MISSING** | -- | -- |
| 54 | `wlfr_bnft_health_ind` | character varying(5) | Y | **MISSING** | -- | -- |
| 55 | `wlfr_bnft_dental_ind` | character varying(5) | Y | **MISSING** | -- | -- |
| 56 | `wlfr_bnft_vision_ind` | character varying(5) | Y | **MISSING** | -- | -- |
| 57 | `wlfr_bnft_life_insur_ind` | character varying(5) | Y | **MISSING** | -- | -- |
| 58 | `wlfr_bnft_temp_disab_ind` | character varying(5) | Y | **MISSING** | -- | -- |
| 59 | `wlfr_bnft_long_term_disab_ind` | character varying(5) | Y | **MISSING** | -- | -- |
| 60 | `wlfr_bnft_unemp_ind` | character varying(5) | Y | **MISSING** | -- | -- |
| 61 | `wlfr_bnft_drug_ind` | character varying(5) | Y | **MISSING** | -- | -- |
| 62 | `wlfr_bnft_stop_loss_ind` | character varying(5) | Y | **MISSING** | -- | -- |
| 63 | `wlfr_bnft_hmo_ind` | character varying(5) | Y | **MISSING** | -- | -- |
| 64 | `wlfr_bnft_ppo_ind` | character varying(5) | Y | **MISSING** | -- | -- |
| 65 | `wlfr_bnft_indemnity_ind` | character varying(5) | Y | **MISSING** | -- | -- |
| 66 | `wlfr_bnft_other_ind` | character varying(5) | Y | **MISSING** | -- | -- |
| 67 | `wlfr_type_bnft_oth_text` | text | Y | **MISSING** | -- | -- |
| 68 | `wlfr_premium_rcvd_amt` | numeric | Y | **MISSING** | -- | -- |
| 69 | `wlfr_unpaid_due_amt` | numeric | Y | **MISSING** | -- | -- |
| 70 | `wlfr_reserve_amt` | numeric | Y | **MISSING** | -- | -- |
| 71 | `wlfr_tot_earned_prem_amt` | numeric | Y | **MISSING** | -- | -- |
| 72 | `wlfr_claims_paid_amt` | numeric | Y | **MISSING** | -- | -- |
| 73 | `wlfr_incr_reserve_amt` | numeric | Y | **MISSING** | -- | -- |
| 74 | `wlfr_incurred_claim_amt` | numeric | Y | **MISSING** | -- | -- |
| 75 | `wlfr_claims_chrgd_amt` | numeric | Y | **MISSING** | -- | -- |
| 76 | `wlfr_ret_commissions_amt` | numeric | Y | **MISSING** | -- | -- |
| 77 | `wlfr_ret_admin_amt` | numeric | Y | **MISSING** | -- | -- |
| 78 | `wlfr_ret_oth_cost_amt` | numeric | Y | **MISSING** | -- | -- |
| 79 | `wlfr_ret_oth_expense_amt` | numeric | Y | **MISSING** | -- | -- |
| 80 | `wlfr_ret_taxes_amt` | numeric | Y | **MISSING** | -- | -- |
| 81 | `wlfr_ret_charges_amt` | numeric | Y | **MISSING** | -- | -- |
| 82 | `wlfr_ret_oth_chrgs_amt` | numeric | Y | **MISSING** | -- | -- |
| 83 | `wlfr_ret_tot_amt` | numeric | Y | **MISSING** | -- | -- |
| 84 | `wlfr_refund_cash_ind` | character varying(5) | Y | **MISSING** | -- | -- |
| 85 | `wlfr_refund_credit_ind` | character varying(5) | Y | **MISSING** | -- | -- |
| 86 | `wlfr_refund_amt` | numeric | Y | **MISSING** | -- | -- |
| 87 | `wlfr_held_bnfts_amt` | numeric | Y | **MISSING** | -- | -- |
| 88 | `wlfr_claims_reserve_amt` | numeric | Y | **MISSING** | -- | -- |
| 89 | `wlfr_oth_reserve_amt` | numeric | Y | **MISSING** | -- | -- |
| 90 | `wlfr_divnds_due_amt` | numeric | Y | **MISSING** | -- | -- |
| 91 | `wlfr_tot_charges_paid_amt` | numeric | Y | **MISSING** | -- | -- |
| 92 | `wlfr_acquis_cost_amt` | numeric | Y | **MISSING** | -- | -- |
| 93 | `wlfr_acquis_cost_text` | text | Y | **MISSING** | -- | -- |
| 94 | `ins_fail_provide_info_ind` | character varying(5) | Y | **MISSING** | -- | -- |
| 95 | `ins_fail_provide_info_text` | text | Y | **MISSING** | -- | -- |
| 96 | `form_year` | character varying(10) | Y | **MISSING** | -- | -- |
| 97 | `created_at` | timestamp with time zone | Y | **MISSING** | -- | -- |
| 98 | `updated_at` | timestamp with time zone | Y | **MISSING** | -- | -- |

#### `dol.schedule_a_part1` -- UNREGISTERED -- 380,509 rows

Column registry: **UNDOCUMENTED**

| # | Column | Type | Null | Description | Role | Format |
|---|--------|------|------|-------------|------|--------|
| 1 | `id` | bigint | N | **MISSING** | -- | -- |
| 2 | `ack_id` | character varying(50) | N | **MISSING** | -- | -- |
| 3 | `form_id` | character varying(50) | Y | **MISSING** | -- | -- |
| 4 | `row_order` | integer | Y | **MISSING** | -- | -- |
| 5 | `ins_broker_name` | character varying(500) | Y | **MISSING** | -- | -- |
| 6 | `ins_broker_us_address1` | character varying(500) | Y | **MISSING** | -- | -- |
| 7 | `ins_broker_us_address2` | character varying(500) | Y | **MISSING** | -- | -- |
| 8 | `ins_broker_us_city` | character varying(255) | Y | **MISSING** | -- | -- |
| 9 | `ins_broker_us_state` | character varying(10) | Y | **MISSING** | -- | -- |
| 10 | `ins_broker_us_zip` | character varying(20) | Y | **MISSING** | -- | -- |
| 11 | `ins_broker_foreign_address1` | character varying(500) | Y | **MISSING** | -- | -- |
| 12 | `ins_broker_foreign_address2` | character varying(500) | Y | **MISSING** | -- | -- |
| 13 | `ins_broker_foreign_city` | character varying(255) | Y | **MISSING** | -- | -- |
| 14 | `ins_broker_foreign_prov_state` | character varying(100) | Y | **MISSING** | -- | -- |
| 15 | `ins_broker_foreign_cntry` | character varying(100) | Y | **MISSING** | -- | -- |
| 16 | `ins_broker_foreign_postal_cd` | character varying(50) | Y | **MISSING** | -- | -- |
| 17 | `ins_broker_comm_pd_amt` | numeric | Y | **MISSING** | -- | -- |
| 18 | `ins_broker_fees_pd_amt` | numeric | Y | **MISSING** | -- | -- |
| 19 | `ins_broker_fees_pd_text` | text | Y | **MISSING** | -- | -- |
| 20 | `ins_broker_code` | character varying(50) | Y | **MISSING** | -- | -- |
| 21 | `form_year` | character varying(10) | Y | **MISSING** | -- | -- |
| 22 | `created_at` | timestamp with time zone | N | **MISSING** | -- | -- |

#### `dol.schedule_c` -- UNREGISTERED -- 241,556 rows

Column registry: **UNDOCUMENTED**

| # | Column | Type | Null | Description | Role | Format |
|---|--------|------|------|-------------|------|--------|
| 1 | `id` | bigint | N | **MISSING** | -- | -- |
| 2 | `ack_id` | character varying(50) | N | **MISSING** | -- | -- |
| 3 | `provider_exclude_ind` | character varying(10) | Y | **MISSING** | -- | -- |
| 4 | `form_year` | character varying(10) | Y | **MISSING** | -- | -- |
| 5 | `created_at` | timestamp with time zone | N | **MISSING** | -- | -- |

#### `dol.schedule_c_part1_item1` -- UNREGISTERED -- 396,838 rows

Column registry: **UNDOCUMENTED**

| # | Column | Type | Null | Description | Role | Format |
|---|--------|------|------|-------------|------|--------|
| 1 | `id` | bigint | N | **MISSING** | -- | -- |
| 2 | `ack_id` | character varying(50) | N | **MISSING** | -- | -- |
| 3 | `row_order` | integer | Y | **MISSING** | -- | -- |
| 4 | `provider_eligible_name` | character varying(500) | Y | **MISSING** | -- | -- |
| 5 | `provider_eligible_ein` | character varying(20) | Y | **MISSING** | -- | -- |
| 6 | `provider_eligible_us_address1` | character varying(500) | Y | **MISSING** | -- | -- |
| 7 | `provider_eligible_us_address2` | character varying(500) | Y | **MISSING** | -- | -- |
| 8 | `provider_eligible_us_city` | character varying(255) | Y | **MISSING** | -- | -- |
| 9 | `provider_eligible_us_state` | character varying(10) | Y | **MISSING** | -- | -- |
| 10 | `provider_eligible_us_zip` | character varying(20) | Y | **MISSING** | -- | -- |
| 11 | `prov_eligible_foreign_address1` | character varying(500) | Y | **MISSING** | -- | -- |
| 12 | `prov_eligible_foreign_address2` | character varying(500) | Y | **MISSING** | -- | -- |
| 13 | `prov_eligible_foreign_city` | character varying(255) | Y | **MISSING** | -- | -- |
| 14 | `prov_eligible_foreign_prov_st` | character varying(100) | Y | **MISSING** | -- | -- |
| 15 | `prov_eligible_foreign_cntry` | character varying(100) | Y | **MISSING** | -- | -- |
| 16 | `prov_eligible_foreign_post_cd` | character varying(50) | Y | **MISSING** | -- | -- |
| 17 | `form_year` | character varying(10) | Y | **MISSING** | -- | -- |
| 18 | `created_at` | timestamp with time zone | N | **MISSING** | -- | -- |

#### `dol.schedule_c_part1_item2` -- UNREGISTERED -- 754,802 rows

Column registry: **UNDOCUMENTED**

| # | Column | Type | Null | Description | Role | Format |
|---|--------|------|------|-------------|------|--------|
| 1 | `id` | bigint | N | **MISSING** | -- | -- |
| 2 | `ack_id` | character varying(50) | N | **MISSING** | -- | -- |
| 3 | `row_order` | integer | Y | **MISSING** | -- | -- |
| 4 | `provider_other_name` | character varying(500) | Y | **MISSING** | -- | -- |
| 5 | `provider_other_ein` | character varying(20) | Y | **MISSING** | -- | -- |
| 6 | `provider_other_us_address1` | character varying(500) | Y | **MISSING** | -- | -- |
| 7 | `provider_other_us_address2` | character varying(500) | Y | **MISSING** | -- | -- |
| 8 | `provider_other_us_city` | character varying(255) | Y | **MISSING** | -- | -- |
| 9 | `provider_other_us_state` | character varying(10) | Y | **MISSING** | -- | -- |
| 10 | `provider_other_us_zip` | character varying(20) | Y | **MISSING** | -- | -- |
| 11 | `prov_other_foreign_address1` | character varying(500) | Y | **MISSING** | -- | -- |
| 12 | `prov_other_foreign_address2` | character varying(500) | Y | **MISSING** | -- | -- |
| 13 | `prov_other_foreign_city` | character varying(255) | Y | **MISSING** | -- | -- |
| 14 | `prov_other_foreign_prov_state` | character varying(100) | Y | **MISSING** | -- | -- |
| 15 | `prov_other_foreign_cntry` | character varying(100) | Y | **MISSING** | -- | -- |
| 16 | `prov_other_foreign_postal_cd` | character varying(50) | Y | **MISSING** | -- | -- |
| 17 | `provider_other_srvc_codes` | character varying(255) | Y | **MISSING** | -- | -- |
| 18 | `provider_other_relation` | character varying(255) | Y | **MISSING** | -- | -- |
| 19 | `provider_other_direct_comp_amt` | numeric | Y | **MISSING** | -- | -- |
| 20 | `prov_other_indirect_comp_ind` | character varying(10) | Y | **MISSING** | -- | -- |
| 21 | `prov_other_elig_ind_comp_ind` | character varying(10) | Y | **MISSING** | -- | -- |
| 22 | `prov_other_tot_ind_comp_amt` | numeric | Y | **MISSING** | -- | -- |
| 23 | `provider_other_amt_formula_ind` | character varying(10) | Y | **MISSING** | -- | -- |
| 24 | `form_year` | character varying(10) | Y | **MISSING** | -- | -- |
| 25 | `created_at` | timestamp with time zone | N | **MISSING** | -- | -- |

#### `dol.schedule_c_part1_item2_codes` -- UNREGISTERED -- 1,848,202 rows

Column registry: **UNDOCUMENTED**

| # | Column | Type | Null | Description | Role | Format |
|---|--------|------|------|-------------|------|--------|
| 1 | `id` | bigint | N | **MISSING** | -- | -- |
| 2 | `ack_id` | character varying(50) | N | **MISSING** | -- | -- |
| 3 | `row_order` | integer | Y | **MISSING** | -- | -- |
| 4 | `code_order` | integer | Y | **MISSING** | -- | -- |
| 5 | `service_code` | character varying(50) | Y | **MISSING** | -- | -- |
| 6 | `form_year` | character varying(10) | Y | **MISSING** | -- | -- |
| 7 | `created_at` | timestamp with time zone | N | **MISSING** | -- | -- |

#### `dol.schedule_c_part1_item3` -- UNREGISTERED -- 383,338 rows

Column registry: **UNDOCUMENTED**

| # | Column | Type | Null | Description | Role | Format |
|---|--------|------|------|-------------|------|--------|
| 1 | `id` | bigint | N | **MISSING** | -- | -- |
| 2 | `ack_id` | character varying(50) | N | **MISSING** | -- | -- |
| 3 | `row_order` | integer | Y | **MISSING** | -- | -- |
| 4 | `provider_indirect_name` | character varying(500) | Y | **MISSING** | -- | -- |
| 5 | `provider_indirect_srvc_codes` | character varying(255) | Y | **MISSING** | -- | -- |
| 6 | `provider_indirect_comp_amt` | numeric | Y | **MISSING** | -- | -- |
| 7 | `provider_payor_name` | character varying(500) | Y | **MISSING** | -- | -- |
| 8 | `provider_payor_ein` | character varying(20) | Y | **MISSING** | -- | -- |
| 9 | `provider_payor_us_address1` | character varying(500) | Y | **MISSING** | -- | -- |
| 10 | `provider_payor_us_address2` | character varying(500) | Y | **MISSING** | -- | -- |
| 11 | `provider_payor_us_city` | character varying(255) | Y | **MISSING** | -- | -- |
| 12 | `provider_payor_us_state` | character varying(10) | Y | **MISSING** | -- | -- |
| 13 | `provider_payor_us_zip` | character varying(20) | Y | **MISSING** | -- | -- |
| 14 | `prov_payor_foreign_address1` | character varying(500) | Y | **MISSING** | -- | -- |
| 15 | `prov_payor_foreign_address2` | character varying(500) | Y | **MISSING** | -- | -- |
| 16 | `prov_payor_foreign_city` | character varying(255) | Y | **MISSING** | -- | -- |
| 17 | `prov_payor_foreign_prov_state` | character varying(100) | Y | **MISSING** | -- | -- |
| 18 | `prov_payor_foreign_cntry` | character varying(100) | Y | **MISSING** | -- | -- |
| 19 | `prov_payor_foreign_postal_cd` | character varying(50) | Y | **MISSING** | -- | -- |
| 20 | `provider_comp_explain_text` | text | Y | **MISSING** | -- | -- |
| 21 | `form_year` | character varying(10) | Y | **MISSING** | -- | -- |
| 22 | `created_at` | timestamp with time zone | N | **MISSING** | -- | -- |

#### `dol.schedule_c_part1_item3_codes` -- UNREGISTERED -- 707,007 rows

Column registry: **UNDOCUMENTED**

| # | Column | Type | Null | Description | Role | Format |
|---|--------|------|------|-------------|------|--------|
| 1 | `id` | bigint | N | **MISSING** | -- | -- |
| 2 | `ack_id` | character varying(50) | N | **MISSING** | -- | -- |
| 3 | `row_order` | integer | Y | **MISSING** | -- | -- |
| 4 | `code_order` | integer | Y | **MISSING** | -- | -- |
| 5 | `service_code` | character varying(50) | Y | **MISSING** | -- | -- |
| 6 | `form_year` | character varying(10) | Y | **MISSING** | -- | -- |
| 7 | `created_at` | timestamp with time zone | N | **MISSING** | -- | -- |

#### `dol.schedule_c_part2` -- UNREGISTERED -- 4,593 rows

Column registry: **UNDOCUMENTED**

| # | Column | Type | Null | Description | Role | Format |
|---|--------|------|------|-------------|------|--------|
| 1 | `id` | bigint | N | **MISSING** | -- | -- |
| 2 | `ack_id` | character varying(50) | N | **MISSING** | -- | -- |
| 3 | `row_order` | integer | Y | **MISSING** | -- | -- |
| 4 | `provider_fail_name` | character varying(500) | Y | **MISSING** | -- | -- |
| 5 | `provider_fail_ein` | character varying(20) | Y | **MISSING** | -- | -- |
| 6 | `provider_fail_us_address1` | character varying(500) | Y | **MISSING** | -- | -- |
| 7 | `provider_fail_us_address2` | character varying(500) | Y | **MISSING** | -- | -- |
| 8 | `provider_fail_us_city` | character varying(255) | Y | **MISSING** | -- | -- |
| 9 | `provider_fail_us_state` | character varying(10) | Y | **MISSING** | -- | -- |
| 10 | `provider_fail_us_zip` | character varying(20) | Y | **MISSING** | -- | -- |
| 11 | `provider_fail_foreign_address1` | character varying(500) | Y | **MISSING** | -- | -- |
| 12 | `provider_fail_foreign_address2` | character varying(500) | Y | **MISSING** | -- | -- |
| 13 | `provider_fail_foreign_city` | character varying(255) | Y | **MISSING** | -- | -- |
| 14 | `provider_fail_foreign_prov_st` | character varying(100) | Y | **MISSING** | -- | -- |
| 15 | `provider_fail_foreign_cntry` | character varying(100) | Y | **MISSING** | -- | -- |
| 16 | `provider_fail_forgn_postal_cd` | character varying(50) | Y | **MISSING** | -- | -- |
| 17 | `provider_fail_srvc_code` | character varying(255) | Y | **MISSING** | -- | -- |
| 18 | `provider_fail_info_text` | text | Y | **MISSING** | -- | -- |
| 19 | `form_year` | character varying(10) | Y | **MISSING** | -- | -- |
| 20 | `created_at` | timestamp with time zone | N | **MISSING** | -- | -- |

#### `dol.schedule_c_part2_codes` -- UNREGISTERED -- 2,352 rows

Column registry: **UNDOCUMENTED**

| # | Column | Type | Null | Description | Role | Format |
|---|--------|------|------|-------------|------|--------|
| 1 | `id` | bigint | N | **MISSING** | -- | -- |
| 2 | `ack_id` | character varying(50) | N | **MISSING** | -- | -- |
| 3 | `row_order` | integer | Y | **MISSING** | -- | -- |
| 4 | `code_order` | integer | Y | **MISSING** | -- | -- |
| 5 | `service_code` | character varying(50) | Y | **MISSING** | -- | -- |
| 6 | `form_year` | character varying(10) | Y | **MISSING** | -- | -- |
| 7 | `created_at` | timestamp with time zone | N | **MISSING** | -- | -- |

#### `dol.schedule_c_part3` -- UNREGISTERED -- 15,514 rows

Column registry: **UNDOCUMENTED**

| # | Column | Type | Null | Description | Role | Format |
|---|--------|------|------|-------------|------|--------|
| 1 | `id` | bigint | N | **MISSING** | -- | -- |
| 2 | `ack_id` | character varying(50) | N | **MISSING** | -- | -- |
| 3 | `row_order` | integer | Y | **MISSING** | -- | -- |
| 4 | `provider_term_name` | character varying(500) | Y | **MISSING** | -- | -- |
| 5 | `provider_term_ein` | character varying(20) | Y | **MISSING** | -- | -- |
| 6 | `provider_term_position` | character varying(500) | Y | **MISSING** | -- | -- |
| 7 | `provider_term_us_address1` | character varying(500) | Y | **MISSING** | -- | -- |
| 8 | `provider_term_us_address2` | character varying(500) | Y | **MISSING** | -- | -- |
| 9 | `provider_term_us_city` | character varying(255) | Y | **MISSING** | -- | -- |
| 10 | `provider_term_us_state` | character varying(10) | Y | **MISSING** | -- | -- |
| 11 | `provider_term_us_zip` | character varying(20) | Y | **MISSING** | -- | -- |
| 12 | `provider_term_foreign_address1` | character varying(500) | Y | **MISSING** | -- | -- |
| 13 | `provider_term_foreign_address2` | character varying(500) | Y | **MISSING** | -- | -- |
| 14 | `provider_term_foreign_city` | character varying(255) | Y | **MISSING** | -- | -- |
| 15 | `provider_term_foreign_prov_st` | character varying(100) | Y | **MISSING** | -- | -- |
| 16 | `provider_term_foreign_cntry` | character varying(100) | Y | **MISSING** | -- | -- |
| 17 | `provider_term_forgn_postal_cd` | character varying(50) | Y | **MISSING** | -- | -- |
| 18 | `provider_term_phone_num` | character varying(30) | Y | **MISSING** | -- | -- |
| 19 | `provider_term_text` | text | Y | **MISSING** | -- | -- |
| 20 | `provider_term_phone_num_foreig` | character varying(30) | Y | **MISSING** | -- | -- |
| 21 | `form_year` | character varying(10) | Y | **MISSING** | -- | -- |
| 22 | `created_at` | timestamp with time zone | N | **MISSING** | -- | -- |

#### `dol.schedule_d` -- UNREGISTERED -- 121,813 rows

Column registry: **UNDOCUMENTED**

| # | Column | Type | Null | Description | Role | Format |
|---|--------|------|------|-------------|------|--------|
| 1 | `id` | bigint | N | **MISSING** | -- | -- |
| 2 | `ack_id` | character varying(50) | N | **MISSING** | -- | -- |
| 3 | `sch_d_plan_year_begin_date` | character varying(30) | Y | **MISSING** | -- | -- |
| 4 | `sch_d_tax_prd` | character varying(30) | Y | **MISSING** | -- | -- |
| 5 | `sch_d_pn` | character varying(10) | Y | **MISSING** | -- | -- |
| 6 | `sch_d_ein` | character varying(20) | Y | **MISSING** | -- | -- |
| 7 | `form_year` | character varying(10) | Y | **MISSING** | -- | -- |
| 8 | `created_at` | timestamp with time zone | N | **MISSING** | -- | -- |

#### `dol.schedule_d_part1` -- UNREGISTERED -- 808,051 rows

Column registry: **UNDOCUMENTED**

| # | Column | Type | Null | Description | Role | Format |
|---|--------|------|------|-------------|------|--------|
| 1 | `id` | bigint | N | **MISSING** | -- | -- |
| 2 | `ack_id` | character varying(50) | N | **MISSING** | -- | -- |
| 3 | `row_order` | integer | Y | **MISSING** | -- | -- |
| 4 | `dfe_p1_entity_name` | character varying(500) | Y | **MISSING** | -- | -- |
| 5 | `dfe_p1_spons_name` | character varying(500) | Y | **MISSING** | -- | -- |
| 6 | `dfe_p1_plan_ein` | character varying(20) | Y | **MISSING** | -- | -- |
| 7 | `dfe_p1_plan_pn` | character varying(10) | Y | **MISSING** | -- | -- |
| 8 | `dfe_p1_entity_code` | character varying(10) | Y | **MISSING** | -- | -- |
| 9 | `dfe_p1_plan_int_eoy_amt` | numeric | Y | **MISSING** | -- | -- |
| 10 | `form_year` | character varying(10) | Y | **MISSING** | -- | -- |
| 11 | `created_at` | timestamp with time zone | N | **MISSING** | -- | -- |

#### `dol.schedule_d_part2` -- UNREGISTERED -- 2,392,252 rows

Column registry: **UNDOCUMENTED**

| # | Column | Type | Null | Description | Role | Format |
|---|--------|------|------|-------------|------|--------|
| 1 | `id` | bigint | N | **MISSING** | -- | -- |
| 2 | `ack_id` | character varying(50) | N | **MISSING** | -- | -- |
| 3 | `row_order` | integer | Y | **MISSING** | -- | -- |
| 4 | `dfe_p2_plan_name` | character varying(500) | Y | **MISSING** | -- | -- |
| 5 | `dfe_p2_plan_spons_name` | character varying(500) | Y | **MISSING** | -- | -- |
| 6 | `dfe_p2_plan_ein` | character varying(20) | Y | **MISSING** | -- | -- |
| 7 | `dfe_p2_plan_pn` | character varying(10) | Y | **MISSING** | -- | -- |
| 8 | `form_year` | character varying(10) | Y | **MISSING** | -- | -- |
| 9 | `created_at` | timestamp with time zone | N | **MISSING** | -- | -- |

#### `dol.schedule_dcg` -- UNREGISTERED -- 235 rows

Column registry: **UNDOCUMENTED**

| # | Column | Type | Null | Description | Role | Format |
|---|--------|------|------|-------------|------|--------|
| 1 | `id` | bigint | N | **MISSING** | -- | -- |
| 2 | `ack_id` | character varying(50) | N | **MISSING** | -- | -- |
| 3 | `form_id` | character varying(50) | Y | **MISSING** | -- | -- |
| 4 | `sch_dcg_name` | character varying(500) | Y | **MISSING** | -- | -- |
| 5 | `sch_dcg_plan_num` | character varying(10) | Y | **MISSING** | -- | -- |
| 6 | `sch_dcg_sponsor_name` | character varying(500) | Y | **MISSING** | -- | -- |
| 7 | `sch_dcg_ein` | character varying(20) | Y | **MISSING** | -- | -- |
| 8 | `dcg_plan_type` | character varying(50) | Y | **MISSING** | -- | -- |
| 9 | `dcg_initial_filing_ind` | character varying(10) | Y | **MISSING** | -- | -- |
| 10 | `dcg_amended_ind` | character varying(10) | Y | **MISSING** | -- | -- |
| 11 | `dcg_final_ind` | character varying(10) | Y | **MISSING** | -- | -- |
| 12 | `dcg_plan_name` | character varying(500) | Y | **MISSING** | -- | -- |
| 13 | `dcg_plan_num` | character varying(10) | Y | **MISSING** | -- | -- |
| 14 | `dcg_plan_eff_date` | character varying(30) | Y | **MISSING** | -- | -- |
| 15 | `dcg_sponsor_name` | character varying(500) | Y | **MISSING** | -- | -- |
| 16 | `dcg_spons_dba_name` | character varying(500) | Y | **MISSING** | -- | -- |
| 17 | `dcg_spons_care_of_name` | character varying(500) | Y | **MISSING** | -- | -- |
| 18 | `dcg_spons_us_address1` | character varying(500) | Y | **MISSING** | -- | -- |
| 19 | `dcg_spons_us_address2` | character varying(500) | Y | **MISSING** | -- | -- |
| 20 | `dcg_spons_us_city` | character varying(255) | Y | **MISSING** | -- | -- |
| 21 | `dcg_spons_us_state` | character varying(10) | Y | **MISSING** | -- | -- |
| 22 | `dcg_spons_us_zip` | character varying(20) | Y | **MISSING** | -- | -- |
| 23 | `dcg_spons_foreign_address1` | character varying(500) | Y | **MISSING** | -- | -- |
| 24 | `dcg_spons_foreign_address2` | character varying(500) | Y | **MISSING** | -- | -- |
| 25 | `dcg_spons_foreign_city` | character varying(255) | Y | **MISSING** | -- | -- |
| 26 | `dcg_spons_foreign_prov_state` | character varying(100) | Y | **MISSING** | -- | -- |
| 27 | `dcg_spons_foreign_cntry` | character varying(100) | Y | **MISSING** | -- | -- |
| 28 | `dcg_spons_foreign_postal_cd` | character varying(50) | Y | **MISSING** | -- | -- |
| 29 | `dcg_spons_loc_us_address1` | character varying(500) | Y | **MISSING** | -- | -- |
| 30 | `dcg_spons_loc_us_address2` | character varying(500) | Y | **MISSING** | -- | -- |
| 31 | `dcg_spons_loc_us_city` | character varying(255) | Y | **MISSING** | -- | -- |
| 32 | `dcg_spons_loc_us_state` | character varying(10) | Y | **MISSING** | -- | -- |
| 33 | `dcg_spons_loc_us_zip` | character varying(20) | Y | **MISSING** | -- | -- |
| 34 | `dcg_spons_loc_foreign_address1` | character varying(500) | Y | **MISSING** | -- | -- |
| 35 | `dcg_spons_loc_foreign_address2` | character varying(500) | Y | **MISSING** | -- | -- |
| 36 | `dcg_spons_loc_foreign_city` | character varying(255) | Y | **MISSING** | -- | -- |
| 37 | `dcg_spons_loc_foreign_prov_state` | character varying(100) | Y | **MISSING** | -- | -- |
| 38 | `dcg_spons_loc_foreign_cntry` | character varying(100) | Y | **MISSING** | -- | -- |
| 39 | `dcg_spons_loc_foreign_postal_cd` | character varying(50) | Y | **MISSING** | -- | -- |
| 40 | `dcg_spons_ein` | character varying(20) | Y | **MISSING** | -- | -- |
| 41 | `dcg_spons_phone_num` | character varying(30) | Y | **MISSING** | -- | -- |
| 42 | `dcg_spons_phone_num_foreign` | character varying(30) | Y | **MISSING** | -- | -- |
| 43 | `dcg_business_code` | character varying(20) | Y | **MISSING** | -- | -- |
| 44 | `dcg_last_rpt_spons_name` | character varying(500) | Y | **MISSING** | -- | -- |
| 45 | `dcg_last_rpt_spons_ein` | character varying(20) | Y | **MISSING** | -- | -- |
| 46 | `dcg_last_rpt_plan_name` | character varying(500) | Y | **MISSING** | -- | -- |
| 47 | `dcg_last_rpt_plan_num` | character varying(10) | Y | **MISSING** | -- | -- |
| 48 | `dcg_admin_name` | character varying(500) | Y | **MISSING** | -- | -- |
| 49 | `dcg_admin_us_address1` | character varying(500) | Y | **MISSING** | -- | -- |
| 50 | `dcg_admin_us_address2` | character varying(500) | Y | **MISSING** | -- | -- |
| 51 | `dcg_admin_us_city` | character varying(255) | Y | **MISSING** | -- | -- |
| 52 | `dcg_admin_us_state` | character varying(10) | Y | **MISSING** | -- | -- |
| 53 | `dcg_admin_us_zip` | character varying(20) | Y | **MISSING** | -- | -- |
| 54 | `dcg_admin_foreign_address1` | character varying(500) | Y | **MISSING** | -- | -- |
| 55 | `dcg_admin_foreign_address2` | character varying(500) | Y | **MISSING** | -- | -- |
| 56 | `dcg_admin_foreign_city` | character varying(255) | Y | **MISSING** | -- | -- |
| 57 | `dcg_admin_foreign_prov_state` | character varying(100) | Y | **MISSING** | -- | -- |
| 58 | `dcg_admin_foreign_cntry` | character varying(100) | Y | **MISSING** | -- | -- |
| 59 | `dcg_admin_foreign_postal_cd` | character varying(50) | Y | **MISSING** | -- | -- |
| 60 | `dcg_admin_ein` | character varying(20) | Y | **MISSING** | -- | -- |
| 61 | `dcg_admin_phone_num` | character varying(30) | Y | **MISSING** | -- | -- |
| 62 | `dcg_admin_phone_num_foreign` | character varying(30) | Y | **MISSING** | -- | -- |
| 63 | `dcg_tot_partcp_boy_cnt` | numeric | Y | **MISSING** | -- | -- |
| 64 | `dcg_tot_act_rtd_sep_benef_cnt` | numeric | Y | **MISSING** | -- | -- |
| 65 | `dcg_tot_act_partcp_boy_cnt` | numeric | Y | **MISSING** | -- | -- |
| 66 | `dcg_tot_act_partcp_eoy_cnt` | numeric | Y | **MISSING** | -- | -- |
| 67 | `dcg_partcp_account_bal_boy_cnt` | numeric | Y | **MISSING** | -- | -- |
| 68 | `dcg_partcp_account_bal_eoy_cnt` | numeric | Y | **MISSING** | -- | -- |
| 69 | `dcg_sep_partcp_partl_vstd_cnt` | numeric | Y | **MISSING** | -- | -- |
| 70 | `dcg_tot_assets_boy_amt` | numeric | Y | **MISSING** | -- | -- |
| 71 | `dcg_partcp_loans_boy_amt` | numeric | Y | **MISSING** | -- | -- |
| 72 | `dcg_tot_liabilities_boy_amt` | numeric | Y | **MISSING** | -- | -- |
| 73 | `dcg_net_assets_boy_amt` | numeric | Y | **MISSING** | -- | -- |
| 74 | `dcg_tot_assets_eoy_amt` | numeric | Y | **MISSING** | -- | -- |
| 75 | `dcg_partcp_loans_eoy_amt` | numeric | Y | **MISSING** | -- | -- |
| 76 | `dcg_tot_liabilities_eoy_amt` | numeric | Y | **MISSING** | -- | -- |
| 77 | `dcg_net_assets_eoy_amt` | numeric | Y | **MISSING** | -- | -- |
| 78 | `dcg_emplr_contrib_income_amt` | numeric | Y | **MISSING** | -- | -- |
| 79 | `dcg_participant_contrib_income_amt` | numeric | Y | **MISSING** | -- | -- |
| 80 | `dcg_oth_contrib_rcvd_amt` | numeric | Y | **MISSING** | -- | -- |
| 81 | `dcg_non_cash_contrib_amt` | numeric | Y | **MISSING** | -- | -- |
| 82 | `dcg_tot_contrib_amt` | numeric | Y | **MISSING** | -- | -- |
| 83 | `dcg_other_income_amt` | numeric | Y | **MISSING** | -- | -- |
| 84 | `dcg_tot_income_amt` | numeric | Y | **MISSING** | -- | -- |
| 85 | `dcg_tot_bnft_amt` | numeric | Y | **MISSING** | -- | -- |
| 86 | `dcg_corrective_distrib_amt` | numeric | Y | **MISSING** | -- | -- |
| 87 | `dcg_deemed_distrib_partcp_lns_amt` | numeric | Y | **MISSING** | -- | -- |
| 88 | `dcg_admin_srvc_providers_amt` | numeric | Y | **MISSING** | -- | -- |
| 89 | `dcg_oth_expenses_amt` | numeric | Y | **MISSING** | -- | -- |
| 90 | `dcg_tot_expenses_amt` | numeric | Y | **MISSING** | -- | -- |
| 91 | `dcg_net_income_amt` | numeric | Y | **MISSING** | -- | -- |
| 92 | `dcg_tot_transfers_to_amt` | numeric | Y | **MISSING** | -- | -- |
| 93 | `dcg_tot_transfers_from_amt` | numeric | Y | **MISSING** | -- | -- |
| 94 | `dcg_type_pension_bnft_code` | character varying(50) | Y | **MISSING** | -- | -- |
| 95 | `dcg_fail_transmit_contrib_ind` | character varying(10) | Y | **MISSING** | -- | -- |
| 96 | `dcg_fail_transmit_contrib_amt` | numeric | Y | **MISSING** | -- | -- |
| 97 | `dcg_party_in_int_not_rptd_ind` | character varying(10) | Y | **MISSING** | -- | -- |
| 98 | `dcg_party_in_int_not_rptd_amt` | numeric | Y | **MISSING** | -- | -- |
| 99 | `dcg_fail_provide_benefit_due_ind` | character varying(10) | Y | **MISSING** | -- | -- |
| 100 | `dcg_fail_provide_benefit_due_amt` | numeric | Y | **MISSING** | -- | -- |
| 101 | `dcg_fidelity_bond_ind` | character varying(10) | Y | **MISSING** | -- | -- |
| 102 | `dcg_fidelity_bond_amt` | numeric | Y | **MISSING** | -- | -- |
| 103 | `dcg_loss_discv_dur_year_ind` | character varying(10) | Y | **MISSING** | -- | -- |
| 104 | `dcg_loss_discv_dur_year_amt` | numeric | Y | **MISSING** | -- | -- |
| 105 | `dcg_dc_plan_funding_reqd_ind` | character varying(10) | Y | **MISSING** | -- | -- |
| 106 | `dcg_plan_satisfy_tests_ind` | character varying(10) | Y | **MISSING** | -- | -- |
| 107 | `dcg_401k_design_based_safe_harbor_ind` | character varying(10) | Y | **MISSING** | -- | -- |
| 108 | `dcg_401k_prior_year_adp_test_ind` | character varying(10) | Y | **MISSING** | -- | -- |
| 109 | `dcg_401k_current_year_adp_test_ind` | character varying(10) | Y | **MISSING** | -- | -- |
| 110 | `dcg_401k_na_ind` | character varying(10) | Y | **MISSING** | -- | -- |
| 111 | `dcg_opin_letter_date` | character varying(30) | Y | **MISSING** | -- | -- |
| 112 | `dcg_opin_letter_serial_num` | character varying(50) | Y | **MISSING** | -- | -- |
| 113 | `dcg_iqpa_attached_ind` | character varying(10) | Y | **MISSING** | -- | -- |
| 114 | `dcg_acctnt_opinion_type_cd` | character varying(10) | Y | **MISSING** | -- | -- |
| 115 | `dcg_acct_performed_ltd_audit_103_8_ind` | character varying(10) | Y | **MISSING** | -- | -- |
| 116 | `dcg_acct_performed_ltd_audit_103_12d_ind` | character varying(10) | Y | **MISSING** | -- | -- |
| 117 | `dcg_acct_performed_not_ltd_audit_ind` | character varying(10) | Y | **MISSING** | -- | -- |
| 118 | `dcg_accountant_firm_name` | character varying(500) | Y | **MISSING** | -- | -- |
| 119 | `dcg_accountant_firm_ein` | character varying(20) | Y | **MISSING** | -- | -- |
| 120 | `form_year` | character varying(10) | Y | **MISSING** | -- | -- |
| 121 | `created_at` | timestamp with time zone | N | **MISSING** | -- | -- |

#### `dol.schedule_g` -- UNREGISTERED -- 568 rows

Column registry: **UNDOCUMENTED**

| # | Column | Type | Null | Description | Role | Format |
|---|--------|------|------|-------------|------|--------|
| 1 | `id` | bigint | N | **MISSING** | -- | -- |
| 2 | `ack_id` | character varying(50) | N | **MISSING** | -- | -- |
| 3 | `sch_g_plan_year_begin_date` | character varying(30) | Y | **MISSING** | -- | -- |
| 4 | `sch_g_tax_prd` | character varying(30) | Y | **MISSING** | -- | -- |
| 5 | `sch_g_pn` | character varying(10) | Y | **MISSING** | -- | -- |
| 6 | `sch_g_ein` | character varying(20) | Y | **MISSING** | -- | -- |
| 7 | `form_year` | character varying(10) | Y | **MISSING** | -- | -- |
| 8 | `created_at` | timestamp with time zone | N | **MISSING** | -- | -- |

#### `dol.schedule_g_part1` -- UNREGISTERED -- 784 rows

Column registry: **UNDOCUMENTED**

| # | Column | Type | Null | Description | Role | Format |
|---|--------|------|------|-------------|------|--------|
| 1 | `id` | bigint | N | **MISSING** | -- | -- |
| 2 | `ack_id` | character varying(50) | N | **MISSING** | -- | -- |
| 3 | `row_order` | integer | Y | **MISSING** | -- | -- |
| 4 | `lns_default_pii_ind` | character varying(10) | Y | **MISSING** | -- | -- |
| 5 | `lns_default_obligor_name` | character varying(500) | Y | **MISSING** | -- | -- |
| 6 | `lns_default_obligor_us_addr1` | character varying(500) | Y | **MISSING** | -- | -- |
| 7 | `lns_default_obligor_us_addr2` | character varying(500) | Y | **MISSING** | -- | -- |
| 8 | `lns_default_obligor_us_city` | character varying(255) | Y | **MISSING** | -- | -- |
| 9 | `lns_default_obligor_us_state` | character varying(10) | Y | **MISSING** | -- | -- |
| 10 | `lns_default_obligor_us_zip` | character varying(20) | Y | **MISSING** | -- | -- |
| 11 | `lns_dft_obligor_foreign_addr1` | character varying(500) | Y | **MISSING** | -- | -- |
| 12 | `lns_dft_obligor_foreign_addr2` | character varying(500) | Y | **MISSING** | -- | -- |
| 13 | `lns_dft_obligor_foreign_city` | character varying(255) | Y | **MISSING** | -- | -- |
| 14 | `lns_dft_obligor_forgn_prov_st` | character varying(100) | Y | **MISSING** | -- | -- |
| 15 | `lns_dft_obligor_forgn_country` | character varying(100) | Y | **MISSING** | -- | -- |
| 16 | `lns_dft_obligor_forgn_post_cd` | character varying(50) | Y | **MISSING** | -- | -- |
| 17 | `lns_default_description_text` | text | Y | **MISSING** | -- | -- |
| 18 | `lns_default_original_amt` | numeric | Y | **MISSING** | -- | -- |
| 19 | `lns_default_prncpl_rcvd_amt` | numeric | Y | **MISSING** | -- | -- |
| 20 | `lns_default_int_rcvd_amt` | numeric | Y | **MISSING** | -- | -- |
| 21 | `lns_default_unpaid_bal_amt` | numeric | Y | **MISSING** | -- | -- |
| 22 | `lns_default_prcpl_overdue_amt` | numeric | Y | **MISSING** | -- | -- |
| 23 | `lns_default_int_overdue_amt` | numeric | Y | **MISSING** | -- | -- |
| 24 | `form_year` | character varying(10) | Y | **MISSING** | -- | -- |
| 25 | `created_at` | timestamp with time zone | N | **MISSING** | -- | -- |

#### `dol.schedule_g_part2` -- UNREGISTERED -- 97 rows

Column registry: **UNDOCUMENTED**

| # | Column | Type | Null | Description | Role | Format |
|---|--------|------|------|-------------|------|--------|
| 1 | `id` | bigint | N | **MISSING** | -- | -- |
| 2 | `ack_id` | character varying(50) | N | **MISSING** | -- | -- |
| 3 | `row_order` | integer | Y | **MISSING** | -- | -- |
| 4 | `leases_default_pii_ind` | character varying(10) | Y | **MISSING** | -- | -- |
| 5 | `leases_default_lessor_name` | character varying(500) | Y | **MISSING** | -- | -- |
| 6 | `leases_default_relation_text` | text | Y | **MISSING** | -- | -- |
| 7 | `leases_default_terms_text` | text | Y | **MISSING** | -- | -- |
| 8 | `leases_default_cost_amt` | numeric | Y | **MISSING** | -- | -- |
| 9 | `leases_default_curr_value_amt` | numeric | Y | **MISSING** | -- | -- |
| 10 | `leases_default_rentl_rcpt_amt` | numeric | Y | **MISSING** | -- | -- |
| 11 | `leases_default_expense_pd_amt` | numeric | Y | **MISSING** | -- | -- |
| 12 | `leases_default_net_rcpt_amt` | numeric | Y | **MISSING** | -- | -- |
| 13 | `leases_default_arrears_amt` | numeric | Y | **MISSING** | -- | -- |
| 14 | `form_year` | character varying(10) | Y | **MISSING** | -- | -- |
| 15 | `created_at` | timestamp with time zone | N | **MISSING** | -- | -- |

#### `dol.schedule_g_part3` -- UNREGISTERED -- 469 rows

Column registry: **UNDOCUMENTED**

| # | Column | Type | Null | Description | Role | Format |
|---|--------|------|------|-------------|------|--------|
| 1 | `id` | bigint | N | **MISSING** | -- | -- |
| 2 | `ack_id` | character varying(50) | N | **MISSING** | -- | -- |
| 3 | `row_order` | integer | Y | **MISSING** | -- | -- |
| 4 | `non_exempt_party_name` | character varying(500) | Y | **MISSING** | -- | -- |
| 5 | `non_exempt_relation_text` | text | Y | **MISSING** | -- | -- |
| 6 | `non_exempt_terms_text` | text | Y | **MISSING** | -- | -- |
| 7 | `non_exempt_pur_price_amt` | numeric | Y | **MISSING** | -- | -- |
| 8 | `non_exempt_sell_price_amt` | numeric | Y | **MISSING** | -- | -- |
| 9 | `non_exempt_ls_rntl_amt` | numeric | Y | **MISSING** | -- | -- |
| 10 | `non_exempt_expense_incr_amt` | numeric | Y | **MISSING** | -- | -- |
| 11 | `non_exempt_cost_ast_amt` | numeric | Y | **MISSING** | -- | -- |
| 12 | `non_exempt_curr_value_ast_amt` | numeric | Y | **MISSING** | -- | -- |
| 13 | `non_exempt_gain_loss_amt` | numeric | Y | **MISSING** | -- | -- |
| 14 | `form_year` | character varying(10) | Y | **MISSING** | -- | -- |
| 15 | `created_at` | timestamp with time zone | N | **MISSING** | -- | -- |

#### `dol.schedule_h` -- UNREGISTERED -- 169,276 rows

Column registry: **UNDOCUMENTED**

| # | Column | Type | Null | Description | Role | Format |
|---|--------|------|------|-------------|------|--------|
| 1 | `id` | bigint | N | **MISSING** | -- | -- |
| 2 | `ack_id` | character varying(50) | N | **MISSING** | -- | -- |
| 3 | `sch_h_plan_year_begin_date` | character varying(30) | Y | **MISSING** | -- | -- |
| 4 | `sch_h_tax_prd` | character varying(30) | Y | **MISSING** | -- | -- |
| 5 | `sch_h_pn` | character varying(10) | Y | **MISSING** | -- | -- |
| 6 | `sch_h_ein` | character varying(20) | Y | **MISSING** | -- | -- |
| 7 | `non_int_bear_cash_boy_amt` | numeric | Y | **MISSING** | -- | -- |
| 8 | `emplr_contrib_boy_amt` | numeric | Y | **MISSING** | -- | -- |
| 9 | `partcp_contrib_boy_amt` | numeric | Y | **MISSING** | -- | -- |
| 10 | `other_receivables_boy_amt` | numeric | Y | **MISSING** | -- | -- |
| 11 | `int_bear_cash_boy_amt` | numeric | Y | **MISSING** | -- | -- |
| 12 | `govt_sec_boy_amt` | numeric | Y | **MISSING** | -- | -- |
| 13 | `corp_debt_preferred_boy_amt` | numeric | Y | **MISSING** | -- | -- |
| 14 | `corp_debt_other_boy_amt` | numeric | Y | **MISSING** | -- | -- |
| 15 | `pref_stock_boy_amt` | numeric | Y | **MISSING** | -- | -- |
| 16 | `common_stock_boy_amt` | numeric | Y | **MISSING** | -- | -- |
| 17 | `joint_venture_boy_amt` | numeric | Y | **MISSING** | -- | -- |
| 18 | `real_estate_boy_amt` | numeric | Y | **MISSING** | -- | -- |
| 19 | `other_loans_boy_amt` | numeric | Y | **MISSING** | -- | -- |
| 20 | `partcp_loans_boy_amt` | numeric | Y | **MISSING** | -- | -- |
| 21 | `int_common_tr_boy_amt` | numeric | Y | **MISSING** | -- | -- |
| 22 | `int_pool_sep_acct_boy_amt` | numeric | Y | **MISSING** | -- | -- |
| 23 | `int_master_tr_boy_amt` | numeric | Y | **MISSING** | -- | -- |
| 24 | `int_103_12_invst_boy_amt` | numeric | Y | **MISSING** | -- | -- |
| 25 | `int_reg_invst_co_boy_amt` | numeric | Y | **MISSING** | -- | -- |
| 26 | `ins_co_gen_acct_boy_amt` | numeric | Y | **MISSING** | -- | -- |
| 27 | `oth_invst_boy_amt` | numeric | Y | **MISSING** | -- | -- |
| 28 | `emplr_sec_boy_amt` | numeric | Y | **MISSING** | -- | -- |
| 29 | `emplr_prop_boy_amt` | numeric | Y | **MISSING** | -- | -- |
| 30 | `bldgs_used_boy_amt` | numeric | Y | **MISSING** | -- | -- |
| 31 | `tot_assets_boy_amt` | numeric | Y | **MISSING** | -- | -- |
| 32 | `bnfts_payable_boy_amt` | numeric | Y | **MISSING** | -- | -- |
| 33 | `oprtng_payable_boy_amt` | numeric | Y | **MISSING** | -- | -- |
| 34 | `acquis_indbt_boy_amt` | numeric | Y | **MISSING** | -- | -- |
| 35 | `other_liab_boy_amt` | numeric | Y | **MISSING** | -- | -- |
| 36 | `tot_liabilities_boy_amt` | numeric | Y | **MISSING** | -- | -- |
| 37 | `net_assets_boy_amt` | numeric | Y | **MISSING** | -- | -- |
| 38 | `non_int_bear_cash_eoy_amt` | numeric | Y | **MISSING** | -- | -- |
| 39 | `emplr_contrib_eoy_amt` | numeric | Y | **MISSING** | -- | -- |
| 40 | `partcp_contrib_eoy_amt` | numeric | Y | **MISSING** | -- | -- |
| 41 | `other_receivables_eoy_amt` | numeric | Y | **MISSING** | -- | -- |
| 42 | `int_bear_cash_eoy_amt` | numeric | Y | **MISSING** | -- | -- |
| 43 | `govt_sec_eoy_amt` | numeric | Y | **MISSING** | -- | -- |
| 44 | `corp_debt_preferred_eoy_amt` | numeric | Y | **MISSING** | -- | -- |
| 45 | `corp_debt_other_eoy_amt` | numeric | Y | **MISSING** | -- | -- |
| 46 | `pref_stock_eoy_amt` | numeric | Y | **MISSING** | -- | -- |
| 47 | `common_stock_eoy_amt` | numeric | Y | **MISSING** | -- | -- |
| 48 | `joint_venture_eoy_amt` | numeric | Y | **MISSING** | -- | -- |
| 49 | `real_estate_eoy_amt` | numeric | Y | **MISSING** | -- | -- |
| 50 | `other_loans_eoy_amt` | numeric | Y | **MISSING** | -- | -- |
| 51 | `partcp_loans_eoy_amt` | numeric | Y | **MISSING** | -- | -- |
| 52 | `int_common_tr_eoy_amt` | numeric | Y | **MISSING** | -- | -- |
| 53 | `int_pool_sep_acct_eoy_amt` | numeric | Y | **MISSING** | -- | -- |
| 54 | `int_master_tr_eoy_amt` | numeric | Y | **MISSING** | -- | -- |
| 55 | `int_103_12_invst_eoy_amt` | numeric | Y | **MISSING** | -- | -- |
| 56 | `int_reg_invst_co_eoy_amt` | numeric | Y | **MISSING** | -- | -- |
| 57 | `ins_co_gen_acct_eoy_amt` | numeric | Y | **MISSING** | -- | -- |
| 58 | `oth_invst_eoy_amt` | numeric | Y | **MISSING** | -- | -- |
| 59 | `emplr_sec_eoy_amt` | numeric | Y | **MISSING** | -- | -- |
| 60 | `emplr_prop_eoy_amt` | numeric | Y | **MISSING** | -- | -- |
| 61 | `bldgs_used_eoy_amt` | numeric | Y | **MISSING** | -- | -- |
| 62 | `tot_assets_eoy_amt` | numeric | Y | **MISSING** | -- | -- |
| 63 | `bnfts_payable_eoy_amt` | numeric | Y | **MISSING** | -- | -- |
| 64 | `oprtng_payable_eoy_amt` | numeric | Y | **MISSING** | -- | -- |
| 65 | `acquis_indbt_eoy_amt` | numeric | Y | **MISSING** | -- | -- |
| 66 | `other_liab_eoy_amt` | numeric | Y | **MISSING** | -- | -- |
| 67 | `tot_liabilities_eoy_amt` | numeric | Y | **MISSING** | -- | -- |
| 68 | `net_assets_eoy_amt` | numeric | Y | **MISSING** | -- | -- |
| 69 | `emplr_contrib_income_amt` | numeric | Y | **MISSING** | -- | -- |
| 70 | `participant_contrib_amt` | numeric | Y | **MISSING** | -- | -- |
| 71 | `oth_contrib_rcvd_amt` | numeric | Y | **MISSING** | -- | -- |
| 72 | `non_cash_contrib_bs_amt` | numeric | Y | **MISSING** | -- | -- |
| 73 | `tot_contrib_amt` | numeric | Y | **MISSING** | -- | -- |
| 74 | `int_bear_cash_amt` | numeric | Y | **MISSING** | -- | -- |
| 75 | `int_on_govt_sec_amt` | numeric | Y | **MISSING** | -- | -- |
| 76 | `int_on_corp_debt_amt` | numeric | Y | **MISSING** | -- | -- |
| 77 | `int_on_oth_loans_amt` | numeric | Y | **MISSING** | -- | -- |
| 78 | `int_on_partcp_loans_amt` | numeric | Y | **MISSING** | -- | -- |
| 79 | `int_on_oth_invst_amt` | numeric | Y | **MISSING** | -- | -- |
| 80 | `total_interest_amt` | numeric | Y | **MISSING** | -- | -- |
| 81 | `divnd_pref_stock_amt` | numeric | Y | **MISSING** | -- | -- |
| 82 | `divnd_common_stock_amt` | numeric | Y | **MISSING** | -- | -- |
| 83 | `registered_invst_amt` | numeric | Y | **MISSING** | -- | -- |
| 84 | `total_dividends_amt` | numeric | Y | **MISSING** | -- | -- |
| 85 | `total_rents_amt` | numeric | Y | **MISSING** | -- | -- |
| 86 | `aggregate_proceeds_amt` | numeric | Y | **MISSING** | -- | -- |
| 87 | `aggregate_costs_amt` | numeric | Y | **MISSING** | -- | -- |
| 88 | `tot_gain_loss_sale_ast_amt` | numeric | Y | **MISSING** | -- | -- |
| 89 | `unrealzd_apprctn_re_amt` | numeric | Y | **MISSING** | -- | -- |
| 90 | `unrealzd_apprctn_oth_amt` | numeric | Y | **MISSING** | -- | -- |
| 91 | `tot_unrealzd_apprctn_amt` | numeric | Y | **MISSING** | -- | -- |
| 92 | `gain_loss_com_trust_amt` | numeric | Y | **MISSING** | -- | -- |
| 93 | `gain_loss_pool_sep_amt` | numeric | Y | **MISSING** | -- | -- |
| 94 | `gain_loss_master_tr_amt` | numeric | Y | **MISSING** | -- | -- |
| 95 | `gain_loss_103_12_invst_amt` | numeric | Y | **MISSING** | -- | -- |
| 96 | `gain_loss_reg_invst_amt` | numeric | Y | **MISSING** | -- | -- |
| 97 | `other_income_amt` | numeric | Y | **MISSING** | -- | -- |
| 98 | `tot_income_amt` | numeric | Y | **MISSING** | -- | -- |
| 99 | `distrib_drt_partcp_amt` | numeric | Y | **MISSING** | -- | -- |
| 100 | `ins_carrier_bnfts_amt` | numeric | Y | **MISSING** | -- | -- |
| 101 | `oth_bnft_payment_amt` | numeric | Y | **MISSING** | -- | -- |
| 102 | `tot_distrib_bnft_amt` | numeric | Y | **MISSING** | -- | -- |
| 103 | `tot_corrective_distrib_amt` | numeric | Y | **MISSING** | -- | -- |
| 104 | `tot_deemed_distr_part_lns_amt` | numeric | Y | **MISSING** | -- | -- |
| 105 | `tot_int_expense_amt` | numeric | Y | **MISSING** | -- | -- |
| 106 | `professional_fees_amt` | numeric | Y | **MISSING** | -- | -- |
| 107 | `contract_admin_fees_amt` | numeric | Y | **MISSING** | -- | -- |
| 108 | `invst_mgmt_fees_amt` | numeric | Y | **MISSING** | -- | -- |
| 109 | `other_admin_fees_amt` | numeric | Y | **MISSING** | -- | -- |
| 110 | `tot_admin_expenses_amt` | numeric | Y | **MISSING** | -- | -- |
| 111 | `tot_expenses_amt` | numeric | Y | **MISSING** | -- | -- |
| 112 | `net_income_amt` | numeric | Y | **MISSING** | -- | -- |
| 113 | `tot_transfers_to_amt` | numeric | Y | **MISSING** | -- | -- |
| 114 | `tot_transfers_from_amt` | numeric | Y | **MISSING** | -- | -- |
| 115 | `acctnt_opinion_type_cd` | character varying(10) | Y | **MISSING** | -- | -- |
| 116 | `acct_performed_ltd_audit_ind` | character varying(10) | Y | **MISSING** | -- | -- |
| 117 | `accountant_firm_name` | character varying(500) | Y | **MISSING** | -- | -- |
| 118 | `accountant_firm_ein` | character varying(20) | Y | **MISSING** | -- | -- |
| 119 | `acct_opin_not_on_file_ind` | character varying(10) | Y | **MISSING** | -- | -- |
| 120 | `fail_transmit_contrib_ind` | character varying(10) | Y | **MISSING** | -- | -- |
| 121 | `fail_transmit_contrib_amt` | numeric | Y | **MISSING** | -- | -- |
| 122 | `loans_in_default_ind` | character varying(10) | Y | **MISSING** | -- | -- |
| 123 | `loans_in_default_amt` | numeric | Y | **MISSING** | -- | -- |
| 124 | `leases_in_default_ind` | character varying(10) | Y | **MISSING** | -- | -- |
| 125 | `leases_in_default_amt` | numeric | Y | **MISSING** | -- | -- |
| 126 | `party_in_int_not_rptd_ind` | character varying(10) | Y | **MISSING** | -- | -- |
| 127 | `party_in_int_not_rptd_amt` | numeric | Y | **MISSING** | -- | -- |
| 128 | `plan_ins_fdlty_bond_ind` | character varying(10) | Y | **MISSING** | -- | -- |
| 129 | `plan_ins_fdlty_bond_amt` | numeric | Y | **MISSING** | -- | -- |
| 130 | `loss_discv_dur_year_ind` | character varying(10) | Y | **MISSING** | -- | -- |
| 131 | `loss_discv_dur_year_amt` | numeric | Y | **MISSING** | -- | -- |
| 132 | `asset_undeterm_val_ind` | character varying(10) | Y | **MISSING** | -- | -- |
| 133 | `asset_undeterm_val_amt` | numeric | Y | **MISSING** | -- | -- |
| 134 | `non_cash_contrib_ind` | character varying(10) | Y | **MISSING** | -- | -- |
| 135 | `non_cash_contrib_amt` | numeric | Y | **MISSING** | -- | -- |
| 136 | `ast_held_invst_ind` | character varying(10) | Y | **MISSING** | -- | -- |
| 137 | `five_prcnt_trans_ind` | character varying(10) | Y | **MISSING** | -- | -- |
| 138 | `all_plan_ast_distrib_ind` | character varying(10) | Y | **MISSING** | -- | -- |
| 139 | `fail_provide_benefit_due_ind` | character varying(10) | Y | **MISSING** | -- | -- |
| 140 | `fail_provide_benefit_due_amt` | numeric | Y | **MISSING** | -- | -- |
| 141 | `plan_blackout_period_ind` | character varying(10) | Y | **MISSING** | -- | -- |
| 142 | `comply_blackout_notice_ind` | character varying(10) | Y | **MISSING** | -- | -- |
| 143 | `res_term_plan_adpt_ind` | character varying(10) | Y | **MISSING** | -- | -- |
| 144 | `res_term_plan_adpt_amt` | numeric | Y | **MISSING** | -- | -- |
| 145 | `fdcry_trust_ein` | character varying(20) | Y | **MISSING** | -- | -- |
| 146 | `fdcry_trust_name` | character varying(500) | Y | **MISSING** | -- | -- |
| 147 | `covered_pbgc_insurance_ind` | character varying(10) | Y | **MISSING** | -- | -- |
| 148 | `trust_incur_unrel_tax_inc_ind` | character varying(10) | Y | **MISSING** | -- | -- |
| 149 | `trust_incur_unrel_tax_inc_amt` | numeric | Y | **MISSING** | -- | -- |
| 150 | `in_service_distrib_ind` | character varying(10) | Y | **MISSING** | -- | -- |
| 151 | `in_service_distrib_amt` | numeric | Y | **MISSING** | -- | -- |
| 152 | `fdcry_trustee_cust_name` | character varying(500) | Y | **MISSING** | -- | -- |
| 153 | `fdcry_trust_cust_phon_num` | character varying(30) | Y | **MISSING** | -- | -- |
| 154 | `fdcry_trust_cust_phon_nu_fore` | character varying(30) | Y | **MISSING** | -- | -- |
| 155 | `distrib_made_employee_62_ind` | character varying(10) | Y | **MISSING** | -- | -- |
| 156 | `premium_filing_confirm_number` | character varying(50) | Y | **MISSING** | -- | -- |
| 157 | `acct_perf_ltd_audit_103_8_ind` | character varying(10) | Y | **MISSING** | -- | -- |
| 158 | `acct_perf_ltd_audit_103_12_ind` | character varying(10) | Y | **MISSING** | -- | -- |
| 159 | `acct_perf_not_ltd_audit_ind` | character varying(10) | Y | **MISSING** | -- | -- |
| 160 | `salaries_allowances_amt` | numeric | Y | **MISSING** | -- | -- |
| 161 | `oth_recordkeeping_fees_amt` | numeric | Y | **MISSING** | -- | -- |
| 162 | `iqpa_audit_fees_amt` | numeric | Y | **MISSING** | -- | -- |
| 163 | `trustee_custodial_fees_amt` | numeric | Y | **MISSING** | -- | -- |
| 164 | `actuarial_fees_amt` | numeric | Y | **MISSING** | -- | -- |
| 165 | `legal_fees_amt` | numeric | Y | **MISSING** | -- | -- |
| 166 | `valuation_appraisal_fees_amt` | numeric | Y | **MISSING** | -- | -- |
| 167 | `other_trustee_fees_expenses_amt` | numeric | Y | **MISSING** | -- | -- |
| 168 | `form_year` | character varying(10) | Y | **MISSING** | -- | -- |
| 169 | `created_at` | timestamp with time zone | N | **MISSING** | -- | -- |

#### `dol.schedule_h_part1` -- UNREGISTERED -- 20,359 rows

Column registry: **UNDOCUMENTED**

| # | Column | Type | Null | Description | Role | Format |
|---|--------|------|------|-------------|------|--------|
| 1 | `id` | bigint | N | **MISSING** | -- | -- |
| 2 | `ack_id` | character varying(50) | N | **MISSING** | -- | -- |
| 3 | `row_order` | integer | Y | **MISSING** | -- | -- |
| 4 | `plan_transfer_name` | character varying(500) | Y | **MISSING** | -- | -- |
| 5 | `plan_transfer_ein` | character varying(20) | Y | **MISSING** | -- | -- |
| 6 | `plan_transfer_pn` | character varying(10) | Y | **MISSING** | -- | -- |
| 7 | `form_year` | character varying(10) | Y | **MISSING** | -- | -- |
| 8 | `created_at` | timestamp with time zone | N | **MISSING** | -- | -- |

#### `dol.schedule_i` -- UNREGISTERED -- 116,493 rows

Column registry: **UNDOCUMENTED**

| # | Column | Type | Null | Description | Role | Format |
|---|--------|------|------|-------------|------|--------|
| 1 | `id` | bigint | N | **MISSING** | -- | -- |
| 2 | `ack_id` | character varying(50) | N | **MISSING** | -- | -- |
| 3 | `sch_i_plan_year_begin_date` | character varying(30) | Y | **MISSING** | -- | -- |
| 4 | `sch_i_tax_prd` | character varying(30) | Y | **MISSING** | -- | -- |
| 5 | `sch_i_plan_num` | character varying(10) | Y | **MISSING** | -- | -- |
| 6 | `sch_i_ein` | character varying(20) | Y | **MISSING** | -- | -- |
| 7 | `small_tot_assets_boy_amt` | numeric | Y | **MISSING** | -- | -- |
| 8 | `small_tot_liabilities_boy_amt` | numeric | Y | **MISSING** | -- | -- |
| 9 | `small_net_assets_boy_amt` | numeric | Y | **MISSING** | -- | -- |
| 10 | `small_tot_assets_eoy_amt` | numeric | Y | **MISSING** | -- | -- |
| 11 | `small_tot_liabilities_eoy_amt` | numeric | Y | **MISSING** | -- | -- |
| 12 | `small_net_assets_eoy_amt` | numeric | Y | **MISSING** | -- | -- |
| 13 | `small_emplr_contrib_income_amt` | numeric | Y | **MISSING** | -- | -- |
| 14 | `small_participant_contrib_amt` | numeric | Y | **MISSING** | -- | -- |
| 15 | `small_oth_contrib_rcvd_amt` | numeric | Y | **MISSING** | -- | -- |
| 16 | `small_non_cash_contrib_bs_amt` | numeric | Y | **MISSING** | -- | -- |
| 17 | `small_other_income_amt` | numeric | Y | **MISSING** | -- | -- |
| 18 | `small_tot_income_amt` | numeric | Y | **MISSING** | -- | -- |
| 19 | `small_tot_distrib_bnft_amt` | numeric | Y | **MISSING** | -- | -- |
| 20 | `small_corrective_distrib_amt` | numeric | Y | **MISSING** | -- | -- |
| 21 | `small_deem_dstrb_partcp_ln_amt` | numeric | Y | **MISSING** | -- | -- |
| 22 | `small_admin_srvc_providers_amt` | numeric | Y | **MISSING** | -- | -- |
| 23 | `small_oth_expenses_amt` | numeric | Y | **MISSING** | -- | -- |
| 24 | `small_tot_expenses_amt` | numeric | Y | **MISSING** | -- | -- |
| 25 | `small_net_income_amt` | numeric | Y | **MISSING** | -- | -- |
| 26 | `small_tot_plan_transfers_amt` | numeric | Y | **MISSING** | -- | -- |
| 27 | `small_joint_venture_eoy_ind` | character varying(10) | Y | **MISSING** | -- | -- |
| 28 | `small_joint_venture_eoy_amt` | numeric | Y | **MISSING** | -- | -- |
| 29 | `small_emplr_prop_eoy_ind` | character varying(10) | Y | **MISSING** | -- | -- |
| 30 | `small_emplr_prop_eoy_amt` | numeric | Y | **MISSING** | -- | -- |
| 31 | `small_inv_real_estate_eoy_ind` | character varying(10) | Y | **MISSING** | -- | -- |
| 32 | `small_inv_real_estate_eoy_amt` | numeric | Y | **MISSING** | -- | -- |
| 33 | `small_emplr_sec_eoy_ind` | character varying(10) | Y | **MISSING** | -- | -- |
| 34 | `small_emplr_sec_eoy_amt` | numeric | Y | **MISSING** | -- | -- |
| 35 | `small_mortg_partcp_eoy_ind` | character varying(10) | Y | **MISSING** | -- | -- |
| 36 | `small_mortg_partcp_eoy_amt` | numeric | Y | **MISSING** | -- | -- |
| 37 | `small_oth_lns_partcp_eoy_ind` | character varying(10) | Y | **MISSING** | -- | -- |
| 38 | `small_oth_lns_partcp_eoy_amt` | numeric | Y | **MISSING** | -- | -- |
| 39 | `small_personal_prop_eoy_ind` | character varying(10) | Y | **MISSING** | -- | -- |
| 40 | `small_personal_prop_eoy_amt` | numeric | Y | **MISSING** | -- | -- |
| 41 | `small_fail_transm_contrib_ind` | character varying(10) | Y | **MISSING** | -- | -- |
| 42 | `small_fail_transm_contrib_amt` | numeric | Y | **MISSING** | -- | -- |
| 43 | `small_loans_in_default_ind` | character varying(10) | Y | **MISSING** | -- | -- |
| 44 | `small_loans_in_default_amt` | numeric | Y | **MISSING** | -- | -- |
| 45 | `small_leases_in_default_ind` | character varying(10) | Y | **MISSING** | -- | -- |
| 46 | `small_leases_in_default_amt` | numeric | Y | **MISSING** | -- | -- |
| 47 | `sm_party_in_int_not_rptd_ind` | character varying(10) | Y | **MISSING** | -- | -- |
| 48 | `sm_party_in_int_not_rptd_amt` | numeric | Y | **MISSING** | -- | -- |
| 49 | `small_plan_ins_fdlty_bond_ind` | character varying(10) | Y | **MISSING** | -- | -- |
| 50 | `small_plan_ins_fdlty_bond_amt` | numeric | Y | **MISSING** | -- | -- |
| 51 | `small_loss_discv_dur_year_ind` | character varying(10) | Y | **MISSING** | -- | -- |
| 52 | `small_loss_discv_dur_year_amt` | numeric | Y | **MISSING** | -- | -- |
| 53 | `small_asset_undeterm_val_ind` | character varying(10) | Y | **MISSING** | -- | -- |
| 54 | `small_asset_undeterm_val_amt` | numeric | Y | **MISSING** | -- | -- |
| 55 | `small_non_cash_contrib_ind` | character varying(10) | Y | **MISSING** | -- | -- |
| 56 | `small_non_cash_contrib_amt` | numeric | Y | **MISSING** | -- | -- |
| 57 | `small_20_prcnt_sngl_invst_ind` | character varying(10) | Y | **MISSING** | -- | -- |
| 58 | `small_20_prcnt_sngl_invst_amt` | numeric | Y | **MISSING** | -- | -- |
| 59 | `small_all_plan_ast_distrib_ind` | character varying(10) | Y | **MISSING** | -- | -- |
| 60 | `sm_waiv_annual_iqpa_report_ind` | character varying(10) | Y | **MISSING** | -- | -- |
| 61 | `sm_fail_provide_benef_due_ind` | character varying(10) | Y | **MISSING** | -- | -- |
| 62 | `sm_fail_provide_benef_due_amt` | numeric | Y | **MISSING** | -- | -- |
| 63 | `small_plan_blackout_period_ind` | character varying(10) | Y | **MISSING** | -- | -- |
| 64 | `sm_comply_blackout_notice_ind` | character varying(10) | Y | **MISSING** | -- | -- |
| 65 | `small_res_term_plan_adpt_ind` | character varying(10) | Y | **MISSING** | -- | -- |
| 66 | `small_res_term_plan_adpt_amt` | numeric | Y | **MISSING** | -- | -- |
| 67 | `fdcry_trust_ein` | character varying(20) | Y | **MISSING** | -- | -- |
| 68 | `fdcry_trust_name` | character varying(500) | Y | **MISSING** | -- | -- |
| 69 | `small_covered_pbgc_ins_ind` | character varying(10) | Y | **MISSING** | -- | -- |
| 70 | `trust_incur_unrel_tax_inc_ind` | character varying(10) | Y | **MISSING** | -- | -- |
| 71 | `trust_incur_unrel_tax_inc_amt` | numeric | Y | **MISSING** | -- | -- |
| 72 | `in_service_distrib_ind` | character varying(10) | Y | **MISSING** | -- | -- |
| 73 | `in_service_distrib_amt` | numeric | Y | **MISSING** | -- | -- |
| 74 | `fdcry_trustee_cust_name` | character varying(500) | Y | **MISSING** | -- | -- |
| 75 | `fdcry_trust_cust_phone_num` | character varying(30) | Y | **MISSING** | -- | -- |
| 76 | `fdcry_trust_cust_phon_nu_fore` | character varying(30) | Y | **MISSING** | -- | -- |
| 77 | `distrib_made_employee_62_ind` | character varying(10) | Y | **MISSING** | -- | -- |
| 78 | `premium_filing_confirm_number` | character varying(50) | Y | **MISSING** | -- | -- |
| 79 | `form_year` | character varying(10) | Y | **MISSING** | -- | -- |
| 80 | `created_at` | timestamp with time zone | N | **MISSING** | -- | -- |

#### `dol.schedule_i_part1` -- UNREGISTERED -- 944 rows

Column registry: **UNDOCUMENTED**

| # | Column | Type | Null | Description | Role | Format |
|---|--------|------|------|-------------|------|--------|
| 1 | `id` | bigint | N | **MISSING** | -- | -- |
| 2 | `ack_id` | character varying(50) | N | **MISSING** | -- | -- |
| 3 | `row_order` | integer | Y | **MISSING** | -- | -- |
| 4 | `small_plan_transfer_name` | character varying(500) | Y | **MISSING** | -- | -- |
| 5 | `small_plan_transfer_ein` | character varying(20) | Y | **MISSING** | -- | -- |
| 6 | `small_plan_transfer_pn` | character varying(10) | Y | **MISSING** | -- | -- |
| 7 | `form_year` | character varying(10) | Y | **MISSING** | -- | -- |
| 8 | `created_at` | timestamp with time zone | N | **MISSING** | -- | -- |

### `enrichment` -- Enrichment Sources -- Hunter.io company and contact data (system reference)

**Tables**: 3 | **Total rows**: 672,187
**Views**: 4 -- v_column_metadata, v_hunter_company_sources, v_hunter_contact_sources, v_hunter_sources_by_type

| Table | Leaf Type | Frozen | Rows | Columns | Documented |
|-------|-----------|--------|------|---------|------------|
| `column_registry` | SYSTEM |  | 53 | 12 | 0 |
| `hunter_company` | SYSTEM |  | 88,554 | 26 | 0 |
| `hunter_contact` | SYSTEM |  | 583,580 | 59 | 0 |

#### `enrichment.column_registry` -- SYSTEM -- 53 rows

Column registry: **UNDOCUMENTED**

| # | Column | Type | Null | Description | Role | Format |
|---|--------|------|------|-------------|------|--------|
| 1 | `id` | integer | N | **MISSING** | -- | -- |
| 2 | `table_name` | character varying(100) | N | **MISSING** | -- | -- |
| 3 | `column_name` | character varying(100) | N | **MISSING** | -- | -- |
| 4 | `column_id` | character varying(50) | N | **MISSING** | -- | -- |
| 5 | `data_type` | character varying(50) | N | **MISSING** | -- | -- |
| 6 | `format_pattern` | character varying(255) | Y | **MISSING** | -- | -- |
| 7 | `description` | text | N | **MISSING** | -- | -- |
| 8 | `example_value` | text | Y | **MISSING** | -- | -- |
| 9 | `is_required` | boolean | Y | **MISSING** | -- | -- |
| 10 | `is_pii` | boolean | Y | **MISSING** | -- | -- |
| 11 | `ai_usage_hint` | text | Y | **MISSING** | -- | -- |
| 12 | `created_at` | timestamp without time zone | Y | **MISSING** | -- | -- |

#### `enrichment.hunter_company` -- SYSTEM -- 88,554 rows

Column registry: **UNDOCUMENTED**

| # | Column | Type | Null | Description | Role | Format |
|---|--------|------|------|-------------|------|--------|
| 1 | `id` | integer | N | **MISSING** | -- | -- |
| 2 | `domain` | character varying(255) | N | **MISSING** | -- | -- |
| 3 | `organization` | character varying(500) | Y | **MISSING** | -- | -- |
| 4 | `headcount` | character varying(50) | Y | **MISSING** | -- | -- |
| 5 | `country` | character varying(10) | Y | **MISSING** | -- | -- |
| 6 | `state` | character varying(50) | Y | **MISSING** | -- | -- |
| 7 | `city` | character varying(100) | Y | **MISSING** | -- | -- |
| 8 | `postal_code` | character varying(20) | Y | **MISSING** | -- | -- |
| 9 | `street` | character varying(255) | Y | **MISSING** | -- | -- |
| 10 | `email_pattern` | character varying(100) | Y | **MISSING** | -- | -- |
| 11 | `company_type` | character varying(100) | Y | **MISSING** | -- | -- |
| 12 | `industry` | character varying(255) | Y | **MISSING** | -- | -- |
| 13 | `enriched_at` | timestamp without time zone | Y | **MISSING** | -- | -- |
| 14 | `created_at` | timestamp without time zone | Y | **MISSING** | -- | -- |
| 15 | `updated_at` | timestamp without time zone | Y | **MISSING** | -- | -- |
| 16 | `company_embedding` | USER-DEFINED | Y | **MISSING** | -- | -- |
| 17 | `industry_normalized` | character varying(100) | Y | **MISSING** | -- | -- |
| 18 | `headcount_min` | integer | Y | **MISSING** | -- | -- |
| 19 | `headcount_max` | integer | Y | **MISSING** | -- | -- |
| 20 | `location_full` | text | Y | **MISSING** | -- | -- |
| 21 | `data_quality_score` | numeric | Y | **MISSING** | -- | -- |
| 22 | `tags` | ARRAY | Y | **MISSING** | -- | -- |
| 23 | `source` | character varying(50) | Y | **MISSING** | -- | -- |
| 24 | `company_unique_id` | character varying(50) | Y | **MISSING** | -- | -- |
| 25 | `outreach_id` | uuid | Y | **MISSING** | -- | -- |
| 26 | `source_file` | character varying(255) | Y | **MISSING** | -- | -- |

#### `enrichment.hunter_contact` -- SYSTEM -- 583,580 rows

Column registry: **UNDOCUMENTED**

| # | Column | Type | Null | Description | Role | Format |
|---|--------|------|------|-------------|------|--------|
| 1 | `id` | integer | N | **MISSING** | -- | -- |
| 2 | `domain` | character varying(255) | N | **MISSING** | -- | -- |
| 3 | `email` | character varying(255) | Y | **MISSING** | -- | -- |
| 4 | `first_name` | character varying(100) | Y | **MISSING** | -- | -- |
| 5 | `last_name` | character varying(100) | Y | **MISSING** | -- | -- |
| 6 | `department` | character varying(100) | Y | **MISSING** | -- | -- |
| 7 | `job_title` | character varying(255) | Y | **MISSING** | -- | -- |
| 8 | `position_raw` | character varying(500) | Y | **MISSING** | -- | -- |
| 9 | `linkedin_url` | character varying(500) | Y | **MISSING** | -- | -- |
| 10 | `twitter_handle` | character varying(100) | Y | **MISSING** | -- | -- |
| 11 | `phone_number` | character varying(50) | Y | **MISSING** | -- | -- |
| 12 | `confidence_score` | integer | Y | **MISSING** | -- | -- |
| 13 | `email_type` | character varying(20) | Y | **MISSING** | -- | -- |
| 14 | `num_sources` | integer | Y | **MISSING** | -- | -- |
| 15 | `created_at` | timestamp without time zone | Y | **MISSING** | -- | -- |
| 16 | `contact_embedding` | USER-DEFINED | Y | **MISSING** | -- | -- |
| 17 | `title_normalized` | character varying(100) | Y | **MISSING** | -- | -- |
| 18 | `seniority_level` | character varying(50) | Y | **MISSING** | -- | -- |
| 19 | `department_normalized` | character varying(50) | Y | **MISSING** | -- | -- |
| 20 | `is_decision_maker` | boolean | Y | **MISSING** | -- | -- |
| 21 | `full_name` | character varying(200) | Y | **MISSING** | -- | -- |
| 22 | `email_verified` | boolean | Y | **MISSING** | -- | -- |
| 23 | `data_quality_score` | numeric | Y | **MISSING** | -- | -- |
| 24 | `outreach_priority` | integer | Y | **MISSING** | -- | -- |
| 25 | `tags` | ARRAY | Y | **MISSING** | -- | -- |
| 26 | `source` | character varying(50) | Y | **MISSING** | -- | -- |
| 27 | `company_unique_id` | character varying(50) | Y | **MISSING** | -- | -- |
| 28 | `outreach_id` | uuid | Y | **MISSING** | -- | -- |
| 29 | `source_1` | text | Y | **MISSING** | -- | -- |
| 30 | `source_2` | text | Y | **MISSING** | -- | -- |
| 31 | `source_3` | text | Y | **MISSING** | -- | -- |
| 32 | `source_4` | text | Y | **MISSING** | -- | -- |
| 33 | `source_5` | text | Y | **MISSING** | -- | -- |
| 34 | `source_6` | text | Y | **MISSING** | -- | -- |
| 35 | `source_7` | text | Y | **MISSING** | -- | -- |
| 36 | `source_8` | text | Y | **MISSING** | -- | -- |
| 37 | `source_9` | text | Y | **MISSING** | -- | -- |
| 38 | `source_10` | text | Y | **MISSING** | -- | -- |
| 39 | `source_11` | text | Y | **MISSING** | -- | -- |
| 40 | `source_12` | text | Y | **MISSING** | -- | -- |
| 41 | `source_13` | text | Y | **MISSING** | -- | -- |
| 42 | `source_14` | text | Y | **MISSING** | -- | -- |
| 43 | `source_15` | text | Y | **MISSING** | -- | -- |
| 44 | `source_16` | text | Y | **MISSING** | -- | -- |
| 45 | `source_17` | text | Y | **MISSING** | -- | -- |
| 46 | `source_18` | text | Y | **MISSING** | -- | -- |
| 47 | `source_19` | text | Y | **MISSING** | -- | -- |
| 48 | `source_20` | text | Y | **MISSING** | -- | -- |
| 49 | `source_21` | text | Y | **MISSING** | -- | -- |
| 50 | `source_22` | text | Y | **MISSING** | -- | -- |
| 51 | `source_23` | text | Y | **MISSING** | -- | -- |
| 52 | `source_24` | text | Y | **MISSING** | -- | -- |
| 53 | `source_25` | text | Y | **MISSING** | -- | -- |
| 54 | `source_26` | text | Y | **MISSING** | -- | -- |
| 55 | `source_27` | text | Y | **MISSING** | -- | -- |
| 56 | `source_28` | text | Y | **MISSING** | -- | -- |
| 57 | `source_29` | text | Y | **MISSING** | -- | -- |
| 58 | `source_30` | text | Y | **MISSING** | -- | -- |
| 59 | `source_file` | character varying(255) | Y | **MISSING** | -- | -- |

### `intake` -- Intake & Staging -- raw CSV imports, candidate records, quarantine

**Tables**: 7 | **Total rows**: 322,625

| Table | Leaf Type | Frozen | Rows | Columns | Documented |
|-------|-----------|--------|------|---------|------------|
| `company_raw_intake` | STAGING |  | 563 | 35 | 0 |
| `company_raw_wv` | STAGING |  | 62,146 | 12 | 0 |
| `people_candidate` | STAGING |  | 0 | 14 | 0 |
| `people_raw_intake` | STAGING |  | 120,045 | 40 | 0 |
| `people_raw_wv` | STAGING |  | 10 | 13 | 0 |
| `people_staging` | STAGING |  | 139,859 | 15 | 0 |
| `quarantine` | STAGING |  | 2 | 28 | 0 |

#### `intake.company_raw_intake` -- STAGING -- 563 rows

Column registry: **UNDOCUMENTED**

| # | Column | Type | Null | Description | Role | Format |
|---|--------|------|------|-------------|------|--------|
| 1 | `id` | bigint | N | **MISSING** | -- | -- |
| 2 | `company` | text | N | **MISSING** | -- | -- |
| 3 | `company_name_for_emails` | text | Y | **MISSING** | -- | -- |
| 4 | `num_employees` | integer | Y | **MISSING** | -- | -- |
| 5 | `industry` | text | Y | **MISSING** | -- | -- |
| 6 | `website` | text | Y | **MISSING** | -- | -- |
| 7 | `company_linkedin_url` | text | Y | **MISSING** | -- | -- |
| 8 | `facebook_url` | text | Y | **MISSING** | -- | -- |
| 9 | `twitter_url` | text | Y | **MISSING** | -- | -- |
| 10 | `company_street` | text | Y | **MISSING** | -- | -- |
| 11 | `company_city` | text | Y | **MISSING** | -- | -- |
| 12 | `company_state` | text | Y | **MISSING** | -- | -- |
| 13 | `company_country` | text | Y | **MISSING** | -- | -- |
| 14 | `company_postal_code` | text | Y | **MISSING** | -- | -- |
| 15 | `company_address` | text | Y | **MISSING** | -- | -- |
| 16 | `company_phone` | text | Y | **MISSING** | -- | -- |
| 17 | `sic_codes` | text | Y | **MISSING** | -- | -- |
| 18 | `founded_year` | integer | Y | **MISSING** | -- | -- |
| 19 | `created_at` | timestamp with time zone | Y | **MISSING** | -- | -- |
| 20 | `state_abbrev` | text | Y | **MISSING** | -- | -- |
| 21 | `import_batch_id` | text | Y | **MISSING** | -- | -- |
| 22 | `validated` | boolean | Y | **MISSING** | -- | -- |
| 23 | `validation_notes` | text | Y | **MISSING** | -- | -- |
| 24 | `validated_at` | timestamp with time zone | Y | **MISSING** | -- | -- |
| 25 | `validated_by` | text | Y | **MISSING** | -- | -- |
| 26 | `enrichment_attempt` | integer | Y | **MISSING** | -- | -- |
| 27 | `chronic_bad` | boolean | Y | **MISSING** | -- | -- |
| 28 | `last_enriched_at` | timestamp without time zone | Y | **MISSING** | -- | -- |
| 29 | `enriched_by` | character varying(255) | Y | **MISSING** | -- | -- |
| 30 | `b2_file_path` | text | Y | **MISSING** | -- | -- |
| 31 | `b2_uploaded_at` | timestamp without time zone | Y | **MISSING** | -- | -- |
| 32 | `apollo_id` | character varying(255) | Y | **MISSING** | -- | -- |
| 33 | `last_hash` | character varying(64) | Y | **MISSING** | -- | -- |
| 34 | `garage_bay` | character varying(10) | Y | **MISSING** | -- | -- |
| 35 | `validation_reasons` | text | Y | **MISSING** | -- | -- |

#### `intake.company_raw_wv` -- STAGING -- 62,146 rows

Column registry: **UNDOCUMENTED**

| # | Column | Type | Null | Description | Role | Format |
|---|--------|------|------|-------------|------|--------|
| 1 | `company_unique_id` | text | N | **MISSING** | -- | -- |
| 2 | `company_name` | text | Y | **MISSING** | -- | -- |
| 3 | `domain` | text | Y | **MISSING** | -- | -- |
| 4 | `website` | text | Y | **MISSING** | -- | -- |
| 5 | `industry` | text | Y | **MISSING** | -- | -- |
| 6 | `employee_count` | integer | Y | **MISSING** | -- | -- |
| 7 | `phone` | text | Y | **MISSING** | -- | -- |
| 8 | `address` | text | Y | **MISSING** | -- | -- |
| 9 | `city` | text | Y | **MISSING** | -- | -- |
| 10 | `state` | text | Y | **MISSING** | -- | -- |
| 11 | `zip` | text | Y | **MISSING** | -- | -- |
| 12 | `created_at` | timestamp without time zone | Y | **MISSING** | -- | -- |

#### `intake.people_candidate` -- STAGING -- 0 rows

Column registry: **UNDOCUMENTED**

| # | Column | Type | Null | Description | Role | Format |
|---|--------|------|------|-------------|------|--------|
| 1 | `candidate_id` | uuid | N | **MISSING** | -- | -- |
| 2 | `outreach_id` | uuid | N | **MISSING** | -- | -- |
| 3 | `slot_type` | character varying(20) | N | **MISSING** | -- | -- |
| 4 | `person_name` | text | Y | **MISSING** | -- | -- |
| 5 | `person_title` | text | Y | **MISSING** | -- | -- |
| 6 | `person_email` | text | Y | **MISSING** | -- | -- |
| 7 | `linkedin_url` | text | Y | **MISSING** | -- | -- |
| 8 | `confidence_score` | numeric | Y | **MISSING** | -- | -- |
| 9 | `source` | character varying(50) | N | **MISSING** | -- | -- |
| 10 | `status` | character varying(20) | N | **MISSING** | -- | -- |
| 11 | `rejection_reason` | text | Y | **MISSING** | -- | -- |
| 12 | `created_at` | timestamp with time zone | N | **MISSING** | -- | -- |
| 13 | `processed_at` | timestamp with time zone | Y | **MISSING** | -- | -- |
| 14 | `expires_at` | timestamp with time zone | Y | **MISSING** | -- | -- |

#### `intake.people_raw_intake` -- STAGING -- 120,045 rows

Column registry: **UNDOCUMENTED**

| # | Column | Type | Null | Description | Role | Format |
|---|--------|------|------|-------------|------|--------|
| 1 | `id` | integer | N | **MISSING** | -- | -- |
| 2 | `first_name` | character varying(255) | Y | **MISSING** | -- | -- |
| 3 | `last_name` | character varying(255) | Y | **MISSING** | -- | -- |
| 4 | `full_name` | character varying(500) | Y | **MISSING** | -- | -- |
| 5 | `email` | character varying(500) | Y | **MISSING** | -- | -- |
| 6 | `work_phone` | character varying(50) | Y | **MISSING** | -- | -- |
| 7 | `personal_phone` | character varying(50) | Y | **MISSING** | -- | -- |
| 8 | `title` | character varying(500) | Y | **MISSING** | -- | -- |
| 9 | `seniority` | character varying(100) | Y | **MISSING** | -- | -- |
| 10 | `department` | character varying(255) | Y | **MISSING** | -- | -- |
| 11 | `company_name` | character varying(500) | Y | **MISSING** | -- | -- |
| 12 | `company_unique_id` | character varying(100) | Y | **MISSING** | -- | -- |
| 13 | `linkedin_url` | text | Y | **MISSING** | -- | -- |
| 14 | `twitter_url` | text | Y | **MISSING** | -- | -- |
| 15 | `facebook_url` | text | Y | **MISSING** | -- | -- |
| 16 | `bio` | text | Y | **MISSING** | -- | -- |
| 17 | `skills` | ARRAY | Y | **MISSING** | -- | -- |
| 18 | `education` | text | Y | **MISSING** | -- | -- |
| 19 | `certifications` | text | Y | **MISSING** | -- | -- |
| 20 | `city` | character varying(255) | Y | **MISSING** | -- | -- |
| 21 | `state` | character varying(100) | Y | **MISSING** | -- | -- |
| 22 | `state_abbrev` | character varying(2) | Y | **MISSING** | -- | -- |
| 23 | `country` | character varying(100) | Y | **MISSING** | -- | -- |
| 24 | `source_system` | character varying(100) | Y | **MISSING** | -- | -- |
| 25 | `source_record_id` | character varying(255) | Y | **MISSING** | -- | -- |
| 26 | `import_batch_id` | character varying(100) | Y | **MISSING** | -- | -- |
| 27 | `validated` | boolean | Y | **MISSING** | -- | -- |
| 28 | `validation_notes` | text | Y | **MISSING** | -- | -- |
| 29 | `validated_at` | timestamp without time zone | Y | **MISSING** | -- | -- |
| 30 | `validated_by` | character varying(255) | Y | **MISSING** | -- | -- |
| 31 | `enrichment_attempt` | integer | Y | **MISSING** | -- | -- |
| 32 | `chronic_bad` | boolean | Y | **MISSING** | -- | -- |
| 33 | `last_enriched_at` | timestamp without time zone | Y | **MISSING** | -- | -- |
| 34 | `enriched_by` | character varying(255) | Y | **MISSING** | -- | -- |
| 35 | `b2_file_path` | text | Y | **MISSING** | -- | -- |
| 36 | `b2_uploaded_at` | timestamp without time zone | Y | **MISSING** | -- | -- |
| 37 | `created_at` | timestamp without time zone | Y | **MISSING** | -- | -- |
| 38 | `updated_at` | timestamp without time zone | Y | **MISSING** | -- | -- |
| 39 | `slot_type` | character varying(10) | Y | **MISSING** | -- | -- |
| 40 | `backfill_source` | character varying(50) | Y | **MISSING** | -- | -- |

#### `intake.people_raw_wv` -- STAGING -- 10 rows

Column registry: **UNDOCUMENTED**

| # | Column | Type | Null | Description | Role | Format |
|---|--------|------|------|-------------|------|--------|
| 1 | `unique_id` | text | N | **MISSING** | -- | -- |
| 2 | `full_name` | text | Y | **MISSING** | -- | -- |
| 3 | `first_name` | text | Y | **MISSING** | -- | -- |
| 4 | `last_name` | text | Y | **MISSING** | -- | -- |
| 5 | `email` | text | Y | **MISSING** | -- | -- |
| 6 | `phone` | text | Y | **MISSING** | -- | -- |
| 7 | `title` | text | Y | **MISSING** | -- | -- |
| 8 | `company_name` | text | Y | **MISSING** | -- | -- |
| 9 | `company_unique_id` | text | Y | **MISSING** | -- | -- |
| 10 | `linkedin_url` | text | Y | **MISSING** | -- | -- |
| 11 | `city` | text | Y | **MISSING** | -- | -- |
| 12 | `state` | text | Y | **MISSING** | -- | -- |
| 13 | `created_at` | timestamp without time zone | Y | **MISSING** | -- | -- |

#### `intake.people_staging` -- STAGING -- 139,859 rows

Column registry: **UNDOCUMENTED**

| # | Column | Type | Null | Description | Role | Format |
|---|--------|------|------|-------------|------|--------|
| 1 | `id` | integer | N | **MISSING** | -- | -- |
| 2 | `source_url_id` | uuid | Y | **MISSING** | -- | -- |
| 3 | `company_unique_id` | text | N | **MISSING** | -- | -- |
| 4 | `raw_name` | text | Y | **MISSING** | -- | -- |
| 5 | `first_name` | character varying(100) | Y | **MISSING** | -- | -- |
| 6 | `last_name` | character varying(100) | Y | **MISSING** | -- | -- |
| 7 | `raw_title` | text | Y | **MISSING** | -- | -- |
| 8 | `normalized_title` | character varying(100) | Y | **MISSING** | -- | -- |
| 9 | `mapped_slot_type` | character varying(20) | Y | **MISSING** | -- | -- |
| 10 | `linkedin_url` | character varying(500) | Y | **MISSING** | -- | -- |
| 11 | `email` | character varying(255) | Y | **MISSING** | -- | -- |
| 12 | `confidence_score` | numeric | Y | **MISSING** | -- | -- |
| 13 | `status` | character varying(20) | Y | **MISSING** | -- | -- |
| 14 | `created_at` | timestamp without time zone | Y | **MISSING** | -- | -- |
| 15 | `processed_at` | timestamp without time zone | Y | **MISSING** | -- | -- |

#### `intake.quarantine` -- STAGING -- 2 rows

Column registry: **UNDOCUMENTED**

| # | Column | Type | Null | Description | Role | Format |
|---|--------|------|------|-------------|------|--------|
| 1 | `id` | bigint | N | **MISSING** | -- | -- |
| 2 | `company_unique_id` | text | N | **MISSING** | -- | -- |
| 3 | `company_name` | text | Y | **MISSING** | -- | -- |
| 4 | `domain` | text | Y | **MISSING** | -- | -- |
| 5 | `industry` | text | Y | **MISSING** | -- | -- |
| 6 | `employee_count` | integer | Y | **MISSING** | -- | -- |
| 7 | `website` | text | Y | **MISSING** | -- | -- |
| 8 | `phone` | text | Y | **MISSING** | -- | -- |
| 9 | `address` | text | Y | **MISSING** | -- | -- |
| 10 | `city` | text | Y | **MISSING** | -- | -- |
| 11 | `state` | text | Y | **MISSING** | -- | -- |
| 12 | `zip` | text | Y | **MISSING** | -- | -- |
| 13 | `validation_status` | text | Y | **MISSING** | -- | -- |
| 14 | `reason_code` | text | N | **MISSING** | -- | -- |
| 15 | `validation_errors` | jsonb | N | **MISSING** | -- | -- |
| 16 | `validation_warnings` | jsonb | Y | **MISSING** | -- | -- |
| 17 | `failed_at` | timestamp without time zone | Y | **MISSING** | -- | -- |
| 18 | `reviewed` | boolean | Y | **MISSING** | -- | -- |
| 19 | `batch_id` | text | Y | **MISSING** | -- | -- |
| 20 | `source_table` | text | Y | **MISSING** | -- | -- |
| 21 | `created_at` | timestamp without time zone | Y | **MISSING** | -- | -- |
| 22 | `updated_at` | timestamp without time zone | Y | **MISSING** | -- | -- |
| 23 | `promoted_to` | text | Y | **MISSING** | -- | -- |
| 24 | `promoted_at` | timestamp without time zone | Y | **MISSING** | -- | -- |
| 25 | `enrichment_data` | jsonb | Y | **MISSING** | -- | -- |
| 26 | `linkedin_url` | text | Y | **MISSING** | -- | -- |
| 27 | `revenue` | numeric | Y | **MISSING** | -- | -- |
| 28 | `location` | text | Y | **MISSING** | -- | -- |

### `bit` -- BIT/CLS Authorization -- movement events, phase state, proof lines

**Tables**: 4 | **Total rows**: 0
**Views**: 2 -- vw_active_movements, vw_company_authorization

| Table | Leaf Type | Frozen | Rows | Columns | Documented |
|-------|-----------|--------|------|---------|------------|
| `authorization_log` | CANONICAL |  | 0 | 12 | 0 |
| `movement_events` | MV |  | 0 | 17 | 0 |
| `phase_state` | CANONICAL |  | 0 | 14 | 0 |
| `proof_lines` | CANONICAL |  | 0 | 11 | 0 |

#### `bit.authorization_log` -- CANONICAL -- 0 rows

Column registry: **UNDOCUMENTED**

| # | Column | Type | Null | Description | Role | Format |
|---|--------|------|------|-------------|------|--------|
| 1 | `log_id` | uuid | N | **MISSING** | -- | -- |
| 2 | `company_unique_id` | text | N | **MISSING** | -- | -- |
| 3 | `requested_action` | text | N | **MISSING** | -- | -- |
| 4 | `requested_band` | integer | N | **MISSING** | -- | -- |
| 5 | `authorized` | boolean | N | **MISSING** | -- | -- |
| 6 | `actual_band` | integer | N | **MISSING** | -- | -- |
| 7 | `denial_reason` | text | Y | **MISSING** | -- | -- |
| 8 | `proof_id` | text | Y | **MISSING** | -- | -- |
| 9 | `proof_valid` | boolean | Y | **MISSING** | -- | -- |
| 10 | `requested_at` | timestamp with time zone | N | **MISSING** | -- | -- |
| 11 | `requested_by` | text | N | **MISSING** | -- | -- |
| 12 | `correlation_id` | text | Y | **MISSING** | -- | -- |

#### `bit.movement_events` -- MV -- 0 rows

Column registry: **UNDOCUMENTED**

| # | Column | Type | Null | Description | Role | Format |
|---|--------|------|------|-------------|------|--------|
| 1 | `movement_id` | uuid | N | **MISSING** | -- | -- |
| 2 | `company_unique_id` | text | N | **MISSING** | -- | -- |
| 3 | `source_hub` | text | N | **MISSING** | -- | -- |
| 4 | `source_table` | text | N | **MISSING** | -- | -- |
| 5 | `source_fields` | ARRAY | N | **MISSING** | -- | -- |
| 6 | `movement_class` | text | N | **MISSING** | -- | -- |
| 7 | `pressure_class` | text | N | **MISSING** | -- | -- |
| 8 | `domain` | text | N | **MISSING** | -- | -- |
| 9 | `direction` | text | N | **MISSING** | -- | -- |
| 10 | `magnitude` | numeric | N | **MISSING** | -- | -- |
| 11 | `detected_at` | timestamp with time zone | N | **MISSING** | -- | -- |
| 12 | `valid_from` | timestamp with time zone | N | **MISSING** | -- | -- |
| 13 | `valid_until` | timestamp with time zone | N | **MISSING** | -- | -- |
| 14 | `comparison_period` | text | Y | **MISSING** | -- | -- |
| 15 | `evidence` | jsonb | N | **MISSING** | -- | -- |
| 16 | `source_record_ids` | jsonb | N | **MISSING** | -- | -- |
| 17 | `created_at` | timestamp with time zone | N | **MISSING** | -- | -- |

#### `bit.phase_state` -- CANONICAL -- 0 rows

Column registry: **UNDOCUMENTED**

| # | Column | Type | Null | Description | Role | Format |
|---|--------|------|------|-------------|------|--------|
| 1 | `company_unique_id` | text | N | **MISSING** | -- | -- |
| 2 | `current_band` | integer | N | **MISSING** | -- | -- |
| 3 | `phase_status` | text | N | **MISSING** | -- | -- |
| 4 | `dol_active` | boolean | N | **MISSING** | -- | -- |
| 5 | `people_active` | boolean | N | **MISSING** | -- | -- |
| 6 | `blog_active` | boolean | N | **MISSING** | -- | -- |
| 7 | `primary_pressure` | text | Y | **MISSING** | -- | -- |
| 8 | `aligned_domains` | integer | N | **MISSING** | -- | -- |
| 9 | `last_movement_at` | timestamp with time zone | Y | **MISSING** | -- | -- |
| 10 | `last_band_change_at` | timestamp with time zone | Y | **MISSING** | -- | -- |
| 11 | `phase_entered_at` | timestamp with time zone | Y | **MISSING** | -- | -- |
| 12 | `stasis_start` | timestamp with time zone | Y | **MISSING** | -- | -- |
| 13 | `stasis_years` | numeric | Y | **MISSING** | -- | -- |
| 14 | `updated_at` | timestamp with time zone | N | **MISSING** | -- | -- |

#### `bit.proof_lines` -- CANONICAL -- 0 rows

Column registry: **UNDOCUMENTED**

| # | Column | Type | Null | Description | Role | Format |
|---|--------|------|------|-------------|------|--------|
| 1 | `proof_id` | text | N | **MISSING** | -- | -- |
| 2 | `company_unique_id` | text | N | **MISSING** | -- | -- |
| 3 | `band` | integer | N | **MISSING** | -- | -- |
| 4 | `pressure_class` | text | N | **MISSING** | -- | -- |
| 5 | `sources` | ARRAY | N | **MISSING** | -- | -- |
| 6 | `evidence` | jsonb | N | **MISSING** | -- | -- |
| 7 | `movement_ids` | ARRAY | N | **MISSING** | -- | -- |
| 8 | `human_readable` | text | N | **MISSING** | -- | -- |
| 9 | `generated_at` | timestamp with time zone | N | **MISSING** | -- | -- |
| 10 | `valid_until` | timestamp with time zone | N | **MISSING** | -- | -- |
| 11 | `generated_by` | text | N | **MISSING** | -- | -- |

### `blog` -- Blog Pressure Signals -- content-derived movement signals

**Tables**: 1 | **Total rows**: 0

| Table | Leaf Type | Frozen | Rows | Columns | Documented |
|-------|-----------|--------|------|---------|------------|
| `pressure_signals` | MV |  | 0 | 12 | 0 |

#### `blog.pressure_signals` -- MV -- 0 rows

Column registry: **UNDOCUMENTED**

| # | Column | Type | Null | Description | Role | Format |
|---|--------|------|------|-------------|------|--------|
| 1 | `signal_id` | uuid | N | **MISSING** | -- | -- |
| 2 | `company_unique_id` | text | N | **MISSING** | -- | -- |
| 3 | `signal_type` | character varying(50) | N | **MISSING** | -- | -- |
| 4 | `pressure_domain` | USER-DEFINED | N | **MISSING** | -- | -- |
| 5 | `pressure_class` | USER-DEFINED | Y | **MISSING** | -- | -- |
| 6 | `signal_value` | jsonb | N | **MISSING** | -- | -- |
| 7 | `magnitude` | integer | N | **MISSING** | -- | -- |
| 8 | `detected_at` | timestamp with time zone | N | **MISSING** | -- | -- |
| 9 | `expires_at` | timestamp with time zone | N | **MISSING** | -- | -- |
| 10 | `correlation_id` | uuid | Y | **MISSING** | -- | -- |
| 11 | `source_record_id` | text | Y | **MISSING** | -- | -- |
| 12 | `created_at` | timestamp with time zone | N | **MISSING** | -- | -- |

### `coverage` -- Coverage Hub -- service agent assignments and market definitions

**Tables**: 2 | **Total rows**: 10
**Views**: 1 -- v_service_agent_coverage_zips

| Table | Leaf Type | Frozen | Rows | Columns | Documented |
|-------|-----------|--------|------|---------|------------|
| `service_agent` | CANONICAL |  | 3 | 7 | 0 |
| `service_agent_coverage` | CANONICAL |  | 7 | 10 | 0 |

#### `coverage.service_agent` -- CANONICAL -- 3 rows

Column registry: **UNDOCUMENTED**

| # | Column | Type | Null | Description | Role | Format |
|---|--------|------|------|-------------|------|--------|
| 1 | `service_agent_id` | uuid | N | **MISSING** | -- | -- |
| 2 | `agent_name` | text | N | **MISSING** | -- | -- |
| 3 | `status` | text | N | **MISSING** | -- | -- |
| 4 | `created_at` | timestamp with time zone | N | **MISSING** | -- | -- |
| 5 | `agent_number` | text | N | **MISSING** | -- | -- |
| 6 | `first_name` | text | Y | **MISSING** | -- | -- |
| 7 | `last_name` | text | Y | **MISSING** | -- | -- |

#### `coverage.service_agent_coverage` -- CANONICAL -- 7 rows

Column registry: **UNDOCUMENTED**

| # | Column | Type | Null | Description | Role | Format |
|---|--------|------|------|-------------|------|--------|
| 1 | `coverage_id` | uuid | N | **MISSING** | -- | -- |
| 2 | `service_agent_id` | uuid | N | **MISSING** | -- | -- |
| 3 | `anchor_zip` | text | N | **MISSING** | -- | -- |
| 4 | `radius_miles` | numeric | N | **MISSING** | -- | -- |
| 5 | `status` | text | N | **MISSING** | -- | -- |
| 6 | `created_by` | text | N | **MISSING** | -- | -- |
| 7 | `created_at` | timestamp with time zone | N | **MISSING** | -- | -- |
| 8 | `retired_at` | timestamp with time zone | Y | **MISSING** | -- | -- |
| 9 | `retired_by` | text | Y | **MISSING** | -- | -- |
| 10 | `notes` | text | Y | **MISSING** | -- | -- |

### `company` -- DEPRECATED -- pre-CL company data, replaced by cl + outreach schemas

**Tables**: 11 | **Total rows**: 210,404
**Views**: 6 -- next_company_urls_30d, v_needs_enrichment, vw_anchor_staleness, vw_company_slots, vw_due_renewals_ready, vw_next_renewal

| Table | Leaf Type | Frozen | Rows | Columns | Documented |
|-------|-----------|--------|------|---------|------------|
| `company_events` | DEPRECATED |  | 0 | 10 | 0 |
| `company_master` | DEPRECATED |  | 92,116 | 36 | 0 |
| `company_sidecar` | DEPRECATED |  | 0 | 11 | 0 |
| `company_slots` | DEPRECATED |  | 1,359 | 5 | 0 |
| `company_source_urls` | DEPRECATED |  | 114,736 | 19 | 0 |
| `contact_enrichment` | DEPRECATED |  | 0 | 11 | 0 |
| `email_verification` | DEPRECATED |  | 0 | 8 | 0 |
| `message_key_reference` | DEPRECATED |  | 8 | 13 | 0 |
| `pipeline_errors` | DEPRECATED |  | 0 | 12 | 0 |
| `pipeline_events` | DEPRECATED |  | 2,185 | 8 | 0 |
| `validation_failures_log` | DEPRECATED |  | 0 | 16 | 0 |

#### `company.company_events` -- DEPRECATED -- 0 rows

Column registry: **UNDOCUMENTED**

| # | Column | Type | Null | Description | Role | Format |
|---|--------|------|------|-------------|------|--------|
| 1 | `id` | integer | N | **MISSING** | -- | -- |
| 2 | `company_unique_id` | text | N | **MISSING** | -- | -- |
| 3 | `event_type` | text | Y | **MISSING** | -- | -- |
| 4 | `event_date` | date | Y | **MISSING** | -- | -- |
| 5 | `source_url` | text | Y | **MISSING** | -- | -- |
| 6 | `summary` | text | Y | **MISSING** | -- | -- |
| 7 | `detected_at` | timestamp without time zone | N | **MISSING** | -- | -- |
| 8 | `impacts_bit` | boolean | Y | **MISSING** | -- | -- |
| 9 | `bit_impact_score` | integer | Y | **MISSING** | -- | -- |
| 10 | `created_at` | timestamp without time zone | Y | **MISSING** | -- | -- |

#### `company.company_master` -- DEPRECATED -- 92,116 rows

Column registry: **UNDOCUMENTED**

| # | Column | Type | Null | Description | Role | Format |
|---|--------|------|------|-------------|------|--------|
| 1 | `company_unique_id` | text | N | **MISSING** | -- | -- |
| 2 | `company_name` | text | N | **MISSING** | -- | -- |
| 3 | `website_url` | text | Y | **MISSING** | -- | -- |
| 4 | `industry` | text | Y | **MISSING** | -- | -- |
| 5 | `employee_count` | integer | N | **MISSING** | -- | -- |
| 6 | `company_phone` | text | Y | **MISSING** | -- | -- |
| 7 | `address_street` | text | Y | **MISSING** | -- | -- |
| 8 | `address_city` | text | Y | **MISSING** | -- | -- |
| 9 | `address_state` | text | N | **MISSING** | -- | -- |
| 10 | `address_zip` | text | Y | **MISSING** | -- | -- |
| 11 | `address_country` | text | Y | **MISSING** | -- | -- |
| 12 | `linkedin_url` | text | Y | **MISSING** | -- | -- |
| 13 | `facebook_url` | text | Y | **MISSING** | -- | -- |
| 14 | `twitter_url` | text | Y | **MISSING** | -- | -- |
| 15 | `sic_codes` | text | Y | **MISSING** | -- | -- |
| 16 | `founded_year` | integer | Y | **MISSING** | -- | -- |
| 17 | `keywords` | ARRAY | Y | **MISSING** | -- | -- |
| 18 | `description` | text | Y | **MISSING** | -- | -- |
| 19 | `source_system` | text | N | **MISSING** | -- | -- |
| 20 | `source_record_id` | text | Y | **MISSING** | -- | -- |
| 21 | `promoted_from_intake_at` | timestamp with time zone | N | **MISSING** | -- | -- |
| 22 | `promotion_audit_log_id` | integer | Y | **MISSING** | -- | -- |
| 23 | `created_at` | timestamp with time zone | Y | **MISSING** | -- | -- |
| 24 | `updated_at` | timestamp with time zone | Y | **MISSING** | -- | -- |
| 25 | `state_abbrev` | text | Y | **MISSING** | -- | -- |
| 26 | `import_batch_id` | text | Y | **MISSING** | -- | -- |
| 27 | `validated_at` | timestamp with time zone | Y | **MISSING** | -- | -- |
| 28 | `validated_by` | text | Y | **MISSING** | -- | -- |
| 29 | `data_quality_score` | numeric | Y | **MISSING** | -- | -- |
| 30 | `email_pattern` | character varying(50) | Y | **MISSING** | -- | -- |
| 31 | `email_pattern_confidence` | integer | Y | **MISSING** | -- | -- |
| 32 | `email_pattern_source` | character varying(50) | Y | **MISSING** | -- | -- |
| 33 | `email_pattern_verified_at` | timestamp without time zone | Y | **MISSING** | -- | -- |
| 34 | `ein` | character varying(9) | Y | **MISSING** | -- | -- |
| 35 | `duns` | character varying(9) | Y | **MISSING** | -- | -- |
| 36 | `cage_code` | character varying(5) | Y | **MISSING** | -- | -- |

#### `company.company_sidecar` -- DEPRECATED -- 0 rows

Column registry: **UNDOCUMENTED**

| # | Column | Type | Null | Description | Role | Format |
|---|--------|------|------|-------------|------|--------|
| 1 | `company_unique_id` | character varying(50) | N | **MISSING** | -- | -- |
| 2 | `ein_number` | character varying(20) | Y | **MISSING** | -- | -- |
| 3 | `dun_and_bradstreet_number` | character varying(20) | Y | **MISSING** | -- | -- |
| 4 | `clay_tags` | ARRAY | Y | **MISSING** | -- | -- |
| 5 | `clay_segments` | ARRAY | Y | **MISSING** | -- | -- |
| 6 | `enrichment_payload` | jsonb | Y | **MISSING** | -- | -- |
| 7 | `last_enriched_at` | timestamp without time zone | Y | **MISSING** | -- | -- |
| 8 | `enrichment_source` | text | Y | **MISSING** | -- | -- |
| 9 | `confidence_score` | numeric | Y | **MISSING** | -- | -- |
| 10 | `created_at` | timestamp without time zone | Y | **MISSING** | -- | -- |
| 11 | `updated_at` | timestamp without time zone | Y | **MISSING** | -- | -- |

#### `company.company_slots` -- DEPRECATED -- 1,359 rows

Column registry: **UNDOCUMENTED**

| # | Column | Type | Null | Description | Role | Format |
|---|--------|------|------|-------------|------|--------|
| 1 | `company_slot_unique_id` | text | N | **MISSING** | -- | -- |
| 2 | `company_unique_id` | text | N | **MISSING** | -- | -- |
| 3 | `slot_type` | text | Y | **MISSING** | -- | -- |
| 4 | `slot_label` | text | Y | **MISSING** | -- | -- |
| 5 | `created_at` | timestamp with time zone | Y | **MISSING** | -- | -- |

#### `company.company_source_urls` -- DEPRECATED -- 114,736 rows

Column registry: **UNDOCUMENTED**

| # | Column | Type | Null | Description | Role | Format |
|---|--------|------|------|-------------|------|--------|
| 1 | `source_id` | uuid | N | **MISSING** | -- | -- |
| 2 | `company_unique_id` | text | N | **MISSING** | -- | -- |
| 3 | `source_type` | character varying(50) | N | **MISSING** | -- | -- |
| 4 | `source_url` | text | N | **MISSING** | -- | -- |
| 5 | `page_title` | text | Y | **MISSING** | -- | -- |
| 6 | `discovered_at` | timestamp with time zone | N | **MISSING** | -- | -- |
| 7 | `discovered_from` | character varying(100) | Y | **MISSING** | -- | -- |
| 8 | `last_checked_at` | timestamp with time zone | Y | **MISSING** | -- | -- |
| 9 | `http_status` | integer | Y | **MISSING** | -- | -- |
| 10 | `is_accessible` | boolean | Y | **MISSING** | -- | -- |
| 11 | `content_checksum` | text | Y | **MISSING** | -- | -- |
| 12 | `last_content_change_at` | timestamp with time zone | Y | **MISSING** | -- | -- |
| 13 | `extraction_status` | character varying(50) | Y | **MISSING** | -- | -- |
| 14 | `extracted_at` | timestamp with time zone | Y | **MISSING** | -- | -- |
| 15 | `created_at` | timestamp with time zone | Y | **MISSING** | -- | -- |
| 16 | `updated_at` | timestamp with time zone | Y | **MISSING** | -- | -- |
| 17 | `extraction_error` | text | Y | **MISSING** | -- | -- |
| 18 | `people_extracted` | integer | Y | **MISSING** | -- | -- |
| 19 | `requires_paid_enrichment` | boolean | Y | **MISSING** | -- | -- |

#### `company.contact_enrichment` -- DEPRECATED -- 0 rows

Column registry: **UNDOCUMENTED**

| # | Column | Type | Null | Description | Role | Format |
|---|--------|------|------|-------------|------|--------|
| 1 | `id` | integer | N | **MISSING** | -- | -- |
| 2 | `company_slot_unique_id` | text | N | **MISSING** | -- | -- |
| 3 | `linkedin_url` | text | Y | **MISSING** | -- | -- |
| 4 | `full_name` | text | Y | **MISSING** | -- | -- |
| 5 | `email` | text | Y | **MISSING** | -- | -- |
| 6 | `phone` | text | Y | **MISSING** | -- | -- |
| 7 | `enrichment_status` | text | Y | **MISSING** | -- | -- |
| 8 | `enrichment_source` | text | Y | **MISSING** | -- | -- |
| 9 | `enrichment_data` | jsonb | Y | **MISSING** | -- | -- |
| 10 | `created_at` | timestamp without time zone | Y | **MISSING** | -- | -- |
| 11 | `enriched_at` | timestamp without time zone | Y | **MISSING** | -- | -- |

#### `company.email_verification` -- DEPRECATED -- 0 rows

Column registry: **UNDOCUMENTED**

| # | Column | Type | Null | Description | Role | Format |
|---|--------|------|------|-------------|------|--------|
| 1 | `id` | integer | N | **MISSING** | -- | -- |
| 2 | `enrichment_id` | integer | N | **MISSING** | -- | -- |
| 3 | `email` | text | N | **MISSING** | -- | -- |
| 4 | `verification_status` | text | Y | **MISSING** | -- | -- |
| 5 | `verification_service` | text | Y | **MISSING** | -- | -- |
| 6 | `verification_result` | jsonb | Y | **MISSING** | -- | -- |
| 7 | `verified_at` | timestamp without time zone | Y | **MISSING** | -- | -- |
| 8 | `created_at` | timestamp without time zone | Y | **MISSING** | -- | -- |

#### `company.message_key_reference` -- DEPRECATED -- 8 rows

Column registry: **UNDOCUMENTED**

| # | Column | Type | Null | Description | Role | Format |
|---|--------|------|------|-------------|------|--------|
| 1 | `message_key` | text | N | **MISSING** | -- | -- |
| 2 | `role` | text | N | **MISSING** | -- | -- |
| 3 | `message_type` | text | N | **MISSING** | -- | -- |
| 4 | `trigger_condition` | text | Y | **MISSING** | -- | -- |
| 5 | `vibeos_template_id` | text | Y | **MISSING** | -- | -- |
| 6 | `message_channel` | text | Y | **MISSING** | -- | -- |
| 7 | `subject_line` | text | Y | **MISSING** | -- | -- |
| 8 | `preview_text` | text | Y | **MISSING** | -- | -- |
| 9 | `send_delay_hours` | integer | Y | **MISSING** | -- | -- |
| 10 | `optimal_send_time` | text | Y | **MISSING** | -- | -- |
| 11 | `active` | boolean | Y | **MISSING** | -- | -- |
| 12 | `created_at` | timestamp with time zone | Y | **MISSING** | -- | -- |
| 13 | `updated_at` | timestamp with time zone | Y | **MISSING** | -- | -- |

#### `company.pipeline_errors` -- DEPRECATED -- 0 rows

Column registry: **UNDOCUMENTED**

| # | Column | Type | Null | Description | Role | Format |
|---|--------|------|------|-------------|------|--------|
| 1 | `id` | integer | N | **MISSING** | -- | -- |
| 2 | `event_type` | text | N | **MISSING** | -- | -- |
| 3 | `record_id` | text | N | **MISSING** | -- | -- |
| 4 | `error_message` | text | N | **MISSING** | -- | -- |
| 5 | `error_details` | jsonb | Y | **MISSING** | -- | -- |
| 6 | `severity` | text | Y | **MISSING** | -- | -- |
| 7 | `resolved` | boolean | Y | **MISSING** | -- | -- |
| 8 | `resolved_at` | timestamp without time zone | Y | **MISSING** | -- | -- |
| 9 | `resolved_by` | text | Y | **MISSING** | -- | -- |
| 10 | `resolution_notes` | text | Y | **MISSING** | -- | -- |
| 11 | `created_at` | timestamp without time zone | Y | **MISSING** | -- | -- |
| 12 | `error_type` | character varying(100) | Y | **MISSING** | -- | -- |

#### `company.pipeline_events` -- DEPRECATED -- 2,185 rows

Column registry: **UNDOCUMENTED**

| # | Column | Type | Null | Description | Role | Format |
|---|--------|------|------|-------------|------|--------|
| 1 | `id` | integer | N | **MISSING** | -- | -- |
| 2 | `event_type` | text | N | **MISSING** | -- | -- |
| 3 | `payload` | jsonb | N | **MISSING** | -- | -- |
| 4 | `status` | text | Y | **MISSING** | -- | -- |
| 5 | `error_message` | text | Y | **MISSING** | -- | -- |
| 6 | `retry_count` | integer | Y | **MISSING** | -- | -- |
| 7 | `created_at` | timestamp without time zone | Y | **MISSING** | -- | -- |
| 8 | `processed_at` | timestamp without time zone | Y | **MISSING** | -- | -- |

#### `company.validation_failures_log` -- DEPRECATED -- 0 rows

Column registry: **UNDOCUMENTED**

| # | Column | Type | Null | Description | Role | Format |
|---|--------|------|------|-------------|------|--------|
| 1 | `id` | integer | N | **MISSING** | -- | -- |
| 2 | `company_id` | text | Y | **MISSING** | -- | -- |
| 3 | `person_id` | text | Y | **MISSING** | -- | -- |
| 4 | `company_name` | text | Y | **MISSING** | -- | -- |
| 5 | `person_name` | text | Y | **MISSING** | -- | -- |
| 6 | `fail_reason` | text | N | **MISSING** | -- | -- |
| 7 | `state` | text | Y | **MISSING** | -- | -- |
| 8 | `validation_timestamp` | timestamp with time zone | Y | **MISSING** | -- | -- |
| 9 | `pipeline_id` | text | N | **MISSING** | -- | -- |
| 10 | `failure_type` | text | N | **MISSING** | -- | -- |
| 11 | `created_at` | timestamp with time zone | Y | **MISSING** | -- | -- |
| 12 | `updated_at` | timestamp with time zone | Y | **MISSING** | -- | -- |
| 13 | `exported_to_sheets` | boolean | Y | **MISSING** | -- | -- |
| 14 | `exported_at` | timestamp with time zone | Y | **MISSING** | -- | -- |
| 15 | `exported_to_b2` | boolean | Y | **MISSING** | -- | -- |
| 16 | `exported_to_b2_at` | timestamp without time zone | Y | **MISSING** | -- | -- |

### `marketing` -- DEPRECATED -- pre-CL marketing pipeline, replaced by outreach + people schemas

**Tables**: 8 | **Total rows**: 1,752
**Views**: 10 -- marketing_ceo, marketing_cfo, marketing_hr, v_companies_need_enrichment, v_phase_stats, vw_error_rate_24h, vw_health_crawl_staleness, vw_health_profile_staleness, vw_queue_sizes, vw_unresolved_errors

| Table | Leaf Type | Frozen | Rows | Columns | Documented |
|-------|-----------|--------|------|---------|------------|
| `company_master` | DEPRECATED |  | 512 | 13 | 0 |
| `failed_company_match` | DEPRECATED |  | 32 | 20 | 0 |
| `failed_email_verification` | DEPRECATED |  | 310 | 27 | 0 |
| `failed_low_confidence` | DEPRECATED |  | 5 | 22 | 0 |
| `failed_no_pattern` | DEPRECATED |  | 6 | 24 | 0 |
| `failed_slot_assignment` | DEPRECATED |  | 222 | 24 | 0 |
| `people_master` | DEPRECATED |  | 149 | 17 | 0 |
| `review_queue` | DEPRECATED |  | 516 | 20 | 0 |

#### `marketing.company_master` -- DEPRECATED -- 512 rows

Column registry: **UNDOCUMENTED**

| # | Column | Type | Null | Description | Role | Format |
|---|--------|------|------|-------------|------|--------|
| 1 | `company_unique_id` | character varying(50) | N | **MISSING** | -- | -- |
| 2 | `company_name` | character varying(500) | N | **MISSING** | -- | -- |
| 3 | `domain` | character varying(255) | Y | **MISSING** | -- | -- |
| 4 | `industry` | character varying(255) | Y | **MISSING** | -- | -- |
| 5 | `employee_count` | integer | Y | **MISSING** | -- | -- |
| 6 | `email_pattern` | character varying(50) | Y | **MISSING** | -- | -- |
| 7 | `pattern_confidence` | numeric | Y | **MISSING** | -- | -- |
| 8 | `source` | character varying(100) | Y | **MISSING** | -- | -- |
| 9 | `source_file` | character varying(255) | Y | **MISSING** | -- | -- |
| 10 | `created_at` | timestamp without time zone | Y | **MISSING** | -- | -- |
| 11 | `updated_at` | timestamp without time zone | Y | **MISSING** | -- | -- |
| 12 | `bit_band` | integer | Y | **MISSING** | -- | -- |
| 13 | `bit_phase` | text | Y | **MISSING** | -- | -- |

#### `marketing.failed_company_match` -- DEPRECATED -- 32 rows

Column registry: **UNDOCUMENTED**

| # | Column | Type | Null | Description | Role | Format |
|---|--------|------|------|-------------|------|--------|
| 1 | `id` | integer | N | **MISSING** | -- | -- |
| 2 | `person_id` | character varying(50) | N | **MISSING** | -- | -- |
| 3 | `full_name` | character varying(500) | N | **MISSING** | -- | -- |
| 4 | `job_title` | character varying(500) | Y | **MISSING** | -- | -- |
| 5 | `title_seniority` | character varying(50) | Y | **MISSING** | -- | -- |
| 6 | `company_name_raw` | character varying(500) | N | **MISSING** | -- | -- |
| 7 | `linkedin_url` | character varying(500) | Y | **MISSING** | -- | -- |
| 8 | `best_match_company` | character varying(500) | Y | **MISSING** | -- | -- |
| 9 | `best_match_score` | numeric | Y | **MISSING** | -- | -- |
| 10 | `best_match_notes` | text | Y | **MISSING** | -- | -- |
| 11 | `resolution_status` | character varying(50) | Y | **MISSING** | -- | -- |
| 12 | `resolution` | character varying(50) | Y | **MISSING** | -- | -- |
| 13 | `resolution_notes` | text | Y | **MISSING** | -- | -- |
| 14 | `resolved_by` | character varying(255) | Y | **MISSING** | -- | -- |
| 15 | `resolved_at` | timestamp without time zone | Y | **MISSING** | -- | -- |
| 16 | `resolved_company_id` | character varying(50) | Y | **MISSING** | -- | -- |
| 17 | `source` | character varying(100) | Y | **MISSING** | -- | -- |
| 18 | `source_file` | character varying(255) | Y | **MISSING** | -- | -- |
| 19 | `created_at` | timestamp without time zone | Y | **MISSING** | -- | -- |
| 20 | `updated_at` | timestamp without time zone | Y | **MISSING** | -- | -- |

#### `marketing.failed_email_verification` -- DEPRECATED -- 310 rows

Column registry: **UNDOCUMENTED**

| # | Column | Type | Null | Description | Role | Format |
|---|--------|------|------|-------------|------|--------|
| 1 | `id` | integer | N | **MISSING** | -- | -- |
| 2 | `person_id` | character varying(50) | N | **MISSING** | -- | -- |
| 3 | `full_name` | character varying(500) | N | **MISSING** | -- | -- |
| 4 | `job_title` | character varying(500) | Y | **MISSING** | -- | -- |
| 5 | `title_seniority` | character varying(50) | Y | **MISSING** | -- | -- |
| 6 | `company_name_raw` | character varying(500) | Y | **MISSING** | -- | -- |
| 7 | `linkedin_url` | character varying(500) | Y | **MISSING** | -- | -- |
| 8 | `company_id` | character varying(50) | Y | **MISSING** | -- | -- |
| 9 | `company_name` | character varying(500) | Y | **MISSING** | -- | -- |
| 10 | `company_domain` | character varying(255) | Y | **MISSING** | -- | -- |
| 11 | `email_pattern` | character varying(50) | Y | **MISSING** | -- | -- |
| 12 | `slot_type` | character varying(50) | Y | **MISSING** | -- | -- |
| 13 | `generated_email` | character varying(255) | Y | **MISSING** | -- | -- |
| 14 | `verification_error` | character varying(255) | Y | **MISSING** | -- | -- |
| 15 | `verification_notes` | text | Y | **MISSING** | -- | -- |
| 16 | `email_variants` | text | Y | **MISSING** | -- | -- |
| 17 | `resolution_status` | character varying(50) | Y | **MISSING** | -- | -- |
| 18 | `resolution` | character varying(50) | Y | **MISSING** | -- | -- |
| 19 | `resolution_notes` | text | Y | **MISSING** | -- | -- |
| 20 | `resolved_by` | character varying(255) | Y | **MISSING** | -- | -- |
| 21 | `resolved_at` | timestamp without time zone | Y | **MISSING** | -- | -- |
| 22 | `verified_email` | character varying(255) | Y | **MISSING** | -- | -- |
| 23 | `verified_email_source` | character varying(100) | Y | **MISSING** | -- | -- |
| 24 | `source` | character varying(100) | Y | **MISSING** | -- | -- |
| 25 | `source_file` | character varying(255) | Y | **MISSING** | -- | -- |
| 26 | `created_at` | timestamp without time zone | Y | **MISSING** | -- | -- |
| 27 | `updated_at` | timestamp without time zone | Y | **MISSING** | -- | -- |

#### `marketing.failed_low_confidence` -- DEPRECATED -- 5 rows

Column registry: **UNDOCUMENTED**

| # | Column | Type | Null | Description | Role | Format |
|---|--------|------|------|-------------|------|--------|
| 1 | `id` | integer | N | **MISSING** | -- | -- |
| 2 | `person_id` | character varying(50) | N | **MISSING** | -- | -- |
| 3 | `full_name` | character varying(500) | N | **MISSING** | -- | -- |
| 4 | `job_title` | character varying(500) | Y | **MISSING** | -- | -- |
| 5 | `title_seniority` | character varying(50) | Y | **MISSING** | -- | -- |
| 6 | `company_name_raw` | character varying(500) | N | **MISSING** | -- | -- |
| 7 | `linkedin_url` | character varying(500) | Y | **MISSING** | -- | -- |
| 8 | `matched_company_id` | character varying(50) | Y | **MISSING** | -- | -- |
| 9 | `matched_company_name` | character varying(500) | Y | **MISSING** | -- | -- |
| 10 | `matched_company_domain` | character varying(255) | Y | **MISSING** | -- | -- |
| 11 | `fuzzy_score` | numeric | Y | **MISSING** | -- | -- |
| 12 | `match_notes` | text | Y | **MISSING** | -- | -- |
| 13 | `resolution_status` | character varying(50) | Y | **MISSING** | -- | -- |
| 14 | `resolution` | character varying(50) | Y | **MISSING** | -- | -- |
| 15 | `resolution_notes` | text | Y | **MISSING** | -- | -- |
| 16 | `resolved_by` | character varying(255) | Y | **MISSING** | -- | -- |
| 17 | `resolved_at` | timestamp without time zone | Y | **MISSING** | -- | -- |
| 18 | `confirmed_company_id` | character varying(50) | Y | **MISSING** | -- | -- |
| 19 | `source` | character varying(100) | Y | **MISSING** | -- | -- |
| 20 | `source_file` | character varying(255) | Y | **MISSING** | -- | -- |
| 21 | `created_at` | timestamp without time zone | Y | **MISSING** | -- | -- |
| 22 | `updated_at` | timestamp without time zone | Y | **MISSING** | -- | -- |

#### `marketing.failed_no_pattern` -- DEPRECATED -- 6 rows

Column registry: **UNDOCUMENTED**

| # | Column | Type | Null | Description | Role | Format |
|---|--------|------|------|-------------|------|--------|
| 1 | `id` | integer | N | **MISSING** | -- | -- |
| 2 | `person_id` | character varying(50) | N | **MISSING** | -- | -- |
| 3 | `full_name` | character varying(500) | N | **MISSING** | -- | -- |
| 4 | `job_title` | character varying(500) | Y | **MISSING** | -- | -- |
| 5 | `title_seniority` | character varying(50) | Y | **MISSING** | -- | -- |
| 6 | `company_name_raw` | character varying(500) | Y | **MISSING** | -- | -- |
| 7 | `linkedin_url` | character varying(500) | Y | **MISSING** | -- | -- |
| 8 | `company_id` | character varying(50) | Y | **MISSING** | -- | -- |
| 9 | `company_name` | character varying(500) | Y | **MISSING** | -- | -- |
| 10 | `company_domain` | character varying(255) | Y | **MISSING** | -- | -- |
| 11 | `slot_type` | character varying(50) | Y | **MISSING** | -- | -- |
| 12 | `failure_reason` | character varying(100) | Y | **MISSING** | -- | -- |
| 13 | `failure_notes` | text | Y | **MISSING** | -- | -- |
| 14 | `resolution_status` | character varying(50) | Y | **MISSING** | -- | -- |
| 15 | `resolution` | character varying(50) | Y | **MISSING** | -- | -- |
| 16 | `resolution_notes` | text | Y | **MISSING** | -- | -- |
| 17 | `resolved_by` | character varying(255) | Y | **MISSING** | -- | -- |
| 18 | `resolved_at` | timestamp without time zone | Y | **MISSING** | -- | -- |
| 19 | `manual_email` | character varying(255) | Y | **MISSING** | -- | -- |
| 20 | `manual_email_source` | character varying(100) | Y | **MISSING** | -- | -- |
| 21 | `source` | character varying(100) | Y | **MISSING** | -- | -- |
| 22 | `source_file` | character varying(255) | Y | **MISSING** | -- | -- |
| 23 | `created_at` | timestamp without time zone | Y | **MISSING** | -- | -- |
| 24 | `updated_at` | timestamp without time zone | Y | **MISSING** | -- | -- |

#### `marketing.failed_slot_assignment` -- DEPRECATED -- 222 rows

Column registry: **UNDOCUMENTED**

| # | Column | Type | Null | Description | Role | Format |
|---|--------|------|------|-------------|------|--------|
| 1 | `id` | integer | N | **MISSING** | -- | -- |
| 2 | `person_id` | character varying(50) | N | **MISSING** | -- | -- |
| 3 | `full_name` | character varying(500) | N | **MISSING** | -- | -- |
| 4 | `job_title` | character varying(500) | Y | **MISSING** | -- | -- |
| 5 | `title_seniority` | character varying(50) | Y | **MISSING** | -- | -- |
| 6 | `company_name_raw` | character varying(500) | Y | **MISSING** | -- | -- |
| 7 | `linkedin_url` | character varying(500) | Y | **MISSING** | -- | -- |
| 8 | `matched_company_id` | character varying(50) | Y | **MISSING** | -- | -- |
| 9 | `matched_company_name` | character varying(500) | Y | **MISSING** | -- | -- |
| 10 | `matched_company_domain` | character varying(255) | Y | **MISSING** | -- | -- |
| 11 | `fuzzy_score` | numeric | Y | **MISSING** | -- | -- |
| 12 | `slot_type` | character varying(50) | Y | **MISSING** | -- | -- |
| 13 | `lost_to_person_id` | character varying(50) | Y | **MISSING** | -- | -- |
| 14 | `lost_to_person_name` | character varying(500) | Y | **MISSING** | -- | -- |
| 15 | `lost_to_seniority` | character varying(50) | Y | **MISSING** | -- | -- |
| 16 | `resolution_status` | character varying(50) | Y | **MISSING** | -- | -- |
| 17 | `resolution` | character varying(50) | Y | **MISSING** | -- | -- |
| 18 | `resolution_notes` | text | Y | **MISSING** | -- | -- |
| 19 | `resolved_by` | character varying(255) | Y | **MISSING** | -- | -- |
| 20 | `resolved_at` | timestamp without time zone | Y | **MISSING** | -- | -- |
| 21 | `source` | character varying(100) | Y | **MISSING** | -- | -- |
| 22 | `source_file` | character varying(255) | Y | **MISSING** | -- | -- |
| 23 | `created_at` | timestamp without time zone | Y | **MISSING** | -- | -- |
| 24 | `updated_at` | timestamp without time zone | Y | **MISSING** | -- | -- |

#### `marketing.people_master` -- DEPRECATED -- 149 rows

Column registry: **UNDOCUMENTED**

| # | Column | Type | Null | Description | Role | Format |
|---|--------|------|------|-------------|------|--------|
| 1 | `unique_id` | character varying(50) | N | **MISSING** | -- | -- |
| 2 | `company_unique_id` | character varying(50) | Y | **MISSING** | -- | -- |
| 3 | `full_name` | character varying(500) | N | **MISSING** | -- | -- |
| 4 | `first_name` | character varying(255) | Y | **MISSING** | -- | -- |
| 5 | `last_name` | character varying(255) | Y | **MISSING** | -- | -- |
| 6 | `email` | character varying(255) | Y | **MISSING** | -- | -- |
| 7 | `email_verified` | boolean | Y | **MISSING** | -- | -- |
| 8 | `email_confidence` | numeric | Y | **MISSING** | -- | -- |
| 9 | `linkedin_url` | character varying(500) | Y | **MISSING** | -- | -- |
| 10 | `title` | character varying(500) | Y | **MISSING** | -- | -- |
| 11 | `title_seniority` | character varying(50) | Y | **MISSING** | -- | -- |
| 12 | `location` | character varying(500) | Y | **MISSING** | -- | -- |
| 13 | `source` | character varying(100) | Y | **MISSING** | -- | -- |
| 14 | `source_file` | character varying(255) | Y | **MISSING** | -- | -- |
| 15 | `created_at` | timestamp without time zone | Y | **MISSING** | -- | -- |
| 16 | `updated_at` | timestamp without time zone | Y | **MISSING** | -- | -- |
| 17 | `slot_complete` | boolean | Y | **MISSING** | -- | -- |

#### `marketing.review_queue` -- DEPRECATED -- 516 rows

Column registry: **UNDOCUMENTED**

| # | Column | Type | Null | Description | Role | Format |
|---|--------|------|------|-------------|------|--------|
| 1 | `review_id` | integer | N | **MISSING** | -- | -- |
| 2 | `person_id` | character varying(50) | N | **MISSING** | -- | -- |
| 3 | `full_name` | character varying(500) | N | **MISSING** | -- | -- |
| 4 | `job_title` | character varying(500) | Y | **MISSING** | -- | -- |
| 5 | `company_name_raw` | character varying(500) | Y | **MISSING** | -- | -- |
| 6 | `review_reason` | character varying(50) | N | **MISSING** | -- | -- |
| 7 | `review_notes` | text | Y | **MISSING** | -- | -- |
| 8 | `fuzzy_score` | numeric | Y | **MISSING** | -- | -- |
| 9 | `fuzzy_matched_company` | character varying(500) | Y | **MISSING** | -- | -- |
| 10 | `matched_company_id` | character varying(50) | Y | **MISSING** | -- | -- |
| 11 | `linkedin_url` | character varying(500) | Y | **MISSING** | -- | -- |
| 12 | `review_status` | character varying(50) | Y | **MISSING** | -- | -- |
| 13 | `reviewed_by` | character varying(255) | Y | **MISSING** | -- | -- |
| 14 | `reviewed_at` | timestamp without time zone | Y | **MISSING** | -- | -- |
| 15 | `resolution` | character varying(50) | Y | **MISSING** | -- | -- |
| 16 | `resolution_notes` | text | Y | **MISSING** | -- | -- |
| 17 | `source` | character varying(100) | Y | **MISSING** | -- | -- |
| 18 | `source_file` | character varying(255) | Y | **MISSING** | -- | -- |
| 19 | `created_at` | timestamp without time zone | Y | **MISSING** | -- | -- |
| 20 | `updated_at` | timestamp without time zone | Y | **MISSING** | -- | -- |

### `partners` -- Partner Lane -- fractional CFO partner records

**Tables**: 2 | **Total rows**: 833

| Table | Leaf Type | Frozen | Rows | Columns | Documented |
|-------|-----------|--------|------|---------|------------|
| `fractional_cfo_master` | UNREGISTERED |  | 833 | 13 | 0 |
| `partner_appointments` | UNREGISTERED |  | 0 | 8 | 0 |

#### `partners.fractional_cfo_master` -- UNREGISTERED -- 833 rows

Column registry: **UNDOCUMENTED**

| # | Column | Type | Null | Description | Role | Format |
|---|--------|------|------|-------------|------|--------|
| 1 | `fractional_cfo_id` | uuid | N | **MISSING** | -- | -- |
| 2 | `firm_name` | text | N | **MISSING** | -- | -- |
| 3 | `primary_contact_name` | text | N | **MISSING** | -- | -- |
| 4 | `linkedin_url` | text | Y | **MISSING** | -- | -- |
| 5 | `email` | text | Y | **MISSING** | -- | -- |
| 6 | `geography` | text | Y | **MISSING** | -- | -- |
| 7 | `niche_focus` | text | Y | **MISSING** | -- | -- |
| 8 | `source` | text | N | **MISSING** | -- | -- |
| 9 | `source_detail` | text | Y | **MISSING** | -- | -- |
| 10 | `status` | USER-DEFINED | N | **MISSING** | -- | -- |
| 11 | `metadata` | jsonb | Y | **MISSING** | -- | -- |
| 12 | `created_at` | timestamp with time zone | N | **MISSING** | -- | -- |
| 13 | `updated_at` | timestamp with time zone | N | **MISSING** | -- | -- |

#### `partners.partner_appointments` -- UNREGISTERED -- 0 rows

Column registry: **UNDOCUMENTED**

| # | Column | Type | Null | Description | Role | Format |
|---|--------|------|------|-------------|------|--------|
| 1 | `partner_appointment_uid` | text | N | **MISSING** | -- | -- |
| 2 | `fractional_cfo_id` | uuid | N | **MISSING** | -- | -- |
| 3 | `meeting_date` | date | N | **MISSING** | -- | -- |
| 4 | `meeting_type` | USER-DEFINED | N | **MISSING** | -- | -- |
| 5 | `outcome` | USER-DEFINED | N | **MISSING** | -- | -- |
| 6 | `notes` | text | Y | **MISSING** | -- | -- |
| 7 | `metadata` | jsonb | Y | **MISSING** | -- | -- |
| 8 | `created_at` | timestamp with time zone | N | **MISSING** | -- | -- |

### `sales` -- Sales Lane -- appointments already had (reactivation)

**Tables**: 1 | **Total rows**: 771

| Table | Leaf Type | Frozen | Rows | Columns | Documented |
|-------|-----------|--------|------|---------|------------|
| `appointments_already_had` | UNREGISTERED |  | 771 | 12 | 0 |

#### `sales.appointments_already_had` -- UNREGISTERED -- 771 rows

Column registry: **UNDOCUMENTED**

| # | Column | Type | Null | Description | Role | Format |
|---|--------|------|------|-------------|------|--------|
| 1 | `appointment_uid` | text | N | **MISSING** | -- | -- |
| 2 | `company_id` | uuid | Y | **MISSING** | -- | -- |
| 3 | `people_id` | uuid | Y | **MISSING** | -- | -- |
| 4 | `outreach_id` | uuid | Y | **MISSING** | -- | -- |
| 5 | `meeting_date` | date | N | **MISSING** | -- | -- |
| 6 | `meeting_type` | USER-DEFINED | N | **MISSING** | -- | -- |
| 7 | `meeting_outcome` | USER-DEFINED | N | **MISSING** | -- | -- |
| 8 | `stalled_reason` | text | Y | **MISSING** | -- | -- |
| 9 | `source` | USER-DEFINED | N | **MISSING** | -- | -- |
| 10 | `source_record_id` | text | Y | **MISSING** | -- | -- |
| 11 | `metadata` | jsonb | Y | **MISSING** | -- | -- |
| 12 | `created_at` | timestamp with time zone | N | **MISSING** | -- | -- |

### `clnt` -- Client Hub Scaffold -- future client management (ALL EMPTY)

**Tables**: 13 | **Total rows**: 0

| Table | Leaf Type | Frozen | Rows | Columns | Documented |
|-------|-----------|--------|------|---------|------------|
| `audit_event` | UNREGISTERED |  | 0 | 6 | 0 |
| `client_hub` | UNREGISTERED |  | 0 | 5 | 0 |
| `client_master` | UNREGISTERED |  | 0 | 7 | 0 |
| `compliance_flag` | UNREGISTERED |  | 0 | 7 | 0 |
| `election` | UNREGISTERED |  | 0 | 8 | 0 |
| `external_identity_map` | UNREGISTERED |  | 0 | 10 | 0 |
| `intake_batch` | UNREGISTERED |  | 0 | 6 | 0 |
| `intake_record` | UNREGISTERED |  | 0 | 5 | 0 |
| `person` | UNREGISTERED |  | 0 | 8 | 0 |
| `plan` | UNREGISTERED |  | 0 | 18 | 0 |
| `plan_quote` | UNREGISTERED |  | 0 | 13 | 0 |
| `service_request` | UNREGISTERED |  | 0 | 7 | 0 |
| `vendor` | UNREGISTERED |  | 0 | 6 | 0 |

#### `clnt.audit_event` -- UNREGISTERED -- 0 rows

Column registry: **UNDOCUMENTED**

| # | Column | Type | Null | Description | Role | Format |
|---|--------|------|------|-------------|------|--------|
| 1 | `audit_event_id` | uuid | N | **MISSING** | -- | -- |
| 2 | `client_id` | uuid | N | **MISSING** | -- | -- |
| 3 | `entity_type` | text | N | **MISSING** | -- | -- |
| 4 | `entity_id` | uuid | N | **MISSING** | -- | -- |
| 5 | `action` | text | N | **MISSING** | -- | -- |
| 6 | `created_at` | timestamp with time zone | N | **MISSING** | -- | -- |

#### `clnt.client_hub` -- UNREGISTERED -- 0 rows

Column registry: **UNDOCUMENTED**

| # | Column | Type | Null | Description | Role | Format |
|---|--------|------|------|-------------|------|--------|
| 1 | `client_id` | uuid | N | **MISSING** | -- | -- |
| 2 | `created_at` | timestamp with time zone | N | **MISSING** | -- | -- |
| 3 | `status` | text | N | **MISSING** | -- | -- |
| 4 | `source` | text | Y | **MISSING** | -- | -- |
| 5 | `version` | integer | N | **MISSING** | -- | -- |

#### `clnt.client_master` -- UNREGISTERED -- 0 rows

Column registry: **UNDOCUMENTED**

| # | Column | Type | Null | Description | Role | Format |
|---|--------|------|------|-------------|------|--------|
| 1 | `client_id` | uuid | N | **MISSING** | -- | -- |
| 2 | `legal_name` | text | N | **MISSING** | -- | -- |
| 3 | `fein` | text | Y | **MISSING** | -- | -- |
| 4 | `domicile_state` | text | Y | **MISSING** | -- | -- |
| 5 | `effective_date` | date | Y | **MISSING** | -- | -- |
| 6 | `created_at` | timestamp with time zone | N | **MISSING** | -- | -- |
| 7 | `updated_at` | timestamp with time zone | N | **MISSING** | -- | -- |

#### `clnt.compliance_flag` -- UNREGISTERED -- 0 rows

Column registry: **UNDOCUMENTED**

| # | Column | Type | Null | Description | Role | Format |
|---|--------|------|------|-------------|------|--------|
| 1 | `compliance_flag_id` | uuid | N | **MISSING** | -- | -- |
| 2 | `client_id` | uuid | N | **MISSING** | -- | -- |
| 3 | `flag_type` | text | N | **MISSING** | -- | -- |
| 4 | `status` | text | N | **MISSING** | -- | -- |
| 5 | `effective_date` | date | Y | **MISSING** | -- | -- |
| 6 | `created_at` | timestamp with time zone | N | **MISSING** | -- | -- |
| 7 | `updated_at` | timestamp with time zone | N | **MISSING** | -- | -- |

#### `clnt.election` -- UNREGISTERED -- 0 rows

Column registry: **UNDOCUMENTED**

| # | Column | Type | Null | Description | Role | Format |
|---|--------|------|------|-------------|------|--------|
| 1 | `election_id` | uuid | N | **MISSING** | -- | -- |
| 2 | `client_id` | uuid | N | **MISSING** | -- | -- |
| 3 | `person_id` | uuid | N | **MISSING** | -- | -- |
| 4 | `plan_id` | uuid | N | **MISSING** | -- | -- |
| 5 | `coverage_tier` | text | N | **MISSING** | -- | -- |
| 6 | `effective_date` | date | N | **MISSING** | -- | -- |
| 7 | `created_at` | timestamp with time zone | N | **MISSING** | -- | -- |
| 8 | `updated_at` | timestamp with time zone | N | **MISSING** | -- | -- |

#### `clnt.external_identity_map` -- UNREGISTERED -- 0 rows

Column registry: **UNDOCUMENTED**

| # | Column | Type | Null | Description | Role | Format |
|---|--------|------|------|-------------|------|--------|
| 1 | `external_identity_id` | uuid | N | **MISSING** | -- | -- |
| 2 | `client_id` | uuid | N | **MISSING** | -- | -- |
| 3 | `entity_type` | text | N | **MISSING** | -- | -- |
| 4 | `internal_id` | uuid | N | **MISSING** | -- | -- |
| 5 | `vendor_id` | uuid | N | **MISSING** | -- | -- |
| 6 | `external_id_value` | text | N | **MISSING** | -- | -- |
| 7 | `effective_date` | date | Y | **MISSING** | -- | -- |
| 8 | `status` | text | N | **MISSING** | -- | -- |
| 9 | `created_at` | timestamp with time zone | N | **MISSING** | -- | -- |
| 10 | `updated_at` | timestamp with time zone | N | **MISSING** | -- | -- |

#### `clnt.intake_batch` -- UNREGISTERED -- 0 rows

Column registry: **UNDOCUMENTED**

| # | Column | Type | Null | Description | Role | Format |
|---|--------|------|------|-------------|------|--------|
| 1 | `intake_batch_id` | uuid | N | **MISSING** | -- | -- |
| 2 | `client_id` | uuid | N | **MISSING** | -- | -- |
| 3 | `upload_date` | timestamp with time zone | N | **MISSING** | -- | -- |
| 4 | `status` | text | N | **MISSING** | -- | -- |
| 5 | `created_at` | timestamp with time zone | N | **MISSING** | -- | -- |
| 6 | `updated_at` | timestamp with time zone | N | **MISSING** | -- | -- |

#### `clnt.intake_record` -- UNREGISTERED -- 0 rows

Column registry: **UNDOCUMENTED**

| # | Column | Type | Null | Description | Role | Format |
|---|--------|------|------|-------------|------|--------|
| 1 | `intake_record_id` | uuid | N | **MISSING** | -- | -- |
| 2 | `client_id` | uuid | N | **MISSING** | -- | -- |
| 3 | `intake_batch_id` | uuid | N | **MISSING** | -- | -- |
| 4 | `raw_payload` | jsonb | N | **MISSING** | -- | -- |
| 5 | `created_at` | timestamp with time zone | N | **MISSING** | -- | -- |

#### `clnt.person` -- UNREGISTERED -- 0 rows

Column registry: **UNDOCUMENTED**

| # | Column | Type | Null | Description | Role | Format |
|---|--------|------|------|-------------|------|--------|
| 1 | `person_id` | uuid | N | **MISSING** | -- | -- |
| 2 | `client_id` | uuid | N | **MISSING** | -- | -- |
| 3 | `first_name` | text | N | **MISSING** | -- | -- |
| 4 | `last_name` | text | N | **MISSING** | -- | -- |
| 5 | `ssn_hash` | text | Y | **MISSING** | -- | -- |
| 6 | `status` | text | N | **MISSING** | -- | -- |
| 7 | `created_at` | timestamp with time zone | N | **MISSING** | -- | -- |
| 8 | `updated_at` | timestamp with time zone | N | **MISSING** | -- | -- |

#### `clnt.plan` -- UNREGISTERED -- 0 rows

Column registry: **UNDOCUMENTED**

| # | Column | Type | Null | Description | Role | Format |
|---|--------|------|------|-------------|------|--------|
| 1 | `plan_id` | uuid | N | **MISSING** | -- | -- |
| 2 | `client_id` | uuid | N | **MISSING** | -- | -- |
| 3 | `benefit_type` | text | N | **MISSING** | -- | -- |
| 4 | `carrier_id` | text | Y | **MISSING** | -- | -- |
| 5 | `effective_date` | date | Y | **MISSING** | -- | -- |
| 6 | `status` | text | N | **MISSING** | -- | -- |
| 7 | `version` | integer | N | **MISSING** | -- | -- |
| 8 | `rate_ee` | numeric | Y | **MISSING** | -- | -- |
| 9 | `rate_es` | numeric | Y | **MISSING** | -- | -- |
| 10 | `rate_ec` | numeric | Y | **MISSING** | -- | -- |
| 11 | `rate_fam` | numeric | Y | **MISSING** | -- | -- |
| 12 | `employer_rate_ee` | numeric | Y | **MISSING** | -- | -- |
| 13 | `employer_rate_es` | numeric | Y | **MISSING** | -- | -- |
| 14 | `employer_rate_ec` | numeric | Y | **MISSING** | -- | -- |
| 15 | `employer_rate_fam` | numeric | Y | **MISSING** | -- | -- |
| 16 | `created_at` | timestamp with time zone | N | **MISSING** | -- | -- |
| 17 | `updated_at` | timestamp with time zone | N | **MISSING** | -- | -- |
| 18 | `source_quote_id` | uuid | Y | **MISSING** | -- | -- |

#### `clnt.plan_quote` -- UNREGISTERED -- 0 rows

Column registry: **UNDOCUMENTED**

| # | Column | Type | Null | Description | Role | Format |
|---|--------|------|------|-------------|------|--------|
| 1 | `plan_quote_id` | uuid | N | **MISSING** | -- | -- |
| 2 | `client_id` | uuid | N | **MISSING** | -- | -- |
| 3 | `benefit_type` | text | N | **MISSING** | -- | -- |
| 4 | `carrier_id` | text | N | **MISSING** | -- | -- |
| 5 | `effective_year` | integer | N | **MISSING** | -- | -- |
| 6 | `rate_ee` | numeric | Y | **MISSING** | -- | -- |
| 7 | `rate_es` | numeric | Y | **MISSING** | -- | -- |
| 8 | `rate_ec` | numeric | Y | **MISSING** | -- | -- |
| 9 | `rate_fam` | numeric | Y | **MISSING** | -- | -- |
| 10 | `source` | text | Y | **MISSING** | -- | -- |
| 11 | `received_date` | date | Y | **MISSING** | -- | -- |
| 12 | `status` | text | N | **MISSING** | -- | -- |
| 13 | `created_at` | timestamp with time zone | N | **MISSING** | -- | -- |

#### `clnt.service_request` -- UNREGISTERED -- 0 rows

Column registry: **UNDOCUMENTED**

| # | Column | Type | Null | Description | Role | Format |
|---|--------|------|------|-------------|------|--------|
| 1 | `service_request_id` | uuid | N | **MISSING** | -- | -- |
| 2 | `client_id` | uuid | N | **MISSING** | -- | -- |
| 3 | `category` | text | N | **MISSING** | -- | -- |
| 4 | `status` | text | N | **MISSING** | -- | -- |
| 5 | `opened_at` | timestamp with time zone | N | **MISSING** | -- | -- |
| 6 | `created_at` | timestamp with time zone | N | **MISSING** | -- | -- |
| 7 | `updated_at` | timestamp with time zone | N | **MISSING** | -- | -- |

#### `clnt.vendor` -- UNREGISTERED -- 0 rows

Column registry: **UNDOCUMENTED**

| # | Column | Type | Null | Description | Role | Format |
|---|--------|------|------|-------------|------|--------|
| 1 | `vendor_id` | uuid | N | **MISSING** | -- | -- |
| 2 | `client_id` | uuid | N | **MISSING** | -- | -- |
| 3 | `vendor_name` | text | N | **MISSING** | -- | -- |
| 4 | `vendor_type` | text | Y | **MISSING** | -- | -- |
| 5 | `created_at` | timestamp with time zone | N | **MISSING** | -- | -- |
| 6 | `updated_at` | timestamp with time zone | N | **MISSING** | -- | -- |

### `lcs` -- Lifecycle Signal System -- event streaming infrastructure (NOT ACTIVE)

**Tables**: 11 | **Total rows**: 32

| Table | Leaf Type | Frozen | Rows | Columns | Documented |
|-------|-----------|--------|------|---------|------------|
| `adapter_registry` | UNREGISTERED |  | 3 | 15 | 0 |
| `domain_pool` | UNREGISTERED |  | 10 | 18 | 0 |
| `err0` | UNREGISTERED |  | 0 | 13 | 0 |
| `event` | UNREGISTERED |  | 0 | 21 | 0 |
| `event_2026_02` | UNREGISTERED |  | 0 | 21 | 0 |
| `event_2026_03` | UNREGISTERED |  | 0 | 21 | 0 |
| `event_2026_04` | UNREGISTERED |  | 0 | 21 | 0 |
| `frame_registry` | UNREGISTERED |  | 10 | 13 | 0 |
| `signal_queue` | UNREGISTERED |  | 0 | 15 | 0 |
| `signal_registry` | UNREGISTERED |  | 9 | 13 | 0 |
| `suppression` | UNREGISTERED |  | 0 | 16 | 0 |

#### `lcs.adapter_registry` -- UNREGISTERED -- 3 rows

Column registry: **UNDOCUMENTED**

| # | Column | Type | Null | Description | Role | Format |
|---|--------|------|------|-------------|------|--------|
| 1 | `adapter_type` | text | N | **MISSING** | -- | -- |
| 2 | `adapter_name` | text | N | **MISSING** | -- | -- |
| 3 | `channel` | text | N | **MISSING** | -- | -- |
| 4 | `direction` | text | N | **MISSING** | -- | -- |
| 5 | `description` | text | Y | **MISSING** | -- | -- |
| 6 | `domain_rotation_config` | jsonb | Y | **MISSING** | -- | -- |
| 7 | `health_status` | text | N | **MISSING** | -- | -- |
| 8 | `daily_cap` | integer | Y | **MISSING** | -- | -- |
| 9 | `sent_today` | integer | N | **MISSING** | -- | -- |
| 10 | `bounce_rate_24h` | numeric | Y | **MISSING** | -- | -- |
| 11 | `complaint_rate_24h` | numeric | Y | **MISSING** | -- | -- |
| 12 | `auto_pause_rules` | jsonb | Y | **MISSING** | -- | -- |
| 13 | `is_active` | boolean | N | **MISSING** | -- | -- |
| 14 | `created_at` | timestamp with time zone | N | **MISSING** | -- | -- |
| 15 | `updated_at` | timestamp with time zone | N | **MISSING** | -- | -- |

#### `lcs.domain_pool` -- UNREGISTERED -- 10 rows

Column registry: **UNDOCUMENTED**

| # | Column | Type | Null | Description | Role | Format |
|---|--------|------|------|-------------|------|--------|
| 1 | `id` | uuid | N | **MISSING** | -- | -- |
| 2 | `domain` | text | N | **MISSING** | -- | -- |
| 3 | `subdomain` | text | N | **MISSING** | -- | -- |
| 4 | `sender_name` | text | N | **MISSING** | -- | -- |
| 5 | `sender_email` | text | N | **MISSING** | -- | -- |
| 6 | `status` | text | N | **MISSING** | -- | -- |
| 7 | `warmup_day` | integer | N | **MISSING** | -- | -- |
| 8 | `daily_cap` | integer | N | **MISSING** | -- | -- |
| 9 | `sent_today` | integer | N | **MISSING** | -- | -- |
| 10 | `bounce_rate_24h` | numeric | N | **MISSING** | -- | -- |
| 11 | `complaint_rate_24h` | numeric | N | **MISSING** | -- | -- |
| 12 | `last_sent_at` | timestamp with time zone | Y | **MISSING** | -- | -- |
| 13 | `last_health_check_at` | timestamp with time zone | Y | **MISSING** | -- | -- |
| 14 | `paused_at` | timestamp with time zone | Y | **MISSING** | -- | -- |
| 15 | `pause_reason` | text | Y | **MISSING** | -- | -- |
| 16 | `mailgun_verified` | boolean | N | **MISSING** | -- | -- |
| 17 | `created_at` | timestamp with time zone | N | **MISSING** | -- | -- |
| 18 | `updated_at` | timestamp with time zone | N | **MISSING** | -- | -- |

#### `lcs.err0` -- UNREGISTERED -- 0 rows

Column registry: **UNDOCUMENTED**

| # | Column | Type | Null | Description | Role | Format |
|---|--------|------|------|-------------|------|--------|
| 1 | `error_id` | uuid | N | **MISSING** | -- | -- |
| 2 | `message_run_id` | text | N | **MISSING** | -- | -- |
| 3 | `communication_id` | text | Y | **MISSING** | -- | -- |
| 4 | `sovereign_company_id` | text | Y | **MISSING** | -- | -- |
| 5 | `failure_type` | text | N | **MISSING** | -- | -- |
| 6 | `failure_message` | text | N | **MISSING** | -- | -- |
| 7 | `lifecycle_phase` | text | Y | **MISSING** | -- | -- |
| 8 | `adapter_type` | text | Y | **MISSING** | -- | -- |
| 9 | `orbt_strike_number` | integer | Y | **MISSING** | -- | -- |
| 10 | `orbt_action_taken` | text | Y | **MISSING** | -- | -- |
| 11 | `orbt_alt_channel_eligible` | boolean | Y | **MISSING** | -- | -- |
| 12 | `orbt_alt_channel_reason` | text | Y | **MISSING** | -- | -- |
| 13 | `created_at` | timestamp with time zone | N | **MISSING** | -- | -- |

#### `lcs.event` -- UNREGISTERED -- 0 rows

Column registry: **UNDOCUMENTED**

| # | Column | Type | Null | Description | Role | Format |
|---|--------|------|------|-------------|------|--------|
| 1 | `communication_id` | text | N | **MISSING** | -- | -- |
| 2 | `message_run_id` | text | N | **MISSING** | -- | -- |
| 3 | `sovereign_company_id` | uuid | N | **MISSING** | -- | -- |
| 4 | `entity_type` | text | N | **MISSING** | -- | -- |
| 5 | `entity_id` | uuid | N | **MISSING** | -- | -- |
| 6 | `signal_set_hash` | text | N | **MISSING** | -- | -- |
| 7 | `frame_id` | text | N | **MISSING** | -- | -- |
| 8 | `adapter_type` | text | N | **MISSING** | -- | -- |
| 9 | `channel` | text | N | **MISSING** | -- | -- |
| 10 | `delivery_status` | text | N | **MISSING** | -- | -- |
| 11 | `lifecycle_phase` | text | N | **MISSING** | -- | -- |
| 12 | `event_type` | text | N | **MISSING** | -- | -- |
| 13 | `lane` | text | N | **MISSING** | -- | -- |
| 14 | `agent_number` | text | N | **MISSING** | -- | -- |
| 15 | `step_number` | integer | N | **MISSING** | -- | -- |
| 16 | `step_name` | text | N | **MISSING** | -- | -- |
| 17 | `payload` | jsonb | Y | **MISSING** | -- | -- |
| 18 | `adapter_response` | jsonb | Y | **MISSING** | -- | -- |
| 19 | `intelligence_tier` | integer | Y | **MISSING** | -- | -- |
| 20 | `sender_identity` | text | Y | **MISSING** | -- | -- |
| 21 | `created_at` | timestamp with time zone | N | **MISSING** | -- | -- |

#### `lcs.event_2026_02` -- UNREGISTERED -- 0 rows

Column registry: **UNDOCUMENTED**

| # | Column | Type | Null | Description | Role | Format |
|---|--------|------|------|-------------|------|--------|
| 1 | `communication_id` | text | N | **MISSING** | -- | -- |
| 2 | `message_run_id` | text | N | **MISSING** | -- | -- |
| 3 | `sovereign_company_id` | uuid | N | **MISSING** | -- | -- |
| 4 | `entity_type` | text | N | **MISSING** | -- | -- |
| 5 | `entity_id` | uuid | N | **MISSING** | -- | -- |
| 6 | `signal_set_hash` | text | N | **MISSING** | -- | -- |
| 7 | `frame_id` | text | N | **MISSING** | -- | -- |
| 8 | `adapter_type` | text | N | **MISSING** | -- | -- |
| 9 | `channel` | text | N | **MISSING** | -- | -- |
| 10 | `delivery_status` | text | N | **MISSING** | -- | -- |
| 11 | `lifecycle_phase` | text | N | **MISSING** | -- | -- |
| 12 | `event_type` | text | N | **MISSING** | -- | -- |
| 13 | `lane` | text | N | **MISSING** | -- | -- |
| 14 | `agent_number` | text | N | **MISSING** | -- | -- |
| 15 | `step_number` | integer | N | **MISSING** | -- | -- |
| 16 | `step_name` | text | N | **MISSING** | -- | -- |
| 17 | `payload` | jsonb | Y | **MISSING** | -- | -- |
| 18 | `adapter_response` | jsonb | Y | **MISSING** | -- | -- |
| 19 | `intelligence_tier` | integer | Y | **MISSING** | -- | -- |
| 20 | `sender_identity` | text | Y | **MISSING** | -- | -- |
| 21 | `created_at` | timestamp with time zone | N | **MISSING** | -- | -- |

#### `lcs.event_2026_03` -- UNREGISTERED -- 0 rows

Column registry: **UNDOCUMENTED**

| # | Column | Type | Null | Description | Role | Format |
|---|--------|------|------|-------------|------|--------|
| 1 | `communication_id` | text | N | **MISSING** | -- | -- |
| 2 | `message_run_id` | text | N | **MISSING** | -- | -- |
| 3 | `sovereign_company_id` | uuid | N | **MISSING** | -- | -- |
| 4 | `entity_type` | text | N | **MISSING** | -- | -- |
| 5 | `entity_id` | uuid | N | **MISSING** | -- | -- |
| 6 | `signal_set_hash` | text | N | **MISSING** | -- | -- |
| 7 | `frame_id` | text | N | **MISSING** | -- | -- |
| 8 | `adapter_type` | text | N | **MISSING** | -- | -- |
| 9 | `channel` | text | N | **MISSING** | -- | -- |
| 10 | `delivery_status` | text | N | **MISSING** | -- | -- |
| 11 | `lifecycle_phase` | text | N | **MISSING** | -- | -- |
| 12 | `event_type` | text | N | **MISSING** | -- | -- |
| 13 | `lane` | text | N | **MISSING** | -- | -- |
| 14 | `agent_number` | text | N | **MISSING** | -- | -- |
| 15 | `step_number` | integer | N | **MISSING** | -- | -- |
| 16 | `step_name` | text | N | **MISSING** | -- | -- |
| 17 | `payload` | jsonb | Y | **MISSING** | -- | -- |
| 18 | `adapter_response` | jsonb | Y | **MISSING** | -- | -- |
| 19 | `intelligence_tier` | integer | Y | **MISSING** | -- | -- |
| 20 | `sender_identity` | text | Y | **MISSING** | -- | -- |
| 21 | `created_at` | timestamp with time zone | N | **MISSING** | -- | -- |

#### `lcs.event_2026_04` -- UNREGISTERED -- 0 rows

Column registry: **UNDOCUMENTED**

| # | Column | Type | Null | Description | Role | Format |
|---|--------|------|------|-------------|------|--------|
| 1 | `communication_id` | text | N | **MISSING** | -- | -- |
| 2 | `message_run_id` | text | N | **MISSING** | -- | -- |
| 3 | `sovereign_company_id` | uuid | N | **MISSING** | -- | -- |
| 4 | `entity_type` | text | N | **MISSING** | -- | -- |
| 5 | `entity_id` | uuid | N | **MISSING** | -- | -- |
| 6 | `signal_set_hash` | text | N | **MISSING** | -- | -- |
| 7 | `frame_id` | text | N | **MISSING** | -- | -- |
| 8 | `adapter_type` | text | N | **MISSING** | -- | -- |
| 9 | `channel` | text | N | **MISSING** | -- | -- |
| 10 | `delivery_status` | text | N | **MISSING** | -- | -- |
| 11 | `lifecycle_phase` | text | N | **MISSING** | -- | -- |
| 12 | `event_type` | text | N | **MISSING** | -- | -- |
| 13 | `lane` | text | N | **MISSING** | -- | -- |
| 14 | `agent_number` | text | N | **MISSING** | -- | -- |
| 15 | `step_number` | integer | N | **MISSING** | -- | -- |
| 16 | `step_name` | text | N | **MISSING** | -- | -- |
| 17 | `payload` | jsonb | Y | **MISSING** | -- | -- |
| 18 | `adapter_response` | jsonb | Y | **MISSING** | -- | -- |
| 19 | `intelligence_tier` | integer | Y | **MISSING** | -- | -- |
| 20 | `sender_identity` | text | Y | **MISSING** | -- | -- |
| 21 | `created_at` | timestamp with time zone | N | **MISSING** | -- | -- |

#### `lcs.frame_registry` -- UNREGISTERED -- 10 rows

Column registry: **UNDOCUMENTED**

| # | Column | Type | Null | Description | Role | Format |
|---|--------|------|------|-------------|------|--------|
| 1 | `frame_id` | text | N | **MISSING** | -- | -- |
| 2 | `frame_name` | text | N | **MISSING** | -- | -- |
| 3 | `lifecycle_phase` | text | N | **MISSING** | -- | -- |
| 4 | `frame_type` | text | N | **MISSING** | -- | -- |
| 5 | `tier` | integer | N | **MISSING** | -- | -- |
| 6 | `required_fields` | jsonb | N | **MISSING** | -- | -- |
| 7 | `fallback_frame` | text | Y | **MISSING** | -- | -- |
| 8 | `channel` | text | Y | **MISSING** | -- | -- |
| 9 | `step_in_sequence` | integer | Y | **MISSING** | -- | -- |
| 10 | `description` | text | Y | **MISSING** | -- | -- |
| 11 | `is_active` | boolean | N | **MISSING** | -- | -- |
| 12 | `created_at` | timestamp with time zone | N | **MISSING** | -- | -- |
| 13 | `updated_at` | timestamp with time zone | N | **MISSING** | -- | -- |

#### `lcs.signal_queue` -- UNREGISTERED -- 0 rows

Column registry: **UNDOCUMENTED**

| # | Column | Type | Null | Description | Role | Format |
|---|--------|------|------|-------------|------|--------|
| 1 | `id` | uuid | N | **MISSING** | -- | -- |
| 2 | `signal_set_hash` | text | N | **MISSING** | -- | -- |
| 3 | `signal_category` | text | N | **MISSING** | -- | -- |
| 4 | `sovereign_company_id` | uuid | N | **MISSING** | -- | -- |
| 5 | `lifecycle_phase` | text | N | **MISSING** | -- | -- |
| 6 | `preferred_channel` | text | Y | **MISSING** | -- | -- |
| 7 | `preferred_lane` | text | Y | **MISSING** | -- | -- |
| 8 | `agent_number` | text | Y | **MISSING** | -- | -- |
| 9 | `signal_data` | jsonb | N | **MISSING** | -- | -- |
| 10 | `source_hub` | text | N | **MISSING** | -- | -- |
| 11 | `source_signal_id` | uuid | Y | **MISSING** | -- | -- |
| 12 | `status` | text | N | **MISSING** | -- | -- |
| 13 | `priority` | integer | N | **MISSING** | -- | -- |
| 14 | `created_at` | timestamp with time zone | N | **MISSING** | -- | -- |
| 15 | `processed_at` | timestamp with time zone | Y | **MISSING** | -- | -- |

#### `lcs.signal_registry` -- UNREGISTERED -- 9 rows

Column registry: **UNDOCUMENTED**

| # | Column | Type | Null | Description | Role | Format |
|---|--------|------|------|-------------|------|--------|
| 1 | `signal_set_hash` | text | N | **MISSING** | -- | -- |
| 2 | `signal_name` | text | N | **MISSING** | -- | -- |
| 3 | `lifecycle_phase` | text | N | **MISSING** | -- | -- |
| 4 | `signal_category` | text | N | **MISSING** | -- | -- |
| 5 | `description` | text | Y | **MISSING** | -- | -- |
| 6 | `data_fetched_at` | timestamp with time zone | Y | **MISSING** | -- | -- |
| 7 | `data_expires_at` | timestamp with time zone | Y | **MISSING** | -- | -- |
| 8 | `freshness_window` | interval | N | **MISSING** | -- | -- |
| 9 | `signal_validity_score` | numeric | Y | **MISSING** | -- | -- |
| 10 | `validity_threshold` | numeric | N | **MISSING** | -- | -- |
| 11 | `is_active` | boolean | N | **MISSING** | -- | -- |
| 12 | `created_at` | timestamp with time zone | N | **MISSING** | -- | -- |
| 13 | `updated_at` | timestamp with time zone | N | **MISSING** | -- | -- |

#### `lcs.suppression` -- UNREGISTERED -- 0 rows

Column registry: **UNDOCUMENTED**

| # | Column | Type | Null | Description | Role | Format |
|---|--------|------|------|-------------|------|--------|
| 1 | `id` | uuid | N | **MISSING** | -- | -- |
| 2 | `email` | text | Y | **MISSING** | -- | -- |
| 3 | `entity_id` | uuid | Y | **MISSING** | -- | -- |
| 4 | `sovereign_company_id` | uuid | Y | **MISSING** | -- | -- |
| 5 | `suppression_state` | text | N | **MISSING** | -- | -- |
| 6 | `never_contact` | boolean | N | **MISSING** | -- | -- |
| 7 | `unsubscribed` | boolean | N | **MISSING** | -- | -- |
| 8 | `hard_bounced` | boolean | N | **MISSING** | -- | -- |
| 9 | `complained` | boolean | N | **MISSING** | -- | -- |
| 10 | `suppression_source` | text | N | **MISSING** | -- | -- |
| 11 | `source_event_id` | text | Y | **MISSING** | -- | -- |
| 12 | `channel` | text | Y | **MISSING** | -- | -- |
| 13 | `domain` | text | Y | **MISSING** | -- | -- |
| 14 | `created_at` | timestamp with time zone | N | **MISSING** | -- | -- |
| 15 | `updated_at` | timestamp with time zone | N | **MISSING** | -- | -- |
| 16 | `expires_at` | timestamp with time zone | Y | **MISSING** | -- | -- |

### `ref` -- Reference Data -- county FIPS codes, ZIP-county mapping

**Tables**: 2 | **Total rows**: 49,863

| Table | Leaf Type | Frozen | Rows | Columns | Documented |
|-------|-----------|--------|------|---------|------------|
| `county_fips` | SYSTEM |  | 3,222 | 8 | 0 |
| `zip_county_map` | SYSTEM |  | 46,641 | 5 | 0 |

#### `ref.county_fips` -- SYSTEM -- 3,222 rows

Column registry: **UNDOCUMENTED**

| # | Column | Type | Null | Description | Role | Format |
|---|--------|------|------|-------------|------|--------|
| 1 | `county_fips` | character(5) | N | **MISSING** | -- | -- |
| 2 | `state_fips` | character(2) | N | **MISSING** | -- | -- |
| 3 | `county_code` | character(3) | N | **MISSING** | -- | -- |
| 4 | `county_name` | text | N | **MISSING** | -- | -- |
| 5 | `state_name` | text | N | **MISSING** | -- | -- |
| 6 | `source` | text | Y | **MISSING** | -- | -- |
| 7 | `source_year` | integer | N | **MISSING** | -- | -- |
| 8 | `created_at` | timestamp without time zone | Y | **MISSING** | -- | -- |

#### `ref.zip_county_map` -- SYSTEM -- 46,641 rows

Column registry: **UNDOCUMENTED**

| # | Column | Type | Null | Description | Role | Format |
|---|--------|------|------|-------------|------|--------|
| 1 | `zip` | character(5) | N | **MISSING** | -- | -- |
| 2 | `county_fips` | character(5) | N | **MISSING** | -- | -- |
| 3 | `is_primary` | boolean | Y | **MISSING** | -- | -- |
| 4 | `source` | text | Y | **MISSING** | -- | -- |
| 5 | `created_at` | timestamp without time zone | Y | **MISSING** | -- | -- |

### `reference` -- Reference Data -- US ZIP code master list

**Tables**: 1 | **Total rows**: 41,551

| Table | Leaf Type | Frozen | Rows | Columns | Documented |
|-------|-----------|--------|------|---------|------------|
| `us_zip_codes` | REGISTRY |  | 41,551 | 39 | 0 |

#### `reference.us_zip_codes` -- REGISTRY -- 41,551 rows

Column registry: **UNDOCUMENTED**

| # | Column | Type | Null | Description | Role | Format |
|---|--------|------|------|-------------|------|--------|
| 1 | `zip` | text | N | **MISSING** | -- | -- |
| 2 | `lat` | numeric | Y | **MISSING** | -- | -- |
| 3 | `lng` | numeric | Y | **MISSING** | -- | -- |
| 4 | `city` | text | Y | **MISSING** | -- | -- |
| 5 | `state_id` | text | Y | **MISSING** | -- | -- |
| 6 | `state_name` | text | Y | **MISSING** | -- | -- |
| 7 | `zcta` | boolean | Y | **MISSING** | -- | -- |
| 8 | `parent_zcta` | text | Y | **MISSING** | -- | -- |
| 9 | `population` | integer | Y | **MISSING** | -- | -- |
| 10 | `density` | numeric | Y | **MISSING** | -- | -- |
| 11 | `county_fips` | text | Y | **MISSING** | -- | -- |
| 12 | `county_name` | text | Y | **MISSING** | -- | -- |
| 13 | `county_weights` | jsonb | Y | **MISSING** | -- | -- |
| 14 | `county_names_all` | text | Y | **MISSING** | -- | -- |
| 15 | `county_fips_all` | text | Y | **MISSING** | -- | -- |
| 16 | `imprecise` | boolean | Y | **MISSING** | -- | -- |
| 17 | `military` | boolean | Y | **MISSING** | -- | -- |
| 18 | `timezone` | text | Y | **MISSING** | -- | -- |
| 19 | `age_median` | numeric | Y | **MISSING** | -- | -- |
| 20 | `male` | numeric | Y | **MISSING** | -- | -- |
| 21 | `female` | numeric | Y | **MISSING** | -- | -- |
| 22 | `married` | numeric | Y | **MISSING** | -- | -- |
| 23 | `family_size` | numeric | Y | **MISSING** | -- | -- |
| 24 | `income_household_median` | integer | Y | **MISSING** | -- | -- |
| 25 | `income_household_six_figure` | numeric | Y | **MISSING** | -- | -- |
| 26 | `home_ownership` | numeric | Y | **MISSING** | -- | -- |
| 27 | `home_value` | integer | Y | **MISSING** | -- | -- |
| 28 | `rent_median` | integer | Y | **MISSING** | -- | -- |
| 29 | `education_college_or_above` | numeric | Y | **MISSING** | -- | -- |
| 30 | `labor_force_participation` | numeric | Y | **MISSING** | -- | -- |
| 31 | `unemployment_rate` | numeric | Y | **MISSING** | -- | -- |
| 32 | `race_white` | numeric | Y | **MISSING** | -- | -- |
| 33 | `race_black` | numeric | Y | **MISSING** | -- | -- |
| 34 | `race_asian` | numeric | Y | **MISSING** | -- | -- |
| 35 | `race_native` | numeric | Y | **MISSING** | -- | -- |
| 36 | `race_pacific` | numeric | Y | **MISSING** | -- | -- |
| 37 | `race_other` | numeric | Y | **MISSING** | -- | -- |
| 38 | `race_multiple` | numeric | Y | **MISSING** | -- | -- |
| 39 | `created_at` | timestamp with time zone | Y | **MISSING** | -- | -- |

### `shq` -- System Health -- audit log, error master, governance monitoring

**Tables**: 3 | **Total rows**: 95,524
**Views**: 8 -- v_dol_enrichment_queue, v_error_summary_24h, vw_blocking_errors_by_outreach, vw_error_governance_summary, vw_error_resolution_rate, vw_promotion_readiness, vw_promotion_readiness_summary, vw_unresolved_errors_by_source

| Table | Leaf Type | Frozen | Rows | Columns | Documented |
|-------|-----------|--------|------|---------|------------|
| `audit_log` | SYSTEM |  | 1,609 | 5 | 0 |
| `error_master` | SYSTEM |  | 93,915 | 16 | 0 |
| `error_master_archive` | SYSTEM |  | 0 | 21 | 0 |

#### `shq.audit_log` -- SYSTEM -- 1,609 rows

Column registry: **UNDOCUMENTED**

| # | Column | Type | Null | Description | Role | Format |
|---|--------|------|------|-------------|------|--------|
| 1 | `id` | integer | N | **MISSING** | -- | -- |
| 2 | `event_type` | character varying(255) | N | **MISSING** | -- | -- |
| 3 | `event_source` | character varying(255) | N | **MISSING** | -- | -- |
| 4 | `details` | jsonb | Y | **MISSING** | -- | -- |
| 5 | `created_at` | timestamp without time zone | Y | **MISSING** | -- | -- |

#### `shq.error_master` -- SYSTEM -- 93,915 rows

Column registry: **UNDOCUMENTED**

| # | Column | Type | Null | Description | Role | Format |
|---|--------|------|------|-------------|------|--------|
| 1 | `error_id` | uuid | N | **MISSING** | -- | -- |
| 2 | `process_id` | character varying(50) | N | **MISSING** | -- | -- |
| 3 | `agent_id` | character varying(50) | N | **MISSING** | -- | -- |
| 4 | `severity` | character varying(20) | N | **MISSING** | -- | -- |
| 5 | `error_type` | character varying(50) | N | **MISSING** | -- | -- |
| 6 | `message` | text | N | **MISSING** | -- | -- |
| 7 | `company_unique_id` | character varying(50) | Y | **MISSING** | -- | -- |
| 8 | `outreach_context_id` | character varying(100) | Y | **MISSING** | -- | -- |
| 9 | `air_event_id` | character varying(50) | Y | **MISSING** | -- | -- |
| 10 | `context` | jsonb | Y | **MISSING** | -- | -- |
| 11 | `created_at` | timestamp with time zone | N | **MISSING** | -- | -- |
| 12 | `resolved_at` | timestamp with time zone | Y | **MISSING** | -- | -- |
| 13 | `resolution_type` | character varying(30) | Y | **MISSING** | -- | -- |
| 14 | `disposition` | USER-DEFINED | Y | **MISSING** | -- | -- |
| 15 | `archived_at` | timestamp with time zone | Y | **MISSING** | -- | -- |
| 16 | `ttl_tier` | USER-DEFINED | Y | **MISSING** | -- | -- |

#### `shq.error_master_archive` -- SYSTEM -- 0 rows

Column registry: **UNDOCUMENTED**

| # | Column | Type | Null | Description | Role | Format |
|---|--------|------|------|-------------|------|--------|
| 1 | `id` | integer | N | **MISSING** | -- | -- |
| 2 | `error_id` | uuid | N | **MISSING** | -- | -- |
| 3 | `process_id` | text | Y | **MISSING** | -- | -- |
| 4 | `agent_id` | text | Y | **MISSING** | -- | -- |
| 5 | `severity` | text | Y | **MISSING** | -- | -- |
| 6 | `error_type` | text | Y | **MISSING** | -- | -- |
| 7 | `message` | text | Y | **MISSING** | -- | -- |
| 8 | `company_unique_id` | text | Y | **MISSING** | -- | -- |
| 9 | `outreach_context_id` | text | Y | **MISSING** | -- | -- |
| 10 | `air_event_id` | text | Y | **MISSING** | -- | -- |
| 11 | `context` | jsonb | Y | **MISSING** | -- | -- |
| 12 | `created_at` | timestamp with time zone | Y | **MISSING** | -- | -- |
| 13 | `resolved_at` | timestamp with time zone | Y | **MISSING** | -- | -- |
| 14 | `resolution_type` | text | Y | **MISSING** | -- | -- |
| 15 | `disposition` | USER-DEFINED | Y | **MISSING** | -- | -- |
| 16 | `ttl_tier` | USER-DEFINED | Y | **MISSING** | -- | -- |
| 17 | `archived_at` | timestamp with time zone | N | **MISSING** | -- | -- |
| 18 | `archived_by` | text | Y | **MISSING** | -- | -- |
| 19 | `archive_reason` | text | Y | **MISSING** | -- | -- |
| 20 | `final_disposition` | USER-DEFINED | Y | **MISSING** | -- | -- |
| 21 | `retention_expires_at` | timestamp with time zone | Y | **MISSING** | -- | -- |

### `talent_flow` -- DEPRECATED -- executive movement tracking, replaced by bit.movement_events

**Tables**: 2 | **Total rows**: 0

| Table | Leaf Type | Frozen | Rows | Columns | Documented |
|-------|-----------|--------|------|---------|------------|
| `movement_history` | DEPRECATED |  | 0 | 13 | 0 |
| `movements` | DEPRECATED |  | 0 | 12 | 0 |

#### `talent_flow.movement_history` -- DEPRECATED -- 0 rows

Column registry: **UNDOCUMENTED**

| # | Column | Type | Null | Description | Role | Format |
|---|--------|------|------|-------------|------|--------|
| 1 | `history_id` | uuid | N | **MISSING** | -- | -- |
| 2 | `person_identifier` | text | N | **MISSING** | -- | -- |
| 3 | `from_outreach_id` | uuid | Y | **MISSING** | -- | -- |
| 4 | `to_outreach_id` | uuid | Y | **MISSING** | -- | -- |
| 5 | `movement_type` | character varying(30) | Y | **MISSING** | -- | -- |
| 6 | `detected_at` | timestamp with time zone | Y | **MISSING** | -- | -- |
| 7 | `detection_source` | character varying(50) | Y | **MISSING** | -- | -- |
| 8 | `processed_at` | timestamp with time zone | Y | **MISSING** | -- | -- |
| 9 | `signal_emitted` | character varying(50) | Y | **MISSING** | -- | -- |
| 10 | `bit_event_created` | boolean | Y | **MISSING** | -- | -- |
| 11 | `correlation_id` | uuid | Y | **MISSING** | -- | -- |
| 12 | `process_id` | uuid | Y | **MISSING** | -- | -- |
| 13 | `created_at` | timestamp with time zone | Y | **MISSING** | -- | -- |

#### `talent_flow.movements` -- DEPRECATED -- 0 rows

Column registry: **UNDOCUMENTED**

| # | Column | Type | Null | Description | Role | Format |
|---|--------|------|------|-------------|------|--------|
| 1 | `movement_id` | uuid | N | **MISSING** | -- | -- |
| 2 | `contact_id` | uuid | N | **MISSING** | -- | -- |
| 3 | `movement_type` | character varying(20) | N | **MISSING** | -- | -- |
| 4 | `old_company_id` | text | Y | **MISSING** | -- | -- |
| 5 | `new_company_id` | text | Y | **MISSING** | -- | -- |
| 6 | `old_title` | text | Y | **MISSING** | -- | -- |
| 7 | `new_title` | text | Y | **MISSING** | -- | -- |
| 8 | `confidence_score` | integer | N | **MISSING** | -- | -- |
| 9 | `detected_at` | timestamp with time zone | N | **MISSING** | -- | -- |
| 10 | `detected_source` | character varying(50) | N | **MISSING** | -- | -- |
| 11 | `created_at` | timestamp with time zone | N | **MISSING** | -- | -- |
| 12 | `updated_at` | timestamp with time zone | N | **MISSING** | -- | -- |

### `catalog` -- System Catalog -- schema metadata for AI/tooling reference

**Tables**: 4 | **Total rows**: 762
**Views**: 3 -- v_ai_reference, v_schema_summary, v_searchable_columns

| Table | Leaf Type | Frozen | Rows | Columns | Documented |
|-------|-----------|--------|------|---------|------------|
| `columns` | SYSTEM |  | 725 | 27 | 0 |
| `relationships` | SYSTEM |  | 0 | 10 | 0 |
| `schemas` | SYSTEM |  | 6 | 8 | 0 |
| `tables` | SYSTEM |  | 31 | 15 | 0 |

#### `catalog.columns` -- SYSTEM -- 725 rows

Column registry: **UNDOCUMENTED**

| # | Column | Type | Null | Description | Role | Format |
|---|--------|------|------|-------------|------|--------|
| 1 | `column_id` | character varying(200) | N | **MISSING** | -- | -- |
| 2 | `table_id` | character varying(100) | N | **MISSING** | -- | -- |
| 3 | `column_name` | character varying(100) | N | **MISSING** | -- | -- |
| 4 | `ordinal_position` | integer | Y | **MISSING** | -- | -- |
| 5 | `data_type` | character varying(50) | N | **MISSING** | -- | -- |
| 6 | `max_length` | integer | Y | **MISSING** | -- | -- |
| 7 | `is_nullable` | boolean | Y | **MISSING** | -- | -- |
| 8 | `default_value` | text | Y | **MISSING** | -- | -- |
| 9 | `description` | text | N | **MISSING** | -- | -- |
| 10 | `business_name` | character varying(100) | Y | **MISSING** | -- | -- |
| 11 | `business_definition` | text | Y | **MISSING** | -- | -- |
| 12 | `format_pattern` | character varying(100) | Y | **MISSING** | -- | -- |
| 13 | `format_example` | character varying(200) | Y | **MISSING** | -- | -- |
| 14 | `valid_values` | ARRAY | Y | **MISSING** | -- | -- |
| 15 | `validation_rule` | text | Y | **MISSING** | -- | -- |
| 16 | `is_primary_key` | boolean | Y | **MISSING** | -- | -- |
| 17 | `is_foreign_key` | boolean | Y | **MISSING** | -- | -- |
| 18 | `references_column` | character varying(200) | Y | **MISSING** | -- | -- |
| 19 | `pii_classification` | character varying(20) | Y | **MISSING** | -- | -- |
| 20 | `data_sensitivity` | character varying(20) | Y | **MISSING** | -- | -- |
| 21 | `source_system` | character varying(100) | Y | **MISSING** | -- | -- |
| 22 | `source_field` | character varying(200) | Y | **MISSING** | -- | -- |
| 23 | `transformation_logic` | text | Y | **MISSING** | -- | -- |
| 24 | `tags` | ARRAY | Y | **MISSING** | -- | -- |
| 25 | `synonyms` | ARRAY | Y | **MISSING** | -- | -- |
| 26 | `created_at` | timestamp without time zone | Y | **MISSING** | -- | -- |
| 27 | `updated_at` | timestamp without time zone | Y | **MISSING** | -- | -- |

#### `catalog.relationships` -- SYSTEM -- 0 rows

Column registry: **UNDOCUMENTED**

| # | Column | Type | Null | Description | Role | Format |
|---|--------|------|------|-------------|------|--------|
| 1 | `relationship_id` | integer | N | **MISSING** | -- | -- |
| 2 | `from_table_id` | character varying(100) | N | **MISSING** | -- | -- |
| 3 | `from_column_id` | character varying(200) | N | **MISSING** | -- | -- |
| 4 | `to_table_id` | character varying(100) | N | **MISSING** | -- | -- |
| 5 | `to_column_id` | character varying(200) | N | **MISSING** | -- | -- |
| 6 | `relationship_type` | character varying(20) | N | **MISSING** | -- | -- |
| 7 | `relationship_name` | character varying(100) | Y | **MISSING** | -- | -- |
| 8 | `description` | text | Y | **MISSING** | -- | -- |
| 9 | `is_enforced` | boolean | Y | **MISSING** | -- | -- |
| 10 | `created_at` | timestamp without time zone | Y | **MISSING** | -- | -- |

#### `catalog.schemas` -- SYSTEM -- 6 rows

Column registry: **UNDOCUMENTED**

| # | Column | Type | Null | Description | Role | Format |
|---|--------|------|------|-------------|------|--------|
| 1 | `schema_id` | character varying(50) | N | **MISSING** | -- | -- |
| 2 | `schema_name` | character varying(50) | N | **MISSING** | -- | -- |
| 3 | `schema_type` | character varying(20) | N | **MISSING** | -- | -- |
| 4 | `description` | text | N | **MISSING** | -- | -- |
| 5 | `parent_schema` | character varying(50) | Y | **MISSING** | -- | -- |
| 6 | `owner` | character varying(100) | Y | **MISSING** | -- | -- |
| 7 | `created_at` | timestamp without time zone | Y | **MISSING** | -- | -- |
| 8 | `updated_at` | timestamp without time zone | Y | **MISSING** | -- | -- |

#### `catalog.tables` -- SYSTEM -- 31 rows

Column registry: **UNDOCUMENTED**

| # | Column | Type | Null | Description | Role | Format |
|---|--------|------|------|-------------|------|--------|
| 1 | `table_id` | character varying(100) | N | **MISSING** | -- | -- |
| 2 | `schema_id` | character varying(50) | N | **MISSING** | -- | -- |
| 3 | `table_name` | character varying(100) | N | **MISSING** | -- | -- |
| 4 | `table_type` | character varying(20) | N | **MISSING** | -- | -- |
| 5 | `description` | text | N | **MISSING** | -- | -- |
| 6 | `business_purpose` | text | Y | **MISSING** | -- | -- |
| 7 | `primary_key` | character varying(100) | Y | **MISSING** | -- | -- |
| 8 | `foreign_keys` | jsonb | Y | **MISSING** | -- | -- |
| 9 | `row_count_approx` | integer | Y | **MISSING** | -- | -- |
| 10 | `data_source` | character varying(100) | Y | **MISSING** | -- | -- |
| 11 | `refresh_frequency` | character varying(50) | Y | **MISSING** | -- | -- |
| 12 | `owner` | character varying(100) | Y | **MISSING** | -- | -- |
| 13 | `tags` | ARRAY | Y | **MISSING** | -- | -- |
| 14 | `created_at` | timestamp without time zone | Y | **MISSING** | -- | -- |
| 15 | `updated_at` | timestamp without time zone | Y | **MISSING** | -- | -- |

### `archive` -- Archive -- archived tables from CTB cleanup and sovereign cleanup

**Tables**: 96 | **Total rows**: 351,734

*96 archive tables total, 44 with data. Column details omitted.*

| Table | Rows |
|-------|------|
| people_people_staging_ctb | 139,861 |
| company_company_master_ctb | 74,641 |
| company_target_orphaned_archive_ctb | 52,812 |
| company_url_discovery_failures_ctb | 42,348 |
| people_paid_enrichment_queue_ctb | 32,011 |
| outreach_orphan_archive_ctb | 2,709 |
| people_slot_assignment_history_ctb | 1,370 |
| company_company_slots_ctb | 1,359 |
| people_people_resolution_queue_ctb | 1,206 |
| people_slot_orphan_snapshot_ctb | 1,053 |
| shq_schema_registry_761013 | 688 |
| marketing_company_master_ctb | 512 |
| marketing_failed_email_verification_ctb | 310 |
| marketing_failed_slot_assignment_ctb | 222 |
| people_company_resolution_log_ctb | 155 |
| marketing_people_master_ctb | 149 |
| people_slot_quarantine_ctb | 75 |
| marketing_marketing_company_column_metadata_755327 | 54 |
| archive_log | 45 |
| marketing_failed_company_match_ctb | 32 |
| people_people_invalid_ctb | 21 |
| outreach_dol_url_enrichment_ctb | 16 |
| shq_table_relationships_761234 | 14 |
| people_people_promotion_audit_ctb | 9 |
| company_message_key_reference_ctb | 8 |
| intake_enrichment_handler_registry_752947 | 8 |
| marketing_failed_no_pattern_ctb | 6 |
| marketing_failed_low_confidence_ctb | 5 |
| bit_signal_752056 | 4 |
| people_contact_757489 | 4 |
| company_company_slot_752509 | 3 |
| marketing_campaign_contact_754523 | 3 |
| marketing_message_log_757035 | 3 |
| people_contact_verification_757966 | 3 |
| company_marketing_company_752726 | 2 |
| marketing_marketing_apollo_raw_755096 | 2 |
| people_marketing_people_758180 | 2 |
| shq_schema_audit_log_760790 | 2 |
| vault_contact_promotions_761442 | 2 |
| company_company_752287 | 1 |
| intake_validation_audit_log_753371 | 1 |
| marketing_ac_handoff_753855 | 1 |
| marketing_booking_event_754073 | 1 |
| marketing_campaign_754289 | 1 |
