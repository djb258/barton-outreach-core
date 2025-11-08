#!/usr/bin/env python3
"""
Move unmapped people to people_invalid for manual validation

These are people whose titles don't match CEO/CFO/HR patterns.
They need manual review to determine if they should fill slots.
"""

import os, sys, psycopg2, psycopg2.extras, json, uuid
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

def main():
    batch_id = f"UNMAPPED-{datetime.now().strftime('%Y%m%d-%H%M%S')}-{uuid.uuid4().hex[:8]}"

    conn = psycopg2.connect(os.getenv('DATABASE_URL'))
    conn.autocommit = False
    cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

    try:
        print("=" * 70)
        print("Move Unmapped People to Invalid for Validation")
        print("=" * 70)
        print(f"\nBatch ID: {batch_id}\n")

        # Find people NOT mapped to any slot
        cursor.execute("""
            SELECT
                pm.unique_id,
                pm.full_name,
                pm.first_name,
                pm.last_name,
                pm.email,
                pm.work_phone_e164,
                pm.personal_phone_e164,
                pm.title,
                pm.linkedin_url,
                pm.company_unique_id,
                cm.company_name
            FROM marketing.people_master pm
            JOIN marketing.company_master cm ON pm.company_unique_id = cm.company_unique_id
            WHERE pm.unique_id NOT IN (
                SELECT person_unique_id
                FROM marketing.company_slot
                WHERE is_filled = TRUE
                AND person_unique_id IS NOT NULL
            )
            AND pm.title IS NOT NULL
            ORDER BY pm.title
        """)

        unmapped_people = cursor.fetchall()
        total = len(unmapped_people)

        print(f"Found {total} unmapped people with titles\n")

        if total == 0:
            print("No unmapped people to process")
            return

        print(f"{'Person':30} | {'Title':50} | {'Company':40}")
        print("-" * 130)

        moved_count = 0

        for person in unmapped_people:
            name_display = (person['full_name'][:30] if person['full_name'] else '')
            title_display = (person['title'][:50] if person['title'] else '(no title)')
            company_display = (person['company_name'][:40] if person['company_name'] else '')

            print(f"{name_display:30} | {title_display:50} | {company_display:40}")

            # Insert to people_invalid
            reason_code = "Title does not match CEO/CFO/HR patterns"
            validation_errors = [
                "Manual review needed",
                f"Title: {person['title']}",
                "Determine if this person should fill CEO, CFO, or HR slot",
                "Or if title patterns need expansion"
            ]

            cursor.execute("""
                INSERT INTO marketing.people_invalid (
                    unique_id, full_name, first_name, last_name,
                    email, phone, title, linkedin_url,
                    company_unique_id, validation_status,
                    reason_code, validation_errors, validation_warnings,
                    failed_at, batch_id, source_table
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, 'NEEDS_REVIEW', %s, %s, %s, now(), %s, 'marketing.people_master')
                ON CONFLICT (unique_id) DO UPDATE SET
                    reason_code = EXCLUDED.reason_code,
                    validation_errors = EXCLUDED.validation_errors,
                    batch_id = EXCLUDED.batch_id,
                    failed_at = now(),
                    validation_status = 'NEEDS_REVIEW'
            """, (
                person['unique_id'],
                person['full_name'],
                person['first_name'],
                person['last_name'],
                person['email'],
                person['work_phone_e164'] or person['personal_phone_e164'],
                person['title'],
                person['linkedin_url'],
                person['company_unique_id'],
                reason_code,
                json.dumps(validation_errors),
                json.dumps(["Unmapped to slot - needs manual classification"]),
                batch_id
            ))

            moved_count += 1

        conn.commit()

        print(f"\n[OK] Moved {moved_count} unmapped people to people_invalid")
        print(f"\nBatch ID: {batch_id}")

        # Show summary
        cursor.execute("""
            SELECT COUNT(*) FROM marketing.people_invalid
            WHERE batch_id = %s
        """, (batch_id,))
        count = cursor.fetchone()[0]

        print(f"\n=== NEXT STEPS ===")
        print(f"1. Review {count} people in people_invalid table")
        print(f"2. For each person, determine:")
        print(f"   - Should they fill a CEO slot?")
        print(f"   - Should they fill a CFO slot?")
        print(f"   - Should they fill an HR slot?")
        print(f"   - Or are they truly non-executive roles?")
        print(f"\n3. Once validated, move back to people_master")
        print(f"4. Re-run slot mapping to fill remaining slots")
        print(f"\nQuery to review:")
        print(f"SELECT unique_id, full_name, title, validation_errors")
        print(f"FROM marketing.people_invalid")
        print(f"WHERE batch_id = '{batch_id}'")
        print(f"ORDER BY title;")

    except Exception as e:
        conn.rollback()
        print(f"\n[FAIL] Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    finally:
        cursor.close()
        conn.close()

if __name__ == '__main__':
    main()
