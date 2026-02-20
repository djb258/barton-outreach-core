#!/usr/bin/env python3
"""
Generate DATABASE_AUDIT.md — Complete table & column inventory from live Neon data.

Cross-references:
  - information_schema (actual tables + columns)
  - ctb.table_registry (leaf type, frozen status)
  - column_registry.yml (descriptions, semantic roles, formats)

Usage:
    doppler run -- python scripts/generate_database_audit.py
"""

import os
import sys
import yaml
import psycopg2
from collections import defaultdict

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")


def get_connection():
    return psycopg2.connect(
        host=os.environ["NEON_HOST"],
        dbname=os.environ["NEON_DATABASE"],
        user=os.environ["NEON_USER"],
        password=os.environ["NEON_PASSWORD"],
        sslmode="require",
    )


def load_column_registry(path="column_registry.yml"):
    """Load column_registry.yml and build lookup: schema.table.column -> metadata."""
    with open(path, "r", encoding="utf-8") as f:
        registry = yaml.safe_load(f)

    lookup = {}

    # Spine table
    spine = registry.get("spine_table", {})
    spine_key = f"{spine['schema']}.{spine['name']}"
    for col in spine.get("columns", []):
        lookup[f"{spine_key}.{col['name']}"] = {
            "description": col.get("description", ""),
            "semantic_role": col.get("semantic_role", ""),
            "format": col.get("format", ""),
        }

    # Sub-hub tables
    for subhub in registry.get("subhubs", []):
        for tbl_def in subhub.get("tables", []):
            tbl_key = f"{tbl_def['schema']}.{tbl_def['name']}"
            for col in tbl_def.get("columns", []):
                lookup[f"{tbl_key}.{col['name']}"] = {
                    "description": col.get("description", ""),
                    "semantic_role": col.get("semantic_role", ""),
                    "format": col.get("format", ""),
                }

    return lookup


SCHEMA_PURPOSES = {
    "cl": "Authority Registry -- sovereign company identity, lifecycle pointers",
    "outreach": "Operational Spine + Sub-Hub Data -- all outreach workflow state and sub-hub tables",
    "outreach_ctx": "Outreach Context -- API context tracking and spend logging",
    "people": "People Intelligence Sub-Hub -- executive slots, contact data, enrichment",
    "dol": "DOL Filings -- Form 5500, Schedule A/C/D/G/H/I data from EFAST2",
    "enrichment": "Enrichment Sources -- Hunter.io company and contact data (system reference)",
    "intake": "Intake & Staging -- raw CSV imports, candidate records, quarantine",
    "bit": "BIT/CLS Authorization -- movement events, phase state, proof lines",
    "blog": "Blog Pressure Signals -- content-derived movement signals",
    "coverage": "Coverage Hub -- service agent assignments and market definitions",
    "company_target": "(Views only) -- pressure signal and authorization views",
    "company": "DEPRECATED -- pre-CL company data, replaced by cl + outreach schemas",
    "marketing": "DEPRECATED -- pre-CL marketing pipeline, replaced by outreach + people schemas",
    "partners": "Partner Lane -- fractional CFO partner records",
    "sales": "Sales Lane -- appointments already had (reactivation)",
    "clnt": "Client Hub Scaffold -- future client management (ALL EMPTY)",
    "lcs": "Lifecycle Signal System -- event streaming infrastructure (NOT ACTIVE)",
    "ref": "Reference Data -- county FIPS codes, ZIP-county mapping",
    "reference": "Reference Data -- US ZIP code master list",
    "shq": "System Health -- audit log, error master, governance monitoring",
    "talent_flow": "DEPRECATED -- executive movement tracking, replaced by bit.movement_events",
    "catalog": "System Catalog -- schema metadata for AI/tooling reference",
    "archive": "Archive -- archived tables from CTB cleanup and sovereign cleanup",
}

SCHEMA_ORDER = [
    "cl", "outreach", "outreach_ctx", "people", "dol", "enrichment",
    "intake", "bit", "blog", "coverage", "company_target", "company",
    "marketing", "partners", "sales", "clnt", "lcs", "ref", "reference",
    "shq", "talent_flow", "catalog", "archive",
]

DEPRECATED_REPLACEMENTS = {
    "company.company_source_urls": "outreach.blog (about_url, news_url) + migration needed for other page types",
    "company.company_master": "cl.company_identity + outreach.company_target",
    "company.pipeline_events": "outreach.pipeline_audit_log",
    "company.company_slots": "people.company_slot",
    "company.company_events": "None (legacy)",
    "company.company_sidecar": "None (legacy)",
    "company.contact_enrichment": "enrichment.hunter_contact",
    "company.email_verification": "people.people_master.email_verified",
    "company.message_key_reference": "None (legacy)",
    "company.pipeline_errors": "outreach.company_target_errors",
    "company.validation_failures_log": "outreach.company_target_errors",
    "marketing.review_queue": "None (legacy)",
    "marketing.company_master": "outreach.company_target",
    "marketing.failed_email_verification": "people.people_errors",
    "marketing.failed_slot_assignment": "people.people_errors",
    "marketing.people_master": "people.people_master",
    "marketing.failed_company_match": "outreach.company_target_errors",
    "marketing.failed_no_pattern": "outreach.company_target_errors",
    "marketing.failed_low_confidence": "outreach.company_target_errors",
    "outreach.campaigns": "None (legacy)",
    "outreach.send_log": "None (legacy)",
    "outreach.sequences": "None (legacy)",
    "talent_flow.movement_history": "bit.movement_events",
    "talent_flow.movements": "bit.movement_events",
}


def main():
    conn = get_connection()
    cur = conn.cursor()

    # ── 1. All tables with CTB status ──
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
        WHERE t.table_schema NOT IN ('pg_catalog','information_schema','pg_toast','public','ctb')
          AND t.table_schema NOT LIKE 'pg_temp%%'
          AND t.table_schema NOT LIKE 'pg_toast_temp%%'
          AND t.table_type = 'BASE TABLE'
        ORDER BY t.table_schema, t.table_name
    """)
    tables = {}
    for schema, tbl, leaf, frozen, rows in cur.fetchall():
        key = f"{schema}.{tbl}"
        tables[key] = {
            "schema": schema,
            "table": tbl,
            "leaf": leaf,
            "frozen": frozen,
            "rows": int(rows),
        }

    # ── 2. All columns ──
    cur.execute("""
        SELECT table_schema, table_name, column_name, data_type,
               is_nullable, column_default, character_maximum_length,
               ordinal_position
        FROM information_schema.columns
        WHERE table_schema NOT IN ('pg_catalog','information_schema','pg_toast','public','ctb')
          AND table_schema NOT LIKE 'pg_temp%%'
          AND table_schema NOT LIKE 'pg_toast_temp%%'
        ORDER BY table_schema, table_name, ordinal_position
    """)
    columns = defaultdict(list)
    for schema, tbl, col, dtype, nullable, default, maxlen, pos in cur.fetchall():
        key = f"{schema}.{tbl}"
        dtype_str = dtype
        if maxlen:
            dtype_str = f"{dtype}({maxlen})"
        columns[key].append({
            "name": col,
            "type": dtype_str,
            "nullable": nullable == "YES",
            "default": str(default)[:60] if default else None,
            "position": pos,
        })

    # ── 3. Views ──
    cur.execute("""
        SELECT table_schema, table_name
        FROM information_schema.views
        WHERE table_schema NOT IN ('pg_catalog','information_schema','pg_toast','public')
        ORDER BY table_schema, table_name
    """)
    views = defaultdict(list)
    for schema, view in cur.fetchall():
        views[schema].append(view)

    conn.close()

    # ── 4. Load column_registry.yml ──
    reg_lookup = load_column_registry()

    # ── 5. Compute stats ──
    total_tables = len(tables)
    total_cols = sum(len(v) for v in columns.values())
    registered = sum(1 for t in tables.values() if t["leaf"] != "UNREGISTERED")
    unregistered = sum(1 for t in tables.values() if t["leaf"] == "UNREGISTERED")
    unreg_with_data = sum(1 for t in tables.values() if t["leaf"] == "UNREGISTERED" and t["rows"] > 0)
    deprecated_with_data = sum(1 for t in tables.values() if t["leaf"] == "DEPRECATED" and t["rows"] > 0)
    frozen_count = sum(1 for t in tables.values() if t["frozen"])
    documented_cols = len(reg_lookup)

    # Group tables by schema
    by_schema = defaultdict(list)
    for key, info in tables.items():
        by_schema[info["schema"]].append(info)

    # ── 6. Build the document ──
    lines = []

    def w(s=""):
        lines.append(s)

    w("# DATABASE AUDIT -- Complete Table & Column Inventory")
    w()
    w("> **Source**: Neon PostgreSQL (live query)")
    w("> **Generated**: 2026-02-20")
    w("> **Cross-referenced**: `ctb.table_registry` + `column_registry.yml`")
    w("> **Authority**: This document is a PROJECTION of the live database. Regenerate with:")
    w("> `doppler run -- python scripts/generate_database_audit.py`")
    w()
    w("---")
    w()
    w("## Executive Summary")
    w()
    w("| Metric | Count |")
    w("|--------|-------|")
    w(f"| **Total tables** | **{total_tables}** |")
    w(f"| Total columns | {total_cols:,} |")
    w(f"| CTB registered | {registered} |")
    w(f"| **UNREGISTERED** | **{unregistered}** |")
    w(f"| Unregistered WITH data | {unreg_with_data} |")
    w(f"| Deprecated WITH data | {deprecated_with_data} |")
    w(f"| Frozen core tables | {frozen_count} |")
    w(f"| Columns in column_registry.yml | {documented_cols} |")
    w(f"| **Column documentation gap** | **{total_cols - documented_cols:,} columns undocumented** |")
    w(f"| Views | {sum(len(v) for v in views.values())} |")
    w(f"| Schemas | {len(by_schema)} |")
    w()

    # ── CRITICAL ISSUES ──
    w("---")
    w()
    w("## Critical Issues")
    w()
    w("### 1. UNREGISTERED Tables with Data")
    w()
    w("These tables exist in the database but are NOT in `ctb.table_registry`.")
    w("They need to be registered with a leaf type or retired.")
    w()
    w("| Schema | Table | Rows | Recommended Action |")
    w("|--------|-------|------|--------------------|")

    unreg_data = sorted(
        [t for t in tables.values() if t["leaf"] == "UNREGISTERED" and t["rows"] > 0],
        key=lambda x: -x["rows"],
    )
    for t in unreg_data:
        s, n = t["schema"], t["table"]
        if s == "dol" and n.startswith("schedule_"):
            action = "Register as CANONICAL (DOL filing data from EFAST2)"
        elif s == "dol":
            action = "Register as CANONICAL (DOL filing data)"
        elif s == "outreach" and n == "source_urls":
            action = "Migrate data to outreach.blog, then DROP"
        elif s == "outreach" and n == "sitemap_discovery":
            action = "Register as SYSTEM or migrate to outreach.blog"
        elif s == "outreach" and n == "company_target_dead_ends":
            action = "Register as ERROR or ARCHIVE"
        elif s == "cl" and "backup" in n:
            action = "Register as ARCHIVE (backup table)"
        elif s == "cl" and "registry" in n:
            action = "Register as REGISTRY"
        elif s in ("partners", "sales"):
            action = "Register as CANONICAL (messaging lane)"
        elif s == "lcs":
            action = "Register as SYSTEM (lifecycle signals)"
        elif s == "clnt":
            action = "Register as CANONICAL (client hub scaffold)"
        else:
            action = "Assess and register"
        w(f"| {s} | {n} | {t['rows']:,} | {action} |")

    w()
    w("### 2. DEPRECATED Tables with Data")
    w()
    w("These are marked DEPRECATED in CTB but still contain data.")
    w("Data should be migrated to canonical tables before dropping.")
    w()
    w("| Schema | Table | Rows | Canonical Replacement |")
    w("|--------|-------|------|-----------------------|")

    dep_data = sorted(
        [t for t in tables.values() if t["leaf"] == "DEPRECATED" and t["rows"] > 0],
        key=lambda x: -x["rows"],
    )
    for t in dep_data:
        key = f"{t['schema']}.{t['table']}"
        repl = DEPRECATED_REPLACEMENTS.get(key, "TBD")
        w(f"| {t['schema']} | {t['table']} | {t['rows']:,} | {repl} |")

    w()
    w("### 3. Column Documentation Gap")
    w()
    w(f"The `column_registry.yml` documents **{documented_cols} columns** across 13 tables.")
    w(f"The database has **{total_cols:,} columns** across {total_tables} tables.")
    pct = 100 * (total_cols - documented_cols) // total_cols if total_cols else 0
    w(f"**{total_cols - documented_cols:,} columns ({pct}%) have NO description, semantic_role, or format.**")
    w()
    w("Every column should have:")
    w("- `description`: What the column stores")
    w("- `semantic_role`: identifier | foreign_key | attribute | metric")
    w("- `format`: UUID | STRING | EMAIL | ENUM | BOOLEAN | INTEGER | ISO-8601 | NUMERIC")
    w()

    # ── SCHEMA SECTIONS ──
    w("---")
    w()
    w("## Schema-by-Schema Inventory")
    w()

    for schema in SCHEMA_ORDER:
        if schema not in by_schema:
            continue

        schema_tables = sorted(by_schema[schema], key=lambda x: x["table"])
        purpose = SCHEMA_PURPOSES.get(schema, "")
        total_rows = sum(t["rows"] for t in schema_tables)

        w(f"### `{schema}` -- {purpose}")
        w()
        w(f"**Tables**: {len(schema_tables)} | **Total rows**: {total_rows:,}")

        if schema in views:
            w(f"**Views**: {len(views[schema])} -- {', '.join(views[schema])}")
        w()

        # Archive schema: just list tables with data
        if schema == "archive":
            archive_with_data = [t for t in schema_tables if t["rows"] > 0]
            w(f"*{len(schema_tables)} archive tables total, {len(archive_with_data)} with data. Column details omitted.*")
            w()
            if archive_with_data:
                w("| Table | Rows |")
                w("|-------|------|")
                for t in sorted(archive_with_data, key=lambda x: -x["rows"]):
                    w(f"| {t['table']} | {t['rows']:,} |")
                w()
            continue

        # Table summary for this schema
        w("| Table | Leaf Type | Frozen | Rows | Columns | Documented |")
        w("|-------|-----------|--------|------|---------|------------|")
        for t in schema_tables:
            key = f"{t['schema']}.{t['table']}"
            cols = columns.get(key, [])
            doc_count = sum(1 for c in cols if f"{key}.{c['name']}" in reg_lookup)
            frozen_str = "YES" if t["frozen"] else ""
            doc_str = f"{doc_count}/{len(cols)}" if doc_count > 0 else "0"
            w(f"| `{t['table']}` | {t['leaf']} | {frozen_str} | {t['rows']:,} | {len(cols)} | {doc_str} |")
        w()

        # Column detail per table
        for t in schema_tables:
            key = f"{t['schema']}.{t['table']}"
            cols = columns.get(key, [])
            if not cols:
                continue

            frozen_tag = " FROZEN" if t["frozen"] else ""
            w(f"#### `{key}` -- {t['leaf']}{frozen_tag} -- {t['rows']:,} rows")
            w()

            doc_count = sum(1 for c in cols if f"{key}.{c['name']}" in reg_lookup)
            if doc_count == len(cols):
                doc_status = "ALL DOCUMENTED"
            elif doc_count > 0:
                doc_status = f"{doc_count}/{len(cols)} documented"
            else:
                doc_status = "UNDOCUMENTED"
            w(f"Column registry: **{doc_status}**")
            w()

            w("| # | Column | Type | Null | Description | Role | Format |")
            w("|---|--------|------|------|-------------|------|--------|")

            for i, c in enumerate(cols, 1):
                reg = reg_lookup.get(f"{key}.{c['name']}", {})
                desc = reg.get("description", "")
                role = reg.get("semantic_role", "")
                fmt = reg.get("format", "")
                null_str = "Y" if c["nullable"] else "N"
                if not desc:
                    desc = "**MISSING**"
                    role = "--"
                    fmt = "--"
                w(f"| {i} | `{c['name']}` | {c['type']} | {null_str} | {desc} | {role} | {fmt} |")

            w()

    # ── Remaining schemas not in order ──
    remaining = set(by_schema.keys()) - set(SCHEMA_ORDER)
    if remaining:
        w("### Other Schemas")
        w()
        for schema in sorted(remaining):
            w(f"- `{schema}`: {len(by_schema[schema])} tables")
        w()

    # ── Write file ──
    output = "\n".join(lines)
    out_path = "docs/DATABASE_AUDIT.md"
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(output)

    print(f"\nWritten: {out_path}")
    print(f"  {total_tables} tables, {total_cols:,} columns")
    print(f"  {documented_cols} columns documented in column_registry.yml")
    print(f"  {total_cols - documented_cols:,} columns UNDOCUMENTED")
    print(f"  {unregistered} UNREGISTERED tables ({unreg_with_data} with data)")
    print(f"  {deprecated_with_data} DEPRECATED tables with data")


if __name__ == "__main__":
    main()
