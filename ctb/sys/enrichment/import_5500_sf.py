#!/usr/bin/env python3
"""
DOL Form 5500-SF Import Script

Imports DOL Form 5500-SF (Short Form) data for small plans (<100 participants).
Complements the regular Form 5500 for large plans (>=100 participants).

Based on 2023 F_5500_SF data dictionary / file layout.

Input: data/F_5500_SF_2023_latest.csv
Output: Loads to marketing.form_5500_sf via staging table
"""

import pandas as pd
import os
from pathlib import Path

# ============================================================================
# CONFIGURATION - CHANGE YEAR HERE
# ============================================================================
YEAR = "2023"
DATA_DIR = Path("data")

# ============================================================================
# STEP 1: LOAD CSV
# ============================================================================
print(f"Loading Form 5500-SF (Short Form) for {YEAR}...")
df = pd.read_csv(
    DATA_DIR / f"F_5500_SF_{YEAR}_latest.csv",
    dtype=str,  # Keep all as strings initially
    low_memory=False
)

# Strip leading/trailing spaces
print("Stripping whitespace from all string columns...")
df = df.apply(lambda x: x.str.strip() if x.dtype == "object" else x)

print(f"Loaded {len(df):,} Form 5500-SF filings")

# ============================================================================
# STEP 2: VERIFY REQUIRED COLUMNS
# ============================================================================
print("\nVerifying required columns...")

required_columns = [
    "ACK_ID",
    "SF_SPONS_EIN",
    "SF_SPONSOR_NAME"
]

missing = [col for col in required_columns if col not in df.columns]
if missing:
    raise ValueError(f"Missing required columns: {missing}")

print(f"[OK] All required columns present")
print(f"  Unique ACK_IDs: {df['ACK_ID'].nunique():,}")
print(f"  Unique EINs: {df['SF_SPONS_EIN'].nunique():,}")

# ============================================================================
# STEP 3: COLUMN MAPPING (DOL → Neon schema)
# ============================================================================
print("\nMapping columns to database schema...")

# Map DOL column names (5500-SF uses SF_ prefix) to Neon schema
column_mapping = {
    # Primary key
    "ACK_ID": "ack_id",

    # System metadata
    "SF_FILING_STATUS": "filing_status",
    "SF_DATE_RECEIVED": "date_received",
    "SF_VALID_SIG": "valid_sig",

    # Sponsor/Company fields (5500-SF uses SF_ prefix)
    "SF_SPONS_EIN": "sponsor_dfe_ein",
    "SF_SPONSOR_NAME": "sponsor_dfe_name",
    "SF_SPONSOR_DFE_DBA_NAME": "spons_dfe_dba_name",

    # Mailing address (5500-SF format)
    "SF_SPONS_US_ADDRESS1": "spons_dfe_mail_us_address1",
    "SF_SPONS_US_ADDRESS2": "spons_dfe_mail_us_address2",
    "SF_SPONS_US_CITY": "spons_dfe_mail_us_city",
    "SF_SPONS_US_STATE": "spons_dfe_mail_us_state",
    "SF_SPONS_US_ZIP": "spons_dfe_mail_us_zip",

    # Foreign address (may be present)
    "SF_SPONS_FOREIGN_ADDRESS1": "spons_dfe_loc_us_address1",
    "SF_SPONS_FOREIGN_ADDRESS2": "spons_dfe_loc_us_address2",
    "SF_SPONS_FOREIGN_CITY": "spons_dfe_loc_us_city",
    "SF_SPONS_FOREIGN_PROV_STATE": "spons_dfe_loc_us_state",
    "SF_SPONS_FOREIGN_POSTAL_CD": "spons_dfe_loc_us_zip",

    # Contact
    "SF_SPONS_PHONE_NUM": "spons_dfe_phone_num",
    "SF_BUSINESS_CD": "business_code",

    # Plan-level fields (5500-SF format)
    "SF_PLAN_NAME": "plan_name",
    "SF_PLAN_NUM": "plan_number",

    # Plan type codes (benefit codes, not boolean indicators)
    "SF_TYPE_PENSION_BNFT_CODE": "plan_type_pension_ind",
    "SF_TYPE_WELFARE_BNFT_CODE": "plan_type_welfare_ind",

    # Funding indicators
    "SF_FUNDING_INSURANCE_IND": "funding_insurance_ind",
    "SF_FUNDING_TRUST_IND": "funding_trust_ind",
    "SF_FUNDING_GEN_ASSETS_IND": "funding_gen_assets_ind",

    # Benefit indicators
    "SF_BENEFIT_INSURANCE_IND": "benefit_insurance_ind",
    "SF_BENEFIT_TRUST_IND": "benefit_trust_ind",
    "SF_BENEFIT_GEN_ASSETS_IND": "benefit_gen_assets_ind",

    # Participant counts (5500-SF format)
    "SF_TOT_ACT_PARTCP_BOY_CNT": "tot_active_partcp_boy_cnt",
    "SF_TOT_PARTCP_BOY_CNT": "tot_partcp_boy_cnt",
    "SF_TOT_ACT_PARTCP_EOY_CNT": "tot_active_partcp_eoy_cnt",
    "SF_TOT_PARTCP_EOY_CNT": "tot_partcp_eoy_cnt",
    "SF_PARTCP_CNT_IND": "participant_cnt_rptd_ind",

    # Plan year and program flags
    "SF_SHORT_PLAN_YR_IND": "short_plan_year_ind",
    "SF_DFVC_PROGRAM_IND": "dfvc_program_ind",

    # Schedule attachment indicators
    "SF_SCH_A_ATTACHED_IND": "sch_a_attached_ind",
    "SF_NUM_SCH_A_ATTACHED_CNT": "num_sch_a_attached_cnt",
    "SF_MEWA_IND": "mewa_m1_attached_ind",
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
    "filing_status",
    "date_received",
    "valid_sig",
    "sponsor_dfe_ein",
    "sponsor_dfe_name",
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
    "plan_name",
    "plan_number",
    "plan_type_pension_ind",
    "plan_type_welfare_ind",
    "funding_insurance_ind",
    "funding_trust_ind",
    "funding_gen_assets_ind",
    "benefit_insurance_ind",
    "benefit_trust_ind",
    "benefit_gen_assets_ind",
    "tot_active_partcp_boy_cnt",
    "tot_partcp_boy_cnt",
    "tot_active_partcp_eoy_cnt",
    "tot_partcp_eoy_cnt",
    "participant_cnt_rptd_ind",
    "short_plan_year_ind",
    "dfvc_program_ind",
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
    "mewa_m1_attached_ind",
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
output_file = Path("output") / f"form_5500_sf_{YEAR}_staging.csv"
output_file.parent.mkdir(exist_ok=True)

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

print(f"\nForm 5500-SF ({YEAR}):")
print(f"  Total filings: {len(df_staging):,}")
print(f"  Unique sponsors (EIN): {df_staging['sponsor_dfe_ein'].nunique():,}")
print(f"  Unique states: {df_staging['spons_dfe_mail_us_state'].nunique():,}")

# Plan type breakdown
pension_count = (df_staging['plan_type_pension_ind'] == '1').sum()
welfare_count = (df_staging['plan_type_welfare_ind'] == '1').sum()
print(f"\nPlan Types:")
print(f"  Pension plans: {pension_count:,} ({100*pension_count/len(df_staging):.1f}%)")
print(f"  Welfare plans: {welfare_count:,} ({100*welfare_count/len(df_staging):.1f}%)")

# Schedule attachment stats
sch_a_count = (df_staging['sch_a_attached_ind'] == '1').sum()
sch_c_count = (df_staging['sch_c_attached_ind'] == '1').sum()
print(f"\nSchedule Attachments:")
print(f"  Schedule A (insurance): {sch_a_count:,} ({100*sch_a_count/len(df_staging):.1f}%)")
print(f"  Schedule C (service providers): {sch_c_count:,} ({100*sch_c_count/len(df_staging):.1f}%)")

# Participant count distribution
df_staging['tot_partcp_eoy_cnt_numeric'] = pd.to_numeric(df_staging['tot_partcp_eoy_cnt'], errors='coerce')
print(f"\nParticipant Count Distribution:")
print(f"  Min: {df_staging['tot_partcp_eoy_cnt_numeric'].min():.0f}")
print(f"  Median: {df_staging['tot_partcp_eoy_cnt_numeric'].median():.0f}")
print(f"  Max: {df_staging['tot_partcp_eoy_cnt_numeric'].max():.0f}")
print(f"  Mean: {df_staging['tot_partcp_eoy_cnt_numeric'].mean():.1f}")

# ============================================================================
# NEXT STEPS
# ============================================================================
print("\n" + "=" * 80)
print("NEXT STEPS")
print("=" * 80)
print(f"""
1. IMPORT TO STAGING TABLE:
   psql $NEON_CONNECTION_STRING << 'EOF'
   \\COPY marketing.form_5500_sf_staging FROM '{output_file.absolute()}' CSV HEADER;
   EOF

2. VERIFY STAGING:
   psql $NEON_CONNECTION_STRING -c "SELECT COUNT(*) FROM marketing.form_5500_sf_staging;"

3. PROCESS STAGING (matches companies, updates EINs):
   psql $NEON_CONNECTION_STRING -c "CALL marketing.process_5500_sf_staging();"

4. VERIFY MAIN TABLE:
   psql $NEON_CONNECTION_STRING -c "SELECT COUNT(*) FROM marketing.form_5500_sf;"

5. CHECK MATCH RATE:
   psql $NEON_CONNECTION_STRING -c "
   SELECT
       COUNT(*) as total,
       COUNT(company_unique_id) as matched,
       ROUND(100.0 * COUNT(company_unique_id) / COUNT(*), 1) as match_rate_pct
   FROM marketing.form_5500_sf;
   "

6. FILTER BY PLAN TYPE:
   -- Pension plans only
   SELECT * FROM marketing.form_5500_sf WHERE plan_type_pension_ind = '1';

   -- Welfare plans only
   SELECT * FROM marketing.form_5500_sf WHERE plan_type_welfare_ind = '1';

7. JOIN TO REGULAR 5500 (UNION for complete coverage):
   SELECT '5500' as form_type, sponsor_dfe_ein, sponsor_dfe_name, state
   FROM marketing.form_5500
   UNION ALL
   SELECT '5500-SF' as form_type, sponsor_dfe_ein, sponsor_dfe_name, spons_dfe_mail_us_state
   FROM marketing.form_5500_sf;
""")

print("=" * 80)
print("SCRIPT COMPLETE!")
print("=" * 80)
