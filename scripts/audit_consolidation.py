#!/usr/bin/env python3
"""One-shot read-only audit for table consolidation analysis."""
import os, sys, psycopg2
if sys.platform == "win32": sys.stdout.reconfigure(encoding="utf-8")

conn = psycopg2.connect(
    host=os.environ["NEON_HOST"], dbname=os.environ["NEON_DATABASE"],
    user=os.environ["NEON_USER"], password=os.environ["NEON_PASSWORD"],
    sslmode="require",
)
cur = conn.cursor()

# All non-DOL, non-archive-schema tables
cur.execute("""
    SELECT t.table_schema, t.table_name,
           COALESCE(c.leaf_type, 'UNREGISTERED') AS leaf_type,
           COALESCE(c.is_frozen, FALSE) AS is_frozen,
           COALESCE(s.n_live_tup, 0) AS rows
    FROM information_schema.tables t
    LEFT JOIN ctb.table_registry c
        ON c.table_schema = t.table_schema AND c.table_name = t.table_name
    LEFT JOIN pg_stat_user_tables s
        ON s.schemaname = t.table_schema AND s.relname = t.table_name
    WHERE t.table_schema NOT IN ('pg_catalog','information_schema','pg_toast','public','ctb','archive')
      AND t.table_schema NOT LIKE 'pg_temp%%'
      AND t.table_type = 'BASE TABLE'
    ORDER BY t.table_schema, t.table_name
""")
all_tables = cur.fetchall()

# Group by hub
HUB_MAP = {
    "cl": "CL",
    "outreach.outreach": "SPINE", "outreach.outreach_archive": "SPINE",
    "outreach.outreach_errors": "SPINE", "outreach.outreach_excluded": "SPINE",
    "outreach.outreach_legacy_quarantine": "SPINE", "outreach.outreach_orphan_archive": "SPINE",
    "outreach.column_registry": "SPINE", "outreach.ctb_audit_log": "SPINE",
    "outreach.ctb_queue": "SPINE", "outreach.engagement_events": "SPINE",
    "outreach.entity_resolution_queue": "SPINE", "outreach.hub_registry": "SPINE",
    "outreach.manual_overrides": "SPINE", "outreach.mv_credit_usage": "SPINE",
    "outreach.override_audit_log": "SPINE", "outreach.pipeline_audit_log": "SPINE",
    "outreach.company_target": "CT", "outreach.company_hub_status": "CT",
    "outreach.company_target_archive": "CT", "outreach.company_target_dead_ends": "CT",
    "outreach.company_target_errors": "CT", "outreach.company_target_errors_archive": "CT",
    "outreach.company_target_orphaned_archive": "CT",
    "outreach.url_discovery_failures": "CT", "outreach.url_discovery_failures_archive": "CT",
    "outreach.people": "PEOPLE", "outreach.people_archive": "PEOPLE",
    "outreach.people_errors": "PEOPLE",
    "people": "PEOPLE",
    "outreach.dol": "DOL_BRIDGE", "outreach.dol_archive": "DOL_BRIDGE",
    "outreach.dol_audit_log": "DOL_BRIDGE", "outreach.dol_errors": "DOL_BRIDGE",
    "outreach.dol_errors_archive": "DOL_BRIDGE", "outreach.dol_url_enrichment": "DOL_BRIDGE",
    "dol": "DOL_FILING",
    "outreach.bit_scores": "BIT", "outreach.bit_scores_archive": "BIT",
    "outreach.bit_errors": "BIT", "outreach.bit_input_history": "BIT",
    "outreach.bit_signals": "BIT",
    "outreach.campaigns": "BIT", "outreach.send_log": "BIT", "outreach.sequences": "BIT",
    "bit": "BIT",
    "outreach.blog": "BLOG", "outreach.blog_archive": "BLOG",
    "outreach.blog_errors": "BLOG", "outreach.blog_ingress_control": "BLOG",
    "outreach.blog_source_history": "BLOG",
    "outreach.sitemap_discovery": "BLOG", "outreach.source_urls": "BLOG",
    "blog": "BLOG",
    "coverage": "COVERAGE",
    "outreach.appointments": "LANE",
    "sales": "LANE", "partners": "LANE",
    "enrichment": "SYS", "intake": "SYS", "catalog": "SYS",
    "outreach_ctx": "SYS", "ref": "SYS", "reference": "SYS", "shq": "SYS",
    "company": "DEPRECATED", "marketing": "DEPRECATED", "talent_flow": "DEPRECATED",
    "clnt": "FUTURE", "lcs": "FUTURE",
}

def get_hub(schema, table):
    key = f"{schema}.{table}"
    if key in HUB_MAP:
        return HUB_MAP[key]
    if schema in HUB_MAP:
        return HUB_MAP[schema]
    return "OTHER"

hubs = {}
for schema, table, leaf, frozen, rows in all_tables:
    hub = get_hub(schema, table)
    if hub not in hubs:
        hubs[hub] = []
    hubs[hub].append({
        "fqn": f"{schema}.{table}",
        "leaf": leaf, "frozen": frozen, "rows": int(rows),
        "is_archive": "_archive" in table or leaf == "ARCHIVE",
        "is_empty": int(rows) == 0,
    })

order = ["CL", "SPINE", "CT", "PEOPLE", "DOL_BRIDGE", "DOL_FILING", "BIT", "BLOG",
         "COVERAGE", "LANE", "SYS", "DEPRECATED", "FUTURE", "OTHER"]
names = {
    "CL": "CL Authority Registry", "SPINE": "Outreach Spine",
    "CT": "Company Target (04.04.01)", "PEOPLE": "People Intelligence (04.04.02)",
    "DOL_BRIDGE": "DOL Bridge (outreach-side)", "DOL_FILING": "DOL Filing Data (EXEMPT)",
    "BIT": "BIT/CLS Authorization (04.04.04)", "BLOG": "Blog Content (04.04.05)",
    "COVERAGE": "Coverage (04.04.06)", "LANE": "Messaging Lanes",
    "SYS": "System / Reference / Enrichment",
    "DEPRECATED": "DEPRECATED Schemas", "FUTURE": "Future (scaffolded)",
}

print("=" * 100)
print("  TABLE CONSOLIDATION AUDIT — Read-Only")
print("=" * 100)

total = 0
total_data = 0
total_empty = 0
total_archive = 0

for hub_key in order:
    tables = hubs.get(hub_key, [])
    if not tables:
        continue
    name = names.get(hub_key, hub_key)
    data_tables = [t for t in tables if not t["is_archive"] and not t["is_empty"]]
    empty_tables = [t for t in tables if t["is_empty"] and not t["is_archive"]]
    archive_tables = [t for t in tables if t["is_archive"]]
    frozen_tables = [t for t in tables if t["frozen"]]

    total += len(tables)
    total_data += len(data_tables)
    total_empty += len(empty_tables)
    total_archive += len(archive_tables)

    print(f"\n{'─' * 100}")
    print(f"  {name}")
    print(f"  Tables: {len(tables)} total | {len(data_tables)} with data | "
          f"{len(empty_tables)} empty | {len(archive_tables)} archive | "
          f"{len(frozen_tables)} frozen")
    print(f"{'─' * 100}")

    for t in sorted(tables, key=lambda x: (x["is_archive"], x["is_empty"], x["fqn"])):
        frozen_tag = " FROZEN" if t["frozen"] else ""
        empty_tag = " (EMPTY)" if t["is_empty"] else ""
        archive_tag = " [archive]" if t["is_archive"] else ""
        print(f"    {t['fqn']:<55s} {t['leaf']:>14s}{frozen_tag}{empty_tag}{archive_tag}  {t['rows']:>10,} rows")

print(f"\n{'=' * 100}")
print(f"  TOTALS (excluding archive schema)")
print(f"  Tables: {total} | With data: {total_data} | Empty: {total_empty} | Archive: {total_archive}")
print(f"{'=' * 100}")

conn.close()
