#!/usr/bin/env python3
"""
Add sync tracking columns to Neon invalid tables
"""
import psycopg2
import os
from dotenv import load_dotenv

load_dotenv()

def main():
    db_url = os.getenv('DATABASE_URL')

    print(f"[*] Connecting to Neon database...")

    try:
        conn = psycopg2.connect(db_url)
        cursor = conn.cursor()

        print("[*] Adding sync tracking columns...")

        # Add columns to company_invalid
        print("\n[+] Updating marketing.company_invalid...")
        cursor.execute("""
            ALTER TABLE marketing.company_invalid
            ADD COLUMN IF NOT EXISTS promoted_to TEXT,
            ADD COLUMN IF NOT EXISTS promoted_at TIMESTAMP,
            ADD COLUMN IF NOT EXISTS enrichment_data JSONB,
            ADD COLUMN IF NOT EXISTS linkedin_url TEXT,
            ADD COLUMN IF NOT EXISTS revenue NUMERIC,
            ADD COLUMN IF NOT EXISTS location TEXT
        """)

        # Add columns to people_invalid
        print("[+] Updating marketing.people_invalid...")
        cursor.execute("""
            ALTER TABLE marketing.people_invalid
            ADD COLUMN IF NOT EXISTS promoted_to TEXT,
            ADD COLUMN IF NOT EXISTS promoted_at TIMESTAMP,
            ADD COLUMN IF NOT EXISTS enrichment_data JSONB
        """)

        # Create indexes for sync performance
        print("[+] Creating indexes...")
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_company_invalid_promoted
            ON marketing.company_invalid(promoted_to, promoted_at);

            CREATE INDEX IF NOT EXISTS idx_company_invalid_status
            ON marketing.company_invalid(validation_status);

            CREATE INDEX IF NOT EXISTS idx_people_invalid_promoted
            ON marketing.people_invalid(promoted_to, promoted_at);

            CREATE INDEX IF NOT EXISTS idx_people_invalid_status
            ON marketing.people_invalid(validation_status);
        """)

        conn.commit()

        # Verify
        print("\n[*] Verifying...")
        cursor.execute("""
            SELECT COUNT(*) FROM marketing.company_invalid WHERE promoted_to IS NULL
        """)
        company_count = cursor.fetchone()[0]

        cursor.execute("""
            SELECT COUNT(*) FROM marketing.people_invalid WHERE promoted_to IS NULL
        """)
        people_count = cursor.fetchone()[0]

        print(f"""
╔══════════════════════════════════════════════╗
║        SYNC SETUP COMPLETE                   ║
╠══════════════════════════════════════════════╣
║ Companies ready for sync: {company_count:4d}             ║
║ People ready for sync:    {people_count:4d}             ║
║                                              ║
║ Total records ready:      {company_count + people_count:4d}             ║
╚══════════════════════════════════════════════╝

[+] Database is now ready for Neon -> Supabase sync!
        """)

        conn.close()

    except Exception as e:
        print(f"\n[-] Error: {e}")

if __name__ == "__main__":
    main()
