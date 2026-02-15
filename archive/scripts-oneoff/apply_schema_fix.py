#!/usr/bin/env python3
"""Apply the URL discovery schema fix."""
import os
from pathlib import Path
import psycopg2

def main():
    conn = psycopg2.connect(
        host=os.environ['NEON_HOST'],
        database=os.environ['NEON_DATABASE'],
        user=os.environ['NEON_USER'],
        password=os.environ['NEON_PASSWORD'],
        sslmode='require'
    )

    sql_path = Path(__file__).parent / "fix_url_discovery_schema.sql"
    sql = sql_path.read_text()

    print("Applying schema fix...")
    cur = conn.cursor()
    cur.execute(sql)
    conn.commit()
    print("Schema fix applied successfully")

    # Test the governance job
    print("\nTesting governance job...")
    cur.execute("SELECT * FROM shq.fn_run_error_governance_jobs()")
    for row in cur.fetchall():
        print(f"  {row[0]}: {row[1]}")
    conn.commit()

    print("\n=== FIX COMPLETE ===")
    conn.close()

if __name__ == "__main__":
    main()
