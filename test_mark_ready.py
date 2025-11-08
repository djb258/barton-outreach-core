#!/usr/bin/env python3
"""
Test script: Mark a few records as READY for push-back testing
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

        print("\n[*] Finding sample records to enrich...")

        # Get 2 companies missing domains
        cursor.execute("""
            SELECT id, source_id, company_name, domain
            FROM public.company_needs_enrichment
            WHERE domain IS NULL OR domain = ''
            LIMIT 2
        """)
        companies = cursor.fetchall()

        # Get 1 person missing email
        cursor.execute("""
            SELECT id, source_id, first_name, last_name, email
            FROM public.people_needs_enrichment
            WHERE email IS NULL OR email = ''
            LIMIT 1
        """)
        people = cursor.fetchall()

        if companies:
            print(f"\n[*] Enriching {len(companies)} companies...")
            for company in companies:
                uuid, source_id, name, domain = company
                # Add sample enrichment data
                fake_domain = f"{name.lower().replace(' ', '').replace(',', '')[:20]}.com" if name else "example.com"

                cursor.execute("""
                    UPDATE public.company_needs_enrichment
                    SET
                        domain = %s,
                        industry = 'Technology',
                        location = 'Charleston, WV',
                        validation_status = 'READY',
                        enriched_by = 'test-script',
                        enriched_at = NOW()
                    WHERE id = %s
                """, (fake_domain, uuid))

                print(f"   [+] Enriched: {name} -> {fake_domain}")

        if people:
            print(f"\n[*] Enriching {len(people)} people...")
            for person in people:
                uuid, source_id, first_name, last_name, email = person
                # Add sample enrichment data
                fake_email = f"{first_name.lower() if first_name else 'john'}.{last_name.lower() if last_name else 'doe'}@example.com"

                cursor.execute("""
                    UPDATE public.people_needs_enrichment
                    SET
                        email = %s,
                        title = 'Business Development Manager',
                        validation_status = 'READY',
                        enriched_by = 'test-script',
                        enriched_at = NOW()
                    WHERE id = %s
                """, (fake_email, uuid))

                print(f"   [+] Enriched: {first_name} {last_name} -> {fake_email}")

        conn.commit()

        total = len(companies) + len(people)
        print(f"\n[+] Marked {total} records as READY")
        print("[*] Run check_ready_for_pushback.py to verify")
        print("[*] Run sync_supabase_to_neon.py to push back to Neon")

        conn.close()

    except Exception as e:
        print(f"[-] Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
