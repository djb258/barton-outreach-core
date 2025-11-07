"""
Trigger Enrichment Process for Companies
Runs Apify leads-finder and logs to pipeline_events
"""
import os
import sys
from pathlib import Path
from dotenv import load_dotenv
import psycopg2
from psycopg2.extras import RealDictCursor
import requests
import json
from datetime import datetime

if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')
    sys.stdout.reconfigure(line_buffering=True)  # Enable line buffering
    sys.stderr.reconfigure(line_buffering=True)

# Load environment - find project root by looking for .git directory
project_root = Path(__file__).resolve()
while not (project_root / ".git").exists() and project_root != project_root.parent:
    project_root = project_root.parent
env_path = project_root / ".env"
load_dotenv(env_path)
print("[DEBUG] Environment loaded", flush=True)

DATABASE_URL = os.getenv('NEON_DATABASE_URL') or os.getenv('DATABASE_URL')
APIFY_TOKEN = os.getenv('APIFY_TOKEN') or os.getenv('APIFY_API_KEY')
N8N_BASE_URL = os.getenv('N8N_BASE_URL', 'https://dbarton.app.n8n.cloud')
N8N_API_KEY = os.getenv('N8N_API_KEY')

# Apify Leads Finder actor ID (format: username~actorname)
# This actor finds CEO, CFO, HR executives with LinkedIn profiles
LEADS_FINDER_ACTOR = 'code_crafter~leads-finder'

print("="*70)
print("  COMPANY ENRICHMENT ORCHESTRATOR")
print("="*70)
print()

# Connect to database
print("[DB] Connecting to Neon database...")
conn = psycopg2.connect(DATABASE_URL)
cursor = conn.cursor(cursor_factory=RealDictCursor)

# Get unenriched companies (limit to batch size)
BATCH_SIZE = 5  # Start small for testing
print(f"[QUERY] Fetching {BATCH_SIZE} unenriched companies...")

cursor.execute("""
    SELECT
        company_unique_id,
        company_name,
        website_url,
        COALESCE(state_abbrev, address_state) as state
    FROM marketing.company_master
    WHERE validated_at IS NULL
      AND (state_abbrev = 'WV' OR address_state = 'WV' OR address_state = 'West Virginia')
    ORDER BY created_at DESC
    LIMIT %s
""", (BATCH_SIZE,))

companies = cursor.fetchall()

if not companies:
    print("[INFO] No unenriched companies found!")
    cursor.close()
    conn.close()
    sys.exit(0)

print(f"[OK] Found {len(companies)} companies to enrich\n")

# Display companies
for i, company in enumerate(companies, 1):
    print(f"{i}. {company['company_name']}")
    print(f"   ID: {company['company_unique_id']}")
    print(f"   Website: {company['website_url']}")
    print(f"   State: {company['state']}")
    print()

# Log event helper
def log_pipeline_event(event_type, payload, status='pending', error_msg=None):
    """Log event to pipeline_events table"""
    try:
        cursor.execute("""
            INSERT INTO marketing.pipeline_events
            (event_type, payload, status, error_message, retry_count, created_at)
            VALUES (%s, %s, %s, %s, 0, NOW())
            RETURNING id
        """, (event_type, json.dumps(payload), status, error_msg))
        conn.commit()
        return cursor.fetchone()['id']
    except Exception as e:
        print(f"[ERROR] Failed to log event: {e}")
        conn.rollback()
        return None

# Process each company
print("="*70)
print("  STARTING ENRICHMENT PROCESS")
print("="*70)
print()

results = {
    'total': len(companies),
    'success': 0,
    'failed': 0,
    'errors': []
}

for idx, company in enumerate(companies, 1):
    print(f"\n[{idx}/{len(companies)}] Processing: {company['company_name']}")
    print("-" * 70)

    company_id = company['company_unique_id']
    company_name = company['company_name']
    website = company['website_url']

    # Prepare payload
    payload = {
        'company_id': company_id,
        'company_name': company_name,
        'website': website,
        'trigger_time': datetime.utcnow().isoformat(),
        'batch_id': 'ENRICHMENT-TEST-001'
    }

    # Log start event
    event_id = log_pipeline_event('company_enrichment_started', payload, 'pending')
    print(f"[LOG] Created pipeline event ID: {event_id}")

    # Option 1: Trigger Apify Leads Finder
    if APIFY_TOKEN:
        print(f"[APIFY] Triggering leads-finder for {company_name}...")

        try:
            # Prepare Apify input
            apify_input = {
                "companyName": company_name,
                "website": website,
                "targetRoles": ["CEO", "CFO", "HR Director", "HR Manager"],
                "maxContacts": 10
            }

            # Call Apify API
            apify_url = f"https://api.apify.com/v2/acts/{LEADS_FINDER_ACTOR}/runs"
            headers = {
                "Authorization": f"Bearer {APIFY_TOKEN}",
                "Content-Type": "application/json"
            }
            params = {
                "timeout": 300,
                "waitForFinish": 60  # Wait up to 1 minute
            }

            print(f"[APIFY] Calling API...")
            response = requests.post(
                apify_url,
                headers=headers,
                json=apify_input,
                params=params,
                timeout=70
            )

            if response.status_code == 201 or response.status_code == 200:
                apify_result = response.json()
                run_id = apify_result.get('data', {}).get('id', 'unknown')
                status = apify_result.get('data', {}).get('status', 'unknown')

                print(f"[APIFY] ✓ Run started - ID: {run_id}, Status: {status}")

                # Update event
                log_pipeline_event('company_enrichment_apify', {
                    **payload,
                    'apify_run_id': run_id,
                    'apify_status': status
                }, 'processed')

                results['success'] += 1

                # Mark company as validated
                cursor.execute("""
                    UPDATE marketing.company_master
                    SET validated_at = NOW(), validated_by = 'apify-enrichment'
                    WHERE company_unique_id = %s
                """, (company_id,))
                conn.commit()
                print(f"[DB] ✓ Marked company as validated")

                # Fetch dataset results (contacts found)
                dataset_id = apify_result.get('data', {}).get('defaultDatasetId')
                if dataset_id:
                    print(f"[APIFY] Fetching contacts from dataset {dataset_id}...")
                    dataset_url = f"https://api.apify.com/v2/datasets/{dataset_id}/items"
                    dataset_response = requests.get(dataset_url, headers=headers, timeout=30)

                    if dataset_response.status_code == 200:
                        contacts = dataset_response.json()
                        print(f"[APIFY] Found {len(contacts)} contacts")

                        # Get company slots for CEO, CFO, HR
                        cursor.execute("""
                            SELECT company_slot_unique_id, slot_label
                            FROM marketing.company_slots
                            WHERE company_unique_id = %s
                            AND slot_type = 'executive'
                            ORDER BY slot_label
                        """, (company_id,))
                        slots = cursor.fetchall()
                        slot_map = {slot['slot_label']: slot['company_slot_unique_id'] for slot in slots}

                        # Insert contacts into people_master
                        contacts_inserted = 0
                        for contact in contacts:
                            # Determine slot based on title
                            title = contact.get('title', '').lower()
                            slot_id = None

                            if 'ceo' in title or 'chief executive' in title:
                                slot_id = slot_map.get('CEO')
                            elif 'cfo' in title or 'chief financial' in title:
                                slot_id = slot_map.get('CFO')
                            elif 'hr' in title or 'human resource' in title or 'people' in title:
                                slot_id = slot_map.get('HR Director')

                            if slot_id and contact.get('name'):
                                # Generate unique_id for person
                                person_id = f"{slot_id}.person"

                                try:
                                    cursor.execute("""
                                        INSERT INTO marketing.people_master (
                                            unique_id, company_unique_id, company_slot_unique_id,
                                            first_name, last_name, full_name, title,
                                            email, linkedin_url, source_system,
                                            promoted_from_intake_at, created_at, updated_at
                                        ) VALUES (
                                            %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, NOW(), NOW(), NOW()
                                        )
                                        ON CONFLICT (unique_id) DO UPDATE SET
                                            full_name = EXCLUDED.full_name,
                                            title = EXCLUDED.title,
                                            email = EXCLUDED.email,
                                            linkedin_url = EXCLUDED.linkedin_url,
                                            updated_at = NOW()
                                    """, (
                                        person_id,
                                        company_id,
                                        slot_id,
                                        contact.get('name', '').split()[0] if contact.get('name') else '',
                                        ' '.join(contact.get('name', '').split()[1:]) if contact.get('name') and len(contact.get('name', '').split()) > 1 else '',
                                        contact.get('name'),
                                        contact.get('title'),
                                        contact.get('email'),
                                        contact.get('linkedinUrl'),
                                        'apify-leads-finder'
                                    ))
                                    contacts_inserted += 1
                                except Exception as e:
                                    print(f"[DB] Warning: Could not insert {contact.get('name')}: {e}")

                        conn.commit()
                        print(f"[DB] ✓ Inserted {contacts_inserted} contacts into people_master")
                    else:
                        print(f"[APIFY] Failed to fetch dataset: {dataset_response.status_code}")
                else:
                    print(f"[APIFY] No dataset ID found")

            else:
                error_msg = f"Apify API error: {response.status_code} - {response.text[:200]}"
                print(f"[APIFY] ✗ {error_msg}")
                log_pipeline_event('company_enrichment_failed', payload, 'failed', error_msg)
                results['failed'] += 1
                results['errors'].append(f"{company_name}: {error_msg}")

        except Exception as e:
            error_msg = f"Apify exception: {str(e)}"
            print(f"[APIFY] ✗ {error_msg}")
            log_pipeline_event('company_enrichment_failed', payload, 'failed', error_msg)
            results['failed'] += 1
            results['errors'].append(f"{company_name}: {error_msg}")

    else:
        print("[SKIP] No Apify token configured")
        results['failed'] += 1

    print()

# Final report
print("="*70)
print("  ENRICHMENT REPORT")
print("="*70)
print()
print(f"Total companies processed: {results['total']}")
print(f"✓ Successful: {results['success']}")
print(f"✗ Failed: {results['failed']}")

if results['errors']:
    print("\nErrors:")
    for error in results['errors']:
        print(f"  - {error}")

print("\n" + "="*70)
print("  ENRICHMENT COMPLETE")
print("="*70)

cursor.close()
conn.close()
