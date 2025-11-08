#!/usr/bin/env python3
"""
Inspect current Neon database schema
"""
import psycopg2
import os
from dotenv import load_dotenv

load_dotenv()

def main():
    db_url = os.getenv('DATABASE_URL')

    print(f"[*] Connecting to Neon database...")

    try:
        conn = psycopg2.connect(db_url)
        cursor = conn.cursor()

        # Check if tables exist
        cursor.execute("""
            SELECT tablename
            FROM pg_tables
            WHERE schemaname = 'marketing'
            AND tablename LIKE '%invalid%'
            ORDER BY tablename
        """)
        tables = cursor.fetchall()

        if not tables:
            print("\n[!] No 'invalid' tables found in marketing schema")
            print("[*] Available tables in marketing schema:")
            cursor.execute("""
                SELECT tablename
                FROM pg_tables
                WHERE schemaname = 'marketing'
                ORDER BY tablename
            """)
            for table in cursor.fetchall():
                print(f"   - marketing.{table[0]}")
        else:
            for table in tables:
                table_name = table[0]
                print(f"\n[*] Schema for marketing.{table_name}:")
                cursor.execute(f"""
                    SELECT column_name, data_type, is_nullable, column_default
                    FROM information_schema.columns
                    WHERE table_schema = 'marketing'
                    AND table_name = '{table_name}'
                    ORDER BY ordinal_position
                """)
                columns = cursor.fetchall()
                for col in columns:
                    print(f"   - {col[0]:30s} {col[1]:20s} {'NULL' if col[2]=='YES' else 'NOT NULL':10s} {col[3] or ''}")

                # Count records
                cursor.execute(f"SELECT COUNT(*) FROM marketing.{table_name}")
                count = cursor.fetchone()[0]
                print(f"\n   Total records: {count}")

        conn.close()

    except Exception as e:
        print(f"\n[-] Error: {e}")

if __name__ == "__main__":
    main()
