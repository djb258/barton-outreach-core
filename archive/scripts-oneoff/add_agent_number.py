import os
import sys
import psycopg2

# Set UTF-8 encoding for Windows
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
cur = conn.cursor()

try:
    # Step 1: Add agent_number column
    print("Adding agent_number column...")
    cur.execute("""
        ALTER TABLE coverage.service_agent
        ADD COLUMN agent_number TEXT;
    """)
    print("✓ Column added")

    # Step 2: Set existing agent to SA-001
    print("\nSetting agent_number for existing agent...")
    cur.execute("""
        UPDATE coverage.service_agent
        SET agent_number = 'SA-001'
        WHERE service_agent_id = '597121e4-249a-4105-be08-4f9221d0922f';
    """)
    print(f"✓ Updated {cur.rowcount} row(s)")

    # Step 3: Make column NOT NULL
    print("\nSetting NOT NULL constraint...")
    cur.execute("""
        ALTER TABLE coverage.service_agent
        ALTER COLUMN agent_number SET NOT NULL;
    """)
    print("✓ NOT NULL constraint added")

    # Step 4: Add UNIQUE constraint
    print("\nAdding UNIQUE constraint...")
    cur.execute("""
        ALTER TABLE coverage.service_agent
        ADD CONSTRAINT uq_service_agent_number UNIQUE (agent_number);
    """)
    print("✓ UNIQUE constraint added")

    # Commit all changes
    conn.commit()
    print("\n✓ All changes committed")

    # Step 5: Verify the changes
    print("\n" + "="*60)
    print("VERIFICATION - Final State:")
    print("="*60)
    cur.execute("""
        SELECT service_agent_id, agent_number, agent_name, status
        FROM coverage.service_agent;
    """)

    rows = cur.fetchall()
    print(f"\nTotal agents: {len(rows)}\n")
    print(f"{'Agent ID':<40} {'Number':<10} {'Name':<30} {'Status':<10}")
    print("-" * 100)
    for row in rows:
        print(f"{row[0]:<40} {row[1]:<10} {row[2]:<30} {row[3]:<10}")

except Exception as e:
    conn.rollback()
    print(f"\n✗ Error: {e}")
    sys.exit(1)
finally:
    cur.close()
    conn.close()
