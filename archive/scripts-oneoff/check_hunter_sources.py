"""
Hunter Source Attribution Check
Query Neon database to check if Hunter's source URLs are being captured
"""

import os
import sys
import psycopg2
import psycopg2.extras
from dotenv import load_dotenv

# Load environment
load_dotenv()

def get_db_connection():
    """Get PostgreSQL database connection to Neon"""
    connection_string = os.getenv("DATABASE_URL") or os.getenv("NEON_DATABASE_URL")
    if not connection_string:
        raise ValueError("DATABASE_URL or NEON_DATABASE_URL environment variable not set")
    return psycopg2.connect(connection_string)

def check_hunter_tables():
    """Check Hunter tables for source attribution fields"""
    conn = get_db_connection()
    cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

    print("=" * 80)
    print("HUNTER SOURCE ATTRIBUTION CHECK")
    print("=" * 80)

    try:
        # 1. Get all columns from hunter_contact
        print("\n[1] HUNTER_CONTACT TABLE SCHEMA:")
        print("-" * 80)
        cursor.execute("""
            SELECT
                column_name,
                data_type,
                character_maximum_length,
                is_nullable
            FROM information_schema.columns
            WHERE table_schema = 'enrichment'
              AND table_name = 'hunter_contact'
            ORDER BY ordinal_position;
        """)
        columns = cursor.fetchall()

        if columns:
            print(f"\nFound {len(columns)} columns in enrichment.hunter_contact:")
            for col in columns:
                length = f"({col['character_maximum_length']})" if col['character_maximum_length'] else ""
                nullable = "NULL" if col['is_nullable'] == 'YES' else "NOT NULL"
                print(f"  - {col['column_name']:<30} {col['data_type']:<20}{length:<10} {nullable}")
        else:
            print("\nNo columns found - table may not exist")

        # 2. Get sample row from hunter_contact
        print("\n[2] HUNTER_CONTACT SAMPLE ROW:")
        print("-" * 80)
        cursor.execute("SELECT * FROM enrichment.hunter_contact LIMIT 1;")
        sample = cursor.fetchone()

        if sample:
            print("\nSample record structure:")
            for key, value in sample.items():
                # Truncate long values
                value_str = str(value)[:100] if value else "NULL"
                print(f"  - {key:<30} = {value_str}")
        else:
            print("\nNo records found in hunter_contact")

        # 3. Get all columns from hunter_company
        print("\n[3] HUNTER_COMPANY TABLE SCHEMA:")
        print("-" * 80)
        cursor.execute("""
            SELECT
                column_name,
                data_type,
                character_maximum_length,
                is_nullable
            FROM information_schema.columns
            WHERE table_schema = 'enrichment'
              AND table_name = 'hunter_company'
            ORDER BY ordinal_position;
        """)
        columns = cursor.fetchall()

        if columns:
            print(f"\nFound {len(columns)} columns in enrichment.hunter_company:")
            for col in columns:
                length = f"({col['character_maximum_length']})" if col['character_maximum_length'] else ""
                nullable = "NULL" if col['is_nullable'] == 'YES' else "NOT NULL"
                print(f"  - {col['column_name']:<30} {col['data_type']:<20}{length:<10} {nullable}")
        else:
            print("\nNo columns found - table may not exist")

        # 4. Get sample row from hunter_company
        print("\n[4] HUNTER_COMPANY SAMPLE ROW:")
        print("-" * 80)
        cursor.execute("SELECT * FROM enrichment.hunter_company LIMIT 1;")
        sample = cursor.fetchone()

        if sample:
            print("\nSample record structure:")
            for key, value in sample.items():
                value_str = str(value)[:100] if value else "NULL"
                print(f"  - {key:<30} = {value_str}")
        else:
            print("\nNo records found in hunter_company")

        # 5. Check for source-related fields
        print("\n[5] SOURCE ATTRIBUTION ANALYSIS:")
        print("-" * 80)

        source_fields = []
        for table in ['hunter_contact', 'hunter_company']:
            cursor.execute("""
                SELECT column_name
                FROM information_schema.columns
                WHERE table_schema = 'enrichment'
                  AND table_name = %s
                  AND (column_name ILIKE '%%source%%'
                    OR column_name ILIKE '%%url%%'
                    OR column_name ILIKE '%%website%%'
                    OR column_name ILIKE '%%linkedin%%')
                ORDER BY column_name;
            """, (table,))

            fields = cursor.fetchall()
            if fields:
                print(f"\n{table.upper()} - Potential source fields:")
                for field in fields:
                    source_fields.append((table, field['column_name']))
                    print(f"  - {field['column_name']}")

        if not source_fields:
            print("\n⚠ No obvious source attribution fields found")
            print("Hunter's 'sources' field (array of URLs) may not be captured")

        # 6. Check hunter_contact for JSONB fields that might contain sources
        print("\n[6] JSONB FIELDS CHECK:")
        print("-" * 80)
        cursor.execute("""
            SELECT column_name
            FROM information_schema.columns
            WHERE table_schema = 'enrichment'
              AND table_name = 'hunter_contact'
              AND data_type IN ('jsonb', 'json')
            ORDER BY column_name;
        """)

        jsonb_fields = cursor.fetchall()
        if jsonb_fields:
            print("\nJSONB fields in hunter_contact (may contain sources):")
            for field in jsonb_fields:
                print(f"  - {field['column_name']}")

                # Sample the JSONB content
                cursor.execute(f"""
                    SELECT {field['column_name']}
                    FROM enrichment.hunter_contact
                    WHERE {field['column_name']} IS NOT NULL
                    LIMIT 1;
                """)
                sample_json = cursor.fetchone()
                if sample_json:
                    print(f"    Sample: {str(sample_json[field['column_name']])[:200]}...")
        else:
            print("\nNo JSONB fields found in hunter_contact")

        print("\n" + "=" * 80)
        print("CHECK COMPLETE")
        print("=" * 80)

    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        cursor.close()
        conn.close()

if __name__ == "__main__":
    check_hunter_tables()
