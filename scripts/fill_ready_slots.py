#!/usr/bin/env python3
"""
Fill CEO, CFO, and HR slots for companies with email patterns + Hunter contacts.

Doctrine: 04.04.02 (People Intelligence Hub)
Author: Claude Code
Date: 2026-02-05
"""

import os
import psycopg2
import psycopg2.extras
import random
import time
from typing import Dict, List, Tuple

# Title matching patterns
TITLE_PATTERNS = {
    'CEO': ['ceo', 'chief executive', 'president', 'owner', 'founder', 'managing director'],
    'CFO': ['cfo', 'chief financial', 'finance director', 'controller', 'treasurer'],
    'HR': ['hr', 'human resources', 'people operations', 'talent', 'recruiting']
}

def get_db_connection():
    """Create Neon database connection."""
    return psycopg2.connect(os.environ['DATABASE_URL'])

def generate_unique_id() -> str:
    """Generate unique_id in format: 04.04.02.99.NNNNNN.NNN"""
    random_part = random.randint(1, 999999)  # 1-6 digits
    seq_part = int(time.time() * 1000) % 1000  # 3 digits (000-999)
    return f"04.04.02.99.{random_part}.{seq_part:03d}"

def generate_email(first_name: str, last_name: str, domain: str, email_method: str) -> str:
    """Generate email using company's email pattern."""
    first = first_name.lower().strip()
    last = last_name.lower().strip()
    domain_clean = domain.lower().strip()

    # Remove any subdomain (www, etc)
    if domain_clean.startswith('www.'):
        domain_clean = domain_clean[4:]

    patterns = {
        'first.last': f"{first}.{last}@{domain_clean}",
        'firstlast': f"{first}{last}@{domain_clean}",
        'first_last': f"{first}_{last}@{domain_clean}",
        'flast': f"{first[0]}{last}@{domain_clean}",
        'firstl': f"{first}{last[0]}@{domain_clean}",
        'first': f"{first}@{domain_clean}",
        'last.first': f"{last}.{first}@{domain_clean}",
        'lastfirst': f"{last}{first}@{domain_clean}",
        'last_first': f"{last}_{first}@{domain_clean}",
    }

    # Default to first.last if method not recognized
    return patterns.get(email_method, patterns['first.last'])

def match_title(title: str, slot_type: str) -> bool:
    """Check if title matches slot type patterns."""
    if not title:
        return False

    title_lower = title.lower()
    patterns = TITLE_PATTERNS.get(slot_type, [])

    return any(pattern in title_lower for pattern in patterns)

def get_ready_companies(conn) -> List[Tuple]:
    """Get companies with email patterns, Hunter contacts, and empty slots."""
    query = """
    SELECT DISTINCT
        o.outreach_id,
        o.domain,
        ct.email_method,
        o.sovereign_id,
        ci.company_unique_id
    FROM outreach.outreach o
    JOIN outreach.company_target ct ON o.outreach_id = ct.outreach_id
    JOIN enrichment.hunter_contact hc ON LOWER(o.domain) = LOWER(hc.domain)
    JOIN cl.company_identity ci ON ci.sovereign_company_id = o.sovereign_id
    WHERE ct.email_method IS NOT NULL
    AND hc.first_name IS NOT NULL
    AND hc.last_name IS NOT NULL
    AND NOT EXISTS (
        SELECT 1 FROM people.company_slot cs
        WHERE cs.outreach_id = o.outreach_id AND cs.is_filled = true
    )
    ORDER BY o.outreach_id;
    """

    with conn.cursor() as cur:
        cur.execute(query)
        return cur.fetchall()

def get_hunter_contacts(conn, domain: str) -> List[Dict]:
    """Get all Hunter contacts for a domain."""
    query = """
    SELECT first_name, last_name, job_title, position_raw, department
    FROM enrichment.hunter_contact
    WHERE LOWER(domain) = LOWER(%s)
    AND first_name IS NOT NULL
    AND last_name IS NOT NULL;
    """

    with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
        cur.execute(query, (domain,))
        return cur.fetchall()

def get_empty_slots(conn, outreach_id: str) -> List[Dict]:
    """Get unfilled slot types for a company with slot id."""
    query = """
    SELECT slot_type, slot_id, company_unique_id
    FROM people.company_slot
    WHERE outreach_id = %s
    AND is_filled = false
    AND slot_type IN ('CEO', 'CFO', 'HR');
    """

    with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
        cur.execute(query, (outreach_id,))
        return cur.fetchall()

def create_person_and_fill_slot(conn, outreach_id: str, slot_type: str, slot_id: str,
                                 contact: Dict, domain: str, email_method: str, company_unique_id: str, slot_company_unique_id: str) -> bool:
    """Create person record and fill slot."""
    try:
        # Generate unique_id
        unique_id = generate_unique_id()

        # Generate email
        email = generate_email(contact['first_name'], contact['last_name'],
                              domain, email_method)

        # Check if person already exists with this email
        with conn.cursor() as cur:
            cur.execute("""
                SELECT unique_id FROM people.people_master
                WHERE email = %s;
            """, (email,))
            existing = cur.fetchone()

            if existing:
                # Use existing person
                unique_id = existing[0]
            else:
                # Insert into people_master (using slot_id for company_slot_unique_id)
                cur.execute("""
                    INSERT INTO people.people_master (
                        unique_id, company_unique_id, company_slot_unique_id,
                        first_name, last_name, title, email,
                        department, source_system, created_at, updated_at
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, NOW(), NOW())
                    ON CONFLICT (unique_id) DO NOTHING;
                """, (
                    unique_id,
                    slot_company_unique_id,
                    str(slot_id),
                    contact['first_name'],
                    contact['last_name'],
                    contact.get('job_title', ''),
                    email,
                    contact.get('department', ''),
                    'hunter_contact'
                ))

            # Update company_slot
            cur.execute("""
                UPDATE people.company_slot
                SET is_filled = true,
                    person_unique_id = %s,
                    updated_at = NOW()
                WHERE outreach_id = %s
                AND slot_type = %s
                AND is_filled = false;
            """, (unique_id, outreach_id, slot_type))

            if cur.rowcount > 0:
                return True

    except Exception as e:
        print(f"  ERROR filling {slot_type} for {outreach_id}: {e}")
        return False

    return False

def process_companies(conn, companies: List[Tuple]) -> Dict:
    """Process all companies and fill slots."""
    stats = {
        'companies_processed': 0,
        'slots_filled': {'CEO': 0, 'CFO': 0, 'HR': 0},
        'people_created': 0,
        'errors': 0
    }

    import sys
    batch_size = 500
    total = len(companies)

    print(f"\nProcessing {total} companies with LIVE commits every {batch_size} companies...\n")
    sys.stdout.flush()

    for idx, (outreach_id, domain, email_method, sovereign_id, company_unique_id) in enumerate(companies, 1):
        try:
            # Progress every 100 companies
            if idx % 100 == 0:
                print(f"  Processing {idx}/{total}...")
                sys.stdout.flush()

            # Get empty slots for this company
            empty_slots = get_empty_slots(conn, outreach_id)
            if not empty_slots:
                continue

            # Get Hunter contacts
            contacts = get_hunter_contacts(conn, domain)
            if not contacts:
                continue

            # Track slots filled for this company
            company_filled = 0

            # Try to fill each empty slot
            for slot in empty_slots:
                slot_type = slot['slot_type']
                slot_id = slot['slot_id']
                slot_company_unique_id = slot['company_unique_id']

                # Find matching contact
                matched_contact = None
                for contact in contacts:
                    title = contact.get('job_title', '') or contact.get('position_raw', '')
                    if match_title(title, slot_type):
                        matched_contact = contact
                        break

                if matched_contact:
                    if create_person_and_fill_slot(conn, outreach_id, slot_type, slot_id,
                                                   matched_contact, domain, email_method, company_unique_id, slot_company_unique_id):
                        stats['slots_filled'][slot_type] += 1
                        stats['people_created'] += 1
                        company_filled += 1

            if company_filled > 0:
                stats['companies_processed'] += 1

            # Commit every batch_size companies
            if idx % batch_size == 0:
                conn.commit()
                print(f"\n*** BATCH COMMIT at {idx}/{total} ***")
                print(f"CEO: {stats['slots_filled']['CEO']} | "
                      f"CFO: {stats['slots_filled']['CFO']} | "
                      f"HR: {stats['slots_filled']['HR']} | "
                      f"People: {stats['people_created']}\n")
                sys.stdout.flush()

        except Exception as e:
            print(f"  ERROR processing {outreach_id}: {e}")
            sys.stdout.flush()
            stats['errors'] += 1
            try:
                conn.rollback()
            except:
                pass
            continue

    # Final commit
    conn.commit()

    return stats

def main():
    """Main execution."""
    import sys
    print("=" * 80)
    print("SLOT FILLING OPERATION - LIVE MODE")
    print("=" * 80)
    print("\nDoctrine: 04.04.02 (People Intelligence Hub)")
    print("Operation: Fill CEO, CFO, HR slots from Hunter contacts")
    print("Commit Strategy: Batch commits every 500 companies")
    print("\n" + "=" * 80 + "\n")
    sys.stdout.flush()

    print("Connecting to database...")
    sys.stdout.flush()
    conn = get_db_connection()
    print("Connected!")
    sys.stdout.flush()

    try:
        # Get ready companies
        print("Fetching companies with email patterns + Hunter contacts...")
        sys.stdout.flush()
        companies = get_ready_companies(conn)
        print(f"Found {len(companies)} companies ready for slot filling\n")
        sys.stdout.flush()

        if not companies:
            print("No companies found. Exiting.")
            return

        # Process companies
        start_time = time.time()
        stats = process_companies(conn, companies)
        elapsed = time.time() - start_time

        # Final report
        print("\n" + "=" * 80)
        print("FINAL REPORT")
        print("=" * 80)
        print(f"\nCompanies Processed: {stats['companies_processed']}")
        print(f"\nSlots Filled:")
        print(f"  CEO: {stats['slots_filled']['CEO']}")
        print(f"  CFO: {stats['slots_filled']['CFO']}")
        print(f"  HR:  {stats['slots_filled']['HR']}")
        print(f"  TOTAL: {sum(stats['slots_filled'].values())}")
        print(f"\nPeople Created: {stats['people_created']}")
        print(f"Errors: {stats['errors']}")
        print(f"\nElapsed Time: {elapsed:.2f} seconds")
        print(f"Rate: {stats['companies_processed'] / elapsed:.2f} companies/sec")
        print("\n" + "=" * 80)

    except Exception as e:
        print(f"\nFATAL ERROR: {e}")
        conn.rollback()
        raise

    finally:
        conn.close()
        print("\nDatabase connection closed.")

if __name__ == '__main__':
    main()
