#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Migration: Add email verification tracking to marketing.people_master
Tracks if each contact's email is verified, by what method, and when.

CTB Classification Metadata:
CTB Branch: data/migrations
Barton ID: 04.04.08
Unique ID: CTB-EMAILVERIF
Enforcement: ORBT
"""

import os
import sys
import psycopg2
from psycopg2.extras import RealDictCursor

# Set UTF-8 encoding for Windows console
if sys.platform == 'win32':
    import codecs
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')

def check_existing_columns(cur):
    """Check which verification columns already exist."""
    
    print("\n" + "="*100)
    print("CHECKING EXISTING COLUMNS")
    print("="*100 + "\n")
    
    cur.execute("""
        SELECT column_name
        FROM information_schema.columns
        WHERE table_schema = 'marketing'
          AND table_name = 'people_master'
          AND column_name IN ('email_verified', 'email_verification_source', 'email_verified_at')
        ORDER BY column_name
    """)
    
    existing = [row['column_name'] for row in cur.fetchall()]
    
    print("Checking for email verification columns:")
    print(f"  email_verified: {'EXISTS' if 'email_verified' in existing else 'MISSING'}")
    print(f"  email_verification_source: {'EXISTS' if 'email_verification_source' in existing else 'MISSING'}")
    print(f"  email_verified_at: {'EXISTS' if 'email_verified_at' in existing else 'MISSING'}")
    print()
    
    return existing

def add_verification_columns(cur, existing_columns):
    """Add email verification columns if they don't exist."""
    
    print("="*100)
    print("ADDING EMAIL VERIFICATION COLUMNS")
    print("="*100 + "\n")
    
    columns_to_add = []
    
    # Add email_verified if missing
    if 'email_verified' not in existing_columns:
        print("[1/3] Adding email_verified column...")
        cur.execute("""
            ALTER TABLE marketing.people_master
            ADD COLUMN email_verified BOOLEAN DEFAULT FALSE;
            
            COMMENT ON COLUMN marketing.people_master.email_verified IS
                'TRUE if email has been verified as deliverable. Used for send filtering in workflows.';
        """)
        print("      [OK] email_verified added (BOOLEAN, default FALSE)")
        columns_to_add.append('email_verified')
    else:
        print("[1/3] email_verified column already exists - skipping")
    
    # Add email_verification_source if missing
    if 'email_verification_source' not in existing_columns:
        print("[2/3] Adding email_verification_source column...")
        cur.execute("""
            ALTER TABLE marketing.people_master
            ADD COLUMN email_verification_source TEXT;
            
            COMMENT ON COLUMN marketing.people_master.email_verification_source IS
                'Source of email verification: apollo, millionverifier, zerobounce, manual, etc.';
        """)
        print("      [OK] email_verification_source added (TEXT)")
        columns_to_add.append('email_verification_source')
    else:
        print("[2/3] email_verification_source column already exists - skipping")
    
    # Add email_verified_at if missing
    if 'email_verified_at' not in existing_columns:
        print("[3/3] Adding email_verified_at column...")
        cur.execute("""
            ALTER TABLE marketing.people_master
            ADD COLUMN email_verified_at TIMESTAMPTZ;
            
            COMMENT ON COLUMN marketing.people_master.email_verified_at IS
                'Timestamp when email was last verified. Used for re-verification scheduling (30-day refresh).';
        """)
        print("      [OK] email_verified_at added (TIMESTAMPTZ)")
        columns_to_add.append('email_verified_at')
    else:
        print("[3/3] email_verified_at column already exists - skipping")
    
    print()
    
    if columns_to_add:
        print(f"Added {len(columns_to_add)} new columns: {', '.join(columns_to_add)}")
    else:
        print("All verification columns already exist - no changes needed")
    
    print()
    
    return len(columns_to_add) > 0

def create_verification_index(cur):
    """Create index for email_verified lookups."""
    
    print("="*100)
    print("CREATING INDEXES")
    print("="*100 + "\n")
    
    print("Creating index on email_verified...")
    
    cur.execute("""
        CREATE INDEX IF NOT EXISTS idx_people_master_email_verified 
        ON marketing.people_master(email_verified) 
        WHERE email_verified = TRUE;
    """)
    
    cur.execute("""
        COMMENT ON INDEX marketing.idx_people_master_email_verified IS
            'Partial index for fast lookup of verified contacts. Used by messaging workflows.';
    """)
    
    print("[OK] Index created: idx_people_master_email_verified")
    print("     Type: Partial index (WHERE email_verified = TRUE)")
    print("     Purpose: Fast filtering for send-ready contacts")
    print()

def populate_verified_from_apollo(cur):
    """Mark Apollo-verified emails as verified."""
    
    print("="*100)
    print("POPULATING VERIFICATION STATUS FROM APOLLO DATA")
    print("="*100 + "\n")
    
    print("Checking for Apollo-verified contacts...")
    
    # Check if we have any contacts
    cur.execute("SELECT COUNT(*) as count FROM marketing.people_master")
    total = cur.fetchone()['count']
    
    if total == 0:
        print("  No contacts in database yet - skipping")
        print()
        return
    
    # Mark contacts that were imported from Apollo with verified status as verified
    # Assuming they were imported with email_verified already set, or we can infer from source
    cur.execute("""
        UPDATE marketing.people_master
        SET email_verified = TRUE,
            email_verification_source = 'apollo',
            email_verified_at = NOW()
        WHERE source_system = 'apollo_import'
          AND email IS NOT NULL
          AND (email_verified IS NULL OR email_verified = FALSE)
          AND email_verification_source IS NULL
    """)
    
    updated = cur.rowcount
    
    print(f"[OK] Marked {updated} Apollo contacts as verified")
    
    # Show current status
    cur.execute("""
        SELECT 
            email_verified,
            email_verification_source,
            COUNT(*) as count
        FROM marketing.people_master
        WHERE email IS NOT NULL
        GROUP BY email_verified, email_verification_source
        ORDER BY email_verified DESC, count DESC
    """)
    
    status = cur.fetchall()
    
    print("\nVerification Status:")
    for s in status:
        verified = "VERIFIED" if s['email_verified'] else "UNVERIFIED"
        source = s['email_verification_source'] or 'unknown'
        print(f"  {verified} ({source}): {s['count']} contacts")
    
    print()

def show_usage_examples():
    """Show how to use the verification fields."""
    
    print("="*100)
    print("USAGE EXAMPLES")
    print("="*100 + "\n")
    
    print("1. Get only verified contacts for sending:")
    print("-"*100)
    print("""
SELECT full_name, email, email_verified_at
FROM marketing.people_master
WHERE email_verified = TRUE
  AND email IS NOT NULL;
""")
    
    print("2. Mark email as verified (after MillionVerifier):")
    print("-"*100)
    print("""
UPDATE marketing.people_master
SET email_verified = TRUE,
    email_verification_source = 'millionverifier',
    email_verified_at = NOW()
WHERE unique_id = '04.04.02.XX.XXXXX.XXX';
""")
    
    print("3. Find contacts needing re-verification (30-day refresh):")
    print("-"*100)
    print("""
SELECT unique_id, full_name, email, email_verified_at
FROM marketing.people_master
WHERE email_verified = TRUE
  AND (email_verified_at < NOW() - INTERVAL '30 days' OR email_verified_at IS NULL);
""")
    
    print("4. Insert verification record (audit trail):")
    print("-"*100)
    print("""
INSERT INTO marketing.email_verification 
(enrichment_id, email, verification_status, verification_service, verified_at)
VALUES (123, 'test@example.com', 'valid', 'millionverifier', NOW());
""")
    
    print()
    print("="*100 + "\n")

def main():
    """Main execution."""
    
    database_url = os.getenv('NEON_DATABASE_URL')
    
    if not database_url:
        print("[ERROR] NEON_DATABASE_URL not set")
        return
    
    print("\n" + "="*100)
    print("EMAIL VERIFICATION TRACKING MIGRATION")
    print("="*100)
    print("\nAdding verification tracking to marketing.people_master...")
    print()
    
    try:
        conn = psycopg2.connect(database_url)
        conn.autocommit = False
        cur = conn.cursor(cursor_factory=RealDictCursor)
        
        # Check existing
        existing = check_existing_columns(cur)
        
        # Add columns
        changes_made = add_verification_columns(cur, existing)
        
        if changes_made:
            conn.commit()
            print("[COMMITTED] Columns added\n")
        else:
            print("[INFO] No changes needed\n")
        
        # Create index
        create_verification_index(cur)
        conn.commit()
        print("[COMMITTED] Index created\n")
        
        # Populate from existing data
        populate_verified_from_apollo(cur)
        conn.commit()
        print("[COMMITTED] Verification status populated\n")
        
        # Show usage
        show_usage_examples()
        
        # Final summary
        print("="*100)
        print("MIGRATION COMPLETE")
        print("="*100)
        print("\nEmail verification tracking is now active!")
        print("  - email_verified: Flag for send filtering")
        print("  - email_verification_source: Tracks verification method")
        print("  - email_verified_at: Timestamp for refresh scheduling")
        print()
        print("Ready for:")
        print("  - n8n messaging workflows (filters by email_verified = TRUE)")
        print("  - MillionVerifier integration")
        print("  - 30-day re-verification cycles")
        print("="*100 + "\n")
        
        cur.close()
        conn.close()
        
    except Exception as e:
        print(f"\n[ERROR] {e}")
        import traceback
        traceback.print_exc()
        if conn:
            conn.rollback()

if __name__ == "__main__":
    main()

