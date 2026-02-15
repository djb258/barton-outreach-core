"""
Fill people.company_slot with Hunter contacts from multiple CSV sources.

This script:
1. Processes contacts from multiple CSV files
2. Identifies slot types (CEO, CFO, HR) by job title
3. Creates/updates people.people_master records
4. Fills people.company_slot with matched contacts
5. Reports statistics on slots filled and phone numbers added

Author: Database Operations
Date: 2026-02-07
"""

import os
import sys
import csv
import psycopg2
from psycopg2.extras import RealDictCursor
import uuid
from datetime import datetime
from typing import Dict, List, Tuple, Optional
import re

# Database connection configuration
DB_CONFIG = {
    'host': os.getenv('NEON_HOST'),
    'database': os.getenv('NEON_DATABASE'),
    'user': os.getenv('NEON_USER'),
    'password': os.getenv('NEON_PASSWORD'),
    'port': 5432,
    'sslmode': 'require'
}

# Slot type identification patterns
# Order matters: Check more specific patterns first (CFO/HR) before CEO
SLOT_PATTERNS = {
    'CFO': [
        r'\bCFO\b', r'\bChief Financial Officer\b', r'\bVP Finance\b',
        r'\bVice President.*Finance\b', r'\bController\b', r'\bTreasurer\b',
        r'\bFinance Director\b', r'\bFinancial Director\b',
        r'\bVice President.*Financial\b'
    ],
    'HR': [
        r'\bHR\b', r'\bHuman Resources\b', r'\bChief People Officer\b',
        r'\bVP People\b', r'\bCHRO\b', r'\bPeople Operations\b',
        r'\bVice President.*People\b', r'\bVice President.*Human Resources\b',
        r'\bHR Director\b', r'\bDirector.*Human Resources\b',
        r'\bPeople Director\b'
    ],
    'CEO': [
        r'\bCEO\b', r'\bChief Executive Officer\b',
        r'\b(President(?! of ))\b',  # President but not "President of"
        r'\bOwner\b', r'\bFounder\b', r'\bManaging Director\b',
        r'\bGeneral Manager\b', r'\bExecutive Director\b',
        r'\bCompany President\b'
    ]
}


def identify_slot_type(job_title: Optional[str]) -> Optional[str]:
    """
    Identify slot type from job title.
    Checks CFO and HR patterns first (more specific), then CEO (broader).

    Args:
        job_title: The job title string

    Returns:
        Slot type (CEO, CFO, HR) or None if no match
    """
    if not job_title:
        return None

    # Check in specific order: CFO, HR, then CEO
    # This ensures "Vice President Finance" matches CFO, not CEO
    for slot_type in ['CFO', 'HR', 'CEO']:
        patterns = SLOT_PATTERNS.get(slot_type, [])
        for pattern in patterns:
            if re.search(pattern, job_title, re.IGNORECASE):
                return slot_type

    return None


def parse_csv_row_hunter(row: Dict) -> Optional[Dict]:
    """
    Parse a row from Hunter CSV format (invalid-patterns and hunter_enriched files).

    Args:
        row: CSV row as dictionary

    Returns:
        Parsed contact data or None if invalid
    """
    email = row.get('Email address', '').strip()
    if not email or '@' not in email:
        return None

    outreach_id = row.get('outreach_id', '').strip()
    if not outreach_id:
        return None

    job_title = row.get('Job title', '').strip()
    slot_type = identify_slot_type(job_title)

    if not slot_type:
        return None

    return {
        'outreach_id': outreach_id,
        'email': email.lower(),
        'first_name': row.get('First name', '').strip(),
        'last_name': row.get('Last name', '').strip(),
        'job_title': job_title,
        'linkedin_url': row.get('LinkedIn URL', '').strip(),
        'phone_number': row.get('Phone number', '').strip(),
        'slot_type': slot_type,
        'source': 'hunter'
    }


def parse_csv_row_clay(row: Dict) -> Optional[Dict]:
    """
    Parse a row from Clay CSV format.

    Args:
        row: CSV row as dictionary

    Returns:
        Parsed contact data or None if invalid
    """
    outreach_id = row.get('outreach_id', '').strip()
    if not outreach_id:
        return None

    contacts = []

    # Process CEO
    ceo_email = row.get('CEO Email', '').strip()
    if ceo_email and ceo_email != '❌ No Email Found' and '@' in ceo_email:
        ceo_info = row.get('CEO', '')
        name_parts = extract_name_from_clay_format(ceo_info)
        contacts.append({
            'outreach_id': outreach_id,
            'email': ceo_email.lower(),
            'first_name': name_parts['first_name'],
            'last_name': name_parts['last_name'],
            'job_title': name_parts['job_title'],
            'linkedin_url': name_parts['linkedin_url'],
            'phone_number': '',
            'slot_type': 'CEO',
            'source': 'clay'
        })

    # Process CFO
    cfo_email = row.get('CFO Email', '').strip()
    if cfo_email and cfo_email != '❌ No Email Found' and '@' in cfo_email:
        cfo_info = row.get('CFO', '')
        name_parts = extract_name_from_clay_format(cfo_info)
        contacts.append({
            'outreach_id': outreach_id,
            'email': cfo_email.lower(),
            'first_name': name_parts['first_name'],
            'last_name': name_parts['last_name'],
            'job_title': name_parts['job_title'],
            'linkedin_url': name_parts['linkedin_url'],
            'phone_number': '',
            'slot_type': 'CFO',
            'source': 'clay'
        })

    # Process HR Leader
    hr_email = row.get('HR Leader Email', '').strip()
    if hr_email and hr_email != '❌ No Email Found' and '@' in hr_email:
        hr_info = row.get('HR Leader', '')
        name_parts = extract_name_from_clay_format(hr_info)
        contacts.append({
            'outreach_id': outreach_id,
            'email': hr_email.lower(),
            'first_name': name_parts['first_name'],
            'last_name': name_parts['last_name'],
            'job_title': name_parts['job_title'],
            'linkedin_url': name_parts['linkedin_url'],
            'phone_number': '',
            'slot_type': 'HR',
            'source': 'clay'
        })

    return contacts if contacts else None


def extract_name_from_clay_format(info_str: str) -> Dict:
    """
    Extract name, title, and LinkedIn from Clay format string.
    Format: "First Last | Job Title | No email | https://linkedin.com/..."

    Args:
        info_str: Clay formatted info string

    Returns:
        Dictionary with extracted fields
    """
    parts = info_str.split('|')

    result = {
        'first_name': '',
        'last_name': '',
        'job_title': '',
        'linkedin_url': ''
    }

    if len(parts) >= 1:
        name = parts[0].strip()
        name_parts = name.split()
        if name_parts:
            result['first_name'] = name_parts[0]
            if len(name_parts) > 1:
                result['last_name'] = ' '.join(name_parts[1:])

    if len(parts) >= 2:
        result['job_title'] = parts[1].strip()

    if len(parts) >= 4:
        linkedin = parts[3].strip()
        if linkedin.startswith('http'):
            result['linkedin_url'] = linkedin

    return result


def generate_barton_person_id(sequential_num: int) -> str:
    """
    Generate Barton doctrine-compliant person ID.
    Format: 04.04.02.XX.NNNNNN.NNN

    Args:
        sequential_num: Sequential number for this person

    Returns:
        Barton ID string
    """
    # Hub: 04.04.02 (People Intelligence)
    # Cohort: 99 (Hunter import)
    # Sequential: up to 999999
    # Checksum: last 3 digits of sequential
    checksum = sequential_num % 1000
    return f"04.04.02.99.{sequential_num:06d}.{checksum:03d}"


def get_next_person_id_number(cursor) -> int:
    """
    Get the next available sequential number for person ID.

    Args:
        cursor: Database cursor

    Returns:
        Next sequential number
    """
    # Get max sequential number from existing IDs
    cursor.execute("""
        SELECT MAX(
            CAST(
                SPLIT_PART(unique_id, '.', 5) AS INTEGER
            )
        ) as max_seq
        FROM people.people_master
        WHERE unique_id LIKE '04.04.02.99.%'
    """)

    result = cursor.fetchone()
    max_seq = result['max_seq'] if result and result['max_seq'] else 0

    return max_seq + 1


def get_or_create_person(cursor, contact: Dict) -> str:
    """
    Get existing unique_id or create new person in people_master.

    Args:
        cursor: Database cursor
        contact: Contact data dictionary

    Returns:
        unique_id (text)
    """
    # Check if person exists by email
    cursor.execute("""
        SELECT unique_id
        FROM people.people_master
        WHERE LOWER(email) = %s
        LIMIT 1
    """, (contact['email'].lower(),))

    result = cursor.fetchone()

    if result:
        return str(result['unique_id'])

    # Get company_unique_id for this outreach_id
    # Join outreach.outreach (sovereign_id) -> cl.company_identity (sovereign_company_id -> company_unique_id)
    cursor.execute("""
        SELECT ci.company_unique_id
        FROM outreach.outreach o
        JOIN cl.company_identity ci ON o.sovereign_id = ci.sovereign_company_id
        WHERE o.outreach_id = %s
    """, (contact['outreach_id'],))

    company_result = cursor.fetchone()
    if not company_result:
        raise ValueError(f"No company found for outreach_id {contact['outreach_id']}")

    company_unique_id = company_result['company_unique_id']

    # Create new person with Barton ID format
    next_seq = get_next_person_id_number(cursor)
    person_id = generate_barton_person_id(next_seq)

    # Generate slot unique ID (hub 04.04.05 format for slots)
    slot_unique_id = f"04.04.05.99.{next_seq:06d}.{(next_seq % 1000):03d}"

    # Determine phone number (prefer work phone)
    work_phone = contact.get('phone_number', '').strip() if contact.get('phone_number') else None

    cursor.execute("""
        INSERT INTO people.people_master (
            unique_id,
            company_unique_id,
            company_slot_unique_id,
            first_name,
            last_name,
            title,
            email,
            work_phone_e164,
            linkedin_url,
            source_system,
            promoted_from_intake_at,
            created_at,
            updated_at,
            last_verified_at
        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, NOW(), NOW(), NOW(), NOW())
        RETURNING unique_id
    """, (
        person_id,
        company_unique_id,
        slot_unique_id,
        contact['first_name'] or 'Unknown',
        contact['last_name'] or 'Unknown',
        contact['job_title'] or None,
        contact['email'],
        work_phone,
        contact['linkedin_url'] or None,
        contact['source']
    ))

    result = cursor.fetchone()
    return str(result['unique_id'])


def fill_company_slot(cursor, contact: Dict, person_id: str) -> Tuple[bool, bool]:
    """
    Fill company_slot with person data.

    Args:
        cursor: Database cursor
        contact: Contact data dictionary
        person_id: unique_id from people_master

    Returns:
        Tuple of (slot_filled: bool, phone_added: bool)
    """
    # Find unfilled slot for this outreach_id and slot_type
    cursor.execute("""
        SELECT slot_id, slot_phone
        FROM people.company_slot
        WHERE outreach_id = %s
          AND slot_type = %s
          AND (is_filled = FALSE OR is_filled IS NULL)
        ORDER BY created_at ASC
        LIMIT 1
    """, (contact['outreach_id'], contact['slot_type']))

    slot = cursor.fetchone()

    if not slot:
        return (False, False)

    slot_id = slot['slot_id']
    existing_phone = slot['slot_phone']

    # Update slot
    phone_number = contact.get('phone_number', '').strip()
    has_phone = bool(phone_number)
    phone_added = has_phone and not existing_phone

    cursor.execute("""
        UPDATE people.company_slot
        SET
            person_unique_id = %s,
            is_filled = TRUE,
            filled_at = NOW(),
            confidence_score = 1.0,
            source_system = %s,
            slot_phone = COALESCE(NULLIF(%s, ''), slot_phone),
            slot_phone_source = CASE
                WHEN NULLIF(%s, '') IS NOT NULL AND slot_phone IS NULL
                THEN %s
                ELSE slot_phone_source
            END,
            slot_phone_updated_at = CASE
                WHEN NULLIF(%s, '') IS NOT NULL AND slot_phone IS NULL
                THEN NOW()
                ELSE slot_phone_updated_at
            END,
            updated_at = NOW()
        WHERE slot_id = %s
    """, (
        person_id,
        contact['source'],
        phone_number,
        phone_number,
        contact['source'],
        phone_number,
        slot_id
    ))

    return (True, phone_added)


def process_csv_file(file_path: str, file_type: str, conn) -> Dict:
    """
    Process a CSV file and fill slots.

    Args:
        file_path: Path to CSV file
        file_type: 'hunter' or 'clay'
        conn: Database connection

    Returns:
        Statistics dictionary
    """
    stats = {
        'total_rows': 0,
        'contacts_processed': 0,
        'ceo_filled': 0,
        'cfo_filled': 0,
        'hr_filled': 0,
        'phones_added': 0,
        'errors': 0
    }

    print(f"\nProcessing {file_path} (type: {file_type})...")

    # Debug counters
    debug_stats = {
        'contacts_with_slot_type': 0,
        'contacts_with_ceo': 0,
        'contacts_with_cfo': 0,
        'contacts_with_hr': 0
    }

    with open(file_path, 'r', encoding='utf-8', errors='replace') as f:
        reader = csv.DictReader(f)

        with conn.cursor(cursor_factory=RealDictCursor) as cursor:
            for row in reader:
                stats['total_rows'] += 1

                try:
                    # Parse based on file type
                    if file_type == 'hunter':
                        contact = parse_csv_row_hunter(row)
                        contacts = [contact] if contact else []
                    else:  # clay
                        contacts = parse_csv_row_clay(row) or []

                    # Process each contact
                    for contact in contacts:
                        if not contact:
                            continue

                        # Debug: track slot types found
                        debug_stats['contacts_with_slot_type'] += 1
                        if contact['slot_type'] == 'CEO':
                            debug_stats['contacts_with_ceo'] += 1
                        elif contact['slot_type'] == 'CFO':
                            debug_stats['contacts_with_cfo'] += 1
                        elif contact['slot_type'] == 'HR':
                            debug_stats['contacts_with_hr'] += 1

                        # Get or create person
                        person_id = get_or_create_person(cursor, contact)

                        # Fill slot
                        slot_filled, phone_added = fill_company_slot(cursor, contact, person_id)

                        if slot_filled:
                            stats['contacts_processed'] += 1

                            if contact['slot_type'] == 'CEO':
                                stats['ceo_filled'] += 1
                            elif contact['slot_type'] == 'CFO':
                                stats['cfo_filled'] += 1
                            elif contact['slot_type'] == 'HR':
                                stats['hr_filled'] += 1

                            if phone_added:
                                stats['phones_added'] += 1

                    # Commit every 50 rows (more frequent for better progress tracking)
                    if stats['total_rows'] % 50 == 0:
                        conn.commit()
                        print(f"  Processed {stats['total_rows']} rows... "
                              f"({stats['contacts_processed']} slots filled, "
                              f"CEO:{stats['ceo_filled']}, CFO:{stats['cfo_filled']}, "
                              f"HR:{stats['hr_filled']}, Phones:{stats['phones_added']})",
                              flush=True)

                except Exception as e:
                    stats['errors'] += 1
                    if stats['errors'] <= 10:  # Only print first 10 errors
                        print(f"  Error processing row {stats['total_rows']}: {e}", flush=True)
                    elif stats['errors'] == 11:
                        print(f"  (Suppressing further error messages...)", flush=True)
                    conn.rollback()

            # Final commit
            conn.commit()

    # Print debug stats
    print(f"\n  Debug Stats:")
    print(f"    Contacts with slot type: {debug_stats['contacts_with_slot_type']}")
    print(f"    CEO candidates: {debug_stats['contacts_with_ceo']}")
    print(f"    CFO candidates: {debug_stats['contacts_with_cfo']}")
    print(f"    HR candidates: {debug_stats['contacts_with_hr']}")

    return stats


def main():
    """Main execution function."""
    csv_files = [
        (r'C:\Users\CUSTOM PC\Desktop\invalid-patterns-1-2131126.csv', 'hunter'),
        (r'C:\Users\CUSTOM PC\Desktop\Cursor Builds\barton-outreach-core\exports\hunter_enriched_with_email.csv', 'hunter'),
        (r'C:\Users\CUSTOM PC\Desktop\Cursor Builds\barton-outreach-core\exports\clay_has_email_actionable.csv', 'clay')
    ]

    # Verify files exist
    for file_path, _ in csv_files:
        if not os.path.exists(file_path):
            print(f"ERROR: File not found: {file_path}")
            return 1

    # Connect to database
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        print("Connected to Neon PostgreSQL database")
    except Exception as e:
        print(f"ERROR: Failed to connect to database: {e}")
        return 1

    try:
        # Process each file
        total_stats = {
            'total_rows': 0,
            'contacts_processed': 0,
            'ceo_filled': 0,
            'cfo_filled': 0,
            'hr_filled': 0,
            'phones_added': 0,
            'errors': 0
        }

        for file_path, file_type in csv_files:
            stats = process_csv_file(file_path, file_type, conn)

            # Aggregate stats
            for key in total_stats:
                total_stats[key] += stats[key]

            # Print file stats
            print(f"\n  File Stats:")
            print(f"    Total rows: {stats['total_rows']}")
            print(f"    Contacts processed: {stats['contacts_processed']}")
            print(f"    CEO slots filled: {stats['ceo_filled']}")
            print(f"    CFO slots filled: {stats['cfo_filled']}")
            print(f"    HR slots filled: {stats['hr_filled']}")
            print(f"    Phone numbers added: {stats['phones_added']}")
            print(f"    Errors: {stats['errors']}")

        # Print total stats
        print("\n" + "="*60)
        print("TOTAL STATISTICS")
        print("="*60)
        print(f"Total rows processed: {total_stats['total_rows']}")
        print(f"Total contacts matched: {total_stats['contacts_processed']}")
        print(f"CEO slots filled: {total_stats['ceo_filled']}")
        print(f"CFO slots filled: {total_stats['cfo_filled']}")
        print(f"HR slots filled: {total_stats['hr_filled']}")
        print(f"Phone numbers added: {total_stats['phones_added']}")
        print(f"Errors encountered: {total_stats['errors']}")
        print("="*60)

        # Query final slot status
        with conn.cursor(cursor_factory=RealDictCursor) as cursor:
            cursor.execute("""
                SELECT
                    slot_type,
                    COUNT(*) as total_slots,
                    SUM(CASE WHEN is_filled = TRUE THEN 1 ELSE 0 END) as filled_slots,
                    SUM(CASE WHEN slot_phone IS NOT NULL THEN 1 ELSE 0 END) as slots_with_phone,
                    ROUND(100.0 * SUM(CASE WHEN is_filled = TRUE THEN 1 ELSE 0 END) / COUNT(*), 1) as fill_rate
                FROM people.company_slot
                WHERE slot_type IN ('CEO', 'CFO', 'HR')
                GROUP BY slot_type
                ORDER BY slot_type
            """)

            print("\nFINAL SLOT STATUS:")
            print("-" * 60)
            for row in cursor.fetchall():
                print(f"{row['slot_type']}: {row['filled_slots']}/{row['total_slots']} filled "
                      f"({row['fill_rate']}%), {row['slots_with_phone']} with phone")

    except Exception as e:
        print(f"ERROR: {e}")
        conn.rollback()
        return 1

    finally:
        conn.close()

    return 0


if __name__ == '__main__':
    sys.exit(main())
