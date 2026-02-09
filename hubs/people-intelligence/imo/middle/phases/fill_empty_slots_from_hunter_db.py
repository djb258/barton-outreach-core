#!/usr/bin/env python3
"""
Fill Empty Slots from Hunter Contact Table (Direct DB Query)
============================================================
Queries enrichment.hunter_contact directly via JOIN to find
Hunter contacts whose domain + job title match empty slots.

Uses the same pattern as fill_slots_from_hunter.py:
  - Barton ID generation (04.04.02.YY.NNNNNN.NNN)
  - people_master INSERT
  - company_slot UPDATE

Approach: single JOIN query to find all (empty_slot, hunter_contact) pairs,
then process matches in Python.

Usage:
    doppler run -- python fill_empty_slots_from_hunter_db.py [--dry-run] [--slot-type CEO|CFO|HR]

Created: 2026-02-09
"""

import os
import sys
from datetime import datetime
from typing import Optional, List
from dataclasses import dataclass, field

# Windows encoding fix
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')


# Barton ID prefix for People Intelligence hub
BARTON_PREFIX = "04.04.02"
BARTON_YEAR = "26"  # 2026
BATCH_SIZE = 500

# Job title keyword lists (same as fill_slots_from_hunter.py)
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
    for keyword in CFO_KEYWORDS:
        if keyword in title_lower:
            return 'CFO'
    for keyword in HR_KEYWORDS:
        if keyword in title_lower:
            return 'HR'
    for keyword in CEO_KEYWORDS:
        if keyword in title_lower:
            return 'CEO'
    return None


def _build_title_filter(slot_type: str) -> str:
    """Build SQL ILIKE conditions for a slot type's keywords."""
    keywords = {'CEO': CEO_KEYWORDS, 'CFO': CFO_KEYWORDS, 'HR': HR_KEYWORDS}[slot_type]
    conditions = [f"LOWER(hc.job_title) LIKE '%{kw}%'" for kw in keywords]
    return '(' + ' OR '.join(conditions) + ')'


@dataclass
class FillStats:
    empty_slots_total: int = 0
    candidates_found: int = 0
    people_created: int = 0
    slots_filled: int = 0
    ceo_filled: int = 0
    cfo_filled: int = 0
    hr_filled: int = 0
    phones_added: int = 0
    already_in_people_master: int = 0
    errors: List[str] = field(default_factory=list)


def get_connection():
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        print("[FAIL] DATABASE_URL not set. Use: doppler run -- python fill_empty_slots_from_hunter_db.py")
        sys.exit(1)
    import psycopg2
    return psycopg2.connect(database_url)


def get_next_barton_id(cursor) -> str:
    """Generate next Barton ID for people_master."""
    cursor.execute("""
        SELECT MAX(CAST(SPLIT_PART(unique_id, '.', 5) AS INTEGER))
        FROM people.people_master
        WHERE unique_id LIKE %s
    """, (f"{BARTON_PREFIX}.{BARTON_YEAR}.%",))
    result = cursor.fetchone()[0]
    next_seq = (result or 0) + 1
    suffix = str(next_seq)[-3:].zfill(3)
    return f"{BARTON_PREFIX}.{BARTON_YEAR}.{next_seq}.{suffix}"


def find_all_candidates(conn, slot_type_filter=None):
    """Single JOIN query: find all (empty_slot, best_hunter_contact) pairs.

    Returns list of tuples:
      (slot_id, outreach_id, slot_type, company_unique_id,
       hc_email, hc_first_name, hc_last_name, hc_job_title,
       hc_phone_number, hc_linkedin_url)
    """
    cursor = conn.cursor()

    # Build per-slot-type queries and UNION them
    slot_types = [slot_type_filter] if slot_type_filter else ['CEO', 'CFO', 'HR']
    union_parts = []

    for stype in slot_types:
        title_filter = _build_title_filter(stype)
        union_parts.append(f"""
            SELECT * FROM (
                SELECT DISTINCT ON (cs.slot_id)
                    cs.slot_id,
                    cs.outreach_id,
                    cs.slot_type,
                    cs.company_unique_id,
                    hc.email AS hc_email,
                    hc.first_name AS hc_first_name,
                    hc.last_name AS hc_last_name,
                    hc.job_title AS hc_job_title,
                    hc.phone_number AS hc_phone_number,
                    hc.linkedin_url AS hc_linkedin_url
                FROM people.company_slot cs
                JOIN outreach.outreach oo ON oo.outreach_id = cs.outreach_id
                JOIN enrichment.hunter_contact hc
                    ON LOWER(oo.domain) = LOWER(hc.domain)
                    AND hc.email IS NOT NULL AND hc.email != ''
                    AND hc.first_name IS NOT NULL AND hc.first_name != ''
                    AND {title_filter}
                WHERE cs.is_filled = FALSE
                  AND cs.person_unique_id IS NULL
                  AND cs.slot_type = '{stype}'
                ORDER BY cs.slot_id, hc.confidence_score DESC NULLS LAST
            ) sub_{stype.lower()}
        """)

    query = "\nUNION ALL\n".join(union_parts)
    cursor.execute(query)
    rows = cursor.fetchall()
    cursor.close()
    return rows


def fill_slots(conn, candidates, stats: FillStats, dry_run=False):
    """Process candidate matches and fill slots."""
    cursor = conn.cursor()

    if dry_run:
        print("  [DRY RUN] No changes will be made.\n")

    processed = 0
    for row in candidates:
        (slot_id, outreach_id, slot_type, company_unique_id,
         email, first_name, last_name, job_title, phone, linkedin) = row

        processed += 1
        if processed % BATCH_SIZE == 0:
            print(f"  Processed {processed:,}/{len(candidates):,} "
                  f"(filled: {stats.slots_filled:,})...")
            if not dry_run:
                conn.commit()

        if dry_run:
            stats.slots_filled += 1
            if slot_type == 'CEO': stats.ceo_filled += 1
            elif slot_type == 'CFO': stats.cfo_filled += 1
            elif slot_type == 'HR': stats.hr_filled += 1
            if phone: stats.phones_added += 1
            continue

        try:
            # Check if person already exists by email
            cursor.execute("""
                SELECT unique_id FROM people.people_master
                WHERE LOWER(email) = LOWER(%s)
            """, (email,))
            person_row = cursor.fetchone()

            if person_row:
                person_id = person_row[0]
                stats.already_in_people_master += 1
            else:
                if not company_unique_id:
                    stats.errors.append(f"slot {slot_id}: no company_unique_id")
                    continue

                person_id = get_next_barton_id(cursor)
                cursor.execute("""
                    INSERT INTO people.people_master (
                        unique_id, company_unique_id, company_slot_unique_id,
                        first_name, last_name, email,
                        title, linkedin_url, work_phone_e164,
                        source_system, created_at
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, NOW())
                """, (
                    person_id, company_unique_id, slot_id,
                    first_name, last_name, email.lower(),
                    job_title,
                    linkedin if linkedin else None,
                    phone if phone else None,
                    'hunter'
                ))
                stats.people_created += 1

            # Update the slot
            if phone:
                cursor.execute("""
                    UPDATE people.company_slot
                    SET person_unique_id = %s, is_filled = TRUE, filled_at = NOW(),
                        source_system = 'hunter', slot_phone = %s,
                        slot_phone_source = 'hunter', slot_phone_updated_at = NOW()
                    WHERE slot_id = %s
                """, (person_id, phone, slot_id))
                stats.phones_added += 1
            else:
                cursor.execute("""
                    UPDATE people.company_slot
                    SET person_unique_id = %s, is_filled = TRUE, filled_at = NOW(),
                        source_system = 'hunter'
                    WHERE slot_id = %s
                """, (person_id, slot_id))

            stats.slots_filled += 1
            if slot_type == 'CEO': stats.ceo_filled += 1
            elif slot_type == 'CFO': stats.cfo_filled += 1
            elif slot_type == 'HR': stats.hr_filled += 1

        except Exception as e:
            stats.errors.append(f"slot {slot_id}: {str(e)}")
            conn.rollback()

    if not dry_run:
        conn.commit()
    cursor.close()


def main():
    dry_run = '--dry-run' in sys.argv
    slot_type_filter = None

    for i, arg in enumerate(sys.argv):
        if arg == '--slot-type' and i + 1 < len(sys.argv):
            slot_type_filter = sys.argv[i + 1].upper()
            if slot_type_filter not in ('CEO', 'CFO', 'HR'):
                print(f"[ERROR] Invalid slot type: {slot_type_filter}")
                sys.exit(1)

    print("=" * 60)
    print("FILL EMPTY SLOTS FROM HUNTER DB")
    print("=" * 60)
    print(f"Mode: {'DRY RUN' if dry_run else 'LIVE'}")
    if slot_type_filter:
        print(f"Slot type filter: {slot_type_filter}")
    print(f"Started: {datetime.now().isoformat()}")

    conn = get_connection()
    print("Connected to database.")

    # Count empty slots
    cursor = conn.cursor()
    cursor.execute("""
        SELECT slot_type, COUNT(*)
        FROM people.company_slot
        WHERE is_filled = FALSE AND person_unique_id IS NULL
        GROUP BY slot_type ORDER BY slot_type
    """)
    print("\n  Empty slots by type:")
    total_empty = 0
    for stype, cnt in cursor.fetchall():
        print(f"    {stype}: {cnt:,}")
        total_empty += cnt
    print(f"    TOTAL: {total_empty:,}")
    cursor.close()

    # Find all candidates via JOIN
    print("\n  Finding Hunter contacts matching empty slots (JOIN query)...")
    candidates = find_all_candidates(conn, slot_type_filter)
    print(f"  Candidates found: {len(candidates):,}")

    if not candidates:
        print("  No Hunter matches for any empty slots. Done.")
        conn.close()
        return

    # Breakdown
    type_counts = {}
    for row in candidates:
        st = row[2]
        type_counts[st] = type_counts.get(st, 0) + 1
    for st in sorted(type_counts.keys()):
        print(f"    {st}: {type_counts[st]:,}")

    stats = FillStats(empty_slots_total=total_empty, candidates_found=len(candidates))
    fill_slots(conn, candidates, stats, dry_run)
    conn.close()

    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    print(f"  Empty slots total:         {stats.empty_slots_total:,}")
    print(f"  Hunter candidates found:   {stats.candidates_found:,}")
    print(f"  People created:            {stats.people_created:,}")
    print(f"  Already in people_master:  {stats.already_in_people_master:,}")
    print(f"  Slots filled:              {stats.slots_filled:,}")
    print(f"    CEO: {stats.ceo_filled:,}")
    print(f"    CFO: {stats.cfo_filled:,}")
    print(f"    HR:  {stats.hr_filled:,}")
    print(f"  Phone numbers added:       {stats.phones_added:,}")

    if stats.errors:
        print(f"\n  Errors ({len(stats.errors)}):")
        for err in stats.errors[:20]:
            print(f"    - {err}")

    print(f"\nCompleted: {datetime.now().isoformat()}")


if __name__ == "__main__":
    main()
