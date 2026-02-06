#!/usr/bin/env python3
"""
DOL FOIA Multi-Year Import Script
===================================
Appends DOL Form 5500 FOIA data for ANY year into Neon PostgreSQL (dol schema).
All rows tagged with form_year = <year>.

Covers (per year):
  - Form 5500 (regular)            → dol.form_5500
  - Form 5500-SF (short form)      → dol.form_5500_sf
  - Form 5500-SF Part 7 (transfers)→ dol.form_5500_sf_part7
  - Schedule A                     → dol.schedule_a
  - Schedule A Part 1 (brokers)    → dol.schedule_a_part1
  - Schedules C/D/G/H/I (21 tbls) → dol.schedule_*

Usage:
  doppler run -- python import_dol_year.py --year 2024 --create-new-tables --load --verify
  doppler run -- python import_dol_year.py --year 2025 --load --verify
  doppler run -- python import_dol_year.py --year 2024 --load --table form_5500
  doppler run -- python import_dol_year.py --year 2024 --verify

Reusable for 2023, 2024, 2025, 2026 … just pass --year.
"""

import os
import sys
import csv
import time
import argparse
import logging
from pathlib import Path
from io import StringIO

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# PATH RESOLUTION
# ---------------------------------------------------------------------------
SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPT_DIR.parents[4]  # barton-outreach-core/
# parents: [0]=importers, [1]=middle, [2]=imo, [3]=dol-filings, [4]=hubs, [5]=barton-outreach-core
# But SCRIPT_DIR is already .parent (=importers), so SCRIPT_DIR.parents goes:
#   [0]=middle, [1]=imo, [2]=dol-filings, [3]=hubs, [4]=barton-outreach-core


def get_data_dir(year: str) -> Path:
    """Return path to extracted CSVs for the given year."""
    return PROJECT_ROOT / "data" / "5500" / year


# ---------------------------------------------------------------------------
# CSV → Table mapping template
# {table_name: (subfolder, filename_template)}
# The template uses {YEAR} which gets replaced at runtime.
# ---------------------------------------------------------------------------
TABLE_CSV_TEMPLATES = {
    # Core forms
    "form_5500":            ("form_5500",    "f_5500_{YEAR}_latest.csv"),
    "form_5500_sf":         ("form_5500_sf", "f_5500_sf_{YEAR}_latest.csv"),

    # Schedule A
    "schedule_a":           ("schedule_a",   "F_SCH_A_{YEAR}_latest.csv"),

    # Tables first seen in 2024 (will be created if --create-new-tables)
    "schedule_a_part1":     ("schedule_a",   "F_SCH_A_PART1_{YEAR}_latest.csv"),
    "form_5500_sf_part7":   ("form_5500_sf", "F_5500_SF_PART7_{YEAR}_latest.csv"),

    # Schedule C (9 tables)
    "schedule_c":                   ("schedule_c", "F_SCH_C_{YEAR}_latest.csv"),
    "schedule_c_part1_item1":       ("schedule_c", "F_SCH_C_PART1_ITEM1_{YEAR}_latest.csv"),
    "schedule_c_part1_item2":       ("schedule_c", "F_SCH_C_PART1_ITEM2_{YEAR}_latest.csv"),
    "schedule_c_part1_item2_codes": ("schedule_c", "F_SCH_C_PART1_ITEM2_CODES_{YEAR}_latest.csv"),
    "schedule_c_part1_item3":       ("schedule_c", "F_SCH_C_PART1_ITEM3_{YEAR}_latest.csv"),
    "schedule_c_part1_item3_codes": ("schedule_c", "F_SCH_C_PART1_ITEM3_CODES_{YEAR}_latest.csv"),
    "schedule_c_part2":             ("schedule_c", "F_SCH_C_PART2_{YEAR}_latest.csv"),
    "schedule_c_part2_codes":       ("schedule_c", "F_SCH_C_PART2_CODES_{YEAR}_latest.csv"),
    "schedule_c_part3":             ("schedule_c", "F_SCH_C_PART3_{YEAR}_latest.csv"),

    # Schedule D (4 tables)
    "schedule_d":           ("schedule_d", "F_SCH_D_{YEAR}_latest.csv"),
    "schedule_d_part1":     ("schedule_d", "F_SCH_D_PART1_{YEAR}_latest.csv"),
    "schedule_d_part2":     ("schedule_d", "F_SCH_D_PART2_{YEAR}_latest.csv"),
    "schedule_dcg":         ("schedule_d", "F_SCH_DCG_{YEAR}_latest.csv"),

    # Schedule G (4 tables)
    "schedule_g":           ("schedule_g", "F_SCH_G_{YEAR}_latest.csv"),
    "schedule_g_part1":     ("schedule_g", "F_SCH_G_PART1_{YEAR}_latest.csv"),
    "schedule_g_part2":     ("schedule_g", "F_SCH_G_PART2_{YEAR}_latest.csv"),
    "schedule_g_part3":     ("schedule_g", "F_SCH_G_PART3_{YEAR}_latest.csv"),

    # Schedule H (2 tables)
    "schedule_h":           ("schedule_h", "F_SCH_H_{YEAR}_latest.csv"),
    "schedule_h_part1":     ("schedule_h", "F_SCH_H_PART1_{YEAR}_latest.csv"),

    # Schedule I (2 tables)
    "schedule_i":           ("schedule_i", "F_SCH_I_{YEAR}_latest.csv"),
    "schedule_i_part1":     ("schedule_i", "F_SCH_I_PART1_{YEAR}_latest.csv"),
}

# ---------------------------------------------------------------------------
# DDL for tables first introduced post-2023
# Only run once — CREATE TABLE IF NOT EXISTS is safe to re-run.
# ---------------------------------------------------------------------------
NEW_TABLE_DDL = {
    "schedule_a_part1": """
        CREATE TABLE IF NOT EXISTS dol.schedule_a_part1 (
            id BIGSERIAL PRIMARY KEY,
            ack_id VARCHAR(50) NOT NULL,
            form_id VARCHAR(50),
            row_order INTEGER,
            ins_broker_name VARCHAR(500),
            ins_broker_us_address1 VARCHAR(500),
            ins_broker_us_address2 VARCHAR(500),
            ins_broker_us_city VARCHAR(255),
            ins_broker_us_state VARCHAR(10),
            ins_broker_us_zip VARCHAR(20),
            ins_broker_foreign_address1 VARCHAR(500),
            ins_broker_foreign_address2 VARCHAR(500),
            ins_broker_foreign_city VARCHAR(255),
            ins_broker_foreign_prov_state VARCHAR(100),
            ins_broker_foreign_cntry VARCHAR(100),
            ins_broker_foreign_postal_cd VARCHAR(50),
            ins_broker_comm_pd_amt NUMERIC,
            ins_broker_fees_pd_amt NUMERIC,
            ins_broker_fees_pd_text TEXT,
            ins_broker_code VARCHAR(50),
            form_year VARCHAR(10) NOT NULL,
            created_at TIMESTAMPTZ NOT NULL DEFAULT now()
        );
        CREATE INDEX IF NOT EXISTS idx_sch_a_p1_ack ON dol.schedule_a_part1(ack_id);
    """,
    "form_5500_sf_part7": """
        CREATE TABLE IF NOT EXISTS dol.form_5500_sf_part7 (
            id BIGSERIAL PRIMARY KEY,
            ack_id VARCHAR(50) NOT NULL,
            row_order INTEGER,
            sf_plan_transfer_name VARCHAR(500),
            sf_plan_transfer_ein VARCHAR(20),
            sf_plan_transfer_pn VARCHAR(10),
            form_year VARCHAR(10) NOT NULL,
            created_at TIMESTAMPTZ NOT NULL DEFAULT now()
        );
        CREATE INDEX IF NOT EXISTS idx_sf_p7_ack ON dol.form_5500_sf_part7(ack_id);
    """,
}


# ---------------------------------------------------------------------------
# Build the concrete CSV map for a given year
# ---------------------------------------------------------------------------

def build_csv_map(year: str) -> dict:
    """Replace {YEAR} in templates to produce the actual CSV filenames."""
    return {
        table: (subfolder, fname.replace("{YEAR}", year))
        for table, (subfolder, fname) in TABLE_CSV_TEMPLATES.items()
    }


# ---------------------------------------------------------------------------
# Column duplication map
# Some tables have BOTH raw DOL column names AND friendly aliases.
# When loading raw data, we must also populate the alias columns.
# Format: { table_name: { csv_col_lower: [alias_db_col, ...] } }
# ---------------------------------------------------------------------------
COLUMN_DUPLICATES = {
    "form_5500": {
        "spons_dfe_ein":  ["sponsor_dfe_ein"],
        "spons_dfe_pn":   ["plan_number"],
        "sponsor_dfe_name": ["sponsor_dfe_name"],  # already matches, but ensure
    },
    "form_5500_sf": {
        "sf_spons_ein":   ["sf_spons_ein"],  # already direct
        "sf_plan_num":    ["sf_plan_num"],
        "sf_sponsor_name":["sf_sponsor_name"],
    },
}


# ---------------------------------------------------------------------------
# DB helpers
# ---------------------------------------------------------------------------

def get_connection():
    """Get psycopg2 connection using project env var conventions."""
    import psycopg2
    conn_string = os.getenv("DATABASE_URL") or os.getenv("NEON_CONNECTION_STRING")
    if not conn_string:
        host = os.getenv("NEON_HOST")
        database = os.getenv("NEON_DATABASE")
        user = os.getenv("NEON_USER")
        password = os.getenv("NEON_PASSWORD")
        if not all([host, database, user, password]):
            logger.error("No database connection info. Set DATABASE_URL or NEON_* env vars.")
            sys.exit(1)
        conn_string = f"postgresql://{user}:{password}@{host}:5432/{database}?sslmode=require"
    return psycopg2.connect(conn_string)


def get_table_columns(conn, table_name: str) -> list[str]:
    """Return ordered list of column names for dol.{table_name}."""
    cur = conn.cursor()
    cur.execute("""
        SELECT column_name
        FROM information_schema.columns
        WHERE table_schema = 'dol' AND table_name = %s
        ORDER BY ordinal_position
    """, (table_name,))
    cols = [r[0] for r in cur.fetchall()]
    cur.close()
    return cols


def create_new_tables(conn):
    """Create tables that don't exist yet (schedule_a_part1, form_5500_sf_part7)."""
    cur = conn.cursor()
    cur.execute("CREATE SCHEMA IF NOT EXISTS dol;")
    for table_name, ddl in NEW_TABLE_DDL.items():
        logger.info(f"  Creating dol.{table_name} (IF NOT EXISTS)...")
        cur.execute(ddl)
    conn.commit()
    cur.close()
    logger.info("New tables ensured.")


def clear_year(conn, table_name: str, year: str):
    """Delete any existing rows for this year (idempotent reload)."""
    cur = conn.cursor()
    cur.execute(f"DELETE FROM dol.{table_name} WHERE form_year = %s", (year,))
    deleted = cur.rowcount
    conn.commit()
    cur.close()
    if deleted > 0:
        logger.info(f"    Cleared {deleted:,} existing {year} rows from dol.{table_name}")


def load_csv_to_table(conn, table_name: str, csv_path: Path, year: str) -> int:
    """
    Bulk-load a CSV into dol.{table_name} using COPY.

    Strategy:
    1. Read CSV header columns (uppercase in file)
    2. Get existing table columns from DB
    3. Find intersection (CSV cols that exist in table), lowercased
    4. Stream CSV data with form_year=<year> appended via COPY

    For tables with existing data from other years, this APPENDS.
    For same-year re-runs, clear_year() is called first (idempotent).
    """
    cur = conn.cursor()

    # 1. Read CSV header
    with open(csv_path, "r", encoding="utf-8", errors="replace") as f:
        reader = csv.reader(f)
        csv_header_raw = [col.strip() for col in next(reader)]

    csv_header_lower = [col.lower() for col in csv_header_raw]

    # 2. Get table columns
    table_cols = get_table_columns(conn, table_name)
    if not table_cols:
        logger.error(f"  Table dol.{table_name} does not exist! Run --create-new-tables first.")
        return 0

    # 3. Find usable columns: CSV cols that exist in the table
    #    Exclude auto-generated cols
    skip_cols = {"id", "created_at", "updated_at", "filing_id", "company_unique_id",
                 "schedule_id", "sponsor_state", "sponsor_name"}
    table_cols_set = set(table_cols) - skip_cols

    # Build ordered list of (csv_index, db_column_name)
    load_map = []
    for idx, csv_col in enumerate(csv_header_lower):
        if csv_col in table_cols_set:
            load_map.append((idx, csv_col))

    if not load_map:
        logger.error(f"  No matching columns between CSV and dol.{table_name}!")
        logger.error(f"  CSV cols (first 10): {csv_header_lower[:10]}")
        logger.error(f"  Table cols (first 10): {sorted(table_cols_set)[:10]}")
        return 0

    # Check for column duplicates (raw DOL col → friendly alias col)
    dupes = COLUMN_DUPLICATES.get(table_name, {})
    extra_dupe_cols = []  # list of (source_csv_idx, alias_db_col)
    for idx, csv_col in load_map:
        if csv_col in dupes:
            for alias in dupes[csv_col]:
                if alias != csv_col and alias in table_cols_set:
                    # Don't add if we already have this alias in load_map
                    existing_db_cols = {col for _, col in load_map}
                    if alias not in existing_db_cols:
                        extra_dupe_cols.append((idx, alias))

    # Check if form_year is in CSV already
    csv_has_form_year = "form_year" in csv_header_lower

    # Build column list for COPY (add form_year if not in CSV, add dupe aliases)
    db_columns = [col for _, col in load_map]
    for _, alias_col in extra_dupe_cols:
        db_columns.append(alias_col)
    if not csv_has_form_year and "form_year" in table_cols_set:
        db_columns.append("form_year")

    col_list_sql = ", ".join(db_columns)

    logger.info(f"  Loading {csv_path.name} → dol.{table_name}")
    logger.info(f"    CSV cols: {len(csv_header_lower)}, DB cols: {len(table_cols)}, "
                f"Matched: {len(load_map)}")

    # 4. Stream data through StringIO
    buffer = StringIO()
    writer = csv.writer(buffer)
    row_count = 0

    with open(csv_path, "r", encoding="utf-8", errors="replace") as f:
        reader = csv.reader(f)
        next(reader)  # skip header

        for row in reader:
            # Pad short rows
            while len(row) < len(csv_header_raw):
                row.append("")

            # Extract only matched columns
            out_row = [row[idx] for idx, _ in load_map]

            # Append duplicated alias columns
            for src_idx, _ in extra_dupe_cols:
                out_row.append(row[src_idx])

            # Append form_year if not in CSV
            if not csv_has_form_year and "form_year" in table_cols_set:
                out_row.append(year)

            writer.writerow(out_row)
            row_count += 1

    buffer.seek(0)

    # 5. COPY into table
    copy_sql = (
        f"COPY dol.{table_name} ({col_list_sql}) "
        f"FROM STDIN WITH (FORMAT csv, NULL '', DELIMITER ',')"
    )
    cur.copy_expert(copy_sql, buffer)
    conn.commit()

    # 6. Verify count for this year
    cur.execute(f"SELECT COUNT(*) FROM dol.{table_name} WHERE form_year = %s", (year,))
    db_count = cur.fetchone()[0]
    cur.close()

    logger.info(f"    ✓ {row_count:,} CSV rows → {db_count:,} DB rows (form_year={year})")
    return db_count


def verify_year(conn, year: str, csv_map: dict):
    """Post-load verification for the given year."""
    cur = conn.cursor()

    logger.info("\n" + "=" * 70)
    logger.info(f"{year} VERIFICATION REPORT")
    logger.info("=" * 70)

    # 1. Row counts by year for loaded tables
    logger.info(f"\n--- Row Counts (showing all years for loaded tables) ---")
    all_tables = list(csv_map.keys())
    total_year = 0

    for table_name in all_tables:
        try:
            cur.execute(f"""
                SELECT form_year, COUNT(*)
                FROM dol.{table_name}
                GROUP BY form_year
                ORDER BY form_year
            """)
            rows = cur.fetchall()
            year_str = ", ".join([f"{yr}={cnt:,}" for yr, cnt in rows])
            logger.info(f"  dol.{table_name}: {year_str}")
            for yr, cnt in rows:
                if yr == year:
                    total_year += cnt
        except Exception as e:
            logger.warning(f"  dol.{table_name}: ERROR - {e}")
            conn.rollback()

    logger.info(f"\n  TOTAL {year} ROWS: {total_year:,}")

    # 2. ACK_ID join coverage for this year
    logger.info(f"\n--- {year} ACK_ID Join Coverage (→ dol.form_5500) ---")
    schedule_tables = [
        t for t in all_tables
        if t.startswith("schedule_") or t == "schedule_dcg"
    ]

    for table_name in schedule_tables:
        try:
            cur.execute(f"""
                SELECT
                    COUNT(DISTINCT s.ack_id) AS total,
                    COUNT(DISTINCT f.ack_id) AS matched,
                    ROUND(
                        COUNT(DISTINCT f.ack_id)::numeric /
                        NULLIF(COUNT(DISTINCT s.ack_id), 0) * 100, 1
                    ) AS pct
                FROM dol.{table_name} s
                LEFT JOIN dol.form_5500 f
                    ON f.ack_id = s.ack_id AND f.form_year = %s
                WHERE s.form_year = %s
            """, (year, year))
            row = cur.fetchone()
            if row and row[0] and row[0] > 0:
                logger.info(f"  dol.{table_name}: {row[1]:,}/{row[0]:,} ({row[2]}%)")
        except Exception as e:
            logger.warning(f"  dol.{table_name}: ERROR - {e}")
            conn.rollback()

    # 3. Grand total across all years
    logger.info(f"\n--- Grand Total (all years) ---")
    grand = 0
    for table_name in all_tables:
        try:
            cur.execute(f"SELECT COUNT(*) FROM dol.{table_name}")
            cnt = cur.fetchone()[0]
            grand += cnt
        except:
            conn.rollback()
    logger.info(f"  All tables combined: {grand:,} rows")

    cur.close()
    logger.info("\n" + "=" * 70)


# ---------------------------------------------------------------------------
# MAIN
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description="Import DOL 5500 FOIA data for any year into Neon (dol schema)"
    )
    parser.add_argument(
        "--year", type=str, required=True,
        help="Filing year to import (e.g. 2024, 2025)"
    )
    parser.add_argument(
        "--create-new-tables", action="store_true",
        help="Create tables that don't exist yet (schedule_a_part1, form_5500_sf_part7)"
    )
    parser.add_argument("--load", action="store_true", help="Load CSVs for the specified year")
    parser.add_argument("--verify", action="store_true", help="Run post-load verification")
    parser.add_argument(
        "--table", type=str,
        help="Load only a specific table (e.g. form_5500, schedule_c)"
    )
    args = parser.parse_args()

    year = args.year

    if not any([args.create_new_tables, args.load, args.verify]):
        parser.print_help()
        sys.exit(0)

    csv_map = build_csv_map(year)
    data_dir = get_data_dir(year)

    logger.info(f"Year: {year}")
    logger.info(f"Data dir: {data_dir}")
    logger.info(f"Tables: {len(csv_map)}")

    if not data_dir.exists():
        logger.error(f"Data directory not found: {data_dir}")
        logger.error(f"Extract ZIPs first into data/5500/{year}/<schedule>/")
        sys.exit(1)

    conn = get_connection()
    # Disable read-only triggers for import
    cur = conn.cursor()
    cur.execute("SET session \"dol.import_mode\" = 'active';")
    conn.commit()
    cur.close()
    logger.info("Connected to Neon. Import mode: active")

    try:
        # Step 1: Create new tables (idempotent)
        if args.create_new_tables:
            logger.info("\n=== CREATING NEW TABLES (IF NOT EXISTS) ===")
            create_new_tables(conn)

        # Step 2: Load CSVs
        if args.load:
            logger.info(f"\n=== LOADING {year} CSVs ===")
            manifest = {}
            start_all = time.time()

            tables_to_load = list(csv_map.items())
            if args.table:
                if args.table not in csv_map:
                    logger.error(f"Unknown table: {args.table}")
                    logger.error(f"Options: {sorted(csv_map.keys())}")
                    sys.exit(1)
                tables_to_load = [(args.table, csv_map[args.table])]

            for table_name, (subfolder, csv_file) in tables_to_load:
                csv_path = data_dir / subfolder / csv_file

                # Case-insensitive file search
                if not csv_path.exists():
                    found = None
                    parent = data_dir / subfolder
                    if parent.exists():
                        for f in parent.iterdir():
                            if f.name.lower() == csv_file.lower():
                                found = f
                                break
                    if found:
                        csv_path = found
                    else:
                        logger.warning(f"  ⊘ SKIPPED (no CSV): dol.{table_name} — {csv_file}")
                        manifest[table_name] = {"status": "SKIPPED", "file": csv_file}
                        continue

                start = time.time()
                try:
                    # Clear existing data for this year (idempotent re-run)
                    clear_year(conn, table_name, year)
                    count = load_csv_to_table(conn, table_name, csv_path, year)
                    elapsed = round(time.time() - start, 1)
                    manifest[table_name] = {
                        "status": "OK",
                        "file": csv_file,
                        "rows": count,
                        "seconds": elapsed,
                    }
                except Exception as e:
                    logger.error(f"  ✗ FAILED: dol.{table_name}: {e}")
                    conn.rollback()
                    manifest[table_name] = {
                        "status": "FAILED",
                        "file": csv_file,
                        "error": str(e),
                    }

            total_elapsed = round(time.time() - start_all, 1)
            total_rows = sum(
                m.get("rows", 0) for m in manifest.values() if m["status"] == "OK"
            )

            # Print manifest
            logger.info(f"\n=== {year} LOAD MANIFEST ===")
            for tbl, info in manifest.items():
                if info["status"] == "OK":
                    logger.info(
                        f"  ✓ dol.{tbl}: {info['rows']:,} rows "
                        f"({info['seconds']}s) — {info['file']}"
                    )
                elif info["status"] == "SKIPPED":
                    logger.info(f"  ⊘ dol.{tbl}: SKIPPED — {info['file']}")
                else:
                    logger.info(
                        f"  ✗ dol.{tbl}: {info['status']} — "
                        f"{info.get('error', info.get('file', ''))}"
                    )

            logger.info(f"\n  TOTAL: {total_rows:,} rows in {total_elapsed}s")

        # Step 3: Verify
        if args.verify:
            verify_year(conn, year, csv_map)

    finally:
        conn.close()
        logger.info("\nDone. Connection closed.")


if __name__ == "__main__":
    main()
