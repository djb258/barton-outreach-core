# Neon Database ERD Reference
**Generated**: 2025-01-16  
**Database**: Neon PostgreSQL (via Doppler barton-outreach-core/dev)  
**Total Tables**: 129  
**Total Rows**: 3,145,081  

---

## Schema Summary

| Schema | Tables | Rows | Description |
|--------|--------|------|-------------|
| `archive` | 46 | 844 | Archived/historical data |
| `bit` | 3 | 0 | BIT scoring tables (empty) |
| `catalog` | 4 | 762 | Catalog/reference data |
| `cl` | 10 | 484,143 | Company lifecycle data |
| `clay` | 2 | 0 | Clay enrichment (empty) |
| `company` | 10 | 75,380 | Company master data |
| `dol` | 9 | 2,432,366 | **DOL Form 5500 filings** |
| `intake` | 5 | 62,721 | Raw intake staging |
| `marketing` | 8 | 1,748 | Marketing pipeline |
| `neon_auth` | 1 | 0 | Neon auth sync (empty) |
| `outreach` | 12 | 84,323 | **Core outreach hub** |
| `outreach_ctx` | 3 | 3 | **Outreach contexts** |
| `people` | 7 | 2,756 | People/contacts master |
| `ple` | 3 | 0 | PLE cycles (empty) |
| `public` | 4 | 33 | Migrations, routing |
| `shq` | 2 | 2 | SHQ audit/error master |

---

## Schema: archive (46 tables, 844 rows)

> Archived versions of main tables. See main schemas for column definitions.

---

## Schema: bit (3 tables, 0 rows)

### bit.score_components (0 rows)
| Column | Type | Nullable | Key |
|--------|------|----------|-----|
| id | integer | NOT NULL | PK |
| company_unique_id | text | NOT NULL | |
| component_name | text | NOT NULL | |
| component_value | integer | NULL | |
| weight | numeric | NULL | |
| calculated_at | timestamp without time zone | NULL | |

### bit.score_history (0 rows)
| Column | Type | Nullable | Key |
|--------|------|----------|-----|
| id | integer | NOT NULL | PK |
| company_unique_id | text | NOT NULL | |
| bit_score | integer | NULL | |
| score_date | date | NOT NULL | |
| score_factors | jsonb | NULL | |
| created_at | timestamp without time zone | NULL | |

### bit.score_master (0 rows)
| Column | Type | Nullable | Key |
|--------|------|----------|-----|
| id | integer | NOT NULL | PK |
| company_unique_id | text | NOT NULL | |
| current_bit_score | integer | NULL | |
| score_tier | text | NULL | |
| last_calculated_at | timestamp without time zone | NULL | |
| calculation_version | text | NULL | |
| created_at | timestamp without time zone | NULL | |
| updated_at | timestamp without time zone | NULL | |

---

## Schema: catalog (4 tables, 762 rows)

### catalog.sic_codes (724 rows)
| Column | Type | Nullable | Key |
|--------|------|----------|-----|
| sic_code | character varying(10) | NOT NULL | PK |
| industry_title | character varying(255) | NOT NULL | |
| division | character varying(1) | NULL | |
| major_group | character varying(2) | NULL | |
| created_at | timestamp without time zone | NULL | |

### catalog.states (8 rows)
| Column | Type | Nullable | Key |
|--------|------|----------|-----|
| state_abbrev | character varying(2) | NOT NULL | PK |
| state_name | character varying(50) | NOT NULL | |
| region | character varying(50) | NULL | |
| timezone | character varying(50) | NULL | |
| is_target | boolean | NULL | |
| created_at | timestamp without time zone | NULL | |

### catalog.title_patterns (25 rows)
| Column | Type | Nullable | Key |
|--------|------|----------|-----|
| id | integer | NOT NULL | PK |
| pattern | character varying(255) | NOT NULL | |
| slot_type | character varying(50) | NOT NULL | |
| seniority_level | character varying(50) | NULL | |
| priority | integer | NULL | |
| is_active | boolean | NULL | |
| created_at | timestamp without time zone | NULL | |

### catalog.email_patterns (5 rows)
| Column | Type | Nullable | Key |
|--------|------|----------|-----|
| id | integer | NOT NULL | PK |
| pattern_name | character varying(50) | NOT NULL | |
| pattern_template | character varying(100) | NOT NULL | |
| description | text | NULL | |
| usage_frequency | numeric | NULL | |
| created_at | timestamp without time zone | NULL | |

---

## Schema: cl (10 tables, 484,143 rows)

### cl.company_target_pipeline (18,316 rows)
| Column | Type | Nullable | Key |
|--------|------|----------|-----|
| target_id | uuid | NOT NULL | PK |
| company_unique_id | text | NOT NULL | |
| outreach_id | uuid | NULL | |
| target_status | text | NOT NULL | |
| priority_score | integer | NULL | |
| assignment_date | timestamp with time zone | NULL | |
| last_activity_date | timestamp with time zone | NULL | |
| notes | text | NULL | |
| created_at | timestamp with time zone | NOT NULL | |
| updated_at | timestamp with time zone | NOT NULL | |

### cl.form_5500 (229,877 rows)
| Column | Type | Nullable | Key |
|--------|------|----------|-----|
| id | integer | NOT NULL | PK |
| ack_id | character varying(30) | NOT NULL | |
| form_plan_year_begin_date | date | NULL | |
| form_tax_prd | date | NULL | |
| type_of_plan_entity_cd | character varying(5) | NULL | |
| plan_eff_date | date | NULL | |
| sponsor_dfe_name | character varying(140) | NULL | |
| sponsor_dfe_dba_name | character varying(140) | NULL | |
| sponsor_dfe_ein | character varying(9) | NULL | |
| sponsor_dfe_mail_us_address1 | character varying(35) | NULL | |
| sponsor_dfe_mail_us_city | character varying(22) | NULL | |
| sponsor_dfe_mail_us_state | character varying(2) | NULL | |
| sponsor_dfe_mail_us_zip | character varying(15) | NULL | |
| sponsor_dfe_phone_num | character varying(15) | NULL | |
| admin_name | character varying(140) | NULL | |
| admin_phone_num | character varying(15) | NULL | |
| last_rpt_plan_name | character varying(140) | NULL | |
| admin_signed_date | date | NULL | |
| spons_signed_date | date | NULL | |
| tot_partcp_boy_cnt | integer | NULL | |
| tot_active_partcp_cnt | integer | NULL | |
| rtd_sep_partcp_rcvg_cnt | integer | NULL | |
| eligible_partcp_cnt | integer | NULL | |
| tot_assets_eoy_amt | numeric | NULL | |
| tot_liabilities_eoy_amt | numeric | NULL | |
| net_assets_eoy_amt | numeric | NULL | |
| wlfr_tot_inc_amt | numeric | NULL | |
| raw_payload | jsonb | NULL | |
| created_at | timestamp without time zone | NULL | |

### cl.form_5500_sf (235,950 rows)
| Column | Type | Nullable | Key |
|--------|------|----------|-----|
| id | integer | NOT NULL | PK |
| ack_id | character varying(30) | NOT NULL | |
| form_plan_year_begin_date | date | NULL | |
| form_tax_prd | date | NULL | |
| type_of_plan_entity_cd | character varying(5) | NULL | |
| plan_eff_date | date | NULL | |
| sf_sponsor_name | character varying(140) | NULL | |
| sf_sponsor_dba_name | character varying(140) | NULL | |
| sf_sponsor_ein | character varying(9) | NULL | |
| sf_sponsor_us_address1 | character varying(35) | NULL | |
| sf_sponsor_us_city | character varying(22) | NULL | |
| sf_sponsor_us_state | character varying(2) | NULL | |
| sf_sponsor_us_zip | character varying(15) | NULL | |
| sf_sponsor_phone_num | character varying(15) | NULL | |
| sf_plan_name | character varying(140) | NULL | |
| sf_tot_partcp_boy_cnt | integer | NULL | |
| sf_tot_act_rtd_sep_cnt | integer | NULL | |
| sf_tot_assets_eoy_amt | numeric | NULL | |
| raw_payload | jsonb | NULL | |
| created_at | timestamp without time zone | NULL | |

---

## Schema: company (10 tables, 75,380 rows)

### company.company_lifecycle_version (18,455 rows)
| Column | Type | Nullable | Key |
|--------|------|----------|-----|
| version_id | uuid | NOT NULL | PK |
| company_unique_id | text | NOT NULL | |
| version_number | integer | NOT NULL | |
| change_type | text | NOT NULL | |
| changed_fields | ARRAY | NULL | |
| old_values | jsonb | NULL | |
| new_values | jsonb | NULL | |
| changed_by | text | NULL | |
| changed_at | timestamp with time zone | NOT NULL | |
| source_system | text | NULL | |
| audit_hash | text | NULL | |
| is_current | boolean | NOT NULL | |
| superseded_at | timestamp with time zone | NULL | |
| created_at | timestamp with time zone | NOT NULL | |

### company.company_master (18,345 rows)
| Column | Type | Nullable | Key |
|--------|------|----------|-----|
| company_unique_id | text | NOT NULL | PK |
| company_name | text | NOT NULL | |
| domain | text | NULL | |
| website | text | NULL | |
| industry | text | NULL | |
| employee_count | integer | NULL | |
| phone | text | NULL | |
| address | text | NULL | |
| city | text | NULL | |
| state | text | NULL | |
| zip | text | NULL | |
| linkedin_url | text | NULL | |
| data_quality_score | integer | NULL | |
| last_validated_at | timestamp with time zone | NULL | |
| enrichment_status | text | NULL | |
| source_system | text | NOT NULL | |
| source_record_id | text | NULL | |
| promoted_from_intake_at | timestamp with time zone | NULL | |
| promotion_audit_log_id | integer | NULL | |
| created_at | timestamp with time zone | NULL | |
| updated_at | timestamp with time zone | NULL | |
| revenue | numeric | NULL | |
| facebook_url | text | NULL | |
| twitter_url | text | NULL | |
| sic_codes | text | NULL | |
| founded_year | integer | NULL | |

### company.company_sidecar (100 rows)
| Column | Type | Nullable | Key |
|--------|------|----------|-----|
| company_unique_id | text | NOT NULL | PK |
| clay_insight_summary | text | NULL | |
| clay_segments | ARRAY | NULL | |
| enrichment_payload | jsonb | NULL | |
| last_enriched_at | timestamp without time zone | NULL | |
| enrichment_source | text | NULL | |
| confidence_score | numeric | NULL | |
| created_at | timestamp without time zone | NULL | |
| updated_at | timestamp without time zone | NULL | |

### company.promotion_audit_log (18,369 rows)
| Column | Type | Nullable | Key |
|--------|------|----------|-----|
| log_id | integer | NOT NULL | PK |
| company_unique_id | text | NOT NULL | |
| person_unique_id | text | NULL | |
| source_table | text | NOT NULL | |
| destination_table | text | NOT NULL | |
| record_hash_before | text | NULL | |
| record_hash_after | text | NULL | |
| promoted_at | timestamp with time zone | NOT NULL | |
| promoted_by | text | NULL | |
| validation_status | text | NOT NULL | |
| validation_details | jsonb | NULL | |

### company.quarantine (2 rows)
| Column | Type | Nullable | Key |
|--------|------|----------|-----|
| id | bigint | NOT NULL | PK |
| company_unique_id | text | NOT NULL | |
| company_name | text | NULL | |
| domain | text | NULL | |
| industry | text | NULL | |
| employee_count | integer | NULL | |
| website | text | NULL | |
| phone | text | NULL | |
| address | text | NULL | |
| city | text | NULL | |
| state | text | NULL | |
| zip | text | NULL | |
| validation_status | text | NULL | |
| reason_code | text | NOT NULL | |
| validation_errors | jsonb | NOT NULL | |
| validation_warnings | jsonb | NULL | |
| failed_at | timestamp without time zone | NULL | |
| reviewed | boolean | NULL | |
| batch_id | text | NULL | |
| source_table | text | NULL | |
| created_at | timestamp without time zone | NULL | |
| updated_at | timestamp without time zone | NULL | |
| promoted_to | text | NULL | |
| promoted_at | timestamp without time zone | NULL | |
| enrichment_data | jsonb | NULL | |
| linkedin_url | text | NULL | |
| revenue | numeric | NULL | |
| location | text | NULL | |

---

## Schema: dol (9 tables, 2,432,366 rows)

> **Primary DOL Form 5500 filing data - 2.4M rows**

### dol.form_5500 (230,009 rows)
| Column | Type | Nullable | Key |
|--------|------|----------|-----|
| id | integer | NOT NULL | PK |
| ack_id | character varying(30) | NOT NULL | |
| form_plan_year_begin_date | date | NULL | |
| form_tax_prd | date | NULL | |
| type_of_plan_entity_cd | character varying(5) | NULL | |
| plan_eff_date | date | NULL | |
| sponsor_dfe_name | character varying(140) | NULL | |
| sponsor_dfe_dba_name | character varying(140) | NULL | |
| **sponsor_dfe_ein** | character varying(9) | NULL | |
| sponsor_dfe_mail_us_address1 | character varying(35) | NULL | |
| sponsor_dfe_mail_us_city | character varying(22) | NULL | |
| sponsor_dfe_mail_us_state | character varying(2) | NULL | |
| sponsor_dfe_mail_us_zip | character varying(15) | NULL | |
| sponsor_dfe_phone_num | character varying(15) | NULL | |
| admin_name | character varying(140) | NULL | |
| admin_phone_num | character varying(15) | NULL | |
| last_rpt_plan_name | character varying(140) | NULL | |
| admin_signed_date | date | NULL | |
| spons_signed_date | date | NULL | |
| tot_partcp_boy_cnt | integer | NULL | |
| tot_active_partcp_cnt | integer | NULL | |
| rtd_sep_partcp_rcvg_cnt | integer | NULL | |
| eligible_partcp_cnt | integer | NULL | |
| tot_assets_eoy_amt | numeric | NULL | |
| tot_liabilities_eoy_amt | numeric | NULL | |
| net_assets_eoy_amt | numeric | NULL | |
| wlfr_tot_inc_amt | numeric | NULL | |
| raw_payload | jsonb | NULL | |
| created_at | timestamp without time zone | NULL | |

### dol.form_5500_sf (759,569 rows)
| Column | Type | Nullable | Key |
|--------|------|----------|-----|
| id | integer | NOT NULL | PK |
| ack_id | character varying(30) | NOT NULL | |
| form_plan_year_begin_date | date | NULL | |
| form_tax_prd | date | NULL | |
| type_of_plan_entity_cd | character varying(5) | NULL | |
| plan_eff_date | date | NULL | |
| sf_sponsor_name | character varying(140) | NULL | |
| sf_sponsor_dba_name | character varying(140) | NULL | |
| **sf_sponsor_ein** | character varying(9) | NULL | |
| sf_sponsor_us_address1 | character varying(35) | NULL | |
| sf_sponsor_us_city | character varying(22) | NULL | |
| sf_sponsor_us_state | character varying(2) | NULL | |
| sf_sponsor_us_zip | character varying(15) | NULL | |
| sf_sponsor_phone_num | character varying(15) | NULL | |
| sf_plan_name | character varying(140) | NULL | |
| sf_tot_partcp_boy_cnt | integer | NULL | |
| sf_tot_act_rtd_sep_cnt | integer | NULL | |
| sf_tot_assets_eoy_amt | numeric | NULL | |
| raw_payload | jsonb | NULL | |
| created_at | timestamp without time zone | NULL | |

### dol.form_5500_staging (769,154 rows)
| Column | Type | Nullable | Key |
|--------|------|----------|-----|
| ack_id | text | NULL | |
| form_plan_year_begin_date | text | NULL | |
| form_tax_prd | text | NULL | |
| type_of_plan_entity_cd | text | NULL | |
| plan_eff_date | text | NULL | |
| sponsor_dfe_name | text | NULL | |
| sponsor_dfe_dba_name | text | NULL | |
| sponsor_dfe_ein | text | NULL | |
| ... (staging fields) |

### dol.ein_linkage (0 rows)
| Column | Type | Nullable | Key |
|--------|------|----------|-----|
| linkage_id | uuid | NOT NULL | PK |
| outreach_id | uuid | NOT NULL | |
| ein | character varying(9) | NOT NULL | |
| linkage_source | character varying(50) | NOT NULL | |
| is_primary | boolean | NOT NULL | |
| confidence_score | numeric | NULL | |
| linked_at | timestamp with time zone | NOT NULL | |
| linked_by | character varying(100) | NULL | |
| created_at | timestamp with time zone | NOT NULL | |

### dol.schedule_a (336,817 rows)
| Column | Type | Nullable | Key |
|--------|------|----------|-----|
| id | integer | NOT NULL | PK |
| ack_id | character varying(30) | NOT NULL | |
| sch_a_plan_year_begin_date | date | NULL | |
| sch_a_plan_year_end_date | date | NULL | |
| insurance_company_name | character varying(140) | NULL | |
| **insurance_company_ein** | character varying(9) | NULL | |
| contract_number | character varying(50) | NULL | |
| policy_year_begin_date | date | NULL | |
| policy_year_end_date | date | NULL | |
| renewal_month | integer | NULL | |
| renewal_year | integer | NULL | |
| covered_lives | integer | NULL | |
| wlfr_bnft_health_ind | character varying(1) | NULL | |
| wlfr_bnft_dental_ind | character varying(1) | NULL | |
| wlfr_bnft_vision_ind | character varying(1) | NULL | |
| wlfr_bnft_life_ind | character varying(1) | NULL | |
| wlfr_bnft_stdisd_ind | character varying(1) | NULL | |
| wlfr_bnft_ltdisd_ind | character varying(1) | NULL | |
| insurance_commissions_fees | numeric | NULL | |
| total_premiums_paid | numeric | NULL | |
| raw_payload | jsonb | NULL | |
| created_at | timestamp without time zone | NULL | |

### dol.violations (0 rows)
| Column | Type | Nullable | Key |
|--------|------|----------|-----|
| id | integer | NOT NULL | PK |
| company_unique_id | text | NULL | |
| ein | character varying(9) | NOT NULL | |
| violation_type | character varying(100) | NULL | |
| violation_date | date | NULL | |
| resolution_date | date | NULL | |
| penalty_amount | numeric | NULL | |
| description | text | NULL | |
| source_url | character varying(500) | NULL | |
| raw_payload | jsonb | NULL | |
| detected_at | timestamp without time zone | NULL | |

---

## Schema: intake (5 tables, 62,721 rows)

### intake.company_raw_intake (563 rows)
| Column | Type | Nullable | Key |
|--------|------|----------|-----|
| id | bigint | NOT NULL | PK |
| company | text | NOT NULL | |
| company_name_for_emails | text | NULL | |
| num_employees | integer | NULL | |
| industry | text | NULL | |
| website | text | NULL | |
| company_linkedin_url | text | NULL | |
| facebook_url | text | NULL | |
| twitter_url | text | NULL | |
| company_street | text | NULL | |
| company_city | text | NULL | |
| company_state | text | NULL | |
| company_country | text | NULL | |
| company_postal_code | text | NULL | |
| company_address | text | NULL | |
| company_phone | text | NULL | |
| sic_codes | text | NULL | |
| founded_year | integer | NULL | |
| created_at | timestamp with time zone | NULL | |
| state_abbrev | text | NULL | |
| import_batch_id | text | NULL | |
| validated | boolean | NULL | |
| validation_notes | text | NULL | |
| validated_at | timestamp with time zone | NULL | |
| validated_by | text | NULL | |
| enrichment_attempt | integer | NULL | |
| chronic_bad | boolean | NULL | |
| last_enriched_at | timestamp without time zone | NULL | |
| enriched_by | character varying(255) | NULL | |
| b2_file_path | text | NULL | |
| b2_uploaded_at | timestamp without time zone | NULL | |
| apollo_id | character varying(255) | NULL | |
| last_hash | character varying(64) | NULL | |
| garage_bay | character varying(10) | NULL | |
| validation_reasons | text | NULL | |

### intake.company_raw_wv (62,146 rows)
| Column | Type | Nullable | Key |
|--------|------|----------|-----|
| company_unique_id | text | NOT NULL | PK |
| company_name | text | NULL | |
| domain | text | NULL | |
| website | text | NULL | |
| industry | text | NULL | |
| employee_count | integer | NULL | |
| phone | text | NULL | |
| address | text | NULL | |
| city | text | NULL | |
| state | text | NULL | |
| zip | text | NULL | |
| created_at | timestamp without time zone | NULL | |

### intake.people_raw_intake (0 rows)
Full people staging schema (see output for details)

### intake.people_raw_wv (10 rows)
WV-specific people intake

### intake.quarantine (2 rows)
Failed intake records

---

## Schema: marketing (8 tables, 1,748 rows)

### marketing.company_master (512 rows)
| Column | Type | Nullable | Key |
|--------|------|----------|-----|
| company_unique_id | character varying(50) | NOT NULL | PK |
| company_name | character varying(500) | NOT NULL | |
| domain | character varying(255) | NULL | |
| industry | character varying(255) | NULL | |
| employee_count | integer | NULL | |
| email_pattern | character varying(50) | NULL | |
| pattern_confidence | numeric | NULL | |
| source | character varying(100) | NULL | |
| source_file | character varying(255) | NULL | |
| created_at | timestamp without time zone | NULL | |
| updated_at | timestamp without time zone | NULL | |

### marketing.people_master (145 rows)
| Column | Type | Nullable | Key |
|--------|------|----------|-----|
| unique_id | character varying(50) | NOT NULL | PK |
| company_unique_id | character varying(50) | NULL | |
| full_name | character varying(500) | NOT NULL | |
| first_name | character varying(255) | NULL | |
| last_name | character varying(255) | NULL | |
| email | character varying(255) | NULL | |
| email_verified | boolean | NULL | |
| email_confidence | numeric | NULL | |
| linkedin_url | character varying(500) | NULL | |
| title | character varying(500) | NULL | |
| title_seniority | character varying(50) | NULL | |
| location | character varying(500) | NULL | |
| source | character varying(100) | NULL | |
| source_file | character varying(255) | NULL | |
| created_at | timestamp without time zone | NULL | |
| updated_at | timestamp without time zone | NULL | |
| slot_complete | boolean | NULL | |

### marketing.failed_* tables (various)
- `failed_company_match` (32 rows)
- `failed_email_verification` (310 rows)
- `failed_low_confidence` (5 rows)
- `failed_no_pattern` (6 rows)
- `failed_slot_assignment` (222 rows)

### marketing.review_queue (516 rows)
Manual review queue for fuzzy matches

---

## Schema: outreach (12 tables, 84,323 rows)

> **Core Outreach Hub - Primary operational tables**

### outreach.outreach (63,911 rows) ⭐ SOVEREIGN
| Column | Type | Nullable | Key |
|--------|------|----------|-----|
| **outreach_id** | uuid | NOT NULL | PK |
| **sovereign_id** | uuid | NOT NULL | |
| created_at | timestamp with time zone | NOT NULL | |
| updated_at | timestamp with time zone | NOT NULL | |
| domain | character varying(255) | NULL | |

### outreach.company_target (18,395 rows) ⭐
| Column | Type | Nullable | Key |
|--------|------|----------|-----|
| target_id | uuid | NOT NULL | PK |
| company_unique_id | text | NULL | |
| **outreach_id** | uuid | NULL | FK |
| outreach_status | text | NOT NULL | |
| bit_score_snapshot | integer | NULL | |
| first_targeted_at | timestamp with time zone | NULL | |
| last_targeted_at | timestamp with time zone | NULL | |
| sequence_count | integer | NOT NULL | |
| active_sequence_id | text | NULL | |
| source | text | NULL | |
| created_at | timestamp with time zone | NOT NULL | |
| updated_at | timestamp with time zone | NOT NULL | |
| email_method | character varying(100) | NULL | |
| method_type | character varying(50) | NULL | |
| confidence_score | numeric | NULL | |
| execution_status | character varying(50) | NULL | |
| imo_completed_at | timestamp with time zone | NULL | |
| is_catchall | boolean | NULL | |

### outreach.dol (0 rows) ⭐ DOL Sub-Hub
| Column | Type | Nullable | Key |
|--------|------|----------|-----|
| dol_id | uuid | NOT NULL | PK |
| **outreach_id** | uuid | NOT NULL | FK |
| **ein** | text | NULL | |
| filing_present | boolean | NULL | |
| funding_type | text | NULL | |
| broker_or_advisor | text | NULL | |
| carrier | text | NULL | |
| created_at | timestamp with time zone | NULL | |
| updated_at | timestamp with time zone | NULL | |

### outreach.blog (0 rows)
Blog content sub-hub

### outreach.people (0 rows)
People sub-hub (contacts per outreach_id)

### outreach.*_errors (various)
- `company_target_errors` (271 rows)
- `dol_errors` (0 rows)
- `blog_errors` (0 rows)
- `people_errors` (0 rows)

### outreach.engagement_events (0 rows)
Event tracking for opens, clicks, replies

### outreach.column_registry (48 rows)
Schema documentation registry

### outreach.outreach_legacy_quarantine (1,698 rows)
Quarantined legacy outreach records

---

## Schema: outreach_ctx (3 tables, 3 rows)

> **Outreach Context Control - Campaign orchestration**

### outreach_ctx.context (3 rows) ⭐
| Column | Type | Nullable | Key |
|--------|------|----------|-----|
| **outreach_context_id** | text | NOT NULL | PK |
| created_at | timestamp with time zone | NOT NULL | |
| status | text | NOT NULL | |
| notes | text | NULL | |

### outreach_ctx.spend_log (0 rows)
Credit spend tracking per context

### outreach_ctx.tool_attempts (0 rows)
Tool usage tracking per context

---

## Schema: people (7 tables, 2,756 rows)

### people.people_master (170 rows) ⭐
| Column | Type | Nullable | Key |
|--------|------|----------|-----|
| unique_id | text | NOT NULL | PK |
| company_unique_id | text | NOT NULL | |
| company_slot_unique_id | text | NOT NULL | |
| first_name | text | NOT NULL | |
| last_name | text | NOT NULL | |
| full_name | text | NULL | |
| title | text | NULL | |
| seniority | text | NULL | |
| department | text | NULL | |
| email | text | NULL | |
| work_phone_e164 | text | NULL | |
| personal_phone_e164 | text | NULL | |
| linkedin_url | text | NULL | |
| twitter_url | text | NULL | |
| facebook_url | text | NULL | |
| bio | text | NULL | |
| skills | ARRAY | NULL | |
| education | text | NULL | |
| certifications | ARRAY | NULL | |
| source_system | text | NOT NULL | |
| source_record_id | text | NULL | |
| promoted_from_intake_at | timestamp with time zone | NOT NULL | |
| promotion_audit_log_id | integer | NULL | |
| created_at | timestamp with time zone | NULL | |
| updated_at | timestamp with time zone | NULL | |
| email_verified | boolean | NULL | |
| message_key_scheduled | text | NULL | |
| email_verification_source | text | NULL | |
| email_verified_at | timestamp with time zone | NULL | |
| validation_status | character varying | NULL | |
| last_verified_at | timestamp without time zone | NOT NULL | |
| last_enrichment_attempt | timestamp without time zone | NULL | |

### people.company_slot (1,359 rows)
| Column | Type | Nullable | Key |
|--------|------|----------|-----|
| company_slot_unique_id | text | NOT NULL | PK |
| company_unique_id | text | NOT NULL | |
| person_unique_id | text | NULL | |
| slot_type | text | NOT NULL | |
| is_filled | boolean | NULL | |
| confidence_score | numeric | NULL | |
| created_at | timestamp with time zone | NULL | |
| filled_at | timestamp with time zone | NULL | |
| last_refreshed_at | timestamp with time zone | NULL | |
| filled_by | text | NULL | |
| source_system | text | NULL | |
| enrichment_attempts | integer | NULL | |
| status | character varying(20) | NULL | |
| vacated_at | timestamp without time zone | NULL | |
| phone | character varying(20) | NULL | |
| phone_extension | character varying(10) | NULL | |
| phone_verified_at | timestamp without time zone | NULL | |

### people.people_resolution_queue (1,206 rows)
Contact resolution queue

### people.people_invalid (21 rows)
Invalid people records

### people.people_sidecar (0 rows)
Enrichment data

### people.person_movement_history (0 rows)
Job change tracking

### people.person_scores (0 rows)
BIT scoring for people

---

## Schema: ple (3 tables, 0 rows)

> **PLE Cycle Management - Empty, awaiting implementation**

### ple.ple_cycle (0 rows)
### ple.ple_step (0 rows)
### ple.ple_log (0 rows)

---

## Schema: public (4 tables, 33 rows)

### public.migration_log (21 rows)
| Column | Type | Nullable | Key |
|--------|------|----------|-----|
| id | integer | NOT NULL | PK |
| migration_name | character varying(100) | NULL | |
| step | character varying(200) | NULL | |
| status | character varying(20) | NULL | |
| details | text | NULL | |
| executed_at | timestamp without time zone | NULL | |

### public.garage_runs (3 rows)
Garage/enrichment run tracking

### public.shq_validation_log (9 rows)
SHQ validation run history

### public.agent_routing_log (0 rows)
Agent task routing

---

## Schema: shq (2 tables, 2 rows)

> **System HQ - Central audit and error tracking**

### shq.audit_log (2 rows)
| Column | Type | Nullable | Key |
|--------|------|----------|-----|
| id | integer | NOT NULL | PK |
| event_type | character varying(255) | NOT NULL | |
| event_source | character varying(255) | NOT NULL | |
| details | jsonb | NULL | |
| created_at | timestamp without time zone | NULL | |

### shq.error_master (0 rows) ⭐ Central Error Store
| Column | Type | Nullable | Key |
|--------|------|----------|-----|
| error_id | uuid | NOT NULL | PK |
| process_id | character varying(50) | NOT NULL | |
| agent_id | character varying(50) | NOT NULL | |
| severity | character varying(20) | NOT NULL | |
| error_type | character varying(50) | NOT NULL | |
| message | text | NOT NULL | |
| company_unique_id | character varying(50) | NULL | |
| outreach_context_id | character varying(100) | NULL | |
| air_event_id | character varying(50) | NULL | |
| context | jsonb | NULL | |
| created_at | timestamp with time zone | NOT NULL | |
| resolved_at | timestamp with time zone | NULL | |
| resolution_type | character varying(30) | NULL | |

---

## Key Relationships (ERD)

```
┌─────────────────┐         ┌─────────────────────┐
│ outreach_ctx.   │         │ outreach.outreach   │
│ context         │◄───────►│ (sovereign)         │
│ [3 rows]        │         │ [63,911 rows]       │
└─────────────────┘         └─────────┬───────────┘
                                      │
          ┌───────────────────────────┼───────────────────────────┐
          │                           │                           │
          ▼                           ▼                           ▼
┌─────────────────┐         ┌─────────────────┐         ┌─────────────────┐
│ outreach.       │         │ outreach.dol    │         │ outreach.blog   │
│ company_target  │         │ (EIN binding)   │         │                 │
│ [18,395 rows]   │         │ [0 rows]        │         │ [0 rows]        │
└────────┬────────┘         └────────┬────────┘         └─────────────────┘
         │                           │
         │                           ▼
         │                  ┌─────────────────┐
         │                  │ dol.ein_linkage │
         │                  │ [0 rows]        │
         │                  └────────┬────────┘
         │                           │
         │                           ▼
         │                  ┌─────────────────────────────────────┐
         │                  │ dol.form_5500 + dol.form_5500_sf    │
         │                  │ [989,578 rows - EIN source]         │
         │                  └─────────────────────────────────────┘
         │
         ▼
┌─────────────────┐         ┌─────────────────┐
│ company.        │◄───────►│ people.         │
│ company_master  │         │ people_master   │
│ [18,345 rows]   │         │ [170 rows]      │
└─────────────────┘         └─────────────────┘
```

---

## EIN Column Locations

| Table | Column | Rows | Notes |
|-------|--------|------|-------|
| `dol.form_5500` | `sponsor_dfe_ein` | 230,009 | Large plans |
| `dol.form_5500_sf` | `sf_sponsor_ein` | 759,569 | Small plans |
| `dol.schedule_a` | `insurance_company_ein` | 336,817 | Insurance |
| `dol.ein_linkage` | `ein` | 0 | Outreach binding (empty) |
| `dol.violations` | `ein` | 0 | Violations (empty) |
| `outreach.dol` | `ein` | 0 | DOL sub-hub (empty) |

---

## Doctrine Notes

1. **Outreach ID is sovereign** - All sub-hubs bind via `outreach_id`
2. **EIN binding gap** - `dol.ein_linkage` and `outreach.dol` are empty
3. **989,578 EINs available** in Form 5500 data, awaiting linkage
4. **3 active contexts** in `outreach_ctx.context`
5. **shq.error_master** is the central error store (just created)

---

*Generated by temp_erd_builder.py*
