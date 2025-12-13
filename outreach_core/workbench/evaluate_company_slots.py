#!/usr/bin/env python3
"""
Slot Evaluation Agent - Post-Enrichment
========================================

After people enrichment, re-evaluates companies to detect missing leadership
slots (CEO, CFO, HR) and updates company_slot tracking.

Workflow:
1. Loop through all companies in marketing.company_master
2. For each company, ensure 3 slot records exist (CEO, CFO, HR)
3. Query all people for that company from marketing.people_master
4. Match people to slots by title keywords
5. Update company_slot table with person assignments and status

Matching Rules:
- CEO: "ceo", "chief executive"
- CFO: "cfo", "chief financial"
- HR: "hr", "human resources", "talent", "people operations"

Priority: Exact match > Contains > Regex fuzzy match
First match wins. One person can fill multiple slots.

Status Logic:
- "filled": Person found and assigned
- "open": No person found, enrichment_attempts < 2
- "closed_missing": No person found, enrichment_attempts >= 2

Author: Claude Code
Created: 2025-11-18
Barton ID: 04.04.02.04.50000.###
"""

import os
import sys
import re
import argparse
from datetime import datetime
from collections import defaultdict
import psycopg2
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# ============================================================================
# CONFIGURATION
# ============================================================================

SLOT_TYPES = ['CEO', 'CFO', 'HR']

# Title matching keywords (case-insensitive)
TITLE_KEYWORDS = {
    'CEO': [
        r'\bceo\b',  # Exact word boundary match
        'chief executive officer',
        'chief executive',
    ],
    'CFO': [
        r'\bcfo\b',
        'chief financial officer',
        'chief financial',
    ],
    'HR': [
        r'\bhr\b',
        'human resources',
        'talent',
        'people operations',
        'chief people officer',
        'head of people',
        'vp of people',
        'director of human resources',
    ],
}

# Barton ID configuration
BARTON_SUBHIVE = "04"
BARTON_APP = "04"
BARTON_LAYER_SLOT = "02"
BARTON_SCHEMA_SLOT = "04"
BARTON_TABLE_SLOT = "10000"

# Statistics tracking
stats = {
    'companies_processed': 0,
    'slots_created': 0,
    'slots_updated': 0,
    'slots_filled': 0,
    'slots_open': 0,
    'slots_closed_missing': 0,
    'compound_matches': 0,  # People filling multiple slots
    'multiple_candidates': 0,  # Multiple people matching same slot
    'backfill_triggered': 0,  # Enrichment requests triggered for unfilled slots
}

# ============================================================================
# BARTON ID GENERATION
# ============================================================================

def generate_slot_barton_id(sequence_num):
    """
    Generate Barton ID for company_slot: 04.04.02.04.10000.XXX
    """
    two_digit = sequence_num % 100
    return f"{BARTON_SUBHIVE}.{BARTON_APP}.{BARTON_LAYER_SLOT}.{two_digit:02d}.{BARTON_TABLE_SLOT}.{sequence_num:03d}"

def get_next_slot_sequence(cursor):
    """Get next sequence number for company_slot Barton IDs"""
    cursor.execute("""
        SELECT company_slot_unique_id
        FROM marketing.company_slot
        ORDER BY company_slot_unique_id DESC
        LIMIT 1;
    """)
    result = cursor.fetchone()
    if result:
        # Extract sequence from last ID (format: 04.04.02.04.10000.XXX)
        last_id = result[0]
        sequence = int(last_id.split('.')[-1])
        return sequence + 1
    return 1  # First record

# ============================================================================
# TITLE MATCHING LOGIC
# ============================================================================

def match_title_to_slot(title: str, slot_type: str) -> bool:
    """
    Check if a title matches a slot type using keyword matching.

    Priority order:
    1. Exact match (e.g., title == "CEO")
    2. Contains keyword (e.g., "Chief Executive Officer")
    3. Regex word boundary match (e.g., r"\bceo\b")

    Args:
        title: Job title from people_master
        slot_type: CEO, CFO, or HR

    Returns:
        True if title matches slot type, False otherwise
    """
    if not title:
        return False

    title_lower = title.lower().strip()
    keywords = TITLE_KEYWORDS.get(slot_type, [])

    for keyword in keywords:
        # Check if keyword is a regex pattern (starts with \b or contains special chars)
        if keyword.startswith(r'\b') or '\\' in keyword:
            # Regex match
            if re.search(keyword, title_lower, re.IGNORECASE):
                return True
        else:
            # Simple contains match
            if keyword in title_lower:
                return True

    return False

def find_slot_matches(people: list, slot_type: str) -> list:
    """
    Find all people whose titles match a given slot type.

    Args:
        people: List of person dictionaries with 'title' and 'unique_id'
        slot_type: CEO, CFO, or HR

    Returns:
        List of matching person records
    """
    matches = []
    for person in people:
        if match_title_to_slot(person.get('title', ''), slot_type):
            matches.append(person)
    return matches

# ============================================================================
# SLOT BACKFILL ENRICHMENT TRIGGERING
# ============================================================================

def trigger_slot_backfill(cursor, company_id: str, company_name: str, slot_type: str,
                         enrichment_attempt: int, dry_run: bool = False):
    """
    Trigger enrichment for an unfilled slot by creating a placeholder person
    in people_raw_intake and logging to agent_routing_log.

    Uses ON CONFLICT to prevent duplicate backfill requests.

    Args:
        cursor: Database cursor
        company_id: Company Barton ID
        company_name: Company name (for logging)
        slot_type: CEO, CFO, or HR
        enrichment_attempt: Current attempt count
        dry_run: If True, don't execute (print only)
    """
    # Insert placeholder person into people_raw_intake
    # Uses ON CONFLICT to prevent duplicates
    sql_person = """
        INSERT INTO intake.people_raw_intake (
            company_unique_id,
            company_name,
            source_system,
            slot_type,
            backfill_source,
            enrichment_attempt,
            validated,
            created_at
        ) VALUES (
            %s, %s, %s, %s, %s, %s, FALSE, NOW()
        )
        ON CONFLICT (company_unique_id, slot_type)
        WHERE source_system = 'slot_backfill' AND validated = FALSE
        DO UPDATE SET
            enrichment_attempt = EXCLUDED.enrichment_attempt,
            updated_at = NOW()
        RETURNING id;
    """

    # Log to agent_routing_log for agent assignment
    sql_routing = """
        INSERT INTO public.agent_routing_log (
            record_type,
            record_id,
            garage_bay,
            agent_name,
            routing_reason,
            routed_at,
            status
        ) VALUES (
            %s, %s, %s, %s, %s, NOW(), %s
        );
    """

    if dry_run:
        print(f"    [DRY RUN] Would trigger backfill for {slot_type} at {company_name}")
        return

    try:
        # Insert placeholder person (with deduplication)
        cursor.execute(sql_person, (
            company_id,
            company_name,
            'slot_backfill',
            slot_type,
            'slot_evaluation',
            enrichment_attempt
        ))

        person_intake_id = cursor.fetchone()[0]

        # Log to agent routing
        agent_name = 'b2_enrichment_agent'  # Default enrichment agent
        routing_reason = f"slot_backfill_{slot_type}_attempt_{enrichment_attempt}"

        cursor.execute(sql_routing, (
            'person_slot_backfill',
            str(person_intake_id),
            'bay_a',  # Slot backfill is missing person data (Bay A)
            agent_name,
            routing_reason,
            'queued'
        ))

        stats['backfill_triggered'] += 1
        print(f"    [BACKFILL] Triggered {slot_type} enrichment (attempt {enrichment_attempt})")

    except Exception as e:
        # Likely duplicate (ON CONFLICT hit but didn't return id)
        if 'duplicate' in str(e).lower() or 'unique' in str(e).lower():
            print(f"    [SKIP] Backfill already queued for {slot_type}")
        else:
            print(f"    [ERROR] Failed to trigger backfill: {e}")

# ============================================================================
# SLOT UPSERT LOGIC
# ============================================================================

def upsert_company_slot(cursor, company_id: str, slot_type: str, person_id: str = None,
                       current_attempts: int = 0, company_name: str = '', dry_run: bool = False):
    """
    UPSERT a company slot record.

    Logic:
    - If person_id provided: is_filled=TRUE, status='filled', reset attempts to 0
    - If person_id is None: is_filled=FALSE, increment attempts, set status based on attempts
    - If status='open' and attempts < 2: trigger slot backfill enrichment

    Args:
        cursor: Database cursor
        company_id: Company Barton ID
        slot_type: CEO, CFO, or HR
        person_id: Person Barton ID (None if no match)
        current_attempts: Current enrichment_attempts count
        company_name: Company name (for backfill logging)
        dry_run: If True, don't execute (print only)
    """
    # Determine values based on whether person was found
    if person_id:
        is_filled = True
        status = 'filled'
        enrichment_attempts = 0  # Reset attempts on successful fill
        filled_at = datetime.now()
    else:
        is_filled = False
        enrichment_attempts = current_attempts + 1
        status = 'closed_missing' if enrichment_attempts >= 2 else 'open'
        filled_at = None

        # Trigger backfill enrichment if slot is still open (attempts < 2)
        if status == 'open' and enrichment_attempts < 2:
            trigger_slot_backfill(cursor, company_id, company_name, slot_type,
                                enrichment_attempts, dry_run)

    # Check if slot already exists
    cursor.execute("""
        SELECT company_slot_unique_id, enrichment_attempts
        FROM marketing.company_slot
        WHERE company_unique_id = %s AND slot_type = %s;
    """, (company_id, slot_type))

    existing = cursor.fetchone()

    if existing:
        # UPDATE existing slot
        slot_id = existing[0]

        sql = """
            UPDATE marketing.company_slot
            SET
                person_unique_id = %s,
                is_filled = %s,
                filled_at = %s,
                enrichment_attempts = %s,
                status = %s,
                last_refreshed_at = NOW()
            WHERE company_slot_unique_id = %s;
        """
        params = (person_id, is_filled, filled_at, enrichment_attempts, status, slot_id)

        if dry_run:
            print(f"  [DRY RUN] UPDATE slot {slot_id}: {slot_type} -> {status}")
        else:
            cursor.execute(sql, params)
            stats['slots_updated'] += 1

    else:
        # INSERT new slot
        slot_id = generate_slot_barton_id(get_next_slot_sequence(cursor))

        sql = """
            INSERT INTO marketing.company_slot (
                company_slot_unique_id,
                company_unique_id,
                person_unique_id,
                slot_type,
                is_filled,
                filled_at,
                enrichment_attempts,
                status,
                last_refreshed_at
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, NOW());
        """
        params = (slot_id, company_id, person_id, slot_type, is_filled,
                 filled_at, enrichment_attempts, status)

        if dry_run:
            print(f"  [DRY RUN] INSERT slot {slot_id}: {slot_type} -> {status}")
        else:
            cursor.execute(sql, params)
            stats['slots_created'] += 1

    # Update statistics
    if status == 'filled':
        stats['slots_filled'] += 1
    elif status == 'open':
        stats['slots_open'] += 1
    elif status == 'closed_missing':
        stats['slots_closed_missing'] += 1

# ============================================================================
# MAIN EVALUATION LOGIC
# ============================================================================

def evaluate_company_slots(cursor, dry_run: bool = False):
    """
    Main evaluation loop: process all companies and update slot assignments.

    Args:
        cursor: Database cursor
        dry_run: If True, don't execute updates (simulation mode)
    """
    print("=" * 80)
    print("SLOT EVALUATION AGENT - POST-ENRICHMENT")
    print("=" * 80)
    print()
    print(f"Mode: {'DRY RUN (Simulation)' if dry_run else 'LIVE UPDATE'}")
    print(f"Timestamp: {datetime.now().isoformat()}")
    print()

    # Step 1: Get all companies
    print("STEP 1: Fetching All Companies")
    print("-" * 80)
    cursor.execute("""
        SELECT company_unique_id, company_name
        FROM marketing.company_master
        ORDER BY company_unique_id;
    """)
    companies = cursor.fetchall()
    print(f"[OK] Found {len(companies)} companies")
    print()

    # Step 2: Process each company
    print("STEP 2: Evaluating Slots for Each Company")
    print("-" * 80)

    for idx, (company_id, company_name) in enumerate(companies, 1):
        stats['companies_processed'] += 1

        # Get all people for this company
        cursor.execute("""
            SELECT unique_id, full_name, title
            FROM marketing.people_master
            WHERE company_unique_id = %s;
        """, (company_id,))

        people = [
            {'unique_id': row[0], 'full_name': row[1], 'title': row[2]}
            for row in cursor.fetchall()
        ]

        # Get current slot attempts for this company
        cursor.execute("""
            SELECT slot_type, enrichment_attempts
            FROM marketing.company_slot
            WHERE company_unique_id = %s;
        """, (company_id,))

        current_attempts = {row[0]: row[1] for row in cursor.fetchall()}

        # Evaluate each slot type
        # Use ASCII-safe version for all processing to avoid encoding errors
        company_name_safe = company_name.encode('ascii', 'ignore').decode('ascii')
        print(f"  [{idx}/{len(companies)}] {company_name_safe} ({company_id})")

        filled_slots = []

        for slot_type in SLOT_TYPES:
            # Find all people matching this slot
            matches = find_slot_matches(people, slot_type)

            if matches:
                # First match wins
                person = matches[0]
                person_id = person['unique_id']
                person_name = person['full_name'].encode('ascii', 'ignore').decode('ascii')

                upsert_company_slot(
                    cursor, company_id, slot_type, person_id,
                    current_attempts.get(slot_type, 0), company_name_safe, dry_run
                )

                filled_slots.append(f"{slot_type}: {person_name}")

                # Track compound matches (one person filling multiple slots)
                if len([m for m in matches if m['unique_id'] == person_id]) > 1:
                    stats['compound_matches'] += 1

                # Track multiple candidates (>1 person matched)
                if len(matches) > 1:
                    stats['multiple_candidates'] += 1
                    other_names = [m['full_name'] for m in matches[1:]]
                    print(f"    [WARNING] {slot_type}: {len(matches)} candidates, picked first match")

            else:
                # No match found - increment attempts and trigger backfill
                upsert_company_slot(
                    cursor, company_id, slot_type, None,
                    current_attempts.get(slot_type, 0), company_name_safe, dry_run
                )

        if filled_slots:
            print(f"    Filled: {', '.join(filled_slots)}")
        else:
            print(f"    No slots filled (no matching titles)")

    print()
    print("[OK] Slot evaluation complete")
    print()

# ============================================================================
# SUMMARY REPORT
# ============================================================================

def print_summary():
    """Print evaluation summary statistics"""
    print("=" * 80)
    print("SLOT EVALUATION SUMMARY")
    print("=" * 80)
    print()
    print(f"Companies Processed: {stats['companies_processed']}")
    print(f"Slots Created: {stats['slots_created']}")
    print(f"Slots Updated: {stats['slots_updated']}")
    print()
    print("Slot Status Distribution:")
    print(f"  Filled: {stats['slots_filled']}")
    print(f"  Open (< 2 attempts): {stats['slots_open']}")
    print(f"  Closed Missing (>= 2 attempts): {stats['slots_closed_missing']}")
    print()
    print("Data Quality Metrics:")
    print(f"  Compound Matches (1 person = multiple slots): {stats['compound_matches']}")
    print(f"  Multiple Candidates (>1 person per slot): {stats['multiple_candidates']}")
    print()
    print("Enrichment Backfill:")
    print(f"  Slot Backfill Requests Triggered: {stats['backfill_triggered']}")
    print()

    total_slots = stats['slots_filled'] + stats['slots_open'] + stats['slots_closed_missing']
    if total_slots > 0:
        fill_rate = (stats['slots_filled'] / total_slots) * 100
        print(f"Overall Fill Rate: {fill_rate:.1f}% ({stats['slots_filled']}/{total_slots})")

    print()
    print("=" * 80)

# ============================================================================
# CLI ENTRY POINT
# ============================================================================

def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description='Evaluate company leadership slots after people enrichment'
    )
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Simulation mode: show what would be updated without making changes'
    )
    args = parser.parse_args()

    # Connect to database
    try:
        conn = psycopg2.connect(
            host=os.getenv('NEON_HOST'),
            database=os.getenv('NEON_DATABASE'),
            user=os.getenv('NEON_USER'),
            password=os.getenv('NEON_PASSWORD'),
            sslmode='require'
        )
        cursor = conn.cursor()
    except Exception as e:
        print(f"[ERROR] Database connection failed: {e}")
        sys.exit(1)

    try:
        # Run evaluation
        evaluate_company_slots(cursor, dry_run=args.dry_run)

        # Commit if not dry run
        if not args.dry_run:
            conn.commit()
            print("[OK] Changes committed to database")
        else:
            print("[DRY RUN] No changes made to database")

        # Print summary
        print_summary()

    except Exception as e:
        print(f"[ERROR] Evaluation failed: {e}")
        conn.rollback()
        sys.exit(1)
    finally:
        cursor.close()
        conn.close()

if __name__ == '__main__':
    main()
