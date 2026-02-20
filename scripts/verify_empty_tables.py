#!/usr/bin/env python3
"""
Verify all candidate "empty" tables truly have 0 rows via COUNT(*).

pg_stat_user_tables.n_live_tup is an ESTIMATE from autovacuum.
This script runs actual COUNT(*) on each table to confirm before any DROP.
"""
import os, sys, psycopg2

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")

# These are the 59 tables identified as empty (0 rows per pg_stat)
# We verify each one with a real COUNT(*)
CANDIDATES = [
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
    # Future - lcs (11)
    "lcs.adapter_registry",
    "lcs.domain_pool",
    "lcs.err0",
    "lcs.event",
    "lcs.event_2026_02",
    "lcs.event_2026_03",
    "lcs.event_2026_04",
    "lcs.frame_registry",
    "lcs.signal_queue",
    "lcs.signal_registry",
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
print("  EMPTY TABLE VERIFICATION — COUNT(*) on each candidate")
print("=" * 80)

truly_empty = []
NOT_empty = []
missing = []

for fqn in CANDIDATES:
    schema, table = fqn.split(".", 1)
    try:
        cur.execute(f'SELECT COUNT(*) FROM "{schema}"."{table}"')
        count = cur.fetchone()[0]
        if count == 0:
            truly_empty.append((fqn, count))
            print(f"  {fqn:<55s}  {count:>8,}  OK")
        else:
            NOT_empty.append((fqn, count))
            print(f"  {fqn:<55s}  {count:>8,}  *** HAS DATA ***")
    except Exception as e:
        missing.append((fqn, str(e)))
        print(f"  {fqn:<55s}  {'ERROR':>8s}  {e}")
        conn.rollback()

print()
print("=" * 80)
print(f"  RESULTS")
print(f"  Truly empty (0 rows):    {len(truly_empty)}")
print(f"  NOT empty (has data):    {len(NOT_empty)}")
print(f"  Missing/error:           {len(missing)}")
print("=" * 80)

if NOT_empty:
    print()
    print("  *** TABLES THAT ARE NOT EMPTY — DO NOT DROP ***")
    for fqn, count in NOT_empty:
        print(f"    {fqn}: {count:,} rows")

if missing:
    print()
    print("  *** TABLES WITH ERRORS ***")
    for fqn, err in missing:
        print(f"    {fqn}: {err}")

print()
conn.close()
