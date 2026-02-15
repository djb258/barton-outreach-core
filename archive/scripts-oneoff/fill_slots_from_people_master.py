#!/usr/bin/env python3
"""
Fill Slots from People Master
=============================
Assigns people from people.people_master to unfilled slots in people.company_slot
based on title matching through the bridge linkage.

Path: people_master -> bridge -> outreach.outreach -> company_slot

Usage:
    doppler run -- python scripts/fill_slots_from_people_master.py [--dry-run]
"""

import os
import sys
import psycopg2
from datetime import datetime, timezone

DRY_RUN = "--dry-run" in sys.argv

# Title patterns for slot matching
SLOT_PATTERNS = {
    'CEO': [
        '%ceo%', '%chief executive%', '%president%', '%owner%', '%founder%'
    ],
    'CFO': [
        '%cfo%', '%chief financial%', '%finance director%', '%vp finance%',
        '%controller%', '%treasurer%'
    ],
    'HR': [
        '%hr %', '%human resource%', '%people %', '%talent%', '%chro%',
        '%chief people%', '%personnel%'
    ]
}


def connect_db():
    """Connect to Neon PostgreSQL via Doppler."""
    return psycopg2.connect(
        host=os.environ['NEON_HOST'],
        database=os.environ['NEON_DATABASE'],
        user=os.environ['NEON_USER'],
        password=os.environ['NEON_PASSWORD'],
        sslmode='require'
    )


def build_title_condition(patterns):
    """Build SQL LIKE condition for title patterns."""
    conditions = [f"LOWER(pm.title) LIKE '{p}'" for p in patterns]
    return f"({' OR '.join(conditions)})"


def fill_slots_for_type(cur, slot_type: str) -> int:
    """Fill unfilled slots of given type with matching people."""
    patterns = SLOT_PATTERNS.get(slot_type, [])
    if not patterns:
        return 0

    title_condition = build_title_condition(patterns)

    # Find fillable slots with best matching person (using ROW_NUMBER to get one person per slot)
    select_sql = f"""
        WITH matched_people AS (
            SELECT
                cs.slot_id,
                pm.unique_id as person_unique_id,
                pm.full_name,
                pm.title,
                pm.email,
                ROW_NUMBER() OVER (
                    PARTITION BY cs.slot_id
                    ORDER BY
                        CASE
                            WHEN pm.email_verified = true THEN 0
                            ELSE 1
                        END,
                        pm.created_at DESC
                ) as rn
            FROM people.company_slot cs
            JOIN outreach.outreach o ON o.outreach_id = cs.outreach_id
            JOIN cl.company_identity_bridge b ON b.company_sov_id = o.sovereign_id
            JOIN people.people_master pm ON pm.company_unique_id = b.source_company_id
            WHERE cs.slot_type = '{slot_type}'
            AND (cs.is_filled = false OR cs.is_filled IS NULL)
            AND pm.title IS NOT NULL
            AND {title_condition}
        )
        SELECT slot_id, person_unique_id, full_name, title, email
        FROM matched_people
        WHERE rn = 1
    """

    cur.execute(select_sql)
    matches = cur.fetchall()

    if not matches:
        return 0

    print(f"\n  Found {len(matches):,} {slot_type} slots to fill")

    # Show samples
    print(f"  Sample matches:")
    for row in matches[:5]:
        slot_id, person_id, name, title, email = row
        print(f"    {name[:30]:<30} | {title[:30]:<30} | {email or 'no email'}")

    if DRY_RUN:
        print(f"  [DRY RUN] Would fill {len(matches):,} {slot_type} slots")
        return len(matches)

    # Update slots
    filled = 0
    for row in matches:
        slot_id, person_unique_id, _, _, _ = row
        cur.execute("""
            UPDATE people.company_slot
            SET person_unique_id = %s,
                is_filled = true,
                filled_at = NOW(),
                source_system = 'people_master_bridge',
                updated_at = NOW()
            WHERE slot_id = %s
            AND (is_filled = false OR is_filled IS NULL)
        """, (person_unique_id, slot_id))
        filled += cur.rowcount

    print(f"  Filled: {filled:,} {slot_type} slots")
    return filled


def run_slot_fill():
    """Main slot filling process."""
    conn = connect_db()
    cur = conn.cursor()

    print("=" * 80)
    print("SLOT FILL FROM PEOPLE MASTER")
    print(f"Timestamp: {datetime.now(timezone.utc).isoformat()}")
    print(f"Mode: {'DRY RUN' if DRY_RUN else 'LIVE EXECUTION'}")
    print("=" * 80)

    # Pre-fill stats
    print("\n[1] PRE-FILL STATUS")
    print("-" * 50)
    cur.execute("""
        SELECT
            slot_type,
            COUNT(*) as total,
            COUNT(*) FILTER (WHERE is_filled = true) as filled
        FROM people.company_slot
        GROUP BY slot_type
        ORDER BY slot_type
    """)
    for row in cur.fetchall():
        slot_type, total, filled = row
        print(f"  {slot_type}: {filled:,} / {total:,} filled ({filled/total*100:.1f}%)")

    # Fill each slot type
    print("\n[2] FILLING SLOTS")
    print("-" * 50)

    total_filled = 0
    for slot_type in ['CEO', 'CFO', 'HR']:
        filled = fill_slots_for_type(cur, slot_type)
        total_filled += filled

    # Post-fill stats
    if not DRY_RUN and total_filled > 0:
        conn.commit()

        print("\n[3] POST-FILL STATUS")
        print("-" * 50)
        cur.execute("""
            SELECT
                slot_type,
                COUNT(*) as total,
                COUNT(*) FILTER (WHERE is_filled = true) as filled
            FROM people.company_slot
            GROUP BY slot_type
            ORDER BY slot_type
        """)
        for row in cur.fetchall():
            slot_type, total, filled = row
            print(f"  {slot_type}: {filled:,} / {total:,} filled ({filled/total*100:.1f}%)")

    # Summary
    print("\n" + "=" * 80)
    print("SUMMARY")
    print("=" * 80)
    print(f"  Total slots filled: {total_filled:,}")

    if DRY_RUN:
        print("\n  [DRY RUN] No changes made. Run without --dry-run to execute.")
    else:
        print("\n  Changes committed successfully!")

    conn.close()
    return total_filled


if __name__ == "__main__":
    run_slot_fill()
