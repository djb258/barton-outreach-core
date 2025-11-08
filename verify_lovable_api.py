#!/usr/bin/env python3
"""
Verify data synced to Lovable Supabase using REST API
Check both company_needs_enrichment and people_needs_enrichment tables
"""
import requests
import os
from dotenv import load_dotenv

load_dotenv()

# Lovable Supabase configuration
SUPABASE_URL = "https://sfkgilgjmfqfjlvgdhzt.supabase.co"
SUPABASE_ANON_KEY = os.getenv('SUPABASE_ANON_KEY')

def check_companies():
    """Check company records via REST API"""
    print("\n[*] Checking company_needs_enrichment table...")

    headers = {
        "apikey": SUPABASE_ANON_KEY,
        "Authorization": f"Bearer {SUPABASE_ANON_KEY}"
    }

    # Get count and recent records
    response = requests.get(
        f"{SUPABASE_URL}/rest/v1/company_needs_enrichment",
        headers={**headers, "Prefer": "count=exact"},
        params={
            "select": "*",
            "order": "created_at.desc",
            "limit": 10
        }
    )

    # 200 or 206 (Partial Content) are both success
    if response.status_code in [200, 206]:
        records = response.json()
        content_range = response.headers.get('Content-Range', '0-0/0')
        total = content_range.split('/')[-1]

        print(f"[+] Total companies: {total}")
        print(f"[+] Content-Range: {content_range}")
        print(f"\n[*] Recent 10 companies:")
        for company in records[:10]:
            print(f"    - {company.get('company_name', 'N/A')}")
            print(f"      Website: {company.get('website', 'N/A')}")
            print(f"      Industry: {company.get('industry', 'N/A')}")
            print(f"      City: {company.get('hq_city', 'N/A')}")
            print(f"      Source: {company.get('validation_source', 'N/A')}")
            print(f"      State: {company.get('state', 'N/A')}")
            print(f"      Created: {company.get('created_at', 'N/A')}")
            print()

        return int(total) if total.isdigit() else len(records)
    else:
        print(f"[-] Error: {response.status_code}")
        print(f"    {response.text}")
        return 0

def check_people():
    """Check people records via REST API"""
    print("\n[*] Checking people_needs_enrichment table...")

    headers = {
        "apikey": SUPABASE_ANON_KEY,
        "Authorization": f"Bearer {SUPABASE_ANON_KEY}"
    }

    # Get count and recent records
    response = requests.get(
        f"{SUPABASE_URL}/rest/v1/people_needs_enrichment",
        headers={**headers, "Prefer": "count=exact"},
        params={
            "select": "*",
            "order": "created_at.desc",
            "limit": 10
        }
    )

    # 200 or 206 (Partial Content) are both success
    if response.status_code in [200, 206]:
        records = response.json()
        content_range = response.headers.get('Content-Range', '0-0/0')
        total = content_range.split('/')[-1]

        print(f"[+] Total people: {total}")
        print(f"[+] Content-Range: {content_range}")
        print(f"\n[*] Recent 10 people:")
        for person in records[:10]:
            print(f"    - {person.get('first_name', 'N/A')} {person.get('last_name', 'N/A')}")
            print(f"      Email: {person.get('email', 'N/A')}")
            print(f"      Title: {person.get('title', 'N/A')}")
            print(f"      Company: {person.get('company_name', 'N/A')}")
            print(f"      LinkedIn: {person.get('linkedin_url', 'N/A')}")
            print(f"      Source: {person.get('validation_source', 'N/A')}")
            print(f"      State: {person.get('state', 'N/A')}")
            print(f"      Created: {person.get('created_at', 'N/A')}")
            print()

        return int(total) if total.isdigit() else len(records)
    else:
        print(f"[-] Error: {response.status_code}")
        print(f"    {response.text}")
        return 0

def main():
    if not SUPABASE_ANON_KEY:
        print("[-] SUPABASE_ANON_KEY not found in .env")
        print("[*] Add it to your .env file")
        return

    print("\n" + "="*60)
    print("  LOVABLE SUPABASE VERIFICATION (REST API)")
    print("="*60)
    print(f"\n[*] Project URL: {SUPABASE_URL}")

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
