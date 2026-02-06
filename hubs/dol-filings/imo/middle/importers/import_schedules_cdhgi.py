#!/usr/bin/env python3
"""
DOL Form 5500 Schedule C/D/G/H/I Import Script
================================================
Imports 2023 FOIA schedule data into Neon PostgreSQL (dol schema).

Each schedule becomes its own table (or set of tables for sub-parts).
All linked to dol.form_5500 / dol.form_5500_sf via ACK_ID.

Tables created:
  dol.schedule_c              - Schedule C header (broker/TPA exclusion flag)
  dol.schedule_c_part1_item1  - Eligible indirect compensation providers
  dol.schedule_c_part1_item2  - Other service providers (direct/indirect comp)
  dol.schedule_c_part1_item2_codes - Service codes for Part1 Item2
  dol.schedule_c_part1_item3  - Indirect compensation received by providers
  dol.schedule_c_part1_item3_codes - Service codes for Part1 Item3
  dol.schedule_c_part2        - Providers who failed to provide info
  dol.schedule_c_part2_codes  - Service codes for Part2
  dol.schedule_c_part3        - Terminated service providers
  dol.schedule_d              - Schedule D header (DFE info)
  dol.schedule_d_part1        - DFE entity investments
  dol.schedule_d_part2        - Plans participating in DFE
  dol.schedule_dcg            - Combined D/C/G filing (small/simple plans)
  dol.schedule_g              - Schedule G header
  dol.schedule_g_part1        - Loans/fixed income in default
  dol.schedule_g_part2        - Leases in default
  dol.schedule_g_part3        - Non-exempt transactions
  dol.schedule_h              - Schedule H (large plan financials)
  dol.schedule_h_part1        - Plan transfers
  dol.schedule_i              - Schedule I (small plan financials)
  dol.schedule_i_part1        - Small plan transfers

Usage:
  python import_schedules_cdhgi.py --create-tables   # DDL only
  python import_schedules_cdhgi.py --load             # Load CSVs
  python import_schedules_cdhgi.py --create-tables --load  # Both
  python import_schedules_cdhgi.py --verify           # Post-load checks
"""

import os
import sys
import csv
import time
import argparse
import logging
from pathlib import Path
from io import StringIO

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s'
)
logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# CONFIG
# ---------------------------------------------------------------------------
DATA_DIR = Path(__file__).resolve().parents[5] / "data" / "5500" / "2023"

# Map: table_name -> (subfolder, csv_filename)
TABLE_CSV_MAP = {
    # Schedule C
    "schedule_c":                 ("schedule_c", "F_SCH_C_2023_latest.csv"),
    "schedule_c_part1_item1":     ("schedule_c", "F_SCH_C_PART1_ITEM1_2023_latest.csv"),
    "schedule_c_part1_item2":     ("schedule_c", "F_SCH_C_PART1_ITEM2_2023_latest.csv"),
    "schedule_c_part1_item2_codes": ("schedule_c", "F_SCH_C_PART1_ITEM2_CODES_2023_latest.csv"),
    "schedule_c_part1_item3":     ("schedule_c", "F_SCH_C_PART1_ITEM3_2023_latest.csv"),
    "schedule_c_part1_item3_codes": ("schedule_c", "F_SCH_C_PART1_ITEM3_CODES_2023_latest.csv"),
    "schedule_c_part2":           ("schedule_c", "F_SCH_C_PART2_2023_latest.csv"),
    "schedule_c_part2_codes":     ("schedule_c", "F_SCH_C_PART2_CODES_2023_latest.csv"),
    "schedule_c_part3":           ("schedule_c", "F_SCH_C_PART3_2023_latest.csv"),
    # Schedule D
    "schedule_d":                 ("schedule_d", "F_SCH_D_2023_latest.csv"),
    "schedule_d_part1":           ("schedule_d", "F_SCH_D_PART1_2023_latest.csv"),
    "schedule_d_part2":           ("schedule_d", "F_SCH_D_PART2_2023_latest.csv"),
    "schedule_dcg":               ("schedule_d", "F_SCH_DCG_2023_latest.csv"),
    # Schedule G
    "schedule_g":                 ("schedule_g", "F_SCH_G_2023_latest.csv"),
    "schedule_g_part1":           ("schedule_g", "F_SCH_G_PART1_2023_latest.csv"),
    "schedule_g_part2":           ("schedule_g", "F_SCH_G_PART2_2023_latest.csv"),
    "schedule_g_part3":           ("schedule_g", "F_SCH_G_PART3_2023_latest.csv"),
    # Schedule H
    "schedule_h":                 ("schedule_h", "F_SCH_H_2023_latest.csv"),
    "schedule_h_part1":           ("schedule_h", "F_SCH_H_PART1_2023_latest.csv"),
    # Schedule I
    "schedule_i":                 ("schedule_i", "F_SCH_I_2023_latest.csv"),
    "schedule_i_part1":           ("schedule_i", "F_SCH_I_PART1_2023_latest.csv"),
}

# ---------------------------------------------------------------------------
# DDL — Preserves original DOL column names (lowercased), adds PK + audit
# ---------------------------------------------------------------------------
DDL = {
    # ===== SCHEDULE C =====
    "schedule_c": """
        CREATE TABLE IF NOT EXISTS dol.schedule_c (
            id BIGSERIAL PRIMARY KEY,
            ack_id VARCHAR(50) NOT NULL,
            provider_exclude_ind VARCHAR(10),
            form_year VARCHAR(10) DEFAULT '2023',
            created_at TIMESTAMPTZ NOT NULL DEFAULT now()
        );
        CREATE INDEX IF NOT EXISTS idx_schedule_c_ack_id ON dol.schedule_c(ack_id);
    """,
    "schedule_c_part1_item1": """
        CREATE TABLE IF NOT EXISTS dol.schedule_c_part1_item1 (
            id BIGSERIAL PRIMARY KEY,
            ack_id VARCHAR(50) NOT NULL,
            row_order INTEGER,
            provider_eligible_name VARCHAR(500),
            provider_eligible_ein VARCHAR(20),
            provider_eligible_us_address1 VARCHAR(500),
            provider_eligible_us_address2 VARCHAR(500),
            provider_eligible_us_city VARCHAR(255),
            provider_eligible_us_state VARCHAR(10),
            provider_eligible_us_zip VARCHAR(20),
            prov_eligible_foreign_address1 VARCHAR(500),
            prov_eligible_foreign_address2 VARCHAR(500),
            prov_eligible_foreign_city VARCHAR(255),
            prov_eligible_foreign_prov_st VARCHAR(100),
            prov_eligible_foreign_cntry VARCHAR(100),
            prov_eligible_foreign_post_cd VARCHAR(50),
            form_year VARCHAR(10) DEFAULT '2023',
            created_at TIMESTAMPTZ NOT NULL DEFAULT now()
        );
        CREATE INDEX IF NOT EXISTS idx_sch_c_p1i1_ack ON dol.schedule_c_part1_item1(ack_id);
    """,
    "schedule_c_part1_item2": """
        CREATE TABLE IF NOT EXISTS dol.schedule_c_part1_item2 (
            id BIGSERIAL PRIMARY KEY,
            ack_id VARCHAR(50) NOT NULL,
            row_order INTEGER,
            provider_other_name VARCHAR(500),
            provider_other_ein VARCHAR(20),
            provider_other_us_address1 VARCHAR(500),
            provider_other_us_address2 VARCHAR(500),
            provider_other_us_city VARCHAR(255),
            provider_other_us_state VARCHAR(10),
            provider_other_us_zip VARCHAR(20),
            prov_other_foreign_address1 VARCHAR(500),
            prov_other_foreign_address2 VARCHAR(500),
            prov_other_foreign_city VARCHAR(255),
            prov_other_foreign_prov_state VARCHAR(100),
            prov_other_foreign_cntry VARCHAR(100),
            prov_other_foreign_postal_cd VARCHAR(50),
            provider_other_srvc_codes VARCHAR(255),
            provider_other_relation VARCHAR(255),
            provider_other_direct_comp_amt NUMERIC,
            prov_other_indirect_comp_ind VARCHAR(10),
            prov_other_elig_ind_comp_ind VARCHAR(10),
            prov_other_tot_ind_comp_amt NUMERIC,
            provider_other_amt_formula_ind VARCHAR(10),
            form_year VARCHAR(10) DEFAULT '2023',
            created_at TIMESTAMPTZ NOT NULL DEFAULT now()
        );
        CREATE INDEX IF NOT EXISTS idx_sch_c_p1i2_ack ON dol.schedule_c_part1_item2(ack_id);
    """,
    "schedule_c_part1_item2_codes": """
        CREATE TABLE IF NOT EXISTS dol.schedule_c_part1_item2_codes (
            id BIGSERIAL PRIMARY KEY,
            ack_id VARCHAR(50) NOT NULL,
            row_order INTEGER,
            code_order INTEGER,
            service_code VARCHAR(50),
            form_year VARCHAR(10) DEFAULT '2023',
            created_at TIMESTAMPTZ NOT NULL DEFAULT now()
        );
        CREATE INDEX IF NOT EXISTS idx_sch_c_p1i2c_ack ON dol.schedule_c_part1_item2_codes(ack_id);
    """,
    "schedule_c_part1_item3": """
        CREATE TABLE IF NOT EXISTS dol.schedule_c_part1_item3 (
            id BIGSERIAL PRIMARY KEY,
            ack_id VARCHAR(50) NOT NULL,
            row_order INTEGER,
            provider_indirect_name VARCHAR(500),
            provider_indirect_srvc_codes VARCHAR(255),
            provider_indirect_comp_amt NUMERIC,
            provider_payor_name VARCHAR(500),
            provider_payor_ein VARCHAR(20),
            provider_payor_us_address1 VARCHAR(500),
            provider_payor_us_address2 VARCHAR(500),
            provider_payor_us_city VARCHAR(255),
            provider_payor_us_state VARCHAR(10),
            provider_payor_us_zip VARCHAR(20),
            prov_payor_foreign_address1 VARCHAR(500),
            prov_payor_foreign_address2 VARCHAR(500),
            prov_payor_foreign_city VARCHAR(255),
            prov_payor_foreign_prov_state VARCHAR(100),
            prov_payor_foreign_cntry VARCHAR(100),
            prov_payor_foreign_postal_cd VARCHAR(50),
            provider_comp_explain_text TEXT,
            form_year VARCHAR(10) DEFAULT '2023',
            created_at TIMESTAMPTZ NOT NULL DEFAULT now()
        );
        CREATE INDEX IF NOT EXISTS idx_sch_c_p1i3_ack ON dol.schedule_c_part1_item3(ack_id);
    """,
    "schedule_c_part1_item3_codes": """
        CREATE TABLE IF NOT EXISTS dol.schedule_c_part1_item3_codes (
            id BIGSERIAL PRIMARY KEY,
            ack_id VARCHAR(50) NOT NULL,
            row_order INTEGER,
            code_order INTEGER,
            service_code VARCHAR(50),
            form_year VARCHAR(10) DEFAULT '2023',
            created_at TIMESTAMPTZ NOT NULL DEFAULT now()
        );
        CREATE INDEX IF NOT EXISTS idx_sch_c_p1i3c_ack ON dol.schedule_c_part1_item3_codes(ack_id);
    """,
    "schedule_c_part2": """
        CREATE TABLE IF NOT EXISTS dol.schedule_c_part2 (
            id BIGSERIAL PRIMARY KEY,
            ack_id VARCHAR(50) NOT NULL,
            row_order INTEGER,
            provider_fail_name VARCHAR(500),
            provider_fail_ein VARCHAR(20),
            provider_fail_us_address1 VARCHAR(500),
            provider_fail_us_address2 VARCHAR(500),
            provider_fail_us_city VARCHAR(255),
            provider_fail_us_state VARCHAR(10),
            provider_fail_us_zip VARCHAR(20),
            provider_fail_foreign_address1 VARCHAR(500),
            provider_fail_foreign_address2 VARCHAR(500),
            provider_fail_foreign_city VARCHAR(255),
            provider_fail_foreign_prov_st VARCHAR(100),
            provider_fail_foreign_cntry VARCHAR(100),
            provider_fail_forgn_postal_cd VARCHAR(50),
            provider_fail_srvc_code VARCHAR(255),
            provider_fail_info_text TEXT,
            form_year VARCHAR(10) DEFAULT '2023',
            created_at TIMESTAMPTZ NOT NULL DEFAULT now()
        );
        CREATE INDEX IF NOT EXISTS idx_sch_c_p2_ack ON dol.schedule_c_part2(ack_id);
    """,
    "schedule_c_part2_codes": """
        CREATE TABLE IF NOT EXISTS dol.schedule_c_part2_codes (
            id BIGSERIAL PRIMARY KEY,
            ack_id VARCHAR(50) NOT NULL,
            row_order INTEGER,
            code_order INTEGER,
            service_code VARCHAR(50),
            form_year VARCHAR(10) DEFAULT '2023',
            created_at TIMESTAMPTZ NOT NULL DEFAULT now()
        );
        CREATE INDEX IF NOT EXISTS idx_sch_c_p2c_ack ON dol.schedule_c_part2_codes(ack_id);
    """,
    "schedule_c_part3": """
        CREATE TABLE IF NOT EXISTS dol.schedule_c_part3 (
            id BIGSERIAL PRIMARY KEY,
            ack_id VARCHAR(50) NOT NULL,
            row_order INTEGER,
            provider_term_name VARCHAR(500),
            provider_term_ein VARCHAR(20),
            provider_term_position VARCHAR(500),
            provider_term_us_address1 VARCHAR(500),
            provider_term_us_address2 VARCHAR(500),
            provider_term_us_city VARCHAR(255),
            provider_term_us_state VARCHAR(10),
            provider_term_us_zip VARCHAR(20),
            provider_term_foreign_address1 VARCHAR(500),
            provider_term_foreign_address2 VARCHAR(500),
            provider_term_foreign_city VARCHAR(255),
            provider_term_foreign_prov_st VARCHAR(100),
            provider_term_foreign_cntry VARCHAR(100),
            provider_term_forgn_postal_cd VARCHAR(50),
            provider_term_phone_num VARCHAR(30),
            provider_term_text TEXT,
            provider_term_phone_num_foreig VARCHAR(30),
            form_year VARCHAR(10) DEFAULT '2023',
            created_at TIMESTAMPTZ NOT NULL DEFAULT now()
        );
        CREATE INDEX IF NOT EXISTS idx_sch_c_p3_ack ON dol.schedule_c_part3(ack_id);
    """,

    # ===== SCHEDULE D =====
    "schedule_d": """
        CREATE TABLE IF NOT EXISTS dol.schedule_d (
            id BIGSERIAL PRIMARY KEY,
            ack_id VARCHAR(50) NOT NULL,
            sch_d_plan_year_begin_date VARCHAR(30),
            sch_d_tax_prd VARCHAR(30),
            sch_d_pn VARCHAR(10),
            sch_d_ein VARCHAR(20),
            form_year VARCHAR(10) DEFAULT '2023',
            created_at TIMESTAMPTZ NOT NULL DEFAULT now()
        );
        CREATE INDEX IF NOT EXISTS idx_schedule_d_ack_id ON dol.schedule_d(ack_id);
        CREATE INDEX IF NOT EXISTS idx_schedule_d_ein ON dol.schedule_d(sch_d_ein);
    """,
    "schedule_d_part1": """
        CREATE TABLE IF NOT EXISTS dol.schedule_d_part1 (
            id BIGSERIAL PRIMARY KEY,
            ack_id VARCHAR(50) NOT NULL,
            row_order INTEGER,
            dfe_p1_entity_name VARCHAR(500),
            dfe_p1_spons_name VARCHAR(500),
            dfe_p1_plan_ein VARCHAR(20),
            dfe_p1_plan_pn VARCHAR(10),
            dfe_p1_entity_code VARCHAR(10),
            dfe_p1_plan_int_eoy_amt NUMERIC,
            form_year VARCHAR(10) DEFAULT '2023',
            created_at TIMESTAMPTZ NOT NULL DEFAULT now()
        );
        CREATE INDEX IF NOT EXISTS idx_sch_d_p1_ack ON dol.schedule_d_part1(ack_id);
    """,
    "schedule_d_part2": """
        CREATE TABLE IF NOT EXISTS dol.schedule_d_part2 (
            id BIGSERIAL PRIMARY KEY,
            ack_id VARCHAR(50) NOT NULL,
            row_order INTEGER,
            dfe_p2_plan_name VARCHAR(500),
            dfe_p2_plan_spons_name VARCHAR(500),
            dfe_p2_plan_ein VARCHAR(20),
            dfe_p2_plan_pn VARCHAR(10),
            form_year VARCHAR(10) DEFAULT '2023',
            created_at TIMESTAMPTZ NOT NULL DEFAULT now()
        );
        CREATE INDEX IF NOT EXISTS idx_sch_d_p2_ack ON dol.schedule_d_part2(ack_id);
    """,
    "schedule_dcg": """
        CREATE TABLE IF NOT EXISTS dol.schedule_dcg (
            id BIGSERIAL PRIMARY KEY,
            ack_id VARCHAR(50) NOT NULL,
            form_id VARCHAR(50),
            sch_dcg_name VARCHAR(500),
            sch_dcg_plan_num VARCHAR(10),
            sch_dcg_sponsor_name VARCHAR(500),
            sch_dcg_ein VARCHAR(20),
            dcg_plan_type VARCHAR(50),
            dcg_initial_filing_ind VARCHAR(10),
            dcg_amended_ind VARCHAR(10),
            dcg_final_ind VARCHAR(10),
            dcg_plan_name VARCHAR(500),
            dcg_plan_num VARCHAR(10),
            dcg_plan_eff_date VARCHAR(30),
            dcg_sponsor_name VARCHAR(500),
            dcg_spons_dba_name VARCHAR(500),
            dcg_spons_care_of_name VARCHAR(500),
            dcg_spons_us_address1 VARCHAR(500),
            dcg_spons_us_address2 VARCHAR(500),
            dcg_spons_us_city VARCHAR(255),
            dcg_spons_us_state VARCHAR(10),
            dcg_spons_us_zip VARCHAR(20),
            dcg_spons_foreign_address1 VARCHAR(500),
            dcg_spons_foreign_address2 VARCHAR(500),
            dcg_spons_foreign_city VARCHAR(255),
            dcg_spons_foreign_prov_state VARCHAR(100),
            dcg_spons_foreign_cntry VARCHAR(100),
            dcg_spons_foreign_postal_cd VARCHAR(50),
            dcg_spons_loc_us_address1 VARCHAR(500),
            dcg_spons_loc_us_address2 VARCHAR(500),
            dcg_spons_loc_us_city VARCHAR(255),
            dcg_spons_loc_us_state VARCHAR(10),
            dcg_spons_loc_us_zip VARCHAR(20),
            dcg_spons_loc_foreign_address1 VARCHAR(500),
            dcg_spons_loc_foreign_address2 VARCHAR(500),
            dcg_spons_loc_foreign_city VARCHAR(255),
            dcg_spons_loc_foreign_prov_state VARCHAR(100),
            dcg_spons_loc_foreign_cntry VARCHAR(100),
            dcg_spons_loc_foreign_postal_cd VARCHAR(50),
            dcg_spons_ein VARCHAR(20),
            dcg_spons_phone_num VARCHAR(30),
            dcg_spons_phone_num_foreign VARCHAR(30),
            dcg_business_code VARCHAR(20),
            dcg_last_rpt_spons_name VARCHAR(500),
            dcg_last_rpt_spons_ein VARCHAR(20),
            dcg_last_rpt_plan_name VARCHAR(500),
            dcg_last_rpt_plan_num VARCHAR(10),
            dcg_admin_name VARCHAR(500),
            dcg_admin_us_address1 VARCHAR(500),
            dcg_admin_us_address2 VARCHAR(500),
            dcg_admin_us_city VARCHAR(255),
            dcg_admin_us_state VARCHAR(10),
            dcg_admin_us_zip VARCHAR(20),
            dcg_admin_foreign_address1 VARCHAR(500),
            dcg_admin_foreign_address2 VARCHAR(500),
            dcg_admin_foreign_city VARCHAR(255),
            dcg_admin_foreign_prov_state VARCHAR(100),
            dcg_admin_foreign_cntry VARCHAR(100),
            dcg_admin_foreign_postal_cd VARCHAR(50),
            dcg_admin_ein VARCHAR(20),
            dcg_admin_phone_num VARCHAR(30),
            dcg_admin_phone_num_foreign VARCHAR(30),
            dcg_tot_partcp_boy_cnt NUMERIC,
            dcg_tot_act_rtd_sep_benef_cnt NUMERIC,
            dcg_tot_act_partcp_boy_cnt NUMERIC,
            dcg_tot_act_partcp_eoy_cnt NUMERIC,
            dcg_partcp_account_bal_boy_cnt NUMERIC,
            dcg_partcp_account_bal_eoy_cnt NUMERIC,
            dcg_sep_partcp_partl_vstd_cnt NUMERIC,
            dcg_tot_assets_boy_amt NUMERIC,
            dcg_partcp_loans_boy_amt NUMERIC,
            dcg_tot_liabilities_boy_amt NUMERIC,
            dcg_net_assets_boy_amt NUMERIC,
            dcg_tot_assets_eoy_amt NUMERIC,
            dcg_partcp_loans_eoy_amt NUMERIC,
            dcg_tot_liabilities_eoy_amt NUMERIC,
            dcg_net_assets_eoy_amt NUMERIC,
            dcg_emplr_contrib_income_amt NUMERIC,
            dcg_participant_contrib_income_amt NUMERIC,
            dcg_oth_contrib_rcvd_amt NUMERIC,
            dcg_non_cash_contrib_amt NUMERIC,
            dcg_tot_contrib_amt NUMERIC,
            dcg_other_income_amt NUMERIC,
            dcg_tot_income_amt NUMERIC,
            dcg_tot_bnft_amt NUMERIC,
            dcg_corrective_distrib_amt NUMERIC,
            dcg_deemed_distrib_partcp_lns_amt NUMERIC,
            dcg_admin_srvc_providers_amt NUMERIC,
            dcg_oth_expenses_amt NUMERIC,
            dcg_tot_expenses_amt NUMERIC,
            dcg_net_income_amt NUMERIC,
            dcg_tot_transfers_to_amt NUMERIC,
            dcg_tot_transfers_from_amt NUMERIC,
            dcg_type_pension_bnft_code VARCHAR(50),
            dcg_fail_transmit_contrib_ind VARCHAR(10),
            dcg_fail_transmit_contrib_amt NUMERIC,
            dcg_party_in_int_not_rptd_ind VARCHAR(10),
            dcg_party_in_int_not_rptd_amt NUMERIC,
            dcg_fail_provide_benefit_due_ind VARCHAR(10),
            dcg_fail_provide_benefit_due_amt NUMERIC,
            dcg_fidelity_bond_ind VARCHAR(10),
            dcg_fidelity_bond_amt NUMERIC,
            dcg_loss_discv_dur_year_ind VARCHAR(10),
            dcg_loss_discv_dur_year_amt NUMERIC,
            dcg_dc_plan_funding_reqd_ind VARCHAR(10),
            dcg_plan_satisfy_tests_ind VARCHAR(10),
            dcg_401k_design_based_safe_harbor_ind VARCHAR(10),
            dcg_401k_prior_year_adp_test_ind VARCHAR(10),
            dcg_401k_current_year_adp_test_ind VARCHAR(10),
            dcg_401k_na_ind VARCHAR(10),
            dcg_opin_letter_date VARCHAR(30),
            dcg_opin_letter_serial_num VARCHAR(50),
            dcg_iqpa_attached_ind VARCHAR(10),
            dcg_acctnt_opinion_type_cd VARCHAR(10),
            dcg_acct_performed_ltd_audit_103_8_ind VARCHAR(10),
            dcg_acct_performed_ltd_audit_103_12d_ind VARCHAR(10),
            dcg_acct_performed_not_ltd_audit_ind VARCHAR(10),
            dcg_accountant_firm_name VARCHAR(500),
            dcg_accountant_firm_ein VARCHAR(20),
            form_year VARCHAR(10) DEFAULT '2023',
            created_at TIMESTAMPTZ NOT NULL DEFAULT now()
        );
        CREATE INDEX IF NOT EXISTS idx_schedule_dcg_ack ON dol.schedule_dcg(ack_id);
        CREATE INDEX IF NOT EXISTS idx_schedule_dcg_ein ON dol.schedule_dcg(sch_dcg_ein);
    """,

    # ===== SCHEDULE G =====
    "schedule_g": """
        CREATE TABLE IF NOT EXISTS dol.schedule_g (
            id BIGSERIAL PRIMARY KEY,
            ack_id VARCHAR(50) NOT NULL,
            sch_g_plan_year_begin_date VARCHAR(30),
            sch_g_tax_prd VARCHAR(30),
            sch_g_pn VARCHAR(10),
            sch_g_ein VARCHAR(20),
            form_year VARCHAR(10) DEFAULT '2023',
            created_at TIMESTAMPTZ NOT NULL DEFAULT now()
        );
        CREATE INDEX IF NOT EXISTS idx_schedule_g_ack ON dol.schedule_g(ack_id);
        CREATE INDEX IF NOT EXISTS idx_schedule_g_ein ON dol.schedule_g(sch_g_ein);
    """,
    "schedule_g_part1": """
        CREATE TABLE IF NOT EXISTS dol.schedule_g_part1 (
            id BIGSERIAL PRIMARY KEY,
            ack_id VARCHAR(50) NOT NULL,
            row_order INTEGER,
            lns_default_pii_ind VARCHAR(10),
            lns_default_obligor_name VARCHAR(500),
            lns_default_obligor_us_addr1 VARCHAR(500),
            lns_default_obligor_us_addr2 VARCHAR(500),
            lns_default_obligor_us_city VARCHAR(255),
            lns_default_obligor_us_state VARCHAR(10),
            lns_default_obligor_us_zip VARCHAR(20),
            lns_dft_obligor_foreign_addr1 VARCHAR(500),
            lns_dft_obligor_foreign_addr2 VARCHAR(500),
            lns_dft_obligor_foreign_city VARCHAR(255),
            lns_dft_obligor_forgn_prov_st VARCHAR(100),
            lns_dft_obligor_forgn_country VARCHAR(100),
            lns_dft_obligor_forgn_post_cd VARCHAR(50),
            lns_default_description_text TEXT,
            lns_default_original_amt NUMERIC,
            lns_default_prncpl_rcvd_amt NUMERIC,
            lns_default_int_rcvd_amt NUMERIC,
            lns_default_unpaid_bal_amt NUMERIC,
            lns_default_prcpl_overdue_amt NUMERIC,
            lns_default_int_overdue_amt NUMERIC,
            form_year VARCHAR(10) DEFAULT '2023',
            created_at TIMESTAMPTZ NOT NULL DEFAULT now()
        );
        CREATE INDEX IF NOT EXISTS idx_sch_g_p1_ack ON dol.schedule_g_part1(ack_id);
    """,
    "schedule_g_part2": """
        CREATE TABLE IF NOT EXISTS dol.schedule_g_part2 (
            id BIGSERIAL PRIMARY KEY,
            ack_id VARCHAR(50) NOT NULL,
            row_order INTEGER,
            leases_default_pii_ind VARCHAR(10),
            leases_default_lessor_name VARCHAR(500),
            leases_default_relation_text TEXT,
            leases_default_terms_text TEXT,
            leases_default_cost_amt NUMERIC,
            leases_default_curr_value_amt NUMERIC,
            leases_default_rentl_rcpt_amt NUMERIC,
            leases_default_expense_pd_amt NUMERIC,
            leases_default_net_rcpt_amt NUMERIC,
            leases_default_arrears_amt NUMERIC,
            form_year VARCHAR(10) DEFAULT '2023',
            created_at TIMESTAMPTZ NOT NULL DEFAULT now()
        );
        CREATE INDEX IF NOT EXISTS idx_sch_g_p2_ack ON dol.schedule_g_part2(ack_id);
    """,
    "schedule_g_part3": """
        CREATE TABLE IF NOT EXISTS dol.schedule_g_part3 (
            id BIGSERIAL PRIMARY KEY,
            ack_id VARCHAR(50) NOT NULL,
            row_order INTEGER,
            non_exempt_party_name VARCHAR(500),
            non_exempt_relation_text TEXT,
            non_exempt_terms_text TEXT,
            non_exempt_pur_price_amt NUMERIC,
            non_exempt_sell_price_amt NUMERIC,
            non_exempt_ls_rntl_amt NUMERIC,
            non_exempt_expense_incr_amt NUMERIC,
            non_exempt_cost_ast_amt NUMERIC,
            non_exempt_curr_value_ast_amt NUMERIC,
            non_exempt_gain_loss_amt NUMERIC,
            form_year VARCHAR(10) DEFAULT '2023',
            created_at TIMESTAMPTZ NOT NULL DEFAULT now()
        );
        CREATE INDEX IF NOT EXISTS idx_sch_g_p3_ack ON dol.schedule_g_part3(ack_id);
    """,

    # ===== SCHEDULE H =====
    "schedule_h": """
        CREATE TABLE IF NOT EXISTS dol.schedule_h (
            id BIGSERIAL PRIMARY KEY,
            ack_id VARCHAR(50) NOT NULL,
            sch_h_plan_year_begin_date VARCHAR(30),
            sch_h_tax_prd VARCHAR(30),
            sch_h_pn VARCHAR(10),
            sch_h_ein VARCHAR(20),
            non_int_bear_cash_boy_amt NUMERIC, emplr_contrib_boy_amt NUMERIC,
            partcp_contrib_boy_amt NUMERIC, other_receivables_boy_amt NUMERIC,
            int_bear_cash_boy_amt NUMERIC, govt_sec_boy_amt NUMERIC,
            corp_debt_preferred_boy_amt NUMERIC, corp_debt_other_boy_amt NUMERIC,
            pref_stock_boy_amt NUMERIC, common_stock_boy_amt NUMERIC,
            joint_venture_boy_amt NUMERIC, real_estate_boy_amt NUMERIC,
            other_loans_boy_amt NUMERIC, partcp_loans_boy_amt NUMERIC,
            int_common_tr_boy_amt NUMERIC, int_pool_sep_acct_boy_amt NUMERIC,
            int_master_tr_boy_amt NUMERIC, int_103_12_invst_boy_amt NUMERIC,
            int_reg_invst_co_boy_amt NUMERIC, ins_co_gen_acct_boy_amt NUMERIC,
            oth_invst_boy_amt NUMERIC, emplr_sec_boy_amt NUMERIC,
            emplr_prop_boy_amt NUMERIC, bldgs_used_boy_amt NUMERIC,
            tot_assets_boy_amt NUMERIC, bnfts_payable_boy_amt NUMERIC,
            oprtng_payable_boy_amt NUMERIC, acquis_indbt_boy_amt NUMERIC,
            other_liab_boy_amt NUMERIC, tot_liabilities_boy_amt NUMERIC,
            net_assets_boy_amt NUMERIC,
            non_int_bear_cash_eoy_amt NUMERIC, emplr_contrib_eoy_amt NUMERIC,
            partcp_contrib_eoy_amt NUMERIC, other_receivables_eoy_amt NUMERIC,
            int_bear_cash_eoy_amt NUMERIC, govt_sec_eoy_amt NUMERIC,
            corp_debt_preferred_eoy_amt NUMERIC, corp_debt_other_eoy_amt NUMERIC,
            pref_stock_eoy_amt NUMERIC, common_stock_eoy_amt NUMERIC,
            joint_venture_eoy_amt NUMERIC, real_estate_eoy_amt NUMERIC,
            other_loans_eoy_amt NUMERIC, partcp_loans_eoy_amt NUMERIC,
            int_common_tr_eoy_amt NUMERIC, int_pool_sep_acct_eoy_amt NUMERIC,
            int_master_tr_eoy_amt NUMERIC, int_103_12_invst_eoy_amt NUMERIC,
            int_reg_invst_co_eoy_amt NUMERIC, ins_co_gen_acct_eoy_amt NUMERIC,
            oth_invst_eoy_amt NUMERIC, emplr_sec_eoy_amt NUMERIC,
            emplr_prop_eoy_amt NUMERIC, bldgs_used_eoy_amt NUMERIC,
            tot_assets_eoy_amt NUMERIC, bnfts_payable_eoy_amt NUMERIC,
            oprtng_payable_eoy_amt NUMERIC, acquis_indbt_eoy_amt NUMERIC,
            other_liab_eoy_amt NUMERIC, tot_liabilities_eoy_amt NUMERIC,
            net_assets_eoy_amt NUMERIC,
            emplr_contrib_income_amt NUMERIC, participant_contrib_amt NUMERIC,
            oth_contrib_rcvd_amt NUMERIC, non_cash_contrib_bs_amt NUMERIC,
            tot_contrib_amt NUMERIC,
            int_bear_cash_amt NUMERIC, int_on_govt_sec_amt NUMERIC,
            int_on_corp_debt_amt NUMERIC, int_on_oth_loans_amt NUMERIC,
            int_on_partcp_loans_amt NUMERIC, int_on_oth_invst_amt NUMERIC,
            total_interest_amt NUMERIC,
            divnd_pref_stock_amt NUMERIC, divnd_common_stock_amt NUMERIC,
            registered_invst_amt NUMERIC, total_dividends_amt NUMERIC,
            total_rents_amt NUMERIC,
            aggregate_proceeds_amt NUMERIC, aggregate_costs_amt NUMERIC,
            tot_gain_loss_sale_ast_amt NUMERIC,
            unrealzd_apprctn_re_amt NUMERIC, unrealzd_apprctn_oth_amt NUMERIC,
            tot_unrealzd_apprctn_amt NUMERIC,
            gain_loss_com_trust_amt NUMERIC, gain_loss_pool_sep_amt NUMERIC,
            gain_loss_master_tr_amt NUMERIC, gain_loss_103_12_invst_amt NUMERIC,
            gain_loss_reg_invst_amt NUMERIC, other_income_amt NUMERIC,
            tot_income_amt NUMERIC,
            distrib_drt_partcp_amt NUMERIC, ins_carrier_bnfts_amt NUMERIC,
            oth_bnft_payment_amt NUMERIC, tot_distrib_bnft_amt NUMERIC,
            tot_corrective_distrib_amt NUMERIC, tot_deemed_distr_part_lns_amt NUMERIC,
            tot_int_expense_amt NUMERIC,
            professional_fees_amt NUMERIC, contract_admin_fees_amt NUMERIC,
            invst_mgmt_fees_amt NUMERIC, other_admin_fees_amt NUMERIC,
            tot_admin_expenses_amt NUMERIC, tot_expenses_amt NUMERIC,
            net_income_amt NUMERIC,
            tot_transfers_to_amt NUMERIC, tot_transfers_from_amt NUMERIC,
            acctnt_opinion_type_cd VARCHAR(10),
            acct_performed_ltd_audit_ind VARCHAR(10),
            accountant_firm_name VARCHAR(500), accountant_firm_ein VARCHAR(20),
            acct_opin_not_on_file_ind VARCHAR(10),
            fail_transmit_contrib_ind VARCHAR(10), fail_transmit_contrib_amt NUMERIC,
            loans_in_default_ind VARCHAR(10), loans_in_default_amt NUMERIC,
            leases_in_default_ind VARCHAR(10), leases_in_default_amt NUMERIC,
            party_in_int_not_rptd_ind VARCHAR(10), party_in_int_not_rptd_amt NUMERIC,
            plan_ins_fdlty_bond_ind VARCHAR(10), plan_ins_fdlty_bond_amt NUMERIC,
            loss_discv_dur_year_ind VARCHAR(10), loss_discv_dur_year_amt NUMERIC,
            asset_undeterm_val_ind VARCHAR(10), asset_undeterm_val_amt NUMERIC,
            non_cash_contrib_ind VARCHAR(10), non_cash_contrib_amt NUMERIC,
            ast_held_invst_ind VARCHAR(10), five_prcnt_trans_ind VARCHAR(10),
            all_plan_ast_distrib_ind VARCHAR(10),
            fail_provide_benefit_due_ind VARCHAR(10), fail_provide_benefit_due_amt NUMERIC,
            plan_blackout_period_ind VARCHAR(10), comply_blackout_notice_ind VARCHAR(10),
            res_term_plan_adpt_ind VARCHAR(10), res_term_plan_adpt_amt NUMERIC,
            fdcry_trust_ein VARCHAR(20), fdcry_trust_name VARCHAR(500),
            covered_pbgc_insurance_ind VARCHAR(10),
            trust_incur_unrel_tax_inc_ind VARCHAR(10), trust_incur_unrel_tax_inc_amt NUMERIC,
            in_service_distrib_ind VARCHAR(10), in_service_distrib_amt NUMERIC,
            fdcry_trustee_cust_name VARCHAR(500),
            fdcry_trust_cust_phon_num VARCHAR(30), fdcry_trust_cust_phon_nu_fore VARCHAR(30),
            distrib_made_employee_62_ind VARCHAR(10),
            premium_filing_confirm_number VARCHAR(50),
            acct_perf_ltd_audit_103_8_ind VARCHAR(10),
            acct_perf_ltd_audit_103_12_ind VARCHAR(10),
            acct_perf_not_ltd_audit_ind VARCHAR(10),
            salaries_allowances_amt NUMERIC, oth_recordkeeping_fees_amt NUMERIC,
            iqpa_audit_fees_amt NUMERIC, trustee_custodial_fees_amt NUMERIC,
            actuarial_fees_amt NUMERIC, legal_fees_amt NUMERIC,
            valuation_appraisal_fees_amt NUMERIC, other_trustee_fees_expenses_amt NUMERIC,
            form_year VARCHAR(10) DEFAULT '2023',
            created_at TIMESTAMPTZ NOT NULL DEFAULT now()
        );
        CREATE INDEX IF NOT EXISTS idx_schedule_h_ack ON dol.schedule_h(ack_id);
        CREATE INDEX IF NOT EXISTS idx_schedule_h_ein ON dol.schedule_h(sch_h_ein);
    """,
    "schedule_h_part1": """
        CREATE TABLE IF NOT EXISTS dol.schedule_h_part1 (
            id BIGSERIAL PRIMARY KEY,
            ack_id VARCHAR(50) NOT NULL,
            row_order INTEGER,
            plan_transfer_name VARCHAR(500),
            plan_transfer_ein VARCHAR(20),
            plan_transfer_pn VARCHAR(10),
            form_year VARCHAR(10) DEFAULT '2023',
            created_at TIMESTAMPTZ NOT NULL DEFAULT now()
        );
        CREATE INDEX IF NOT EXISTS idx_sch_h_p1_ack ON dol.schedule_h_part1(ack_id);
    """,

    # ===== SCHEDULE I =====
    "schedule_i": """
        CREATE TABLE IF NOT EXISTS dol.schedule_i (
            id BIGSERIAL PRIMARY KEY,
            ack_id VARCHAR(50) NOT NULL,
            sch_i_plan_year_begin_date VARCHAR(30),
            sch_i_tax_prd VARCHAR(30),
            sch_i_plan_num VARCHAR(10),
            sch_i_ein VARCHAR(20),
            small_tot_assets_boy_amt NUMERIC, small_tot_liabilities_boy_amt NUMERIC,
            small_net_assets_boy_amt NUMERIC,
            small_tot_assets_eoy_amt NUMERIC, small_tot_liabilities_eoy_amt NUMERIC,
            small_net_assets_eoy_amt NUMERIC,
            small_emplr_contrib_income_amt NUMERIC, small_participant_contrib_amt NUMERIC,
            small_oth_contrib_rcvd_amt NUMERIC, small_non_cash_contrib_bs_amt NUMERIC,
            small_other_income_amt NUMERIC, small_tot_income_amt NUMERIC,
            small_tot_distrib_bnft_amt NUMERIC, small_corrective_distrib_amt NUMERIC,
            small_deem_dstrb_partcp_ln_amt NUMERIC,
            small_admin_srvc_providers_amt NUMERIC, small_oth_expenses_amt NUMERIC,
            small_tot_expenses_amt NUMERIC, small_net_income_amt NUMERIC,
            small_tot_plan_transfers_amt NUMERIC,
            small_joint_venture_eoy_ind VARCHAR(10), small_joint_venture_eoy_amt NUMERIC,
            small_emplr_prop_eoy_ind VARCHAR(10), small_emplr_prop_eoy_amt NUMERIC,
            small_inv_real_estate_eoy_ind VARCHAR(10), small_inv_real_estate_eoy_amt NUMERIC,
            small_emplr_sec_eoy_ind VARCHAR(10), small_emplr_sec_eoy_amt NUMERIC,
            small_mortg_partcp_eoy_ind VARCHAR(10), small_mortg_partcp_eoy_amt NUMERIC,
            small_oth_lns_partcp_eoy_ind VARCHAR(10), small_oth_lns_partcp_eoy_amt NUMERIC,
            small_personal_prop_eoy_ind VARCHAR(10), small_personal_prop_eoy_amt NUMERIC,
            small_fail_transm_contrib_ind VARCHAR(10), small_fail_transm_contrib_amt NUMERIC,
            small_loans_in_default_ind VARCHAR(10), small_loans_in_default_amt NUMERIC,
            small_leases_in_default_ind VARCHAR(10), small_leases_in_default_amt NUMERIC,
            sm_party_in_int_not_rptd_ind VARCHAR(10), sm_party_in_int_not_rptd_amt NUMERIC,
            small_plan_ins_fdlty_bond_ind VARCHAR(10), small_plan_ins_fdlty_bond_amt NUMERIC,
            small_loss_discv_dur_year_ind VARCHAR(10), small_loss_discv_dur_year_amt NUMERIC,
            small_asset_undeterm_val_ind VARCHAR(10), small_asset_undeterm_val_amt NUMERIC,
            small_non_cash_contrib_ind VARCHAR(10), small_non_cash_contrib_amt NUMERIC,
            small_20_prcnt_sngl_invst_ind VARCHAR(10), small_20_prcnt_sngl_invst_amt NUMERIC,
            small_all_plan_ast_distrib_ind VARCHAR(10),
            sm_waiv_annual_iqpa_report_ind VARCHAR(10),
            sm_fail_provide_benef_due_ind VARCHAR(10), sm_fail_provide_benef_due_amt NUMERIC,
            small_plan_blackout_period_ind VARCHAR(10), sm_comply_blackout_notice_ind VARCHAR(10),
            small_res_term_plan_adpt_ind VARCHAR(10), small_res_term_plan_adpt_amt NUMERIC,
            fdcry_trust_ein VARCHAR(20), fdcry_trust_name VARCHAR(500),
            small_covered_pbgc_ins_ind VARCHAR(10),
            trust_incur_unrel_tax_inc_ind VARCHAR(10), trust_incur_unrel_tax_inc_amt NUMERIC,
            in_service_distrib_ind VARCHAR(10), in_service_distrib_amt NUMERIC,
            fdcry_trustee_cust_name VARCHAR(500),
            fdcry_trust_cust_phone_num VARCHAR(30), fdcry_trust_cust_phon_nu_fore VARCHAR(30),
            distrib_made_employee_62_ind VARCHAR(10),
            premium_filing_confirm_number VARCHAR(50),
            form_year VARCHAR(10) DEFAULT '2023',
            created_at TIMESTAMPTZ NOT NULL DEFAULT now()
        );
        CREATE INDEX IF NOT EXISTS idx_schedule_i_ack ON dol.schedule_i(ack_id);
        CREATE INDEX IF NOT EXISTS idx_schedule_i_ein ON dol.schedule_i(sch_i_ein);
    """,
    "schedule_i_part1": """
        CREATE TABLE IF NOT EXISTS dol.schedule_i_part1 (
            id BIGSERIAL PRIMARY KEY,
            ack_id VARCHAR(50) NOT NULL,
            row_order INTEGER,
            small_plan_transfer_name VARCHAR(500),
            small_plan_transfer_ein VARCHAR(20),
            small_plan_transfer_pn VARCHAR(10),
            form_year VARCHAR(10) DEFAULT '2023',
            created_at TIMESTAMPTZ NOT NULL DEFAULT now()
        );
        CREATE INDEX IF NOT EXISTS idx_sch_i_p1_ack ON dol.schedule_i_part1(ack_id);
    """,
}

# ---------------------------------------------------------------------------
# DB helpers
# ---------------------------------------------------------------------------

def get_connection():
    """Get psycopg2 connection using project env var conventions."""
    import psycopg2
    conn_string = os.getenv("DATABASE_URL") or os.getenv("NEON_CONNECTION_STRING")
    if not conn_string:
        host = os.getenv("NEON_HOST")
        database = os.getenv("NEON_DATABASE")
        user = os.getenv("NEON_USER")
        password = os.getenv("NEON_PASSWORD")
        if not all([host, database, user, password]):
            logger.error("No database connection info found. Set DATABASE_URL or NEON_* env vars.")
            sys.exit(1)
        conn_string = f"postgresql://{user}:{password}@{host}:5432/{database}?sslmode=require"
    return psycopg2.connect(conn_string)


def create_tables(conn):
    """Run all DDL statements."""
    cur = conn.cursor()
    cur.execute("CREATE SCHEMA IF NOT EXISTS dol;")
    for table_name, ddl in DDL.items():
        logger.info(f"  Creating dol.{table_name}...")
        cur.execute(ddl)
    conn.commit()
    cur.close()
    logger.info("All tables created successfully.")


def load_csv_to_table(conn, table_name: str, csv_path: Path) -> int:
    """
    Bulk-load a CSV into dol.{table_name} using COPY.
    Reads CSV header to build column list dynamically.
    Returns row count loaded.
    """
    cur = conn.cursor()

    # Read CSV header
    with open(csv_path, 'r', encoding='utf-8', errors='replace') as f:
        reader = csv.reader(f)
        header = [col.strip().lower() for col in next(reader)]

    # Columns to load = CSV columns (original, lowered)
    col_list = ", ".join(header)

    # Use COPY with StringIO for efficient bulk load
    logger.info(f"  Loading {csv_path.name} -> dol.{table_name} ({len(header)} cols)...")

    with open(csv_path, 'r', encoding='utf-8', errors='replace') as f:
        # Skip header
        next(f)
        # Use copy_expert for flexibility
        copy_sql = f"COPY dol.{table_name} ({col_list}) FROM STDIN WITH (FORMAT csv, NULL '', DELIMITER ',')"
        cur.copy_expert(copy_sql, f)

    conn.commit()

    # Get row count
    cur.execute(f"SELECT COUNT(*) FROM dol.{table_name} WHERE form_year = '2023'")
    count = cur.fetchone()[0]
    cur.close()

    logger.info(f"  ✓ dol.{table_name}: {count:,} rows loaded")
    return count


def verify_data(conn):
    """Post-load verification: row counts + ACK_ID join coverage."""
    cur = conn.cursor()
    results = {}

    logger.info("\n" + "=" * 70)
    logger.info("VERIFICATION REPORT")
    logger.info("=" * 70)

    # 1. Row counts per table
    logger.info("\n--- Row Counts ---")
    for table_name in DDL.keys():
        try:
            cur.execute(f"SELECT COUNT(*) FROM dol.{table_name}")
            count = cur.fetchone()[0]
            results[table_name] = count
            logger.info(f"  dol.{table_name}: {count:,}")
        except Exception as e:
            logger.warning(f"  dol.{table_name}: ERROR - {e}")
            conn.rollback()

    # 2. ACK_ID linkage to form_5500
    logger.info("\n--- ACK_ID Join Coverage (→ dol.form_5500) ---")
    for table_name in DDL.keys():
        try:
            cur.execute(f"""
                SELECT
                    COUNT(DISTINCT s.ack_id) AS total_ack_ids,
                    COUNT(DISTINCT f.ack_id) AS matched_to_5500,
                    ROUND(COUNT(DISTINCT f.ack_id)::numeric / NULLIF(COUNT(DISTINCT s.ack_id), 0) * 100, 1) AS match_pct
                FROM dol.{table_name} s
                LEFT JOIN dol.form_5500 f ON f.ack_id = s.ack_id
            """)
            row = cur.fetchone()
            logger.info(f"  dol.{table_name}: {row[1]:,}/{row[0]:,} matched ({row[2]}%)")
        except Exception as e:
            logger.warning(f"  dol.{table_name}: ERROR - {e}")
            conn.rollback()

    # 3. ACK_ID linkage to form_5500_sf
    logger.info("\n--- ACK_ID Join Coverage (→ dol.form_5500_sf) ---")
    for table_name in ["schedule_h", "schedule_i", "schedule_d", "schedule_g", "schedule_c"]:
        try:
            cur.execute(f"""
                SELECT
                    COUNT(DISTINCT s.ack_id) AS total_ack_ids,
                    COUNT(DISTINCT sf.ack_id) AS matched_to_sf,
                    ROUND(COUNT(DISTINCT sf.ack_id)::numeric / NULLIF(COUNT(DISTINCT s.ack_id), 0) * 100, 1) AS match_pct
                FROM dol.{table_name} s
                LEFT JOIN dol.form_5500_sf sf ON sf.ack_id = s.ack_id
            """)
            row = cur.fetchone()
            logger.info(f"  dol.{table_name}: {row[1]:,}/{row[0]:,} matched to SF ({row[2]}%)")
        except Exception as e:
            logger.warning(f"  dol.{table_name}: ERROR - {e}")
            conn.rollback()

    cur.close()
    logger.info("\n" + "=" * 70)
    return results


# ---------------------------------------------------------------------------
# MAIN
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description="Import DOL 5500 Schedules C/D/G/H/I to Neon")
    parser.add_argument("--create-tables", action="store_true", help="Run DDL to create tables")
    parser.add_argument("--load", action="store_true", help="Load CSVs into tables")
    parser.add_argument("--verify", action="store_true", help="Run post-load verification")
    parser.add_argument("--table", type=str, help="Load only a specific table (e.g. schedule_c_part1_item2)")
    args = parser.parse_args()

    if not any([args.create_tables, args.load, args.verify]):
        parser.print_help()
        sys.exit(0)

    conn = get_connection()
    logger.info("Connected to Neon.")

    try:
        # Step 1: Create tables
        if args.create_tables:
            logger.info("\n=== CREATING TABLES ===")
            create_tables(conn)

        # Step 2: Load CSVs
        if args.load:
            logger.info("\n=== LOADING CSVs ===")
            manifest = {}
            tables_to_load = TABLE_CSV_MAP.items()

            if args.table:
                if args.table not in TABLE_CSV_MAP:
                    logger.error(f"Unknown table: {args.table}. Options: {list(TABLE_CSV_MAP.keys())}")
                    sys.exit(1)
                tables_to_load = [(args.table, TABLE_CSV_MAP[args.table])]

            for table_name, (subfolder, csv_file) in tables_to_load:
                csv_path = DATA_DIR / subfolder / csv_file
                if not csv_path.exists():
                    logger.error(f"  ✗ MISSING: {csv_path}")
                    manifest[table_name] = {"status": "MISSING", "file": str(csv_path)}
                    continue

                start = time.time()
                try:
                    count = load_csv_to_table(conn, table_name, csv_path)
                    elapsed = round(time.time() - start, 1)
                    manifest[table_name] = {
                        "status": "OK",
                        "file": csv_file,
                        "rows": count,
                        "seconds": elapsed,
                    }
                except Exception as e:
                    logger.error(f"  ✗ FAILED loading {table_name}: {e}")
                    conn.rollback()
                    manifest[table_name] = {"status": "FAILED", "file": csv_file, "error": str(e)}

            # Print manifest
            logger.info("\n=== LOAD MANIFEST ===")
            for tbl, info in manifest.items():
                if info["status"] == "OK":
                    logger.info(f"  ✓ dol.{tbl}: {info['rows']:,} rows ({info['seconds']}s) — {info['file']}")
                else:
                    logger.info(f"  ✗ dol.{tbl}: {info['status']} — {info.get('error', info.get('file', ''))}")

        # Step 3: Verify
        if args.verify:
            verify_data(conn)

    finally:
        conn.close()
        logger.info("\nDone. Connection closed.")


if __name__ == "__main__":
    main()
