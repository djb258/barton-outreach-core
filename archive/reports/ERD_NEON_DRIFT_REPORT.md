# ERD vs Neon Schema Drift Report

**Generated**: Mon 02/02/2026 05:27 AM

**Neon Tables (Relevant Schemas)**: 103
**ERD Documented Tables**: 50
**Matching Tables**: 40

## Summary

- **Undocumented Tables** (in Neon, not in ERD): 63
- **Stale/Missing Tables** (in ERD, not in Neon): 10
- **Tables with Column Mismatches**: 40

## 1. Tables in Neon but NOT in ERD (Undocumented)

These tables exist in the database but are not documented in any SCHEMA.md file:


### bit schema

- `bit.authorization_log`
- `bit.movement_events`
- `bit.phase_state`
- `bit.proof_lines`

### cl schema

- `cl.cl_err_existence`
- `cl.cl_errors_archive`
- `cl.company_candidate`
- `cl.company_domains_archive`
- `cl.company_domains_excluded`
- `cl.company_identity_archive`
- `cl.company_identity_bridge`
- `cl.company_identity_excluded`
- `cl.company_names`
- `cl.company_names_archive`
- `cl.company_names_excluded`
- `cl.domain_hierarchy`
- `cl.domain_hierarchy_archive`
- `cl.identity_confidence`
- `cl.identity_confidence_archive`
- `cl.identity_confidence_excluded`

### company schema

- `company.company_events`
- `company.message_key_reference`
- `company.pipeline_errors`
- `company.pipeline_events`
- `company.validation_failures_log`

### dol schema

- `dol.ein_urls`
- `dol.form_5500_icp_filtered`

### outreach schema

- `outreach.bit_input_history`
- `outreach.bit_scores_archive`
- `outreach.blog`
- `outreach.blog_archive`
- `outreach.blog_errors`
- `outreach.blog_ingress_control`
- `outreach.blog_source_history`
- `outreach.column_registry`
- `outreach.company_target_archive`
- `outreach.dol_archive`
- `outreach.dol_url_enrichment`
- `outreach.entity_resolution_queue`
- `outreach.hub_registry`
- `outreach.manual_overrides`
- `outreach.mv_credit_usage`
- `outreach.outreach_archive`
- `outreach.outreach_errors`
- `outreach.outreach_excluded`
- `outreach.outreach_legacy_quarantine`
- `outreach.outreach_orphan_archive`
- `outreach.override_audit_log`
- `outreach.people_archive`
- `outreach.pipeline_audit_log`

### people schema

- `people.company_resolution_log`
- `people.company_slot_archive`
- `people.paid_enrichment_queue`
- `people.people_invalid`
- `people.people_master_archive`
- `people.people_promotion_audit`
- `people.people_resolution_history`
- `people.people_resolution_queue`
- `people.people_staging`
- `people.person_scores`
- `people.slot_orphan_snapshot_r0_002`
- `people.slot_quarantine_r0_002`
- `people.title_slot_mapping`

## 2. Tables in ERD but NOT in Neon (Stale Documentation)

These tables are documented but don't exist in the database:

- `bit.bit_company_score`
- `bit.bit_contact_score`
- `bit.bit_signal`
- `blog.pressure_signals`
- `company.target_vw_all_pressure_signals`
- `marketing.company_master`
- `marketing.people_master`
- `outreach.ctx_context`
- `outreach.ctx_spend_log`
- `talent.flow_movement_history`

## 3. Column Mismatches

Tables where columns differ between ERD and Neon:


### cl.company_domains

*Source: `hubs/outreach-execution/SCHEMA.md`*

**Data Type Mismatches:**

| Column | Neon Type | ERD Type |
|--------|-----------|----------|
| `checked_at` | `timestamp with time zone` | `timestamp` |


### cl.company_identity

*Source: `hubs/company-target/SCHEMA.md`*

**Columns in Neon but not in ERD:**
- `canonical_name`
- `client_id`
- `client_promoted_at`
- `company_fingerprint`
- `domain_status_code`
- `eligibility_status`
- `employee_count_band`
- `entity_role`
- `exclusion_reason`
- `existence_verified`
- `final_outcome`
- `final_reason`
- `identity_pass`
- `identity_status`
- `last_pass_at`
- `lifecycle_run_id`
- `linkedin_company_url`
- `name_match_score`
- `normalized_domain`
- `outreach_attached_at`
- `outreach_id`
- `sales_opened_at`
- `sales_process_id`
- `sovereign_company_id`
- `state_match_result`
- `state_verified`
- `verification_run_id`
- `verified_at`

**Data Type Mismatches:**

| Column | Neon Type | ERD Type |
|--------|-----------|----------|
| `created_at` | `timestamp with time zone` | `timestamp` |


### company.company_master

*Source: `hubs/company-target/SCHEMA.md`*

**Columns in Neon but not in ERD:**
- `address_city`
- `address_country`
- `address_street`
- `address_zip`
- `cage_code`
- `company_phone`
- `created_at`
- `data_quality_score`
- `description`
- `email_pattern_source`
- `email_pattern_verified_at`
- `facebook_url`
- `founded_year`
- `import_batch_id`
- `keywords`
- `linkedin_url`
- `promoted_from_intake_at`
- `promotion_audit_log_id`
- `sic_codes`
- `source_record_id`
- `state_abbrev`
- `twitter_url`
- `updated_at`
- `validated_at`
- `validated_by`


### company.company_sidecar

*Source: `hubs/company-target/SCHEMA.md`*

**Columns in ERD but not in Neon:**
- `clay_tags`
- `company_unique_id`
- `confidence_score`
- `dun_and_bradstreet_number`
- `ein_number`
- `enrichment_payload`


### company.company_slots

*Source: `hubs/company-target/SCHEMA.md`*

**Columns in ERD but not in Neon:**
- `company_slot_unique_id`
- `company_unique_id`
- `created_at`
- `slot_label`
- `slot_type`


### company.company_source_urls

*Source: `hubs/blog-content/SCHEMA.md`*

**Columns in Neon but not in ERD:**
- `content_checksum`
- `created_at`
- `discovered_from`
- `extracted_at`
- `extraction_error`
- `http_status`
- `is_accessible`
- `last_checked_at`
- `last_content_change_at`
- `people_extracted`
- `requires_paid_enrichment`
- `updated_at`


### company.contact_enrichment

*Source: `hubs/company-target/SCHEMA.md`*

**Columns in ERD but not in Neon:**
- `company_slot_unique_id`
- `email`
- `enrichment_result`
- `enrichment_status`
- `id`


### company.email_verification

*Source: `hubs/company-target/SCHEMA.md`*

**Columns in ERD but not in Neon:**
- `email`
- `enrichment_id`
- `id`
- `verification_result`
- `verification_service`
- `verification_status`


### company.url_discovery_failures

*Source: `hubs/blog-content/SCHEMA.md`*

**Columns in ERD but not in Neon:**
- `company_unique_id`
- `failure_id`
- `failure_reason`
- `retry_count`
- `website_url`


### dol.column_metadata

*Source: `hubs/dol-filings/SCHEMA.md`*

**Columns in ERD but not in Neon:**
- `category`
- `column_id`
- `column_name`
- `data_type`
- `description`
- `id`
- `is_pii`
- `is_searchable`
- `table_name`


### dol.form_5500

*Source: `hubs/dol-filings/SCHEMA.md`*

**Columns in Neon but not in ERD:**
- `admin_address_same_spon_ind`
- `admin_care_of_name`
- `admin_foreign_address1`
- `admin_foreign_address2`
- `admin_foreign_city`
- `admin_foreign_cntry`
- `admin_foreign_postal_cd`
- `admin_foreign_prov_state`
- `admin_manual_signed_date`
- `admin_manual_signed_name`
- `admin_name_same_spon_ind`
- `admin_phone_num`
- `admin_phone_num_foreign`
- `admin_signed_date`
- `admin_signed_name`
- `admin_us_address1`
- `admin_us_address2`
- `admin_us_city`
- `admin_us_state`
- `admin_us_zip`
- `adopted_plan_perm_sec_act`
- `amended_ind`
- `benef_rcvg_bnft_cnt`
- `benefit_gen_asset_ind`
- `benefit_insurance_ind`
- `benefit_sec412_ind`
- `benefit_trust_ind`
- `business_code`
- `collective_bargain_ind`
- `compliance_m1_filing_req_ind`
- `contrib_emplrs_cnt`
- `created_at`
- `date_received`
- `dfe_manual_signed_date`
- `dfe_manual_signed_name`
- `dfe_signed_date`
- `dfe_signed_name`
- `dfvc_program_ind`
- `ext_automatic_ind`
- `ext_special_ind`
- `ext_special_text`
- `f5558_application_filed_ind`
- `final_filing_ind`
- `form_plan_year_begin_date`
- `form_tax_prd`
- `funding_gen_asset_ind`
- `funding_insurance_ind`
- `funding_sec412_ind`
- `funding_trust_ind`
- `initial_filing_ind`
- `last_rpt_plan_name`
- `last_rpt_plan_num`
- `last_rpt_spons_ein`
- `last_rpt_spons_name`
- `m1_receipt_confirmation_code`
- `num_sch_dcg_attached_cnt`
- `partcp_account_bal_cnt`
- `partcp_account_bal_cnt_boy`
- `plan_eff_date`
- `preparer_firm_name`
- `preparer_foreign_address1`
- `preparer_foreign_address2`
- `preparer_foreign_city`
- `preparer_foreign_cntry`
- `preparer_foreign_postal_cd`
- `preparer_foreign_prov_state`
- `preparer_name`
- `preparer_phone_num`
- `preparer_phone_num_foreign`
- `preparer_us_address1`
- `preparer_us_address2`
- `preparer_us_city`
- `preparer_us_state`
- `preparer_us_zip`
- `rtd_sep_partcp_fut_cnt`
- `rtd_sep_partcp_rcvg_cnt`
- `sch_c_attached_ind`
- `sch_d_attached_ind`
- `sch_dcg_attached_ind`
- `sch_g_attached_ind`
- `sch_h_attached_ind`
- `sch_i_attached_ind`
- `sch_mb_attached_ind`
- `sch_mep_attached_ind`
- `sch_r_attached_ind`
- `sch_sb_attached_ind`
- `sep_partcp_partl_vstd_cnt`
- `short_plan_yr_ind`
- `spons_dfe_care_of_name`
- `spons_dfe_ein`
- `spons_dfe_loc_foreign_address1`
- `spons_dfe_loc_foreign_address2`
- `spons_dfe_loc_foreign_city`
- `spons_dfe_loc_foreign_cntry`
- `spons_dfe_loc_forgn_postal_cd`
- `spons_dfe_loc_forgn_prov_st`
- `spons_dfe_loc_us_address1`
- `spons_dfe_loc_us_address2`
- `spons_dfe_loc_us_city`
- `spons_dfe_loc_us_state`
- `spons_dfe_loc_us_zip`
- `spons_dfe_mail_foreign_addr1`
- `spons_dfe_mail_foreign_addr2`
- `spons_dfe_mail_foreign_city`
- `spons_dfe_mail_foreign_cntry`
- `spons_dfe_mail_forgn_postal_cd`
- `spons_dfe_mail_forgn_prov_st`
- `spons_dfe_mail_us_address1`
- `spons_dfe_mail_us_address2`
- `spons_dfe_phone_num`
- `spons_dfe_phone_num_foreign`
- `spons_dfe_pn`
- `spons_manual_signed_date`
- `spons_manual_signed_name`
- `spons_signed_date`
- `spons_signed_name`
- `subj_m1_filing_req_ind`
- `subtl_act_rtd_sep_cnt`
- `tot_act_partcp_boy_cnt`
- `tot_act_rtd_sep_benef_cnt`
- `tot_partcp_boy_cnt`
- `type_dfe_plan_entity_cd`
- `type_pension_bnft_code`
- `type_plan_entity_cd`
- `type_welfare_bnft_code`
- `updated_at`
- `valid_admin_signature`
- `valid_dfe_signature`
- `valid_sponsor_signature`


### dol.form_5500_sf

*Source: `hubs/dol-filings/SCHEMA.md`*

**Columns in Neon but not in ERD:**
- `collectively_bargained`
- `created_at`
- `date_received`
- `sf_401k_current_year_adp_ind`
- `sf_401k_current_year_adp_test_ind`
- `sf_401k_design_based_safe_harbor_ind`
- `sf_401k_design_based_safe_ind`
- `sf_401k_na_ind`
- `sf_401k_plan_ind`
- `sf_401k_prior_year_adp_ind`
- `sf_401k_prior_year_adp_test_ind`
- `sf_401k_satisfy_rqmts_ind`
- `sf_5558_application_filed_ind`
- `sf_admin_addrss_same_spon_ind`
- `sf_admin_care_of_name`
- `sf_admin_ein`
- `sf_admin_foreign_address1`
- `sf_admin_foreign_address2`
- `sf_admin_foreign_city`
- `sf_admin_foreign_cntry`
- `sf_admin_foreign_postal_cd`
- `sf_admin_foreign_prov_state`
- `sf_admin_manual_sign_date`
- `sf_admin_manual_signed_name`
- `sf_admin_name`
- `sf_admin_name_same_spon_ind`
- `sf_admin_phone_num`
- `sf_admin_phone_num_foreign`
- `sf_admin_signed_date`
- `sf_admin_signed_name`
- `sf_admin_srvc_providers_amt`
- `sf_admin_us_address1`
- `sf_admin_us_address2`
- `sf_admin_us_city`
- `sf_admin_us_state`
- `sf_admin_us_zip`
- `sf_adopted_plan_perm_sec_act`
- `sf_adp_acp_test_ind`
- `sf_all_plan_ast_distrib_ind`
- `sf_amended_ind`
- `sf_broker_fees_paid_amt`
- `sf_broker_fees_paid_ind`
- `sf_business_code`
- `sf_comply_blackout_notice_ind`
- `sf_corrective_deemed_distr_amt`
- `sf_covered_pbgc_insurance_ind`
- `sf_db_plan_funding_reqd_ind`
- `sf_dc_plan_funding_reqd_ind`
- `sf_dfvc_program_ind`
- `sf_distrib_made_employe_62_ind`
- `sf_eligible_assets_ind`
- `sf_emplr_contrib_income_amt`
- `sf_emplr_contrib_paid_amt`
- `sf_ext_automatic_ind`
- `sf_ext_special_ind`
- `sf_ext_special_text`
- `sf_fail_provide_benef_due_amt`
- `sf_fail_provide_benef_due_ind`
- `sf_fail_transmit_contrib_amt`
- `sf_fail_transmit_contrib_ind`
- `sf_fav_determ_ltr_date`
- `sf_fdcry_trus_cus_phon_numfore`
- `sf_fdcry_trust_ein`
- `sf_fdcry_trust_name`
- `sf_fdcry_truste_cust_name`
- `sf_fdcry_truste_cust_phone_num`
- `sf_final_filing_ind`
- `sf_funding_deadline_ind`
- `sf_funding_deficiency_amt`
- `sf_in_service_distrib_amt`
- `sf_in_service_distrib_ind`
- `sf_initial_filing_ind`
- `sf_iqpa_waiver_ind`
- `sf_last_opin_advi_date`
- `sf_last_opin_advi_serial_num`
- `sf_last_plan_amendment_date`
- `sf_last_rpt_plan_name`
- `sf_last_rpt_plan_num`
- `sf_last_rpt_spons_ein`
- `sf_last_rpt_spons_name`
- `sf_loss_discv_dur_year_amt`
- `sf_loss_discv_dur_year_ind`
- `sf_min_req_distrib_ind`
- `sf_mthd_avg_bnft_test_ind`
- `sf_mthd_na_ind`
- `sf_mthd_ratio_prcnt_test_ind`
- `sf_mthd_used_satisfy_rqmts_ind`
- `sf_net_assets_boy_amt`
- `sf_net_assets_eoy_amt`
- `sf_net_income_amt`
- `sf_opin_letter_date`
- `sf_opin_letter_serial_num`
- `sf_oth_contrib_rcvd_amt`
- `sf_oth_expenses_amt`
- `sf_other_income_amt`
- `sf_partcp_account_bal_cnt`
- `sf_partcp_account_bal_cnt_boy`
- `sf_partcp_loans_eoy_amt`
- `sf_partcp_loans_ind`
- `sf_particip_contrib_income_amt`
- `sf_party_in_int_not_rptd_amt`
- `sf_party_in_int_not_rptd_ind`
- `sf_pbgc_notified_cd`
- `sf_pbgc_notified_explan_text`
- `sf_plan_blackout_period_ind`
- `sf_plan_eff_date`
- `sf_plan_entity_cd`
- `sf_plan_ins_fdlty_bond_amt`
- `sf_plan_ins_fdlty_bond_ind`
- `sf_plan_maintain_us_terri_ind`
- `sf_plan_num`
- `sf_plan_satisfy_tests_ind`
- `sf_plan_timely_amended_ind`
- `sf_plan_year_begin_date`
- `sf_premium_filing_confirm_no`
- `sf_preparer_firm_name`
- `sf_preparer_foreign_address1`
- `sf_preparer_foreign_address2`
- `sf_preparer_foreign_city`
- `sf_preparer_foreign_cntry`
- `sf_preparer_foreign_postal_cd`
- `sf_preparer_foreign_prov_state`
- `sf_preparer_name`
- `sf_preparer_phone_num`
- `sf_preparer_phone_num_foreign`
- `sf_preparer_us_address1`
- `sf_preparer_us_address2`
- `sf_preparer_us_city`
- `sf_preparer_us_state`
- `sf_preparer_us_zip`
- `sf_res_term_plan_adpt_amt`
- `sf_res_term_plan_adpt_ind`
- `sf_ruling_letter_grant_date`
- `sf_sec_412_req_contrib_amt`
- `sf_sep_partcp_partl_vstd_cnt`
- `sf_short_plan_yr_ind`
- `sf_spons_care_of_name`
- `sf_spons_foreign_address1`
- `sf_spons_foreign_address2`
- `sf_spons_foreign_city`
- `sf_spons_foreign_cntry`
- `sf_spons_foreign_postal_cd`
- `sf_spons_foreign_prov_state`
- `sf_spons_loc_foreign_address1`
- `sf_spons_loc_foreign_address2`
- `sf_spons_loc_foreign_city`
- `sf_spons_loc_foreign_cntry`
- `sf_spons_loc_foreign_postal_cd`
- `sf_spons_loc_foreign_prov_stat`
- `sf_spons_loc_us_address1`
- `sf_spons_loc_us_address2`
- `sf_spons_loc_us_city`
- `sf_spons_loc_us_state`
- `sf_spons_loc_us_zip`
- `sf_spons_manual_signed_date`
- `sf_spons_manual_signed_name`
- `sf_spons_phone_num`
- `sf_spons_phone_num_foreign`
- `sf_spons_signed_date`
- `sf_spons_signed_name`
- `sf_spons_us_address1`
- `sf_spons_us_address2`
- `sf_sponsor_dfe_dba_name`
- `sf_tax_code`
- `sf_tax_prd`
- `sf_tot_act_partcp_boy_cnt`
- `sf_tot_act_partcp_eoy_cnt`
- `sf_tot_act_rtd_sep_benef_cnt`
- `sf_tot_assets_boy_amt`
- `sf_tot_distrib_bnft_amt`
- `sf_tot_expenses_amt`
- `sf_tot_income_amt`
- `sf_tot_liabilities_boy_amt`
- `sf_tot_liabilities_eoy_amt`
- `sf_tot_plan_transfers_amt`
- `sf_trus_inc_unrel_tax_inc_amt`
- `sf_trus_inc_unrel_tax_inc_ind`
- `sf_type_pension_bnft_code`
- `sf_type_welfare_bnft_code`
- `sf_unp_min_cont_cur_yrtot_amt`
- `updated_at`
- `valid_admin_signature`
- `valid_sponsor_signature`


### dol.pressure_signals

*Source: `hubs/dol-filings/SCHEMA.md`*

**Columns in ERD but not in Neon:**
- `company_unique_id`
- `correlation_id`
- `detected_at`
- `expires_at`
- `magnitude`
- `pressure_class`
- `pressure_domain`
- `signal_id`
- `signal_type`
- `signal_value`
- `source_record_id`


### dol.renewal_calendar

*Source: `hubs/dol-filings/SCHEMA.md`*

**Columns in ERD but not in Neon:**
- `carrier_name`
- `company_unique_id`
- `days_until_renewal`
- `filing_id`
- `is_upcoming`
- `plan_name`
- `renewal_date`
- `renewal_id`
- `renewal_month`
- `renewal_year`
- `schedule_id`


### dol.schedule_a

*Source: `hubs/dol-filings/SCHEMA.md`*

**Columns in ERD but not in Neon:**
- `ack_id`
- `company_unique_id`
- `filing_id`
- `form_year`
- `ins_broker_comm_tot_amt`
- `ins_broker_fees_tot_amt`
- `ins_carrier_ein`
- `ins_carrier_naic_code`
- `ins_carrier_name`
- `ins_contract_num`
- `ins_policy_from_date`
- `ins_policy_to_date`
- `ins_prsn_covered_eoy_cnt`
- `schedule_id`
- `sponsor_name`
- `sponsor_state`


### outreach.bit_errors

*Source: `hubs/outreach-execution/SCHEMA.md`*

**Columns in ERD but not in Neon:**
- `blocking_reason`
- `correlation_id`
- `error_id`
- `failure_code`
- `outreach_id`
- `pipeline_stage`
- `retry_allowed`
- `severity`


### outreach.bit_scores

*Source: `hubs/outreach-execution/SCHEMA.md`*

**Columns in Neon but not in ERD:**
- `created_at`
- `updated_at`

**Data Type Mismatches:**

| Column | Neon Type | ERD Type |
|--------|-----------|----------|
| `last_signal_at` | `timestamp with time zone` | `timestamp` |
| `last_scored_at` | `timestamp with time zone` | `timestamp` |


### outreach.bit_signals

*Source: `hubs/talent-flow/SCHEMA.md`*

**Columns in ERD but not in Neon:**
- `correlation_id`
- `decay_period_days`
- `decayed_impact`
- `outreach_id`
- `signal_id`
- `signal_impact`
- `signal_timestamp`
- `signal_type`
- `source_spoke`


### outreach.campaigns

*Source: `hubs/outreach-execution/SCHEMA.md`*

**Columns in ERD but not in Neon:**
- `campaign_id`
- `campaign_name`
- `campaign_status`
- `campaign_type`
- `daily_send_limit`
- `end_date`
- `start_date`
- `target_bit_score_min`
- `target_outreach_state`
- `total_clicked`
- `total_opened`
- `total_replied`
- `total_send_limit`
- `total_sent`
- `total_targeted`


### outreach.company_hub_status

*Source: `hubs/company-target/SCHEMA.md`*

**Columns in ERD but not in Neon:**
- `company_unique_id`
- `hub_id`
- `last_processed_at`
- `metric_value`
- `status`
- `status_reason`


### outreach.company_target

*Source: `hubs/people-intelligence/SCHEMA.md`*

**Columns in Neon but not in ERD:**
- `active_sequence_id`
- `bit_score_snapshot`
- `confidence_score`
- `created_at`
- `email_method`
- `execution_status`
- `first_targeted_at`
- `imo_completed_at`
- `is_catchall`
- `last_targeted_at`
- `method_type`
- `sequence_count`
- `source`
- `updated_at`


### outreach.company_target_errors

*Source: `hubs/company-target/SCHEMA.md`*

**Columns in ERD but not in Neon:**
- `blocking_reason`
- `error_id`
- `failure_code`
- `outreach_id`
- `pipeline_stage`
- `raw_input`
- `retry_allowed`
- `severity`
- `stack_trace`


### outreach.dol

*Source: `hubs/dol-filings/SCHEMA.md`*

**Columns in Neon but not in ERD:**
- `created_at`
- `updated_at`


### outreach.dol_audit_log

*Source: `hubs/dol-filings/SCHEMA.md`*

**Columns in ERD but not in Neon:**
- `attempted`
- `company_id`
- `ein`
- `fail_reason`
- `log_id`
- `outcome`
- `run_id`
- `state`


### outreach.dol_errors

*Source: `hubs/dol-filings/SCHEMA.md`*

**Columns in ERD but not in Neon:**
- `blocking_reason`
- `error_id`
- `failure_code`
- `outreach_id`
- `pipeline_stage`
- `raw_input`
- `retry_allowed`
- `severity`


### outreach.engagement_events

*Source: `hubs/outreach-execution/SCHEMA.md`*

**Columns in ERD but not in Neon:**
- `company_unique_id`
- `event_hash`
- `event_id`
- `event_subtype`
- `event_ts`
- `event_type`
- `is_duplicate`
- `is_processed`
- `metadata`
- `outreach_id`
- `person_id`
- `source_campaign_id`
- `source_system`
- `target_id`
- `transition_to_state`
- `triggered_transition`


### outreach.outreach

*Source: `hubs/talent-flow/SCHEMA.md`*

**Columns in Neon but not in ERD:**
- `updated_at`

**Data Type Mismatches:**

| Column | Neon Type | ERD Type |
|--------|-----------|----------|
| `created_at` | `timestamp with time zone` | `timestamp` |


### outreach.people

*Source: `hubs/people-intelligence/SCHEMA.md`*

**Columns in Neon but not in ERD:**
- `created_at`
- `last_state_change_ts`
- `source`
- `updated_at`

**Data Type Mismatches:**

| Column | Neon Type | ERD Type |
|--------|-----------|----------|
| `email_verified_at` | `timestamp with time zone` | `timestamp` |
| `lifecycle_state` | `USER-DEFINED` | `enum` |
| `last_event_ts` | `timestamp with time zone` | `timestamp` |
| `funnel_membership` | `USER-DEFINED` | `enum` |


### outreach.people_errors

*Source: `hubs/people-intelligence/SCHEMA.md`*

**Columns in ERD but not in Neon:**
- `blocking_reason`
- `error_id`
- `failure_code`
- `outreach_id`
- `pipeline_stage`
- `retry_allowed`
- `severity`


### outreach.send_log

*Source: `hubs/outreach-execution/SCHEMA.md`*

**Columns in ERD but not in Neon:**
- `bounced_at`
- `campaign_id`
- `click_count`
- `clicked_at`
- `company_unique_id`
- `delivered_at`
- `email_subject`
- `email_to`
- `error_message`
- `open_count`
- `opened_at`
- `person_id`
- `replied_at`
- `retry_count`
- `scheduled_at`
- `send_id`
- `send_status`
- `sent_at`
- `sequence_id`
- `sequence_step`
- `target_id`


### outreach.sequences

*Source: `hubs/outreach-execution/SCHEMA.md`*

**Columns in ERD but not in Neon:**
- `body_template`
- `campaign_id`
- `delay_days`
- `delay_hours`
- `send_time_preference`
- `sequence_id`
- `sequence_name`
- `sequence_order`
- `sequence_status`
- `subject_template`
- `template_type`


### people.company_slot

*Source: `hubs/people-intelligence/SCHEMA.md`*

**Columns in Neon but not in ERD:**
- `created_at`
- `updated_at`

**Data Type Mismatches:**

| Column | Neon Type | ERD Type |
|--------|-----------|----------|
| `filled_at` | `timestamp with time zone` | `timestamp` |


### people.people_candidate

*Source: `hubs/people-intelligence/SCHEMA.md`*

**Columns in ERD but not in Neon:**
- `candidate_id`
- `confidence_score`
- `expires_at`
- `linkedin_url`
- `outreach_id`
- `person_email`
- `person_name`
- `person_title`
- `rejection_reason`
- `slot_type`
- `source`
- `status`


### people.people_errors

*Source: `hubs/people-intelligence/SCHEMA.md`*

**Columns in ERD but not in Neon:**
- `error_code`
- `error_id`
- `error_message`
- `error_stage`
- `error_type`
- `outreach_id`
- `person_id`
- `raw_payload`
- `retry_strategy`
- `slot_id`
- `source_hints_used`


### people.people_master

*Source: `hubs/talent-flow/SCHEMA.md`*

**Columns in Neon but not in ERD:**
- `bio`
- `certifications`
- `created_at`
- `department`
- `education`
- `email_verification_source`
- `email_verified`
- `email_verified_at`
- `facebook_url`
- `full_name`
- `last_enrichment_attempt`
- `last_verified_at`
- `message_key_scheduled`
- `personal_phone_e164`
- `promoted_from_intake_at`
- `promotion_audit_log_id`
- `seniority`
- `skills`
- `source_record_id`
- `source_system`
- `twitter_url`
- `updated_at`
- `validation_status`
- `work_phone_e164`


### people.people_sidecar

*Source: `hubs/people-intelligence/SCHEMA.md`*

**Columns in ERD but not in Neon:**
- `clay_insight_summary`
- `clay_segments`
- `confidence_score`
- `enrichment_payload`
- `enrichment_source`
- `last_enriched_at`
- `person_unique_id`
- `social_profiles`


### people.person_movement_history

*Source: `hubs/talent-flow/SCHEMA.md`*

**Columns in ERD but not in Neon:**
- `company_from_id`
- `company_to_id`
- `created_at`
- `detected_at`
- `id`
- `linkedin_url`
- `movement_type`
- `person_unique_id`
- `raw_payload`
- `title_from`
- `title_to`


### people.pressure_signals

*Source: `hubs/talent-flow/SCHEMA.md`*

**Columns in ERD but not in Neon:**
- `company_unique_id`
- `magnitude`
- `pressure_domain`
- `signal_id`
- `signal_type`


### people.slot_assignment_history

*Source: `hubs/people-intelligence/SCHEMA.md`*

**Columns in ERD but not in Neon:**
- `company_slot_unique_id`
- `company_unique_id`
- `confidence_score`
- `displaced_by_person_id`
- `displacement_reason`
- `event_metadata`
- `event_type`
- `history_id`
- `person_unique_id`
- `slot_type`
- `source_system`
- `tenure_days`


### people.slot_ingress_control

*Source: `hubs/people-intelligence/SCHEMA.md`*

**Columns in ERD but not in Neon:**
- `description`
- `enabled_at`
- `enabled_by`
- `is_enabled`
- `switch_id`
- `switch_name`

## 4. Recommendations

### Undocumented Tables
- Review each undocumented table
- If table is operational: Add to appropriate SCHEMA.md
- If table is legacy/unused: Consider archiving or dropping
- Special attention to: *_archive, *_errors, *_excluded tables

### Stale Documentation
- Remove or mark as deprecated in ERD
- Update migration scripts if tables were intentionally dropped

### Column Mismatches
- Update SCHEMA.md files to reflect actual Neon schema
- Consider if schema changes need migrations
- Verify foreign key relationships are documented