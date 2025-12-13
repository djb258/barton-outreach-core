#!/usr/bin/env python3
"""
Extract Schedule A Renewal Dates from DOL Form 5500 FOIA Dataset

Based on 2023 F_SCH_A data dictionary and Schedule A instructions.
Extracts policy year dates to derive renewal timing for insurance contracts.

Input: data/F_SCH_A_2023_Latest.csv
Output: output/schedule_a_2023_with_renewals.csv
"""

import pandas as pd
from pathlib import Path
from datetime import datetime

# ============================================================================
# CONFIGURATION
# ============================================================================
YEAR = "2023"
DATA_DIR = Path("data")
OUTPUT_DIR = Path("output")

# Ensure output directory exists
OUTPUT_DIR.mkdir(exist_ok=True)

# ============================================================================
# STEP 1: LOAD SCHEDULE A CSV
# ============================================================================
print(f"Loading Schedule A for {YEAR}...")
df = pd.read_csv(
    DATA_DIR / f"F_SCH_A_{YEAR}_Latest.csv",
    dtype=str,  # Keep all as strings initially
    low_memory=False,
    encoding='utf-8'
)

# Strip whitespace from all string columns
print("Stripping whitespace...")
df = df.apply(lambda x: x.str.strip() if x.dtype == "object" else x)

print(f"Loaded {len(df):,} Schedule A records")

# ============================================================================
# STEP 2: COLUMN MAPPING (2023 Data Dictionary)
# ============================================================================
print("\nMapping Schedule A columns...")

# Based on 2023 Schedule A layout from DOL Form 5500 Datasets Guide
# Reference: https://www.dol.gov/sites/dolgov/files/ebsa/pdf_files/form-5500-datasets-guide.pdf

column_mapping = {
    # Primary key
    "ACK_ID": "ack_id",

    # Insurance carrier information
    "INSURANCE_COMPANY_NAME": "insurance_carrier_name",
    "INSURANCE_COMPANY_EIN_PN": "insurance_carrier_ein",  # May be INSURANCE_COMPANY_EIN

    # Policy/Contract information
    "CONTRACT_NUMBER": "policy_number",  # May also be POLICY_NUMBER

    # Policy year dates (key fields for renewal timing)
    # These column names vary by year - check 2023 data dictionary
    "POLICY_YEAR_FROM_DATE": "policy_year_begin_date",
    "POLICY_YEAR_TO_DATE": "policy_year_end_date",
}

# Alternative column names to check (varies by year)
alternative_mappings = {
    # Carrier name variations
    "INSURANCE_CARRIER_NAME": "insurance_carrier_name",
    "INS_COMPANY_NAME": "insurance_carrier_name",

    # Carrier EIN variations
    "INSURANCE_COMPANY_EIN": "insurance_carrier_ein",
    "INS_COMPANY_EIN": "insurance_carrier_ein",

    # Policy number variations
    "POLICY_NUMBER": "policy_number",
    "CONTRACT_NUM": "policy_number",

    # Policy year date variations
    "POLICY_YR_FROM_DT": "policy_year_begin_date",
    "POLICY_YR_TO_DT": "policy_year_end_date",
    "POL_YR_BEGIN_DATE": "policy_year_begin_date",
    "POL_YR_END_DATE": "policy_year_end_date",
}

# Merge mappings
all_mappings = {**column_mapping, **alternative_mappings}

# Find which columns actually exist in the dataframe
print("\nDetecting column names from CSV...")
available_mappings = {}
for source_col, target_col in all_mappings.items():
    if source_col in df.columns:
        available_mappings[source_col] = target_col
        print(f"  ✓ Found: {source_col} → {target_col}")

# Check for required columns
required_targets = ["ack_id", "policy_year_begin_date", "policy_year_end_date"]
mapped_targets = set(available_mappings.values())

missing_required = [col for col in required_targets if col not in mapped_targets]
if missing_required:
    print(f"\n⚠ Warning: Missing required columns: {missing_required}")
    print("Available columns in CSV:")
    print(df.columns.tolist()[:20])  # Show first 20 columns
    raise ValueError(f"Required columns not found: {missing_required}")

# Rename columns
df_clean = df.rename(columns=available_mappings)

print(f"\n✓ Mapped {len(available_mappings)} columns successfully")

# ============================================================================
# STEP 3: SELECT AND NORMALIZE CORE COLUMNS
# ============================================================================
print("\nSelecting core Schedule A columns...")

# Core columns to keep
core_columns = [
    "ack_id",
    "insurance_carrier_name",
    "insurance_carrier_ein",
    "policy_number",
    "policy_year_begin_date",
    "policy_year_end_date",
]

# Add missing columns as empty strings
for col in core_columns:
    if col not in df_clean.columns:
        df_clean[col] = ""

df_sched_a = df_clean[core_columns].copy()

print(f"  Selected {len(core_columns)} core columns")
print(f"  Rows: {len(df_sched_a):,}")

# ============================================================================
# STEP 4: PARSE DATES AND CREATE DERIVED FIELDS
# ============================================================================
print("\nParsing policy year dates...")

def parse_flexible_date(date_str):
    """
    Parse date from various DOL formats:
    - YYYY-MM-DD
    - MM/DD/YYYY
    - YYYYMMDD
    Returns pd.Timestamp or pd.NaT
    """
    if pd.isna(date_str) or date_str == "" or str(date_str).strip() == "":
        return pd.NaT

    date_str = str(date_str).strip()

    # Try multiple formats
    formats = [
        "%Y-%m-%d",      # 2023-01-01
        "%m/%d/%Y",      # 01/01/2023
        "%Y%m%d",        # 20230101
        "%m-%d-%Y",      # 01-01-2023
        "%d-%m-%Y",      # 01-01-2023 (European)
    ]

    for fmt in formats:
        try:
            return pd.to_datetime(date_str, format=fmt)
        except (ValueError, TypeError):
            continue

    # If all fail, try pandas auto-parse
    try:
        return pd.to_datetime(date_str)
    except:
        return pd.NaT

# Parse begin date
print("  Parsing policy_year_begin_date...")
df_sched_a["policy_year_begin_date"] = df_sched_a["policy_year_begin_date"].apply(parse_flexible_date)
valid_begin = df_sched_a["policy_year_begin_date"].notna().sum()
print(f"    ✓ Parsed {valid_begin:,} valid begin dates ({100*valid_begin/len(df_sched_a):.1f}%)")

# Parse end date
print("  Parsing policy_year_end_date...")
df_sched_a["policy_year_end_date"] = df_sched_a["policy_year_end_date"].apply(parse_flexible_date)
valid_end = df_sched_a["policy_year_end_date"].notna().sum()
print(f"    ✓ Parsed {valid_end:,} valid end dates ({100*valid_end/len(df_sched_a):.1f}%)")

# Create derived fields: renewal_month and renewal_year
print("\nCreating renewal timing fields...")

df_sched_a["renewal_month"] = df_sched_a["policy_year_end_date"].apply(
    lambda x: x.month if pd.notna(x) else None
)

df_sched_a["renewal_year"] = df_sched_a["policy_year_end_date"].apply(
    lambda x: x.year if pd.notna(x) else None
)

valid_renewal = df_sched_a["renewal_month"].notna().sum()
print(f"  ✓ Created renewal_month: {valid_renewal:,} valid values")
print(f"  ✓ Created renewal_year: {valid_renewal:,} valid values")

# ============================================================================
# STEP 5: OUTPUT CLEANED SCHEDULE A WITH RENEWALS
# ============================================================================
output_file = OUTPUT_DIR / f"schedule_a_{YEAR}_with_renewals.csv"

print(f"\nWriting output: {output_file}")
df_sched_a.to_csv(output_file, index=False, encoding="utf-8")

print(f"✓ Wrote {len(df_sched_a):,} records")

# ============================================================================
# SUMMARY STATISTICS
# ============================================================================
print("\n" + "=" * 80)
print("SUMMARY STATISTICS")
print("=" * 80)

print(f"\nSchedule A Records ({YEAR}):")
print(f"  Total records: {len(df_sched_a):,}")
print(f"  Unique ACK_IDs: {df_sched_a['ack_id'].nunique():,}")
print(f"  Unique carriers: {df_sched_a['insurance_carrier_name'].nunique():,}")

print(f"\nDate Parsing Results:")
print(f"  Valid begin dates: {df_sched_a['policy_year_begin_date'].notna().sum():,} ({100*df_sched_a['policy_year_begin_date'].notna().sum()/len(df_sched_a):.1f}%)")
print(f"  Valid end dates: {df_sched_a['policy_year_end_date'].notna().sum():,} ({100*df_sched_a['policy_year_end_date'].notna().sum()/len(df_sched_a):.1f}%)")
print(f"  Valid renewal months: {df_sched_a['renewal_month'].notna().sum():,} ({100*df_sched_a['renewal_month'].notna().sum()/len(df_sched_a):.1f}%)")

# Renewal month distribution
print(f"\nRenewal Month Distribution:")
month_dist = df_sched_a['renewal_month'].value_counts().sort_index()
month_names = ["", "Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
for month in range(1, 13):
    count = month_dist.get(month, 0)
    if count > 0:
        pct = 100 * count / df_sched_a['renewal_month'].notna().sum()
        print(f"  {month_names[month]:>3}: {count:>8,} ({pct:>5.1f}%)")

# Renewal year distribution
print(f"\nRenewal Year Distribution:")
year_dist = df_sched_a['renewal_year'].value_counts().sort_index()
for year in sorted(year_dist.index)[:10]:  # Show top 10 years
    count = year_dist[year]
    pct = 100 * count / df_sched_a['renewal_year'].notna().sum()
    print(f"  {int(year)}: {count:>8,} ({pct:>5.1f}%)")

# Missing data summary
print(f"\nMissing Data Summary:")
print(f"  Missing begin dates: {df_sched_a['policy_year_begin_date'].isna().sum():,}")
print(f"  Missing end dates: {df_sched_a['policy_year_end_date'].isna().sum():,}")
print(f"  Missing renewal month: {df_sched_a['renewal_month'].isna().sum():,}")
print(f"  Missing carrier name: {(df_sched_a['insurance_carrier_name'] == '').sum():,}")
print(f"  Missing policy number: {(df_sched_a['policy_number'] == '').sum():,}")

# ============================================================================
# NEXT STEPS
# ============================================================================
print("\n" + "=" * 80)
print("NEXT STEPS")
print("=" * 80)
print(f"""
1. LOAD TO DATABASE (if desired):
   - Create schedule_a table with renewal columns
   - Load {output_file.name} via COPY or bulk insert

2. JOIN TO MAIN FORM 5500:
   SELECT
       f.sponsor_dfe_ein,
       f.sponsor_dfe_name,
       sa.insurance_carrier_name,
       sa.policy_number,
       sa.renewal_month,
       sa.renewal_year
   FROM form_5500 f
   JOIN schedule_a sa ON sa.ack_id = f.ack_id
   WHERE sa.renewal_month IS NOT NULL;

3. RENEWAL TIMING ANALYSIS:
   -- Companies with renewals in specific months
   SELECT renewal_month, COUNT(DISTINCT ack_id) as plan_count
   FROM schedule_a
   WHERE renewal_month IS NOT NULL
   GROUP BY renewal_month
   ORDER BY renewal_month;

4. INSURANCE CARRIER ANALYSIS:
   -- Market share by carrier
   SELECT
       insurance_carrier_name,
       COUNT(*) as contract_count,
       COUNT(DISTINCT ack_id) as plan_count
   FROM schedule_a
   WHERE insurance_carrier_name != ''
   GROUP BY insurance_carrier_name
   ORDER BY contract_count DESC
   LIMIT 20;

5. OUTREACH TIMING:
   -- Companies with renewals in next 3 months
   -- (Run this query with current date)
   SELECT DISTINCT ack_id
   FROM schedule_a
   WHERE renewal_month IN (
       EXTRACT(MONTH FROM CURRENT_DATE),
       EXTRACT(MONTH FROM CURRENT_DATE + INTERVAL '1 month'),
       EXTRACT(MONTH FROM CURRENT_DATE + INTERVAL '2 months')
   )
   AND renewal_year = EXTRACT(YEAR FROM CURRENT_DATE);
""")

print("=" * 80)
print("✅ Script complete!")
print("=" * 80)
print(f"\nOutput file: {output_file}")
print(f"Records: {len(df_sched_a):,}")
print(f"With renewal dates: {df_sched_a['renewal_month'].notna().sum():,}")
