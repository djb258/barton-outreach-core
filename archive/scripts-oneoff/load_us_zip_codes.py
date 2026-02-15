"""
Load US zip codes from uszips.xlsx into reference.us_zip_codes in Neon.

Usage:
    doppler run -- python scripts/load_us_zip_codes.py
    doppler run -- python scripts/load_us_zip_codes.py --dry-run
"""

import argparse
import json
import os
import sys
import time

import openpyxl
import psycopg2
from psycopg2.extras import execute_values


XLSX_PATH = r"C:\Users\CUSTOM PC\Desktop\uszips.xlsx"

COLUMNS = [
    "zip", "lat", "lng", "city", "state_id", "state_name",
    "zcta", "parent_zcta", "population", "density",
    "county_fips", "county_name", "county_weights", "county_names_all",
    "county_fips_all", "imprecise", "military", "timezone",
    "age_median", "male", "female", "married", "family_size",
    "income_household_median", "income_household_six_figure",
    "home_ownership", "home_value", "rent_median",
    "education_college_or_above", "labor_force_participation",
    "unemployment_rate", "race_white", "race_black", "race_asian",
    "race_native", "race_pacific", "race_other", "race_multiple",
]

MIGRATION_SQL = open(
    os.path.join(os.path.dirname(__file__), "..", "neon", "migrations",
                 "2026-02-10-us-zip-codes-reference.sql")
).read()


def parse_bool(val):
    if val is None:
        return None
    if isinstance(val, bool):
        return val
    s = str(val).strip().upper()
    return s in ("TRUE", "1", "YES")


def parse_int(val):
    if val is None:
        return None
    try:
        return int(float(val))
    except (ValueError, TypeError):
        return None


def parse_float(val):
    if val is None:
        return None
    try:
        return float(val)
    except (ValueError, TypeError):
        return None


def parse_json(val):
    if val is None:
        return None
    if isinstance(val, dict):
        return json.dumps(val)
    try:
        parsed = json.loads(str(val))
        return json.dumps(parsed)
    except (json.JSONDecodeError, TypeError):
        return None


def transform_row(raw_row):
    """Transform a raw Excel row into DB-ready tuple."""
    r = dict(zip(COLUMNS, raw_row))

    return (
        str(r["zip"]).zfill(5) if r["zip"] is not None else None,  # preserve leading zeros
        parse_float(r["lat"]),
        parse_float(r["lng"]),
        str(r["city"]).strip() if r["city"] else None,
        str(r["state_id"]).strip() if r["state_id"] else None,
        str(r["state_name"]).strip() if r["state_name"] else None,
        parse_bool(r["zcta"]),
        str(r["parent_zcta"]).strip() if r["parent_zcta"] else None,
        parse_int(r["population"]),
        parse_float(r["density"]),
        str(r["county_fips"]).strip() if r["county_fips"] else None,
        str(r["county_name"]).strip() if r["county_name"] else None,
        parse_json(r["county_weights"]),
        str(r["county_names_all"]).strip() if r["county_names_all"] else None,
        str(r["county_fips_all"]).strip() if r["county_fips_all"] else None,
        parse_bool(r["imprecise"]),
        parse_bool(r["military"]),
        str(r["timezone"]).strip() if r["timezone"] else None,
        parse_float(r["age_median"]),
        parse_float(r["male"]),
        parse_float(r["female"]),
        parse_float(r["married"]),
        parse_float(r["family_size"]),
        parse_int(r["income_household_median"]),
        parse_float(r["income_household_six_figure"]),
        parse_float(r["home_ownership"]),
        parse_int(r["home_value"]),
        parse_int(r["rent_median"]),
        parse_float(r["education_college_or_above"]),
        parse_float(r["labor_force_participation"]),
        parse_float(r["unemployment_rate"]),
        parse_float(r["race_white"]),
        parse_float(r["race_black"]),
        parse_float(r["race_asian"]),
        parse_float(r["race_native"]),
        parse_float(r["race_pacific"]),
        parse_float(r["race_other"]),
        parse_float(r["race_multiple"]),
    )


def main():
    parser = argparse.ArgumentParser(description="Load US zip codes into Neon")
    parser.add_argument("--dry-run", action="store_true", help="Preview without writing")
    args = parser.parse_args()

    print(f"Reading {XLSX_PATH}...")
    wb = openpyxl.load_workbook(XLSX_PATH, read_only=True)
    ws = wb.active

    rows = []
    for i, row in enumerate(ws.iter_rows(values_only=True)):
        if i == 0:
            continue  # skip header
        transformed = transform_row(row)
        if transformed[0] is not None:
            rows.append(transformed)

    wb.close()
    print(f"Read {len(rows):,} zip codes from Excel")

    # Sample output
    print(f"\nSample rows:")
    for r in rows[:3]:
        print(f"  {r[0]} | {r[3]}, {r[4]} | pop={r[8]} | income=${r[23]}")

    # State distribution
    states = {}
    for r in rows:
        st = r[4] or "UNKNOWN"
        states[st] = states.get(st, 0) + 1
    print(f"\nStates/territories: {len(states)}")
    top5 = sorted(states.items(), key=lambda x: -x[1])[:5]
    for st, cnt in top5:
        print(f"  {st}: {cnt:,} zips")

    if args.dry_run:
        print("\n[DRY RUN] Would insert {0:,} rows into reference.us_zip_codes".format(len(rows)))
        return

    # Connect and load
    conn = psycopg2.connect(
        host=os.environ["NEON_HOST"],
        dbname=os.environ["NEON_DATABASE"],
        user=os.environ["NEON_USER"],
        password=os.environ["NEON_PASSWORD"],
        sslmode="require",
    )
    cur = conn.cursor()

    # Run migration (idempotent)
    print("\nRunning migration (CREATE SCHEMA + TABLE IF NOT EXISTS)...")
    cur.execute(MIGRATION_SQL)
    conn.commit()
    print("Migration complete.")

    # Check if already loaded
    cur.execute("SELECT COUNT(*) FROM reference.us_zip_codes")
    existing = cur.fetchone()[0]
    if existing > 0:
        print(f"\nTable already has {existing:,} rows. Truncating and reloading...")
        cur.execute("TRUNCATE reference.us_zip_codes")
        conn.commit()

    # Bulk insert in batches
    insert_sql = """
        INSERT INTO reference.us_zip_codes (
            zip, lat, lng, city, state_id, state_name,
            zcta, parent_zcta, population, density,
            county_fips, county_name, county_weights, county_names_all,
            county_fips_all, imprecise, military, timezone,
            age_median, male, female, married, family_size,
            income_household_median, income_household_six_figure,
            home_ownership, home_value, rent_median,
            education_college_or_above, labor_force_participation,
            unemployment_rate, race_white, race_black, race_asian,
            race_native, race_pacific, race_other, race_multiple
        ) VALUES %s
    """

    batch_size = 2000
    total_inserted = 0
    start = time.time()

    for i in range(0, len(rows), batch_size):
        batch = rows[i:i + batch_size]
        execute_values(cur, insert_sql, batch, page_size=batch_size)
        conn.commit()
        total_inserted += len(batch)
        elapsed = time.time() - start
        print(f"  Inserted {total_inserted:,} / {len(rows):,} ({elapsed:.1f}s)")

    elapsed = time.time() - start
    print(f"\nDone. Loaded {total_inserted:,} zip codes in {elapsed:.1f}s")

    # Verify
    cur.execute("SELECT COUNT(*) FROM reference.us_zip_codes")
    final = cur.fetchone()[0]
    cur.execute("SELECT COUNT(DISTINCT state_id) FROM reference.us_zip_codes")
    state_count = cur.fetchone()[0]
    cur.execute("SELECT state_id, COUNT(*) FROM reference.us_zip_codes GROUP BY state_id ORDER BY COUNT(*) DESC LIMIT 5")
    top_states = cur.fetchall()

    print(f"\nVerification:")
    print(f"  Total rows: {final:,}")
    print(f"  States/territories: {state_count}")
    print(f"  Top 5 by zip count:")
    for st, cnt in top_states:
        print(f"    {st}: {cnt:,}")

    # Register in CTB
    cur.execute("""
        INSERT INTO ctb.table_registry (table_schema, table_name, leaf_type, is_frozen, notes)
        VALUES ('reference', 'us_zip_codes', 'REGISTRY', FALSE, 'US zip code reference with demographics. Source: SimpleMaps uszips.xlsx')
        ON CONFLICT DO NOTHING
    """)
    conn.commit()
    print("\nRegistered in CTB registry as REGISTRY leaf type.")

    conn.close()


if __name__ == "__main__":
    main()
