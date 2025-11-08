#!/usr/bin/env python3
"""
Sync invalid records from Neon to Supabase Enrichment Hub
"""
import psycopg2
import os
import json
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

def generate_batch_id():
    """Generate unique batch ID"""
    return f"EXT-{datetime.now().strftime('%Y-%m-%d')}-{os.urandom(4).hex()}"

def sync_companies(neon_conn, supabase_conn, batch_id, batch_size=1000):
    """Sync company records from Neon to Supabase"""
    neon_cursor = neon_conn.cursor()
    supabase_cursor = supabase_conn.cursor()

    print(f"\n[*] Syncing companies (batch: {batch_id})...")

    # Pull companies from Neon
    neon_cursor.execute(f"""
        SELECT
            id, company_unique_id, company_name, domain, industry,
            employee_count, website, phone, address, city, state, zip,
            validation_status, reason_code, validation_errors, validation_warnings,
            batch_id as source_batch_id, source_table, created_at
        FROM marketing.company_invalid
        WHERE promoted_to IS NULL
        LIMIT {batch_size}
    """)

    companies = neon_cursor.fetchall()
    count = len(companies)

    if count == 0:
        print("[*] No companies to sync")
        return 0

    print(f"[*] Found {count} companies to sync")

    # Insert into Supabase
    inserted = 0
    for company in companies:
        try:
            supabase_cursor.execute("""
                INSERT INTO public.company_needs_enrichment (
                    source_id, company_name, domain, industry, employee_count,
                    website, phone, address, city, state, zip,
                    validation_status, validation_errors, validation_warnings,
                    source_repo, source_table, batch_id, entity_type,
                    enrichment_source, priority, needs_review,
                    reason_code, pulled_at, imported_at
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (
                str(company[0]),  # source_id
                company[2],  # company_name
                company[3],  # domain
                company[4],  # industry
                company[5],  # employee_count
                company[6],  # website
                company[7],  # phone
                company[8],  # address
                company[9],  # city
                company[10],  # state
                company[11],  # zip
                'PENDING',  # validation_status
                json.dumps(company[14]) if company[14] else None,  # validation_errors (array -> json)
                json.dumps(company[15]) if company[15] else None,  # validation_warnings (array -> json)
                'barton-outreach-core',  # source_repo
                company[17] or 'marketing.company_invalid',  # source_table
                batch_id,  # batch_id
                'company',  # entity_type
                'external-import',  # enrichment_source
                'medium',  # priority
                True,  # needs_review
                company[13],  # reason_code
                datetime.now(),  # pulled_at
                datetime.now()  # imported_at
            ))
            inserted += 1
        except Exception as e:
            print(f"[!] Error inserting company {company[0]}: {e}")

    supabase_conn.commit()
    print(f"[+] Inserted {inserted}/{count} companies to Supabase")

    # Mark as promoted in Neon
    company_ids = [c[0] for c in companies]
    neon_cursor.execute("""
        UPDATE marketing.company_invalid
        SET promoted_to = 'enrichment-hub',
            promoted_at = NOW()
        WHERE id = ANY(%s)
    """, (company_ids,))
    neon_conn.commit()

    print(f"[+] Marked {len(company_ids)} companies as promoted in Neon")

    return inserted

def sync_people(neon_conn, supabase_conn, batch_id, batch_size=1000):
    """Sync people records from Neon to Supabase"""
    neon_cursor = neon_conn.cursor()
    supabase_cursor = supabase_conn.cursor()

    print(f"\n[*] Syncing people (batch: {batch_id})...")

    # Pull people from Neon
    neon_cursor.execute(f"""
        SELECT
            id, unique_id, full_name, first_name, last_name,
            email, phone, title, company_name, company_unique_id,
            linkedin_url, city, state,
            validation_status, reason_code, validation_errors, validation_warnings,
            batch_id as source_batch_id, source_table, created_at
        FROM marketing.people_invalid
        WHERE promoted_to IS NULL
        LIMIT {batch_size}
    """)

    people = neon_cursor.fetchall()
    count = len(people)

    if count == 0:
        print("[*] No people to sync")
        return 0

    print(f"[*] Found {count} people to sync")

    # Insert into Supabase
    inserted = 0
    for person in people:
        try:
            supabase_cursor.execute("""
                INSERT INTO public.people_needs_enrichment (
                    source_id, unique_id, full_name, first_name, last_name,
                    email, phone, title, company_name, company_unique_id,
                    linkedin_url, city, state,
                    validation_status, validation_errors, validation_warnings,
                    source_repo, source_table, batch_id, entity_type,
                    enrichment_source, priority, needs_review,
                    reason_code, pulled_at, imported_at
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (
                str(person[0]),  # source_id
                person[1],  # unique_id
                person[2],  # full_name
                person[3],  # first_name
                person[4],  # last_name
                person[5],  # email
                person[6],  # phone
                person[7],  # title
                person[8],  # company_name
                person[9],  # company_unique_id
                person[10],  # linkedin_url
                person[11],  # city
                person[12],  # state
                'PENDING',  # validation_status
                json.dumps(person[15]) if person[15] else None,  # validation_errors (array -> json)
                json.dumps(person[16]) if person[16] else None,  # validation_warnings (array -> json)
                'barton-outreach-core',  # source_repo
                person[18] or 'marketing.people_invalid',  # source_table
                batch_id,  # batch_id
                'people',  # entity_type
                'external-import',  # enrichment_source
                'medium',  # priority
                True,  # needs_review
                person[14],  # reason_code
                datetime.now(),  # pulled_at
                datetime.now()  # imported_at
            ))
            inserted += 1
        except Exception as e:
            print(f"[!] Error inserting person {person[0]}: {e}")

    supabase_conn.commit()
    print(f"[+] Inserted {inserted}/{count} people to Supabase")

    # Mark as promoted in Neon
    people_ids = [p[0] for p in people]
    neon_cursor.execute("""
        UPDATE marketing.people_invalid
        SET promoted_to = 'enrichment-hub',
            promoted_at = NOW()
        WHERE id = ANY(%s)
    """, (people_ids,))
    neon_conn.commit()

    print(f"[+] Marked {len(people_ids)} people as promoted in Neon")

    return inserted

def main():
    neon_url = os.getenv('DATABASE_URL')
    supabase_url = os.getenv('SUPABASE_DB_URL')

    if not neon_url or not supabase_url:
        print("[-] Missing DATABASE_URL or SUPABASE_DB_URL in .env")
        return

    print("\n" + "="*60)
    print("  NEON -> SUPABASE ENRICHMENT SYNC")
    print("="*60)

    try:
        # Connect to both databases
        print("\n[*] Connecting to Neon...")
        neon_conn = psycopg2.connect(neon_url)

        print("[*] Connecting to Supabase...")
        supabase_conn = psycopg2.connect(supabase_url)

        # Generate batch ID
        batch_id = generate_batch_id()
        print(f"[*] Batch ID: {batch_id}")

        # Sync companies
        company_count = sync_companies(neon_conn, supabase_conn, batch_id)

        # Sync people
        people_count = sync_people(neon_conn, supabase_conn, batch_id)

        # Summary
        total = company_count + people_count
        print("\n" + "="*60)
        print("  SYNC COMPLETE")
        print("="*60)
        print(f"  Companies synced:  {company_count:4d}")
        print(f"  People synced:     {people_count:4d}")
        print(f"  Total records:     {total:4d}")
        print(f"  Batch ID:          {batch_id}")
        print("="*60)
        print("\n[+] Records now available in Supabase for enrichment!")
        print(f"[*] Supabase URL: {os.getenv('SUPABASE_URL')}")
        print("\n")

        neon_conn.close()
        supabase_conn.close()

    except Exception as e:
        print(f"\n[-] Sync failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
