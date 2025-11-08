#!/usr/bin/env python3
"""
Test n8n Webhook Proxy Edge Function
Sends sample data to Supabase edge function
"""
import requests
import os
from dotenv import load_dotenv

load_dotenv()

# Edge function URL
EDGE_FUNCTION_URL = "https://sfkgilgjmfqfjlvgdhzt.supabase.co/functions/v1/n8n-webhook-proxy"

# Get Supabase anon key from .env
SUPABASE_ANON_KEY = os.getenv('SUPABASE_ANON_KEY')

if not SUPABASE_ANON_KEY:
    print("[-] SUPABASE_ANON_KEY not found in .env")
    print("[*] Add this to .env:")
    print("    SUPABASE_ANON_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...")
    exit(1)

def test_company_insert():
    """Test inserting company records via edge function"""
    print("\n[*] Testing company insert...")

    payload = {
        "entity": "company",
        "state": "PENDING",
        "source_repo": "test-script",
        "batch_id": "TEST-BATCH-001",
        "records": [
            {
                "company_name": "Edge Function Test Company",
                "domain": "edgetest.com",
                "industry": "Technology",
                "employee_count": 100,
                "location": "Charleston, WV",
                "city": "Charleston",
                "state": "WV"
            },
            {
                "company_name": "Another Test Company",
                "domain": "anothertest.com",
                "industry": "Consulting",
                "employee_count": 50,
                "location": "Morgantown, WV",
                "city": "Morgantown",
                "state": "WV"
            }
        ]
    }

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {SUPABASE_ANON_KEY}"
    }

    try:
        response = requests.post(EDGE_FUNCTION_URL, headers=headers, json=payload, timeout=30)

        print(f"[*] Status Code: {response.status_code}")

        if response.status_code == 200:
            result = response.json()
            print(f"[+] Success!")
            print(f"    Entity: {result.get('entity')}")
            print(f"    Batch ID: {result.get('batch_id')}")
            print(f"    Records Received: {result.get('records_received')}")
            print(f"    Records Inserted: {result.get('records_inserted')}")

            if result.get('errors'):
                print(f"[!] Errors occurred:")
                for error in result['errors']:
                    print(f"    - {error}")
        else:
            print(f"[-] Error: {response.text}")

        return response.status_code == 200

    except Exception as e:
        print(f"[-] Request failed: {e}")
        return False

def test_people_insert():
    """Test inserting people records via edge function"""
    print("\n[*] Testing people insert...")

    payload = {
        "entity": "people",
        "state": "PENDING",
        "source_repo": "test-script",
        "batch_id": "TEST-BATCH-002",
        "records": [
            {
                "first_name": "Jane",
                "last_name": "Smith",
                "email": "jane.smith@edgetest.com",
                "phone": "(555) 123-4567",
                "title": "CEO",
                "company_name": "Edge Function Test Company",
                "city": "Charleston",
                "state": "WV"
            },
            {
                "first_name": "Bob",
                "last_name": "Johnson",
                "email": "bob.johnson@anothertest.com",
                "title": "CTO",
                "company_name": "Another Test Company",
                "city": "Morgantown",
                "state": "WV"
            }
        ]
    }

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {SUPABASE_ANON_KEY}"
    }

    try:
        response = requests.post(EDGE_FUNCTION_URL, headers=headers, json=payload, timeout=30)

        print(f"[*] Status Code: {response.status_code}")

        if response.status_code == 200:
            result = response.json()
            print(f"[+] Success!")
            print(f"    Entity: {result.get('entity')}")
            print(f"    Batch ID: {result.get('batch_id')}")
            print(f"    Records Received: {result.get('records_received')}")
            print(f"    Records Inserted: {result.get('records_inserted')}")

            if result.get('errors'):
                print(f"[!] Errors occurred:")
                for error in result['errors']:
                    print(f"    - {error}")
        else:
            print(f"[-] Error: {response.text}")

        return response.status_code == 200

    except Exception as e:
        print(f"[-] Request failed: {e}")
        return False

def main():
    print("\n" + "="*60)
    print("  SUPABASE EDGE FUNCTION TEST")
    print("  n8n Webhook Proxy")
    print("="*60)

    print(f"\n[*] Edge Function URL: {EDGE_FUNCTION_URL}")
    print(f"[*] Using Anon Key: {SUPABASE_ANON_KEY[:20]}...")

    # Test company insert
    company_success = test_company_insert()

    # Test people insert
    people_success = test_people_insert()

    # Summary
    print("\n" + "="*60)
    print("  TEST SUMMARY")
    print("="*60)
    print(f"  Company Insert: {'✓ PASSED' if company_success else '✗ FAILED'}")
    print(f"  People Insert:  {'✓ PASSED' if people_success else '✗ FAILED'}")
    print("="*60)

    if company_success and people_success:
        print("\n[+] All tests passed!")
        print("[*] Check Supabase dashboard to verify records")
        print(f"[*] https://supabase.com/dashboard/project/sfkgilgjmfqfjlvgdhzt/editor")
    else:
        print("\n[!] Some tests failed")
        print("[*] Check edge function logs:")
        print("    supabase functions logs n8n-webhook-proxy")

if __name__ == "__main__":
    main()
