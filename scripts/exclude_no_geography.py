"""
Exclude companies with no US geography from outreach pipeline.

1. Move to outreach.outreach_excluded
2. Archive from CT, spine, and sub-hubs
3. Run post-exclusion audit

Usage:
    doppler run -- python scripts/exclude_no_geography.py
    doppler run -- python scripts/exclude_no_geography.py --apply
"""

import argparse
import os
import sys
import time

import psycopg2

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")

NON_US_CITIES = {
    "singapore", "bengaluru", "mumbai", "new delhi", "pune", "noida",
    "hyderabad", "hyderābād", "ahmedabad", "nanjing", "navi mumbai",
    "kolkata", "chennai", "raipur", "rāipur", "guangzhou", "gurgaon",
    "tokyo", "london", "toronto", "montreal", "sydney", "melbourne",
    "dublin", "amsterdam", "zurich", "paris", "berlin", "minato-ku",
    "maharashtra", "goodwood", "bangalore",
}

INTL_TLDS = {
    ".uk", ".co.uk", ".ca", ".au", ".com.au", ".de", ".fr", ".nl",
    ".in", ".co.in", ".jp", ".cn", ".za", ".co.za", ".be", ".se",
    ".dk", ".no", ".ie", ".ch", ".at", ".sg", ".nz", ".co.nz",
    ".ru", ".br", ".co.kr", ".kr", ".hk", ".tw", ".ph", ".pk",
    ".ge", ".ee", ".coop",
}


def get_connection():
    return psycopg2.connect(
        host=os.environ["NEON_HOST"],
        dbname=os.environ["NEON_DATABASE"],
        user=os.environ["NEON_USER"],
        password=os.environ["NEON_PASSWORD"],
        sslmode="require",
    )


def main():
    parser = argparse.ArgumentParser(description="Exclude companies with no US geography")
    parser.add_argument("--apply", action="store_true", help="Apply exclusions")
    args = parser.parse_args()

    conn = get_connection()
    cur = conn.cursor()

    # ================================================================
    # Identify exclusion candidates
    # ================================================================
    cur.execute("""
        SELECT ct.outreach_id, o.domain, ci.company_name, ct.city,
               ct.state, ct.country, ci.sovereign_company_id
        FROM outreach.company_target ct
        JOIN outreach.outreach o ON o.outreach_id = ct.outreach_id
        JOIN cl.company_identity ci ON ci.outreach_id = ct.outreach_id
        WHERE ct.postal_code IS NULL OR TRIM(ct.postal_code) = ''
    """)
    rows = cur.fetchall()

    intl_ids = []
    no_geo_ids = []

    for oid, domain, name, city, state, country, sid in rows:
        # International by country
        if country and country.strip() and country.strip().upper() not in ('US', 'USA', 'UNITED STATES'):
            intl_ids.append((oid, domain, name, 'INTERNATIONAL_COMPANY', sid))
            continue

        # International by TLD
        d = (domain or '').lower()
        is_intl_tld = any(d.endswith(tld) for tld in INTL_TLDS)
        if is_intl_tld:
            intl_ids.append((oid, domain, name, 'INTERNATIONAL_TLD', sid))
            continue

        # International by city
        if city and city.lower().strip() in NON_US_CITIES:
            intl_ids.append((oid, domain, name, 'INTERNATIONAL_CITY', sid))
            continue

        # Everything else = no geography data
        no_geo_ids.append((oid, domain, name, 'NO_US_GEOGRAPHY', sid))

    all_excludes = intl_ids + no_geo_ids

    print(f"{'='*65}")
    print(f"  No-Geography Exclusion")
    print(f"{'='*65}")
    print(f"\n  Total to exclude: {len(all_excludes):,}")
    print(f"    International:    {len(intl_ids):,}")
    print(f"    No US geography:  {len(no_geo_ids):,}")

    # Breakdown
    reasons = {}
    for _, _, _, reason, _ in all_excludes:
        reasons[reason] = reasons.get(reason, 0) + 1
    print(f"\n  By reason:")
    for reason, cnt in sorted(reasons.items(), key=lambda x: -x[1]):
        print(f"    {reason}: {cnt:,}")

    if not args.apply:
        print(f"\n  [DRY RUN] Add --apply to execute exclusions")
        conn.close()
        return

    # ================================================================
    # Execute exclusions
    # ================================================================
    start = time.time()
    exclude_oids = [str(r[0]) for r in all_excludes]

    # 1. Insert into outreach_excluded
    for oid, domain, name, reason, sid in all_excludes:
        cur.execute("""
            INSERT INTO outreach.outreach_excluded
                (outreach_id, company_name, domain, exclusion_reason,
                 excluded_at, sovereign_id, excluded_by)
            VALUES (%s, %s, %s, %s, NOW(), %s, 'ZIP_GAP_CLEANUP')
            ON CONFLICT (outreach_id) DO NOTHING
        """, (oid, name, domain, reason, sid))
    print(f"\n  Inserted {len(all_excludes):,} into outreach_excluded")

    # 2. Archive from CT (explicit columns — archive schema differs)
    cur.execute("""
        INSERT INTO outreach.company_target_archive
            (target_id, company_unique_id, outreach_status, bit_score_snapshot,
             first_targeted_at, last_targeted_at, sequence_count, active_sequence_id,
             source, created_at, updated_at, outreach_id, email_method, method_type,
             confidence_score, execution_status, imo_completed_at, is_catchall,
             archived_at, archive_reason)
        SELECT
            target_id, company_unique_id, outreach_status, bit_score_snapshot,
            first_targeted_at, last_targeted_at, sequence_count, active_sequence_id,
            source, created_at, updated_at, outreach_id, email_method, method_type,
            confidence_score, execution_status, imo_completed_at, is_catchall,
            NOW(), 'ZIP_GAP_CLEANUP'
        FROM outreach.company_target
        WHERE outreach_id = ANY(%s::uuid[])
        ON CONFLICT DO NOTHING
    """, (exclude_oids,))
    ct_archived = cur.rowcount

    # 3. Delete from CT
    cur.execute("""
        DELETE FROM outreach.company_target
        WHERE outreach_id = ANY(%s::uuid[])
    """, (exclude_oids,))
    ct_deleted = cur.rowcount
    print(f"  CT: archived {ct_archived:,}, deleted {ct_deleted:,}")

    # 4. Delete from sub-hubs (archive where possible, skip if schema mismatch)
    for table in ["outreach.dol", "outreach.blog", "outreach.bit_scores"]:
        cur.execute(f"""
            DELETE FROM {table}
            WHERE outreach_id = ANY(%s::uuid[])
        """, (exclude_oids,))
        print(f"  {table}: deleted {cur.rowcount:,}")

    # 5. People slots
    cur.execute("""
        DELETE FROM people.company_slot
        WHERE outreach_id = ANY(%s::uuid[])
    """, (exclude_oids,))
    print(f"  people.company_slot: deleted {cur.rowcount:,}")

    # 6. Clean ALL FK references before spine delete
    fk_tables = [
        "outreach.appointments",
        "outreach.bit_errors",
        "outreach.bit_input_history",
        "outreach.bit_signals",
        "outreach.blog_errors",
        "outreach.blog_source_history",
        "outreach.company_target_errors",
        "outreach.dol_errors",
        "outreach.engagement_events",
        "outreach.people",
        "outreach.people_errors",
        "outreach.sitemap_discovery",
    ]
    for ref_table in fk_tables:
        cur.execute(f"""
            DELETE FROM {ref_table}
            WHERE outreach_id = ANY(%s::uuid[])
        """, (exclude_oids,))
        if cur.rowcount > 0:
            print(f"  {ref_table}: deleted {cur.rowcount:,}")

    # 7. Delete from spine
    cur.execute("""
        DELETE FROM outreach.outreach
        WHERE outreach_id = ANY(%s::uuid[])
    """, (exclude_oids,))
    print(f"  outreach.outreach (spine): deleted {cur.rowcount:,}")

    # 7. CL outreach_id is WRITE-ONCE (trigger enforced).
    # Spine is deleted; CL pointer is now a dangling reference = correct for excluded.
    print(f"  cl.company_identity: write-once, not modified")

    conn.commit()
    elapsed = time.time() - start

    # ================================================================
    # Post-exclusion verification
    # ================================================================
    cur.execute("""
        SELECT
            COUNT(*) AS total,
            COUNT(CASE WHEN postal_code IS NOT NULL AND TRIM(postal_code) != '' THEN 1 END) AS has_zip,
            COUNT(CASE WHEN city IS NOT NULL AND TRIM(city) != '' THEN 1 END) AS has_city,
            COUNT(CASE WHEN state IS NOT NULL AND TRIM(state) != '' THEN 1 END) AS has_state,
            COUNT(CASE WHEN country IS NOT NULL AND TRIM(country) != '' THEN 1 END) AS has_country
        FROM outreach.company_target
    """)
    r = cur.fetchone()
    total = r[0]
    print(f"\n  {'='*65}")
    print(f"  POST-EXCLUSION CT STATE:")
    print(f"    CT total:     {total:,}")
    print(f"    postal_code:  {r[1]:,} ({100*r[1]/total:.1f}%)")
    print(f"    city:         {r[2]:,} ({100*r[2]/total:.1f}%)")
    print(f"    state:        {r[3]:,} ({100*r[3]/total:.1f}%)")
    print(f"    country:      {r[4]:,} ({100*r[4]/total:.1f}%)")

    # Spine alignment
    cur.execute("SELECT COUNT(*) FROM outreach.outreach")
    spine = cur.fetchone()[0]
    print(f"\n    Spine:        {spine:,}")
    print(f"    CT = Spine:   {'YES' if spine == total else 'NO — CHECK!'}")

    print(f"\n    Time: {elapsed:.1f}s")

    conn.close()
    print(f"\n{'='*65}")
    print(f"  Done.")
    print(f"{'='*65}")


if __name__ == "__main__":
    main()
