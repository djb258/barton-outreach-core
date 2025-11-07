"""
Check pipeline_events table structure and sample data
"""
import os
import sys
from pathlib import Path
from dotenv import load_dotenv
import psycopg2
from psycopg2.extras import RealDictCursor

if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

# Find project root by looking for .git directory
project_root = Path(__file__).resolve()
while not (project_root / ".git").exists() and project_root != project_root.parent:
    project_root = project_root.parent
env_path = project_root / ".env"
load_dotenv(env_path)

DATABASE_URL = os.getenv('NEON_DATABASE_URL') or os.getenv('DATABASE_URL')

conn = psycopg2.connect(DATABASE_URL)
cursor = conn.cursor(cursor_factory=RealDictCursor)

# Check pipeline_events columns
print("=== COLUMNS IN 'marketing.pipeline_events' ===")
cursor.execute("""
    SELECT column_name, data_type, is_nullable
    FROM information_schema.columns
    WHERE table_schema = 'marketing'
    AND table_name = 'pipeline_events'
    ORDER BY ordinal_position
""")
columns = cursor.fetchall()
for col in columns:
    nullable = "NULL" if col['is_nullable'] == 'YES' else "NOT NULL"
    print(f"  {col['column_name']:<30} {col['data_type']:<20} {nullable}")

# Sample data
print("\n=== SAMPLE DATA FROM pipeline_events (first 5) ===")
cursor.execute("SELECT * FROM marketing.pipeline_events ORDER BY created_at DESC LIMIT 5")
samples = cursor.fetchall()
for i, row in enumerate(samples, 1):
    print(f"\nEvent {i}:")
    for key, value in row.items():
        print(f"  {key}: {value}")

# Check distinct event types
print("\n=== DISTINCT EVENT TYPES (phases) ===")
cursor.execute("SELECT DISTINCT event_type FROM marketing.pipeline_events ORDER BY event_type")
event_types = cursor.fetchall()
for et in event_types:
    print(f"  - {et['event_type']}")

# Check if we can get phase-like stats
print("\n=== EVENT TYPE COUNTS (potential phase stats) ===")
cursor.execute("""
    SELECT
        event_type,
        COUNT(*) as count,
        MAX(created_at) as last_updated
    FROM marketing.pipeline_events
    GROUP BY event_type
    ORDER BY event_type
""")
stats = cursor.fetchall()
for stat in stats:
    print(f"  {stat['event_type']:<40} Count: {stat['count']:<10} Last: {stat['last_updated']}")

cursor.close()
conn.close()
