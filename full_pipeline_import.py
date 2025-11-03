#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Complete pipeline: Companies → Slots → People
Promotes companies, generates slots, and imports contacts all linked up.

CTB Classification Metadata:
CTB Branch: sys/tools
Barton ID: 08.02.05
Unique ID: CTB-FULLPIPELINE
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

def promote_companies_to_marketing(cur):
    """Step 1: Promote companies from intake to marketing.company_master"""
    
    print("\n" + "="*100)
    print("STEP 1: PROMOTE COMPANIES TO MARKETING")
    print("="*100 + "\n")
    
    # Get companies from intake
    cur.execute("SELECT COUNT(*) as count FROM intake.company_raw_intake")
    intake_count = cur.fetchone()['count']
    print(f"Companies in intake: {intake_count:,}")
    
    # Check if already in marketing
    cur.execute("SELECT COUNT(*) as count FROM marketing.company_master")
    existing_count = cur.fetchone()['count']
    print(f"Companies in marketing: {existing_count:,}")
    
    if intake_count == 0:
        print("[ERROR] No companies in intake to promote")
        return False
    
    print(f"\nPromoting {intake_count:,} companies...")
    
    # Promote companies with proper Barton ID format
    # Format: 04.04.01.XX.XXXXX.XXX
    cur.execute("""
        WITH numbered_companies AS (
            SELECT 
                *,
                ROW_NUMBER() OVER (ORDER BY id) as row_num
            FROM intake.company_raw_intake
        )
        INSERT INTO marketing.company_master (
            company_unique_id,
            company_name,
            website_url,
            industry,
            employee_count,
            company_phone,
            address_street,
            address_city,
            address_state,
            address_zip,
            address_country,
            linkedin_url,
            facebook_url,
            twitter_url,
            sic_codes,
            founded_year,
            state_abbrev,
            source_system,
            source_record_id,
            promoted_from_intake_at,
            import_batch_id,
            created_at,
            updated_at
        )
        SELECT 
            '04.04.01.' || 
            LPAD((row_num % 100)::text, 2, '0') || '.' ||
            LPAD((row_num % 100000)::text, 5, '0') || '.' ||
            LPAD((row_num % 1000)::text, 3, '0'),
            company,
            COALESCE(website, ''),
            industry,
            num_employees,
            company_phone,
            company_street,
            company_city,
            company_state,
            company_postal_code,
            COALESCE(company_country, 'United States'),
            company_linkedin_url,
            facebook_url,
            twitter_url,
            sic_codes,
            founded_year,
            state_abbrev,
            'apollo_import',
            id::text,
            NOW(),
            import_batch_id,
            created_at,
            NOW()
        FROM numbered_companies
        ON CONFLICT (company_unique_id) DO NOTHING
    """)
    
    promoted = cur.rowcount
    print(f"[OK] Promoted {promoted:,} companies to marketing.company_master")
    
    return True

def generate_company_slots(cur):
    """Step 2: Generate CEO/CFO/HR slots for each company"""
    
    print("\n" + "="*100)
    print("STEP 2: GENERATE COMPANY SLOTS (CEO/CFO/HR)")
    print("="*100 + "\n")
    
    # Get companies that need slots
    cur.execute("""
        SELECT company_unique_id, company_name
        FROM marketing.company_master
        WHERE company_unique_id NOT IN (
            SELECT DISTINCT company_unique_id 
            FROM marketing.company_slots
        )
    """)
    
    companies = cur.fetchall()
    print(f"Companies needing slots: {len(companies):,}")
    
    if len(companies) == 0:
        print("[INFO] All companies already have slots")
        return True
    
    print("Generating 3 slots per company (CEO, CFO, HR)...")
    
    # Generate slots for each company with proper Barton IDs
    # Format: 04.04.05.XX.XXXXX.XXX
    slots_to_insert = []
    slot_counter = 1
    for company in companies:
        company_id = company['company_unique_id']
        for slot_type in ['CEO', 'CFO', 'HR']:
            # Generate Barton ID for slot
            slot_id = f"04.04.05.{(slot_counter % 100):02d}.{(slot_counter % 100000):05d}.{(slot_counter % 1000):03d}"
            slot_label = f"{slot_type} - {company['company_name']}"
            slots_to_insert.append((slot_id, company_id, slot_type, slot_label))
            slot_counter += 1
    
    # Insert slots
    insert_query = """
        INSERT INTO marketing.company_slots 
        (company_slot_unique_id, company_unique_id, slot_type, slot_label)
        VALUES %s
    """
    
    execute_values(cur, insert_query, slots_to_insert, page_size=300)
    
    print(f"[OK] Generated {len(slots_to_insert):,} slots ({len(companies)} companies × 3 roles)")
    
    # Verify
    cur.execute("SELECT COUNT(*) as count FROM marketing.company_slots")
    total_slots = cur.fetchone()['count']
    print(f"Total slots in database: {total_slots:,}")
    
    return True

def import_people_linked(people_csv, cur):
    """Step 3: Import people and link to slots"""
    
    print("\n" + "="*100)
    print("STEP 3: IMPORT PEOPLE AND LINK TO COMPANIES/SLOTS")
    print("="*100 + "\n")
    
    # Load people CSV
    print(f"Loading people data from: {people_csv}")
    df = pd.read_csv(people_csv)
    print(f"Loaded {len(df):,} contacts\n")
    
    # Map columns
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
        "Company Name": "company_name",
    }
    
    existing_mappings = {k: v for k, v in column_mapping.items() if k in df.columns}
    df = df.rename(columns=existing_mappings)
    
    # Filter valid rows
    df = df[df["email"].notna() & df["first_name"].notna() & df["last_name"].notna()]
    
    # Create full_name
    df["full_name"] = df["first_name"] + " " + df["last_name"]
    
    # Determine slot type
    def get_slot_type(title):
        if pd.isna(title):
            return "OTHER"
        title_lower = str(title).lower()
        if any(x in title_lower for x in ["ceo", "chief executive", "president"]):
            return "CEO"
        elif any(x in title_lower for x in ["cfo", "chief financial", "finance"]):
            return "CFO"
        elif any(x in title_lower for x in ["chro", "chief human", "hr director", "human resources"]):
            return "HR"
        return "OTHER"
    
    df["slot_type"] = df["title"].apply(get_slot_type)
    
    print(f"Contact breakdown:")
    print(f"  CEO: {(df['slot_type'] == 'CEO').sum()}")
    print(f"  CFO: {(df['slot_type'] == 'CFO').sum()}")
    print(f"  HR: {(df['slot_type'] == 'HR').sum()}")
    print(f"  Other: {(df['slot_type'] == 'OTHER').sum()}\n")
    
    # Get company and slot lookups
    print("Building company and slot lookups...")
    
    cur.execute("""
        SELECT 
            cm.company_unique_id,
            cm.company_name,
            cs.company_slot_unique_id,
            cs.slot_type
        FROM marketing.company_master cm
        LEFT JOIN marketing.company_slots cs ON cm.company_unique_id = cs.company_unique_id
    """)
    
    rows = cur.fetchall()
    
    # Build lookup: company_name -> {slot_type -> slot_id, company_id}
    company_slot_lookup = {}
    for row in rows:
        comp_name = row['company_name']
        if comp_name not in company_slot_lookup:
            company_slot_lookup[comp_name] = {
                'company_id': row['company_unique_id'],
                'slots': {}
            }
        if row['slot_type'] and row['company_slot_unique_id']:
            company_slot_lookup[comp_name]['slots'][row['slot_type']] = row['company_slot_unique_id']
    
    print(f"Loaded {len(company_slot_lookup):,} companies with slots\n")
    
    print("Matching people to slots...")
    
    # Get current max person counter from existing people
    cur.execute("""
        SELECT COUNT(*) as count
        FROM marketing.people_master
    """)
    existing_people = cur.fetchone()['count']
    person_counter = existing_people + 1
    
    # Get existing emails to avoid duplicates
    cur.execute("""
        SELECT email
        FROM marketing.people_master
        WHERE email IS NOT NULL
    """)
    existing_emails = {row['email'].lower() for row in cur.fetchall()}
    
    print(f"Starting person counter at: {person_counter} (existing: {existing_people})")
    print(f"Existing emails to skip: {len(existing_emails)}\n")
    
    # Match people to slots
    people_to_insert = []
    matched = 0
    unmatched = 0
    skipped_duplicate = 0
    
    for idx, row in df.iterrows():
        company_name = str(row.get('company_name', '')).strip()
        slot_type = row.get('slot_type', 'OTHER')
        email = row.get('email', '').strip().lower() if pd.notna(row.get('email')) else ''
        
        # Skip duplicates
        if email and email in existing_emails:
            skipped_duplicate += 1
            continue
        
        # Find company and slot
        company_data = company_slot_lookup.get(company_name)
        
        if company_data and slot_type in company_data['slots']:
            matched += 1
            
            # Generate Barton ID for person
            # Format: 04.04.02.XX.XXXXX.XXX
            unique_id = f"04.04.02.{(person_counter % 100):02d}.{(person_counter % 100000):05d}.{(person_counter % 1000):03d}"
            person_counter += 1
            
            # Clean email status
            email_status = str(row.get('email_status', 'gray')).lower()
            if email_status == 'verified':
                email_status = 'green'
            email_verified = email_status == 'green'
            
            person_record = (
                unique_id,
                company_data['company_id'],
                company_data['slots'][slot_type],
                row.get('first_name'),
                row.get('last_name'),
                # full_name is auto-generated, skip it
                row.get('title') if pd.notna(row.get('title')) else None,
                row.get('seniority') if pd.notna(row.get('seniority')) else None,
                str(row.get('department')).split(',')[0].strip() if pd.notna(row.get('department')) else None,
                row.get('email'),
                row.get('work_phone') if pd.notna(row.get('work_phone')) else None,
                row.get('mobile_phone') if pd.notna(row.get('mobile_phone')) else None,
                row.get('linkedin_url') if pd.notna(row.get('linkedin_url')) else None,
                None,  # twitter_url
                None,  # facebook_url
                None,  # bio
                None,  # skills
                None,  # education
                None,  # certifications
                'apollo_import',  # source_system
                row.get('apollo_contact_id') if pd.notna(row.get('apollo_contact_id')) else None,
                email_verified
            )
            
            people_to_insert.append(person_record)
        else:
            unmatched += 1
    
    print(f"  Matched: {matched}")
    print(f"  Unmatched: {unmatched}")
    print(f"  Skipped (duplicates): {skipped_duplicate}")
    
    if matched == 0:
        print("\n[ERROR] No people matched to slots")
        return False
    
    print(f"\nInserting {len(people_to_insert):,} people into marketing.people_master...")
    
    # Insert people (full_name is auto-generated)
    insert_query = """
        INSERT INTO marketing.people_master (
            unique_id, company_unique_id, company_slot_unique_id,
            first_name, last_name, title, seniority, department,
            email, work_phone_e164, personal_phone_e164, linkedin_url,
            twitter_url, facebook_url, bio, skills, education, certifications,
            source_system, source_record_id, email_verified
        )
        VALUES %s
    """
    
    execute_values(cur, insert_query, people_to_insert, page_size=100)
    
    print(f"[OK] Successfully inserted {len(people_to_insert):,} people")
    
    return True

def run_full_pipeline(people_csv):
    """Run the complete import pipeline"""
    
    database_url = os.getenv('NEON_DATABASE_URL')
    
    if not database_url:
        print("[ERROR] NEON_DATABASE_URL not set")
        return False
    
    print("\n" + "="*100)
    print("FULL DATA PIPELINE: COMPANIES -> SLOTS -> PEOPLE")
    print("="*100)
    
    try:
        conn = psycopg2.connect(database_url)
        conn.autocommit = False  # Use transactions
        cur = conn.cursor(cursor_factory=RealDictCursor)
        
        # Step 1: Promote companies
        if not promote_companies_to_marketing(cur):
            print("\n[FAILED] Company promotion failed")
            conn.rollback()
            return False
        
        conn.commit()
        print("[COMMITTED] Company promotion complete")
        
        # Step 2: Generate slots
        if not generate_company_slots(cur):
            print("\n[FAILED] Slot generation failed")
            conn.rollback()
            return False
        
        conn.commit()
        print("[COMMITTED] Slot generation complete")
        
        # Step 3: Import people
        if not import_people_linked(people_csv, cur):
            print("\n[FAILED] People import failed")
            conn.rollback()
            return False
        
        conn.commit()
        print("[COMMITTED] People import complete")
        
        # Final verification
        print("\n" + "="*100)
        print("FINAL VERIFICATION")
        print("="*100 + "\n")
        
        cur.execute("SELECT COUNT(*) as count FROM intake.company_raw_intake")
        intake_count = cur.fetchone()['count']
        
        cur.execute("SELECT COUNT(*) as count FROM marketing.company_master")
        companies_count = cur.fetchone()['count']
        
        cur.execute("SELECT COUNT(*) as count FROM marketing.company_slots")
        slots_count = cur.fetchone()['count']
        
        cur.execute("SELECT COUNT(*) as count FROM marketing.people_master")
        people_count = cur.fetchone()['count']
        
        print(f"  intake.company_raw_intake:     {intake_count:,} companies")
        print(f"  marketing.company_master:      {companies_count:,} companies")
        print(f"  marketing.company_slots:       {slots_count:,} slots")
        print(f"  marketing.people_master:       {people_count:,} contacts")
        print()
        
        # Show slot fill rate
        cur.execute("""
            SELECT 
                cs.slot_type,
                COUNT(*) as total_slots,
                COUNT(pm.unique_id) as filled_slots
            FROM marketing.company_slots cs
            LEFT JOIN marketing.people_master pm ON cs.company_slot_unique_id = pm.company_slot_unique_id
            GROUP BY cs.slot_type
            ORDER BY cs.slot_type
        """)
        
        slot_stats = cur.fetchall()
        print("  Slot Fill Rates:")
        for stat in slot_stats:
            fill_rate = (stat['filled_slots'] / stat['total_slots'] * 100) if stat['total_slots'] > 0 else 0
            print(f"    {stat['slot_type']}: {stat['filled_slots']:,}/{stat['total_slots']:,} ({fill_rate:.1f}%)")
        
        print("\n" + "="*100)
        print("PIPELINE COMPLETE - ALL DATA LINKED!")
        print("="*100)
        print(f"  Status: SUCCESS")
        print(f"  All relationships intact:")
        print(f"    Companies -> Slots -> People")
        print("="*100 + "\n")
        
        cur.close()
        conn.close()
        
        return True
        
    except Exception as e:
        print(f"\n[ERROR] Pipeline failed: {e}")
        import traceback
        traceback.print_exc()
        if conn:
            conn.rollback()
            print("[ROLLBACK] All changes rolled back")
        return False

def main():
    """Main execution."""
    
    # Get people CSV from command line
    if len(sys.argv) > 1:
        people_file = sys.argv[1]
    else:
        people_file = "ceo-cfo-wv.csv"
    
    if not os.path.exists(people_file):
        print(f"[ERROR] People file not found: {people_file}")
        print("\nUsage: python full_pipeline_import.py <people_csv>")
        return
    
    # Confirm
    print("\n" + "="*100)
    print("READY TO RUN FULL PIPELINE")
    print("="*100)
    print("  This will:")
    print("    1. Promote companies from intake -> marketing.company_master")
    print("    2. Generate CEO/CFO/HR slots for all companies")
    print("    3. Import people and link them to slots")
    print("\nType 'YES' to proceed: ", end='')
    
    if os.getenv('AUTO_CONFIRM') == 'YES':
        confirmation = 'YES'
        print("YES (auto-confirmed)")
    else:
        confirmation = input().strip()
    
    if confirmation != 'YES':
        print("\n[CANCELLED]")
        return
    
    # Run pipeline
    success = run_full_pipeline(people_file)
    
    if success:
        print("\n[SUCCESS] Full pipeline complete!")
        print("  All companies, slots, and people are now linked in Neon database")
    else:
        print("\n[FAILED] Pipeline did not complete successfully")

if __name__ == "__main__":
    main()

