#!/usr/bin/env python3
"""
WV HR & Benefits - Phase 4: Neon Database Export (Slot-Complete Only)
=====================================================================
Exports ONLY slot-complete people to Neon PostgreSQL.

A person is "slot-complete" when:
  1. company_valid = true (company exists in Company Hub with domain)
  2. person_company_valid = true (person has verified company association)
  3. email_verified = true (email has been verified)

This enforces the Hub-and-Spoke Golden Rule:
  - No spoke data exports without valid company anchor
  - No email exports without verification

Tables:
  - marketing.company_master (companies)
  - marketing.people_master (people/contacts)

Created: 2024-12-10
Updated: 2024-12-11 - Only export slot-complete people
"""

import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Tuple
from dotenv import load_dotenv
import psycopg2

# Load environment
load_dotenv()

# Paths
OUTPUT_DIR = Path(__file__).parent.parent / "output" / "wv_hr_benefits"
COMPANIES_FILE = OUTPUT_DIR / "companies.json"
PEOPLE_FILE = OUTPUT_DIR / "people.json"

# Neon connection
DATABASE_URL = os.getenv('DATABASE_URL') or os.getenv('NEON_DATABASE_URL')


def generate_barton_id(prefix: str, sequence: int) -> str:
    """Generate Barton Doctrine ID format: 04.04.02.04.XXXXX.###"""
    entity_codes = {
        'company': '30000',
        'people': '20000',
    }
    entity_code = entity_codes.get(prefix, '99999')
    return f"04.04.02.04.{entity_code}.{sequence:03d}"


def connect_db():
    """Connect to Neon PostgreSQL"""
    print(f"   Connecting to Neon...")
    conn = psycopg2.connect(DATABASE_URL)
    print(f"   Connected successfully")
    return conn


def ensure_tables_exist(conn):
    """Ensure required tables exist"""
    cur = conn.cursor()

    cur.execute("""
        SELECT schema_name FROM information_schema.schemata
        WHERE schema_name = 'marketing'
    """)
    if not cur.fetchone():
        print("   Creating marketing schema...")
        cur.execute("CREATE SCHEMA IF NOT EXISTS marketing")

    cur.execute("""
        CREATE TABLE IF NOT EXISTS marketing.company_master (
            company_unique_id VARCHAR(50) PRIMARY KEY,
            company_name VARCHAR(500) NOT NULL,
            domain VARCHAR(255),
            industry VARCHAR(255),
            employee_count INTEGER,
            email_pattern VARCHAR(50),
            pattern_confidence DECIMAL(3,2),
            source VARCHAR(100),
            source_file VARCHAR(255),
            created_at TIMESTAMP DEFAULT NOW(),
            updated_at TIMESTAMP DEFAULT NOW()
        )
    """)

    # Review queue table for people who didn't match or didn't get slots
    cur.execute("""
        CREATE TABLE IF NOT EXISTS marketing.review_queue (
            review_id SERIAL PRIMARY KEY,
            person_id VARCHAR(50) NOT NULL,
            full_name VARCHAR(500) NOT NULL,
            job_title VARCHAR(500),
            company_name_raw VARCHAR(500),
            review_reason VARCHAR(50) NOT NULL,
            review_notes TEXT,
            fuzzy_score DECIMAL(5,2),
            fuzzy_matched_company VARCHAR(500),
            matched_company_id VARCHAR(50),
            linkedin_url VARCHAR(500),
            review_status VARCHAR(50) DEFAULT 'pending',
            reviewed_by VARCHAR(255),
            reviewed_at TIMESTAMP,
            resolution VARCHAR(50),
            resolution_notes TEXT,
            source VARCHAR(100),
            source_file VARCHAR(255),
            created_at TIMESTAMP DEFAULT NOW(),
            updated_at TIMESTAMP DEFAULT NOW(),
            UNIQUE(person_id, source_file)
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS marketing.people_master (
            unique_id VARCHAR(50) PRIMARY KEY,
            company_unique_id VARCHAR(50) REFERENCES marketing.company_master(company_unique_id),
            full_name VARCHAR(500) NOT NULL,
            first_name VARCHAR(255),
            last_name VARCHAR(255),
            email VARCHAR(255),
            email_verified BOOLEAN DEFAULT FALSE,
            email_confidence DECIMAL(3,2),
            linkedin_url VARCHAR(500),
            title VARCHAR(500),
            title_seniority VARCHAR(50),
            location VARCHAR(500),
            source VARCHAR(100),
            source_file VARCHAR(255),
            slot_complete BOOLEAN DEFAULT FALSE,
            created_at TIMESTAMP DEFAULT NOW(),
            updated_at TIMESTAMP DEFAULT NOW()
        )
    """)

    # Add slot_complete column if it doesn't exist (for existing tables)
    cur.execute("""
        DO $$
        BEGIN
            IF NOT EXISTS (
                SELECT 1 FROM information_schema.columns
                WHERE table_schema = 'marketing'
                AND table_name = 'people_master'
                AND column_name = 'slot_complete'
            ) THEN
                ALTER TABLE marketing.people_master ADD COLUMN slot_complete BOOLEAN DEFAULT FALSE;
            END IF;
        END $$;
    """)

    # Create indexes
    cur.execute("""
        CREATE INDEX IF NOT EXISTS idx_company_domain
        ON marketing.company_master(domain)
    """)
    cur.execute("""
        CREATE INDEX IF NOT EXISTS idx_people_company
        ON marketing.people_master(company_unique_id)
    """)
    cur.execute("""
        CREATE INDEX IF NOT EXISTS idx_people_email
        ON marketing.people_master(email)
    """)
    cur.execute("""
        CREATE INDEX IF NOT EXISTS idx_people_seniority
        ON marketing.people_master(title_seniority)
    """)
    cur.execute("""
        CREATE INDEX IF NOT EXISTS idx_people_slot_complete
        ON marketing.people_master(slot_complete)
    """)

    # Review queue indexes
    cur.execute("""
        CREATE INDEX IF NOT EXISTS idx_review_reason
        ON marketing.review_queue(review_reason)
    """)
    cur.execute("""
        CREATE INDEX IF NOT EXISTS idx_review_status
        ON marketing.review_queue(review_status)
    """)
    cur.execute("""
        CREATE INDEX IF NOT EXISTS idx_review_source
        ON marketing.review_queue(source_file)
    """)

    conn.commit()
    print("   Tables verified/created")


def check_slot_complete(person: Dict, company: Dict) -> Tuple[bool, List[str]]:
    """
    Check if a person record is slot-complete for export.

    Returns (is_complete, reasons_if_not)
    """
    reasons = []

    # 1. Company must have domain (company_valid)
    if not company.get('domain'):
        reasons.append("company_no_domain")

    # 2. Company must have email pattern (pattern discovered)
    if not company.get('email_pattern'):
        reasons.append("company_no_pattern")

    # 3. Person must have email
    if not person.get('email'):
        reasons.append("person_no_email")

    # 4. Email must be verified
    if not person.get('email_verified'):
        reasons.append("email_not_verified")

    return len(reasons) == 0, reasons


def filter_slot_complete(people: Dict, companies: Dict) -> Tuple[Dict, Dict, List[Dict]]:
    """
    Filter people to only slot-complete records.

    Returns:
        - slot_complete_people: Dict of people ready for export
        - slot_complete_companies: Dict of companies with slot-complete people
        - rejected: List of rejected records with reasons
    """
    slot_complete_people = {}
    slot_complete_companies = {}
    rejected = []

    for person_id, person in people.items():
        company_id = person.get('company_id')
        company = companies.get(company_id, {})

        is_complete, reasons = check_slot_complete(person, company)

        if is_complete:
            slot_complete_people[person_id] = person
            # Also track the company
            if company_id and company_id not in slot_complete_companies:
                slot_complete_companies[company_id] = company
        else:
            rejected.append({
                'person_id': person_id,
                'full_name': person.get('full_name'),
                'company_id': company_id,
                'reasons': reasons
            })

    return slot_complete_people, slot_complete_companies, rejected


def export_companies(conn, companies: Dict) -> Dict[str, str]:
    """Export companies to Neon, return mapping of local_id -> barton_id"""
    cur = conn.cursor()

    cur.execute("""
        SELECT MAX(CAST(SPLIT_PART(company_unique_id, '.', 6) AS INTEGER))
        FROM marketing.company_master
        WHERE company_unique_id LIKE '04.04.02.04.30000.%'
    """)
    result = cur.fetchone()
    sequence = (result[0] or 0) + 1

    id_mapping = {}
    inserted = 0
    updated = 0
    source_file = "WV HR and Benefits.csv"

    for local_id, company in companies.items():
        domain = company.get('domain')

        if domain:
            cur.execute("""
                SELECT company_unique_id FROM marketing.company_master
                WHERE domain = %s
            """, (domain,))
            existing = cur.fetchone()

            if existing:
                barton_id = existing[0]
                cur.execute("""
                    UPDATE marketing.company_master SET
                        email_pattern = COALESCE(%s, email_pattern),
                        pattern_confidence = COALESCE(%s, pattern_confidence),
                        updated_at = NOW()
                    WHERE company_unique_id = %s
                """, (
                    company.get('email_pattern'),
                    company.get('pattern_confidence'),
                    barton_id
                ))
                id_mapping[local_id] = barton_id
                updated += 1
                continue

        barton_id = generate_barton_id('company', sequence)
        sequence += 1

        cur.execute("""
            INSERT INTO marketing.company_master (
                company_unique_id, company_name, domain, email_pattern,
                pattern_confidence, source, source_file, created_at, updated_at
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, NOW(), NOW())
            ON CONFLICT (company_unique_id) DO UPDATE SET
                email_pattern = EXCLUDED.email_pattern,
                pattern_confidence = EXCLUDED.pattern_confidence,
                updated_at = NOW()
        """, (
            barton_id,
            company.get('company_name'),
            domain,
            company.get('email_pattern'),
            company.get('pattern_confidence'),
            'WV_HR_Pipeline',
            source_file
        ))

        id_mapping[local_id] = barton_id
        inserted += 1

    conn.commit()
    print(f"   Companies: {inserted} inserted, {updated} updated")
    return id_mapping


def export_people(conn, people: Dict, company_mapping: Dict) -> Tuple[int, int, int]:
    """Export slot-complete people to Neon"""
    cur = conn.cursor()

    cur.execute("""
        SELECT MAX(CAST(SPLIT_PART(unique_id, '.', 6) AS INTEGER))
        FROM marketing.people_master
        WHERE unique_id LIKE '04.04.02.04.20000.%'
    """)
    result = cur.fetchone()
    sequence = (result[0] or 0) + 1

    inserted = 0
    updated = 0
    skipped = 0
    source_file = "WV HR and Benefits.csv"

    for local_id, person in people.items():
        local_company_id = person.get('company_id')
        company_barton_id = company_mapping.get(local_company_id)

        if not company_barton_id:
            skipped += 1
            continue

        email = person.get('email')
        linkedin_url = person.get('linkedin_url')

        if linkedin_url:
            cur.execute("""
                SELECT unique_id FROM marketing.people_master
                WHERE linkedin_url = %s
            """, (linkedin_url,))
            existing = cur.fetchone()

            if existing:
                barton_id = existing[0]
                cur.execute("""
                    UPDATE marketing.people_master SET
                        email = COALESCE(%s, email),
                        email_verified = COALESCE(%s, email_verified),
                        email_confidence = COALESCE(%s, email_confidence),
                        title = COALESCE(%s, title),
                        title_seniority = COALESCE(%s, title_seniority),
                        slot_complete = TRUE,
                        updated_at = NOW()
                    WHERE unique_id = %s
                """, (
                    email,
                    person.get('email_verified', False),
                    person.get('email_confidence'),
                    person.get('job_title'),
                    person.get('title_seniority'),
                    barton_id
                ))
                updated += 1
                continue

        barton_id = generate_barton_id('people', sequence)
        sequence += 1

        cur.execute("""
            INSERT INTO marketing.people_master (
                unique_id, company_unique_id, full_name, first_name, last_name,
                email, email_verified, email_confidence, linkedin_url,
                title, title_seniority, location, source, source_file,
                slot_complete, created_at, updated_at
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, TRUE, NOW(), NOW())
            ON CONFLICT (unique_id) DO UPDATE SET
                email = EXCLUDED.email,
                email_verified = EXCLUDED.email_verified,
                email_confidence = EXCLUDED.email_confidence,
                title = EXCLUDED.title,
                slot_complete = TRUE,
                updated_at = NOW()
        """, (
            barton_id,
            company_barton_id,
            person.get('full_name'),
            person.get('first_name'),
            person.get('last_name'),
            email,
            person.get('email_verified', False),
            person.get('email_confidence'),
            linkedin_url,
            person.get('job_title'),
            person.get('title_seniority'),
            person.get('location'),
            'WV_HR_Pipeline',
            source_file
        ))

        inserted += 1

    conn.commit()
    print(f"   People: {inserted} inserted, {updated} updated, {skipped} skipped (no company)")
    return inserted, updated, skipped


def export_review_queue(conn, people: Dict, source_file: str = "WV HR and Benefits.csv") -> Tuple[int, int]:
    """
    Export people in review queue to Neon.

    Returns: (inserted, updated)
    """
    cur = conn.cursor()

    inserted = 0
    updated = 0

    for person_id, person in people.items():
        # Only export people in review queue
        if not person.get('in_review_queue'):
            continue

        review_reason = person.get('review_reason', 'unknown')
        review_notes = person.get('review_notes', '')
        fuzzy_score = person.get('fuzzy_score', 0)
        fuzzy_matched_company = person.get('fuzzy_matched_company', '')
        company_id = person.get('company_id', '')

        # Check if already exists
        cur.execute("""
            SELECT review_id FROM marketing.review_queue
            WHERE person_id = %s AND source_file = %s
        """, (person_id, source_file))
        existing = cur.fetchone()

        if existing:
            # Update existing record
            cur.execute("""
                UPDATE marketing.review_queue SET
                    full_name = %s,
                    job_title = %s,
                    company_name_raw = %s,
                    review_reason = %s,
                    review_notes = %s,
                    fuzzy_score = %s,
                    fuzzy_matched_company = %s,
                    matched_company_id = %s,
                    linkedin_url = %s,
                    updated_at = NOW()
                WHERE person_id = %s AND source_file = %s
            """, (
                person.get('full_name'),
                person.get('job_title'),
                person.get('company_name_raw'),
                review_reason,
                review_notes,
                fuzzy_score if fuzzy_score else None,
                fuzzy_matched_company if fuzzy_matched_company else None,
                company_id if company_id else None,
                person.get('linkedin_url'),
                person_id,
                source_file
            ))
            updated += 1
        else:
            # Insert new record
            cur.execute("""
                INSERT INTO marketing.review_queue (
                    person_id, full_name, job_title, company_name_raw,
                    review_reason, review_notes, fuzzy_score, fuzzy_matched_company,
                    matched_company_id, linkedin_url, source, source_file,
                    created_at, updated_at
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, NOW(), NOW())
            """, (
                person_id,
                person.get('full_name'),
                person.get('job_title'),
                person.get('company_name_raw'),
                review_reason,
                review_notes,
                fuzzy_score if fuzzy_score else None,
                fuzzy_matched_company if fuzzy_matched_company else None,
                company_id if company_id else None,
                person.get('linkedin_url'),
                'WV_HR_Pipeline',
                source_file
            ))
            inserted += 1

    conn.commit()
    return inserted, updated


def get_review_queue_stats(conn, source_file: str = "WV HR and Benefits.csv") -> Dict:
    """Get review queue stats"""
    cur = conn.cursor()

    cur.execute("""
        SELECT review_reason, COUNT(*)
        FROM marketing.review_queue
        WHERE source_file = %s
        GROUP BY review_reason
    """, (source_file,))
    reason_counts = dict(cur.fetchall())

    cur.execute("""
        SELECT review_status, COUNT(*)
        FROM marketing.review_queue
        WHERE source_file = %s
        GROUP BY review_status
    """, (source_file,))
    status_counts = dict(cur.fetchall())

    cur.execute("""
        SELECT COUNT(*) FROM marketing.review_queue
        WHERE source_file = %s
    """, (source_file,))
    total = cur.fetchone()[0]

    return {
        'total': total,
        'by_reason': reason_counts,
        'by_status': status_counts
    }


def get_export_stats(conn) -> Dict:
    """Get stats after export"""
    cur = conn.cursor()

    cur.execute("SELECT COUNT(*) FROM marketing.company_master WHERE source = 'WV_HR_Pipeline'")
    total_companies = cur.fetchone()[0]

    cur.execute("SELECT COUNT(*) FROM marketing.people_master WHERE source = 'WV_HR_Pipeline'")
    total_people = cur.fetchone()[0]

    cur.execute("""
        SELECT COUNT(*) FROM marketing.people_master
        WHERE source = 'WV_HR_Pipeline' AND slot_complete = TRUE
    """)
    slot_complete_people = cur.fetchone()[0]

    cur.execute("""
        SELECT COUNT(*) FROM marketing.people_master
        WHERE source = 'WV_HR_Pipeline' AND email_verified = TRUE
    """)
    verified_emails = cur.fetchone()[0]

    cur.execute("""
        SELECT title_seniority, COUNT(*)
        FROM marketing.people_master
        WHERE source = 'WV_HR_Pipeline'
          AND slot_complete = TRUE
          AND title_seniority IN ('chro', 'vp', 'director')
        GROUP BY title_seniority
    """)
    seniority_counts = dict(cur.fetchall())

    return {
        'total_companies': total_companies,
        'total_people': total_people,
        'slot_complete_people': slot_complete_people,
        'verified_emails': verified_emails,
        'chro_count': seniority_counts.get('chro', 0),
        'vp_count': seniority_counts.get('vp', 0),
        'director_count': seniority_counts.get('director', 0)
    }


def main():
    """Main execution"""
    print("\n" + "=" * 60)
    print(" WV HR & BENEFITS - PHASE 4: NEON EXPORT ".center(60))
    print(" (Slot-Complete Only) ".center(60))
    print("=" * 60)

    # Load data
    print("\n[LOADING] Input Files")
    print("=" * 55)

    with open(COMPANIES_FILE, 'r') as f:
        companies = json.load(f)
    print(f"   Loaded: {len(companies)} companies")

    with open(PEOPLE_FILE, 'r') as f:
        people = json.load(f)
    print(f"   Loaded: {len(people)} people")

    # Filter to slot-complete only
    print("\n[FILTERING] Slot-Complete Records")
    print("=" * 55)

    slot_people, slot_companies, rejected = filter_slot_complete(people, companies)

    print(f"   Slot-Complete People: {len(slot_people)}")
    print(f"   Slot-Complete Companies: {len(slot_companies)}")
    print(f"   Rejected (not slot-complete): {len(rejected)}")

    # Rejection breakdown
    rejection_reasons = {}
    for r in rejected:
        for reason in r['reasons']:
            rejection_reasons[reason] = rejection_reasons.get(reason, 0) + 1

    if rejection_reasons:
        print("\n   Rejection Breakdown:")
        for reason, count in sorted(rejection_reasons.items(), key=lambda x: -x[1]):
            print(f"     - {reason}: {count}")

    if len(slot_people) == 0:
        print("\n   [WARN] No slot-complete people to export!")
        print("   Run Phases 2 and 3 first to generate and verify emails.")
        return None

    # Connect to Neon
    print("\n[CONNECTING] Neon PostgreSQL")
    print("=" * 55)
    conn = connect_db()

    # Ensure tables
    print("\n[SETUP] Ensuring Tables")
    print("=" * 55)
    ensure_tables_exist(conn)

    # Export companies (only those with slot-complete people)
    print("\n[EXPORTING] Companies (with slot-complete people)")
    print("=" * 55)
    company_mapping = export_companies(conn, slot_companies)

    # Export slot-complete people only
    print("\n[EXPORTING] Slot-Complete People")
    print("=" * 55)
    people_inserted, people_updated, people_skipped = export_people(conn, slot_people, company_mapping)

    # Export review queue (all people, will filter to in_review_queue=True)
    print("\n[EXPORTING] Review Queue")
    print("=" * 55)
    review_inserted, review_updated = export_review_queue(conn, people)
    print(f"   Review Queue: {review_inserted} inserted, {review_updated} updated")

    # Get stats
    print("\n[STATS] Export Summary")
    print("=" * 55)
    stats = get_export_stats(conn)
    review_stats = get_review_queue_stats(conn)

    # Update progress
    progress_file = OUTPUT_DIR / "progress.json"
    with open(progress_file, 'r') as f:
        progress = json.load(f)

    progress['neon_companies_exported'] = stats['total_companies']
    progress['neon_people_exported'] = stats['total_people']
    progress['neon_slot_complete_exported'] = stats['slot_complete_people']
    progress['rejected_not_slot_complete'] = len(rejected)
    progress['current_phase'] = 'export_complete'
    progress['status'] = 'complete'
    progress['phase4_completed_at'] = datetime.now(timezone.utc).isoformat()
    progress['export_mode'] = 'slot_complete_only'

    with open(progress_file, 'w') as f:
        json.dump(progress, f, indent=2)

    # Close connection
    conn.close()

    # Print dashboard
    print("\n")
    print("+" + "=" * 62 + "+")
    print("|" + " WV HR & BENEFITS - NEON EXPORT COMPLETE ".center(62) + "|")
    print("|" + " (Slot-Complete Only) ".center(62) + "|")
    print("+" + "=" * 62 + "+")

    print("|" + " DATABASE RECORDS ".center(62, "-") + "|")
    print("|" + f"   Companies in Neon: {stats['total_companies']}".ljust(62) + "|")
    print("|" + f"   Total People in Neon: {stats['total_people']}".ljust(62) + "|")
    print("|" + f"   Slot-Complete People: {stats['slot_complete_people']}".ljust(62) + "|")
    print("|" + f"   Verified Emails: {stats['verified_emails']}".ljust(62) + "|")

    print("+" + "-" * 62 + "+")
    print("|" + " HIGH-VALUE SLOT-COMPLETE IN NEON ".center(62, "-") + "|")
    print("|" + f"   CHRO: {stats['chro_count']}".ljust(62) + "|")
    print("|" + f"   VP: {stats['vp_count']}".ljust(62) + "|")
    print("|" + f"   Director: {stats['director_count']}".ljust(62) + "|")

    total_hv = stats['chro_count'] + stats['vp_count'] + stats['director_count']
    print("|" + f"   TOTAL HIGH-VALUE: {total_hv}".ljust(62) + "|")

    print("+" + "-" * 62 + "+")
    print("|" + " REVIEW QUEUE IN NEON ".center(62, "-") + "|")
    print("|" + f"   Total in Review Queue: {review_stats['total']}".ljust(62) + "|")
    for reason, count in sorted(review_stats['by_reason'].items(), key=lambda x: -x[1]):
        print("|" + f"     - {reason}: {count}".ljust(62) + "|")

    print("+" + "-" * 62 + "+")
    print("|" + " REVIEW QUEUE STATUS ".center(62, "-") + "|")
    for status, count in sorted(review_stats['by_status'].items(), key=lambda x: -x[1]):
        print("|" + f"     - {status}: {count}".ljust(62) + "|")

    print("+" + "=" * 62 + "+")

    print("\n[COMPLETE] Phase 4 finished!")
    print("   Data now available in Neon PostgreSQL")
    print("   Tables:")
    print("     - marketing.company_master (slot-complete companies)")
    print("     - marketing.people_master (slot-complete people)")
    print("     - marketing.review_queue (people needing review)")
    print(f"   Review Queue: {review_stats['total']} people ready for manual review")

    return stats


if __name__ == "__main__":
    main()
