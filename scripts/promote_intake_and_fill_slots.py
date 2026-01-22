#!/usr/bin/env python3
"""
Promote Intake People and Fill Slots
====================================
Promotes people from intake.people_raw_intake to people.people_master
using company name matching, then assigns them to unfilled slots.

Path: intake -> cl (by company name) -> people_master -> slots

Usage:
    doppler run -- python scripts/promote_intake_and_fill_slots.py [--dry-run]
"""

import os
import sys
import psycopg2
from datetime import datetime, timezone
import uuid

DRY_RUN = "--dry-run" in sys.argv

SLOT_PATTERNS = {
    'CEO': ['%ceo%', '%chief executive%', '%president%', '%owner%', '%founder%'],
    'CFO': ['%cfo%', '%chief financial%', '%finance director%', '%controller%', '%treasurer%'],
    'HR': ['%hr %', '%human resource%', '%people %', '%talent%', '%chro%', '%personnel%']
}


def connect_db():
    return psycopg2.connect(
        host=os.environ['NEON_HOST'],
        database=os.environ['NEON_DATABASE'],
        user=os.environ['NEON_USER'],
        password=os.environ['NEON_PASSWORD'],
        sslmode='require'
    )


def build_title_condition(patterns, table_alias='p'):
    conditions = [f"LOWER({table_alias}.title) LIKE '{p}'" for p in patterns]
    return f"({' OR '.join(conditions)})"


def promote_and_fill(conn, cur, slot_type: str) -> tuple:
    """Promote intake people and fill slots for a given slot type."""
    patterns = SLOT_PATTERNS.get(slot_type, [])
    if not patterns:
        return 0, 0

    title_condition = build_title_condition(patterns)

    # Find intake people that can fill unfilled slots
    # Use bridge.source_company_id (Barton format) for people_master.company_unique_id
    select_sql = f"""
        WITH promotable AS (
            SELECT
                p.id as intake_id,
                p.first_name,
                p.last_name,
                p.full_name,
                p.title,
                p.linkedin_url,
                p.email,
                b.source_company_id as barton_company_id,
                cs.slot_id,
                cs.outreach_id,
                ROW_NUMBER() OVER (
                    PARTITION BY cs.slot_id
                    ORDER BY
                        CASE WHEN p.linkedin_url IS NOT NULL THEN 0 ELSE 1 END,
                        p.id
                ) as rn
            FROM intake.people_raw_intake p
            JOIN cl.company_identity ci ON LOWER(ci.company_name) = LOWER(p.company_name)
            JOIN cl.company_identity_bridge b ON b.company_sov_id = ci.company_unique_id
            JOIN outreach.outreach o ON o.sovereign_id = ci.company_unique_id
            JOIN people.company_slot cs ON cs.outreach_id = o.outreach_id
            WHERE ci.identity_status = 'PASS'
            AND p.title IS NOT NULL
            AND cs.slot_type = '{slot_type}'
            AND (cs.is_filled = false OR cs.is_filled IS NULL)
            AND {title_condition}
            AND b.source_company_id ~ '^04\\.04\\.01\\.[0-9]{{2}}\\.[0-9]{{5}}\\.[0-9]{{3}}$'
            AND (p.linkedin_url IS NOT NULL OR p.email IS NOT NULL)
            AND NOT EXISTS (
                SELECT 1 FROM people.people_master pm
                WHERE pm.full_name = p.full_name
                AND pm.company_unique_id = b.source_company_id
            )
        )
        SELECT intake_id, first_name, last_name, full_name, title, linkedin_url,
               email, barton_company_id, slot_id, outreach_id
        FROM promotable
        WHERE rn = 1
    """

    cur.execute(select_sql)
    matches = cur.fetchall()

    if not matches:
        print(f"  {slot_type}: No new people to promote and assign")
        return 0, 0

    print(f"\n  {slot_type}: Found {len(matches):,} people to promote and assign")
    print(f"  Sample:")
    for row in matches[:3]:
        print(f"    {row[3][:30]:<30} | {row[4][:30]}")

    if DRY_RUN:
        print(f"  [DRY RUN] Would promote {len(matches):,} people and fill slots")
        return len(matches), len(matches)

    promoted = 0
    filled = 0

    for row in matches:
        (intake_id, first_name, last_name, full_name, title, linkedin_url,
         email, barton_company_id, slot_id, outreach_id) = row

        # Generate unique_id for the new person and slot reference
        # Use modulo to ensure proper Barton ID format (5 digits, 3 digits)
        id_part = intake_id % 100000  # Ensure max 5 digits
        suffix = intake_id % 1000      # Last 3 digits
        person_unique_id = f"04.04.02.{datetime.now().strftime('%y')}.{id_part:05d}.{suffix:03d}"
        company_slot_unique_id = f"04.04.05.{datetime.now().strftime('%y')}.{id_part:05d}.{suffix:03d}"

        # Insert into people_master (full_name is a generated column)
        cur.execute("""
            INSERT INTO people.people_master (
                unique_id, company_unique_id, company_slot_unique_id, first_name, last_name,
                title, linkedin_url, email, source_system, created_at, updated_at
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, NOW(), NOW())
            ON CONFLICT DO NOTHING
            RETURNING unique_id
        """, (
            person_unique_id, barton_company_id, company_slot_unique_id, first_name, last_name,
            title, linkedin_url, email, 'intake_promotion'
        ))

        if cur.rowcount > 0:
            promoted += 1

            # Update slot
            cur.execute("""
                UPDATE people.company_slot
                SET person_unique_id = %s,
                    is_filled = true,
                    filled_at = NOW(),
                    source_system = 'intake_promotion',
                    updated_at = NOW()
                WHERE slot_id = %s
                AND (is_filled = false OR is_filled IS NULL)
            """, (person_unique_id, slot_id))

            if cur.rowcount > 0:
                filled += 1

    print(f"  Promoted: {promoted:,}, Filled: {filled:,}")
    return promoted, filled


def run_promotion():
    conn = connect_db()
    cur = conn.cursor()

    print("=" * 80)
    print("PROMOTE INTAKE PEOPLE AND FILL SLOTS")
    print(f"Timestamp: {datetime.now(timezone.utc).isoformat()}")
    print(f"Mode: {'DRY RUN' if DRY_RUN else 'LIVE EXECUTION'}")
    print("=" * 80)

    # Pre-stats
    print("\n[1] PRE-PROMOTION STATUS")
    print("-" * 50)
    cur.execute("SELECT COUNT(*) FROM people.people_master")
    print(f"  people_master: {cur.fetchone()[0]:,}")

    cur.execute("""
        SELECT slot_type, COUNT(*) FILTER (WHERE is_filled = true) as filled,
               COUNT(*) as total
        FROM people.company_slot GROUP BY slot_type ORDER BY slot_type
    """)
    for row in cur.fetchall():
        print(f"  {row[0]} slots: {row[1]:,} / {row[2]:,} filled")

    # Process each slot type
    print("\n[2] PROMOTION AND SLOT FILL")
    print("-" * 50)

    total_promoted = 0
    total_filled = 0

    for slot_type in ['CEO', 'CFO', 'HR']:
        promoted, filled = promote_and_fill(conn, cur, slot_type)
        total_promoted += promoted
        total_filled += filled

    # Commit or rollback
    if not DRY_RUN and total_promoted > 0:
        conn.commit()

        print("\n[3] POST-PROMOTION STATUS")
        print("-" * 50)
        cur.execute("SELECT COUNT(*) FROM people.people_master")
        print(f"  people_master: {cur.fetchone()[0]:,}")

        cur.execute("""
            SELECT slot_type, COUNT(*) FILTER (WHERE is_filled = true) as filled,
                   COUNT(*) as total
            FROM people.company_slot GROUP BY slot_type ORDER BY slot_type
        """)
        for row in cur.fetchall():
            pct = row[1] / row[2] * 100 if row[2] > 0 else 0
            print(f"  {row[0]} slots: {row[1]:,} / {row[2]:,} filled ({pct:.1f}%)")

    print("\n" + "=" * 80)
    print("SUMMARY")
    print("=" * 80)
    print(f"  People promoted: {total_promoted:,}")
    print(f"  Slots filled: {total_filled:,}")

    if DRY_RUN:
        print("\n  [DRY RUN] No changes made.")
    else:
        print("\n  Changes committed!")

    conn.close()


if __name__ == "__main__":
    run_promotion()
