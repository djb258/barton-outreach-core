#!/usr/bin/env python3
"""
Database schema inspection script - READ ONLY
Checks for fractional CFO, appointments, and related tables
"""

import os
import sys
import psycopg2
from psycopg2.extras import RealDictCursor

# Fix Windows UTF-8 encoding
sys.stdout.reconfigure(encoding='utf-8')

def connect_to_neon():
    """Connect to Neon PostgreSQL with read-only mode"""
    conn = psycopg2.connect(
        host=os.environ['NEON_HOST'],
        port=5432,
        database=os.environ['NEON_DATABASE'],
        user=os.environ['NEON_USER'],
        password=os.environ['NEON_PASSWORD'],
        sslmode='require'
    )
    # Set read-only mode
    conn.set_session(readonly=True)
    return conn

def run_query(conn, query, description):
    """Execute a query and return results, handling errors gracefully"""
    print(f"\n{'='*80}")
    print(f"{description}")
    print(f"{'='*80}")
    try:
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        cursor.execute(query)
        results = cursor.fetchall()
        cursor.close()
        return results
    except psycopg2.Error as e:
        conn.rollback()  # Rollback failed transaction
        print(f"❌ Error: {e.pgerror if hasattr(e, 'pgerror') else str(e)}")
        return None

def main():
    conn = None
    try:
        print("Connecting to Neon PostgreSQL (READ-ONLY mode)...")
        conn = connect_to_neon()

        # 1. Check partners.fractional_cfo_master
        results = run_query(
            conn,
            "SELECT COUNT(*) as count FROM partners.fractional_cfo_master",
            "1. partners.fractional_cfo_master - Record Count"
        )
        if results:
            print(f"✓ Table exists with {results[0]['count']} records")

            # Get sample rows if table exists
            sample = run_query(
                conn,
                "SELECT * FROM partners.fractional_cfo_master LIMIT 5",
                "   Sample rows from partners.fractional_cfo_master"
            )
            if sample:
                for i, row in enumerate(sample, 1):
                    print(f"\n   Row {i}:")
                    for key, value in row.items():
                        print(f"     {key}: {value}")

        # 2. Check partners.partner_appointments
        results = run_query(
            conn,
            "SELECT COUNT(*) as count FROM partners.partner_appointments",
            "2. partners.partner_appointments - Record Count"
        )
        if results:
            print(f"✓ Table exists with {results[0]['count']} records")

            sample = run_query(
                conn,
                "SELECT * FROM partners.partner_appointments LIMIT 5",
                "   Sample rows from partners.partner_appointments"
            )
            if sample:
                for i, row in enumerate(sample, 1):
                    print(f"\n   Row {i}:")
                    for key, value in row.items():
                        print(f"     {key}: {value}")

        # 3. Check sales.appointment_history
        results = run_query(
            conn,
            "SELECT COUNT(*) as count FROM sales.appointment_history",
            "3. sales.appointment_history - Record Count"
        )
        if results:
            print(f"✓ Table exists with {results[0]['count']} records")

            sample = run_query(
                conn,
                "SELECT * FROM sales.appointment_history LIMIT 5",
                "   Sample rows from sales.appointment_history"
            )
            if sample:
                for i, row in enumerate(sample, 1):
                    print(f"\n   Row {i}:")
                    for key, value in row.items():
                        print(f"     {key}: {value}")

        # 4. Check bit.reactivation_intent
        results = run_query(
            conn,
            "SELECT COUNT(*) as count FROM bit.reactivation_intent",
            "4. bit.reactivation_intent - Record Count"
        )
        if results:
            print(f"✓ Table exists with {results[0]['count']} records")

            sample = run_query(
                conn,
                "SELECT * FROM bit.reactivation_intent LIMIT 5",
                "   Sample rows from bit.reactivation_intent"
            )
            if sample:
                for i, row in enumerate(sample, 1):
                    print(f"\n   Row {i}:")
                    for key, value in row.items():
                        print(f"     {key}: {value}")

        # 5. Check bit.partner_intent
        results = run_query(
            conn,
            "SELECT COUNT(*) as count FROM bit.partner_intent",
            "5. bit.partner_intent - Record Count"
        )
        if results:
            print(f"✓ Table exists with {results[0]['count']} records")

            sample = run_query(
                conn,
                "SELECT * FROM bit.partner_intent LIMIT 5",
                "   Sample rows from bit.partner_intent"
            )
            if sample:
                for i, row in enumerate(sample, 1):
                    print(f"\n   Row {i}:")
                    for key, value in row.items():
                        print(f"     {key}: {value}")

        # 6. Check outreach.appointments
        results = run_query(
            conn,
            "SELECT COUNT(*) as count FROM outreach.appointments",
            "6. outreach.appointments - Record Count"
        )
        if results:
            print(f"✓ Table exists with {results[0]['count']} records")

            sample = run_query(
                conn,
                "SELECT * FROM outreach.appointments LIMIT 5",
                "   Sample rows from outreach.appointments"
            )
            if sample:
                for i, row in enumerate(sample, 1):
                    print(f"\n   Row {i}:")
                    for key, value in row.items():
                        print(f"     {key}: {value}")

        # 7. Get people.people_master schema
        results = run_query(
            conn,
            """SELECT column_name, data_type, is_nullable, column_default
               FROM information_schema.columns
               WHERE table_schema = 'people' AND table_name = 'people_master'
               ORDER BY ordinal_position""",
            "7. people.people_master - Full Schema"
        )
        if results:
            print(f"\n{'Column Name':<40} {'Type':<30} {'Nullable':<10} {'Default'}")
            print("-" * 120)
            for row in results:
                col_name = row['column_name']
                data_type = row['data_type']
                nullable = row['is_nullable']
                default = row['column_default'] or ''
                print(f"{col_name:<40} {data_type:<30} {nullable:<10} {default}")

        # 8. Get people.company_slot schema
        results = run_query(
            conn,
            """SELECT column_name, data_type, is_nullable, column_default
               FROM information_schema.columns
               WHERE table_schema = 'people' AND table_name = 'company_slot'
               ORDER BY ordinal_position""",
            "8. people.company_slot - Full Schema"
        )
        if results:
            print(f"\n{'Column Name':<40} {'Type':<30} {'Nullable':<10} {'Default'}")
            print("-" * 120)
            for row in results:
                col_name = row['column_name']
                data_type = row['data_type']
                nullable = row['is_nullable']
                default = row['column_default'] or ''
                print(f"{col_name:<40} {data_type:<30} {nullable:<10} {default}")

        # 9. Check if cl.company_identity has company_name column
        results = run_query(
            conn,
            """SELECT column_name, data_type
               FROM information_schema.columns
               WHERE table_schema = 'cl'
               AND table_name = 'company_identity'
               AND column_name = 'company_name'""",
            "9. cl.company_identity - Check for company_name column"
        )
        if results:
            print(f"✓ company_name column exists in cl.company_identity")
            for row in results:
                print(f"   Type: {row['data_type']}")
        else:
            print(f"❌ company_name column NOT found in cl.company_identity")

        print("\n" + "="*80)
        print("Schema inspection complete!")
        print("="*80)

    except Exception as e:
        print(f"\n❌ Fatal error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        if conn:
            conn.close()
            print("\nConnection closed.")

if __name__ == "__main__":
    main()
