"""
Build 3 CSVs for 28461/100mi market:
  1. Total market (for Clay discovery)
  2. Hunter - NO domain (domain discovery search)
  3. Hunter - HAS domain (contact + email pattern search)

Usage:
    doppler run -- python scripts/build_market_csvs.py
"""
import os
import csv
import psycopg2

ANCHOR_LAT = 33.96607
ANCHOR_LNG = -78.03874
RADIUS = 100

def get_connection():
    return psycopg2.connect(
        host=os.environ["NEON_HOST"],
        dbname=os.environ["NEON_DATABASE"],
        user=os.environ["NEON_USER"],
        password=os.environ["NEON_PASSWORD"],
        sslmode="require",
    )

def main():
    conn = get_connection()
    cur = conn.cursor()

    # Radius ZIPs
    cur.execute("""
        SELECT zip FROM reference.us_zip_codes
        WHERE (3959 * acos(LEAST(1.0, GREATEST(-1.0,
            cos(radians(%s)) * cos(radians(lat)) *
            cos(radians(lng) - radians(%s)) +
            sin(radians(%s)) * sin(radians(lat))
        )))) <= %s
    """, (ANCHOR_LAT, ANCHOR_LNG, ANCHOR_LAT, RADIUS))
    radius_zips = [r[0] for r in cur.fetchall()]
    print(f"Radius ZIPs: {len(radius_zips)}")

    os.makedirs("exports", exist_ok=True)

    # ============================================================
    # EXISTING CT companies in radius
    # ============================================================
    cur.execute("""
        SELECT
            ci.sovereign_company_id,
            ct.outreach_id,
            o.domain,
            ci.company_name,
            TRIM(ct.city) AS city,
            UPPER(TRIM(ct.state)) AS state,
            LEFT(TRIM(ct.postal_code), 5) AS zip,
            ct.email_method,
            CASE WHEN EXISTS (SELECT 1 FROM outreach.dol d WHERE d.outreach_id = ct.outreach_id)
                 THEN 'YES' ELSE '' END AS has_dol,
            CASE WHEN EXISTS (SELECT 1 FROM people.company_slot s
                 WHERE s.outreach_id = ct.outreach_id AND s.slot_type = 'CEO' AND s.is_filled)
                 THEN 'YES' ELSE '' END AS has_ceo,
            CASE WHEN EXISTS (SELECT 1 FROM people.company_slot s
                 WHERE s.outreach_id = ct.outreach_id AND s.slot_type = 'CFO' AND s.is_filled)
                 THEN 'YES' ELSE '' END AS has_cfo,
            CASE WHEN EXISTS (SELECT 1 FROM people.company_slot s
                 WHERE s.outreach_id = ct.outreach_id AND s.slot_type = 'HR' AND s.is_filled)
                 THEN 'YES' ELSE '' END AS has_hr,
            o.ein,
            EXISTS (SELECT 1 FROM people.company_slot s
                WHERE s.outreach_id = ct.outreach_id AND s.slot_type = 'CEO' AND s.is_filled) AS ceo_bool,
            EXISTS (SELECT 1 FROM people.company_slot s
                WHERE s.outreach_id = ct.outreach_id AND s.slot_type = 'CFO' AND s.is_filled) AS cfo_bool,
            EXISTS (SELECT 1 FROM people.company_slot s
                WHERE s.outreach_id = ct.outreach_id AND s.slot_type = 'HR' AND s.is_filled) AS hr_bool
        FROM outreach.company_target ct
        JOIN outreach.outreach o ON o.outreach_id = ct.outreach_id
        JOIN cl.company_identity ci ON ci.outreach_id = ct.outreach_id
        WHERE LEFT(TRIM(ct.postal_code), 5) = ANY(%s)
        ORDER BY UPPER(TRIM(ct.state)), ci.company_name
    """, (radius_zips,))
    existing = cur.fetchall()
    print(f"Existing CT companies: {len(existing):,}")

    # Load CL-minted from CSV
    cl_path = "exports/hunter_enrichment_28461_100mi_with_sovereign_ids.csv"
    with open(cl_path, "r", encoding="utf-8") as f:
        cl_data = [r for r in csv.DictReader(f) if r.get("sovereign_id", "").strip()]
    print(f"CL-minted new companies: {len(cl_data):,}")

    # ============================================================
    # CSV 1: TOTAL MARKET (for Clay)
    # ============================================================
    path1 = "exports/28461_100mi_total_market.csv"
    with open(path1, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow([
            "sovereign_id", "outreach_id", "ein", "company_name", "domain",
            "city", "state", "zip", "email_pattern", "has_dol",
            "has_ceo", "has_cfo", "has_hr", "source",
        ])
        for r in existing:
            w.writerow([
                r[0] or "", r[1], r[12] or "", r[3], r[2] or "",
                r[4], r[5], r[6], r[7] or "", r[8],
                r[9], r[10], r[11], "EXISTING",
            ])
        for r in sorted(cl_data, key=lambda x: (x["state"], x["company_name"])):
            domain = r.get("enriched_domain", "").strip()
            w.writerow([
                r["sovereign_id"], "", r["ein"], r["company_name"], domain,
                r["city"], r["state"], r["zip"], "", "",
                "", "", "", "NEW",
            ])

    total1 = len(existing) + len(cl_data)
    print(f"\nCSV 1: TOTAL MARKET (Clay)")
    print(f"  {path1}")
    print(f"  {len(existing):,} existing + {len(cl_data):,} new = {total1:,} total")

    # ============================================================
    # CSV 2: HUNTER - NO DOMAIN (domain discovery)
    # ============================================================
    no_domain = [r for r in cl_data if not r.get("enriched_domain", "").strip()]

    path2 = "exports/28461_100mi_hunter_no_domain.csv"
    with open(path2, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow([
            "sovereign_id", "ein", "company_name", "city", "state", "zip",
            "participants", "dol_source",
        ])
        for r in sorted(no_domain, key=lambda x: -int(x.get("participants") or 0)):
            w.writerow([
                r["sovereign_id"], r["ein"], r["company_name"],
                r["city"], r["state"], r["zip"],
                r["participants"], r["dol_source"],
            ])

    print(f"\nCSV 2: HUNTER - NO DOMAIN (domain discovery)")
    print(f"  {path2}")
    print(f"  {len(no_domain):,} companies")

    # ============================================================
    # CSV 3: HUNTER - HAS DOMAIN (contact + email pattern search)
    # Existing companies with gaps + New CL companies with domain
    # ============================================================

    # Existing with gaps
    existing_gaps = []
    for r in existing:
        has_pattern = bool(r[7] and r[7].strip())
        domain = r[2]
        if not domain:
            continue
        if not has_pattern or not r[13] or not r[14] or not r[15]:
            existing_gaps.append(r)

    has_domain_new = [r for r in cl_data if r.get("enriched_domain", "").strip()]

    path3 = "exports/28461_100mi_hunter_has_domain.csv"
    with open(path3, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow([
            "sovereign_id", "outreach_id", "ein", "company_name", "domain",
            "city", "state", "zip",
            "has_email_pattern", "has_ceo", "has_cfo", "has_hr", "source",
        ])
        for r in existing_gaps:
            w.writerow([
                r[0] or "", r[1], "", r[3], r[2],
                r[4], r[5], r[6],
                "YES" if (r[7] and r[7].strip()) else "", r[9], r[10], r[11],
                "EXISTING_GAP",
            ])
        for r in sorted(has_domain_new, key=lambda x: (x["state"], x["company_name"])):
            w.writerow([
                r["sovereign_id"], "", r["ein"], r["company_name"],
                r["enriched_domain"],
                r["city"], r["state"], r["zip"],
                "", "", "", "",
                "NEW",
            ])

    total3 = len(existing_gaps) + len(has_domain_new)
    print(f"\nCSV 3: HUNTER - HAS DOMAIN (contact + pattern search)")
    print(f"  {path3}")
    print(f"  {len(existing_gaps):,} existing gaps + {len(has_domain_new):,} new = {total3:,} total")

    # ============================================================
    # SUMMARY
    # ============================================================
    print(f"\n{'='*60}")
    print(f"  SUMMARY")
    print(f"{'='*60}")
    print(f"  CSV 1 (Clay total market):    {total1:>6,}  companies")
    print(f"  CSV 2 (Hunter NO domain):     {len(no_domain):>6,}  companies")
    print(f"  CSV 3 (Hunter HAS domain):    {total3:>6,}  companies")
    print(f"  Hunter total (CSV 2 + 3):     {len(no_domain) + total3:>6,}  companies")
    print(f"{'='*60}")

    conn.close()


if __name__ == "__main__":
    main()
