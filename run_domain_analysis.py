#!/usr/bin/env python3
"""Direct execution of domain-based slot analysis queries."""

import sys
try:
    import psycopg2

    # Direct connection
    conn = psycopg2.connect(
        host='ep-ancient-waterfall-a42vy0du-pooler.us-east-1.aws.neon.tech',
        database='Marketing DB',
        user='Marketing DB_owner',
        password='npg_OsE4Z2oPCpiT',
        sslmode='require'
    )
    cur = conn.cursor()

    print("=" * 80)
    print("DOMAIN-BASED SLOT FILLING ANALYSIS (READ-ONLY)")
    print("=" * 80)
    print()

    # Query 1
    print("[1/6] Hunter domains matchable via outreach.outreach.domain")
    cur.execute("""
        SELECT COUNT(DISTINCT hc.domain)
        FROM enrichment.hunter_contact hc
        JOIN outreach.outreach o ON LOWER(hc.domain) = LOWER(o.domain)
    """)
    result = cur.fetchone()[0]
    print(f"Matchable Hunter domains: {result:,}")
    print()

    # Query 2
    print("[2/6] CEO slot fill potential")
    cur.execute("""
        SELECT COUNT(*)
        FROM people.company_slot cs
        JOIN outreach.outreach o ON cs.outreach_id = o.outreach_id
        JOIN enrichment.hunter_contact hc ON LOWER(o.domain) = LOWER(hc.domain)
        WHERE cs.slot_type = 'CEO'
          AND cs.is_filled = FALSE
          AND cs.person_unique_id IS NULL
          AND (hc.job_title ILIKE '%chief executive%'
               OR hc.job_title ILIKE '%ceo%'
               OR (hc.job_title ILIKE '%president%' AND hc.job_title NOT ILIKE '%vice%'))
    """)
    ceo_fillable = cur.fetchone()[0]

    cur.execute("""
        SELECT COUNT(*)
        FROM people.company_slot
        WHERE slot_type = 'CEO' AND is_filled = FALSE AND person_unique_id IS NULL
    """)
    ceo_total = cur.fetchone()[0]

    pct = (ceo_fillable / ceo_total * 100) if ceo_total > 0 else 0
    print(f"Fillable CEO slots: {ceo_fillable:,} of {ceo_total:,} ({pct:.1f}%)")
    print()

    # Query 3
    print("[3/6] CFO slot fill potential")
    cur.execute("""
        SELECT COUNT(*)
        FROM people.company_slot cs
        JOIN outreach.outreach o ON cs.outreach_id = o.outreach_id
        JOIN enrichment.hunter_contact hc ON LOWER(o.domain) = LOWER(hc.domain)
        WHERE cs.slot_type = 'CFO'
          AND cs.is_filled = FALSE
          AND cs.person_unique_id IS NULL
          AND (hc.job_title ILIKE '%chief financial%'
               OR hc.job_title ILIKE '%cfo%')
    """)
    cfo_fillable = cur.fetchone()[0]

    cur.execute("""
        SELECT COUNT(*)
        FROM people.company_slot
        WHERE slot_type = 'CFO' AND is_filled = FALSE AND person_unique_id IS NULL
    """)
    cfo_total = cur.fetchone()[0]

    pct = (cfo_fillable / cfo_total * 100) if cfo_total > 0 else 0
    print(f"Fillable CFO slots: {cfo_fillable:,} of {cfo_total:,} ({pct:.1f}%)")
    print()

    # Query 4
    print("[4/6] HR slot fill potential")
    cur.execute("""
        SELECT COUNT(*)
        FROM people.company_slot cs
        JOIN outreach.outreach o ON cs.outreach_id = o.outreach_id
        JOIN enrichment.hunter_contact hc ON LOWER(o.domain) = LOWER(hc.domain)
        WHERE cs.slot_type = 'HR'
          AND cs.is_filled = FALSE
          AND cs.person_unique_id IS NULL
          AND (hc.job_title ILIKE '%human resources%'
               OR hc.job_title ILIKE '%hr director%'
               OR hc.job_title ILIKE '%hr manager%')
    """)
    hr_fillable = cur.fetchone()[0]

    cur.execute("""
        SELECT COUNT(*)
        FROM people.company_slot
        WHERE slot_type = 'HR' AND is_filled = FALSE AND person_unique_id IS NULL
    """)
    hr_total = cur.fetchone()[0]

    pct = (hr_fillable / hr_total * 100) if hr_total > 0 else 0
    print(f"Fillable HR slots: {hr_fillable:,} of {hr_total:,} ({pct:.1f}%)")
    print()

    # Query 5
    print("[5/6] Sample CEO slot fills (top 5 by confidence score)")
    print("-" * 80)
    cur.execute("""
        SELECT
            o.domain,
            hc.first_name,
            hc.last_name,
            hc.job_title,
            hc.email,
            hc.confidence_score
        FROM people.company_slot cs
        JOIN outreach.outreach o ON cs.outreach_id = o.outreach_id
        JOIN enrichment.hunter_contact hc ON LOWER(o.domain) = LOWER(hc.domain)
        WHERE cs.slot_type = 'CEO'
          AND cs.is_filled = FALSE
          AND cs.person_unique_id IS NULL
          AND (hc.job_title ILIKE '%ceo%' OR hc.job_title ILIKE '%chief executive%')
        ORDER BY hc.confidence_score DESC NULLS LAST
        LIMIT 5
    """)

    for i, row in enumerate(cur.fetchall(), 1):
        domain, fname, lname, title, email, score = row
        print(f"{i}. {domain}")
        print(f"   Name: {fname} {lname}")
        print(f"   Title: {title}")
        print(f"   Email: {email}")
        print(f"   Score: {score if score else 'N/A'}")
        print()

    # Query 6
    print("[6/6] Schema check: outreach.company_target.domain column")
    cur.execute("""
        SELECT EXISTS (
            SELECT 1 FROM information_schema.columns
            WHERE table_schema = 'outreach'
              AND table_name = 'company_target'
              AND column_name = 'domain'
        )
    """)
    has_domain = cur.fetchone()[0]
    print(f"Domain column exists in outreach.company_target: {has_domain}")
    print(f"Note: Domain is stored in outreach.outreach table (FK join via outreach_id)")
    print()

    print("=" * 80)
    print("ANALYSIS COMPLETE")
    print("=" * 80)

    cur.close()
    conn.close()

except Exception as e:
    print(f"ERROR: {e}", file=sys.stderr)
    sys.exit(1)
