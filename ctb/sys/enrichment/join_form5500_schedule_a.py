#!/usr/bin/env python3
"""
DOL Form 5500 + Schedule A Join Script

Joins main Form 5500 filings with Schedule A (insurance information)
using ACK_ID as the primary join key per DOL Form 5500 Datasets Guide.

Input:
  - data/F_5500_2023_latest.csv (main form)
  - data/F_SCH_A_2023_latest.csv (Schedule A)

Output:
  - output/form5500_filings_2023_clean.csv (one row per ACK_ID)
  - output/schedule_a_2023_joined.csv (Schedule A joined with main form)
"""

import pandas as pd
import os
from pathlib import Path

# ============================================================================
# CONFIGURATION - CHANGE YEAR HERE
# ============================================================================
YEAR = "2023"
DATA_DIR = Path("data")
OUTPUT_DIR = Path("output")

# Ensure output directory exists
OUTPUT_DIR.mkdir(exist_ok=True)

# ============================================================================
# STEP 1: LOAD CSVs WITH GOOD DTYPES
# ============================================================================
print(f"Loading Form 5500 main form for {YEAR}...")
df_5500 = pd.read_csv(
    DATA_DIR / f"F_5500_{YEAR}_latest.csv",
    dtype=str,  # Keep all as strings initially
    low_memory=False
)

print(f"Loading Schedule A for {YEAR}...")
df_sch_a = pd.read_csv(
    DATA_DIR / f"F_SCH_A_{YEAR}_latest.csv",
    dtype=str,  # Keep all as strings initially
    low_memory=False
)

# Strip leading/trailing spaces from all string columns
print("Stripping whitespace from all string columns...")
df_5500 = df_5500.apply(lambda x: x.str.strip() if x.dtype == "object" else x)
df_sch_a = df_sch_a.apply(lambda x: x.str.strip() if x.dtype == "object" else x)

print(f"Loaded {len(df_5500):,} Form 5500 filings")
print(f"Loaded {len(df_sch_a):,} Schedule A records")

# ============================================================================
# STEP 2: VERIFY AND NORMALIZE JOIN KEYS
# ============================================================================
print("\nVerifying join keys...")

# Verify ACK_ID exists in both dataframes
if "ACK_ID" not in df_5500.columns:
    raise ValueError("ACK_ID column not found in Form 5500 main file")
if "ACK_ID" not in df_sch_a.columns:
    raise ValueError("ACK_ID column not found in Schedule A file")

print(f"✓ ACK_ID found in both files")
print(f"  Form 5500 unique ACK_IDs: {df_5500['ACK_ID'].nunique():,}")
print(f"  Schedule A unique ACK_IDs: {df_sch_a['ACK_ID'].nunique():,}")

# Optional: Filter to only filings that have Schedule A attached
if "SCH_A_ATTACHED_IND" in df_5500.columns:
    before_count = len(df_5500)
    df_5500 = df_5500[df_5500["SCH_A_ATTACHED_IND"] == "1"].copy()
    print(f"  Filtered to {len(df_5500):,} filings with SCH_A_ATTACHED_IND='1' (removed {before_count - len(df_5500):,})")
else:
    print("  Warning: SCH_A_ATTACHED_IND column not found, keeping all Form 5500 records")

# ============================================================================
# STEP 3: CREATE JOINED VIEW FOR ANALYSIS
# ============================================================================
print("\nJoining Schedule A to main form on ACK_ID...")

# LEFT JOIN: Schedule A onto main form (keeps all Schedule A records)
# Per DOL guide, ACK_ID is the primary join key between forms and schedules
df_join = df_sch_a.merge(
    df_5500,
    on="ACK_ID",
    how="left",
    suffixes=("_sch_a", "_5500")
)

print(f"✓ Join complete: {len(df_join):,} records")
print(f"  Matched to main form: {df_join['SPONS_DFE_EIN'].notna().sum():,}")
print(f"  Unmatched Schedule A records: {df_join['SPONS_DFE_EIN'].isna().sum():,}")

# Create thinner projection with key columns
# Column names match DOL Form 5500 Datasets Guide exactly
projection_columns = {
    # From main form (df_5500)
    "ACK_ID": "ACK_ID",
    "SPONS_DFE_EIN": "SPONS_DFE_EIN",
    "SPONS_DFE_NAME": "SPONS_DFE_NAME",
    "SPONS_DFE_MAIL_US_ADDRESS1": "SPONS_DFE_MAIL_US_ADDRESS1",
    "SPONS_DFE_MAIL_US_CITY": "SPONS_DFE_MAIL_US_CITY",
    "SPONS_DFE_MAIL_US_STATE": "SPONS_DFE_MAIL_US_STATE",
    "SPONS_DFE_MAIL_US_ZIP": "SPONS_DFE_MAIL_US_ZIP",
    "PLAN_NUM": "PLAN_NUM",  # Note: may be PLAN_NUM or PLAN_NUMBER depending on year

    # From Schedule A (df_sch_a)
    "FORM_ID": "FORM_ID",
    "INSURANCE_COMPANY_NAME": "INSURANCE_COMPANY_NAME",
    "INSURANCE_COMPANY_EIN": "INSURANCE_COMPANY_EIN",
    "NAIC_NUMBER": "NAIC_NUMBER",  # Note: may be NAIC_CODE or NAIC_NUMBER
    "CONTRACT_NUMBER": "CONTRACT_NUMBER",
    "WELFARE_BENEFIT_CODE": "WELFARE_BENEFIT_CODE",
    "COVERED_LIVES": "COVERED_LIVES",
}

# Select only columns that exist in the joined dataframe
available_columns = [col for col in projection_columns.keys() if col in df_join.columns]
missing_columns = set(projection_columns.keys()) - set(available_columns)

if missing_columns:
    print(f"\n  Warning: These expected columns are missing: {missing_columns}")
    print(f"  Available columns will be used: {len(available_columns)} of {len(projection_columns)}")

df_5500_sch_a_joined = df_join[available_columns].copy()

# ============================================================================
# STEP 4: ADD COMPANY KEY FOR EIN MASTER
# ============================================================================
print("\nCreating normalized company_key_ein...")

def normalize_ein(ein):
    """Normalize EIN: strip spaces, leading zeros, convert to 9 digits"""
    if pd.isna(ein) or ein == "":
        return None
    ein_clean = str(ein).strip().replace("-", "").replace(" ", "")
    # Remove leading zeros, then pad back to 9 digits
    ein_clean = ein_clean.lstrip("0")
    if len(ein_clean) > 0 and len(ein_clean) <= 9:
        return ein_clean.zfill(9)
    return ein_clean if len(ein_clean) == 9 else None

df_5500_sch_a_joined["company_key_ein"] = df_5500_sch_a_joined["SPONS_DFE_EIN"].apply(normalize_ein)

print(f"✓ Created company_key_ein")
print(f"  Valid EINs: {df_5500_sch_a_joined['company_key_ein'].notna().sum():,}")
print(f"  Null EINs: {df_5500_sch_a_joined['company_key_ein'].isna().sum():,}")

# ============================================================================
# STEP 5: WRITE OUTPUTS FOR WAREHOUSE LOAD
# ============================================================================
print("\nWriting output files...")

# Output 1: Form 5500 filings (deduplicated by ACK_ID)
df_5500_clean = df_5500.drop_duplicates(subset=["ACK_ID"]).copy()
output_file_1 = OUTPUT_DIR / f"form5500_filings_{YEAR}_clean.csv"
df_5500_clean.to_csv(output_file_1, index=False, encoding="utf-8")
print(f"✓ Wrote {len(df_5500_clean):,} Form 5500 filings to: {output_file_1}")

# Output 2: Schedule A joined with main form
output_file_2 = OUTPUT_DIR / f"schedule_a_{YEAR}_joined.csv"
df_5500_sch_a_joined.to_csv(output_file_2, index=False, encoding="utf-8")
print(f"✓ Wrote {len(df_5500_sch_a_joined):,} Schedule A records to: {output_file_2}")

# ============================================================================
# SUMMARY STATISTICS
# ============================================================================
print("\n" + "=" * 80)
print("SUMMARY STATISTICS")
print("=" * 80)
print(f"\nForm 5500 Main Form ({YEAR}):")
print(f"  Total filings: {len(df_5500_clean):,}")
print(f"  Unique sponsors (EIN): {df_5500_clean['SPONS_DFE_EIN'].nunique():,}")
print(f"  Unique states: {df_5500_clean['SPONS_DFE_MAIL_US_STATE'].nunique():,}")

print(f"\nSchedule A Joined ({YEAR}):")
print(f"  Total records: {len(df_5500_sch_a_joined):,}")
print(f"  Unique filings (ACK_ID): {df_5500_sch_a_joined['ACK_ID'].nunique():,}")
print(f"  Unique carriers: {df_5500_sch_a_joined['INSURANCE_COMPANY_NAME'].nunique():,}")
print(f"  Valid company_key_ein: {df_5500_sch_a_joined['company_key_ein'].notna().sum():,}")

# ============================================================================
# NEXT STEPS / CUSTOMIZATION POINTS
# ============================================================================
print("\n" + "=" * 80)
print("NEXT STEPS FOR CUSTOMIZATION")
print("=" * 80)
print("""
1. FILTER MEDICAL VS OTHER WELFARE PLANS:
   - Use WELFARE_BENEFIT_CODE column to filter by plan type
   - Code 4A = Health (medical)
   - Code 4B = Dental
   - Code 4D = Life insurance
   - Code 4E = Disability
   - See: https://5500tax.com/5500tax-group-quick-reference-guide-to-welfare-plans/

   Example:
   df_medical = df_5500_sch_a_joined[
       df_5500_sch_a_joined['WELFARE_BENEFIT_CODE'].str.contains('4A', na=False)
   ]

2. JOIN TO YOUR EIN MASTER:
   - Use the 'company_key_ein' column created above
   - Example:

   df_enriched = df_5500_sch_a_joined.merge(
       your_ein_master,
       left_on='company_key_ein',
       right_on='ein',
       how='left'
   )

3. LOAD TO NEON POSTGRESQL:
   - Use SQLAlchemy or psycopg2
   - Example with pandas:

   from sqlalchemy import create_engine
   engine = create_engine(NEON_CONNECTION_STRING)
   df_5500_sch_a_joined.to_sql(
       'form_5500_schedule_a',
       engine,
       schema='marketing',
       if_exists='append',
       index=False
   )

4. CHANGE YEAR:
   - Update YEAR variable at top of script (line 22)
   - Ensure corresponding CSVs exist in data/ directory
""")

print("=" * 80)
print("✅ Script complete!")
print("=" * 80)
