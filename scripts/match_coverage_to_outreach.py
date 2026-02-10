"""Match coverage ZIPs to outreach companies. Read-only analysis."""
import os, sys, psycopg2

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")

COVERAGE_ID = sys.argv[1] if len(sys.argv) > 1 else None
if not COVERAGE_ID:
    print("Usage: doppler run -- python scripts/match_coverage_to_outreach.py <coverage_id>")
    sys.exit(1)

conn = psycopg2.connect(
    host=os.environ["NEON_HOST"],
    dbname=os.environ["NEON_DATABASE"],
    user=os.environ["NEON_USER"],
    password=os.environ["NEON_PASSWORD"],
    sslmode="require",
)
cur = conn.cursor()

# Verify coverage exists
cur.execute(
    "SELECT anchor_zip, radius_miles, status FROM coverage.service_agent_coverage WHERE coverage_id = %s",
    (COVERAGE_ID,),
)
row = cur.fetchone()
if not row:
    print(f"Coverage {COVERAGE_ID} not found")
    sys.exit(1)
print(f"Coverage: anchor={row[0]}, radius={row[1]}mi, status={row[2]}")

# Count ZIPs in coverage
cur.execute(
    "SELECT COUNT(*) FROM coverage.v_service_agent_coverage_zips WHERE coverage_id = %s",
    (COVERAGE_ID,),
)
zip_count = cur.fetchone()[0]
print(f"ZIPs in coverage: {zip_count:,}")

# ============================================================
# Match 1: CT postal_code
# ============================================================
print("\n=== Match via CT postal_code ===")
cur.execute("""
    SELECT
        ct.outreach_id,
        o.domain,
        ci.company_name,
        ct.postal_code,
        ct.city,
        ct.state,
        cz.distance_miles
    FROM coverage.v_service_agent_coverage_zips cz
    JOIN outreach.company_target ct
        ON LEFT(TRIM(ct.postal_code), 5) = cz.zip
    JOIN outreach.outreach o ON o.outreach_id = ct.outreach_id
    JOIN cl.company_identity ci ON ci.outreach_id = ct.outreach_id
    WHERE cz.coverage_id = %s
      AND ct.postal_code IS NOT NULL
      AND LENGTH(TRIM(ct.postal_code)) >= 5
    ORDER BY cz.distance_miles
""", (COVERAGE_ID,))

ct_rows = cur.fetchall()
print(f"CT postal_code matches: {len(ct_rows)}")

if ct_rows:
    print("\n  Nearest 10:")
    for r in ct_rows[:10]:
        name = (r[2] or "")[:40]
        print(f"    {r[3]:>5s} | {r[5] or '??':>2s} | {r[6]:>6.1f} mi | {name:40s} | {r[1]}")

    print(f"\n  Farthest 5:")
    for r in ct_rows[-5:]:
        name = (r[2] or "")[:40]
        print(f"    {r[3]:>5s} | {r[5] or '??':>2s} | {r[6]:>6.1f} mi | {name:40s} | {r[1]}")

    states = {}
    for r in ct_rows:
        st = r[5] or "UNKNOWN"
        states[st] = states.get(st, 0) + 1
    print(f"\n  By state:")
    for st, cnt in sorted(states.items(), key=lambda x: -x[1]):
        print(f"    {st}: {cnt}")

# ============================================================
# Match 2: DOL EIN -> form_5500 ZIP bridge
# ============================================================
print("\n=== Match via DOL ZIP bridge (form_5500 sponsor ZIP) ===")
cur.execute("""
    SELECT COUNT(DISTINCT dz.outreach_id)
    FROM (
        SELECT DISTINCT d.outreach_id,
               LEFT(TRIM(f.spons_dfe_loc_us_zip), 5) AS dol_zip
        FROM outreach.dol d
        JOIN dol.form_5500 f ON f.spons_dfe_ein = d.ein
        WHERE f.spons_dfe_loc_us_zip IS NOT NULL
          AND LENGTH(TRIM(f.spons_dfe_loc_us_zip)) >= 5
    ) dz
    JOIN coverage.v_service_agent_coverage_zips cz
        ON dz.dol_zip = cz.zip
    WHERE cz.coverage_id = %s
""", (COVERAGE_ID,))
dol_match = cur.fetchone()[0]
print(f"DOL ZIP bridge matches: {dol_match:,}")

# ============================================================
# Combined unique
# ============================================================
print("\n=== Combined (CT + DOL, deduplicated) ===")
cur.execute("""
    SELECT COUNT(DISTINCT outreach_id) FROM (
        SELECT ct.outreach_id
        FROM coverage.v_service_agent_coverage_zips cz
        JOIN outreach.company_target ct
            ON LEFT(TRIM(ct.postal_code), 5) = cz.zip
        WHERE cz.coverage_id = %s
          AND ct.postal_code IS NOT NULL
          AND LENGTH(TRIM(ct.postal_code)) >= 5
        UNION
        SELECT dz.outreach_id
        FROM (
            SELECT DISTINCT d.outreach_id,
                   LEFT(TRIM(f.spons_dfe_loc_us_zip), 5) AS dol_zip
            FROM outreach.dol d
            JOIN dol.form_5500 f ON f.spons_dfe_ein = d.ein
            WHERE f.spons_dfe_loc_us_zip IS NOT NULL
              AND LENGTH(TRIM(f.spons_dfe_loc_us_zip)) >= 5
        ) dz
        JOIN coverage.v_service_agent_coverage_zips cz
            ON dz.dol_zip = cz.zip
        WHERE cz.coverage_id = %s
    ) combined
""", (COVERAGE_ID, COVERAGE_ID))
total_unique = cur.fetchone()[0]
print(f"Total unique outreach companies in coverage: {total_unique:,}")

# ============================================================
# Sub-hub readiness for matched companies
# ============================================================
if total_unique > 0:
    print("\n=== Sub-hub readiness for matched companies ===")
    cur.execute("""
        WITH matched AS (
            SELECT ct.outreach_id
            FROM coverage.v_service_agent_coverage_zips cz
            JOIN outreach.company_target ct
                ON LEFT(TRIM(ct.postal_code), 5) = cz.zip
            WHERE cz.coverage_id = %s
              AND ct.postal_code IS NOT NULL
              AND LENGTH(TRIM(ct.postal_code)) >= 5
            UNION
            SELECT dz.outreach_id
            FROM (
                SELECT DISTINCT d.outreach_id,
                       LEFT(TRIM(f.spons_dfe_loc_us_zip), 5) AS dol_zip
                FROM outreach.dol d
                JOIN dol.form_5500 f ON f.spons_dfe_ein = d.ein
                WHERE f.spons_dfe_loc_us_zip IS NOT NULL
                  AND LENGTH(TRIM(f.spons_dfe_loc_us_zip)) >= 5
            ) dz
            JOIN coverage.v_service_agent_coverage_zips cz
                ON dz.dol_zip = cz.zip
            WHERE cz.coverage_id = %s
        )
        SELECT
            COUNT(*) AS total,
            COUNT(ct.email_method) FILTER (WHERE ct.email_method IS NOT NULL) AS ct_ready,
            COUNT(d.outreach_id) AS dol_ready,
            COUNT(d.outreach_id) FILTER (WHERE d.filing_present = TRUE) AS dol_filing,
            COUNT(d.renewal_month) AS dol_renewal,
            COUNT(DISTINCT cs_ceo.outreach_id) FILTER (WHERE cs_ceo.is_filled = TRUE) AS ceo_filled,
            COUNT(DISTINCT cs_cfo.outreach_id) FILTER (WHERE cs_cfo.is_filled = TRUE) AS cfo_filled,
            COUNT(DISTINCT cs_hr.outreach_id) FILTER (WHERE cs_hr.is_filled = TRUE) AS hr_filled,
            COUNT(b.outreach_id) AS blog_ready,
            COUNT(bs.outreach_id) AS bit_scored
        FROM matched m
        JOIN outreach.company_target ct ON ct.outreach_id = m.outreach_id
        LEFT JOIN outreach.dol d ON d.outreach_id = m.outreach_id
        LEFT JOIN people.company_slot cs_ceo ON cs_ceo.outreach_id = m.outreach_id AND cs_ceo.slot_type = 'CEO'
        LEFT JOIN people.company_slot cs_cfo ON cs_cfo.outreach_id = m.outreach_id AND cs_cfo.slot_type = 'CFO'
        LEFT JOIN people.company_slot cs_hr ON cs_hr.outreach_id = m.outreach_id AND cs_hr.slot_type = 'HR'
        LEFT JOIN outreach.blog b ON b.outreach_id = m.outreach_id
        LEFT JOIN outreach.bit_scores bs ON bs.outreach_id = m.outreach_id
    """, (COVERAGE_ID, COVERAGE_ID))

    r = cur.fetchone()
    total = r[0]
    print(f"  Total companies:     {total:,}")
    print(f"  CT ready (email):    {r[1]:,} ({100*r[1]/total:.1f}%)")
    print(f"  DOL linked:          {r[2]:,} ({100*r[2]/total:.1f}%)")
    print(f"  DOL filing present:  {r[3]:,} ({100*r[3]/total:.1f}%)")
    print(f"  DOL renewal month:   {r[4]:,} ({100*r[4]/total:.1f}%)")
    print(f"  CEO slot filled:     {r[5]:,} ({100*r[5]/total:.1f}%)")
    print(f"  CFO slot filled:     {r[6]:,} ({100*r[6]/total:.1f}%)")
    print(f"  HR slot filled:      {r[7]:,} ({100*r[7]/total:.1f}%)")
    print(f"  Blog present:        {r[8]:,} ({100*r[8]/total:.1f}%)")
    print(f"  BIT scored:          {r[9]:,} ({100*r[9]/total:.1f}%)")

conn.close()
print("\nDone.")
