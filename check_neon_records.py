#!/usr/bin/env python3
"""
Quick script to check Neon database for invalid records
"""
import psycopg2
import os
from dotenv import load_dotenv

load_dotenv()

def main():
    db_url = os.getenv('DATABASE_URL')

    if not db_url:
        print("[-] DATABASE_URL not found in .env")
        return

    print(f"[*] Connecting to Neon database...")

    try:
        conn = psycopg2.connect(db_url)
        cursor = conn.cursor()

        # Check for invalid company records
        print("\n[*] Checking for invalid company records...")
        cursor.execute("""
            SELECT
                COUNT(*) as total,
                COUNT(*) FILTER (WHERE promoted_to IS NULL) as unpromoted,
                COUNT(*) FILTER (WHERE validation_status = 'FAILED') as failed,
                COUNT(*) FILTER (WHERE validation_status = 'PENDING') as pending
            FROM marketing.company_invalid
        """)
        company_stats = cursor.fetchone()

        # Check for invalid people records
        print("[*] Checking for invalid people records...")
        cursor.execute("""
            SELECT
                COUNT(*) as total,
                COUNT(*) FILTER (WHERE promoted_to IS NULL) as unpromoted,
                COUNT(*) FILTER (WHERE validation_status = 'FAILED') as failed,
                COUNT(*) FILTER (WHERE validation_status = 'PENDING') as pending
            FROM marketing.people_invalid
        """)
        people_stats = cursor.fetchone()

        print(f"""
╔══════════════════════════════════════════════╗
║        NEON INVALID RECORDS SUMMARY          ║
╠══════════════════════════════════════════════╣
║ COMPANIES:                                   ║
║   Total:       {company_stats[0]:4d}                         ║
║   Unpromoted:  {company_stats[1]:4d}                         ║
║   Failed:      {company_stats[2]:4d}                         ║
║   Pending:     {company_stats[3]:4d}                         ║
║                                              ║
║ PEOPLE:                                      ║
║   Total:       {people_stats[0]:4d}                         ║
║   Unpromoted:  {people_stats[1]:4d}                         ║
║   Failed:      {people_stats[2]:4d}                         ║
║   Pending:     {people_stats[3]:4d}                         ║
║                                              ║
║ READY FOR SYNC: {company_stats[1] + people_stats[1]:4d}                     ║
╚══════════════════════════════════════════════╝
        """)

        # Show sample records
        if company_stats[1] > 0:
            print("\n[*] Sample Company Records (first 5):")
            cursor.execute("""
                SELECT id, company_name, domain, validation_status, validation_errors
                FROM marketing.company_invalid
                WHERE promoted_to IS NULL
                LIMIT 5
            """)
            for row in cursor.fetchall():
                print(f"  ID {row[0]}: {row[1]} | {row[2] or 'NO DOMAIN'} | {row[3]} | {row[4]}")

        if people_stats[1] > 0:
            print("\n[*] Sample People Records (first 5):")
            cursor.execute("""
                SELECT id, first_name, last_name, email, validation_status
                FROM marketing.people_invalid
                WHERE promoted_to IS NULL
                LIMIT 5
            """)
            for row in cursor.fetchall():
                print(f"  ID {row[0]}: {row[1]} {row[2]} | {row[3] or 'NO EMAIL'} | {row[4]}")

        conn.close()
        print("\n[+] Check complete!")

    except (psycopg2.OperationalError, psycopg2.errors.UndefinedTable) as e:
        if "does not exist" in str(e):
            print(f"\n[!] Tables don't exist yet. Need to create:")
            print("   - marketing.company_invalid")
            print("   - marketing.people_invalid")
            print("\nRun the migration script first!")
        else:
            print(f"\n[-] Database connection error: {e}")
    except Exception as e:
        print(f"\n[-] Error: {e}")

if __name__ == "__main__":
    main()
