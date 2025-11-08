#!/usr/bin/env python3
"""
Verify data synced to Lovable Supabase
Check both company_needs_enrichment and people_needs_enrichment tables
"""
import psycopg2
import os
from dotenv import load_dotenv

load_dotenv()

# Lovable Supabase connection
SUPABASE_DB_URL = "postgresql://postgres.sfkgilgjmfqfjlvgdhzt:Hammersupabase15522!@aws-0-us-east-1.pooler.supabase.com:6543/postgres"

def check_companies():
    """Check company records in Lovable Supabase"""
    print("\n[*] Checking company_needs_enrichment table...")

    conn = psycopg2.connect(SUPABASE_DB_URL)
    cursor = conn.cursor()

    # Count total records
    cursor.execute("""
        SELECT COUNT(*)
        FROM company_needs_enrichment
    """)
    total = cursor.fetchone()[0]
    print(f"[+] Total companies: {total}")

    # Count by validation_source
    cursor.execute("""
        SELECT validation_source, COUNT(*)
        FROM company_needs_enrichment
        GROUP BY validation_source
    """)
    sources = cursor.fetchall()
    print(f"\n[*] By source:")
    for source, count in sources:
        print(f"    {source or 'NULL'}: {count}")

    # Count by state
    cursor.execute("""
        SELECT state, COUNT(*)
        FROM company_needs_enrichment
        GROUP BY state
    """)
    states = cursor.fetchall()
    print(f"\n[*] By state:")
    for state, count in states:
        print(f"    {state or 'NULL'}: {count}")

    # Show recent records
    cursor.execute("""
        SELECT company_name, website, industry, hq_city, created_at, validation_source
        FROM company_needs_enrichment
        ORDER BY created_at DESC
        LIMIT 5
    """)
    recent = cursor.fetchall()
    print(f"\n[*] Recent 5 companies:")
    for company in recent:
        print(f"    - {company[0]} | {company[1]} | {company[2]} | {company[3]}")
        print(f"      Source: {company[5]} | Created: {company[4]}")

    conn.close()
    return total

def check_people():
    """Check people records in Lovable Supabase"""
    print("\n[*] Checking people_needs_enrichment table...")

    conn = psycopg2.connect(SUPABASE_DB_URL)
    cursor = conn.cursor()

    # Count total records
    cursor.execute("""
        SELECT COUNT(*)
        FROM people_needs_enrichment
    """)
    total = cursor.fetchone()[0]
    print(f"[+] Total people: {total}")

    # Count by validation_source
    cursor.execute("""
        SELECT validation_source, COUNT(*)
        FROM people_needs_enrichment
        GROUP BY validation_source
    """)
    sources = cursor.fetchall()
    print(f"\n[*] By source:")
    for source, count in sources:
        print(f"    {source or 'NULL'}: {count}")

    # Count by state
    cursor.execute("""
        SELECT state, COUNT(*)
        FROM people_needs_enrichment
        GROUP BY state
    """)
    states = cursor.fetchall()
    print(f"\n[*] By state:")
    for state, count in states:
        print(f"    {state or 'NULL'}: {count}")

    # Show recent records
    cursor.execute("""
        SELECT first_name, last_name, email, title, company_name, created_at, validation_source
        FROM people_needs_enrichment
        ORDER BY created_at DESC
        LIMIT 5
    """)
    recent = cursor.fetchall()
    print(f"\n[*] Recent 5 people:")
    for person in recent:
        print(f"    - {person[0]} {person[1]} | {person[2]}")
        print(f"      {person[3]} at {person[4]}")
        print(f"      Source: {person[6]} | Created: {person[5]}")

    conn.close()
    return total

def main():
    print("\n" + "="*60)
    print("  LOVABLE SUPABASE VERIFICATION")
    print("="*60)

    try:
        company_count = check_companies()
        people_count = check_people()

        # Summary
        print("\n" + "="*60)
        print("  SUMMARY")
        print("="*60)
        print(f"  Companies:  {company_count:4d}")
        print(f"  People:     {people_count:4d}")
        print(f"  Total:      {company_count + people_count:4d}")
        print("="*60)

        print("\n[+] Verification complete!")
        print("[*] Dashboard: https://supabase.com/dashboard/project/sfkgilgjmfqfjlvgdhzt/editor")

    except Exception as e:
        print(f"\n[-] Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
