import os
import sys
import psycopg2

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")

# Connect to Neon PostgreSQL
conn = psycopg2.connect(
    host=os.environ["NEON_HOST"],
    dbname=os.environ["NEON_DATABASE"],
    user=os.environ["NEON_USER"],
    password=os.environ["NEON_PASSWORD"],
    sslmode="require"
)

try:
    cursor = conn.cursor()

    # Execute UPDATE
    update_sql = """
    UPDATE coverage.service_agent
    SET agent_name = 'Jeff Mussolino'
    WHERE agent_number = 'SA-002';
    """
    cursor.execute(update_sql)
    rows_updated = cursor.rowcount
    print(f"UPDATE executed: {rows_updated} row(s) updated")

    # Commit the update
    conn.commit()

    # Verify with SELECT
    select_sql = """
    SELECT agent_number, agent_name
    FROM coverage.service_agent
    ORDER BY agent_number;
    """
    cursor.execute(select_sql)
    results = cursor.fetchall()

    print("\n=== Verification Results ===")
    print(f"{'Agent Number':<15} {'Agent Name':<30}")
    print("-" * 45)
    for row in results:
        print(f"{row[0]:<15} {row[1]:<30}")

    cursor.close()

except Exception as e:
    conn.rollback()
    print(f"ERROR: {e}")
    raise
finally:
    conn.close()
