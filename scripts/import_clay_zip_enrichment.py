"""
Import Clay ZIP enrichment back into CT.

1. Load Clay CSV, extract outreach_id + Zip Code + State + Company Address
2. Bulk UPDATE CT postal_code where we got a ZIP
3. Backfill city+state from reference.us_zip_codes for new ZIPs
4. For rows Clay returned city+state but no ZIP, reverse-geocode from reference
5. Backfill country='US' for anything with a state

Usage:
    doppler run -- python scripts/import_clay_zip_enrichment.py <csv_path>
    doppler run -- python scripts/import_clay_zip_enrichment.py <csv_path> --apply
"""

import argparse
import csv
import os
import re
import sys
import time

import psycopg2
from psycopg2.extras import execute_values

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")

# US state name -> abbreviation
STATE_ABBREV = {
    "alabama": "AL", "alaska": "AK", "arizona": "AZ", "arkansas": "AR",
    "california": "CA", "colorado": "CO", "connecticut": "CT", "delaware": "DE",
    "district of columbia": "DC", "florida": "FL", "georgia": "GA", "hawaii": "HI",
    "idaho": "ID", "illinois": "IL", "indiana": "IN", "iowa": "IA", "kansas": "KS",
    "kentucky": "KY", "louisiana": "LA", "maine": "ME", "maryland": "MD",
    "massachusetts": "MA", "michigan": "MI", "minnesota": "MN", "mississippi": "MS",
    "missouri": "MO", "montana": "MT", "nebraska": "NE", "nevada": "NV",
    "new hampshire": "NH", "new jersey": "NJ", "new mexico": "NM", "new york": "NY",
    "north carolina": "NC", "north dakota": "ND", "ohio": "OH", "oklahoma": "OK",
    "oregon": "OR", "pennsylvania": "PA", "rhode island": "RI", "south carolina": "SC",
    "south dakota": "SD", "tennessee": "TN", "texas": "TX", "utah": "UT",
    "vermont": "VT", "virginia": "VA", "washington": "WA", "west virginia": "WV",
    "wisconsin": "WI", "wyoming": "WY",
}


def normalize_state(raw):
    """Normalize state to 2-letter abbreviation."""
    if not raw:
        return None
    s = raw.strip()
    if len(s) == 2:
        return s.upper()
    lookup = STATE_ABBREV.get(s.lower())
    if lookup:
        return lookup
    return s.upper()[:2] if len(s) > 2 else None


def normalize_zip(raw):
    """Extract 5-digit ZIP from various formats."""
    if not raw:
        return None
    s = raw.strip()
    m = re.match(r'^(\d{5})', s)
    return m.group(1) if m else None


def parse_city_from_address(addr):
    """Try to extract city from Clay's full address string.
    Format: '215 Racine Dr #102, Wilmington, North Carolina 28403, us'
    """
    if not addr:
        return None
    parts = [p.strip() for p in addr.split(",")]
    if len(parts) >= 3:
        return parts[-3].strip().title() if len(parts) >= 4 else parts[-2].strip().title()
    return None


def get_connection():
    return psycopg2.connect(
        host=os.environ["NEON_HOST"],
        dbname=os.environ["NEON_DATABASE"],
        user=os.environ["NEON_USER"],
        password=os.environ["NEON_PASSWORD"],
        sslmode="require",
    )


def main():
    parser = argparse.ArgumentParser(description="Import Clay ZIP enrichment into CT")
    parser.add_argument("csv_path", help="Path to Clay export CSV")
    parser.add_argument("--apply", action="store_true", help="Apply changes (default: dry-run)")
    args = parser.parse_args()

    # ================================================================
    # Load CSV
    # ================================================================
    with open(args.csv_path, encoding="utf-8") as f:
        reader = csv.DictReader(f)
        rows = list(reader)

    print(f"{'='*65}")
    print(f"  Clay ZIP Enrichment Import")
    print(f"{'='*65}")
    print(f"\n  CSV rows: {len(rows):,}")

    # Parse out what we need
    records = []
    for r in rows:
        oid = r.get("outreach_id", "").strip()
        if not oid:
            continue
        zip_code = normalize_zip(r.get("Zip Code", ""))
        state = normalize_state(r.get("State", ""))
        address = r.get("Company Address", "").strip()
        city = parse_city_from_address(address)
        records.append((oid, zip_code, state, city, address))

    has_zip = sum(1 for _, z, _, _, _ in records if z)
    has_state = sum(1 for _, _, s, _, _ in records if s)
    has_city = sum(1 for _, _, _, c, _ in records if c)
    no_zip_has_state = sum(1 for _, z, s, _, _ in records if not z and s)

    print(f"  Parsed records: {len(records):,}")
    print(f"    With ZIP:     {has_zip:,}")
    print(f"    With state:   {has_state:,}")
    print(f"    With city:    {has_city:,}")
    print(f"    No ZIP but has state: {no_zip_has_state:,}")

    conn = get_connection()
    cur = conn.cursor()

    # Baseline
    cur.execute("""
        SELECT
            COUNT(*) AS total,
            COUNT(CASE WHEN postal_code IS NOT NULL AND TRIM(postal_code) != '' THEN 1 END) AS has_zip
        FROM outreach.company_target
    """)
    total, before_zip = cur.fetchone()
    print(f"\n  CT BEFORE:")
    print(f"    With postal_code: {before_zip:,} / {total:,} ({100*before_zip/total:.1f}%)")

    # ================================================================
    # Stage into temp table
    # ================================================================
    cur.execute("""
        CREATE TEMP TABLE tmp_clay_zip (
            outreach_id UUID,
            clay_zip TEXT,
            clay_state TEXT,
            clay_city TEXT,
            clay_address TEXT
        )
    """)

    execute_values(cur, """
        INSERT INTO tmp_clay_zip (outreach_id, clay_zip, clay_state, clay_city, clay_address)
        VALUES %s
    """, records)
    print(f"\n  Staged {len(records):,} rows into temp table")

    # ================================================================
    # Pass 1: Update CT where Clay returned a valid ZIP
    # ================================================================
    cur.execute("""
        SELECT COUNT(*)
        FROM tmp_clay_zip t
        JOIN outreach.company_target ct ON ct.outreach_id = t.outreach_id
        WHERE t.clay_zip IS NOT NULL
          AND (ct.postal_code IS NULL OR TRIM(ct.postal_code) = '')
    """)
    pass1_candidates = cur.fetchone()[0]
    print(f"\n  Pass 1 — Clay ZIP -> CT postal_code")
    print(f"    Candidates: {pass1_candidates:,}")

    if args.apply and pass1_candidates > 0:
        cur.execute("""
            UPDATE outreach.company_target ct
            SET postal_code = t.clay_zip,
                postal_code_source = 'CLAY_ENRICHMENT',
                postal_code_updated_at = NOW()
            FROM tmp_clay_zip t
            WHERE t.outreach_id = ct.outreach_id
              AND t.clay_zip IS NOT NULL
              AND (ct.postal_code IS NULL OR TRIM(ct.postal_code) = '')
        """)
        print(f"    Applied: {cur.rowcount:,}")

    # ================================================================
    # Pass 2: For new ZIPs, backfill city+state from reference
    # ================================================================
    if args.apply:
        cur.execute("""
            UPDATE outreach.company_target ct
            SET city = z.city
            FROM reference.us_zip_codes z
            WHERE z.zip = LEFT(TRIM(ct.postal_code), 5)
              AND ct.postal_code IS NOT NULL AND TRIM(ct.postal_code) != ''
              AND (ct.city IS NULL OR TRIM(ct.city) = '')
        """)
        city_filled = cur.rowcount

        cur.execute("""
            UPDATE outreach.company_target ct
            SET state = z.state_id
            FROM reference.us_zip_codes z
            WHERE z.zip = LEFT(TRIM(ct.postal_code), 5)
              AND ct.postal_code IS NOT NULL AND TRIM(ct.postal_code) != ''
              AND (ct.state IS NULL OR TRIM(ct.state) = '')
        """)
        state_filled = cur.rowcount

        print(f"\n  Pass 2 — Backfill city+state from reference ZIP")
        print(f"    City filled:  {city_filled:,}")
        print(f"    State filled: {state_filled:,}")

    # ================================================================
    # Pass 3: Clay returned state but no ZIP — reverse geocode
    # ================================================================
    cur.execute("""
        SELECT COUNT(*)
        FROM tmp_clay_zip t
        JOIN outreach.company_target ct ON ct.outreach_id = t.outreach_id
        WHERE t.clay_zip IS NULL
          AND t.clay_city IS NOT NULL
          AND t.clay_state IS NOT NULL
          AND (ct.postal_code IS NULL OR TRIM(ct.postal_code) = '')
    """)
    pass3_candidates = cur.fetchone()[0]
    print(f"\n  Pass 3 — Reverse geocode Clay city+state -> ZIP")
    print(f"    Candidates: {pass3_candidates:,}")

    if args.apply and pass3_candidates > 0:
        # First update CT city+state from Clay where missing
        cur.execute("""
            UPDATE outreach.company_target ct
            SET city = t.clay_city,
                state = t.clay_state
            FROM tmp_clay_zip t
            WHERE t.outreach_id = ct.outreach_id
              AND t.clay_city IS NOT NULL
              AND (ct.city IS NULL OR TRIM(ct.city) = '')
        """)

        cur.execute("""
            UPDATE outreach.company_target ct
            SET state = t.clay_state
            FROM tmp_clay_zip t
            WHERE t.outreach_id = ct.outreach_id
              AND t.clay_state IS NOT NULL
              AND (ct.state IS NULL OR TRIM(ct.state) = '')
        """)

        # Now reverse geocode: city+state -> most populous ZIP
        cur.execute("""
            WITH best_zip AS (
                SELECT DISTINCT ON (ct.outreach_id)
                    ct.outreach_id,
                    z.zip
                FROM outreach.company_target ct
                JOIN reference.us_zip_codes z
                    ON UPPER(z.city) = UPPER(TRIM(ct.city))
                   AND UPPER(z.state_id) = UPPER(TRIM(ct.state))
                WHERE (ct.postal_code IS NULL OR TRIM(ct.postal_code) = '')
                  AND ct.city IS NOT NULL AND TRIM(ct.city) != ''
                  AND ct.state IS NOT NULL AND TRIM(ct.state) != ''
                  AND ct.outreach_id IN (SELECT outreach_id FROM tmp_clay_zip WHERE clay_zip IS NULL)
                ORDER BY ct.outreach_id, z.population DESC NULLS LAST
            )
            UPDATE outreach.company_target ct
            SET postal_code = bz.zip,
                postal_code_source = 'CLAY_CITY_STATE_GEOCODE',
                postal_code_updated_at = NOW()
            FROM best_zip bz
            WHERE bz.outreach_id = ct.outreach_id
              AND (ct.postal_code IS NULL OR TRIM(ct.postal_code) = '')
        """)
        print(f"    Geocoded: {cur.rowcount:,}")

        # Backfill city+state from reference for the geocoded ones
        cur.execute("""
            UPDATE outreach.company_target ct
            SET city = z.city
            FROM reference.us_zip_codes z
            WHERE z.zip = LEFT(TRIM(ct.postal_code), 5)
              AND ct.postal_code IS NOT NULL AND TRIM(ct.postal_code) != ''
              AND (ct.city IS NULL OR TRIM(ct.city) = '')
        """)
        cur.execute("""
            UPDATE outreach.company_target ct
            SET state = z.state_id
            FROM reference.us_zip_codes z
            WHERE z.zip = LEFT(TRIM(ct.postal_code), 5)
              AND ct.postal_code IS NOT NULL AND TRIM(ct.postal_code) != ''
              AND (ct.state IS NULL OR TRIM(ct.state) = '')
        """)

    # ================================================================
    # Pass 4: Backfill country='US' for anything with state
    # ================================================================
    if args.apply:
        cur.execute("""
            UPDATE outreach.company_target
            SET country = 'US'
            WHERE (country IS NULL OR TRIM(country) = '')
              AND state IS NOT NULL AND TRIM(state) != ''
        """)
        print(f"\n  Pass 4 — Country backfill: {cur.rowcount:,}")

    # ================================================================
    # Commit and verify
    # ================================================================
    if args.apply:
        conn.commit()

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
        print(f"\n  CT AFTER:")
        print(f"    postal_code: {r[1]:,} / {r[0]:,} ({100*r[1]/r[0]:.1f}%)  +{r[1]-before_zip:,}")
        print(f"    city:        {r[2]:,} / {r[0]:,} ({100*r[2]/r[0]:.1f}%)")
        print(f"    state:       {r[3]:,} / {r[0]:,} ({100*r[3]/r[0]:.1f}%)")
        print(f"    country:     {r[4]:,} / {r[0]:,} ({100*r[4]/r[0]:.1f}%)")

        # Source breakdown
        cur.execute("""
            SELECT postal_code_source, COUNT(*)
            FROM outreach.company_target
            WHERE postal_code_source IS NOT NULL
            GROUP BY postal_code_source
            ORDER BY COUNT(*) DESC
        """)
        print(f"\n  By source:")
        for row in cur.fetchall():
            print(f"    {row[0]}: {row[1]:,}")

        remaining = r[0] - r[1]
        print(f"\n  Still missing ZIP: {remaining:,} ({100*remaining/r[0]:.1f}%)")
    else:
        print(f"\n  [DRY RUN] Add --apply to commit changes")

    conn.close()
    print(f"\n{'='*65}")
    print(f"  Done.")
    print(f"{'='*65}")


if __name__ == "__main__":
    main()
