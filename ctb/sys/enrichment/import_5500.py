#!/usr/bin/env python3
"""
DOL Form 5500 Import Script

Imports DOL Form 5500 (Regular) data for large plans (>=100 participants).
Complements the Form 5500-SF for small plans (<100 participants).

Based on 2023 F_5500 data dictionary / file layout.

Input: data/F_5500_2023_latest.csv (or f_5500_2023_latest.csv)
Output: output/form_5500_2023_staging.csv
"""

import pandas as pd
import os
from pathlib import Path

# ============================================================================
# CONFIGURATION - CHANGE YEAR HERE
# ============================================================================
YEAR = "2023"
DATA_DIR = Path(__file__).parent.parent.parent.parent / "data"
OUTPUT_DIR = Path(__file__).parent / "output"

# Ensure output directory exists
OUTPUT_DIR.mkdir(exist_ok=True)

# ============================================================================
# STEP 1: FIND AND LOAD CSV
# ============================================================================
print(f"Loading Form 5500 (Regular) for {YEAR}...")

# Try multiple possible filenames
possible_files = [
    DATA_DIR / f"F_5500_{YEAR}_latest.csv",
    DATA_DIR / f"f_5500_{YEAR}_latest.csv",
    DATA_DIR / f"F_5500_{YEAR}_Latest.csv",
]

input_file = None
for f in possible_files:
    if f.exists():
        input_file = f
        break

if input_file is None:
    print(f"ERROR: Could not find Form 5500 CSV file")
    print(f"  Searched in: {DATA_DIR}")
    print(f"  Expected filenames:")
    for f in possible_files:
        print(f"    - {f.name}")
    exit(1)

print(f"  Found: {input_file}")

df = pd.read_csv(
    input_file,
    dtype=str,  # Keep all as strings initially
    low_memory=False
)

# Strip leading/trailing spaces
print("Stripping whitespace from all string columns...")
df = df.apply(lambda x: x.str.strip() if x.dtype == "object" else x)

print(f"Loaded {len(df):,} Form 5500 filings")

# ============================================================================
# STEP 2: VERIFY REQUIRED COLUMNS
# ============================================================================
print("\nVerifying required columns...")

required_columns = [
    "ACK_ID",
    "SPONS_DFE_EIN",
    "SPONSOR_DFE_NAME"
]

missing = [col for col in required_columns if col not in df.columns]
if missing:
    raise ValueError(f"Missing required columns: {missing}")

print(f"[OK] All required columns present")
print(f"  Unique ACK_IDs: {df['ACK_ID'].nunique():,}")
print(f"  Unique EINs: {df['SPONS_DFE_EIN'].nunique():,}")

# ============================================================================
# STEP 3: COLUMN MAPPING (DOL → Neon schema)
# ============================================================================
print("\nMapping columns to database schema...")

# Map DOL column names to Neon schema (lowercase with underscores)
column_mapping = {
    # Primary key
    "ACK_ID": "ack_id",

    # System metadata
    "FORM_PLAN_YEAR_BEGIN_DATE": "form_plan_year_begin_date",
    "FORM_TAX_PRD": "form_tax_prd",
    "FILING_STATUS": "filing_status",
    "DATE_RECEIVED": "date_received",

    # Plan entity types
    "TYPE_PLAN_ENTITY_CD": "type_plan_entity_cd",
    "TYPE_DFE_PLAN_ENTITY_CD": "type_dfe_plan_entity_cd",

    # Filing flags
    "INITIAL_FILING_IND": "initial_filing_ind",
    "AMENDED_IND": "amended_ind",
    "FINAL_FILING_IND": "final_filing_ind",
    "SHORT_PLAN_YR_IND": "short_plan_yr_ind",
    "COLLECTIVE_BARGAIN_IND": "collective_bargain_ind",

    # Plan info
    "PLAN_NAME": "plan_name",
    "SPONS_DFE_PN": "plan_number",
    "PLAN_EFF_DATE": "plan_eff_date",

    # Sponsor/Company fields
    "SPONS_DFE_EIN": "sponsor_dfe_ein",
    "SPONSOR_DFE_NAME": "sponsor_dfe_name",
    "SPONS_DFE_DBA_NAME": "spons_dfe_dba_name",

    # Mailing address
    "SPONS_DFE_MAIL_US_ADDRESS1": "spons_dfe_mail_us_address1",
    "SPONS_DFE_MAIL_US_ADDRESS2": "spons_dfe_mail_us_address2",
    "SPONS_DFE_MAIL_US_CITY": "spons_dfe_mail_us_city",
    "SPONS_DFE_MAIL_US_STATE": "spons_dfe_mail_us_state",
    "SPONS_DFE_MAIL_US_ZIP": "spons_dfe_mail_us_zip",

    # Location address
    "SPONS_DFE_LOC_US_ADDRESS1": "spons_dfe_loc_us_address1",
    "SPONS_DFE_LOC_US_ADDRESS2": "spons_dfe_loc_us_address2",
    "SPONS_DFE_LOC_US_CITY": "spons_dfe_loc_us_city",
    "SPONS_DFE_LOC_US_STATE": "spons_dfe_loc_us_state",
    "SPONS_DFE_LOC_US_ZIP": "spons_dfe_loc_us_zip",

    # Contact
    "SPONS_DFE_PHONE_NUM": "spons_dfe_phone_num",
    "BUSINESS_CODE": "business_code",

    # Participant counts
    "TOT_PARTCP_BOY_CNT": "tot_partcp_boy_cnt",
    "TOT_ACTIVE_PARTCP_CNT": "tot_active_partcp_cnt",
    "RTD_SEP_PARTCP_RCVG_CNT": "rtd_sep_partcp_rcvg_cnt",
    "RTD_SEP_PARTCP_FUT_CNT": "rtd_sep_partcp_fut_cnt",
    "SUBTL_ACT_RTD_SEP_CNT": "subtl_act_rtd_sep_cnt",
    "BENEF_RCVG_BNFT_CNT": "benef_rcvg_bnft_cnt",
    "TOT_ACT_RTD_SEP_BENEF_CNT": "tot_act_rtd_sep_benef_cnt",
    "PARTCP_ACCOUNT_BAL_CNT": "partcp_account_bal_cnt",
    "SEP_PARTCP_PARTL_VSTD_CNT": "sep_partcp_partl_vstd_cnt",
    "CONTRIB_EMPLRS_CNT": "contrib_emplrs_cnt",

    # Plan type codes
    "TYPE_PENSION_BNFT_CODE": "type_pension_bnft_code",
    "TYPE_WELFARE_BNFT_CODE": "type_welfare_bnft_code",

    # Funding indicators
    "FUNDING_INSURANCE_IND": "funding_insurance_ind",
    "FUNDING_SEC412_IND": "funding_sec412_ind",
    "FUNDING_TRUST_IND": "funding_trust_ind",
    "FUNDING_GEN_ASSET_IND": "funding_gen_asset_ind",

    # Benefit indicators
    "BENEFIT_INSURANCE_IND": "benefit_insurance_ind",
    "BENEFIT_SEC412_IND": "benefit_sec412_ind",
    "BENEFIT_TRUST_IND": "benefit_trust_ind",
    "BENEFIT_GEN_ASSET_IND": "benefit_gen_asset_ind",

    # Schedule attachment indicators
    "SCH_A_ATTACHED_IND": "sch_a_attached_ind",
    "NUM_SCH_A_ATTACHED_CNT": "num_sch_a_attached_cnt",
    "SCH_C_ATTACHED_IND": "sch_c_attached_ind",
    "SCH_D_ATTACHED_IND": "sch_d_attached_ind",
    "SCH_G_ATTACHED_IND": "sch_g_attached_ind",
    "SCH_H_ATTACHED_IND": "sch_h_attached_ind",
    "SCH_I_ATTACHED_IND": "sch_i_attached_ind",
    "SCH_MB_ATTACHED_IND": "sch_mb_attached_ind",
    "SCH_SB_ATTACHED_IND": "sch_sb_attached_ind",
    "SCH_R_ATTACHED_IND": "sch_r_attached_ind",

    # Admin info
    "ADMIN_NAME": "admin_name",
    "ADMIN_EIN": "admin_ein",
    "ADMIN_US_STATE": "admin_us_state",
}

# Rename columns that exist in the dataframe
available_mappings = {k: v for k, v in column_mapping.items() if k in df.columns}
df_staging = df.rename(columns=available_mappings)

# Add form_year column (constant for this dataset)
df_staging["form_year"] = YEAR

print(f"[OK] Mapped {len(available_mappings)} columns")
print(f"  Missing optional columns: {len(column_mapping) - len(available_mappings)}")

# ============================================================================
# STEP 4: SELECT STAGING COLUMNS
# ============================================================================
staging_columns = [
    "ack_id",
    "form_plan_year_begin_date",
    "form_tax_prd",
    "type_plan_entity_cd",
    "type_dfe_plan_entity_cd",
    "initial_filing_ind",
    "amended_ind",
    "final_filing_ind",
    "short_plan_yr_ind",
    "collective_bargain_ind",
    "plan_name",
    "plan_number",
    "plan_eff_date",
    "sponsor_dfe_ein",
    "sponsor_dfe_name",
    "spons_dfe_dba_name",
    "spons_dfe_mail_us_address1",
    "spons_dfe_mail_us_address2",
    "spons_dfe_mail_us_city",
    "spons_dfe_mail_us_state",
    "spons_dfe_mail_us_zip",
    "spons_dfe_loc_us_address1",
    "spons_dfe_loc_us_address2",
    "spons_dfe_loc_us_city",
    "spons_dfe_loc_us_state",
    "spons_dfe_loc_us_zip",
    "spons_dfe_phone_num",
    "business_code",
    "tot_partcp_boy_cnt",
    "tot_active_partcp_cnt",
    "rtd_sep_partcp_rcvg_cnt",
    "rtd_sep_partcp_fut_cnt",
    "subtl_act_rtd_sep_cnt",
    "benef_rcvg_bnft_cnt",
    "tot_act_rtd_sep_benef_cnt",
    "partcp_account_bal_cnt",
    "sep_partcp_partl_vstd_cnt",
    "contrib_emplrs_cnt",
    "type_pension_bnft_code",
    "type_welfare_bnft_code",
    "funding_insurance_ind",
    "funding_sec412_ind",
    "funding_trust_ind",
    "funding_gen_asset_ind",
    "benefit_insurance_ind",
    "benefit_sec412_ind",
    "benefit_trust_ind",
    "benefit_gen_asset_ind",
    "sch_a_attached_ind",
    "num_sch_a_attached_cnt",
    "sch_c_attached_ind",
    "sch_d_attached_ind",
    "sch_g_attached_ind",
    "sch_h_attached_ind",
    "sch_i_attached_ind",
    "sch_mb_attached_ind",
    "sch_sb_attached_ind",
    "sch_r_attached_ind",
    "admin_name",
    "admin_ein",
    "admin_us_state",
    "filing_status",
    "date_received",
    "form_year"
]

# Add missing columns as empty strings
for col in staging_columns:
    if col not in df_staging.columns:
        df_staging[col] = ""

df_staging = df_staging[staging_columns]

print(f"\n[OK] Prepared {len(df_staging):,} records for staging")

# ============================================================================
# STEP 5: WRITE STAGING CSV FOR PSQL IMPORT
# ============================================================================
output_file = OUTPUT_DIR / f"form_5500_{YEAR}_staging.csv"

df_staging.to_csv(output_file, index=False, encoding="utf-8")
print(f"\n[OK] Wrote staging CSV: {output_file}")
print(f"  Rows: {len(df_staging):,}")
print(f"  Columns: {len(staging_columns)}")

# ============================================================================
# SUMMARY STATISTICS
# ============================================================================
print("\n" + "=" * 80)
print("SUMMARY STATISTICS")
print("=" * 80)

print(f"\nForm 5500 ({YEAR}):")
print(f"  Total filings: {len(df_staging):,}")
print(f"  Unique sponsors (EIN): {df_staging['sponsor_dfe_ein'].nunique():,}")
print(f"  Unique states: {df_staging['spons_dfe_mail_us_state'].nunique():,}")

# Top states
print(f"\nTop 10 States by Filing Count:")
state_counts = df_staging['spons_dfe_mail_us_state'].value_counts().head(10)
for state, count in state_counts.items():
    pct = 100 * count / len(df_staging)
    print(f"  {state}: {count:,} ({pct:.1f}%)")

# Schedule attachment stats
sch_a_count = (df_staging['sch_a_attached_ind'] == '1').sum()
sch_h_count = (df_staging['sch_h_attached_ind'] == '1').sum()
print(f"\nSchedule Attachments:")
print(f"  Schedule A (insurance): {sch_a_count:,} ({100*sch_a_count/len(df_staging):.1f}%)")
print(f"  Schedule H (financial): {sch_h_count:,} ({100*sch_h_count/len(df_staging):.1f}%)")

# Participant count distribution
df_staging['tot_active_partcp_cnt_numeric'] = pd.to_numeric(df_staging['tot_active_partcp_cnt'], errors='coerce')
print(f"\nParticipant Count Distribution:")
print(f"  Min: {df_staging['tot_active_partcp_cnt_numeric'].min():.0f}")
print(f"  Median: {df_staging['tot_active_partcp_cnt_numeric'].median():.0f}")
print(f"  Max: {df_staging['tot_active_partcp_cnt_numeric'].max():.0f}")
print(f"  Mean: {df_staging['tot_active_partcp_cnt_numeric'].mean():.1f}")

# ============================================================================
# NEXT STEPS
# ============================================================================
print("\n" + "=" * 80)
print("NEXT STEPS")
print("=" * 80)
print(f"""
1. CREATE TABLE (if not done):
   node ctb/sys/enrichment/create_form_5500_table.js

2. IMPORT TO STAGING TABLE:
   psql $NEON_CONNECTION_STRING << 'EOF'
   \\COPY marketing.form_5500_staging FROM '{output_file.absolute()}' CSV HEADER;
   EOF

3. VERIFY STAGING:
   psql $NEON_CONNECTION_STRING -c "SELECT COUNT(*) FROM marketing.form_5500_staging;"

4. PROCESS STAGING (matches companies, updates EINs):
   psql $NEON_CONNECTION_STRING -c "CALL marketing.process_5500_staging();"

5. VERIFY MAIN TABLE:
   psql $NEON_CONNECTION_STRING -c "SELECT COUNT(*) FROM marketing.form_5500;"

6. CHECK MATCH RATE:
   psql $NEON_CONNECTION_STRING -c "
   SELECT
       COUNT(*) as total,
       COUNT(company_unique_id) as matched,
       ROUND(100.0 * COUNT(company_unique_id) / COUNT(*), 1) as match_rate_pct
   FROM marketing.form_5500;
   "
""")

print("=" * 80)
print("SCRIPT COMPLETE!")
print("=" * 80)
