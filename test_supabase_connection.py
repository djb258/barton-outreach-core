#!/usr/bin/env python3
"""
Test Supabase database connection
"""
import psycopg2
import os
from dotenv import load_dotenv

load_dotenv()

def main():
    supabase_url = os.getenv('SUPABASE_DB_URL')

    if not supabase_url:
        print("[-] SUPABASE_DB_URL not found in .env")
        return

    print("[*] Testing Supabase connection...")

    try:
        conn = psycopg2.connect(supabase_url)
        cursor = conn.cursor()

        # Test query
        cursor.execute("SELECT version()")
        version = cursor.fetchone()[0]
        print(f"[+] Connected successfully!")
        print(f"[*] PostgreSQL version: {version[:50]}...")

        # Check for enrichment tables
        cursor.execute("""
            SELECT table_name
            FROM information_schema.tables
            WHERE table_schema = 'public'
            AND table_name LIKE '%enrichment%'
            ORDER BY table_name
        """)
        tables = cursor.fetchall()

        if tables:
            print(f"\n[+] Found {len(tables)} enrichment tables:")
            for table in tables:
                cursor.execute(f"SELECT COUNT(*) FROM public.{table[0]}")
                count = cursor.fetchone()[0]
                print(f"   - {table[0]}: {count} records")
        else:
            print("\n[!] No enrichment tables found. Need to create:")
            print("   - public.company_needs_enrichment")
            print("   - public.people_needs_enrichment")

        conn.close()

    except Exception as e:
        print(f"[-] Connection failed: {e}")

if __name__ == "__main__":
    main()
