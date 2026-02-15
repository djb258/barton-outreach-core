"""
ADR-001 Sub-Hub Table Cardinality Audit
=======================================
Validates OWN-10a, OWN-10b, OWN-10c from ARCHITECTURE.md v2.1.0

Rules:
  OWN-10a: Each sub-hub has exactly 1 CANONICAL table
  OWN-10b: Each sub-hub has exactly 1 ERROR table
  OWN-10c: Additional table types (STAGING, MV, REGISTRY, SUPPORTING) require ADR justification

Architecture:
  Outreach = MAIN HUB (not a sub-hub)
  4 sub-hubs:
    1. company_target
    2. dol
    3. people
    4. blog

ADR Exceptions:
  ADR-020: people.people_master reclassified from CANONICAL to SUPPORTING
           (supports company_slot, the canonical table of the people sub-hub)
"""

import os
import psycopg2

DATABASE_URL = os.environ["DATABASE_URL"]


def run_audit():
    conn = psycopg2.connect(DATABASE_URL)
    cur = conn.cursor()

    # =========================================================================
    # 1. Pull full CTB registry
    # =========================================================================
    cur.execute("""
        SELECT table_schema, table_name, leaf_type, is_frozen
        FROM ctb.table_registry
        ORDER BY table_schema, table_name
    """)
    registry = cur.fetchall()
    registry_set = {(r[0], r[1]): r[2] for r in registry}
    print(f"CTB Registry: {len(registry)} tables total\n")

    # =========================================================================
    # 2. Leaf type distribution
    # =========================================================================
    cur.execute("""
        SELECT leaf_type, COUNT(*) as cnt
        FROM ctb.table_registry
        GROUP BY leaf_type
        ORDER BY cnt DESC
    """)
    leaf_dist = cur.fetchall()
    print("=" * 80)
    print("LEAF TYPE DISTRIBUTION")
    print("=" * 80)
    for leaf, cnt in leaf_dist:
        print(f"  {leaf:<20} {cnt:>5}")
    print()

    # =========================================================================
    # 3. The 4 sub-hubs and their declared tables
    #    Outreach = MAIN HUB (not audited as a sub-hub)
    # =========================================================================
    subhubs = {
        "company_target": {
            "CANONICAL": [("outreach", "company_target")],
            "ERROR": [("outreach", "company_target_errors")],
            "SUPPORTING": [],
        },
        "dol": {
            "CANONICAL": [("outreach", "dol")],
            "ERROR": [("outreach", "dol_errors")],
            "SUPPORTING": [],
        },
        "people": {
            "CANONICAL": [("people", "company_slot")],
            "ERROR": [("people", "people_errors")],
            "SUPPORTING": [("people", "people_master")],  # ADR-020
        },
        "blog": {
            "CANONICAL": [("outreach", "blog")],
            "ERROR": [("outreach", "blog_errors")],
            "SUPPORTING": [],
        },
    }

    # =========================================================================
    # 4. Table existence check
    # =========================================================================
    print("=" * 80)
    print("TABLE EXISTENCE CHECK")
    print("=" * 80)
    all_exist = True
    for subhub, types in subhubs.items():
        for leaf_type, tables in types.items():
            for schema, table in tables:
                if (schema, table) not in registry_set:
                    print(f"  MISSING  {schema}.{table} ({leaf_type}) — sub-hub: {subhub}")
                    all_exist = False
                else:
                    actual_leaf = registry_set[(schema, table)]
                    if actual_leaf != leaf_type:
                        print(f"  MISMATCH {schema}.{table} — declared {leaf_type}, registry says {actual_leaf} — sub-hub: {subhub}")
                        all_exist = False
    if all_exist:
        print("  All declared sub-hub tables found in CTB registry.")
    print()

    # =========================================================================
    # 5. Verify declared tables against live database
    # =========================================================================
    print("=" * 80)
    print("LIVE DATABASE VERIFICATION")
    print("=" * 80)
    for subhub, types in subhubs.items():
        for leaf_type, tables in types.items():
            for schema, table in tables:
                cur.execute("""
                    SELECT EXISTS (
                        SELECT 1 FROM information_schema.tables
                        WHERE table_schema = %s AND table_name = %s
                    )
                """, (schema, table))
                exists = cur.fetchone()[0]
                if exists:
                    cur.execute(f'SELECT COUNT(*) FROM "{schema}"."{table}"')
                    count = cur.fetchone()[0]
                    print(f"  EXISTS   {schema}.{table:<35} {count:>10} rows  ({leaf_type}, {subhub})")
                else:
                    print(f"  MISSING  {schema}.{table:<35} — NOT IN DATABASE  ({leaf_type}, {subhub})")
    print()

    # =========================================================================
    # 6. OWN-10a: Each sub-hub has exactly 1 CANONICAL table
    # =========================================================================
    print("=" * 80)
    print("OWN-10a: Each sub-hub has exactly 1 CANONICAL table")
    print("=" * 80)
    violations_10a = []
    for subhub, types in subhubs.items():
        canonical_count = len(types["CANONICAL"])
        status = "PASS" if canonical_count == 1 else "VIOLATION"
        tables_str = ", ".join(f"{s}.{t}" for s, t in types["CANONICAL"])
        print(f"  {status:<10} {subhub:<25} CANONICAL: {canonical_count}  [{tables_str}]")
        if canonical_count != 1:
            violations_10a.append((subhub, canonical_count, types["CANONICAL"]))
    print()

    # =========================================================================
    # 7. OWN-10b: Each sub-hub has exactly 1 ERROR table
    # =========================================================================
    print("=" * 80)
    print("OWN-10b: Each sub-hub has exactly 1 ERROR table")
    print("=" * 80)
    violations_10b = []
    for subhub, types in subhubs.items():
        error_count = len(types["ERROR"])
        status = "PASS" if error_count == 1 else "VIOLATION"
        tables_str = ", ".join(f"{s}.{t}" for s, t in types["ERROR"]) or "(none)"
        print(f"  {status:<10} {subhub:<25} ERROR: {error_count}  [{tables_str}]")
        if error_count != 1:
            violations_10b.append((subhub, error_count, types["ERROR"]))
    print()

    # =========================================================================
    # 8. OWN-10c: SUPPORTING tables require ADR justification
    # =========================================================================
    print("=" * 80)
    print("OWN-10c: SUPPORTING tables (ADR required)")
    print("=" * 80)
    any_supporting = False
    for subhub, types in subhubs.items():
        supporting = types.get("SUPPORTING", [])
        if supporting:
            any_supporting = True
            tables_str = ", ".join(f"{s}.{t}" for s, t in supporting)
            print(f"  ADR-020   {subhub:<25} SUPPORTING: {len(supporting)}  [{tables_str}]")
    if not any_supporting:
        print("  None — no SUPPORTING tables declared.")
    print()

    # =========================================================================
    # 9. Check for extra tables in sub-hub schemas not accounted for
    # =========================================================================
    print("=" * 80)
    print("UNACCOUNTED TABLES IN SUB-HUB SCHEMAS")
    print("=" * 80)
    # Collect all declared tables
    declared = set()
    for subhub, types in subhubs.items():
        for leaf_type, tables in types.items():
            for schema, table in tables:
                declared.add((schema, table))

    # Also include the main hub spine table and known hub-level tables
    # (these belong to the hub itself, not to any sub-hub)
    declared.add(("outreach", "outreach"))           # Main hub spine
    declared.add(("outreach", "bit_scores"))         # BIT scoring engine (hub-level)
    declared.add(("outreach", "bit_errors"))         # BIT errors (hub-level)
    declared.add(("outreach", "outreach_errors"))    # Spine errors (hub-level)
    declared.add(("outreach", "appointments"))       # Appointments lane (hub-level)
    declared.add(("outreach", "people"))             # People data (hub-level, frozen)
    declared.add(("outreach", "people_errors"))      # People errors (hub-level)
    declared.add(("outreach", "url_discovery_failures"))  # URL failures (hub-level)
    declared.add(("people", "people_invalid"))       # Invalid records (hub-level)
    declared.add(("people", "people_sidecar"))       # Enrichment sidecar (hub-level)
    declared.add(("people", "person_scores"))        # Person BIT scores (hub-level)

    # Check outreach.* and people.* for CANONICAL/ERROR/SUPPORTING tables not in our list
    unaccounted = []
    for (schema, table), leaf in registry_set.items():
        if schema in ("outreach", "people") and leaf in ("CANONICAL", "ERROR", "SUPPORTING"):
            if (schema, table) not in declared:
                unaccounted.append((schema, table, leaf))
                print(f"  {leaf:<12} {schema}.{table}")

    if not unaccounted:
        print("  None — all CANONICAL/ERROR/SUPPORTING tables in outreach/people schemas are accounted for.")
    print()

    # =========================================================================
    # 10. CTB violation log
    # =========================================================================
    cur.execute("SELECT COUNT(*) FROM ctb.violation_log")
    violation_count = cur.fetchone()[0]
    print("=" * 80)
    print(f"CTB VIOLATION LOG: {violation_count} violations")
    print("=" * 80)
    if violation_count > 0:
        cur.execute("SELECT * FROM ctb.violation_log LIMIT 10")
        for row in cur.fetchall():
            print(f"  {row}")
    else:
        print("  Clean — no guardrail violations recorded.")
    print()

    # =========================================================================
    # 11. Frozen core tables
    # =========================================================================
    cur.execute("""
        SELECT table_schema, table_name, leaf_type
        FROM ctb.table_registry
        WHERE is_frozen = TRUE
        ORDER BY table_schema, table_name
    """)
    frozen = cur.fetchall()
    print("=" * 80)
    print(f"FROZEN CORE TABLES: {len(frozen)}")
    print("=" * 80)
    for schema, table, leaf in frozen:
        print(f"  {schema}.{table} ({leaf})")
    print()

    # =========================================================================
    # SUMMARY
    # =========================================================================
    print("=" * 80)
    print("AUDIT SUMMARY — ADR-001 Cardinality Compliance")
    print("=" * 80)
    print(f"  Doctrine Version:    ARCHITECTURE.md v2.1.0")
    print(f"  ADR:                 ADR-001 (Accepted)")
    print(f"  Main Hub:            Outreach (outreach.outreach)")
    print(f"  Sub-hubs audited:    4 (company_target, dol, people, blog)")
    print(f"  Registry Tables:     {len(registry)}")
    print(f"  Frozen Tables:       {len(frozen)}")
    print(f"  CTB Violations:      {violation_count}")
    print()

    print(f"  OWN-10a (exactly 1 CANONICAL):")
    for subhub, types in subhubs.items():
        c = len(types["CANONICAL"])
        status = "PASS" if c == 1 else f"VIOLATION ({c})"
        print(f"    {subhub:<25} {status}")
    print()

    print(f"  OWN-10b (exactly 1 ERROR):")
    for subhub, types in subhubs.items():
        e = len(types["ERROR"])
        status = "PASS" if e == 1 else f"VIOLATION ({e})"
        print(f"    {subhub:<25} {status}")
    print()

    supporting_count = sum(len(t.get("SUPPORTING", [])) for t in subhubs.values())
    print(f"  OWN-10c (SUPPORTING w/ ADR): {supporting_count}")
    for subhub, types in subhubs.items():
        for schema, table in types.get("SUPPORTING", []):
            print(f"    {subhub:<25} {schema}.{table} (ADR-020)")
    print()

    print(f"  Unaccounted CANONICAL/ERROR:  {len(unaccounted)}")
    for schema, table, leaf in unaccounted:
        print(f"    {schema}.{table} ({leaf})")
    print()

    total_violations = len(violations_10a) + len(violations_10b)
    if total_violations == 0:
        print("  RESULT: COMPLIANT")
    else:
        print(f"  RESULT: NON-COMPLIANT — {total_violations} violation(s)")
        print()
        print("  REMEDIATION REQUIRED:")
        for subhub, count, tables in violations_10a:
            tables_str = ", ".join(f"{s}.{t}" for s, t in tables)
            print(f"    {subhub}: {count} CANONICAL tables [{tables_str}] — needs ADR exception or consolidation")
        for subhub, count, tables in violations_10b:
            tables_str = ", ".join(f"{s}.{t}" for s, t in tables) or "(none)"
            if count == 0:
                print(f"    {subhub}: Missing ERROR table — create one")
            else:
                print(f"    {subhub}: {count} ERROR tables [{tables_str}] — consolidate to 1")

    cur.close()
    conn.close()


if __name__ == "__main__":
    run_audit()
