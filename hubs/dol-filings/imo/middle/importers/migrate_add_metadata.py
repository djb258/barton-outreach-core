#!/usr/bin/env python3
"""
migrate_add_metadata.py — Make DOL tables AI-ready and human-ready
===================================================================
Adds:
  1. COMMENT ON TABLE  — human-readable description of each schedule
  2. COMMENT ON COLUMN — every column in every DOL filing table
  3. Missing form_year + composite indexes for cross-year querying
  4. Populates dol.column_metadata catalog for AI/agent consumption

Run:  doppler run -- python migrate_add_metadata.py
"""

import os, sys, logging, psycopg2

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
log = logging.getLogger(__name__)

# ─── TABLE-LEVEL COMMENTS ────────────────────────────────────────────────────

TABLE_COMMENTS = {
    "form_5500": "DOL Form 5500 Annual Return/Report — filed by large employee benefit plans (100+ participants). Contains plan sponsor info, plan characteristics, participant counts, financial totals, and compliance flags. One row per filing per year. Master table — all schedule tables join via ack_id.",
    "form_5500_sf": "DOL Form 5500-SF Short Form Annual Return/Report — filed by small employee benefit plans (<100 participants, <$250K assets). Same conceptual data as form_5500 but simplified. One row per filing per year.",
    "form_5500_sf_part7": "Form 5500-SF Part VII — Plan transfers. Lists plans to which assets were transferred during the plan year for 5500-SF filers.",
    "schedule_a": "Schedule A (Form 5500) — Insurance Information. Reports insurance contracts held by the plan, including carrier details, premiums, commissions, and coverage types. One row per insurance contract.",
    "schedule_a_part1": "Schedule A Part 1 — Insurance Brokers/Agents. Lists brokers and agents who received commissions or fees in connection with insurance contracts reported on Schedule A.",
    "schedule_c": "Schedule C (Form 5500) — Service Provider Information header. Indicates whether certain service providers are excluded. Parent table for Schedule C parts.",
    "schedule_c_part1_item1": "Schedule C Part 1 Item 1 — Eligible Indirect Compensation service providers. Lists service providers who received $5,000+ in eligible indirect compensation.",
    "schedule_c_part1_item2": "Schedule C Part 1 Item 2 — Other service providers receiving $5,000+ in direct/indirect compensation. Includes name, address, EIN, compensation amounts, and service codes.",
    "schedule_c_part1_item2_codes": "Schedule C Part 1 Item 2 Service Codes — Normalized child table of service type codes for Part 1 Item 2 providers.",
    "schedule_c_part1_item3": "Schedule C Part 1 Item 3 — Indirect compensation received by service providers from sources other than the plan or plan sponsor. Lists payor details and compensation.",
    "schedule_c_part1_item3_codes": "Schedule C Part 1 Item 3 Service Codes — Normalized child table of service type codes for Part 1 Item 3 providers.",
    "schedule_c_part2": "Schedule C Part 2 — Service providers who failed or refused to provide required compensation information. Includes provider details and explanation.",
    "schedule_c_part2_codes": "Schedule C Part 2 Service Codes — Normalized child table of service type codes for Part 2 (failure-to-disclose) providers.",
    "schedule_c_part3": "Schedule C Part 3 — Terminated service provider information. Lists providers whose services were terminated during the plan year, with contact info and termination details.",
    "schedule_d": "Schedule D (Form 5500) — DFE/Participating Plan Information header. Filed by Direct Filing Entities (DFEs) such as master trusts, pooled separate accounts, and 103-12 investment entities.",
    "schedule_d_part1": "Schedule D Part 1 — Individual plan information for DFEs. Lists each participating plan, its EIN/PN, entity type, and end-of-year interest amount.",
    "schedule_d_part2": "Schedule D Part 2 — DFE information for individual plans. Identifies DFEs in which the filing plan participates, with EIN/PN of the DFE.",
    "schedule_dcg": "Schedule DCG — Combined Direct Filing Entity schedule. Merged header-level data for DFEs that file combined returns including Schedules D, C, and G information, with full financial statements and compliance data.",
    "schedule_g": "Schedule G (Form 5500) — Financial Transaction Schedules header. Filed when the plan has loans/fixed income in default, leases in default, or nonexempt transactions.",
    "schedule_g_part1": "Schedule G Part 1 — Loans or fixed income obligations in default or classified as uncollectible. Includes obligor details, loan amounts, and overdue balances.",
    "schedule_g_part2": "Schedule G Part 2 — Leases in default or classified as uncollectible. Includes lessor details, lease terms, costs, rental receipts, and arrears.",
    "schedule_g_part3": "Schedule G Part 3 — Nonexempt transactions (prohibited transactions). Lists party-in-interest transaction details including purchase/sale prices, gains/losses.",
    "schedule_h": "Schedule H (Form 5500) — Financial Information for large plans. Full balance sheet (BOY/EOY), income statement, expense detail, compliance questions, accountant info, and fiduciary trust details. 169 columns of detailed financial data.",
    "schedule_h_part1": "Schedule H Part 1 — Plan transfers for large plans. Lists plans to which assets were transferred during the plan year.",
    "schedule_i": "Schedule I (Form 5500-SF) — Financial Information for small plans. Simplified balance sheet, income/expenses, compliance questions, and fiduciary trust details. 80 columns.",
    "schedule_i_part1": "Schedule I Part 1 — Plan transfers for small plans. Lists plans to which assets were transferred during the plan year.",
}

# ─── COLUMN-LEVEL COMMENTS ───────────────────────────────────────────────────
# Organized by table. Common columns (id, ack_id, form_year, created_at, row_order)
# are handled generically. Table-specific columns are defined per table.

COMMON_COLUMN_COMMENTS = {
    "id": "Auto-increment surrogate primary key",
    "ack_id": "DOL acknowledgment ID — unique filing identifier. Foreign key to dol.form_5500.ack_id or dol.form_5500_sf.ack_id for joining across schedules",
    "form_year": "Filing year (2023, 2024, 2025, etc.) — partition key for cross-year queries",
    "created_at": "Timestamp when this row was loaded into the database",
    "row_order": "Sequence number within a single filing — preserves original CSV row ordering when multiple line items exist per filing",
    "form_id": "DOL internal form identifier",
    "code_order": "Sequence number of the service code within a given row_order — preserves code ordering per provider",
    "service_code": "DOL service type classification code identifying the category of service provided",
}

# Per-table column comments (only columns NOT covered by COMMON_COLUMN_COMMENTS)
TABLE_COLUMN_COMMENTS = {
    "form_5500_sf_part7": {
        "sf_plan_transfer_name": "Name of the plan to which assets were transferred",
        "sf_plan_transfer_ein": "EIN (Employer Identification Number) of the receiving plan",
        "sf_plan_transfer_pn": "Plan number of the receiving plan",
    },
    "schedule_a_part1": {
        "ins_broker_name": "Name of insurance broker or agent",
        "ins_broker_us_address1": "Broker US mailing address line 1",
        "ins_broker_us_address2": "Broker US mailing address line 2",
        "ins_broker_us_city": "Broker US city",
        "ins_broker_us_state": "Broker US state code (2-letter)",
        "ins_broker_us_zip": "Broker US ZIP code",
        "ins_broker_foreign_address1": "Broker foreign address line 1",
        "ins_broker_foreign_address2": "Broker foreign address line 2",
        "ins_broker_foreign_city": "Broker foreign city",
        "ins_broker_foreign_prov_state": "Broker foreign province/state",
        "ins_broker_foreign_cntry": "Broker foreign country",
        "ins_broker_foreign_postal_cd": "Broker foreign postal code",
        "ins_broker_comm_pd_amt": "Total commissions paid to broker (USD)",
        "ins_broker_fees_pd_amt": "Total fees paid to broker (USD)",
        "ins_broker_fees_pd_text": "Description/explanation of fees paid to broker",
        "ins_broker_code": "Broker classification code (type of broker/agent)",
    },
    "schedule_c": {
        "provider_exclude_ind": "Indicator (Yes/No) — whether certain service providers are excluded from Part 1 reporting",
    },
    "schedule_c_part1_item1": {
        "provider_eligible_name": "Name of service provider receiving eligible indirect compensation",
        "provider_eligible_ein": "EIN of the eligible indirect compensation provider",
        "provider_eligible_us_address1": "Provider US address line 1",
        "provider_eligible_us_address2": "Provider US address line 2",
        "provider_eligible_us_city": "Provider US city",
        "provider_eligible_us_state": "Provider US state code (2-letter)",
        "provider_eligible_us_zip": "Provider US ZIP code",
        "prov_eligible_foreign_address1": "Provider foreign address line 1",
        "prov_eligible_foreign_address2": "Provider foreign address line 2",
        "prov_eligible_foreign_city": "Provider foreign city",
        "prov_eligible_foreign_prov_st": "Provider foreign province/state",
        "prov_eligible_foreign_cntry": "Provider foreign country",
        "prov_eligible_foreign_post_cd": "Provider foreign postal code",
    },
    "schedule_c_part1_item2": {
        "provider_other_name": "Name of service provider receiving $5,000+ in compensation",
        "provider_other_ein": "EIN of the service provider",
        "provider_other_us_address1": "Provider US address line 1",
        "provider_other_us_address2": "Provider US address line 2",
        "provider_other_us_city": "Provider US city",
        "provider_other_us_state": "Provider US state code (2-letter)",
        "provider_other_us_zip": "Provider US ZIP code",
        "prov_other_foreign_address1": "Provider foreign address line 1",
        "prov_other_foreign_address2": "Provider foreign address line 2",
        "prov_other_foreign_city": "Provider foreign city",
        "prov_other_foreign_prov_state": "Provider foreign province/state",
        "prov_other_foreign_cntry": "Provider foreign country",
        "prov_other_foreign_postal_cd": "Provider foreign postal code",
        "provider_other_srvc_codes": "Concatenated service type codes for this provider",
        "provider_other_relation": "Relationship to plan (e.g., party-in-interest)",
        "provider_other_direct_comp_amt": "Direct compensation paid to provider (USD)",
        "prov_other_indirect_comp_ind": "Indicator (Yes/No) — did provider receive indirect compensation",
        "prov_other_elig_ind_comp_ind": "Indicator (Yes/No) — eligible indirect compensation received",
        "prov_other_tot_ind_comp_amt": "Total indirect compensation amount (USD)",
        "provider_other_amt_formula_ind": "Indicator (Yes/No) — compensation based on formula rather than fixed amount",
    },
    "schedule_c_part1_item2_codes": {},  # all common
    "schedule_c_part1_item3": {
        "provider_indirect_name": "Name of service provider receiving indirect compensation",
        "provider_indirect_srvc_codes": "Concatenated service type codes",
        "provider_indirect_comp_amt": "Amount of indirect compensation received (USD)",
        "provider_payor_name": "Name of the entity that paid the indirect compensation",
        "provider_payor_ein": "EIN of the payor",
        "provider_payor_us_address1": "Payor US address line 1",
        "provider_payor_us_address2": "Payor US address line 2",
        "provider_payor_us_city": "Payor US city",
        "provider_payor_us_state": "Payor US state code (2-letter)",
        "provider_payor_us_zip": "Payor US ZIP code",
        "prov_payor_foreign_address1": "Payor foreign address line 1",
        "prov_payor_foreign_address2": "Payor foreign address line 2",
        "prov_payor_foreign_city": "Payor foreign city",
        "prov_payor_foreign_prov_state": "Payor foreign province/state",
        "prov_payor_foreign_cntry": "Payor foreign country",
        "prov_payor_foreign_postal_cd": "Payor foreign postal code",
        "provider_comp_explain_text": "Free-text explanation of the indirect compensation arrangement",
    },
    "schedule_c_part1_item3_codes": {},  # all common
    "schedule_c_part2": {
        "provider_fail_name": "Name of provider who failed/refused to disclose compensation",
        "provider_fail_ein": "EIN of the non-disclosing provider",
        "provider_fail_us_address1": "Provider US address line 1",
        "provider_fail_us_address2": "Provider US address line 2",
        "provider_fail_us_city": "Provider US city",
        "provider_fail_us_state": "Provider US state code (2-letter)",
        "provider_fail_us_zip": "Provider US ZIP code",
        "provider_fail_foreign_address1": "Provider foreign address line 1",
        "provider_fail_foreign_address2": "Provider foreign address line 2",
        "provider_fail_foreign_city": "Provider foreign city",
        "provider_fail_foreign_prov_st": "Provider foreign province/state",
        "provider_fail_foreign_cntry": "Provider foreign country",
        "provider_fail_forgn_postal_cd": "Provider foreign postal code",
        "provider_fail_srvc_code": "Service type code(s) for the non-disclosing provider",
        "provider_fail_info_text": "Free-text explanation of the provider's failure to disclose",
    },
    "schedule_c_part2_codes": {},  # all common
    "schedule_c_part3": {
        "provider_term_name": "Name of the terminated service provider",
        "provider_term_ein": "EIN of the terminated provider",
        "provider_term_position": "Position/role held by the terminated provider",
        "provider_term_us_address1": "Provider US address line 1",
        "provider_term_us_address2": "Provider US address line 2",
        "provider_term_us_city": "Provider US city",
        "provider_term_us_state": "Provider US state code (2-letter)",
        "provider_term_us_zip": "Provider US ZIP code",
        "provider_term_foreign_address1": "Provider foreign address line 1",
        "provider_term_foreign_address2": "Provider foreign address line 2",
        "provider_term_foreign_city": "Provider foreign city",
        "provider_term_foreign_prov_st": "Provider foreign province/state",
        "provider_term_foreign_cntry": "Provider foreign country",
        "provider_term_forgn_postal_cd": "Provider foreign postal code",
        "provider_term_phone_num": "US phone number of the terminated provider",
        "provider_term_text": "Free-text explanation of the termination",
        "provider_term_phone_num_foreig": "Foreign phone number of the terminated provider",
    },
    "schedule_d": {
        "sch_d_plan_year_begin_date": "First day of the DFE plan year (YYYY-MM-DD)",
        "sch_d_tax_prd": "Tax period end date of the DFE filing",
        "sch_d_pn": "Plan number of the DFE",
        "sch_d_ein": "EIN of the DFE sponsor",
    },
    "schedule_d_part1": {
        "dfe_p1_entity_name": "Name of the participating plan/entity",
        "dfe_p1_spons_name": "Name of the participating plan's sponsor",
        "dfe_p1_plan_ein": "EIN of the participating plan",
        "dfe_p1_plan_pn": "Plan number of the participating plan",
        "dfe_p1_entity_code": "Entity type code of the participating plan",
        "dfe_p1_plan_int_eoy_amt": "End-of-year interest/value amount for this plan in the DFE (USD)",
    },
    "schedule_d_part2": {
        "dfe_p2_plan_name": "Name of the DFE in which this plan participates",
        "dfe_p2_plan_spons_name": "Name of the DFE sponsor",
        "dfe_p2_plan_ein": "EIN of the DFE",
        "dfe_p2_plan_pn": "Plan number of the DFE",
    },
    "schedule_dcg": {
        "sch_dcg_name": "Name of the Direct Filing Entity",
        "sch_dcg_plan_num": "Plan number of the DFE",
        "sch_dcg_sponsor_name": "Sponsor name of the DFE",
        "sch_dcg_ein": "EIN of the DFE sponsor",
        "dcg_plan_type": "Type of plan (e.g., Master Trust, PSA, 103-12 IE, GIA)",
        "dcg_initial_filing_ind": "Indicator — initial filing for this DFE",
        "dcg_amended_ind": "Indicator — this is an amended filing",
        "dcg_final_ind": "Indicator — this is the final filing for this DFE",
        "dcg_plan_name": "Plan name as reported on the filing",
        "dcg_plan_num": "Plan number as reported on the filing",
        "dcg_plan_eff_date": "Effective date of the plan",
        "dcg_sponsor_name": "Sponsor name as reported",
        "dcg_spons_dba_name": "Sponsor DBA (doing business as) name",
        "dcg_spons_care_of_name": "Sponsor care-of name",
        "dcg_spons_us_address1": "Sponsor US mailing address line 1",
        "dcg_spons_us_address2": "Sponsor US mailing address line 2",
        "dcg_spons_us_city": "Sponsor US city",
        "dcg_spons_us_state": "Sponsor US state code (2-letter)",
        "dcg_spons_us_zip": "Sponsor US ZIP code",
        "dcg_spons_foreign_address1": "Sponsor foreign address line 1",
        "dcg_spons_foreign_address2": "Sponsor foreign address line 2",
        "dcg_spons_foreign_city": "Sponsor foreign city",
        "dcg_spons_foreign_prov_state": "Sponsor foreign province/state",
        "dcg_spons_foreign_cntry": "Sponsor foreign country",
        "dcg_spons_foreign_postal_cd": "Sponsor foreign postal code",
        "dcg_spons_loc_us_address1": "Sponsor location (physical) US address line 1",
        "dcg_spons_loc_us_address2": "Sponsor location US address line 2",
        "dcg_spons_loc_us_city": "Sponsor location US city",
        "dcg_spons_loc_us_state": "Sponsor location US state code",
        "dcg_spons_loc_us_zip": "Sponsor location US ZIP code",
        "dcg_spons_loc_foreign_address1": "Sponsor location foreign address line 1",
        "dcg_spons_loc_foreign_address2": "Sponsor location foreign address line 2",
        "dcg_spons_loc_foreign_city": "Sponsor location foreign city",
        "dcg_spons_loc_foreign_prov_state": "Sponsor location foreign province/state",
        "dcg_spons_loc_foreign_cntry": "Sponsor location foreign country",
        "dcg_spons_loc_foreign_postal_cd": "Sponsor location foreign postal code",
        "dcg_spons_ein": "EIN of the plan sponsor",
        "dcg_spons_phone_num": "Sponsor US phone number",
        "dcg_spons_phone_num_foreign": "Sponsor foreign phone number",
        "dcg_business_code": "NAICS business code of the sponsor",
        "dcg_last_rpt_spons_name": "Sponsor name from the last reported filing",
        "dcg_last_rpt_spons_ein": "Sponsor EIN from the last reported filing",
        "dcg_last_rpt_plan_name": "Plan name from the last reported filing",
        "dcg_last_rpt_plan_num": "Plan number from the last reported filing",
        "dcg_admin_name": "Plan administrator name",
        "dcg_admin_us_address1": "Administrator US address line 1",
        "dcg_admin_us_address2": "Administrator US address line 2",
        "dcg_admin_us_city": "Administrator US city",
        "dcg_admin_us_state": "Administrator US state code",
        "dcg_admin_us_zip": "Administrator US ZIP code",
        "dcg_admin_foreign_address1": "Administrator foreign address line 1",
        "dcg_admin_foreign_address2": "Administrator foreign address line 2",
        "dcg_admin_foreign_city": "Administrator foreign city",
        "dcg_admin_foreign_prov_state": "Administrator foreign province/state",
        "dcg_admin_foreign_cntry": "Administrator foreign country",
        "dcg_admin_foreign_postal_cd": "Administrator foreign postal code",
        "dcg_admin_ein": "Administrator EIN",
        "dcg_admin_phone_num": "Administrator US phone number",
        "dcg_admin_phone_num_foreign": "Administrator foreign phone number",
        "dcg_tot_partcp_boy_cnt": "Total participants at beginning of year",
        "dcg_tot_act_rtd_sep_benef_cnt": "Total active, retired, separated beneficiaries count",
        "dcg_tot_act_partcp_boy_cnt": "Total active participants at beginning of year",
        "dcg_tot_act_partcp_eoy_cnt": "Total active participants at end of year",
        "dcg_partcp_account_bal_boy_cnt": "Participants with account balances at beginning of year",
        "dcg_partcp_account_bal_eoy_cnt": "Participants with account balances at end of year",
        "dcg_sep_partcp_partl_vstd_cnt": "Separated participants with partially vested benefits",
        "dcg_tot_assets_boy_amt": "Total assets at beginning of year (USD)",
        "dcg_partcp_loans_boy_amt": "Participant loans at beginning of year (USD)",
        "dcg_tot_liabilities_boy_amt": "Total liabilities at beginning of year (USD)",
        "dcg_net_assets_boy_amt": "Net assets at beginning of year (USD)",
        "dcg_tot_assets_eoy_amt": "Total assets at end of year (USD)",
        "dcg_partcp_loans_eoy_amt": "Participant loans at end of year (USD)",
        "dcg_tot_liabilities_eoy_amt": "Total liabilities at end of year (USD)",
        "dcg_net_assets_eoy_amt": "Net assets at end of year (USD)",
        "dcg_emplr_contrib_income_amt": "Employer contributions received (USD)",
        "dcg_participant_contrib_income_amt": "Participant contributions received (USD)",
        "dcg_oth_contrib_rcvd_amt": "Other contributions received (USD)",
        "dcg_non_cash_contrib_amt": "Non-cash contributions (USD)",
        "dcg_tot_contrib_amt": "Total contributions (USD)",
        "dcg_other_income_amt": "Other income (USD)",
        "dcg_tot_income_amt": "Total income (USD)",
        "dcg_tot_bnft_amt": "Total benefits paid (USD)",
        "dcg_corrective_distrib_amt": "Corrective distributions (USD)",
        "dcg_deemed_distrib_partcp_lns_amt": "Deemed distributions from participant loans (USD)",
        "dcg_admin_srvc_providers_amt": "Payments to administrative service providers (USD)",
        "dcg_oth_expenses_amt": "Other expenses (USD)",
        "dcg_tot_expenses_amt": "Total expenses (USD)",
        "dcg_net_income_amt": "Net income/loss (USD)",
        "dcg_tot_transfers_to_amt": "Total transfers to other plans (USD)",
        "dcg_tot_transfers_from_amt": "Total transfers from other plans (USD)",
        "dcg_type_pension_bnft_code": "Type of pension benefit code",
        "dcg_fail_transmit_contrib_ind": "Indicator — employer failed to timely transmit participant contributions",
        "dcg_fail_transmit_contrib_amt": "Amount of late-transmitted contributions (USD)",
        "dcg_party_in_int_not_rptd_ind": "Indicator — party-in-interest transactions not reported on Schedule G",
        "dcg_party_in_int_not_rptd_amt": "Amount of unreported party-in-interest transactions (USD)",
        "dcg_fail_provide_benefit_due_ind": "Indicator — plan failed to provide benefits when due",
        "dcg_fail_provide_benefit_due_amt": "Amount of benefits not provided when due (USD)",
        "dcg_fidelity_bond_ind": "Indicator — plan covered by fidelity bond",
        "dcg_fidelity_bond_amt": "Fidelity bond coverage amount (USD)",
        "dcg_loss_discv_dur_year_ind": "Indicator — losses discovered during year due to fraud/dishonesty",
        "dcg_loss_discv_dur_year_amt": "Amount of losses discovered (USD)",
        "dcg_dc_plan_funding_reqd_ind": "Indicator — defined contribution plan funding required",
        "dcg_plan_satisfy_tests_ind": "Indicator — plan satisfied coverage/nondiscrimination tests",
        "dcg_401k_design_based_safe_harbor_ind": "Indicator — 401(k) uses design-based safe harbor",
        "dcg_401k_prior_year_adp_test_ind": "Indicator — 401(k) uses prior year ADP test",
        "dcg_401k_current_year_adp_test_ind": "Indicator — 401(k) uses current year ADP test",
        "dcg_401k_na_ind": "Indicator — 401(k) testing not applicable",
        "dcg_opin_letter_date": "Date of IRS opinion/advisory letter",
        "dcg_opin_letter_serial_num": "IRS opinion/advisory letter serial number",
        "dcg_iqpa_attached_ind": "Indicator — Independent Qualified Public Accountant (IQPA) report attached",
        "dcg_acctnt_opinion_type_cd": "Accountant opinion type code (1=Unqualified, 2=Qualified, 3=Disclaimer, 4=Adverse)",
        "dcg_acct_performed_ltd_audit_103_8_ind": "Indicator — accountant performed limited-scope audit per ERISA Sec 103(a)(3)(C) — DOL Reg 2520.103-8",
        "dcg_acct_performed_ltd_audit_103_12d_ind": "Indicator — accountant performed limited-scope audit per DOL Reg 2520.103-12(d)",
        "dcg_acct_performed_not_ltd_audit_ind": "Indicator — accountant performed full (non-limited-scope) audit",
        "dcg_accountant_firm_name": "Name of the accounting firm",
        "dcg_accountant_firm_ein": "EIN of the accounting firm",
    },
    "schedule_g": {
        "sch_g_plan_year_begin_date": "First day of the plan year (YYYY-MM-DD)",
        "sch_g_tax_prd": "Tax period end date",
        "sch_g_pn": "Plan number",
        "sch_g_ein": "EIN of the plan sponsor",
    },
    "schedule_g_part1": {
        "lns_default_pii_ind": "Indicator — party-in-interest involvement in the defaulted loan",
        "lns_default_obligor_name": "Name of the loan obligor in default",
        "lns_default_obligor_us_addr1": "Obligor US address line 1",
        "lns_default_obligor_us_addr2": "Obligor US address line 2",
        "lns_default_obligor_us_city": "Obligor US city",
        "lns_default_obligor_us_state": "Obligor US state code",
        "lns_default_obligor_us_zip": "Obligor US ZIP code",
        "lns_dft_obligor_foreign_addr1": "Obligor foreign address line 1",
        "lns_dft_obligor_foreign_addr2": "Obligor foreign address line 2",
        "lns_dft_obligor_foreign_city": "Obligor foreign city",
        "lns_dft_obligor_forgn_prov_st": "Obligor foreign province/state",
        "lns_dft_obligor_forgn_country": "Obligor foreign country",
        "lns_dft_obligor_forgn_post_cd": "Obligor foreign postal code",
        "lns_default_description_text": "Description of the defaulted loan terms",
        "lns_default_original_amt": "Original loan amount (USD)",
        "lns_default_prncpl_rcvd_amt": "Principal payments received (USD)",
        "lns_default_int_rcvd_amt": "Interest payments received (USD)",
        "lns_default_unpaid_bal_amt": "Unpaid balance (USD)",
        "lns_default_prcpl_overdue_amt": "Overdue principal amount (USD)",
        "lns_default_int_overdue_amt": "Overdue interest amount (USD)",
    },
    "schedule_g_part2": {
        "leases_default_pii_ind": "Indicator — party-in-interest involvement in the defaulted lease",
        "leases_default_lessor_name": "Name of the lessor in default",
        "leases_default_relation_text": "Relationship of lessor to the plan",
        "leases_default_terms_text": "Description of the lease terms",
        "leases_default_cost_amt": "Original cost of the leased property (USD)",
        "leases_default_curr_value_amt": "Current value of the leased property (USD)",
        "leases_default_rentl_rcpt_amt": "Gross rental receipts (USD)",
        "leases_default_expense_pd_amt": "Expenses paid by plan related to the lease (USD)",
        "leases_default_net_rcpt_amt": "Net rental receipts (USD)",
        "leases_default_arrears_amt": "Amount in arrears (USD)",
    },
    "schedule_g_part3": {
        "non_exempt_party_name": "Name of the party involved in the nonexempt transaction",
        "non_exempt_relation_text": "Relationship of the party to the plan",
        "non_exempt_terms_text": "Description of the transaction terms",
        "non_exempt_pur_price_amt": "Purchase price (USD)",
        "non_exempt_sell_price_amt": "Selling price (USD)",
        "non_exempt_ls_rntl_amt": "Lease/rental amount (USD)",
        "non_exempt_expense_incr_amt": "Expenses incurred (USD)",
        "non_exempt_cost_ast_amt": "Cost of asset (USD)",
        "non_exempt_curr_value_ast_amt": "Current value of asset (USD)",
        "non_exempt_gain_loss_amt": "Net gain or loss on the transaction (USD)",
    },
    "schedule_h": {
        # Header fields
        "sch_h_plan_year_begin_date": "First day of the plan year (YYYY-MM-DD)",
        "sch_h_tax_prd": "Tax period end date",
        "sch_h_pn": "Plan number",
        "sch_h_ein": "EIN of the plan sponsor",
        # Balance sheet — beginning of year (BOY)
        "non_int_bear_cash_boy_amt": "Non-interest-bearing cash — beginning of year (USD)",
        "emplr_contrib_boy_amt": "Employer contributions receivable — BOY (USD)",
        "partcp_contrib_boy_amt": "Participant contributions receivable — BOY (USD)",
        "other_receivables_boy_amt": "Other receivables — BOY (USD)",
        "int_bear_cash_boy_amt": "Interest-bearing cash — BOY (USD)",
        "govt_sec_boy_amt": "US government securities — BOY (USD)",
        "corp_debt_preferred_boy_amt": "Corporate debt instruments (preferred) — BOY (USD)",
        "corp_debt_other_boy_amt": "Corporate debt instruments (other) — BOY (USD)",
        "pref_stock_boy_amt": "Preferred stock — BOY (USD)",
        "common_stock_boy_amt": "Common stock — BOY (USD)",
        "joint_venture_boy_amt": "Partnership/joint venture interests — BOY (USD)",
        "real_estate_boy_amt": "Real estate (other than employer property) — BOY (USD)",
        "other_loans_boy_amt": "Loans (other than to participants) — BOY (USD)",
        "partcp_loans_boy_amt": "Participant loans — BOY (USD)",
        "int_common_tr_boy_amt": "Value of interest in common/collective trusts — BOY (USD)",
        "int_pool_sep_acct_boy_amt": "Value of interest in pooled separate accounts — BOY (USD)",
        "int_master_tr_boy_amt": "Value of interest in master trust — BOY (USD)",
        "int_103_12_invst_boy_amt": "Value of interest in 103-12 investment entities — BOY (USD)",
        "int_reg_invst_co_boy_amt": "Value of interest in registered investment companies — BOY (USD)",
        "ins_co_gen_acct_boy_amt": "Value of funds in insurance company general accounts — BOY (USD)",
        "oth_invst_boy_amt": "Other investments — BOY (USD)",
        "emplr_sec_boy_amt": "Employer securities — BOY (USD)",
        "emplr_prop_boy_amt": "Employer real property — BOY (USD)",
        "bldgs_used_boy_amt": "Buildings and other property used in plan operation — BOY (USD)",
        "tot_assets_boy_amt": "Total assets — beginning of year (USD)",
        "bnfts_payable_boy_amt": "Benefit claims payable — BOY (USD)",
        "oprtng_payable_boy_amt": "Operating payables — BOY (USD)",
        "acquis_indbt_boy_amt": "Acquisition indebtedness — BOY (USD)",
        "other_liab_boy_amt": "Other liabilities — BOY (USD)",
        "tot_liabilities_boy_amt": "Total liabilities — BOY (USD)",
        "net_assets_boy_amt": "Net assets — beginning of year (USD)",
        # Balance sheet — end of year (EOY)
        "non_int_bear_cash_eoy_amt": "Non-interest-bearing cash — end of year (USD)",
        "emplr_contrib_eoy_amt": "Employer contributions receivable — EOY (USD)",
        "partcp_contrib_eoy_amt": "Participant contributions receivable — EOY (USD)",
        "other_receivables_eoy_amt": "Other receivables — EOY (USD)",
        "int_bear_cash_eoy_amt": "Interest-bearing cash — EOY (USD)",
        "govt_sec_eoy_amt": "US government securities — EOY (USD)",
        "corp_debt_preferred_eoy_amt": "Corporate debt instruments (preferred) — EOY (USD)",
        "corp_debt_other_eoy_amt": "Corporate debt instruments (other) — EOY (USD)",
        "pref_stock_eoy_amt": "Preferred stock — EOY (USD)",
        "common_stock_eoy_amt": "Common stock — EOY (USD)",
        "joint_venture_eoy_amt": "Partnership/joint venture interests — EOY (USD)",
        "real_estate_eoy_amt": "Real estate (other than employer property) — EOY (USD)",
        "other_loans_eoy_amt": "Loans (other than to participants) — EOY (USD)",
        "partcp_loans_eoy_amt": "Participant loans — EOY (USD)",
        "int_common_tr_eoy_amt": "Value of interest in common/collective trusts — EOY (USD)",
        "int_pool_sep_acct_eoy_amt": "Value of interest in pooled separate accounts — EOY (USD)",
        "int_master_tr_eoy_amt": "Value of interest in master trust — EOY (USD)",
        "int_103_12_invst_eoy_amt": "Value of interest in 103-12 investment entities — EOY (USD)",
        "int_reg_invst_co_eoy_amt": "Value of interest in registered investment companies — EOY (USD)",
        "ins_co_gen_acct_eoy_amt": "Value of funds in insurance company general accounts — EOY (USD)",
        "oth_invst_eoy_amt": "Other investments — EOY (USD)",
        "emplr_sec_eoy_amt": "Employer securities — EOY (USD)",
        "emplr_prop_eoy_amt": "Employer real property — EOY (USD)",
        "bldgs_used_eoy_amt": "Buildings and other property used in plan operation — EOY (USD)",
        "tot_assets_eoy_amt": "Total assets — end of year (USD)",
        "bnfts_payable_eoy_amt": "Benefit claims payable — EOY (USD)",
        "oprtng_payable_eoy_amt": "Operating payables — EOY (USD)",
        "acquis_indbt_eoy_amt": "Acquisition indebtedness — EOY (USD)",
        "other_liab_eoy_amt": "Other liabilities — EOY (USD)",
        "tot_liabilities_eoy_amt": "Total liabilities — EOY (USD)",
        "net_assets_eoy_amt": "Net assets — end of year (USD)",
        # Income statement
        "emplr_contrib_income_amt": "Employer contributions received (USD)",
        "participant_contrib_amt": "Participant contributions received (USD)",
        "oth_contrib_rcvd_amt": "Other contributions received (USD)",
        "non_cash_contrib_bs_amt": "Non-cash contributions included in total (USD)",
        "tot_contrib_amt": "Total contributions (USD)",
        "int_bear_cash_amt": "Interest on interest-bearing cash (USD)",
        "int_on_govt_sec_amt": "Interest on government securities (USD)",
        "int_on_corp_debt_amt": "Interest on corporate debt instruments (USD)",
        "int_on_oth_loans_amt": "Interest on other loans (USD)",
        "int_on_partcp_loans_amt": "Interest on participant loans (USD)",
        "int_on_oth_invst_amt": "Interest on other investments (USD)",
        "total_interest_amt": "Total interest income (USD)",
        "divnd_pref_stock_amt": "Dividends from preferred stock (USD)",
        "divnd_common_stock_amt": "Dividends from common stock (USD)",
        "registered_invst_amt": "Dividends from registered investment companies (USD)",
        "total_dividends_amt": "Total dividend income (USD)",
        "total_rents_amt": "Total rents (USD)",
        "aggregate_proceeds_amt": "Aggregate proceeds from sale/exchange of assets (USD)",
        "aggregate_costs_amt": "Aggregate costs of sold/exchanged assets (USD)",
        "tot_gain_loss_sale_ast_amt": "Net gain/loss on sale of assets (USD)",
        "unrealzd_apprctn_re_amt": "Unrealized appreciation/depreciation — real estate (USD)",
        "unrealzd_apprctn_oth_amt": "Unrealized appreciation/depreciation — other (USD)",
        "tot_unrealzd_apprctn_amt": "Total unrealized appreciation/depreciation (USD)",
        "gain_loss_com_trust_amt": "Net investment gain/loss from common/collective trusts (USD)",
        "gain_loss_pool_sep_amt": "Net investment gain/loss from pooled separate accounts (USD)",
        "gain_loss_master_tr_amt": "Net investment gain/loss from master trusts (USD)",
        "gain_loss_103_12_invst_amt": "Net investment gain/loss from 103-12 investment entities (USD)",
        "gain_loss_reg_invst_amt": "Net investment gain/loss from registered investment companies (USD)",
        "other_income_amt": "Other income (USD)",
        "tot_income_amt": "Total income (USD)",
        # Expenses
        "distrib_drt_partcp_amt": "Distributions directly to participants/beneficiaries (USD)",
        "ins_carrier_bnfts_amt": "Benefits paid via insurance carriers (USD)",
        "oth_bnft_payment_amt": "Other benefit payments (USD)",
        "tot_distrib_bnft_amt": "Total benefit distributions (USD)",
        "tot_corrective_distrib_amt": "Corrective distributions (USD)",
        "tot_deemed_distr_part_lns_amt": "Deemed distributions from participant loans (USD)",
        "tot_int_expense_amt": "Total interest expense (USD)",
        "professional_fees_amt": "Professional fees (legal, accounting) (USD)",
        "contract_admin_fees_amt": "Contract administrator fees (USD)",
        "invst_mgmt_fees_amt": "Investment management fees (USD)",
        "other_admin_fees_amt": "Other administrative fees (USD)",
        "tot_admin_expenses_amt": "Total administrative expenses (USD)",
        "tot_expenses_amt": "Total expenses (USD)",
        "net_income_amt": "Net income/loss (USD)",
        "tot_transfers_to_amt": "Total transfers to other plans (USD)",
        "tot_transfers_from_amt": "Total transfers from other plans (USD)",
        # Compliance / audit
        "acctnt_opinion_type_cd": "Accountant opinion type code (1=Unqualified, 2=Qualified, 3=Disclaimer, 4=Adverse)",
        "acct_performed_ltd_audit_ind": "Indicator — accountant performed a limited-scope audit",
        "accountant_firm_name": "Name of the accounting firm",
        "accountant_firm_ein": "EIN of the accounting firm",
        "acct_opin_not_on_file_ind": "Indicator — accountant opinion not on file",
        "fail_transmit_contrib_ind": "Indicator — employer failed to timely transmit participant contributions",
        "fail_transmit_contrib_amt": "Amount of late-transmitted contributions (USD)",
        "loans_in_default_ind": "Indicator — plan has loans in default or uncollectible",
        "loans_in_default_amt": "Amount of loans in default (USD)",
        "leases_in_default_ind": "Indicator — plan has leases in default or uncollectible",
        "leases_in_default_amt": "Amount of leases in default (USD)",
        "party_in_int_not_rptd_ind": "Indicator — party-in-interest transactions not reported on Sch G",
        "party_in_int_not_rptd_amt": "Amount of unreported party-in-interest transactions (USD)",
        "plan_ins_fdlty_bond_ind": "Indicator — plan covered by fidelity bond",
        "plan_ins_fdlty_bond_amt": "Fidelity bond coverage amount (USD)",
        "loss_discv_dur_year_ind": "Indicator — losses discovered during year from fraud/dishonesty",
        "loss_discv_dur_year_amt": "Amount of losses discovered (USD)",
        "asset_undeterm_val_ind": "Indicator — plan assets include investments with undetermined value",
        "asset_undeterm_val_amt": "Amount of assets with undetermined value (USD)",
        "non_cash_contrib_ind": "Indicator — plan received non-cash contributions",
        "non_cash_contrib_amt": "Total non-cash contributions (USD)",
        "ast_held_invst_ind": "Indicator — plan held assets for investment",
        "five_prcnt_trans_ind": "Indicator — single transaction exceeded 5% of plan assets",
        "all_plan_ast_distrib_ind": "Indicator — all plan assets distributed to participants",
        "fail_provide_benefit_due_ind": "Indicator — plan failed to provide benefits when due",
        "fail_provide_benefit_due_amt": "Amount of benefits not provided when due (USD)",
        "plan_blackout_period_ind": "Indicator — plan had a blackout period",
        "comply_blackout_notice_ind": "Indicator — plan complied with blackout notice requirements",
        "res_term_plan_adpt_ind": "Indicator — resolution to terminate plan adopted",
        "res_term_plan_adpt_amt": "Amount of plan assets at time of termination resolution (USD)",
        "fdcry_trust_ein": "EIN of the fiduciary trust",
        "fdcry_trust_name": "Name of the fiduciary trust",
        "covered_pbgc_insurance_ind": "Indicator — plan covered by PBGC insurance",
        "trust_incur_unrel_tax_inc_ind": "Indicator — trust incurred unrelated business taxable income",
        "trust_incur_unrel_tax_inc_amt": "Amount of unrelated business taxable income (USD)",
        "in_service_distrib_ind": "Indicator — in-service distributions made",
        "in_service_distrib_amt": "Total in-service distributions (USD)",
        "fdcry_trustee_cust_name": "Name of the fiduciary trustee/custodian",
        "fdcry_trust_cust_phon_num": "Trustee/custodian US phone number",
        "fdcry_trust_cust_phon_nu_fore": "Trustee/custodian foreign phone number",
        "distrib_made_employee_62_ind": "Indicator — distributions made to employees under age 62 who separated",
        "premium_filing_confirm_number": "PBGC premium filing confirmation number",
        "acct_perf_ltd_audit_103_8_ind": "Indicator — accountant performed limited-scope audit per DOL Reg 2520.103-8",
        "acct_perf_ltd_audit_103_12_ind": "Indicator — accountant performed limited-scope audit per DOL Reg 2520.103-12(d)",
        "acct_perf_not_ltd_audit_ind": "Indicator — accountant performed full (non-limited-scope) audit",
        # Admin expense detail (2024+ fields)
        "salaries_allowances_amt": "Salaries and allowances — administrative expenses (USD)",
        "oth_recordkeeping_fees_amt": "Other recordkeeping fees (USD)",
        "iqpa_audit_fees_amt": "IQPA audit fees (USD)",
        "trustee_custodial_fees_amt": "Trustee/custodial fees (USD)",
        "actuarial_fees_amt": "Actuarial fees (USD)",
        "legal_fees_amt": "Legal fees (USD)",
        "valuation_appraisal_fees_amt": "Valuation/appraisal fees (USD)",
        "other_trustee_fees_expenses_amt": "Other trustee fees and expenses (USD)",
    },
    "schedule_h_part1": {
        "plan_transfer_name": "Name of the plan to which assets were transferred",
        "plan_transfer_ein": "EIN of the receiving plan",
        "plan_transfer_pn": "Plan number of the receiving plan",
    },
    "schedule_i": {
        # Header fields
        "sch_i_plan_year_begin_date": "First day of the plan year (YYYY-MM-DD)",
        "sch_i_tax_prd": "Tax period end date",
        "sch_i_plan_num": "Plan number",
        "sch_i_ein": "EIN of the plan sponsor",
        # Balance sheet
        "small_tot_assets_boy_amt": "Total assets — beginning of year (USD)",
        "small_tot_liabilities_boy_amt": "Total liabilities — beginning of year (USD)",
        "small_net_assets_boy_amt": "Net assets — beginning of year (USD)",
        "small_tot_assets_eoy_amt": "Total assets — end of year (USD)",
        "small_tot_liabilities_eoy_amt": "Total liabilities — end of year (USD)",
        "small_net_assets_eoy_amt": "Net assets — end of year (USD)",
        # Income
        "small_emplr_contrib_income_amt": "Employer contributions received (USD)",
        "small_participant_contrib_amt": "Participant contributions received (USD)",
        "small_oth_contrib_rcvd_amt": "Other contributions received (USD)",
        "small_non_cash_contrib_bs_amt": "Non-cash contributions included in total (USD)",
        "small_other_income_amt": "Other income (USD)",
        "small_tot_income_amt": "Total income (USD)",
        # Expenses
        "small_tot_distrib_bnft_amt": "Total benefit distributions (USD)",
        "small_corrective_distrib_amt": "Corrective distributions (USD)",
        "small_deem_dstrb_partcp_ln_amt": "Deemed distributions from participant loans (USD)",
        "small_admin_srvc_providers_amt": "Payments to administrative service providers (USD)",
        "small_oth_expenses_amt": "Other expenses (USD)",
        "small_tot_expenses_amt": "Total expenses (USD)",
        "small_net_income_amt": "Net income/loss (USD)",
        "small_tot_plan_transfers_amt": "Total plan transfers (USD)",
        # Asset detail
        "small_joint_venture_eoy_ind": "Indicator — plan invested in joint ventures at EOY",
        "small_joint_venture_eoy_amt": "Joint venture investments at EOY (USD)",
        "small_emplr_prop_eoy_ind": "Indicator — plan held employer real property at EOY",
        "small_emplr_prop_eoy_amt": "Employer real property at EOY (USD)",
        "small_inv_real_estate_eoy_ind": "Indicator — plan invested in real estate at EOY",
        "small_inv_real_estate_eoy_amt": "Real estate investments at EOY (USD)",
        "small_emplr_sec_eoy_ind": "Indicator — plan held employer securities at EOY",
        "small_emplr_sec_eoy_amt": "Employer securities at EOY (USD)",
        "small_mortg_partcp_eoy_ind": "Indicator — plan held participant mortgages at EOY",
        "small_mortg_partcp_eoy_amt": "Participant mortgages at EOY (USD)",
        "small_oth_lns_partcp_eoy_ind": "Indicator — plan held other participant loans at EOY",
        "small_oth_lns_partcp_eoy_amt": "Other participant loans at EOY (USD)",
        "small_personal_prop_eoy_ind": "Indicator — plan held tangible personal property at EOY",
        "small_personal_prop_eoy_amt": "Tangible personal property at EOY (USD)",
        # Compliance
        "small_fail_transm_contrib_ind": "Indicator — employer failed to timely transmit participant contributions",
        "small_fail_transm_contrib_amt": "Amount of late-transmitted contributions (USD)",
        "small_loans_in_default_ind": "Indicator — plan has loans in default",
        "small_loans_in_default_amt": "Amount of loans in default (USD)",
        "small_leases_in_default_ind": "Indicator — plan has leases in default",
        "small_leases_in_default_amt": "Amount of leases in default (USD)",
        "sm_party_in_int_not_rptd_ind": "Indicator — party-in-interest transactions not reported",
        "sm_party_in_int_not_rptd_amt": "Amount of unreported party-in-interest transactions (USD)",
        "small_plan_ins_fdlty_bond_ind": "Indicator — plan covered by fidelity bond",
        "small_plan_ins_fdlty_bond_amt": "Fidelity bond coverage amount (USD)",
        "small_loss_discv_dur_year_ind": "Indicator — losses discovered from fraud/dishonesty",
        "small_loss_discv_dur_year_amt": "Amount of losses discovered (USD)",
        "small_asset_undeterm_val_ind": "Indicator — assets with undetermined value",
        "small_asset_undeterm_val_amt": "Amount of assets with undetermined value (USD)",
        "small_non_cash_contrib_ind": "Indicator — plan received non-cash contributions",
        "small_non_cash_contrib_amt": "Total non-cash contributions (USD)",
        "small_20_prcnt_sngl_invst_ind": "Indicator — single investment exceeded 20% of plan assets",
        "small_20_prcnt_sngl_invst_amt": "Amount of single investment exceeding 20% (USD)",
        "small_all_plan_ast_distrib_ind": "Indicator — all plan assets distributed",
        "sm_waiv_annual_iqpa_report_ind": "Indicator — annual IQPA report waived",
        "sm_fail_provide_benef_due_ind": "Indicator — failed to provide benefits when due",
        "sm_fail_provide_benef_due_amt": "Amount of benefits not provided when due (USD)",
        "small_plan_blackout_period_ind": "Indicator — plan had a blackout period",
        "sm_comply_blackout_notice_ind": "Indicator — complied with blackout notice requirements",
        "small_res_term_plan_adpt_ind": "Indicator — resolution to terminate plan adopted",
        "small_res_term_plan_adpt_amt": "Amount of plan assets at time of termination resolution (USD)",
        "fdcry_trust_ein": "EIN of the fiduciary trust",
        "fdcry_trust_name": "Name of the fiduciary trust",
        "small_covered_pbgc_ins_ind": "Indicator — plan covered by PBGC insurance",
        "trust_incur_unrel_tax_inc_ind": "Indicator — trust incurred unrelated business taxable income",
        "trust_incur_unrel_tax_inc_amt": "Amount of unrelated business taxable income (USD)",
        "in_service_distrib_ind": "Indicator — in-service distributions made",
        "in_service_distrib_amt": "Total in-service distributions (USD)",
        "fdcry_trustee_cust_name": "Name of the fiduciary trustee/custodian",
        "fdcry_trust_cust_phone_num": "Trustee/custodian US phone number",
        "fdcry_trust_cust_phon_nu_fore": "Trustee/custodian foreign phone number",
        "distrib_made_employee_62_ind": "Indicator — distributions made to employees under age 62 who separated",
        "premium_filing_confirm_number": "PBGC premium filing confirmation number",
    },
    "schedule_i_part1": {
        "small_plan_transfer_name": "Name of the plan to which assets were transferred",
        "small_plan_transfer_ein": "EIN of the receiving plan",
        "small_plan_transfer_pn": "Plan number of the receiving plan",
    },
}

# ─── INDEXES TO ADD ──────────────────────────────────────────────────────────
# Tables that need form_year indexes (all schedule tables that lack them)
TABLES_NEED_YEAR_INDEX = [
    "form_5500_sf_part7",
    "schedule_a_part1",
    "schedule_c", "schedule_c_part1_item1", "schedule_c_part1_item2",
    "schedule_c_part1_item2_codes", "schedule_c_part1_item3",
    "schedule_c_part1_item3_codes", "schedule_c_part2", "schedule_c_part2_codes",
    "schedule_c_part3",
    "schedule_d", "schedule_d_part1", "schedule_d_part2", "schedule_dcg",
    "schedule_g", "schedule_g_part1", "schedule_g_part2", "schedule_g_part3",
    "schedule_h", "schedule_h_part1",
    "schedule_i", "schedule_i_part1",
]

# Tables that benefit from composite (ack_id, form_year) for cross-year joins
TABLES_NEED_COMPOSITE_INDEX = [
    "schedule_a_part1",
    "schedule_c", "schedule_c_part1_item1", "schedule_c_part1_item2",
    "schedule_c_part1_item3", "schedule_c_part2", "schedule_c_part3",
    "schedule_d", "schedule_d_part1", "schedule_d_part2",
    "schedule_g", "schedule_g_part1", "schedule_g_part2", "schedule_g_part3",
    "schedule_h", "schedule_h_part1",
    "schedule_i", "schedule_i_part1",
]


def escape_comment(text):
    """Escape single quotes in SQL comments."""
    return text.replace("'", "''")


def main():
    dsn = os.environ.get("DATABASE_URL")
    if not dsn:
        log.error("DATABASE_URL not set. Use: doppler run -- python migrate_add_metadata.py")
        sys.exit(1)

    conn = psycopg2.connect(dsn)
    conn.autocommit = True
    cur = conn.cursor()

    # Activate import mode
    cur.execute("SET session \"dol.import_mode\" = 'active'")

    # ── 1. TABLE COMMENTS ────────────────────────────────────────────────
    log.info("=== Adding table comments ===")
    for table, comment in TABLE_COMMENTS.items():
        sql = f"COMMENT ON TABLE dol.{table} IS '{escape_comment(comment)}';"
        cur.execute(sql)
        log.info(f"  ✓ dol.{table}")
    log.info(f"  {len(TABLE_COMMENTS)} table comments applied")

    # ── 2. COLUMN COMMENTS ───────────────────────────────────────────────
    log.info("\n=== Adding column comments ===")
    total_comments = 0

    # Get actual columns for each table
    for table in TABLE_COLUMN_COMMENTS:
        cur.execute("""
            SELECT column_name
            FROM information_schema.columns
            WHERE table_schema = 'dol' AND table_name = %s
            ORDER BY ordinal_position
        """, (table,))
        db_cols = [r[0] for r in cur.fetchall()]

        table_specific = TABLE_COLUMN_COMMENTS.get(table, {})
        count = 0

        for col in db_cols:
            # Check table-specific first, then common
            comment = table_specific.get(col) or COMMON_COLUMN_COMMENTS.get(col)
            if comment:
                sql = f"COMMENT ON COLUMN dol.{table}.{col} IS '{escape_comment(comment)}';"
                cur.execute(sql)
                count += 1

        log.info(f"  ✓ dol.{table}: {count}/{len(db_cols)} columns commented")
        total_comments += count

    log.info(f"  TOTAL: {total_comments} column comments applied")

    # ── 3. FORM_YEAR INDEXES ─────────────────────────────────────────────
    log.info("\n=== Adding form_year indexes ===")
    for table in TABLES_NEED_YEAR_INDEX:
        idx_name = f"idx_{table}_year"
        sql = f"CREATE INDEX IF NOT EXISTS {idx_name} ON dol.{table} (form_year);"
        cur.execute(sql)
        log.info(f"  ✓ {idx_name}")

    # ── 4. COMPOSITE (ack_id, form_year) INDEXES ─────────────────────────
    log.info("\n=== Adding composite (ack_id, form_year) indexes ===")
    for table in TABLES_NEED_COMPOSITE_INDEX:
        idx_name = f"idx_{table}_ack_year"
        sql = f"CREATE INDEX IF NOT EXISTS {idx_name} ON dol.{table} (ack_id, form_year);"
        cur.execute(sql)
        log.info(f"  ✓ {idx_name}")

    # ── 5. EIN INDEXES on tables with EIN columns ────────────────────────
    log.info("\n=== Adding EIN indexes where applicable ===")
    ein_index_map = {
        "schedule_a_part1": None,  # no EIN col
        "schedule_c_part1_item1": "provider_eligible_ein",
        "schedule_c_part1_item2": "provider_other_ein",
        "schedule_c_part1_item3": "provider_payor_ein",
        "schedule_c_part2": "provider_fail_ein",
        "schedule_c_part3": "provider_term_ein",
        "schedule_d_part1": "dfe_p1_plan_ein",
        "schedule_d_part2": "dfe_p2_plan_ein",
        "schedule_dcg": "dcg_spons_ein",
        "schedule_g_part1": None,  # no EIN col
        "schedule_h": None,  # already has idx_schedule_h_ein
        "schedule_i": None,  # already has idx_schedule_i_ein
    }
    for table, ein_col in ein_index_map.items():
        if ein_col:
            idx_name = f"idx_{table}_ein"
            sql = f"CREATE INDEX IF NOT EXISTS {idx_name} ON dol.{table} ({ein_col});"
            cur.execute(sql)
            log.info(f"  ✓ {idx_name} on {ein_col}")

    # ── 6. POPULATE dol.column_metadata CATALOG ──────────────────────────
    log.info("\n=== Populating dol.column_metadata catalog ===")

    # Get all DOL filing tables and their columns with comments
    table_list = ",".join("'" + t + "'" for t in TABLE_COMMENTS.keys())
    cur.execute(f"""
        SELECT c.table_name, c.column_name, c.data_type,
               c.character_maximum_length, c.numeric_precision, c.numeric_scale,
               c.is_nullable, c.column_default,
               pgd.description
        FROM information_schema.columns c
        JOIN pg_catalog.pg_class cl ON cl.relname = c.table_name
        JOIN pg_catalog.pg_namespace n ON n.oid = cl.relnamespace AND n.nspname = 'dol'
        LEFT JOIN pg_catalog.pg_description pgd
            ON pgd.objoid = cl.oid
            AND pgd.objsubid = c.ordinal_position
        WHERE c.table_schema = 'dol'
          AND c.table_name IN ({table_list})
        ORDER BY c.table_name, c.ordinal_position
    """)
    all_cols = cur.fetchall()

    # Categorize columns
    def categorize(col_name, data_type):
        if col_name in ("id",):
            return "system"
        if col_name in ("created_at", "form_year", "row_order", "code_order", "form_id"):
            return "metadata"
        if col_name == "ack_id":
            return "join_key"
        if "_ind" in col_name:
            return "indicator"
        if "_amt" in col_name or data_type == "numeric":
            return "financial"
        if "_ein" in col_name or "_pn" in col_name:
            return "identifier"
        if "_address" in col_name or "_city" in col_name or "_state" in col_name or "_zip" in col_name or "_cntry" in col_name or "_postal" in col_name or "_prov" in col_name:
            return "address"
        if "_name" in col_name:
            return "entity_name"
        if "_phone" in col_name:
            return "contact"
        if "_date" in col_name or "_prd" in col_name:
            return "date"
        if "_code" in col_name or "_cd" in col_name or "_type" in col_name:
            return "classification"
        if "_text" in col_name or data_type == "text":
            return "freetext"
        return "other"

    def build_data_format(data_type, char_max, num_prec, num_scale):
        if data_type == "character varying" and char_max:
            return f"VARCHAR({char_max})"
        if data_type == "text":
            return "TEXT"
        if data_type == "numeric":
            return "NUMERIC"
        if data_type == "integer":
            return "INTEGER"
        if data_type == "bigint":
            return "BIGINT"
        if "timestamp" in data_type:
            return "TIMESTAMPTZ"
        return data_type.upper()

    # Clear existing catalog entries for filing tables
    cur.execute(f"""
        DELETE FROM dol.column_metadata
        WHERE table_name IN ({table_list})
    """)
    deleted = cur.rowcount
    if deleted:
        log.info(f"  Cleared {deleted} existing catalog rows")

    # Insert new entries
    insert_sql = """
        INSERT INTO dol.column_metadata
            (table_name, column_name, column_id, description, category,
             data_type, format_pattern, max_length, is_pii, is_searchable)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
    """
    inserted = 0
    for row in all_cols:
        table_name, col_name, data_type, char_max, num_prec, num_scale, nullable, default_val, desc = row
        cat = categorize(col_name, data_type)
        fmt = build_data_format(data_type, char_max, num_prec, num_scale)
        column_id = f"dol.{table_name}.{col_name}"

        # Determine PII and searchability
        is_pii = any(x in col_name for x in ["_name", "_ein", "_phone", "_address"])
        is_searchable = col_name in ("ack_id", "form_year") or "_ein" in col_name or "_name" in col_name or "_state" in col_name or "_city" in col_name or "_code" in col_name

        cur.execute(insert_sql, (
            table_name,
            col_name,
            column_id,
            desc or f"[{col_name}]",
            cat,
            fmt,
            None,  # format_pattern
            char_max,
            is_pii,
            is_searchable,
        ))
        inserted += 1

    log.info(f"  ✓ Inserted {inserted} rows into dol.column_metadata")

    # ── SUMMARY ──────────────────────────────────────────────────────────
    log.info("\n" + "=" * 60)
    log.info("MIGRATION COMPLETE")
    log.info("=" * 60)
    log.info(f"  Table comments:    {len(TABLE_COMMENTS)}")
    log.info(f"  Column comments:   {total_comments}")
    log.info(f"  Year indexes:      {len(TABLES_NEED_YEAR_INDEX)}")
    log.info(f"  Composite indexes: {len(TABLES_NEED_COMPOSITE_INDEX)}")
    log.info(f"  Catalog rows:      {inserted}")

    conn.close()
    log.info("\nDone. Connection closed.")


if __name__ == "__main__":
    main()
