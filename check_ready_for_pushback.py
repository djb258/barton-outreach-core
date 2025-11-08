#!/usr/bin/env python3
"""
Check which enriched records are ready to push back to Neon
"""
import psycopg2
import os
from dotenv import load_dotenv

load_dotenv()

def main():
    supabase_url = os.getenv('SUPABASE_DB_URL')

    print("[*] Connecting to Supabase...")

    try:
        conn = psycopg2.connect(supabase_url)
        cursor = conn.cursor()

        # Check READY companies
        print("\n[*] Checking companies ready for push-back...")
        cursor.execute("""
            SELECT COUNT(*) FROM public.company_needs_enrichment
            WHERE validation_status = 'READY'
            AND promoted_to_neon = FALSE
        """)
        ready_companies = cursor.fetchone()[0]

        # Check READY people
        print("[*] Checking people ready for push-back...")
        cursor.execute("""
            SELECT COUNT(*) FROM public.people_needs_enrichment
            WHERE validation_status = 'READY'
            AND promoted_to_neon = FALSE
        """)
        ready_people = cursor.fetchone()[0]

        # Check total status breakdown
        cursor.execute("""
            SELECT
                validation_status,
                COUNT(*) as count
            FROM public.company_needs_enrichment
            GROUP BY validation_status
            ORDER BY validation_status
        """)
        company_status = cursor.fetchall()

        cursor.execute("""
            SELECT
                validation_status,
                COUNT(*) as count
            FROM public.people_needs_enrichment
            GROUP BY validation_status
            ORDER BY validation_status
        """)
        people_status = cursor.fetchall()

        print("\n" + "="*50)
        print("  SUPABASE ENRICHMENT STATUS")
        print("="*50)
        print("\nCOMPANIES:")

        for status, count in company_status:
            print(f"  {status:15s} {count:4d}")

        print("\nPEOPLE:")

        for status, count in people_status:
            print(f"  {status:15s} {count:4d}")

        print("\nREADY TO PUSH BACK:")
        print(f"  Companies:    {ready_companies:4d}")
        print(f"  People:       {ready_people:4d}")
        print(f"  Total:        {ready_companies + ready_people:4d}")
        print("="*50)

        if ready_companies > 0:
            print("\n[*] Sample READY companies (first 5):")
            cursor.execute("""
                SELECT source_id, company_name, domain, enriched_by
                FROM public.company_needs_enrichment
                WHERE validation_status = 'READY'
                AND promoted_to_neon = FALSE
                LIMIT 5
            """)
            for row in cursor.fetchall():
                print(f"   ID {row[0]}: {row[1]} | {row[2] or 'NO DOMAIN'} | Enriched by: {row[3] or 'N/A'}")

        if ready_people > 0:
            print("\n[*] Sample READY people (first 5):")
            cursor.execute("""
                SELECT source_id, first_name, last_name, email, enriched_by
                FROM public.people_needs_enrichment
                WHERE validation_status = 'READY'
                AND promoted_to_neon = FALSE
                LIMIT 5
            """)
            for row in cursor.fetchall():
                print(f"   ID {row[0]}: {row[1]} {row[2]} | {row[3] or 'NO EMAIL'} | Enriched by: {row[4] or 'N/A'}")

        conn.close()

        if ready_companies + ready_people == 0:
            print("\n[!] No records ready for push-back")
            print("[*] Records need validation_status='READY' and promoted_to_neon=FALSE")
            print("\n[*] To mark a record as READY:")
            print("    UPDATE company_needs_enrichment")
            print("    SET validation_status='READY', enriched_by='your-name', enriched_at=NOW()")
            print("    WHERE id='uuid-here'")
        else:
            print(f"\n[+] Ready to push {ready_companies + ready_people} records back to Neon!")

    except Exception as e:
        print(f"[-] Error: {e}")

if __name__ == "__main__":
    main()
