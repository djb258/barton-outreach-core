#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Import Apollo company data into Neon intake.company_raw_intake table.
Handles CSV transformation, validation, and bulk insert.

CTB Classification Metadata:
CTB Branch: sys/tools
Barton ID: 08.02.03
Unique ID: CTB-APOLLOIMPORT
Enforcement: ORBT
"""

import os
import sys
import pandas as pd
import numpy as np
import psycopg2
from psycopg2.extras import execute_values
from datetime import datetime

# Set UTF-8 encoding for Windows console
if sys.platform == 'win32':
    import codecs
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')

def transform_apollo_csv(input_file, output_file=None):
    """Transform Apollo CSV to match Neon schema."""
    
    print("\n" + "="*100)
    print("APOLLO CSV TRANSFORMATION")
    print("="*100 + "\n")
    
    print(f"[1/5] Loading Apollo CSV: {input_file}")
    
    try:
        df = pd.read_csv(input_file)
        print(f"      Loaded {len(df):,} companies")
        print(f"      Original columns: {len(df.columns)}")
        print()
    except Exception as e:
        print(f"[ERROR] Failed to load CSV: {e}")
        return None
    
    print("[2/5] Mapping columns to Neon schema...")
    
    # Column mapping from Apollo to Neon
    column_mapping = {
        "Company Name": "company",
        "Company Name for Emails": "company_name_for_emails",
        "Website": "website",
        "# Employees": "num_employees",
        "Industry": "industry",
        "Company Street": "company_street",
        "Company City": "company_city",
        "Company State": "company_state",
        "Company Postal Code": "company_postal_code",
        "Company Address": "company_address",
        "Company Phone": "company_phone",
        "Company Linkedin Url": "company_linkedin_url",
        "Facebook Url": "facebook_url",
        "Twitter Url": "twitter_url",
        "SIC Codes": "sic_codes",
        "Founded Year": "founded_year",
        "Company Country": "company_country",
    }
    
    # Rename columns that exist
    existing_mappings = {k: v for k, v in column_mapping.items() if k in df.columns}
    df = df.rename(columns=existing_mappings)
    print(f"      Mapped {len(existing_mappings)} columns")
    print()
    
    print("[3/5] Adding required fields...")
    
    # Add fields that don't exist in Apollo export
    if "founded_year" not in df.columns:
        df["founded_year"] = None
    
    if "state_abbrev" not in df.columns:
        # Try to extract state abbreviation from company_state
        if "company_state" in df.columns:
            df["state_abbrev"] = df["company_state"].apply(
                lambda x: x.strip()[:2].upper() if pd.notna(x) and len(str(x).strip()) <= 2 else None
            )
        else:
            df["state_abbrev"] = None
    
    if "company_country" not in df.columns:
        df["company_country"] = "United States"
    
    if "sic_codes" not in df.columns:
        df["sic_codes"] = None
    
    # Add import tracking fields
    batch_id = f"apollo_upload_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    df["import_batch_id"] = batch_id
    df["validated"] = False
    df["validation_notes"] = None
    df["validated_at"] = None
    df["validated_by"] = None
    
    print(f"      Batch ID: {batch_id}")
    print()
    
    print("[4/5] Data validation...")
    
    # Validate required fields
    if "company" not in df.columns:
        print("[ERROR] Required 'company' column not found")
        return None
    
    # Count missing company names
    missing_company = df["company"].isna().sum()
    if missing_company > 0:
        print(f"      [WARNING] {missing_company} rows missing company name - will be filtered")
        df = df[df["company"].notna()]
    
    # Clean numeric fields with range validation
    if "num_employees" in df.columns:
        df["num_employees"] = pd.to_numeric(df["num_employees"], errors='coerce')
        # Cap at PostgreSQL integer max (2147483647)
        df["num_employees"] = df["num_employees"].apply(
            lambda x: int(x) if pd.notna(x) and -2147483648 <= x <= 2147483647 else None
        )
    
    if "founded_year" in df.columns:
        df["founded_year"] = pd.to_numeric(df["founded_year"], errors='coerce')
        # Validate year range
        df["founded_year"] = df["founded_year"].apply(
            lambda x: int(x) if pd.notna(x) and 1800 <= x <= 2100 else None
        )
    
    print(f"      [OK] {len(df):,} valid companies ready for import")
    print()
    
    # Select only the columns that match the Neon schema (excluding 'id' and 'created_at')
    neon_columns = [
        "company", "company_name_for_emails", "num_employees", "industry", 
        "website", "company_linkedin_url", "facebook_url", "twitter_url",
        "company_street", "company_city", "company_state", "company_country",
        "company_postal_code", "company_address", "company_phone",
        "sic_codes", "founded_year", "state_abbrev", "import_batch_id",
        "validated", "validation_notes", "validated_at", "validated_by"
    ]
    
    # Keep only columns that exist and are in the schema
    df_clean = df[[col for col in neon_columns if col in df.columns]]
    
    # Add missing columns with None values
    for col in neon_columns:
        if col not in df_clean.columns:
            df_clean[col] = None
    
    # Reorder columns to match schema
    df_clean = df_clean[neon_columns]
    
    print("[5/5] Preparing data for database insert...")
    print(f"      Final columns: {len(df_clean.columns)}")
    print(f"      Final rows: {len(df_clean):,}")
    
    # Save to CSV if output file specified
    if output_file:
        df_clean.to_csv(output_file, index=False)
        print(f"      Saved to: {output_file}")
    
    print()
    return df_clean, batch_id

def import_to_neon(df, batch_id):
    """Import transformed data into Neon database."""
    
    database_url = os.getenv('NEON_DATABASE_URL')
    
    if not database_url:
        print("[ERROR] NEON_DATABASE_URL not set")
        return False
    
    print("="*100)
    print("NEON DATABASE IMPORT")
    print("="*100 + "\n")
    
    try:
        conn = psycopg2.connect(database_url)
        cur = conn.cursor()
        
        print(f"[1/3] Connecting to Neon database... [OK]")
        
        # Convert DataFrame to list of tuples
        columns = df.columns.tolist()
        values = [tuple(x) for x in df.to_numpy()]
        
        print(f"[2/3] Inserting {len(values):,} companies...")
        
        # Convert data types for PostgreSQL compatibility
        # Replace NaN with None, convert booleans properly
        clean_values = []
        for row in values:
            clean_row = []
            for val in row:
                if pd.isna(val):
                    clean_row.append(None)
                elif isinstance(val, (bool, np.bool_)):
                    clean_row.append(val)
                elif isinstance(val, (float, np.floating)):
                    # Check if it's a whole number
                    if val == val:  # not NaN
                        clean_row.append(int(val) if val.is_integer() else val)
                    else:
                        clean_row.append(None)
                else:
                    clean_row.append(val)
            clean_values.append(tuple(clean_row))
        
        # Build INSERT statement
        column_names = ", ".join(columns)
        placeholders = ", ".join(["%s"] * len(columns))
        
        insert_query = f"""
            INSERT INTO intake.company_raw_intake ({column_names})
            VALUES %s
        """
        
        # Use execute_values for efficient bulk insert
        execute_values(cur, insert_query, clean_values, page_size=100)
        
        conn.commit()
        
        print(f"      [OK] Successfully inserted {len(values):,} companies")
        print()
        
        print("[3/3] Verifying import...")
        
        # Verify the import
        cur.execute("""
            SELECT 
                COUNT(*) as total,
                COUNT(DISTINCT import_batch_id) as batches
            FROM intake.company_raw_intake
            WHERE import_batch_id = %s
        """, (batch_id,))
        
        result = cur.fetchone()
        print(f"      Total companies in batch '{batch_id}': {result[0]:,}")
        print()
        
        # Show sample records
        cur.execute("""
            SELECT company, website, company_city, company_state
            FROM intake.company_raw_intake
            WHERE import_batch_id = %s
            LIMIT 5
        """, (batch_id,))
        
        samples = cur.fetchall()
        print("      Sample records:")
        for i, sample in enumerate(samples, 1):
            print(f"        {i}. {sample[0]}")
            print(f"           {sample[1] or 'No website'} | {sample[2] or 'No city'}, {sample[3] or 'No state'}")
        
        print()
        print("="*100)
        print("IMPORT COMPLETE!")
        print("="*100)
        print(f"  Batch ID: {batch_id}")
        print(f"  Companies imported: {result[0]:,}")
        print(f"  Status: SUCCESS")
        print("="*100 + "\n")
        
        cur.close()
        conn.close()
        
        return True
        
    except Exception as e:
        print(f"[ERROR] Database import failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Main execution."""
    
    # Get input file from command line or use default
    if len(sys.argv) > 1:
        input_file = sys.argv[1]
    else:
        input_file = "apollo-accounts-export.csv"
    
    if not os.path.exists(input_file):
        print(f"[ERROR] File not found: {input_file}")
        print("\nUsage: python import_apollo_to_neon.py <apollo_csv_file>")
        print("Example: python import_apollo_to_neon.py apollo-accounts-export.csv")
        return
    
    # Transform the CSV
    output_csv = "cleaned_apollo_company_raw_intake.csv"
    result = transform_apollo_csv(input_file, output_csv)
    
    if result is None:
        print("[ERROR] CSV transformation failed")
        return
    
    df_clean, batch_id = result
    
    # Ask for confirmation before importing
    print("\n" + "="*100)
    print("READY TO IMPORT TO NEON")
    print("="*100)
    print(f"  Companies to import: {len(df_clean):,}")
    print(f"  Batch ID: {batch_id}")
    print(f"  Target table: intake.company_raw_intake")
    print("\nType 'YES' to proceed with database import, or anything else to cancel: ", end='')
    
    # Check for auto-confirm
    if os.getenv('AUTO_CONFIRM') == 'YES':
        confirmation = 'YES'
        print("YES (auto-confirmed)")
    else:
        confirmation = input().strip()
    
    if confirmation != 'YES':
        print(f"\n[CANCELLED] Data saved to {output_csv} but not imported to database.")
        return
    
    # Import to Neon
    success = import_to_neon(df_clean, batch_id)
    
    if success:
        print(f"\n[SUCCESS] Apollo data successfully imported!")
        print(f"[INFO] Cleaned CSV saved to: {output_csv}")
        print(f"\n[NEXT STEPS]")
        print(f"  1. Promote companies to marketing.company_master")
        print(f"  2. Generate company_slots (CEO/CFO/HR)")
        print(f"  3. Begin enrichment pipeline")
    else:
        print(f"\n[FAILED] Import unsuccessful. Please check errors above.")

if __name__ == "__main__":
    main()

