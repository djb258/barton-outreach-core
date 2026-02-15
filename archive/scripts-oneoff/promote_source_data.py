#!/usr/bin/env python3
"""
Promote Source Data to Production
=================================
Three steps:
  1. Link Hunter contacts to outreach via domain match
  2. Fill empty slots from newly-linked Hunter contacts
  3. Promote Clay intake matches to people_master and fill slots

Usage:
    doppler run -- python scripts/promote_source_data.py [--dry-run]

Created: 2026-02-09
"""
import os
import sys
from datetime import datetime

if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

import psycopg2

BARTON_PREFIX = "04.04.02"
BARTON_YEAR = "26"
BATCH_SIZE = 1000

# ── Job title keywords (same as fill_slots_from_hunter.py) ──
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


def get_slot_type(job_title):
    if not job_title:
        return None
    t = job_title.lower()
    for kw in CFO_KEYWORDS:
        if kw in t:
            return 'CFO'
    for kw in HR_KEYWORDS:
        if kw in t:
            return 'HR'
    for kw in CEO_KEYWORDS:
        if kw in t:
            return 'CEO'
    return None


def get_connection():
    url = os.getenv("DATABASE_URL")
    if not url:
        print("[FAIL] DATABASE_URL not set")
        sys.exit(1)
    return psycopg2.connect(url)


_barton_seq = None

def get_next_barton_id(cursor):
    global _barton_seq
    if _barton_seq is None:
        cursor.execute("""
            SELECT MAX(CAST(SPLIT_PART(unique_id, '.', 5) AS INTEGER))
            FROM people.people_master WHERE unique_id LIKE %s
        """, (BARTON_PREFIX + "." + BARTON_YEAR + ".%",))
        _barton_seq = (cursor.fetchone()[0] or 0)
    _barton_seq += 1
    suffix = str(_barton_seq)[-3:].zfill(3)
    return "{}.{}.{}.{}".format(BARTON_PREFIX, BARTON_YEAR, _barton_seq, suffix)


# ═══════════════════════════════════════════════════════════════════
# STEP 1: Link Hunter contacts by domain
# ═══════════════════════════════════════════════════════════════════
def step1_link_hunter(conn, dry_run):
    print("\n" + "=" * 60)
    print("STEP 1: Link Hunter contacts by domain")
    print("=" * 60)

    cur = conn.cursor()

    cur.execute("""
        SELECT COUNT(*) FROM enrichment.hunter_contact WHERE outreach_id IS NULL
    """)
    unlinked = cur.fetchone()[0]
    print("  Unlinked Hunter contacts:    {:,}".format(unlinked))

    # Count how many can be linked
    cur.execute("""
        SELECT COUNT(*)
        FROM enrichment.hunter_contact hc
        WHERE hc.outreach_id IS NULL
          AND LOWER(hc.domain) IN (SELECT LOWER(domain) FROM outreach.outreach)
    """)
    linkable = cur.fetchone()[0]
    print("  Linkable by domain:          {:,}".format(linkable))

    if linkable == 0:
        print("  Nothing to link.")
        cur.close()
        return 0

    if dry_run:
        print("  [DRY RUN] Would link {:,} Hunter contacts".format(linkable))
        cur.close()
        return linkable

    # Execute the link
    cur.execute("""
        UPDATE enrichment.hunter_contact hc
        SET outreach_id = oo.outreach_id
        FROM outreach.outreach oo
        WHERE LOWER(hc.domain) = LOWER(oo.domain)
          AND hc.outreach_id IS NULL
    """)
    linked = cur.rowcount
    conn.commit()
    print("  Linked: {:,}".format(linked))

    # Verify
    cur.execute("SELECT COUNT(*) FROM enrichment.hunter_contact WHERE outreach_id IS NOT NULL")
    total_linked = cur.fetchone()[0]
    cur.execute("SELECT COUNT(*) FROM enrichment.hunter_contact")
    total = cur.fetchone()[0]
    print("  Hunter linked total now:     {:,} / {:,} ({:.1f}%)".format(
        total_linked, total, total_linked / total * 100))

    cur.close()
    return linked


# ═══════════════════════════════════════════════════════════════════
# STEP 2: Fill empty slots from Hunter (now linked)
# ═══════════════════════════════════════════════════════════════════
def step2_fill_slots_hunter(conn, dry_run):
    print("\n" + "=" * 60)
    print("STEP 2: Fill empty slots from Hunter contacts")
    print("=" * 60)

    cur = conn.cursor()

    # Build title SQL filters
    def title_filter(keywords):
        return "(" + " OR ".join(
            ["LOWER(hc.job_title) LIKE '%" + kw + "%'" for kw in keywords]
        ) + ")"

    # Find all fillable (empty_slot, best_hunter_contact) pairs via domain JOIN
    candidates = []
    for stype, keywords in [('CEO', CEO_KEYWORDS), ('CFO', CFO_KEYWORDS), ('HR', HR_KEYWORDS)]:
        tf = title_filter(keywords)
        query = """
            SELECT * FROM (
                SELECT DISTINCT ON (cs.slot_id)
                    cs.slot_id,
                    cs.outreach_id,
                    cs.slot_type,
                    cs.company_unique_id,
                    hc.email,
                    hc.first_name,
                    hc.last_name,
                    hc.job_title,
                    hc.phone_number,
                    hc.linkedin_url
                FROM people.company_slot cs
                JOIN outreach.outreach oo ON oo.outreach_id = cs.outreach_id
                JOIN enrichment.hunter_contact hc
                    ON LOWER(oo.domain) = LOWER(hc.domain)
                    AND hc.email IS NOT NULL AND hc.email != ''
                    AND hc.first_name IS NOT NULL AND hc.first_name != ''
                    AND """ + tf + """
                WHERE cs.is_filled = FALSE
                  AND cs.person_unique_id IS NULL
                  AND cs.slot_type = '""" + stype + """'
                ORDER BY cs.slot_id, hc.confidence_score DESC NULLS LAST
            ) sub
        """
        cur.execute(query)
        candidates.extend(cur.fetchall())

    print("  Empty slot candidates found: {:,}".format(len(candidates)))

    if not candidates:
        print("  No candidates.")
        cur.close()
        return 0, 0

    # Breakdown
    type_counts = {}
    for row in candidates:
        st = row[2]
        type_counts[st] = type_counts.get(st, 0) + 1
    for st in sorted(type_counts):
        print("    {}: {:,}".format(st, type_counts[st]))

    if dry_run:
        print("  [DRY RUN] Would fill {:,} slots".format(len(candidates)))
        cur.close()
        return len(candidates), 0

    # Fill slots
    slots_filled = 0
    people_created = 0
    errors = 0

    for i, row in enumerate(candidates):
        (slot_id, outreach_id, slot_type, company_unique_id,
         email, first_name, last_name, job_title, phone, linkedin) = row

        if i > 0 and i % BATCH_SIZE == 0:
            conn.commit()
            print("  Progress: {:,}/{:,} filled".format(slots_filled, len(candidates)))

        try:
            # Check if person exists
            cur.execute("SELECT unique_id FROM people.people_master WHERE LOWER(email) = LOWER(%s)", (email,))
            person_row = cur.fetchone()

            if person_row:
                person_id = person_row[0]
            else:
                if not company_unique_id:
                    errors += 1
                    continue
                person_id = get_next_barton_id(cur)
                cur.execute("""
                    INSERT INTO people.people_master (
                        unique_id, company_unique_id, company_slot_unique_id,
                        first_name, last_name, email, title,
                        linkedin_url, work_phone_e164, source_system, created_at
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, 'hunter', NOW())
                """, (person_id, company_unique_id, slot_id,
                      first_name, last_name, email.lower(), job_title,
                      linkedin if linkedin else None,
                      phone if phone else None))
                people_created += 1

            # Update slot
            if phone:
                cur.execute("""
                    UPDATE people.company_slot
                    SET person_unique_id = %s, is_filled = TRUE, filled_at = NOW(),
                        source_system = 'hunter', slot_phone = %s,
                        slot_phone_source = 'hunter', slot_phone_updated_at = NOW()
                    WHERE slot_id = %s
                """, (person_id, phone, slot_id))
            else:
                cur.execute("""
                    UPDATE people.company_slot
                    SET person_unique_id = %s, is_filled = TRUE, filled_at = NOW(),
                        source_system = 'hunter'
                    WHERE slot_id = %s
                """, (person_id, slot_id))
            slots_filled += 1

        except Exception as e:
            errors += 1
            conn.rollback()

    conn.commit()
    print("  Slots filled:   {:,}".format(slots_filled))
    print("  People created: {:,}".format(people_created))
    if errors:
        print("  Errors:         {:,}".format(errors))
    cur.close()
    return slots_filled, people_created


# ═══════════════════════════════════════════════════════════════════
# STEP 3: Promote Clay intake to people_master + fill slots
# ═══════════════════════════════════════════════════════════════════
def step3_promote_clay(conn, dry_run):
    print("\n" + "=" * 60)
    print("STEP 3: Promote Clay intake to people_master + fill slots")
    print("=" * 60)

    cur = conn.cursor()

    # Find Clay people that match CL companies and have a slot_type
    # AND target an empty slot
    cur.execute("""
        SELECT
            pri.id,
            pri.first_name,
            pri.last_name,
            pri.title,
            pri.linkedin_url,
            pri.work_phone,
            pri.slot_type,
            ci.company_unique_id,
            ci.outreach_id,
            cs.slot_id
        FROM intake.people_raw_intake pri
        JOIN cl.company_identity ci
            ON LOWER(TRIM(pri.company_name)) = LOWER(TRIM(ci.company_name))
            AND ci.outreach_id IS NOT NULL
        JOIN people.company_slot cs
            ON cs.outreach_id = ci.outreach_id
            AND cs.slot_type = pri.slot_type
            AND cs.is_filled = FALSE
            AND cs.person_unique_id IS NULL
        WHERE pri.slot_type IN ('CEO', 'CFO', 'HR')
          AND pri.first_name IS NOT NULL AND pri.first_name != ''
          AND pri.last_name IS NOT NULL AND pri.last_name != ''
    """)
    candidates = cur.fetchall()
    print("  Clay candidates (match company + empty slot): {:,}".format(len(candidates)))

    if not candidates:
        print("  No candidates.")
        cur.close()
        return 0, 0

    # Deduplicate: one candidate per slot_id (prefer one with LinkedIn)
    slot_best = {}
    for row in candidates:
        slot_id = row[9]
        has_li = row[4] is not None and row[4] != ''
        if slot_id not in slot_best:
            slot_best[slot_id] = row
        elif has_li and not (slot_best[slot_id][4] is not None and slot_best[slot_id][4] != ''):
            slot_best[slot_id] = row

    unique_candidates = list(slot_best.values())
    print("  Unique slot fills:           {:,}".format(len(unique_candidates)))

    # Breakdown
    type_counts = {}
    li_count = 0
    for row in unique_candidates:
        st = row[6]
        type_counts[st] = type_counts.get(st, 0) + 1
        if row[4]:
            li_count += 1
    for st in sorted(type_counts):
        print("    {}: {:,}".format(st, type_counts[st]))
    print("    With LinkedIn: {:,}".format(li_count))

    if dry_run:
        print("  [DRY RUN] Would fill {:,} slots from Clay".format(len(unique_candidates)))
        cur.close()
        return len(unique_candidates), 0

    # Fill slots
    slots_filled = 0
    people_created = 0
    errors = 0

    for i, row in enumerate(unique_candidates):
        (pri_id, first_name, last_name, title, linkedin,
         phone, slot_type, company_unique_id, outreach_id, slot_id) = row

        if i > 0 and i % BATCH_SIZE == 0:
            conn.commit()
            print("  Progress: {:,}/{:,} filled".format(slots_filled, len(unique_candidates)))

        try:
            # Check if person already exists (by name + company)
            cur.execute("""
                SELECT unique_id FROM people.people_master
                WHERE LOWER(TRIM(first_name)) = LOWER(TRIM(%s))
                  AND LOWER(TRIM(last_name)) = LOWER(TRIM(%s))
                  AND company_unique_id = %s::text
            """, (first_name, last_name, str(company_unique_id)))
            person_row = cur.fetchone()

            if person_row:
                person_id = person_row[0]
                # Update LinkedIn if missing
                if linkedin:
                    cur.execute("""
                        UPDATE people.people_master
                        SET linkedin_url = %s
                        WHERE unique_id = %s
                          AND (linkedin_url IS NULL OR linkedin_url = '')
                    """, (linkedin, person_id))
            else:
                person_id = get_next_barton_id(cur)
                cur.execute("""
                    INSERT INTO people.people_master (
                        unique_id, company_unique_id, company_slot_unique_id,
                        first_name, last_name, title,
                        linkedin_url, work_phone_e164, source_system, created_at
                    ) VALUES (%s, %s::text, %s, %s, %s, %s, %s, %s, 'clay', NOW())
                """, (person_id, str(company_unique_id), slot_id,
                      first_name, last_name, title,
                      linkedin if linkedin else None,
                      phone if phone else None))
                people_created += 1

            # Fill the slot
            cur.execute("""
                UPDATE people.company_slot
                SET person_unique_id = %s, is_filled = TRUE, filled_at = NOW(),
                    source_system = 'clay'
                WHERE slot_id = %s AND is_filled = FALSE
            """, (person_id, slot_id))

            if cur.rowcount > 0:
                slots_filled += 1

        except Exception as e:
            errors += 1
            conn.rollback()

    conn.commit()
    print("  Slots filled:   {:,}".format(slots_filled))
    print("  People created: {:,}".format(people_created))
    if errors:
        print("  Errors:         {:,}".format(errors))
    cur.close()
    return slots_filled, people_created


# ═══════════════════════════════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════════════════════════════
def main():
    dry_run = '--dry-run' in sys.argv

    print("=" * 60)
    print("PROMOTE SOURCE DATA TO PRODUCTION")
    print("=" * 60)
    print("Mode: {}".format("DRY RUN" if dry_run else "LIVE"))
    print("Started: {}".format(datetime.now().isoformat()))

    conn = get_connection()
    print("Connected to database.")

    # Step 1
    linked = step1_link_hunter(conn, dry_run)

    # Step 2
    s2_filled, s2_created = step2_fill_slots_hunter(conn, dry_run)

    # Step 3
    s3_filled, s3_created = step3_promote_clay(conn, dry_run)

    conn.close()

    # Final summary
    print("\n" + "=" * 60)
    print("FINAL SUMMARY")
    print("=" * 60)
    prefix = "Would " if dry_run else ""
    print("  Step 1: {}link {:,} Hunter contacts by domain".format(prefix, linked))
    print("  Step 2: {}fill {:,} slots from Hunter ({:,} new people)".format(prefix, s2_filled, s2_created))
    print("  Step 3: {}fill {:,} slots from Clay ({:,} new people)".format(prefix, s3_filled, s3_created))
    print("  TOTAL:  {}fill {:,} slots, {:,} new people".format(prefix, s2_filled + s3_filled, s2_created + s3_created))
    print("\nCompleted: {}".format(datetime.now().isoformat()))


if __name__ == "__main__":
    main()
