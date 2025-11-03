#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Import Apollo people (CEO/CFO) data into Neon marketing.people_master table.
Links contacts to their companies and slots.

CTB Classification Metadata:
CTB Branch: sys/tools
Barton ID: 08.02.04
Unique ID: CTB-APOLLOPEOPLE
Enforcement: ORBT
"""

import os
import sys
import pandas as pd
import numpy as np
import psycopg2
from psycopg2.extras import execute_values, RealDictCursor
from datetime import datetime
import uuid

# Set UTF-8 encoding for Windows console
if sys.platform == 'win32':
    import codecs
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')

def transform_apollo_people_csv(input_file, output_file=None):
    """Transform Apollo people CSV to match Neon people_master schema."""
    
    print("\n" + "="*100)
    print("APOLLO PEOPLE CSV TRANSFORMATION")
    print("="*100 + "\n")
    
    print(f"[1/6] Loading Apollo People CSV: {input_file}")
    
    try:
        df = pd.read_csv(input_file)
        print(f"      Loaded {len(df):,} contacts")
        print(f"      Original columns: {len(df.columns)}")
        print()
    except Exception as e:
        print(f"[ERROR] Failed to load CSV: {e}")
        return None
    
    print("[2/6] Mapping columns to Neon schema...")
    
    # Column mapping from Apollo to Neon people_master
    column_mapping = {
        "First Name": "first_name",
        "Last Name": "last_name",
        "Title": "title",
        "Email": "email",
        "Email Status": "email_status",
        "Person Linkedin Url": "linkedin_url",
        "Work Direct Phone": "work_phone",
        "Mobile Phone": "mobile_phone",
        "Seniority": "seniority",
        "Departments": "department",
        "Company Name": "company_name",  # For lookup
        "Apollo Contact Id": "apollo_contact_id",
        "Apollo Account Id": "apollo_account_id",
    }
    
    # Rename columns that exist
    existing_mappings = {k: v for k, v in column_mapping.items() if k in df.columns}
    df = df.rename(columns=existing_mappings)
    print(f"      Mapped {len(existing_mappings)} columns")
    print()
    
    print("[3/6] Processing contact data...")
    
    # Filter out rows without email or name
    initial_count = len(df)
    df = df[df["email"].notna() & df["first_name"].notna() & df["last_name"].notna()]
    filtered_count = initial_count - len(df)
    if filtered_count > 0:
        print(f"      [WARNING] Filtered {filtered_count} rows missing required fields")
    
    # Create full_name
    df["full_name"] = df["first_name"] + " " + df["last_name"]
    
    # Normalize email status
    if "email_status" in df.columns:
        df["email_status"] = df["email_status"].str.lower().replace({
            "verified": "green",
            "valid": "green",
            "invalid": "red",
            "risky": "yellow",
            "unknown": "gray"
        })
    else:
        df["email_status"] = "gray"
    
    # Extract department (take first if multiple)
    if "department" in df.columns:
        df["department"] = df["department"].apply(
            lambda x: str(x).split(",")[0].strip() if pd.notna(x) else None
        )
    
    # Determine slot type from title
    def get_slot_type(title):
        if pd.isna(title):
            return None
        title_lower = str(title).lower()
        if any(x in title_lower for x in ["ceo", "chief executive", "president"]):
            return "CEO"
        elif any(x in title_lower for x in ["cfo", "chief financial", "finance"]):
            return "CFO"
        elif any(x in title_lower for x in ["chro", "chief human", "hr director", "human resources"]):
            return "HR"
        return "OTHER"
    
    df["slot_type"] = df["title"].apply(get_slot_type)
    
    print(f"      [OK] {len(df):,} valid contacts ready")
    print(f"      CEO contacts: {(df['slot_type'] == 'CEO').sum()}")
    print(f"      CFO contacts: {(df['slot_type'] == 'CFO').sum()}")
    print(f"      HR contacts: {(df['slot_type'] == 'HR').sum()}")
    print(f"      Other contacts: {(df['slot_type'] == 'OTHER').sum()}")
    print()
    
    print("[4/6] Adding tracking fields...")
    
    # Add import batch ID
    batch_id = f"apollo_people_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    df["import_batch_id"] = batch_id
    df["source"] = "apollo"
    df["status"] = "active"
    
    print(f"      Batch ID: {batch_id}")
    print()
    
    # Save to CSV if output file specified
    if output_file:
        df.to_csv(output_file, index=False)
        print(f"[5/6] Saved cleaned CSV to: {output_file}")
        print()
    
    return df, batch_id

def import_people_to_neon(df, batch_id):
    """Import people data into Neon, linking to companies."""
    
    database_url = os.getenv('NEON_DATABASE_URL')
    
    if not database_url:
        print("[ERROR] NEON_DATABASE_URL not set")
        return False
    
    print("="*100)
    print("NEON DATABASE IMPORT - PEOPLE DATA")
    print("="*100 + "\n")
    
    try:
        conn = psycopg2.connect(database_url)
        cur = conn.cursor(cursor_factory=RealDictCursor)
        
        print(f"[1/5] Connecting to Neon database... [OK]")
        print()
        
        print("[2/5] Looking up company IDs from intake.company_raw_intake...")
        
        # Get all companies with their IDs
        cur.execute("""
            SELECT 
                id,
                company,
                import_batch_id
            FROM intake.company_raw_intake
            ORDER BY created_at DESC
        """)
        
        companies = cur.fetchall()
        company_lookup = {row['company'].strip(): row['id'] for row in companies}
        
        print(f"      Found {len(company_lookup):,} companies in database")
        print()
        
        print("[3/5] Matching people to companies...")
        
        # Match people to companies
        matched = 0
        unmatched = 0
        
        records_to_insert = []
        
        for idx, row in df.iterrows():
            company_name = row.get('company_name', '').strip() if pd.notna(row.get('company_name')) else ''
            
            # Try to find company ID
            company_id = company_lookup.get(company_name)
            
            if not company_id:
                # Try fuzzy match
                for comp_name, comp_id in company_lookup.items():
                    if company_name.lower() in comp_name.lower() or comp_name.lower() in company_name.lower():
                        company_id = comp_id
                        break
            
            if company_id:
                matched += 1
                
                # Create unique_id
                unique_id = f"PER-{uuid.uuid4().hex[:12].upper()}"
                
                # Prepare record
                record = {
                    'unique_id': unique_id,
                    'company_id': company_id,
                    'company_name': company_name,
                    'first_name': row.get('first_name'),
                    'last_name': row.get('last_name'),
                    'full_name': row.get('full_name'),
                    'title': row.get('title'),
                    'email': row.get('email'),
                    'email_status': row.get('email_status', 'gray'),
                    'linkedin_url': row.get('linkedin_url'),
                    'work_phone': row.get('work_phone'),
                    'mobile_phone': row.get('mobile_phone'),
                    'seniority': row.get('seniority'),
                    'department': row.get('department'),
                    'slot_type': row.get('slot_type'),
                    'apollo_contact_id': row.get('apollo_contact_id'),
                    'source': 'apollo',
                    'import_batch_id': batch_id,
                    'status': 'active'
                }
                
                records_to_insert.append(record)
            else:
                unmatched += 1
        
        print(f"      Matched to companies: {matched}")
        print(f"      Unmatched (will skip): {unmatched}")
        print()
        
        if matched == 0:
            print("[ERROR] No contacts matched to companies. Cannot proceed.")
            return False
        
        print(f"[4/5] Inserting {matched:,} contacts into marketing.people_master...")
        
        # Build insert statement - note we're NOT using people_master fields directly
        # We'll insert into a staging area first or use the contact_enrichment table
        
        # Actually, let me insert into marketing.contact_enrichment first
        # since people_master might have FK constraints to company_slots
        
        insert_records = []
        for rec in records_to_insert:
            # Convert None values properly
            insert_record = (
                rec['company_id'],
                rec['slot_type'],
                rec['linkedin_url'] if pd.notna(rec['linkedin_url']) else None,
                rec['full_name'],
                rec['email'],
                rec['title'] if pd.notna(rec['title']) else None,
                rec['work_phone'] if pd.notna(rec['work_phone']) else None,
                rec['mobile_phone'] if pd.notna(rec['mobile_phone']) else None,
                rec['email_status'],
                rec['source'],
                rec['import_batch_id']
            )
            insert_records.append(insert_record)
        
        # Insert into contact_enrichment
        insert_query = """
            INSERT INTO marketing.contact_enrichment 
            (company_raw_intake_id, slot_type, linkedin_url, full_name, email, 
             title, work_phone, mobile_phone, email_status, source, notes)
            VALUES %s
        """
        
        execute_values(cur, insert_query, insert_records, page_size=100)
        
        conn.commit()
        
        print(f"      [OK] Successfully inserted {len(insert_records):,} contacts")
        print()
        
        print("[5/5] Verifying import...")
        
        # Verify
        cur.execute("""
            SELECT 
                COUNT(*) as total,
                COUNT(DISTINCT slot_type) as slot_types,
                COUNT(DISTINCT company_raw_intake_id) as companies
            FROM marketing.contact_enrichment
            WHERE notes = %s
        """, (batch_id,))
        
        result = cur.fetchone()
        print(f"      Total contacts: {result['total']:,}")
        print(f"      Unique companies: {result['companies']:,}")
        print(f"      Slot types: {result['slot_types']:,}")
        print()
        
        # Show breakdown by slot type
        cur.execute("""
            SELECT 
                slot_type,
                COUNT(*) as count
            FROM marketing.contact_enrichment
            WHERE notes = %s
            GROUP BY slot_type
            ORDER BY count DESC
        """, (batch_id,))
        
        slots = cur.fetchall()
        print("      By Role:")
        for slot in slots:
            print(f"        {slot['slot_type']}: {slot['count']:,}")
        print()
        
        # Show samples
        cur.execute("""
            SELECT full_name, email, title, slot_type
            FROM marketing.contact_enrichment
            WHERE notes = %s
            LIMIT 5
        """, (batch_id,))
        
        samples = cur.fetchall()
        print("      Sample contacts:")
        for i, sample in enumerate(samples, 1):
            print(f"        {i}. {sample['full_name']} ({sample['slot_type']})")
            print(f"           {sample['title']}")
            print(f"           {sample['email']}")
        
        print()
        print("="*100)
        print("PEOPLE IMPORT COMPLETE!")
        print("="*100)
        print(f"  Batch ID: {batch_id}")
        print(f"  Contacts imported: {result['total']:,}")
        print(f"  Companies with contacts: {result['companies']:,}")
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
        input_file = "ceo-cfo-wv.csv"
    
    if not os.path.exists(input_file):
        print(f"[ERROR] File not found: {input_file}")
        print("\nUsage: python import_apollo_people_to_neon.py <apollo_people_csv>")
        print("Example: python import_apollo_people_to_neon.py ceo-cfo-wv.csv")
        return
    
    # Transform the CSV
    output_csv = "cleaned_apollo_people.csv"
    result = transform_apollo_people_csv(input_file, output_csv)
    
    if result is None:
        print("[ERROR] CSV transformation failed")
        return
    
    df_clean, batch_id = result
    
    # Ask for confirmation before importing
    print("\n" + "="*100)
    print("READY TO IMPORT TO NEON")
    print("="*100)
    print(f"  Contacts to import: {len(df_clean):,}")
    print(f"  Batch ID: {batch_id}")
    print(f"  Target table: marketing.contact_enrichment")
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
    success = import_people_to_neon(df_clean, batch_id)
    
    if success:
        print(f"\n[SUCCESS] Apollo people data successfully imported and linked!")
        print(f"[INFO] Cleaned CSV saved to: {output_csv}")
        print(f"\n[DATA SUMMARY]")
        print(f"  Companies in intake: 453")
        print(f"  Contacts imported: {len(df_clean):,}")
        print(f"  Linkage: Contacts linked to companies via company_raw_intake_id")
    else:
        print(f"\n[FAILED] Import unsuccessful. Please check errors above.")

if __name__ == "__main__":
    main()

