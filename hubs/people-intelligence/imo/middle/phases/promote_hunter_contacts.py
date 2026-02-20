#!/usr/bin/env python3
"""
Promote Hunter Contacts — Fill empty people slots from enrichment.hunter_contact.

Bridge path:
    enrichment.hunter_contact (outreach_id or domain match)
        -> people.company_slot (unfilled, matching slot_type)
        -> people.people_master (new record)

For each unfilled slot (CEO/CFO/HR), finds the best Hunter contact by:
1. Title keyword matching (same logic as fill_slots_from_hunter.py)
2. Best candidate per (outreach_id, slot_type): prefers LinkedIn > confidence

Processes one slot_type at a time (CEO, CFO, HR) to avoid conflicts.
Batches commits every 1,000 fills for safety.

Usage:
    doppler run -- python scripts/promote_hunter_contacts.py --dry-run
    doppler run -- python scripts/promote_hunter_contacts.py
    doppler run -- python scripts/promote_hunter_contacts.py --slot-type CEO --dry-run
"""

import argparse
import os
import sys
import time

import psycopg2

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")

# Barton ID format
BARTON_PREFIX = "04.04.02"
BARTON_YEAR = "26"

# ---- Title matching (same keywords as fill_slots_from_hunter.py) ----

CFO_KEYWORDS = [
    'cfo', 'chief financial', 'vp finance', 'vice president finance',
    'controller', 'treasurer', 'finance director', 'director of finance',
    'evp/cfo', 'svp finance', 'head of finance',
]

HR_KEYWORDS = [
    'hr', 'human resources', 'chief people', 'vp people', 'chro',
    'people operations', 'talent', 'chief hr', 'director of hr',
    'svp human resources', 'vp human resources', 'head of hr',
    'head of people', 'shrm', 'sphr', 'phr',
]

CEO_KEYWORDS = [
    'ceo', 'chief executive', 'president', 'owner', 'founder',
    'managing director', 'general manager', 'principal', 'chairman',
    'chairwoman', 'chair ', 'co-founder', 'cofounder',
]


def get_slot_type(job_title):
    """Determine slot type from job title. CFO checked first to avoid 'president' overlap."""
    if not job_title:
        return None
    title_lower = job_title.lower()
    for kw in CFO_KEYWORDS:
        if kw in title_lower:
            return 'CFO'
    for kw in HR_KEYWORDS:
        if kw in title_lower:
            return 'HR'
    for kw in CEO_KEYWORDS:
        if kw in title_lower:
            return 'CEO'
    return None


def get_connection():
    return psycopg2.connect(
        host=os.environ["NEON_HOST"],
        dbname=os.environ["NEON_DATABASE"],
        user=os.environ["NEON_USER"],
        password=os.environ["NEON_PASSWORD"],
        sslmode="require",
    )


def get_next_barton_seq(cur):
    """Get current max Barton sequence number."""
    cur.execute("""
        SELECT MAX(CAST(SPLIT_PART(unique_id, '.', 5) AS INTEGER))
        FROM people.people_master
        WHERE unique_id LIKE %s
    """, (f"{BARTON_PREFIX}.{BARTON_YEAR}.%",))
    result = cur.fetchone()[0]
    return (result or 0)


def make_barton_id(seq):
    """Generate Barton ID from sequence number."""
    suffix = str(seq)[-3:].zfill(3)
    return f"{BARTON_PREFIX}.{BARTON_YEAR}.{seq}.{suffix}"


def fetch_candidates(cur, slot_type):
    """Fetch best Hunter contact per unfilled slot for a given slot_type.

    Returns list of (slot_id, outreach_id, company_unique_id,
                     email, first_name, last_name, job_title,
                     linkedin_url, phone_number)
    """
    # Pull all hunter contacts matching unfilled slots of this type.
    # Uses outreach_id on hunter_contact where available, domain bridge as fallback.
    # We pull into Python to apply title matching (too complex for SQL LIKE).
    cur.execute("""
        SELECT cs.slot_id, cs.outreach_id, cs.company_unique_id,
               hc.email, hc.first_name, hc.last_name,
               COALESCE(NULLIF(hc.job_title, ''), hc.position_raw) AS title,
               hc.linkedin_url, hc.phone_number,
               hc.confidence_score
        FROM people.company_slot cs
        JOIN outreach.outreach o ON o.outreach_id = cs.outreach_id
        JOIN enrichment.hunter_contact hc ON (
            (hc.outreach_id IS NOT NULL AND hc.outreach_id = cs.outreach_id)
            OR (hc.outreach_id IS NULL AND LOWER(hc.domain) = LOWER(o.domain))
        )
        WHERE cs.is_filled = FALSE
          AND cs.slot_type = %s
          AND hc.email IS NOT NULL AND hc.email != ''
          AND hc.first_name IS NOT NULL AND hc.first_name != ''
          AND (hc.job_title IS NOT NULL AND hc.job_title != ''
               OR hc.position_raw IS NOT NULL AND hc.position_raw != '')
          AND NOT EXISTS (
              SELECT 1 FROM people.people_master pm
              WHERE LOWER(pm.email) = LOWER(hc.email)
          )
        ORDER BY cs.outreach_id,
                 (hc.linkedin_url IS NOT NULL AND hc.linkedin_url != '') DESC,
                 COALESCE(hc.confidence_score, 0) DESC
    """, (slot_type,))
    rows = cur.fetchall()

    # Apply Python title matching and deduplicate: best per outreach_id
    best = {}  # outreach_id -> row
    for row in rows:
        slot_id, outreach_id, company_uid, email, first, last, title, li, phone, conf = row
        detected_type = get_slot_type(title)
        if detected_type != slot_type:
            continue
        oid = str(outreach_id)
        if oid not in best:
            best[oid] = (slot_id, outreach_id, company_uid,
                         email, first, last, title, li, phone)

    return list(best.values())


def main():
    parser = argparse.ArgumentParser(description="Promote Hunter contacts to fill empty slots")
    parser.add_argument("--dry-run", action="store_true", help="Preview only")
    parser.add_argument("--slot-type", choices=["CEO", "CFO", "HR"],
                        help="Process only one slot type")
    parser.add_argument("--limit", type=int, default=0,
                        help="Limit fills per slot type (0=unlimited)")
    args = parser.parse_args()

    slot_types = [args.slot_type] if args.slot_type else ["CEO", "CFO", "HR"]

    print("=" * 70)
    print("  PROMOTE HUNTER CONTACTS")
    print("  enrichment.hunter_contact -> people.people_master + company_slot")
    if args.dry_run:
        print("  [DRY RUN]")
    if args.limit:
        print(f"  Limit: {args.limit} per slot type")
    print("=" * 70)

    conn = get_connection()
    cur = conn.cursor()

    grand_total = 0

    for slot_type in slot_types:
        print(f"\n  Processing {slot_type}...")
        start = time.time()

        candidates = fetch_candidates(cur, slot_type)
        if args.limit:
            candidates = candidates[:args.limit]

        print(f"    Candidates found: {len(candidates):,}")

        if not candidates:
            continue

        if args.dry_run:
            grand_total += len(candidates)
            # Show sample
            for c in candidates[:5]:
                slot_id, oid, cuid, email, first, last, title, li, phone = c
                li_flag = "LI" if li else "  "
                print(f"      {first or ''} {last or ''} <{email}> [{title[:30]}] {li_flag}")
            if len(candidates) > 5:
                print(f"      ... and {len(candidates) - 5:,} more")
            continue

        # Get starting Barton sequence
        seq = get_next_barton_seq(cur)
        filled = 0
        errors = 0

        for c in candidates:
            slot_id, oid, company_uid, email, first, last, title, li, phone = c
            try:
                # Double-check slot is still unfilled (concurrent safety)
                cur.execute("""
                    SELECT is_filled FROM people.company_slot WHERE slot_id = %s
                """, (slot_id,))
                row = cur.fetchone()
                if not row or row[0]:
                    continue

                # Double-check email not already in people_master
                cur.execute("""
                    SELECT unique_id FROM people.people_master WHERE LOWER(email) = %s
                """, (email.lower(),))
                existing = cur.fetchone()

                if existing:
                    person_id = existing[0]
                else:
                    seq += 1
                    person_id = make_barton_id(seq)
                    cur.execute("""
                        INSERT INTO people.people_master (
                            unique_id, company_unique_id, company_slot_unique_id,
                            first_name, last_name, email,
                            title, linkedin_url, work_phone_e164,
                            source_system, created_at
                        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, NOW())
                    """, (
                        person_id, company_uid, slot_id,
                        first, last, email,
                        title, li, phone,
                        'hunter_bridge_promotion',
                    ))

                # Fill the slot
                if phone:
                    cur.execute("""
                        UPDATE people.company_slot
                        SET person_unique_id = %s, is_filled = TRUE, filled_at = NOW(),
                            source_system = 'hunter_bridge_promotion',
                            slot_phone = %s, slot_phone_source = 'hunter',
                            slot_phone_updated_at = NOW()
                        WHERE slot_id = %s AND is_filled = FALSE
                    """, (person_id, phone, slot_id))
                else:
                    cur.execute("""
                        UPDATE people.company_slot
                        SET person_unique_id = %s, is_filled = TRUE, filled_at = NOW(),
                            source_system = 'hunter_bridge_promotion'
                        WHERE slot_id = %s AND is_filled = FALSE
                    """, (person_id, slot_id))

                if cur.rowcount == 1:
                    filled += 1

                # Batch commit every 1,000
                if filled % 1000 == 0 and filled > 0:
                    conn.commit()
                    print(f"    ... {filled:,} filled")

            except Exception as e:
                errors += 1
                if errors <= 5:
                    print(f"    ERROR: {email}: {e}")
                conn.rollback()

        conn.commit()
        elapsed = time.time() - start
        grand_total += filled
        print(f"    Filled: {filled:,} {slot_type} slots  ({elapsed:.1f}s)")
        if errors:
            print(f"    Errors: {errors:,}")

    # Summary
    print(f"\n{'=' * 70}")
    if args.dry_run:
        print(f"  [DRY RUN] Would fill: {grand_total:,} slots")
    else:
        print(f"  Total slots filled: {grand_total:,}")

        # Current state
        cur.execute("""
            SELECT slot_type, COUNT(*),
                   COUNT(CASE WHEN is_filled THEN 1 END) AS filled
            FROM people.company_slot
            GROUP BY slot_type ORDER BY slot_type
        """)
        print(f"\n  UPDATED SLOT STATUS:")
        print(f"    {'TYPE':5s} {'TOTAL':>8s} {'FILLED':>8s} {'GAP':>8s} {'FILL%':>6s}")
        for st, tot, filled in cur.fetchall():
            gap = tot - filled
            print(f"    {st:5s} {tot:>8,} {filled:>8,} {gap:>8,} {100*filled/tot:>5.0f}%")

    print(f"{'=' * 70}")
    conn.close()


if __name__ == "__main__":
    main()
