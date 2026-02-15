#!/usr/bin/env python3
"""
Enforcement Migration Executor

Execute with: doppler run -- python scripts/execute_enforcement_migrations.py

This script:
1. Executes all 2026-02-02 enforcement migrations in order
2. Verifies columns, tables, and functions exist
3. Runs governance job test
4. Outputs verification results
"""

import os
import sys
import psycopg2
from psycopg2.extras import RealDictCursor
from pathlib import Path
from datetime import datetime

# Migration files in execution order
MIGRATIONS = [
    "infra/migrations/2026-02-02-error-governance-columns.sql",
    "infra/migrations/2026-02-02-error-archive-tables.sql",
    "infra/migrations/2026-02-02-error-ttl-archive-functions.sql",
    "infra/migrations/2026-02-02-promotion-gate-functions.sql",
]

# Verification queries
VERIFY_COLUMNS = [
    ("outreach.dol_errors", "disposition"),
    ("outreach.dol_errors", "ttl_tier"),
    ("outreach.dol_errors", "retry_count"),
    ("outreach.dol_errors", "parked_at"),
    ("outreach.dol_errors", "escalation_level"),
    ("outreach.company_target_errors", "disposition"),
    ("outreach.company_target_errors", "ttl_tier"),
    ("people.people_errors", "disposition"),
    ("people.people_errors", "ttl_tier"),
    ("company.url_discovery_failures", "disposition"),
]

VERIFY_TABLES = [
    "outreach.dol_errors_archive",
    "outreach.company_target_errors_archive",
    "people.people_errors_archive",
    "company.url_discovery_failures_archive",
    "shq.error_master_archive",
]

VERIFY_FUNCTIONS = [
    "shq.fn_get_ttl_interval",
    "shq.fn_archive_expired_errors",
    "shq.fn_auto_park_exhausted_retries",
    "shq.fn_escalate_stale_parked_errors",
    "shq.fn_cleanup_expired_archives",
    "shq.fn_run_error_governance_jobs",
    "shq.fn_check_company_target_done",
    "shq.fn_check_dol_done",
    "shq.fn_check_people_done",
    "shq.fn_check_blog_done",
    "shq.fn_check_bit_done",
    "shq.fn_can_promote_to_hub",
    "shq.fn_get_promotion_blockers",
]

VERIFY_VIEWS = [
    "shq.vw_error_governance_summary",
    "shq.vw_blocking_errors_by_outreach",
    "shq.vw_promotion_readiness",
    "shq.vw_promotion_readiness_summary",
]


def connect_db():
    """Connect to Neon PostgreSQL."""
    return psycopg2.connect(
        host=os.environ['NEON_HOST'],
        database=os.environ['NEON_DATABASE'],
        user=os.environ['NEON_USER'],
        password=os.environ['NEON_PASSWORD'],
        sslmode='require'
    )


def log(msg, level="INFO"):
    """Log with timestamp."""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{timestamp}] [{level}] {msg}")


def execute_migration(conn, migration_path):
    """Execute a single migration file."""
    log(f"Executing: {migration_path}")

    repo_root = Path(__file__).parent.parent
    full_path = repo_root / migration_path

    if not full_path.exists():
        log(f"Migration file not found: {full_path}", "ERROR")
        return False

    sql = full_path.read_text()

    try:
        with conn.cursor() as cur:
            cur.execute(sql)
        conn.commit()
        log(f"SUCCESS: {migration_path}", "SUCCESS")
        return True
    except Exception as e:
        conn.rollback()
        log(f"FAILED: {migration_path} - {e}", "ERROR")
        return False


def verify_column_exists(cur, table, column):
    """Check if a column exists in a table."""
    schema, table_name = table.split(".")
    cur.execute("""
        SELECT 1 FROM information_schema.columns
        WHERE table_schema = %s AND table_name = %s AND column_name = %s
    """, (schema, table_name, column))
    return cur.fetchone() is not None


def verify_table_exists(cur, table):
    """Check if a table exists."""
    schema, table_name = table.split(".")
    cur.execute("""
        SELECT 1 FROM information_schema.tables
        WHERE table_schema = %s AND table_name = %s
    """, (schema, table_name))
    return cur.fetchone() is not None


def verify_function_exists(cur, func):
    """Check if a function exists."""
    schema, func_name = func.split(".")
    cur.execute("""
        SELECT 1 FROM pg_proc p
        JOIN pg_namespace n ON p.pronamespace = n.oid
        WHERE n.nspname = %s AND p.proname = %s
    """, (schema, func_name))
    return cur.fetchone() is not None


def verify_view_exists(cur, view):
    """Check if a view exists."""
    schema, view_name = view.split(".")
    cur.execute("""
        SELECT 1 FROM information_schema.views
        WHERE table_schema = %s AND table_name = %s
    """, (schema, view_name))
    return cur.fetchone() is not None


def run_verification(conn):
    """Run all verification checks."""
    results = {
        "columns": [],
        "tables": [],
        "functions": [],
        "views": [],
        "all_passed": True
    }

    with conn.cursor(cursor_factory=RealDictCursor) as cur:
        # Verify columns
        log("Verifying columns...")
        for table, column in VERIFY_COLUMNS:
            exists = verify_column_exists(cur, table, column)
            results["columns"].append({
                "table": table,
                "column": column,
                "exists": exists
            })
            if not exists:
                results["all_passed"] = False
                log(f"  MISSING: {table}.{column}", "ERROR")
            else:
                log(f"  OK: {table}.{column}")

        # Verify tables
        log("Verifying archive tables...")
        for table in VERIFY_TABLES:
            exists = verify_table_exists(cur, table)
            results["tables"].append({
                "table": table,
                "exists": exists
            })
            if not exists:
                results["all_passed"] = False
                log(f"  MISSING: {table}", "ERROR")
            else:
                log(f"  OK: {table}")

        # Verify functions
        log("Verifying functions...")
        for func in VERIFY_FUNCTIONS:
            exists = verify_function_exists(cur, func)
            results["functions"].append({
                "function": func,
                "exists": exists
            })
            if not exists:
                results["all_passed"] = False
                log(f"  MISSING: {func}", "ERROR")
            else:
                log(f"  OK: {func}")

        # Verify views
        log("Verifying views...")
        for view in VERIFY_VIEWS:
            exists = verify_view_exists(cur, view)
            results["views"].append({
                "view": view,
                "exists": exists
            })
            if not exists:
                results["all_passed"] = False
                log(f"  MISSING: {view}", "ERROR")
            else:
                log(f"  OK: {view}")

    return results


def test_governance_job(conn):
    """Test the governance job runs without error."""
    log("Testing governance job execution...")
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("SELECT * FROM shq.fn_run_error_governance_jobs()")
            results = cur.fetchall()
            conn.commit()
            log(f"  Governance job executed successfully")
            for row in results:
                log(f"    {row['job_name']}: {row['result_summary']}")
            return True
    except Exception as e:
        conn.rollback()
        log(f"  Governance job failed: {e}", "ERROR")
        return False


def test_promotion_readiness(conn):
    """Test promotion readiness view."""
    log("Testing promotion readiness view...")
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("SELECT * FROM shq.vw_promotion_readiness_summary")
            results = cur.fetchall()
            log(f"  Promotion readiness summary:")
            for row in results:
                log(f"    {row['readiness_tier']}: {row['count']} ({row['percentage']}%)")
            return True
    except Exception as e:
        log(f"  Promotion readiness query failed: {e}", "ERROR")
        return False


def main():
    """Main execution."""
    log("=" * 70)
    log("ENFORCEMENT MIGRATION EXECUTOR")
    log("=" * 70)

    # Check environment
    required_vars = ['NEON_HOST', 'NEON_DATABASE', 'NEON_USER', 'NEON_PASSWORD']
    missing = [v for v in required_vars if v not in os.environ]
    if missing:
        log(f"Missing environment variables: {missing}", "ERROR")
        log("Run with: doppler run -- python scripts/execute_enforcement_migrations.py")
        sys.exit(1)

    # Connect
    log("Connecting to Neon PostgreSQL...")
    try:
        conn = connect_db()
        log("Connected successfully")
    except Exception as e:
        log(f"Connection failed: {e}", "ERROR")
        sys.exit(1)

    # Execute migrations
    log("-" * 70)
    log("PHASE 1: EXECUTE MIGRATIONS")
    log("-" * 70)

    all_succeeded = True
    for migration in MIGRATIONS:
        if not execute_migration(conn, migration):
            all_succeeded = False
            log("STOPPING: Migration failed", "ERROR")
            break

    if not all_succeeded:
        conn.close()
        sys.exit(1)

    # Verify
    log("-" * 70)
    log("PHASE 2: VERIFY ARTIFACTS")
    log("-" * 70)

    results = run_verification(conn)

    if not results["all_passed"]:
        log("VERIFICATION FAILED: Some artifacts missing", "ERROR")
        conn.close()
        sys.exit(1)

    # Test
    log("-" * 70)
    log("PHASE 3: TEST EXECUTION")
    log("-" * 70)

    if not test_governance_job(conn):
        log("GOVERNANCE JOB TEST FAILED", "ERROR")
        conn.close()
        sys.exit(1)

    if not test_promotion_readiness(conn):
        log("PROMOTION READINESS TEST FAILED", "ERROR")
        conn.close()
        sys.exit(1)

    # Summary
    log("-" * 70)
    log("EXECUTION COMPLETE")
    log("-" * 70)
    log(f"Migrations executed: {len(MIGRATIONS)}")
    log(f"Columns verified: {len(results['columns'])}")
    log(f"Tables verified: {len(results['tables'])}")
    log(f"Functions verified: {len(results['functions'])}")
    log(f"Views verified: {len(results['views'])}")
    log("")
    log("STATUS: ALL CHECKS PASSED")
    log("=" * 70)

    conn.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
