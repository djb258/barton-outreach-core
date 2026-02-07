#!/usr/bin/env python3
"""
Fill Slots from Hunter CSV
==========================
Fills people.company_slot with contacts from Hunter-enriched CSVs.

This script:
1. Reads Hunter CSV with outreach_id, email, name, job title, phone
2. Matches contacts to slot types (CEO, CFO, HR) by job title
3. Creates people_master records if needed
4. Links people to slots via outreach_id
5. Adds phone numbers to slot_phone column

Usage:
    doppler run -- python fill_slots_from_hunter.py <csv_path> [--dry-run]

Created: 2026-02-07
"""

import os
import sys
import csv
from datetime import datetime
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass

# Barton ID prefix for People Intelligence hub
BARTON_PREFIX = "04.04.02"
BARTON_YEAR = "26"  # 2026

# Windows encoding fix
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')


# =============================================================================
# JOB TITLE TO SLOT TYPE MAPPING
# =============================================================================

CEO_KEYWORDS = [
    'ceo', 'chief executive', 'president', 'owner', 'founder',
    'managing director', 'general manager', 'principal', 'chairman',
    'chairwoman', 'chair ', 'co-founder', 'cofounder'
]

CFO_KEYWORDS = [
    'cfo', 'chief financial', 'vp finance', 'vice president finance',
    'controller', 'treasurer', 'finance director', 'director of finance',
    'evp/cfo', 'svp finance', 'head of finance'
]

HR_KEYWORDS = [
    'hr', 'human resources', 'chief people', 'vp people', 'chro',
    'people operations', 'talent', 'chief hr', 'director of hr',
    'svp human resources', 'vp human resources', 'head of hr',
    'head of people', 'shrm', 'sphr', 'phr'
]


def get_slot_type(job_title: str) -> Optional[str]:
    """Determine slot type from job title."""
    if not job_title:
        return None

    title_lower = job_title.lower()

    # Check CFO first (more specific than CEO keywords like "president")
    for keyword in CFO_KEYWORDS:
        if keyword in title_lower:
            return 'CFO'

    # Check HR
    for keyword in HR_KEYWORDS:
        if keyword in title_lower:
            return 'HR'

    # Check CEO last
    for keyword in CEO_KEYWORDS:
        if keyword in title_lower:
            return 'CEO'

    return None


# =============================================================================
# DATA CLASSES
# =============================================================================

@dataclass
class HunterContact:
    """Contact from Hunter CSV."""
    outreach_id: str
    email: str
    first_name: str
    last_name: str
    job_title: str
    phone_number: Optional[str]
    linkedin_url: Optional[str]
    domain: str
    company_name: str
    slot_type: Optional[str] = None


@dataclass
class FillStats:
    """Statistics for slot filling."""
    total_rows: int = 0
    contacts_with_slot_type: int = 0
    ceo_candidates: int = 0
    cfo_candidates: int = 0
    hr_candidates: int = 0
    people_created: int = 0
    slots_filled: int = 0
    ceo_filled: int = 0
    cfo_filled: int = 0
    hr_filled: int = 0
    phones_added: int = 0
    slots_already_filled: int = 0
    no_slot_found: int = 0
    errors: List[str] = None

    def __post_init__(self):
        if self.errors is None:
            self.errors = []


# =============================================================================
# DATABASE CONNECTION
# =============================================================================

def get_connection():
    """Get database connection from DATABASE_URL."""
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        print("[FAIL] DATABASE_URL not set")
        sys.exit(1)

    import psycopg2
    return psycopg2.connect(database_url)


def get_next_barton_id(cursor) -> str:
    """Generate next Barton ID for people_master.

    Format: 04.04.02.YY.NNNNNN.NNN
    - 04.04.02 = People Intelligence hub
    - YY = year (26 for 2026)
    - NNNNNN = sequence number (1-6 digits)
    - NNN = last 3 digits of sequence
    """
    # Get current max sequence for this year
    cursor.execute("""
        SELECT MAX(
            CAST(SPLIT_PART(unique_id, '.', 5) AS INTEGER)
        )
        FROM people.people_master
        WHERE unique_id LIKE %s
    """, (f"{BARTON_PREFIX}.{BARTON_YEAR}.%",))

    result = cursor.fetchone()[0]
    next_seq = (result or 0) + 1

    # Generate ID: 04.04.02.26.NNNNNN.NNN
    suffix = str(next_seq)[-3:].zfill(3)
    return f"{BARTON_PREFIX}.{BARTON_YEAR}.{next_seq}.{suffix}"


# =============================================================================
# CORE FUNCTIONS
# =============================================================================

def load_contacts_from_csv(csv_path: str) -> List[HunterContact]:
    """Load contacts from Hunter CSV and filter by slot type."""
    contacts = []

    with open(csv_path, 'r', encoding='utf-8', errors='replace') as f:
        reader = csv.DictReader(f)
        for row in reader:
            # Extract fields with multiple column name conventions
            # Support both Hunter format and slot_contacts format
            outreach_id = (row.get('outreach_id') or '').strip()
            email = (row.get('Email address') or row.get('email') or '').strip().lower()
            first_name = (row.get('First name') or row.get('First Name') or row.get('first_name') or '').strip()
            last_name = (row.get('Last name') or row.get('Last Name') or row.get('last_name') or '').strip()
            job_title = (row.get('Job title') or row.get('Position raw') or row.get('job_title') or '').strip()
            phone_number = (row.get('Phone number') or row.get('phone') or '').strip()
            linkedin_url = (row.get('LinkedIn URL') or row.get('linkedin') or '').strip()
            domain = (row.get('domain') or row.get('Domain name') or '').strip()
            company_name = (row.get('company_name') or row.get('Organization') or '').strip()

            # Check if slot_type is already in CSV (slot_contacts format)
            csv_slot_type = (row.get('slot_type') or '').strip().upper()

            # Skip rows without required fields
            if not outreach_id or not email or not first_name:
                continue

            # Determine slot type - use CSV value if present, otherwise detect from job title
            if csv_slot_type in ['CEO', 'CFO', 'HR']:
                slot_type = csv_slot_type
            else:
                slot_type = get_slot_type(job_title)

            contact = HunterContact(
                outreach_id=outreach_id,
                email=email,
                first_name=first_name,
                last_name=last_name,
                job_title=job_title,
                phone_number=phone_number if phone_number else None,
                linkedin_url=linkedin_url if linkedin_url else None,
                domain=domain,
                company_name=company_name,
                slot_type=slot_type
            )
            contacts.append(contact)

    return contacts


def fill_slots(contacts: List[HunterContact], conn, stats: FillStats, dry_run: bool = False) -> None:
    """Fill slots with contacts."""
    cursor = conn.cursor()

    # Filter to only contacts with slot types
    slot_contacts = [c for c in contacts if c.slot_type]
    stats.contacts_with_slot_type = len(slot_contacts)

    # Count by type
    for c in slot_contacts:
        if c.slot_type == 'CEO':
            stats.ceo_candidates += 1
        elif c.slot_type == 'CFO':
            stats.cfo_candidates += 1
        elif c.slot_type == 'HR':
            stats.hr_candidates += 1

    print(f"\nProcessing {len(slot_contacts)} contacts with CEO/CFO/HR titles...")
    print(f"  CEO candidates: {stats.ceo_candidates}")
    print(f"  CFO candidates: {stats.cfo_candidates}")
    print(f"  HR candidates: {stats.hr_candidates}")

    if dry_run:
        print("\n[DRY RUN] No changes will be made to the database.")

    processed = 0
    for contact in slot_contacts:
        processed += 1
        if processed % 500 == 0:
            print(f"  Processed {processed}/{len(slot_contacts)}...")
            if not dry_run:
                conn.commit()

        try:
            # Step 1: Check if slot exists for this outreach_id + slot_type
            cursor.execute("""
                SELECT slot_id, person_unique_id, is_filled, slot_phone, company_unique_id
                FROM people.company_slot
                WHERE outreach_id = %s AND slot_type = %s
            """, (contact.outreach_id, contact.slot_type))

            slot_row = cursor.fetchone()

            if not slot_row:
                stats.no_slot_found += 1
                continue

            slot_id, current_person_id, is_filled, current_phone, company_unique_id = slot_row

            # Skip if already filled
            if is_filled and current_person_id:
                stats.slots_already_filled += 1
                continue

            if dry_run:
                stats.slots_filled += 1
                if contact.slot_type == 'CEO':
                    stats.ceo_filled += 1
                elif contact.slot_type == 'CFO':
                    stats.cfo_filled += 1
                elif contact.slot_type == 'HR':
                    stats.hr_filled += 1
                if contact.phone_number:
                    stats.phones_added += 1
                continue

            # Step 2: Create or get person in people_master
            cursor.execute("""
                SELECT unique_id FROM people.people_master
                WHERE LOWER(email) = %s
            """, (contact.email,))

            person_row = cursor.fetchone()

            if person_row:
                person_id = person_row[0]
            else:
                # Create new person (need company_unique_id from slot)
                if not company_unique_id:
                    stats.errors.append(f"{contact.email}: no company_unique_id on slot")
                    continue

                person_id = get_next_barton_id(cursor)
                cursor.execute("""
                    INSERT INTO people.people_master (
                        unique_id, company_unique_id, company_slot_unique_id,
                        first_name, last_name, email,
                        title, linkedin_url, work_phone_e164, source_system, created_at
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, NOW())
                """, (
                    person_id,
                    company_unique_id,
                    slot_id,
                    contact.first_name,
                    contact.last_name,
                    contact.email,
                    contact.job_title,
                    contact.linkedin_url,
                    contact.phone_number,
                    'hunter'
                ))
                stats.people_created += 1

            # Step 3: Update slot
            if contact.phone_number:
                cursor.execute("""
                    UPDATE people.company_slot
                    SET person_unique_id = %s,
                        is_filled = TRUE,
                        filled_at = NOW(),
                        source_system = 'hunter',
                        slot_phone = %s,
                        slot_phone_source = 'hunter',
                        slot_phone_updated_at = NOW()
                    WHERE slot_id = %s
                """, (person_id, contact.phone_number, slot_id))
                stats.phones_added += 1
            else:
                cursor.execute("""
                    UPDATE people.company_slot
                    SET person_unique_id = %s,
                        is_filled = TRUE,
                        filled_at = NOW(),
                        source_system = 'hunter'
                    WHERE slot_id = %s
                """, (person_id, slot_id))

            stats.slots_filled += 1
            if contact.slot_type == 'CEO':
                stats.ceo_filled += 1
            elif contact.slot_type == 'CFO':
                stats.cfo_filled += 1
            elif contact.slot_type == 'HR':
                stats.hr_filled += 1

        except Exception as e:
            stats.errors.append(f"{contact.email}: {str(e)}")
            conn.rollback()

    if not dry_run:
        conn.commit()

    cursor.close()


# =============================================================================
# MAIN
# =============================================================================

def main():
    if len(sys.argv) < 2:
        print("Usage: python fill_slots_from_hunter.py <csv_path> [--dry-run]")
        print("")
        print("Options:")
        print("  --dry-run    Show what would be done without making changes")
        sys.exit(1)

    csv_path = sys.argv[1]
    dry_run = '--dry-run' in sys.argv

    if not os.path.exists(csv_path):
        print(f"[ERROR] File not found: {csv_path}")
        sys.exit(1)

    print("="*60)
    print("FILL SLOTS FROM HUNTER CSV")
    print("="*60)
    print(f"CSV: {csv_path}")
    print(f"Dry run: {dry_run}")
    print(f"Started: {datetime.now().isoformat()}")

    # Load contacts
    print("\nLoading contacts from CSV...")
    contacts = load_contacts_from_csv(csv_path)

    stats = FillStats(total_rows=len(contacts))
    print(f"  Total rows: {stats.total_rows}")

    # Connect to database
    print("\nConnecting to database...")
    conn = get_connection()
    print("  Connected!")

    # Fill slots
    fill_slots(contacts, conn, stats, dry_run)

    conn.close()

    # Summary
    print("\n" + "="*60)
    print("SUMMARY")
    print("="*60)
    print(f"  Total rows in CSV: {stats.total_rows}")
    print(f"  Contacts with CEO/CFO/HR title: {stats.contacts_with_slot_type}")
    print(f"    - CEO candidates: {stats.ceo_candidates}")
    print(f"    - CFO candidates: {stats.cfo_candidates}")
    print(f"    - HR candidates: {stats.hr_candidates}")
    print(f"")
    print(f"  People created: {stats.people_created}")
    print(f"  Slots filled: {stats.slots_filled}")
    print(f"    - CEO slots: {stats.ceo_filled}")
    print(f"    - CFO slots: {stats.cfo_filled}")
    print(f"    - HR slots: {stats.hr_filled}")
    print(f"  Phone numbers added: {stats.phones_added}")
    print(f"")
    print(f"  Slots already filled: {stats.slots_already_filled}")
    print(f"  No slot found for outreach_id: {stats.no_slot_found}")

    if stats.errors:
        print(f"\n  Errors ({len(stats.errors)}):")
        for err in stats.errors[:10]:
            print(f"    - {err}")

    print(f"\nCompleted: {datetime.now().isoformat()}")


if __name__ == "__main__":
    main()
