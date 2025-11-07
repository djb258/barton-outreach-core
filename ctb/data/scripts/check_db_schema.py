"""
Database Schema Inspector
Check current Neon database schema and tables
"""
import os
import sys
from pathlib import Path
from dotenv import load_dotenv
import psycopg2
from psycopg2.extras import RealDictCursor

# Set UTF-8 encoding
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

# Load environment - find project root by looking for .git directory
project_root = Path(__file__).resolve()
while not (project_root / ".git").exists() and project_root != project_root.parent:
    project_root = project_root.parent
env_path = project_root / ".env"
load_dotenv(env_path)

DATABASE_URL = os.getenv('NEON_DATABASE_URL') or os.getenv('DATABASE_URL')

if not DATABASE_URL:
    print("[ERROR] No database URL found")
    sys.exit(1)

print("[OK] Connecting to Neon database...")

try:
    conn = psycopg2.connect(DATABASE_URL)
    cursor = conn.cursor(cursor_factory=RealDictCursor)

    # Check schemas
    print("\n=== SCHEMAS ===")
    cursor.execute("""
        SELECT schema_name
        FROM information_schema.schemata
        WHERE schema_name NOT IN ('pg_catalog', 'information_schema')
        ORDER BY schema_name
    """)
    schemas = cursor.fetchall()
    for schema in schemas:
        print(f"  - {schema['schema_name']}")

    # Check tables in marketing schema
    print("\n=== TABLES IN 'marketing' SCHEMA ===")
    cursor.execute("""
        SELECT table_name
        FROM information_schema.tables
        WHERE table_schema = 'marketing'
        AND table_type = 'BASE TABLE'
        ORDER BY table_name
    """)
    tables = cursor.fetchall()
    for table in tables:
        print(f"  - {table['table_name']}")

    # Check views in marketing schema
    print("\n=== VIEWS IN 'marketing' SCHEMA ===")
    cursor.execute("""
        SELECT table_name
        FROM information_schema.views
        WHERE table_schema = 'marketing'
        ORDER BY table_name
    """)
    views = cursor.fetchall()
    if views:
        for view in views:
            print(f"  - {view['table_name']}")
    else:
        print("  (No views found)")

    # Check columns in relevant tables
    for table_name in ['company_master', 'pipeline_errors', 'companies', 'errors']:
        print(f"\n=== COLUMNS IN 'marketing.{table_name}' ===")
        cursor.execute("""
            SELECT column_name, data_type, is_nullable
            FROM information_schema.columns
            WHERE table_schema = 'marketing'
            AND table_name = %s
            ORDER BY ordinal_position
        """, (table_name,))
        columns = cursor.fetchall()
        if columns:
            for col in columns:
                nullable = "NULL" if col['is_nullable'] == 'YES' else "NOT NULL"
                print(f"  - {col['column_name']:<30} {col['data_type']:<20} {nullable}")
        else:
            print(f"  (Table not found)")

    # Sample data from companies table
    print("\n=== SAMPLE DATA FROM COMPANIES (first 3 rows) ===")
    cursor.execute("SELECT * FROM marketing.companies LIMIT 3")
    samples = cursor.fetchall()
    if samples:
        for i, row in enumerate(samples, 1):
            print(f"\nRow {i}:")
            for key, value in row.items():
                print(f"  {key}: {value}")
    else:
        print("  (No data)")

    cursor.close()
    conn.close()

    print("\n[OK] Database inspection complete!")

except Exception as e:
    print(f"[ERROR] Database error: {e}")
    sys.exit(1)
