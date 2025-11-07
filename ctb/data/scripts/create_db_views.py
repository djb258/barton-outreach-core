"""
Create necessary database views for the Outreach Command Center
"""
import os
import sys
from pathlib import Path
from dotenv import load_dotenv
import psycopg2

if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

# Find project root by looking for .git directory
project_root = Path(__file__).resolve()
while not (project_root / ".git").exists() and project_root != project_root.parent:
    project_root = project_root.parent
env_path = project_root / "ctb" / "sys" / "security-audit" / ".env"
load_dotenv(env_path)

DATABASE_URL = os.getenv('NEON_DATABASE_URL') or os.getenv('DATABASE_URL')

print("[OK] Connecting to Neon database...")

conn = psycopg2.connect(DATABASE_URL)
cursor = conn.cursor()

# Create v_phase_stats view based on pipeline_events
print("\n[CREATING] v_phase_stats view...")
cursor.execute("""
    CREATE OR REPLACE VIEW marketing.v_phase_stats AS
    SELECT
        event_type as phase,
        COALESCE(status, 'unknown') as status,
        COUNT(*) as count,
        MAX(created_at) as last_updated
    FROM marketing.pipeline_events
    GROUP BY event_type, status
    ORDER BY event_type, status;
""")
print("[OK] v_phase_stats view created")

# Commit the changes
conn.commit()

# Test the view
print("\n[TESTING] v_phase_stats view...")
cursor.execute("SELECT * FROM marketing.v_phase_stats")
results = cursor.fetchall()
print(f"[OK] View returns {len(results)} rows")
for row in results:
    print(f"  Phase: {row[0]}, Status: {row[1]}, Count: {row[2]}, Last Updated: {row[3]}")

cursor.close()
conn.close()

print("\n[SUCCESS] Database views created successfully!")
