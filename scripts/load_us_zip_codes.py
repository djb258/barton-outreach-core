"""
Load SimpleMaps v1.94 uszips.csv into reference.us_zip_codes (Neon PostgreSQL).

Usage:
    doppler run -- python scripts/load_us_zip_codes.py

Steps:
  1. Read CSV with pandas
  2. Coerce all types per schema
  3. TRUNCATE + bulk INSERT in a single transaction via COPY (psycopg2 copy_expert)
  4. Run 6 verification queries
"""

import io
import os
import sys

import pandas as pd
import psycopg2
import psycopg2.extras

CSV_PATH = r"C:\Users\CUSTOM PC\Desktop\uszips.csv"

# Columns that are nullable integers in the DB but arrive as float (NaN) from pandas
INT_COLS = {"population", "income_household_median", "home_value", "rent_median"}

# Columns that are boolean
BOOL_COLS = {"zcta", "imprecise", "military"}

# Columns that must be NULL when the string is empty
NULLABLE_TEXT_COLS = {"parent_zcta"}

# Columns that arrive as numeric but may be empty strings
NUMERIC_COLS = {
    "lat", "lng", "density",
    "age_median", "male", "female", "married", "family_size",
    "income_household_six_figure", "home_ownership",
    "education_college_or_above", "labor_force_participation", "unemployment_rate",
    "race_white", "race_black", "race_asian", "race_native",
    "race_pacific", "race_other", "race_multiple",
}

# Ordered column list matching DB (excludes created_at — it defaults to NOW())
DB_COLUMNS = [
    "zip", "lat", "lng", "city", "state_id", "state_name",
    "zcta", "parent_zcta", "population", "density",
    "county_fips", "county_name", "county_weights",
    "county_names_all", "county_fips_all",
    "imprecise", "military", "timezone",
    "age_median", "male", "female", "married", "family_size",
    "income_household_median", "income_household_six_figure",
    "home_ownership", "home_value", "rent_median",
    "education_college_or_above", "labor_force_participation", "unemployment_rate",
    "race_white", "race_black", "race_asian", "race_native",
    "race_pacific", "race_other", "race_multiple",
]


def coerce_row(row: dict) -> tuple:
    """Convert a raw CSV row dict into an ordered tuple of Python-native values."""
    out = []
    for col in DB_COLUMNS:
        val = row.get(col, "")

        # --- zip: always text, preserve leading zeros ---
        if col == "zip":
            out.append(str(val).strip())
            continue

        # --- boolean columns ---
        if col in BOOL_COLS:
            s = str(val).strip().upper()
            out.append(True if s == "TRUE" else False)
            continue

        # --- nullable text (empty string → None) ---
        if col in NULLABLE_TEXT_COLS:
            s = str(val).strip()
            out.append(None if s == "" else s)
            continue

        # --- county_weights: jsonb — pass raw string, psycopg2 will cast ---
        if col == "county_weights":
            s = str(val).strip()
            out.append(s if s else None)
            continue

        # --- integer columns ---
        if col in INT_COLS:
            s = str(val).strip()
            out.append(int(float(s)) if s != "" else None)
            continue

        # --- numeric columns ---
        if col in NUMERIC_COLS:
            s = str(val).strip()
            out.append(float(s) if s != "" else None)
            continue

        # --- all other text columns ---
        out.append(str(val).strip() if val is not None else None)

    return tuple(out)


def escape_copy_value(v) -> str:
    """
    Render a Python value as a PostgreSQL COPY text-format field.
    NULLs become \\N; booleans become t/f; everything else is string-escaped
    so that backslash, tab, newline and carriage-return are safe.
    Crucially we do NOT wrap values in any extra quoting — COPY text format
    is tab-delimited with no quoting layer, so the string is written as-is
    after escape processing.
    """
    if v is None:
        return "\\N"
    if isinstance(v, bool):
        return "t" if v else "f"
    # Escape in the order: backslash first, then control chars
    s = str(v)
    s = s.replace("\\", "\\\\")   # must be first
    s = s.replace("\t", "\\t")
    s = s.replace("\n", "\\n")
    s = s.replace("\r", "\\r")
    return s


def build_copy_buffer(rows: list[dict]) -> io.StringIO:
    """
    Convert rows to a text buffer suitable for COPY FROM STDIN (FORMAT text).
    Each line is tab-separated fields; NULL represented as \\N.
    We build lines manually (no csv.writer) so that JSON curly-brace strings
    are never wrapped in additional quoting.
    """
    lines = []
    for raw in rows:
        t = coerce_row(raw)
        lines.append("\t".join(escape_copy_value(v) for v in t))

    buf = io.StringIO("\n".join(lines) + "\n")
    return buf


def main():
    # ------------------------------------------------------------------ #
    # 1. Read CSV                                                          #
    # ------------------------------------------------------------------ #
    print(f"Reading CSV: {CSV_PATH}")
    # dtype=str keeps leading zeros on zip and avoids auto-casting
    df = pd.read_csv(CSV_PATH, dtype=str, keep_default_na=False)
    print(f"  Rows read: {len(df):,}  |  Columns: {len(df.columns)}")

    rows = df.to_dict(orient="records")

    # ------------------------------------------------------------------ #
    # 2. Connect to Neon                                                   #
    # ------------------------------------------------------------------ #
    password = os.environ.get("NEON_PASSWORD")
    if not password:
        print("ERROR: NEON_PASSWORD not set. Run via: doppler run -- python ...")
        sys.exit(1)

    print("Connecting to Neon PostgreSQL...")
    conn = psycopg2.connect(
        host="ep-ancient-waterfall-a42vy0du-pooler.us-east-1.aws.neon.tech",
        port=5432,
        dbname="Marketing DB",
        user="Marketing DB_owner",
        password=password,
        sslmode="require",
        connect_timeout=30,
    )
    conn.autocommit = False
    cur = conn.cursor()
    print("  Connected.")

    # ------------------------------------------------------------------ #
    # 3. TRUNCATE + COPY in a single transaction                           #
    # ------------------------------------------------------------------ #
    try:
        print("Truncating reference.us_zip_codes...")
        cur.execute("TRUNCATE TABLE reference.us_zip_codes")

        print(f"Building COPY buffer for {len(rows):,} rows...")
        buf = build_copy_buffer(rows)

        col_list = ", ".join(DB_COLUMNS)
        copy_sql = f"COPY reference.us_zip_codes ({col_list}) FROM STDIN WITH (FORMAT text, NULL '\\N')"

        print("Executing COPY FROM STDIN...")
        cur.copy_expert(copy_sql, buf)

        conn.commit()
        print("  Transaction committed.")

    except Exception as exc:
        conn.rollback()
        print(f"ERROR during load — transaction rolled back.\n{exc}")
        cur.close()
        conn.close()
        sys.exit(1)

    # ------------------------------------------------------------------ #
    # 4. Verification queries                                              #
    # ------------------------------------------------------------------ #
    print("\n--- Verification ---")

    checks = [
        (
            "1. Total row count (expect 41,553)",
            "SELECT count(*) FROM reference.us_zip_codes",
        ),
        (
            "2. WV zip count",
            "SELECT count(*) FROM reference.us_zip_codes WHERE state_id = 'WV'",
        ),
        (
            "3. NYC zip 10001 spot-check",
            "SELECT zip, city, state_id, population, income_household_median "
            "FROM reference.us_zip_codes WHERE zip = '10001'",
        ),
        (
            "4. Puerto Rico zip 00601 (jsonb)",
            "SELECT zip, city, state_id, county_weights::text "
            "FROM reference.us_zip_codes WHERE zip = '00601'",
        ),
        (
            "5. Rows with county_weights NOT NULL",
            "SELECT count(*) FROM reference.us_zip_codes WHERE county_weights IS NOT NULL",
        ),
        (
            "6. ZIP range (min, max)",
            "SELECT min(zip), max(zip) FROM reference.us_zip_codes",
        ),
    ]

    for label, sql in checks:
        cur.execute(sql)
        result = cur.fetchall()
        print(f"\n{label}")
        print(f"  SQL : {sql}")
        print(f"  Result: {result}")

    cur.close()
    conn.close()
    print("\nDone.")


if __name__ == "__main__":
    main()
