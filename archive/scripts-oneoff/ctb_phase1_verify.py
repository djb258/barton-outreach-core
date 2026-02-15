#!/usr/bin/env python3
"""
CTB Phase 1 Verification - READ ONLY
Validates leaf conformance and join integrity after Phase 1.
"""
import psycopg2
import os
import sys
from datetime import datetime

sys.stdout.reconfigure(encoding='utf-8', errors='replace')

def main():
    print("=" * 80)
    print("CTB PHASE 1 VERIFICATION - READ ONLY")
    print(f"Started: {datetime.now().isoformat()}")
    print("=" * 80)

    conn = psycopg2.connect(os.environ['DATABASE_URL'])
    cur = conn.cursor()

    errors = []
    warnings = []

    # ============================================
    # STEP 1: CTB LEAF CONFORMANCE AUDIT
    # ============================================
    print("\n[STEP 1] CTB Leaf Conformance Audit")
    print("-" * 40)

    # Define allowed table types per sub-hub
    sub_hub_rules = {
        'company_target': {
            'schema': 'outreach',
            'canonical': ['company_target'],
            'errors': ['company_target_errors'],
            'mv': ['company_hub_status'],  # Reclassified as MV
            'registry': [],
            'archive': ['company_target_archive', 'company_target_errors_archive'],
        },
        'dol': {
            'schema': 'outreach',
            'canonical': ['dol'],
            'errors': ['dol_errors'],
            'mv': [],
            'registry': [],
            'archive': ['dol_archive', 'dol_errors_archive'],
        },
        'dol_source': {
            'schema': 'dol',
            'canonical': ['form_5500', 'form_5500_sf', 'schedule_a', 'ein_urls', 'renewal_calendar'],
            'errors': [],
            'mv': ['form_5500_icp_filtered'],
            'registry': ['column_metadata'],
            'archive': [],
        },
        'blog': {
            'schema': 'outreach',
            'canonical': ['blog'],
            'errors': ['blog_errors'],
            'mv': [],
            'registry': ['blog_ingress_control'],
            'archive': ['blog_archive'],
        },
        'people': {
            'schema': 'outreach',
            'canonical': ['people'],
            'errors': ['people_errors'],
            'mv': [],
            'registry': [],
            'archive': ['people_archive'],
        },
        'people_data': {
            'schema': 'people',
            'canonical': ['people_master', 'company_slot'],
            'errors': ['people_errors'],
            'mv': [],
            'registry': ['slot_ingress_control', 'title_slot_mapping'],
            'archive': ['people_master_archive', 'company_slot_archive', 'people_errors_archive'],
        },
        'bit': {
            'schema': 'outreach',
            'canonical': ['bit_scores'],
            'errors': ['bit_errors'],
            'mv': ['bit_signals'],  # Reclassified as MV
            'registry': [],
            'archive': ['bit_scores_archive'],
        },
        'execution': {
            'schema': 'outreach',
            'canonical': ['appointments', 'campaigns', 'sequences'],
            'errors': [],
            'mv': ['engagement_events'],  # Reclassified as MV
            'registry': [],
            'archive': [],
        },
    }

    # Get all tables per schema
    cur.execute("""
        SELECT table_schema, table_name
        FROM information_schema.tables
        WHERE table_type = 'BASE TABLE'
          AND table_schema NOT IN ('pg_catalog', 'information_schema', 'archive', 'pg_toast')
          AND table_schema NOT LIKE 'pg_temp%'
        ORDER BY table_schema, table_name
    """)
    all_tables = cur.fetchall()

    # Check for violations in each sub-hub
    for hub_name, rules in sub_hub_rules.items():
        schema = rules['schema']
        allowed = set(rules['canonical'] + rules['errors'] + rules['mv'] + rules['registry'] + rules['archive'])

        hub_tables = [t for s, t in all_tables if s == schema]

        # Filter to tables that should belong to this hub
        if hub_name == 'company_target':
            hub_tables = [t for t in hub_tables if t.startswith('company_target') or t == 'company_hub_status']
        elif hub_name == 'dol' and schema == 'outreach':
            hub_tables = [t for t in hub_tables if t.startswith('dol')]
        elif hub_name == 'blog':
            hub_tables = [t for t in hub_tables if t.startswith('blog')]
        elif hub_name == 'people' and schema == 'outreach':
            hub_tables = [t for t in hub_tables if t.startswith('people')]
        elif hub_name == 'bit':
            hub_tables = [t for t in hub_tables if t.startswith('bit')]
        elif hub_name == 'execution':
            hub_tables = [t for t in hub_tables if t in ['appointments', 'campaigns', 'sequences', 'send_log', 'engagement_events']]
        elif hub_name == 'dol_source':
            hub_tables = [t for s, t in all_tables if s == 'dol']
        elif hub_name == 'people_data':
            hub_tables = [t for s, t in all_tables if s == 'people']

        violations = [t for t in hub_tables if t not in allowed]

        if violations:
            print(f"  [{hub_name}] VIOLATIONS: {violations}")
            for v in violations:
                errors.append(f"{schema}.{v} not in allowed leaf types for {hub_name}")
        else:
            print(f"  [{hub_name}] OK - {len(hub_tables)} tables conform")

    # ============================================
    # STEP 2: JOIN INTEGRITY - ROW COUNT PARITY
    # ============================================
    print("\n[STEP 2] Join Integrity - Row Count Parity")
    print("-" * 40)

    # CL -> Outreach alignment
    cur.execute("SELECT COUNT(*) FROM cl.company_identity WHERE outreach_id IS NOT NULL")
    cl_with_outreach = cur.fetchone()[0]

    cur.execute("SELECT COUNT(*) FROM outreach.outreach")
    outreach_count = cur.fetchone()[0]

    if cl_with_outreach == outreach_count:
        print(f"  [OK] CL -> Outreach: {cl_with_outreach:,} = {outreach_count:,}")
    else:
        print(f"  [FAIL] CL -> Outreach: {cl_with_outreach:,} != {outreach_count:,}")
        errors.append(f"CL-Outreach mismatch: {cl_with_outreach} vs {outreach_count}")

    # Outreach -> Company Target
    cur.execute("SELECT COUNT(*) FROM outreach.outreach")
    outreach_count = cur.fetchone()[0]

    cur.execute("SELECT COUNT(*) FROM outreach.company_target")
    ct_count = cur.fetchone()[0]

    if outreach_count == ct_count:
        print(f"  [OK] Outreach -> CT: {outreach_count:,} = {ct_count:,}")
    else:
        print(f"  [WARN] Outreach -> CT: {outreach_count:,} != {ct_count:,}")
        warnings.append(f"Outreach-CT mismatch: {outreach_count} vs {ct_count}")

    # Outreach -> Blog
    cur.execute("SELECT COUNT(*) FROM outreach.blog")
    blog_count = cur.fetchone()[0]

    if outreach_count == blog_count:
        print(f"  [OK] Outreach -> Blog: {outreach_count:,} = {blog_count:,}")
    else:
        print(f"  [WARN] Outreach -> Blog: {outreach_count:,} != {blog_count:,}")
        warnings.append(f"Outreach-Blog mismatch: {outreach_count} vs {blog_count}")

    # Outreach -> DOL (partial coverage expected)
    cur.execute("SELECT COUNT(*) FROM outreach.dol")
    dol_count = cur.fetchone()[0]

    dol_pct = (dol_count / outreach_count * 100) if outreach_count > 0 else 0
    print(f"  [INFO] Outreach -> DOL: {dol_count:,} / {outreach_count:,} ({dol_pct:.1f}%)")

    # Outreach -> People (partial coverage expected)
    cur.execute("SELECT COUNT(*) FROM outreach.people")
    people_link_count = cur.fetchone()[0]

    people_pct = (people_link_count / outreach_count * 100) if outreach_count > 0 else 0
    print(f"  [INFO] Outreach -> People Link: {people_link_count:,} / {outreach_count:,} ({people_pct:.1f}%)")

    # People schema integrity
    cur.execute("SELECT COUNT(*) FROM people.people_master")
    people_master_count = cur.fetchone()[0]

    cur.execute("SELECT COUNT(*) FROM people.company_slot")
    slot_count = cur.fetchone()[0]

    print(f"  [INFO] People Master: {people_master_count:,} people")
    print(f"  [INFO] Company Slots: {slot_count:,} slots")

    # ============================================
    # STEP 3: CHECK FOR ARCHIVED SOURCE REFERENCES
    # ============================================
    print("\n[STEP 3] Check for Archived Source References")
    print("-" * 40)

    archived_tables = [
        'company.company_master',
        'marketing.company_master',
        'marketing.people_master',
        'company.company_slots',
        'marketing.failed_company_match',
        'marketing.failed_email_verification',
        'marketing.failed_low_confidence',
        'marketing.failed_no_pattern',
        'marketing.failed_slot_assignment',
        'company.message_key_reference',
        'people.slot_orphan_snapshot_r0_002',
        'people.slot_quarantine_r0_002',
        'public.sn_meeting',
        'public.sn_meeting_outcome',
        'public.sn_prospect',
        'public.sn_sales_process',
        'talent_flow.movement_history',
        'talent_flow.movements',
        'outreach.outreach_orphan_archive',
        'outreach.company_target_orphaned_archive',
        'company.company_events',
        'company.company_sidecar',
        'company.contact_enrichment',
        'company.email_verification',
        'company.pipeline_errors',
        'company.validation_failures_log',
    ]

    # Check if these tables still exist (they should, just archived)
    for table in archived_tables:
        schema, tbl = table.split('.')
        cur.execute("""
            SELECT EXISTS (
                SELECT 1 FROM information_schema.tables
                WHERE table_schema = %s AND table_name = %s
            )
        """, (schema, tbl))
        exists = cur.fetchone()[0]

        if exists:
            cur.execute(f"SELECT COUNT(*) FROM {table}")
            count = cur.fetchone()[0]
            if count > 0:
                warnings.append(f"{table} still has {count:,} rows (should redirect to canonical)")

    print(f"  [INFO] {len(archived_tables)} archived source tables checked")
    print(f"  [INFO] Code review needed to redirect any reads to canonical tables")

    # ============================================
    # STEP 4: SCHEMA STATE SNAPSHOT
    # ============================================
    print("\n[STEP 4] Schema State Snapshot")
    print("-" * 40)

    cur.execute("""
        SELECT table_schema, COUNT(*) as table_count
        FROM information_schema.tables
        WHERE table_type = 'BASE TABLE'
          AND table_schema NOT IN ('pg_catalog', 'information_schema', 'pg_toast')
          AND table_schema NOT LIKE 'pg_temp%'
        GROUP BY table_schema
        ORDER BY table_schema
    """)
    schema_counts = cur.fetchall()

    total_tables = 0
    for schema, count in schema_counts:
        print(f"  {schema}: {count} tables")
        total_tables += count

    print(f"\n  Total: {total_tables} tables")

    # Count CTB archives
    cur.execute("""
        SELECT COUNT(*) FROM pg_tables
        WHERE schemaname = 'archive' AND tablename LIKE '%_ctb'
    """)
    ctb_archive_count = cur.fetchone()[0]
    print(f"  CTB Archives: {ctb_archive_count} tables")

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
    for w in warnings:
        print(f"  - {w}")

    if len(errors) == 0:
        print("\n[OK] PHASE 1 VERIFICATION PASSED")
        print("Ready to tag commit as CTB_PHASE1_LOCK")
    else:
        print("\n[FAIL] PHASE 1 VERIFICATION FAILED")
        print("Fix errors before proceeding")

    conn.close()

    return len(errors)

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
