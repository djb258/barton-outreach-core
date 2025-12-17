#!/usr/bin/env python3
"""
Push enriched data from Supabase back to Neon
"""
import psycopg2
import os
import json
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

def push_companies(supabase_conn, neon_conn):
    """Push enriched company data back to Neon"""
    supabase_cursor = supabase_conn.cursor()
    neon_cursor = neon_conn.cursor()

    print("\n[*] Pulling READY companies from Supabase...")

    # Get READY companies from Supabase
    supabase_cursor.execute("""
        SELECT
            source_id, company_name, domain, industry, employee_count,
            revenue, location, linkedin_url, website, enrichment_data,
            enriched_by, enriched_at, id
        FROM public.company_needs_enrichment
        WHERE validation_status = 'READY'
        AND promoted_to_neon = FALSE
        ORDER BY enriched_at ASC
    """)

    companies = supabase_cursor.fetchall()
    count = len(companies)

    if count == 0:
        print("[*] No companies ready to push back")
        return 0

    print(f"[*] Found {count} companies to push back to Neon")

    # Update Neon records with enriched data
    updated = 0
    for company in companies:
        source_id = int(company[0])

        try:
            # Update the invalid record with enriched data
            neon_cursor.execute("""
                UPDATE marketing.company_invalid
                SET
                    domain = COALESCE(%s, domain),
                    industry = COALESCE(%s, industry),
                    employee_count = COALESCE(%s, employee_count),
                    revenue = COALESCE(%s, revenue),
                    location = COALESCE(%s, location),
                    linkedin_url = COALESCE(%s, linkedin_url),
                    website = COALESCE(%s, website),
                    enrichment_data = COALESCE(%s, enrichment_data),
                    validation_status = 'READY',
                    updated_at = NOW()
                WHERE id = %s
            """, (
                company[2],  # domain
                company[3],  # industry
                company[4],  # employee_count
                company[5],  # revenue
                company[6],  # location
                company[7],  # linkedin_url
                company[8],  # website
                json.dumps(company[9]) if company[9] else None,  # enrichment_data
                source_id
            ))

            if neon_cursor.rowcount > 0:
                updated += 1
            else:
                print(f"[!] Warning: No Neon record found for source_id {source_id}")

        except Exception as e:
            print(f"[!] Error updating company {source_id}: {e}")

    neon_conn.commit()
    print(f"[+] Updated {updated}/{count} companies in Neon")

    # Mark as promoted in Supabase
    company_uuids = [str(c[12]) for c in companies]
    placeholders = ','.join(['%s' for _ in company_uuids])
    supabase_cursor.execute(f"""
        UPDATE public.company_needs_enrichment
        SET promoted_to_neon = TRUE,
            promoted_at = NOW(),
            validation_status = 'PASSED'
        WHERE id::text IN ({placeholders})
    """, company_uuids)
    supabase_conn.commit()

    print(f"[+] Marked {len(company_uuids)} companies as promoted in Supabase")

    return updated

def push_people(supabase_conn, neon_conn):
    """Push enriched people data back to Neon"""
    supabase_cursor = supabase_conn.cursor()
    neon_cursor = neon_conn.cursor()

    print("\n[*] Pulling READY people from Supabase...")

    # Get READY people from Supabase
    supabase_cursor.execute("""
        SELECT
            source_id, first_name, last_name, email, phone,
            title, linkedin_url, enrichment_data,
            enriched_by, enriched_at, id
        FROM public.people_needs_enrichment
        WHERE validation_status = 'READY'
        AND promoted_to_neon = FALSE
        ORDER BY enriched_at ASC
    """)

    people = supabase_cursor.fetchall()
    count = len(people)

    if count == 0:
        print("[*] No people ready to push back")
        return 0

    print(f"[*] Found {count} people to push back to Neon")

    # Update Neon records with enriched data
    updated = 0
    for person in people:
        source_id = int(person[0])

        try:
            # Update the invalid record with enriched data
            neon_cursor.execute("""
                UPDATE marketing.people_invalid
                SET
                    first_name = COALESCE(%s, first_name),
                    last_name = COALESCE(%s, last_name),
                    email = COALESCE(%s, email),
                    phone = COALESCE(%s, phone),
                    title = COALESCE(%s, title),
                    linkedin_url = COALESCE(%s, linkedin_url),
                    enrichment_data = COALESCE(%s, enrichment_data),
                    validation_status = 'READY',
                    updated_at = NOW()
                WHERE id = %s
            """, (
                person[1],  # first_name
                person[2],  # last_name
                person[3],  # email
                person[4],  # phone
                person[5],  # title
                person[6],  # linkedin_url
                json.dumps(person[7]) if person[7] else None,  # enrichment_data
                source_id
            ))

            if neon_cursor.rowcount > 0:
                updated += 1
            else:
                print(f"[!] Warning: No Neon record found for source_id {source_id}")

        except Exception as e:
            print(f"[!] Error updating person {source_id}: {e}")

    neon_conn.commit()
    print(f"[+] Updated {updated}/{count} people in Neon")

    # Mark as promoted in Supabase
    people_uuids = [str(p[10]) for p in people]
    placeholders = ','.join(['%s' for _ in people_uuids])
    supabase_cursor.execute(f"""
        UPDATE public.people_needs_enrichment
        SET promoted_to_neon = TRUE,
            promoted_at = NOW(),
            validation_status = 'PASSED'
        WHERE id::text IN ({placeholders})
    """, people_uuids)
    supabase_conn.commit()

    print(f"[+] Marked {len(people_uuids)} people as promoted in Supabase")

    return updated

def main():
    neon_url = os.getenv('DATABASE_URL')
    supabase_url = os.getenv('SUPABASE_DB_URL')

    if not neon_url or not supabase_url:
        print("[-] Missing DATABASE_URL or SUPABASE_DB_URL in .env")
        return

    print("\n" + "="*60)
    print("  SUPABASE -> NEON ENRICHMENT PUSH-BACK")
    print("="*60)

    try:
        # Connect to both databases
        print("\n[*] Connecting to Supabase...")
        supabase_conn = psycopg2.connect(supabase_url)

        print("[*] Connecting to Neon...")
        neon_conn = psycopg2.connect(neon_url)

        # Push companies
        company_count = push_companies(supabase_conn, neon_conn)

        # Push people
        people_count = push_people(supabase_conn, neon_conn)

        # Summary
        total = company_count + people_count
        print("\n" + "="*60)
        print("  PUSH-BACK COMPLETE")
        print("="*60)
        print(f"  Companies updated:  {company_count:4d}")
        print(f"  People updated:     {people_count:4d}")
        print(f"  Total records:      {total:4d}")
        print("="*60)

        if total > 0:
            print("\n[+] Enriched data pushed back to Neon!")
            print("[*] Updated records are now marked as validation_status='READY'")
            print("[*] These records can now be promoted to production tables")
        else:
            print("\n[!] No records were updated")
            print("[*] Make sure records in Supabase have:")
            print("    - validation_status = 'READY'")
            print("    - promoted_to_neon = FALSE")
            print("    - enriched_by is set")

        supabase_conn.close()
        neon_conn.close()

    except Exception as e:
        print(f"\n[-] Push-back failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
