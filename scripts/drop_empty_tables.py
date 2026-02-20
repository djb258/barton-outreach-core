#!/usr/bin/env python3
"""
Drop 55 verified-empty tables + clean up CTB registry.

Pre-flight:
  1. Check for dependent views/FKs that would CASCADE
  2. Show what will be dropped
  3. Execute DROP TABLE
  4. Remove from ctb.table_registry
  5. Verify
"""
import os, sys, psycopg2

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")

TABLES_TO_DROP = [
    # Spine (5)
    "outreach.engagement_events",
    "outreach.manual_overrides",
    "outreach.override_audit_log",
    "outreach.pipeline_audit_log",
    "outreach.outreach_errors",
    # People (6)
    "people.people_sidecar",
    "people.person_scores",
    "people.pressure_signals",
    "people.person_movement_history",
    "people.people_resolution_history",
    "outreach.people_errors",
    # BIT (9)
    "bit.authorization_log",
    "bit.phase_state",
    "bit.proof_lines",
    "bit.movement_events",
    "outreach.bit_input_history",
    "outreach.bit_signals",
    "outreach.campaigns",
    "outreach.send_log",
    "outreach.sequences",
    # Blog (2)
    "blog.pressure_signals",
    "outreach.blog_source_history",
    # DEPRECATED empty (8)
    "company.company_events",
    "company.company_sidecar",
    "company.contact_enrichment",
    "company.email_verification",
    "company.pipeline_errors",
    "company.validation_failures_log",
    "talent_flow.movement_history",
    "talent_flow.movements",
    # Future - clnt (13)
    "clnt.audit_event",
    "clnt.client_hub",
    "clnt.client_master",
    "clnt.compliance_flag",
    "clnt.election",
    "clnt.external_identity_map",
    "clnt.intake_batch",
    "clnt.intake_record",
    "clnt.person",
    "clnt.plan",
    "clnt.plan_quote",
    "clnt.service_request",
    "clnt.vendor",
    # Future - lcs empty only (7)
    "lcs.err0",
    "lcs.event",
    "lcs.event_2026_02",
    "lcs.event_2026_03",
    "lcs.event_2026_04",
    "lcs.signal_queue",
    "lcs.suppression",
    # System empty (5)
    "catalog.relationships",
    "intake.people_candidate",
    "outreach_ctx.spend_log",
    "outreach_ctx.tool_attempts",
    "shq.error_master_archive",
]

conn = psycopg2.connect(
    host=os.environ["NEON_HOST"],
    dbname=os.environ["NEON_DATABASE"],
    user=os.environ["NEON_USER"],
    password=os.environ["NEON_PASSWORD"],
    sslmode="require",
)
cur = conn.cursor()

print("=" * 80)
print("  DROP 55 VERIFIED-EMPTY TABLES")
print("=" * 80)

# ── Step 1: Pre-flight — check for dependent views ──
print("\n  Step 1: Checking for dependent views...")
deps_found = []
for fqn in TABLES_TO_DROP:
    schema, table = fqn.split(".", 1)
    cur.execute("""
        SELECT DISTINCT dependent_ns.nspname || '.' || dependent_view.relname AS view_name
        FROM pg_depend
        JOIN pg_rewrite ON pg_depend.objid = pg_rewrite.oid
        JOIN pg_class AS dependent_view ON pg_rewrite.ev_class = dependent_view.oid
        JOIN pg_class AS source_table ON pg_depend.refobjid = source_table.oid
        JOIN pg_namespace AS dependent_ns ON dependent_view.relnamespace = dependent_ns.oid
        JOIN pg_namespace AS source_ns ON source_table.relnamespace = source_ns.oid
        WHERE source_ns.nspname = %s
          AND source_table.relname = %s
          AND dependent_view.relkind = 'v'
    """, (schema, table))
    views = [r[0] for r in cur.fetchall()]
    if views:
        deps_found.append((fqn, views))
        print(f"    {fqn} -> views: {', '.join(views)}")

if deps_found:
    print(f"\n  Found {len(deps_found)} tables with dependent views.")
    print("  These views will be dropped CASCADE.")
else:
    print("    No dependent views found. Clean drop.")

# ── Step 2: Pre-flight — verify all still empty ──
print("\n  Step 2: Final COUNT(*) verification...")
not_empty = []
for fqn in TABLES_TO_DROP:
    schema, table = fqn.split(".", 1)
    try:
        cur.execute(f'SELECT COUNT(*) FROM "{schema}"."{table}"')
        count = cur.fetchone()[0]
        if count > 0:
            not_empty.append((fqn, count))
    except Exception as e:
        print(f"    ERROR checking {fqn}: {e}")
        conn.rollback()

if not_empty:
    print(f"\n  *** ABORT: {len(not_empty)} tables are NO LONGER EMPTY ***")
    for fqn, count in not_empty:
        print(f"    {fqn}: {count:,} rows")
    print("  Exiting without dropping anything.")
    conn.close()
    sys.exit(1)

print(f"    All {len(TABLES_TO_DROP)} tables confirmed empty. Proceeding.")

# ── Step 3: Drop tables ──
print(f"\n  Step 3: Dropping {len(TABLES_TO_DROP)} tables...")
dropped = 0
errors = 0
for fqn in TABLES_TO_DROP:
    schema, table = fqn.split(".", 1)
    try:
        cur.execute(f'DROP TABLE IF EXISTS "{schema}"."{table}" CASCADE')
        dropped += 1
        print(f"    DROPPED  {fqn}")
    except Exception as e:
        errors += 1
        print(f"    ERROR    {fqn}: {e}")
        conn.rollback()

conn.commit()
print(f"\n    Dropped: {dropped} | Errors: {errors}")

# ── Step 4: Clean up CTB registry ──
print("\n  Step 4: Removing from ctb.table_registry...")
removed = 0
for fqn in TABLES_TO_DROP:
    schema, table = fqn.split(".", 1)
    try:
        cur.execute("""
            DELETE FROM ctb.table_registry
            WHERE table_schema = %s AND table_name = %s
        """, (schema, table))
        if cur.rowcount > 0:
            removed += 1
    except Exception as e:
        print(f"    ERROR removing {fqn} from registry: {e}")
        conn.rollback()

conn.commit()
print(f"    Removed {removed} entries from CTB registry")

# ── Step 5: Verify ──
print("\n  Step 5: Verification...")
still_exist = []
for fqn in TABLES_TO_DROP:
    schema, table = fqn.split(".", 1)
    cur.execute("""
        SELECT 1 FROM information_schema.tables
        WHERE table_schema = %s AND table_name = %s
    """, (schema, table))
    if cur.fetchone():
        still_exist.append(fqn)

if still_exist:
    print(f"    *** {len(still_exist)} tables still exist: ***")
    for fqn in still_exist:
        print(f"      {fqn}")
else:
    print(f"    All {len(TABLES_TO_DROP)} tables confirmed gone.")

# ── Step 6: Updated totals ──
cur.execute("""
    SELECT COUNT(*) FROM information_schema.tables
    WHERE table_schema NOT IN ('pg_catalog','information_schema','pg_toast','public')
      AND table_type = 'BASE TABLE'
""")
total_remaining = cur.fetchone()[0]

cur.execute("SELECT COUNT(*) FROM ctb.table_registry")
ctb_remaining = cur.fetchone()[0]

print(f"\n{'=' * 80}")
print(f"  DONE")
print(f"  Tables dropped:     {dropped}")
print(f"  CTB entries removed: {removed}")
print(f"  Tables remaining:   {total_remaining}")
print(f"  CTB registry:       {ctb_remaining}")
print(f"{'=' * 80}")

conn.close()
