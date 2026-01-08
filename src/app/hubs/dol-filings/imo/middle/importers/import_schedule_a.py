#!/usr/bin/env python3
"""
Schedule A CSV Import Preparation

Reads F_SCH_A_2023_latest.csv (90 columns) and extracts key fields
for import to marketing.schedule_a_staging table.

Key columns extracted:
- ACK_ID (column 1) - Join key to form_5500/form_5500_sf
- Plan year dates (columns 3-4)
- Insurance carrier info (columns 7-10)
- Policy dates (columns 12-13) - For renewal analysis
- Covered lives (column 11)

Input:  data/F_SCH_A_2023_latest.csv (~336K records, 90 columns)
Output: output/schedule_a_2023_staging.csv (~336K records, 13 columns)
"""

import csv
import sys
from pathlib import Path

# Paths
input_file = Path('data/F_SCH_A_2023_latest.csv')
output_file = Path('output/schedule_a_2023_staging.csv')

# Column mapping based on F_SCH_A file layout
COLUMN_MAP = {
    'ACK_ID': 0,                          # Column 1
    'FORM_PLAN_YEAR_BEGIN_DATE': 1,      # Column 2
    'SCH_A_PLAN_YEAR_BEGIN_DATE': 2,     # Column 3
    'SCH_A_PLAN_YEAR_END_DATE': 3,       # Column 4
    'FORM_TAX_PRD': 4,                   # Column 5
    'TYPE_OF_PLAN_ENTITY_CD': 5,         # Column 6
    'INSURANCE_COMPANY_NAME': 6,          # Column 7
    'INSURANCE_COMPANY_EIN': 7,           # Column 8
    'INSURANCE_COMPANY_PHONE_NUM': 8,     # Column 9
    'CONTRACT_NUMBER': 9,                 # Column 10
    'COVERED_LIVES': 10,                  # Column 11 (INS_PRSN_COVERED_EOY_CNT)
    'POLICY_YEAR_BEGIN_DATE': 11,         # Column 12
    'POLICY_YEAR_END_DATE': 12,           # Column 13
}

def clean_value(value):
    """Clean CSV value - strip whitespace, convert empty to None"""
    if value is None:
        return ''
    value = value.strip()
    return value if value else ''

def extract_key_columns(input_path, output_path):
    """Extract key columns from Schedule A CSV"""

    print(f"Reading: {input_path}")
    print(f"Writing: {output_path}")
    print()

    records_processed = 0
    records_written = 0

    with open(input_path, 'r', encoding='utf-8', errors='replace') as infile, \
         open(output_path, 'w', encoding='utf-8', newline='') as outfile:

        reader = csv.reader(infile)
        writer = csv.writer(outfile, quoting=csv.QUOTE_MINIMAL)

        # Read header row
        header = next(reader)
        print(f"[OK] Input CSV has {len(header)} columns")

        # Write output header
        output_header = [
            'ack_id',
            'form_plan_year_begin_date',
            'sch_a_plan_year_begin_date',
            'sch_a_plan_year_end_date',
            'form_tax_prd',
            'type_of_plan_entity_cd',
            'insurance_company_name',
            'insurance_company_ein',
            'insurance_company_phone_num',
            'contract_number',
            'covered_lives',
            'policy_year_begin_date',
            'policy_year_end_date'
        ]
        writer.writerow(output_header)

        # Process data rows
        for row_num, row in enumerate(reader, start=2):
            records_processed += 1

            # Progress indicator
            if records_processed % 50000 == 0:
                print(f"  Processed {records_processed:,} records...")

            # Handle rows with fewer columns than expected (data quality issue)
            while len(row) < len(header):
                row.append('')

            # Extract key columns
            try:
                output_row = [
                    clean_value(row[COLUMN_MAP['ACK_ID']]),
                    clean_value(row[COLUMN_MAP['FORM_PLAN_YEAR_BEGIN_DATE']]),
                    clean_value(row[COLUMN_MAP['SCH_A_PLAN_YEAR_BEGIN_DATE']]),
                    clean_value(row[COLUMN_MAP['SCH_A_PLAN_YEAR_END_DATE']]),
                    clean_value(row[COLUMN_MAP['FORM_TAX_PRD']]),
                    clean_value(row[COLUMN_MAP['TYPE_OF_PLAN_ENTITY_CD']]),
                    clean_value(row[COLUMN_MAP['INSURANCE_COMPANY_NAME']]),
                    clean_value(row[COLUMN_MAP['INSURANCE_COMPANY_EIN']]),
                    clean_value(row[COLUMN_MAP['INSURANCE_COMPANY_PHONE_NUM']]),
                    clean_value(row[COLUMN_MAP['CONTRACT_NUMBER']]),
                    clean_value(row[COLUMN_MAP['COVERED_LIVES']]),
                    clean_value(row[COLUMN_MAP['POLICY_YEAR_BEGIN_DATE']]),
                    clean_value(row[COLUMN_MAP['POLICY_YEAR_END_DATE']]),
                ]

                writer.writerow(output_row)
                records_written += 1

            except IndexError as e:
                print(f"⚠ Warning: Row {row_num} has {len(row)} columns, skipping")
                continue

    print()
    print("=" * 80)
    print("SCHEDULE A CSV PREPARATION COMPLETE")
    print("=" * 80)
    print(f"[OK] Records processed: {records_processed:,}")
    print(f"[OK] Records written:   {records_written:,}")
    print(f"[OK] Output file:       {output_path}")
    print(f"[OK] File size:         {output_path.stat().st_size / 1024 / 1024:.1f} MB")
    print()
    print("Next steps:")
    print("1. Create table: node ctb/sys/enrichment/create_schedule_a_table.js")
    print("2. Import CSV:")
    print(f"   \\COPY marketing.schedule_a_staging FROM '{output_path.absolute()}' CSV HEADER;")
    print("3. Process staging: CALL marketing.process_schedule_a_staging();")
    print("4. Verify: SELECT COUNT(*) FROM marketing.schedule_a;")

if __name__ == '__main__':
    if not input_file.exists():
        print(f"ERROR: Input file not found: {input_file}")
        print()
        print("Please download F_SCH_A_2023_latest.csv from DOL:")
        print("https://www.dol.gov/agencies/ebsa/researchers/data/retirement-bulletin")
        print()
        print("And place it in the data/ directory")
        sys.exit(1)

    # Ensure output directory exists
    output_file.parent.mkdir(exist_ok=True)

    extract_key_columns(input_file, output_file)
