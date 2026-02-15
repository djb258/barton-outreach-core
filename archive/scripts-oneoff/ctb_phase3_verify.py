#!/usr/bin/env python3
"""
CTB Phase 3 Verification - Enforcement & Lockdown
Validates that CTB guardrails are in place and functioning.
"""
import psycopg2
import os
import sys
from datetime import datetime

sys.stdout.reconfigure(encoding='utf-8', errors='replace')


def main():
    print("=" * 80)
    print("CTB PHASE 3 VERIFICATION - ENFORCEMENT & LOCKDOWN")
    print(f"Started: {datetime.now().isoformat()}")
    print("=" * 80)

    conn = psycopg2.connect(os.environ['DATABASE_URL'])
    cur = conn.cursor()

    errors = []
    warnings = []

    # ============================================
    # CHECK 1: CTB Registry Exists
    # ============================================
    print("\n[CHECK 1] CTB Registry Structure")
    print("-" * 40)

    cur.execute("""
        SELECT EXISTS (
            SELECT 1 FROM information_schema.tables
            WHERE table_schema = 'ctb' AND table_name = 'table_registry'
        )
    """)
    registry_exists = cur.fetchone()[0]

    if registry_exists:
        cur.execute("SELECT COUNT(*) FROM ctb.table_registry")
        registry_count = cur.fetchone()[0]
        print(f"  [OK] ctb.table_registry exists ({registry_count:,} tables registered)")
    else:
        errors.append("ctb.table_registry does not exist")
        print("  [FAIL] ctb.table_registry does not exist")

    cur.execute("""
        SELECT EXISTS (
            SELECT 1 FROM information_schema.tables
            WHERE table_schema = 'ctb' AND table_name = 'violation_log'
        )
    """)
    violation_log_exists = cur.fetchone()[0]

    if violation_log_exists:
        cur.execute("SELECT COUNT(*) FROM ctb.violation_log")
        violation_count = cur.fetchone()[0]
        print(f"  [OK] ctb.violation_log exists ({violation_count:,} violations logged)")
    else:
        errors.append("ctb.violation_log does not exist")
        print("  [FAIL] ctb.violation_log does not exist")

    # ============================================
    # CHECK 2: All Tables Registered
    # ============================================
    print("\n[CHECK 2] Table Registration Coverage")
    print("-" * 40)

    if registry_exists:
        # Find unregistered tables
        cur.execute("""
            SELECT t.table_schema, t.table_name
            FROM information_schema.tables t
            LEFT JOIN ctb.table_registry r
                ON t.table_schema = r.table_schema AND t.table_name = r.table_name
            WHERE t.table_type = 'BASE TABLE'
              AND t.table_schema NOT IN ('pg_catalog', 'information_schema', 'pg_toast', 'ctb')
              AND t.table_schema NOT LIKE 'pg_temp%'
              AND r.registry_id IS NULL
            ORDER BY t.table_schema, t.table_name
        """)
        unregistered = cur.fetchall()

        if unregistered:
            print(f"  [WARN] {len(unregistered)} unregistered tables:")
            for schema, table in unregistered[:10]:
                warnings.append(f"Unregistered table: {schema}.{table}")
                print(f"    - {schema}.{table}")
            if len(unregistered) > 10:
                print(f"    ... and {len(unregistered) - 10} more")
        else:
            print("  [OK] All tables registered in CTB registry")

        # Check leaf type distribution
        cur.execute("""
            SELECT leaf_type, COUNT(*) as count
            FROM ctb.table_registry
            GROUP BY leaf_type
            ORDER BY count DESC
        """)
        print("\n  Leaf Type Distribution:")
        for leaf_type, count in cur.fetchall():
            print(f"    {leaf_type}: {count}")

    # ============================================
    # CHECK 3: Error Table Constraints
    # ============================================
    print("\n[CHECK 3] Error Table NOT NULL Constraints")
    print("-" * 40)

    error_tables_to_check = [
        ('outreach', 'dol_errors', 'error_type'),
        ('outreach', 'blog_errors', 'error_type'),
        ('cl', 'cl_errors_archive', 'error_type'),
        ('people', 'people_errors', 'error_type'),
    ]

    for schema, table, column in error_tables_to_check:
        cur.execute("""
            SELECT is_nullable
            FROM information_schema.columns
            WHERE table_schema = %s AND table_name = %s AND column_name = %s
        """, (schema, table, column))
        result = cur.fetchone()

        if result:
            is_nullable = result[0]
            if is_nullable == 'NO':
                print(f"  [OK] {schema}.{table}.{column} is NOT NULL")
            else:
                warnings.append(f"{schema}.{table}.{column} is nullable")
                print(f"  [WARN] {schema}.{table}.{column} is nullable (should be NOT NULL)")
        else:
            warnings.append(f"{schema}.{table}.{column} column not found")
            print(f"  [WARN] {schema}.{table}.{column} column not found")

    # ============================================
    # CHECK 4: Frozen Table Status
    # ============================================
    print("\n[CHECK 4] Frozen Core Tables")
    print("-" * 40)

    if registry_exists:
        cur.execute("""
            SELECT table_schema, table_name, is_frozen
            FROM ctb.table_registry
            WHERE (table_schema, table_name) IN (
                ('cl', 'company_identity'),
                ('outreach', 'outreach'),
                ('outreach', 'company_target'),
                ('outreach', 'dol'),
                ('outreach', 'blog'),
                ('outreach', 'people'),
                ('outreach', 'bit_scores'),
                ('people', 'people_master'),
                ('people', 'company_slot')
            )
            ORDER BY table_schema, table_name
        """)
        frozen_tables = cur.fetchall()

        frozen_count = 0
        for schema, table, is_frozen in frozen_tables:
            status = "[OK] FROZEN" if is_frozen else "[WARN] NOT FROZEN"
            print(f"  {status} {schema}.{table}")
            if is_frozen:
                frozen_count += 1
            else:
                warnings.append(f"{schema}.{table} is not frozen")

        print(f"\n  Frozen: {frozen_count}/9 core tables")

    # ============================================
    # CHECK 5: Join Key Integrity (Regression Check)
    # ============================================
    print("\n[CHECK 5] Join Key Integrity (Regression)")
    print("-" * 40)

    # CL -> Outreach
    cur.execute("SELECT COUNT(*) FROM cl.company_identity WHERE outreach_id IS NOT NULL")
    cl_with_outreach = cur.fetchone()[0]

    cur.execute("SELECT COUNT(*) FROM outreach.outreach")
    outreach_count = cur.fetchone()[0]

    if cl_with_outreach == outreach_count:
        print(f"  [OK] CL -> Outreach: {cl_with_outreach:,} = {outreach_count:,}")
    else:
        errors.append(f"CL-Outreach mismatch: {cl_with_outreach} vs {outreach_count}")
        print(f"  [FAIL] CL -> Outreach: {cl_with_outreach:,} != {outreach_count:,}")

    # ============================================
    # CHECK 6: Event Trigger Status
    # ============================================
    print("\n[CHECK 6] Event Trigger Status")
    print("-" * 40)

    cur.execute("""
        SELECT evtname, evtenabled
        FROM pg_event_trigger
        WHERE evtname LIKE 'ctb%'
    """)
    triggers = cur.fetchall()

    if triggers:
        for name, enabled in triggers:
            status = "[OK] ENABLED" if enabled == 'O' else "[INFO] DISABLED"
            print(f"  {status} {name}")
    else:
        print("  [INFO] No CTB event triggers found (manual enable required)")

    # ============================================
    # SUMMARY
    # ============================================
    print("\n" + "=" * 80)
    print("VERIFICATION SUMMARY")
    print("=" * 80)

    print(f"\nErrors: {len(errors)}")
    for e in errors:
        print(f"  - {e}")

    print(f"\nWarnings: {len(warnings)}")
    for w in warnings[:10]:
        print(f"  - {w}")
    if len(warnings) > 10:
        print(f"  ... and {len(warnings) - 10} more")

    if len(errors) == 0:
        print("\n[OK] PHASE 3 VERIFICATION PASSED")
    else:
        print("\n[FAIL] PHASE 3 VERIFICATION FAILED")

    conn.close()
    return len(errors)


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
