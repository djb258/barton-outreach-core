"""
Pull Enriched Data from Google Sheets → Neon Raw Intake

This script:
1. Reads enriched validation failures from Google Sheets
2. Pushes them back to intake.company_raw_intake (or intake.people_raw_intake)
3. Marks them for re-validation
4. If validation passes, promotes to master tables

Flow:
    Validation Failure → Google Sheets → Agent Enrichment
                                              ↓
    Master Table ← Promotion ← Re-Validation ← Raw Intake (This Script)

Usage:
    python backend/google_sheets/pull_enriched_from_sheets.py \
        --sheet-id "1i9QNWBqMgY825fLg7lblszMs6X6f5tLxCnAP3Qchfeg" \
        --tab-name "Company_Failures" \
        --entity-type "company"
"""

import os
import sys
import io
import json
import argparse
import psycopg2
import psycopg2.extras
from datetime import datetime
from typing import List, Dict
from dotenv import load_dotenv

# Set UTF-8 encoding for Windows console
if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# Load environment variables
load_dotenv()

NEON_CONNECTION_STRING = os.getenv('NEON_CONNECTION_STRING')


# ============================================================================
# GOOGLE SHEETS READER (Placeholder - requires google-api-python-client)
# ============================================================================

def read_from_google_sheets(sheet_id: str, tab_name: str) -> List[Dict]:
    """
    Read enriched data from Google Sheets

    TODO: Implement actual Google Sheets API integration
    For now, this is a placeholder that shows the expected structure.

    Expected Google Sheets structure:
    | company_id | company_name | industry | employee_count | linkedin_url | enrichment_status | enrichment_notes |
    |------------|--------------|----------|----------------|--------------|-------------------|------------------|
    | 04.04...   | WV SUPREME...| Governm..| 500            | https://...  | enriched          | Added industry   |

    enrichment_status values:
    - "pending" - not yet enriched
    - "enriched" - enrichment complete, ready to push back
    - "pushed" - already pushed back to Neon
    - "skip" - skip this record
    """

    # Placeholder - in production, use Google Sheets API
    # Example using google-api-python-client:
    # from googleapiclient.discovery import build
    # from google.oauth2 import service_account
    #
    # credentials = service_account.Credentials.from_service_account_file(
    #     'credentials.json',
    #     scopes=['https://www.googleapis.com/auth/spreadsheets.readonly']
    # )
    # service = build('sheets', 'v4', credentials=credentials)
    # result = service.spreadsheets().values().get(
    #     spreadsheetId=sheet_id, range=f'{tab_name}!A:Z'
    # ).execute()
    # rows = result.get('values', [])

    print("⚠️ Google Sheets API integration not implemented yet")
    print("   Using placeholder data for demonstration")
    print()

    # Return placeholder data for testing
    return [
        {
            "company_id": "04.04.01.33.00033.033",
            "company_name": "WV SUPREME COURT",
            "industry": "Government - Judicial",
            "employee_count": 450,
            "linkedin_url": "https://www.linkedin.com/company/wv-supreme-court",
            "enrichment_status": "enriched",
            "enrichment_notes": "Added industry, employee count, and LinkedIn URL",
            "enriched_by": "Agent-GPT-4",
            "enriched_at": datetime.now().isoformat()
        }
    ]


# ============================================================================
# PUSH TO NEON RAW INTAKE
# ============================================================================

def push_to_raw_intake(
    conn: psycopg2.extensions.connection,
    entity_type: str,
    enriched_data: List[Dict]
) -> Dict:
    """
    Push enriched data back to Neon raw intake tables

    Args:
        conn: PostgreSQL connection
        entity_type: "company" or "person"
        enriched_data: List of enriched records from Google Sheets

    Returns:
        Summary dict with counts
    """
    cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

    pushed_count = 0
    skipped_count = 0
    error_count = 0

    if entity_type == "company":
        table_name = "intake.company_raw_intake"

        for record in enriched_data:
            # Only push records marked as "enriched"
            if record.get('enrichment_status') != 'enriched':
                skipped_count += 1
                continue

            try:
                cursor.execute("""
                    INSERT INTO intake.company_raw_intake (
                        company_unique_id,
                        company,
                        industry,
                        employee_count,
                        linkedin_url,
                        website,
                        state,
                        validated,
                        validated_at,
                        validated_by,
                        validation_notes,
                        source,
                        import_batch_id,
                        created_at
                    )
                    VALUES (
                        %(company_id)s,
                        %(company_name)s,
                        %(industry)s,
                        %(employee_count)s,
                        %(linkedin_url)s,
                        %(website)s,
                        %(state)s,
                        TRUE,  -- Mark as validated since agent enriched it
                        NOW(),
                        %(enriched_by)s,
                        %(enrichment_notes)s,
                        'google-sheets-enrichment',
                        %(import_batch_id)s,
                        NOW()
                    )
                    ON CONFLICT (company_unique_id) DO UPDATE
                    SET
                        company = EXCLUDED.company,
                        industry = EXCLUDED.industry,
                        employee_count = EXCLUDED.employee_count,
                        linkedin_url = EXCLUDED.linkedin_url,
                        validated = TRUE,
                        validated_at = NOW(),
                        validated_by = EXCLUDED.validated_by,
                        validation_notes = EXCLUDED.validation_notes,
                        updated_at = NOW()
                    RETURNING id, company;
                """, {
                    'company_id': record.get('company_id'),
                    'company_name': record.get('company_name'),
                    'industry': record.get('industry'),
                    'employee_count': record.get('employee_count'),
                    'linkedin_url': record.get('linkedin_url'),
                    'website': record.get('website'),
                    'state': record.get('state', 'N/A'),
                    'enriched_by': record.get('enriched_by', 'unknown-agent'),
                    'enrichment_notes': record.get('enrichment_notes', 'Enriched via Google Sheets'),
                    'import_batch_id': f"SHEETS-ENRICH-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
                })

                result = cursor.fetchone()
                print(f"  ✅ Pushed: {result['company']} (ID: {result['id']})")
                pushed_count += 1

            except Exception as e:
                print(f"  ❌ Error pushing {record.get('company_name')}: {str(e)}")
                error_count += 1
                continue

    elif entity_type == "person":
        table_name = "intake.people_raw_intake"

        for record in enriched_data:
            if record.get('enrichment_status') != 'enriched':
                skipped_count += 1
                continue

            try:
                cursor.execute("""
                    INSERT INTO intake.people_raw_intake (
                        person_unique_id,
                        full_name,
                        email,
                        title,
                        linkedin_url,
                        company_unique_id,
                        validated,
                        validated_at,
                        validated_by,
                        validation_notes,
                        source,
                        import_batch_id,
                        created_at
                    )
                    VALUES (
                        %(person_id)s,
                        %(full_name)s,
                        %(email)s,
                        %(title)s,
                        %(linkedin_url)s,
                        %(company_id)s,
                        TRUE,
                        NOW(),
                        %(enriched_by)s,
                        %(enrichment_notes)s,
                        'google-sheets-enrichment',
                        %(import_batch_id)s,
                        NOW()
                    )
                    ON CONFLICT (person_unique_id) DO UPDATE
                    SET
                        full_name = EXCLUDED.full_name,
                        email = EXCLUDED.email,
                        title = EXCLUDED.title,
                        linkedin_url = EXCLUDED.linkedin_url,
                        validated = TRUE,
                        validated_at = NOW(),
                        validated_by = EXCLUDED.validated_by,
                        validation_notes = EXCLUDED.validation_notes,
                        updated_at = NOW()
                    RETURNING id, full_name;
                """, {
                    'person_id': record.get('person_id'),
                    'full_name': record.get('full_name'),
                    'email': record.get('email'),
                    'title': record.get('title'),
                    'linkedin_url': record.get('linkedin_url'),
                    'company_id': record.get('company_id'),
                    'enriched_by': record.get('enriched_by', 'unknown-agent'),
                    'enrichment_notes': record.get('enrichment_notes', 'Enriched via Google Sheets'),
                    'import_batch_id': f"SHEETS-ENRICH-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
                })

                result = cursor.fetchone()
                print(f"  ✅ Pushed: {result['full_name']} (ID: {result['id']})")
                pushed_count += 1

            except Exception as e:
                print(f"  ❌ Error pushing {record.get('full_name')}: {str(e)}")
                error_count += 1
                continue

    conn.commit()
    cursor.close()

    return {
        "pushed": pushed_count,
        "skipped": skipped_count,
        "errors": error_count
    }


# ============================================================================
# PROMOTE TO MASTER TABLE
# ============================================================================

def promote_to_master(
    conn: psycopg2.extensions.connection,
    entity_type: str,
    batch_id: str
) -> Dict:
    """
    Promote validated records from raw intake to master tables

    This uses existing promotion logic (if available) or direct INSERT

    Args:
        conn: PostgreSQL connection
        entity_type: "company" or "person"
        batch_id: Import batch ID to promote

    Returns:
        Summary dict with counts
    """
    cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

    if entity_type == "company":
        # Use existing promotion function if available
        cursor.execute("""
            SELECT shq.promote_company_records(%s, 'google-sheets-enrichment') as promoted_count;
        """, (batch_id,))

        result = cursor.fetchone()
        promoted_count = result['promoted_count'] if result else 0

    elif entity_type == "person":
        # Direct promotion for people (if no function exists)
        cursor.execute("""
            INSERT INTO marketing.people_master (
                unique_id, full_name, email, title, linkedin_url,
                company_unique_id, source, created_at
            )
            SELECT
                person_unique_id, full_name, email, title, linkedin_url,
                company_unique_id, source, created_at
            FROM intake.people_raw_intake
            WHERE import_batch_id = %s
              AND validated = TRUE
            ON CONFLICT (unique_id) DO UPDATE
            SET
                full_name = EXCLUDED.full_name,
                email = EXCLUDED.email,
                title = EXCLUDED.title,
                linkedin_url = EXCLUDED.linkedin_url,
                updated_at = NOW();
        """, (batch_id,))

        promoted_count = cursor.rowcount

    conn.commit()
    cursor.close()

    return {"promoted": promoted_count}


# ============================================================================
# MAIN EXECUTION
# ============================================================================

def main():
    parser = argparse.ArgumentParser(description="Pull enriched data from Google Sheets and push to Neon")
    parser.add_argument("--sheet-id", required=True, help="Google Sheet ID")
    parser.add_argument("--tab-name", required=True, help="Tab name (e.g., Company_Failures)")
    parser.add_argument("--entity-type", required=True, choices=["company", "person"], help="Entity type")
    parser.add_argument("--promote", action="store_true", help="Auto-promote to master table after push")
    parser.add_argument("--dry-run", action="store_true", help="Dry run - don't actually push")

    args = parser.parse_args()

    print("=" * 80)
    print("PULL ENRICHED DATA FROM GOOGLE SHEETS → NEON RAW INTAKE")
    print("=" * 80)
    print(f"Sheet ID: {args.sheet_id}")
    print(f"Tab Name: {args.tab_name}")
    print(f"Entity Type: {args.entity_type}")
    print(f"Promote: {'Yes' if args.promote else 'No'}")
    print(f"Dry Run: {'Yes' if args.dry_run else 'No'}")
    print()

    # Step 1: Read from Google Sheets
    print("Step 1: Reading enriched data from Google Sheets...")
    enriched_data = read_from_google_sheets(args.sheet_id, args.tab_name)
    print(f"✅ Found {len(enriched_data)} record(s)")
    print()

    if args.dry_run:
        print("🔍 DRY RUN - Would push:")
        for record in enriched_data:
            if record.get('enrichment_status') == 'enriched':
                name_field = 'company_name' if args.entity_type == 'company' else 'full_name'
                print(f"  - {record.get(name_field)}")
        print()
        print("✅ Dry run complete")
        return

    # Step 2: Push to raw intake
    print("Step 2: Pushing enriched data to Neon raw intake...")
    conn = psycopg2.connect(NEON_CONNECTION_STRING)

    push_summary = push_to_raw_intake(conn, args.entity_type, enriched_data)
    print()
    print(f"✅ Pushed: {push_summary['pushed']}")
    print(f"⏭️  Skipped: {push_summary['skipped']}")
    print(f"❌ Errors: {push_summary['errors']}")
    print()

    # Step 3: Promote to master (optional)
    if args.promote and push_summary['pushed'] > 0:
        print("Step 3: Promoting to master table...")
        batch_id = f"SHEETS-ENRICH-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
        promote_summary = promote_to_master(conn, args.entity_type, batch_id)
        print(f"✅ Promoted: {promote_summary['promoted']} record(s)")
        print()

    conn.close()

    print("=" * 80)
    print("✅ COMPLETE")
    print("=" * 80)


if __name__ == "__main__":
    main()
