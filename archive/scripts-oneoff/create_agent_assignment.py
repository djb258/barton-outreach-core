import os, sys, psycopg2

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

cur = conn.cursor()

try:
    # Create agent_assignment table
    print("Creating coverage.agent_assignment table...")
    cur.execute("""
        CREATE TABLE coverage.agent_assignment (
            outreach_id UUID NOT NULL,
            agent_number TEXT NOT NULL,
            assigned_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            assigned_by TEXT NOT NULL DEFAULT 'owner',
            notes TEXT,
            CONSTRAINT pk_agent_assignment PRIMARY KEY (outreach_id),
            CONSTRAINT fk_aa_agent FOREIGN KEY (agent_number)
                REFERENCES coverage.service_agent (agent_number)
        );
    """)
    print("✓ Table created")

    # Create index
    print("\nCreating index on agent_number...")
    cur.execute("""
        CREATE INDEX idx_aa_agent ON coverage.agent_assignment (agent_number);
    """)
    print("✓ Index created")

    # Register in CTB
    print("\nRegistering in CTB registry...")
    cur.execute("""
        INSERT INTO ctb.table_registry (table_schema, table_name, leaf_type, notes)
        VALUES ('coverage', 'agent_assignment', 'CANONICAL', 'Agent-to-company assignment (one agent per outreach_id)')
        ON CONFLICT (table_schema, table_name) DO NOTHING;
    """)
    print("✓ CTB registration complete")

    # Commit all changes
    conn.commit()
    print("\n✓ All changes committed")

    # Verify schema
    print("\n" + "="*80)
    print("VERIFICATION: coverage.agent_assignment schema")
    print("="*80)
    cur.execute("""
        SELECT column_name, data_type, is_nullable, column_default
        FROM information_schema.columns
        WHERE table_schema = 'coverage' AND table_name = 'agent_assignment'
        ORDER BY ordinal_position;
    """)

    results = cur.fetchall()
    print(f"\n{'Column Name':<20} {'Data Type':<25} {'Nullable':<10} {'Default':<30}")
    print("-" * 85)
    for row in results:
        col_name, data_type, is_nullable, col_default = row
        print(f"{col_name:<20} {data_type:<25} {is_nullable:<10} {str(col_default or ''):<30}")

    print(f"\n✓ Total columns: {len(results)}")

    # Verify CTB registration
    print("\n" + "="*80)
    print("CTB Registry Entry")
    print("="*80)
    cur.execute("""
        SELECT table_schema, table_name, leaf_type, notes, is_frozen
        FROM ctb.table_registry
        WHERE table_schema = 'coverage' AND table_name = 'agent_assignment';
    """)
    ctb_row = cur.fetchone()
    if ctb_row:
        print(f"Schema: {ctb_row[0]}")
        print(f"Table: {ctb_row[1]}")
        print(f"Leaf Type: {ctb_row[2]}")
        print(f"Notes: {ctb_row[3]}")
        print(f"Frozen: {ctb_row[4]}")

except psycopg2.Error as e:
    print(f"\n✗ Error: {e}")
    conn.rollback()
    sys.exit(1)
finally:
    cur.close()
    conn.close()

print("\n" + "="*80)
print("Operation Summary")
print("="*80)
print("✓ coverage.agent_assignment table created")
print("✓ Primary key on outreach_id")
print("✓ Foreign key to coverage.service_agent(agent_number)")
print("✓ Index on agent_number for reverse lookups")
print("✓ Registered in CTB as CANONICAL leaf type")
