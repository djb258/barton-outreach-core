"""
Resolve the final ZIP gap:
1. Exclude confirmed international companies
2. Fix US companies with sloppy state data (full names, lowercase)
3. Geocode newly-fixable US companies
4. Check remaining against blog/Hunter for last-mile fixes
5. Exclude anything left with no US evidence

Usage:
    doppler run -- python scripts/resolve_final_zip_gap.py
    doppler run -- python scripts/resolve_final_zip_gap.py --apply
"""

import argparse
import os
import re
import sys
import time

import psycopg2

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")

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

# Also handle sloppy abbreviations
SLOPPY_STATE = {
    "tx": "TX", "pa": "PA", "ga": "GA", "nc": "NC", "oh": "OH",
    "va": "VA", "md": "MD", "il": "IL", "co": "CO", "ky": "KY",
}

# Known non-US cities/regions
NON_US_CITIES = {
    "singapore", "bengaluru", "mumbai", "new delhi", "pune", "noida",
    "hyderabad", "hyderābād", "ahmedabad", "nanjing", "navi mumbai",
    "kolkata", "chennai", "raipur", "rāipur", "guangzhou", "gurgaon",
    "tokyo", "london", "toronto", "montreal", "sydney", "melbourne",
    "dublin", "amsterdam", "zurich", "paris", "berlin", "minato-ku",
    "maharashtra", "goodwood", "bangalore",
}

# Non-US country TLDs
INTL_TLDS = {
    ".uk", ".co.uk", ".ca", ".au", ".com.au", ".de", ".fr", ".nl",
    ".in", ".co.in", ".jp", ".cn", ".za", ".co.za", ".be", ".se",
    ".dk", ".no", ".ie", ".ch", ".at", ".sg", ".nz", ".co.nz",
    ".ru", ".br", ".co.kr", ".kr", ".hk", ".tw", ".ph", ".pk",
    ".ge", ".ee", ".coop",
}


def is_international_domain(domain):
    """Check if domain has an international TLD."""
    d = domain.lower()
    for tld in INTL_TLDS:
        if d.endswith(tld):
            return True
    return False


def is_non_us_city(city):
    """Check if city is a known non-US city."""
    if not city:
        return False
    return city.lower().strip() in NON_US_CITIES


def normalize_state_value(val):
    """Try to normalize a sloppy state value to a 2-letter US state."""
    if not val:
        return None
    v = val.strip()
    if len(v) == 2:
        up = v.upper()
        if up in SLOPPY_STATE.values() or up in [s for s in STATE_ABBREV.values()]:
            return up
    lookup = STATE_ABBREV.get(v.lower())
    if lookup:
        return lookup
    lookup = SLOPPY_STATE.get(v.lower())
    if lookup:
        return lookup
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
    parser = argparse.ArgumentParser(description="Resolve final ZIP gap")
    parser.add_argument("--apply", action="store_true", help="Apply changes")
    args = parser.parse_args()

    conn = get_connection()
    cur = conn.cursor()

    # Baseline
    cur.execute("""
        SELECT COUNT(*) FROM outreach.company_target
        WHERE postal_code IS NULL OR TRIM(postal_code) = ''
    """)
    total_gap = cur.fetchone()[0]

    print(f"{'='*65}")
    print(f"  Final ZIP Gap Resolution — {total_gap:,} companies")
    print(f"{'='*65}")

    # ================================================================
    # PASS 1: Fix sloppy US state values in CT
    # Full state names, lowercase abbreviations -> proper 2-letter
    # ================================================================
    cur.execute("""
        SELECT outreach_id, city, state
        FROM outreach.company_target
        WHERE (postal_code IS NULL OR TRIM(postal_code) = '')
          AND state IS NOT NULL AND TRIM(state) != ''
    """)
    sloppy_fixes = []
    for oid, city, state in cur.fetchall():
        if is_non_us_city(city):
            continue
        normalized = normalize_state_value(state)
        if normalized and normalized != state.strip():
            sloppy_fixes.append((normalized, oid))

    print(f"\n  Pass 1 — Fix sloppy state values: {len(sloppy_fixes):,}")
    if sloppy_fixes and args.apply:
        for new_state, oid in sloppy_fixes:
            cur.execute("""
                UPDATE outreach.company_target
                SET state = %s, country = 'US'
                WHERE outreach_id = %s
            """, (new_state, oid))
        print(f"    Fixed: {len(sloppy_fixes):,}")

    # Also fix city values that are actually state names
    cur.execute("""
        SELECT outreach_id, city
        FROM outreach.company_target
        WHERE (postal_code IS NULL OR TRIM(postal_code) = '')
          AND (state IS NULL OR TRIM(state) = '')
          AND city IS NOT NULL AND TRIM(city) != ''
    """)
    city_is_state = []
    for oid, city in cur.fetchall():
        normalized = normalize_state_value(city)
        if normalized:
            city_is_state.append((normalized, oid))

    print(f"  Pass 1b — City is actually a state name: {len(city_is_state):,}")
    if city_is_state and args.apply:
        for new_state, oid in city_is_state:
            cur.execute("""
                UPDATE outreach.company_target
                SET state = %s, city = NULL, country = 'US'
                WHERE outreach_id = %s
            """, (new_state, oid))
        print(f"    Fixed: {len(city_is_state):,}")

    # ================================================================
    # PASS 2: Geocode newly-fixable companies (city+state -> ZIP)
    # ================================================================
    if args.apply:
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
                ORDER BY ct.outreach_id, z.population DESC NULLS LAST
            )
            UPDATE outreach.company_target ct
            SET postal_code = bz.zip,
                postal_code_source = 'CITY_STATE_GEOCODE',
                postal_code_updated_at = NOW()
            FROM best_zip bz
            WHERE bz.outreach_id = ct.outreach_id
              AND (ct.postal_code IS NULL OR TRIM(ct.postal_code) = '')
        """)
        geocoded = cur.rowcount
        print(f"\n  Pass 2 — Geocode city+state -> ZIP: {geocoded:,}")

        # Backfill city+state from reference for new ZIPs
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
        cur.execute("""
            UPDATE outreach.company_target
            SET country = 'US'
            WHERE (country IS NULL OR TRIM(country) = '')
              AND postal_code IS NOT NULL AND TRIM(postal_code) != ''
        """)

    # ================================================================
    # PASS 3: Tag international companies
    # ================================================================
    cur.execute("""
        SELECT ct.outreach_id, o.domain, ct.city, ct.country
        FROM outreach.company_target ct
        JOIN outreach.outreach o ON o.outreach_id = ct.outreach_id
        WHERE ct.postal_code IS NULL OR TRIM(ct.postal_code) = ''
    """)
    remaining = cur.fetchall()

    intl_by_country = []
    intl_by_tld = []
    intl_by_city = []
    still_unknown = []

    for oid, domain, city, country in remaining:
        if country and country.strip() and country.strip().upper() not in ('US', 'USA', 'UNITED STATES'):
            intl_by_country.append(oid)
        elif is_international_domain(domain):
            intl_by_tld.append(oid)
        elif is_non_us_city(city):
            intl_by_city.append(oid)
        else:
            still_unknown.append((oid, domain, city))

    total_intl = len(intl_by_country) + len(intl_by_tld) + len(intl_by_city)
    print(f"\n  Pass 3 — International identification:")
    print(f"    By country:  {len(intl_by_country):,}")
    print(f"    By TLD:      {len(intl_by_tld):,}")
    print(f"    By city:     {len(intl_by_city):,}")
    print(f"    Total intl:  {total_intl:,}")
    print(f"    Remaining:   {len(still_unknown):,}")

    # ================================================================
    # COMMIT and report
    # ================================================================
    if args.apply:
        conn.commit()

    # Final state
    cur.execute("""
        SELECT
            COUNT(*) AS total,
            COUNT(CASE WHEN postal_code IS NOT NULL AND TRIM(postal_code) != '' THEN 1 END) AS has_zip,
            COUNT(CASE WHEN postal_code IS NULL OR TRIM(postal_code) = '' THEN 1 END) AS no_zip
        FROM outreach.company_target
    """)
    r = cur.fetchone()
    print(f"\n  {'='*65}")
    print(f"  CURRENT STATE:")
    print(f"    CT total:         {r[0]:,}")
    print(f"    With postal_code: {r[1]:,} ({100*r[1]/r[0]:.1f}%)")
    print(f"    Missing:          {r[2]:,} ({100*r[2]/r[0]:.1f}%)")
    print(f"      International:  ~{total_intl:,}")
    print(f"      US/unknown:     ~{len(still_unknown):,}")

    if still_unknown:
        print(f"\n  Remaining US/unknown (sample):")
        for oid, domain, city in still_unknown[:20]:
            print(f"    {domain:35s} {(city or '-'):20s}")

    if not args.apply:
        print(f"\n  [DRY RUN] Add --apply to commit changes")

    conn.close()
    print(f"\n{'='*65}")
    print(f"  Done.")
    print(f"{'='*65}")


if __name__ == "__main__":
    main()
