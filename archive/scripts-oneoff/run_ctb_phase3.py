#!/usr/bin/env python3
"""
CTB Phase 3: Enforcement Execution
Creates registry, registers tables, adds guardrails.
"""
import psycopg2
import os
import sys
from datetime import datetime

sys.stdout.reconfigure(encoding='utf-8', errors='replace')


def main():
    print("=" * 70)
    print("CTB PHASE 3: ENFORCEMENT EXECUTION")
    print(f"Started: {datetime.now().isoformat()}")
    print("=" * 70)

    conn = psycopg2.connect(os.environ['DATABASE_URL'])
    conn.autocommit = False
    cur = conn.cursor()

    try:
        # ============================================
        # PART 1: Create CTB Schema and Registry
        # ============================================
        print("\n[PART 1] Creating CTB Registry Schema...")

        cur.execute("CREATE SCHEMA IF NOT EXISTS ctb")
        print("  [OK] Schema ctb created")

        cur.execute("""
            CREATE TABLE IF NOT EXISTS ctb.table_registry (
                registry_id SERIAL PRIMARY KEY,
                table_schema VARCHAR(100) NOT NULL,
                table_name VARCHAR(100) NOT NULL,
                leaf_type VARCHAR(50) NOT NULL CHECK (leaf_type IN
                    ('CANONICAL', 'ERROR', 'MV', 'REGISTRY', 'STAGING', 'ARCHIVE', 'SYSTEM', 'DEPRECATED')),
                ctb_path VARCHAR(200),
                parent_table VARCHAR(200),
                created_at TIMESTAMPTZ DEFAULT NOW(),
                registered_by VARCHAR(100) DEFAULT 'ctb_phase3',
                is_frozen BOOLEAN DEFAULT FALSE,
                notes TEXT,
                UNIQUE (table_schema, table_name)
            )
        """)
        print("  [OK] ctb.table_registry created")

        cur.execute("""
            CREATE TABLE IF NOT EXISTS ctb.violation_log (
                violation_id SERIAL PRIMARY KEY,
                violation_type VARCHAR(100) NOT NULL,
                table_schema VARCHAR(100),
                table_name VARCHAR(100),
                column_name VARCHAR(100),
                violation_message TEXT NOT NULL,
                severity VARCHAR(20) DEFAULT 'WARNING' CHECK (severity IN ('INFO', 'WARNING', 'ERROR', 'CRITICAL')),
                detected_at TIMESTAMPTZ DEFAULT NOW(),
                resolved_at TIMESTAMPTZ,
                resolution_note TEXT
            )
        """)
        print("  [OK] ctb.violation_log created")

        # ============================================
        # PART 2: Register All Existing Tables
        # ============================================
        print("\n[PART 2] Registering tables...")

        cur.execute("""
            SELECT table_schema, table_name
            FROM information_schema.tables
            WHERE table_type = 'BASE TABLE'
              AND table_schema NOT IN ('pg_catalog', 'information_schema', 'pg_toast', 'ctb')
              AND table_schema NOT LIKE 'pg_temp%'
            ORDER BY table_schema, table_name
        """)
        all_tables = cur.fetchall()

        registered = 0
        for schema, table in all_tables:
            # Determine leaf type
            if schema == 'archive':
                leaf_type = 'ARCHIVE'
            elif schema == 'intake':
                leaf_type = 'STAGING'
            elif schema in ('catalog', 'ref', 'shq', 'public', 'enrichment', 'outreach_ctx'):
                leaf_type = 'SYSTEM'
            elif schema in ('marketing', 'company', 'talent_flow'):
                leaf_type = 'DEPRECATED'
            elif 'error' in table.lower() or 'err' in table.lower() or 'failed' in table.lower():
                leaf_type = 'ERROR'
            elif '_status' in table or '_signals' in table or '_events' in table or 'filtered' in table:
                leaf_type = 'MV'
            elif 'registry' in table or 'mapping' in table or 'control' in table or 'metadata' in table:
                leaf_type = 'REGISTRY'
            elif 'staging' in table or 'candidate' in table or 'queue' in table:
                leaf_type = 'STAGING'
            elif 'archive' in table:
                leaf_type = 'ARCHIVE'
            else:
                leaf_type = 'CANONICAL'

            # Determine CTB path
            if schema == 'cl':
                ctb_path = 'cl -> company_identity'
            elif schema == 'outreach':
                ctb_path = 'outreach -> outreach_id'
            elif schema == 'dol':
                ctb_path = 'dol -> form_5500'
            elif schema == 'people':
                ctb_path = 'people -> people_master'
            elif schema == 'bit':
                ctb_path = 'bit -> bit_scores'
            else:
                ctb_path = f'{schema} (non-CTB)'

            cur.execute("""
                INSERT INTO ctb.table_registry (table_schema, table_name, leaf_type, ctb_path, notes)
                VALUES (%s, %s, %s, %s, 'Registered by CTB Phase 3')
                ON CONFLICT (table_schema, table_name) DO NOTHING
            """, (schema, table, leaf_type, ctb_path))
            registered += 1

        print(f"  [OK] {registered} tables registered")

        # ============================================
        # PART 3: Add NOT NULL Constraints
        # ============================================
        print("\n[PART 3] Adding NOT NULL constraints...")

        error_tables = [
            ('outreach', 'dol_errors', 'error_type'),
            ('outreach', 'blog_errors', 'error_type'),
            ('cl', 'cl_errors_archive', 'error_type'),
        ]

        for schema, table, column in error_tables:
            cur.execute(f"SELECT COUNT(*) FROM {schema}.{table} WHERE {column} IS NULL")
            null_count = cur.fetchone()[0]

            if null_count == 0:
                try:
                    cur.execute(f"ALTER TABLE {schema}.{table} ALTER COLUMN {column} SET NOT NULL")
                    print(f"  [OK] {schema}.{table}.{column} set to NOT NULL")
                except Exception as e:
                    print(f"  [WARN] {schema}.{table}.{column}: {e}")
            else:
                print(f"  [SKIP] {schema}.{table}.{column}: {null_count} NULL values exist")

        # ============================================
        # PART 4: Freeze Core Tables
        # ============================================
        print("\n[PART 4] Freezing core tables...")

        core_tables = [
            ('cl', 'company_identity'),
            ('outreach', 'outreach'),
            ('outreach', 'company_target'),
            ('outreach', 'dol'),
            ('outreach', 'blog'),
            ('outreach', 'people'),
            ('outreach', 'bit_scores'),
            ('people', 'people_master'),
            ('people', 'company_slot'),
        ]

        for schema, table in core_tables:
            cur.execute("""
                UPDATE ctb.table_registry
                SET is_frozen = TRUE
                WHERE table_schema = %s AND table_name = %s
            """, (schema, table))

        cur.execute("SELECT COUNT(*) FROM ctb.table_registry WHERE is_frozen = TRUE")
        frozen_count = cur.fetchone()[0]
        print(f"  [OK] {frozen_count} core tables frozen")

        # ============================================
        # PART 5: Log Migration
        # ============================================
        cur.execute("""
            INSERT INTO public.migration_log (migration_name, step, status, details, executed_at)
            VALUES ('ctb-phase3-enforcement', 'complete', 'success',
                    'CTB Phase 3: Registry created, tables registered, guardrails added', NOW())
        """)

        conn.commit()
        print("\n" + "=" * 70)
        print("[OK] CTB PHASE 3 ENFORCEMENT COMPLETE")
        print("=" * 70)

    except Exception as e:
        conn.rollback()
        print(f"\n[ERROR] {e}")
        print("All changes rolled back")
        raise

    finally:
        cur.close()
        conn.close()


if __name__ == "__main__":
    main()
