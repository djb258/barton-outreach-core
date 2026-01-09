#!/usr/bin/env python3
"""
PEOPLE SLOT BULK SEED — STRUCTURE ONLY (ALL OUTREACH IDs)
==========================================================
Purpose: Bulk-create CEO, CFO, HR slots for ALL outreach_ids missing them
Target: people.company_slot
Expected scale: ~62,000 outreach_ids

HARD CONSTRAINTS:
  ✅ NO writes to people.people_master
  ✅ NO writes to people.people_candidate
  ✅ slot_ingress_control MUST remain OFF
  ✅ Idempotent (safe to re-run)
  ✅ Transaction-wrapped
"""

import os
import sys
from datetime import datetime

try:
    import psycopg2
    from psycopg2.extras import RealDictCursor
except ImportError:
    print("ERROR: psycopg2 not installed. Run: pip install psycopg2-binary")
    sys.exit(1)


def get_connection():
    """Get database connection from DATABASE_URL environment variable."""
    database_url = os.environ.get("DATABASE_URL")
    if not database_url:
        raise ValueError("DATABASE_URL environment variable not set")
    return psycopg2.connect(database_url)


def preflight_checks(cur):
    """Run all preflight safety checks. Abort if any fail."""
    print("\n" + "=" * 70)
    print("  PREFLIGHT SAFETY CHECKS")
    print("=" * 70)
    
    # Check 1: Verify slot_ingress_control is OFF
    cur.execute("""
        SELECT is_enabled 
        FROM people.slot_ingress_control 
        WHERE switch_name = 'slot_ingress'
    """)
    result = cur.fetchone()
    
    if result is None:
        print("  ❌ ABORT: slot_ingress_control table missing or empty")
        return False
    
    if result['is_enabled']:
        print("  ❌ ABORT: slot_ingress_control is ENABLED — cannot proceed")
        return False
    
    print("  ✓ slot_ingress_control.is_enabled = FALSE")
    
    # Check 2: Verify UNIQUE constraint exists
    cur.execute("""
        SELECT 1 FROM pg_constraint 
        WHERE conname = 'uq_company_slot_outreach_slot_type'
        AND conrelid = 'people.company_slot'::regclass
    """)
    if not cur.fetchone():
        print("  ❌ ABORT: UNIQUE constraint uq_company_slot_outreach_slot_type missing")
        return False
    
    print("  ✓ UNIQUE(outreach_id, slot_type) constraint exists")
    
    # Check 3: Count source outreach_ids
    cur.execute("""
        SELECT COUNT(DISTINCT outreach_id) as total_outreach_ids
        FROM outreach.company_target
        WHERE outreach_id IS NOT NULL
    """)
    result = cur.fetchone()
    total_source = result['total_outreach_ids']
    print(f"  ✓ Source outreach_ids in company_target: {total_source:,}")
    
    # Check 4: Count existing slots
    cur.execute("""
        SELECT COUNT(*) as existing_slots
        FROM people.company_slot
        WHERE outreach_id IS NOT NULL
    """)
    result = cur.fetchone()
    print(f"  ✓ Existing slots in people.company_slot: {result['existing_slots']:,}")
    
    # Check 5: Pre-counts by slot_type
    cur.execute("""
        SELECT slot_type, COUNT(*) as cnt
        FROM people.company_slot
        WHERE outreach_id IS NOT NULL
        GROUP BY slot_type
        ORDER BY slot_type
    """)
    print("\n  Pre-execution slot counts by type:")
    for row in cur.fetchall():
        print(f"    {row['slot_type']}: {row['cnt']:,}")
    
    # Check 6: Count people_master and people_candidate for baseline
    cur.execute("SELECT COUNT(*) as cnt FROM people.people_master")
    people_master_pre = cur.fetchone()['cnt']
    
    cur.execute("SELECT COUNT(*) as cnt FROM people.people_candidate")
    people_candidate_pre = cur.fetchone()['cnt']
    
    print(f"\n  Baseline counts (MUST NOT CHANGE):")
    print(f"    people.people_master: {people_master_pre:,}")
    print(f"    people.people_candidate: {people_candidate_pre:,}")
    
    print("\n  ✓ All preflight checks PASSED")
    print("=" * 70)
    
    return {
        'total_source_outreach_ids': total_source,
        'people_master_pre': people_master_pre,
        'people_candidate_pre': people_candidate_pre
    }


def execute_bulk_seed(cur, slot_types):
    """
    Execute bulk INSERT for missing slots.
    Uses LEFT JOIN + IS NULL pattern for idempotency.
    """
    print("\n" + "=" * 70)
    print("  EXECUTING BULK SLOT SEED")
    print("=" * 70)
    
    results = {}
    total_inserted = 0
    total_skipped = 0
    
    for slot_type in slot_types:
        print(f"\n  Processing slot_type: {slot_type}")
        
        # Count how many would be inserted
        cur.execute("""
            SELECT COUNT(*) as to_insert
            FROM outreach.company_target ct
            LEFT JOIN people.company_slot cs 
                ON cs.outreach_id = ct.outreach_id 
                AND cs.slot_type = %s
            WHERE ct.outreach_id IS NOT NULL
              AND cs.company_slot_unique_id IS NULL
        """, (slot_type,))
        to_insert = cur.fetchone()['to_insert']
        
        # Count existing
        cur.execute("""
            SELECT COUNT(*) as existing
            FROM people.company_slot
            WHERE slot_type = %s AND outreach_id IS NOT NULL
        """, (slot_type,))
        existing = cur.fetchone()['existing']
        
        print(f"    Existing {slot_type} slots: {existing:,}")
        print(f"    Missing {slot_type} slots: {to_insert:,}")
        
        if to_insert == 0:
            print(f"    ⏭️  No inserts needed for {slot_type}")
            results[slot_type] = {'inserted': 0, 'skipped': existing}
            total_skipped += existing
            continue
        
        # Execute INSERT with LEFT JOIN + IS NULL
        # We need company_unique_id - get it from existing slots or company_target
        cur.execute("""
            INSERT INTO people.company_slot (
                company_slot_unique_id,
                company_unique_id,
                outreach_id,
                slot_type,
                slot_status,
                canonical_flag,
                creation_reason,
                created_at
            )
            SELECT 
                gen_random_uuid()::text,
                COALESCE(
                    -- Try to get company_unique_id from existing slot for same outreach_id
                    (SELECT cs2.company_unique_id 
                     FROM people.company_slot cs2 
                     WHERE cs2.outreach_id = ct.outreach_id 
                     LIMIT 1),
                    -- Fallback: use company_target.company_unique_id if it exists
                    ct.company_unique_id::text
                ),
                ct.outreach_id,
                %s,
                'open',
                TRUE,
                'bulk_seed_structure_only',
                NOW()
            FROM outreach.company_target ct
            LEFT JOIN people.company_slot cs 
                ON cs.outreach_id = ct.outreach_id 
                AND cs.slot_type = %s
            WHERE ct.outreach_id IS NOT NULL
              AND cs.company_slot_unique_id IS NULL
              AND EXISTS (
                  -- Only insert if we can find a valid company_unique_id
                  SELECT 1 FROM people.company_slot cs2 
                  WHERE cs2.outreach_id = ct.outreach_id
              )
        """, (slot_type, slot_type))
        
        inserted = cur.rowcount
        print(f"    ✅ Inserted {inserted:,} {slot_type} slots")
        
        results[slot_type] = {'inserted': inserted, 'skipped': existing}
        total_inserted += inserted
        total_skipped += existing
    
    print(f"\n  TOTAL: {total_inserted:,} slots inserted, {total_skipped:,} already existed")
    print("=" * 70)
    
    return results, total_inserted, total_skipped


def run_validation_queries(cur, preflight_data):
    """Run validation queries and return results."""
    print("\n" + "=" * 70)
    print("  VALIDATION QUERIES")
    print("=" * 70)
    
    # Query 1: COUNT(*) by slot_type
    cur.execute("""
        SELECT slot_type, COUNT(*) as cnt
        FROM people.company_slot
        WHERE outreach_id IS NOT NULL
        GROUP BY slot_type
        ORDER BY slot_type
    """)
    print("\n  Post-execution slot counts by type:")
    slot_counts = {}
    for row in cur.fetchall():
        print(f"    {row['slot_type']}: {row['cnt']:,}")
        slot_counts[row['slot_type']] = row['cnt']
    
    # Query 2: COUNT(DISTINCT outreach_id)
    cur.execute("""
        SELECT COUNT(DISTINCT outreach_id) as unique_outreach_ids
        FROM people.company_slot
        WHERE outreach_id IS NOT NULL
    """)
    unique_outreach = cur.fetchone()['unique_outreach_ids']
    print(f"\n  Unique outreach_ids with slots: {unique_outreach:,}")
    
    # Query 3: Verify kill switch unchanged
    cur.execute("""
        SELECT is_enabled 
        FROM people.slot_ingress_control 
        WHERE switch_name = 'slot_ingress'
    """)
    is_enabled = cur.fetchone()['is_enabled']
    print(f"\n  slot_ingress_control.is_enabled: {is_enabled}")
    if is_enabled:
        print("  ❌ ERROR: Kill switch was modified!")
    else:
        print("  ✓ Kill switch remains OFF")
    
    # Query 4: Verify zero-touch on people_master
    cur.execute("SELECT COUNT(*) as cnt FROM people.people_master")
    people_master_post = cur.fetchone()['cnt']
    delta_master = people_master_post - preflight_data['people_master_pre']
    print(f"\n  people.people_master count: {people_master_post:,} (delta: {delta_master})")
    if delta_master != 0:
        print("  ❌ ERROR: people_master was modified!")
    else:
        print("  ✓ people_master: ZERO TOUCH")
    
    # Query 5: Verify zero-touch on people_candidate
    cur.execute("SELECT COUNT(*) as cnt FROM people.people_candidate")
    people_candidate_post = cur.fetchone()['cnt']
    delta_candidate = people_candidate_post - preflight_data['people_candidate_pre']
    print(f"  people.people_candidate count: {people_candidate_post:,} (delta: {delta_candidate})")
    if delta_candidate != 0:
        print("  ❌ ERROR: people_candidate was modified!")
    else:
        print("  ✓ people_candidate: ZERO TOUCH")
    
    print("=" * 70)
    
    return {
        'slot_counts': slot_counts,
        'unique_outreach_ids': unique_outreach,
        'kill_switch_enabled': is_enabled,
        'people_master_delta': delta_master,
        'people_candidate_delta': delta_candidate
    }


def generate_report(preflight_data, seed_results, total_inserted, total_skipped, validation):
    """Generate final execution report."""
    print("\n")
    print("╔" + "═" * 68 + "╗")
    print("║  PEOPLE SLOT BULK SEED — STRUCTURE ONLY (ALL OUTREACH IDs)        ║")
    print("║  EXECUTION REPORT                                                  ║")
    print("╠" + "═" * 68 + "╣")
    print(f"║  Timestamp: {datetime.now().isoformat():<54} ║")
    print("╠" + "═" * 68 + "╣")
    print("║  SCOPE                                                             ║")
    print(f"║    Source outreach_ids scanned: {preflight_data['total_source_outreach_ids']:>32,} ║")
    print(f"║    Slot types processed: CEO, CFO, HR                             ║")
    print("╠" + "═" * 68 + "╣")
    print("║  RESULTS BY SLOT TYPE                                              ║")
    for slot_type, data in seed_results.items():
        print(f"║    {slot_type}: {data['inserted']:>10,} inserted, {data['skipped']:>10,} skipped      ║")
    print("╠" + "═" * 68 + "╣")
    print("║  TOTALS                                                            ║")
    print(f"║    Total slots inserted: {total_inserted:>40,} ║")
    print(f"║    Total slots skipped (pre-existed): {total_skipped:>27,} ║")
    print(f"║    Unique outreach_ids with slots: {validation['unique_outreach_ids']:>30,} ║")
    print("╠" + "═" * 68 + "╣")
    print("║  ZERO-TOUCH CONFIRMATIONS                                          ║")
    master_status = "✓ CONFIRMED" if validation['people_master_delta'] == 0 else "❌ VIOLATED"
    candidate_status = "✓ CONFIRMED" if validation['people_candidate_delta'] == 0 else "❌ VIOLATED"
    switch_status = "✓ UNCHANGED" if not validation['kill_switch_enabled'] else "❌ MODIFIED"
    print(f"║    people.people_master touched: 0 {master_status:>29} ║")
    print(f"║    people.people_candidate touched: 0 {candidate_status:>26} ║")
    print(f"║    slot_ingress_control modified: NO {switch_status:>26} ║")
    print("╠" + "═" * 68 + "╣")
    print("║  POST-EXECUTION SLOT COUNTS                                        ║")
    for slot_type, count in validation['slot_counts'].items():
        print(f"║    {slot_type}: {count:>56,} ║")
    print("╠" + "═" * 68 + "╣")
    print("║  STATUS: COMPLETE — STRUCTURE ONLY                                 ║")
    print("║  INGRESS: DISABLED (kill switch OFF)                               ║")
    print("║  NEXT: DO NOT PROCEED TO PEOPLE INGESTION                          ║")
    print("╚" + "═" * 68 + "╝")


def main():
    """Main execution flow."""
    print("\n" + "═" * 70)
    print("  PEOPLE SLOT BULK SEED — STRUCTURE ONLY")
    print("  Target: ALL outreach_ids from outreach.company_target")
    print("  Slot types: CEO, CFO, HR")
    print("═" * 70)
    
    slot_types = ['CEO', 'CFO', 'HR']
    
    conn = None
    try:
        conn = get_connection()
        cur = conn.cursor(cursor_factory=RealDictCursor)
        
        # Phase 1: Preflight checks
        preflight_data = preflight_checks(cur)
        if not preflight_data:
            print("\n❌ ABORTING: Preflight checks failed")
            return 1
        
        # Phase 2: Execute bulk seed
        seed_results, total_inserted, total_skipped = execute_bulk_seed(cur, slot_types)
        
        # Phase 3: Run validation queries
        validation = run_validation_queries(cur, preflight_data)
        
        # Verify no violations before commit
        if (validation['people_master_delta'] != 0 or 
            validation['people_candidate_delta'] != 0 or
            validation['kill_switch_enabled']):
            print("\n❌ ROLLING BACK: Safety violations detected")
            conn.rollback()
            return 1
        
        # Commit transaction
        conn.commit()
        print("\n✅ Transaction COMMITTED")
        
        # Phase 4: Generate report
        generate_report(preflight_data, seed_results, total_inserted, total_skipped, validation)
        
        return 0
        
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        if conn:
            conn.rollback()
            print("Transaction ROLLED BACK")
        raise
    finally:
        if conn:
            conn.close()


if __name__ == "__main__":
    sys.exit(main())
