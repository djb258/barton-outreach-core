import os
import sys
import psycopg2
from psycopg2 import extras

# Fix Windows UTF-8 encoding
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")

# Connect to Neon
conn = psycopg2.connect(
    host=os.environ["NEON_HOST"],
    dbname=os.environ["NEON_DATABASE"],
    user=os.environ["NEON_USER"],
    password=os.environ["NEON_PASSWORD"],
    sslmode="require"
)
conn.autocommit = False
cur = conn.cursor(cursor_factory=extras.RealDictCursor)

try:
    print("=" * 80)
    print("STEP 1: Rename SA-001 to Dave Allan")
    print("=" * 80)

    cur.execute("""
        UPDATE coverage.service_agent
        SET agent_name = 'Dave Allan'
        WHERE agent_number = 'SA-001'
        RETURNING agent_number, agent_name, status;
    """)

    result = cur.fetchone()
    if result:
        print(f"✓ Agent renamed: {result['agent_number']} → {result['agent_name']} (status: {result['status']})")
    else:
        print("⚠ No agent found with agent_number = 'SA-001'")

    print()
    print("=" * 80)
    print("STEP 2: Bulk-assign companies in 26739/100mi market to SA-001")
    print("=" * 80)

    # First, check how many companies will be assigned
    cur.execute("""
        SELECT COUNT(*) as company_count
        FROM outreach.company_target ct
        WHERE LEFT(TRIM(ct.postal_code), 5) IN (
            SELECT zip FROM coverage.v_service_agent_coverage_zips
            WHERE coverage_id = '126b7fc9-4a2c-49bd-97ef-4c769312a576'
        )
        AND UPPER(TRIM(ct.state)) IN (
            SELECT DISTINCT state_id FROM coverage.v_service_agent_coverage_zips
            WHERE coverage_id = '126b7fc9-4a2c-49bd-97ef-4c769312a576'
        );
    """)

    count_result = cur.fetchone()
    eligible_count = count_result['company_count']
    print(f"Companies eligible for assignment: {eligible_count:,}")

    # Perform the bulk assignment
    cur.execute("""
        INSERT INTO coverage.agent_assignment (outreach_id, agent_number, assigned_by, notes)
        SELECT ct.outreach_id, 'SA-001', 'owner', 'Mount Storm WV 100mi initial assignment'
        FROM outreach.company_target ct
        WHERE LEFT(TRIM(ct.postal_code), 5) IN (
            SELECT zip FROM coverage.v_service_agent_coverage_zips
            WHERE coverage_id = '126b7fc9-4a2c-49bd-97ef-4c769312a576'
        )
        AND UPPER(TRIM(ct.state)) IN (
            SELECT DISTINCT state_id FROM coverage.v_service_agent_coverage_zips
            WHERE coverage_id = '126b7fc9-4a2c-49bd-97ef-4c769312a576'
        )
        ON CONFLICT (outreach_id) DO NOTHING;
    """)

    assigned_count = cur.rowcount
    print(f"✓ Companies assigned: {assigned_count:,}")

    if assigned_count < eligible_count:
        print(f"  (Note: {eligible_count - assigned_count:,} companies already had assignments and were skipped)")

    print()
    print("=" * 80)
    print("STEP 3: Verification")
    print("=" * 80)

    # Agent info
    print("\nAgent Information:")
    print("-" * 80)
    cur.execute("""
        SELECT agent_number, agent_name, status
        FROM coverage.service_agent
        ORDER BY agent_number;
    """)

    agents = cur.fetchall()
    for agent in agents:
        print(f"  {agent['agent_number']}: {agent['agent_name']} (status: {agent['status']})")

    # Assignment counts
    print("\nAssignment Summary:")
    print("-" * 80)
    cur.execute("""
        SELECT aa.agent_number, sa.agent_name, COUNT(*) as companies
        FROM coverage.agent_assignment aa
        JOIN coverage.service_agent sa ON sa.agent_number = aa.agent_number
        GROUP BY aa.agent_number, sa.agent_name
        ORDER BY aa.agent_number;
    """)

    assignments = cur.fetchall()
    for assignment in assignments:
        print(f"  {assignment['agent_number']} ({assignment['agent_name']}): {assignment['companies']:,} companies")

    # Commit the transaction
    conn.commit()
    print()
    print("=" * 80)
    print("✓ ALL CHANGES COMMITTED SUCCESSFULLY")
    print("=" * 80)

except Exception as e:
    conn.rollback()
    print(f"\n✗ ERROR: {e}")
    print("Transaction rolled back.")
    raise

finally:
    cur.close()
    conn.close()
