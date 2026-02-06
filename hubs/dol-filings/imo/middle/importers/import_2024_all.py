#!/usr/bin/env python3
"""
DOL 2024 Comprehensive Import Script
======================================
Appends 2024 FOIA data into existing Neon PostgreSQL tables (dol schema).
All rows tagged with form_year = '2024'.

Covers:
  - Form 5500 (regular) → dol.form_5500
  - Form 5500-SF (short form) → dol.form_5500_sf
  - Schedule A → dol.schedule_a
  - Schedule A Part 1 (brokers) → dol.schedule_a_part1  [NEW TABLE]
  - Form 5500-SF Part 7 (transfers) → dol.form_5500_sf_part7  [NEW TABLE]
  - Schedules C/D/G/H/I (21 tables) → dol.schedule_*

Usage:
  doppler run -- python import_2024_all.py --create-new-tables
  doppler run -- python import_2024_all.py --load
  doppler run -- python import_2024_all.py --load --table form_5500
  doppler run -- python import_2024_all.py --verify
  doppler run -- python import_2024_all.py --create-new-tables --load --verify
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
# CONFIG
# ---------------------------------------------------------------------------
YEAR = "2024"
DATA_DIR = Path(__file__).resolve().parents[5] / "data" / "5500" / "2024"

# ---------------------------------------------------------------------------
# CSV → Table mapping
# key = dol table name
# value = (subfolder, csv_filename)
# ---------------------------------------------------------------------------
TABLE_CSV_MAP = {
    # Core forms
    "form_5500":            ("form_5500",    "f_5500_2024_latest.csv"),
    "form_5500_sf":         ("form_5500_sf", "f_5500_sf_2024_latest.csv"),

    # Schedule A
    "schedule_a":           ("schedule_a",   "F_SCH_A_2024_latest.csv"),

    # NEW 2024 tables
    "schedule_a_part1":     ("schedule_a",   "F_SCH_A_PART1_2024_latest.csv"),
    "form_5500_sf_part7":   ("form_5500_sf", "F_5500_SF_PART7_2024_latest.csv"),

    # Schedule C (9 tables)
    "schedule_c":                   ("schedule_c", "F_SCH_C_2024_latest.csv"),
    "schedule_c_part1_item1":       ("schedule_c", "F_SCH_C_PART1_ITEM1_2024_latest.csv"),
    "schedule_c_part1_item2":       ("schedule_c", "F_SCH_C_PART1_ITEM2_2024_latest.csv"),
    "schedule_c_part1_item2_codes": ("schedule_c", "F_SCH_C_PART1_ITEM2_CODES_2024_latest.csv"),
    "schedule_c_part1_item3":       ("schedule_c", "F_SCH_C_PART1_ITEM3_2024_latest.csv"),
    "schedule_c_part1_item3_codes": ("schedule_c", "F_SCH_C_PART1_ITEM3_CODES_2024_latest.csv"),
    "schedule_c_part2":             ("schedule_c", "F_SCH_C_PART2_2024_latest.csv"),
    "schedule_c_part2_codes":       ("schedule_c", "F_SCH_C_PART2_CODES_2024_latest.csv"),
    "schedule_c_part3":             ("schedule_c", "F_SCH_C_PART3_2024_latest.csv"),

    # Schedule D (4 tables)
    "schedule_d":           ("schedule_d", "F_SCH_D_2024_latest.csv"),
    "schedule_d_part1":     ("schedule_d", "F_SCH_D_PART1_2024_latest.csv"),
    "schedule_d_part2":     ("schedule_d", "F_SCH_D_PART2_2024_latest.csv"),
    "schedule_dcg":         ("schedule_d", "F_SCH_DCG_2024_latest.csv"),

    # Schedule G (4 tables)
    "schedule_g":           ("schedule_g", "F_SCH_G_2024_latest.csv"),
    "schedule_g_part1":     ("schedule_g", "F_SCH_G_PART1_2024_latest.csv"),
    "schedule_g_part2":     ("schedule_g", "F_SCH_G_PART2_2024_latest.csv"),
    "schedule_g_part3":     ("schedule_g", "F_SCH_G_PART3_2024_latest.csv"),

    # Schedule H (2 tables)
    "schedule_h":           ("schedule_h", "F_SCH_H_2024_latest.csv"),
    "schedule_h_part1":     ("schedule_h", "F_SCH_H_PART1_2024_latest.csv"),

    # Schedule I (2 tables)
    "schedule_i":           ("schedule_i", "F_SCH_I_2024_latest.csv"),
    "schedule_i_part1":     ("schedule_i", "F_SCH_I_PART1_2024_latest.csv"),
}

# ---------------------------------------------------------------------------
# DDL for NEW 2024 tables only
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
            form_year VARCHAR(10) DEFAULT '2024',
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
            form_year VARCHAR(10) DEFAULT '2024',
            created_at TIMESTAMPTZ NOT NULL DEFAULT now()
        );
        CREATE INDEX IF NOT EXISTS idx_sf_p7_ack ON dol.form_5500_sf_part7(ack_id);
    """,
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
    """Create tables that are new in 2024 (schedule_a_part1, form_5500_sf_part7)."""
    cur = conn.cursor()
    cur.execute("CREATE SCHEMA IF NOT EXISTS dol;")
    for table_name, ddl in NEW_TABLE_DDL.items():
        logger.info(f"  Creating dol.{table_name}...")
        cur.execute(ddl)
    conn.commit()
    cur.close()
    logger.info("New 2024 tables created.")


def load_csv_to_table(conn, table_name: str, csv_path: Path) -> int:
    """
    Bulk-load a 2024 CSV into dol.{table_name} using COPY.

    Strategy:
    1. Read CSV header columns (uppercase in file)
    2. Get existing table columns from DB
    3. Find intersection (CSV cols that exist in table), lowercased
    4. Stream CSV data with form_year='2024' appended via COPY

    For tables that already have 2023 data, this APPENDS 2024 rows.
    """
    cur = conn.cursor()

    # 1. Read CSV header
    with open(csv_path, "r", encoding="utf-8", errors="replace") as f:
        reader = csv.reader(f)
        csv_header_raw = [col.strip() for col in next(reader)]

    csv_header_lower = [col.lower() for col in csv_header_raw]

    # 2. Get table columns
    table_cols = get_table_columns(conn, table_name)

    # 3. Find usable columns: CSV cols that exist in the table
    #    Exclude auto-generated cols (id, created_at, updated_at, filing_id, company_unique_id)
    skip_cols = {"id", "created_at", "updated_at", "filing_id", "company_unique_id",
                 "schedule_id", "sponsor_state", "sponsor_name"}
    table_cols_set = set(table_cols) - skip_cols

    # Build ordered list of (csv_index, db_column_name) for columns in both CSV and table
    load_map = []
    for idx, csv_col in enumerate(csv_header_lower):
        if csv_col in table_cols_set:
            load_map.append((idx, csv_col))

    if not load_map:
        logger.error(f"  No matching columns between CSV and dol.{table_name}!")
        logger.error(f"  CSV cols: {csv_header_lower[:10]}...")
        logger.error(f"  Table cols: {sorted(table_cols_set)[:10]}...")
        return 0

    # Check if form_year is in CSV
    csv_has_form_year = "form_year" in csv_header_lower

    # Build column list for COPY (add form_year if not in CSV)
    db_columns = [col for _, col in load_map]
    if not csv_has_form_year and "form_year" in table_cols_set:
        db_columns.append("form_year")

    col_list_sql = ", ".join(db_columns)

    logger.info(f"  Loading {csv_path.name} → dol.{table_name}")
    logger.info(f"    CSV columns: {len(csv_header_lower)}, Table columns: {len(table_cols)}, "
                f"Matched: {len(load_map)}")

    # 4. Stream data through StringIO, selecting only matched columns + form_year
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

            # Append form_year if not in CSV
            if not csv_has_form_year and "form_year" in table_cols_set:
                out_row.append(YEAR)

            writer.writerow(out_row)
            row_count += 1

    buffer.seek(0)

    # 5. COPY into table
    copy_sql = f"COPY dol.{table_name} ({col_list_sql}) FROM STDIN WITH (FORMAT csv, NULL '', DELIMITER ',')"
    cur.copy_expert(copy_sql, buffer)
    conn.commit()

    # If CSV had form_year, update those rows to '2024' just in case
    if csv_has_form_year:
        # The CSV may not have form_year values, defaults will kick in
        pass

    # 6. Verify
    cur.execute(f"SELECT COUNT(*) FROM dol.{table_name} WHERE form_year = %s", (YEAR,))
    db_count = cur.fetchone()[0]
    cur.close()

    logger.info(f"    ✓ {row_count:,} CSV rows → {db_count:,} DB rows (form_year={YEAR})")
    return db_count


def verify_2024(conn):
    """Post-load verification for 2024 data."""
    cur = conn.cursor()

    logger.info("\n" + "=" * 70)
    logger.info("2024 VERIFICATION REPORT")
    logger.info("=" * 70)

    # 1. Row counts by year
    logger.info("\n--- Row Counts by Year ---")
    all_tables = list(TABLE_CSV_MAP.keys())
    total_2024 = 0

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
                if yr == "2024":
                    total_2024 += cnt
        except Exception as e:
            logger.warning(f"  dol.{table_name}: ERROR - {e}")
            conn.rollback()

    logger.info(f"\n  TOTAL 2024 ROWS: {total_2024:,}")

    # 2. ACK_ID join coverage (2024 only → form_5500 2024)
    logger.info("\n--- 2024 ACK_ID Join Coverage (→ dol.form_5500 WHERE form_year='2024') ---")
    schedule_tables = [t for t in all_tables if t.startswith("schedule_") or t == "schedule_dcg"]

    for table_name in schedule_tables:
        try:
            cur.execute(f"""
                SELECT
                    COUNT(DISTINCT s.ack_id) AS total,
                    COUNT(DISTINCT f.ack_id) AS matched,
                    ROUND(COUNT(DISTINCT f.ack_id)::numeric /
                          NULLIF(COUNT(DISTINCT s.ack_id), 0) * 100, 1) AS pct
                FROM dol.{table_name} s
                LEFT JOIN dol.form_5500 f ON f.ack_id = s.ack_id AND f.form_year = '2024'
                WHERE s.form_year = '2024'
            """)
            row = cur.fetchone()
            if row and row[0] > 0:
                logger.info(f"  dol.{table_name}: {row[1]:,}/{row[0]:,} ({row[2]}%)")
        except Exception as e:
            logger.warning(f"  dol.{table_name}: ERROR - {e}")
            conn.rollback()

    # 3. Quick sanity: no duplicate ACK_IDs in form_5500 across years
    logger.info("\n--- Duplicate ACK_ID Check ---")
    try:
        cur.execute("""
            SELECT COUNT(*) - COUNT(DISTINCT ack_id) AS dupes
            FROM dol.form_5500
        """)
        dupes = cur.fetchone()[0]
        logger.info(f"  form_5500 duplicate ACK_IDs: {dupes}")
    except Exception as e:
        logger.warning(f"  ERROR: {e}")
        conn.rollback()

    cur.close()
    logger.info("\n" + "=" * 70)


# ---------------------------------------------------------------------------
# MAIN
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description="Import ALL DOL 2024 data to Neon")
    parser.add_argument("--create-new-tables", action="store_true",
                        help="Create new 2024 tables (schedule_a_part1, form_5500_sf_part7)")
    parser.add_argument("--load", action="store_true", help="Load all 2024 CSVs")
    parser.add_argument("--verify", action="store_true", help="Run post-load verification")
    parser.add_argument("--table", type=str,
                        help="Load only a specific table (e.g. form_5500, schedule_c)")
    args = parser.parse_args()

    if not any([args.create_new_tables, args.load, args.verify]):
        parser.print_help()
        sys.exit(0)

    conn = get_connection()
    logger.info(f"Connected to Neon. Loading {YEAR} data from {DATA_DIR}")

    try:
        # Step 1: Create new tables
        if args.create_new_tables:
            logger.info("\n=== CREATING NEW 2024 TABLES ===")
            create_new_tables(conn)

        # Step 2: Load CSVs
        if args.load:
            logger.info("\n=== LOADING 2024 CSVs ===")
            manifest = {}
            start_all = time.time()

            tables_to_load = TABLE_CSV_MAP.items()
            if args.table:
                if args.table not in TABLE_CSV_MAP:
                    logger.error(f"Unknown table: {args.table}")
                    logger.error(f"Options: {list(TABLE_CSV_MAP.keys())}")
                    sys.exit(1)
                tables_to_load = [(args.table, TABLE_CSV_MAP[args.table])]

            for table_name, (subfolder, csv_file) in tables_to_load:
                csv_path = DATA_DIR / subfolder / csv_file
                if not csv_path.exists():
                    # Try case-insensitive match
                    found = None
                    parent = DATA_DIR / subfolder
                    if parent.exists():
                        for f in parent.iterdir():
                            if f.name.lower() == csv_file.lower():
                                found = f
                                break
                    if found:
                        csv_path = found
                    else:
                        logger.error(f"  ✗ MISSING: {csv_path}")
                        manifest[table_name] = {"status": "MISSING", "file": str(csv_path)}
                        continue

                start = time.time()
                try:
                    count = load_csv_to_table(conn, table_name, csv_path)
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
            logger.info("\n=== 2024 LOAD MANIFEST ===")
            for tbl, info in manifest.items():
                if info["status"] == "OK":
                    logger.info(
                        f"  ✓ dol.{tbl}: {info['rows']:,} rows "
                        f"({info['seconds']}s) — {info['file']}"
                    )
                else:
                    logger.info(
                        f"  ✗ dol.{tbl}: {info['status']} — "
                        f"{info.get('error', info.get('file', ''))}"
                    )

            logger.info(f"\n  TOTAL: {total_rows:,} rows in {total_elapsed}s")

        # Step 3: Verify
        if args.verify:
            verify_2024(conn)

    finally:
        conn.close()
        logger.info("\nDone. Connection closed.")


if __name__ == "__main__":
    main()
