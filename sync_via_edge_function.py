#!/usr/bin/env python3
"""
Pull data from Neon and push to Supabase via Edge Function
Uses the n8n webhook proxy for clean API-based sync
"""
import psycopg2
import requests
import os
import json
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

# Configuration
NEON_DB_URL = os.getenv('DATABASE_URL')
EDGE_FUNCTION_URL = "https://sfkgilgjmfqfjlvgdhzt.supabase.co/functions/v1/n8n-webhook-proxy"
SUPABASE_ANON_KEY = os.getenv('SUPABASE_ANON_KEY')

def pull_companies_from_neon(limit=10):
    """Pull company records from Neon that haven't been promoted"""
    print(f"\n[*] Connecting to Neon database...")

    conn = psycopg2.connect(NEON_DB_URL)
    cursor = conn.cursor()

    # Get companies that haven't been promoted yet
    cursor.execute(f"""
        SELECT
            id, company_unique_id, company_name, domain, industry,
            employee_count, website, phone, address, city, state, zip,
            validation_status, reason_code
        FROM marketing.company_invalid
        WHERE promoted_to IS NULL OR promoted_to != 'lovable-edge-function'
        LIMIT {limit}
    """)

    companies = cursor.fetchall()
    conn.close()

    # Transform to edge function format
    records = []
    company_ids = []

    for company in companies:
        company_ids.append(company[0])
        records.append({
            "company_name": company[2],
            "website": company[6] or company[3],  # Use website or domain
            "industry": company[4],
            "hq_city": company[9],  # Map city to hq_city
            "validated": False,
            "validation_source": "barton-outreach-core"
        })

    print(f"[+] Found {len(records)} companies in Neon")
    return records, company_ids

def pull_people_from_neon(limit=10):
    """Pull people records from Neon that haven't been promoted"""
    print(f"\n[*] Connecting to Neon database...")

    conn = psycopg2.connect(NEON_DB_URL)
    cursor = conn.cursor()

    # Get people that haven't been promoted yet
    cursor.execute(f"""
        SELECT
            id, unique_id, full_name, first_name, last_name,
            email, phone, title, company_name, company_unique_id,
            linkedin_url, city, state, validation_status, reason_code
        FROM marketing.people_invalid
        WHERE promoted_to IS NULL OR promoted_to != 'lovable-edge-function'
        LIMIT {limit}
    """)

    people = cursor.fetchall()
    conn.close()

    # Transform to edge function format
    records = []
    people_ids = []

    for person in people:
        people_ids.append(person[0])
        records.append({
            "first_name": person[3],
            "last_name": person[4],
            "email": person[5],
            "title": person[7],
            "company_name": person[8],
            "linkedin_url": person[10],
            "validated": False,
            "validation_source": "barton-outreach-core"
        })

    print(f"[+] Found {len(records)} people in Neon")
    return records, people_ids

def push_to_edge_function(entity, records):
    """Push records to Supabase via edge function"""
    print(f"\n[*] Pushing {len(records)} {entity} records to edge function...")

    payload = {
        "entity": entity,
        "state": "PENDING",
        "source_repo": "barton-outreach-core",
        "records": records
    }

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {SUPABASE_ANON_KEY}"
    }

    try:
        response = requests.post(EDGE_FUNCTION_URL, headers=headers, json=payload, timeout=60)

        print(f"[*] Response Status: {response.status_code}")

        if response.status_code == 200:
            result = response.json()
            print(f"[+] Success!")
            print(f"    Batch ID: {result.get('batch_id')}")
            print(f"    Records Received: {result.get('records_received')}")
            print(f"    Records Inserted: {result.get('records_inserted')}")

            if result.get('errors'):
                print(f"[!] Some errors occurred:")
                for error in result.get('errors', []):
                    print(f"    - {error}")

            return True, result.get('batch_id')
        else:
            print(f"[-] Error: {response.text}")
            return False, None

    except Exception as e:
        print(f"[-] Request failed: {e}")
        return False, None

def mark_as_promoted(entity, ids):
    """Mark source records as promoted in Neon"""
    print(f"\n[*] Marking {len(ids)} {entity} records as promoted in Neon...")

    conn = psycopg2.connect(NEON_DB_URL)
    cursor = conn.cursor()

    table = "marketing.company_invalid" if entity == "companies" else "marketing.people_invalid"

    cursor.execute(f"""
        UPDATE {table}
        SET promoted_to = 'lovable-edge-function',
            promoted_at = NOW()
        WHERE id = ANY(%s)
    """, (ids,))

    conn.commit()
    updated_count = cursor.rowcount
    conn.close()

    print(f"[+] Marked {updated_count} records as promoted")
    return updated_count

def main():
    if not NEON_DB_URL:
        print("[-] DATABASE_URL not found in .env")
        return

    if not SUPABASE_ANON_KEY:
        print("[-] SUPABASE_ANON_KEY not found in .env")
        print("[*] Get it from: https://supabase.com/dashboard/project/sfkgilgjmfqfjlvgdhzt/settings/api")
        return

    print("\n" + "="*60)
    print("  NEON -> LOVABLE SYNC VIA EDGE FUNCTION")
    print("="*60)
    print(f"\n[*] Edge Function: {EDGE_FUNCTION_URL}")

    total_synced = 0

    # Sync companies
    company_records, company_ids = pull_companies_from_neon(limit=50)

    if company_records:
        success, batch_id = push_to_edge_function("companies", company_records)

        if success:
            mark_as_promoted("companies", company_ids)
            total_synced += len(company_records)

    # Sync people
    people_records, people_ids = pull_people_from_neon(limit=50)

    if people_records:
        success, batch_id = push_to_edge_function("people", people_records)

        if success:
            mark_as_promoted("people", people_ids)
            total_synced += len(people_records)

    # Summary
    print("\n" + "="*60)
    print("  SYNC COMPLETE")
    print("="*60)
    print(f"  Companies synced: {len(company_records) if company_records else 0:4d}")
    print(f"  People synced:    {len(people_records) if people_records else 0:4d}")
    print(f"  Total records:    {total_synced:4d}")
    print("="*60)

    if total_synced > 0:
        print("\n[+] Records now in Lovable Supabase!")
        print("[*] View at: https://supabase.com/dashboard/project/sfkgilgjmfqfjlvgdhzt/editor")
    else:
        print("\n[!] No new records to sync")
        print("[*] All records already promoted to Lovable")

if __name__ == "__main__":
    main()
