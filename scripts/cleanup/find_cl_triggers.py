"""
Find triggers on cl.company_identity table
"""

import os
import sys
import psycopg2

# Fix Windows console encoding
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

def get_neon_connection():
    """Establish Neon database connection"""
    return psycopg2.connect(
        host=os.environ['NEON_HOST'],
        port=os.environ.get('NEON_PORT', '5432'),
        database=os.environ['NEON_DATABASE'],
        user=os.environ['NEON_USER'],
        password=os.environ['NEON_PASSWORD'],
        sslmode='require'
    )

def find_triggers():
    """Find all triggers on cl.company_identity"""
    conn = get_neon_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT
            tgname as trigger_name,
            proname as function_name,
            tgenabled as enabled,
            CASE tgtype::int & 2
                WHEN 2 THEN 'BEFORE'
                ELSE 'AFTER'
            END as timing,
            CASE tgtype::int & 28
                WHEN 4 THEN 'INSERT'
                WHEN 8 THEN 'DELETE'
                WHEN 16 THEN 'UPDATE'
                ELSE 'OTHER'
            END as event
        FROM pg_trigger t
        JOIN pg_class c ON t.tgrelid = c.oid
        JOIN pg_namespace n ON c.relnamespace = n.oid
        LEFT JOIN pg_proc p ON t.tgfoid = p.oid
        WHERE n.nspname = 'cl'
          AND c.relname = 'company_identity'
        ORDER BY tgname
    """)

    triggers = cursor.fetchall()

    if not triggers:
        print("No triggers found on cl.company_identity")
    else:
        print(f"Found {len(triggers)} trigger(s) on cl.company_identity:\n")
        print(f"{'Trigger Name':<40} {'Function':<40} {'Timing':<10} {'Event':<10} {'Enabled':<10}")
        print("-" * 110)
        for row in triggers:
            trigger_name, function_name, enabled, timing, event = row
            enabled_str = "YES" if enabled == 'O' else "NO"
            print(f"{trigger_name:<40} {function_name:<40} {timing:<10} {event:<10} {enabled_str:<10}")

    cursor.close()
    conn.close()

if __name__ == "__main__":
    find_triggers()
