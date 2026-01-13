#!/usr/bin/env python3
"""
People Slot Canary Seed Executor
================================
Executes the canary slot seeding migration with full observability.

SCOPE:
- 100 outreach_ids (canary set)
- 3 slot types: CEO, CFO, HR
- INSERT IF MISSING ONLY

PROHIBITIONS ENFORCED:
- NO writes to people.people_master
- NO writes to people.people_candidate
- NO kill switch changes
- NO updates to existing rows
"""

import os
import uuid
import psycopg2
from psycopg2.extras import RealDictCursor

def execute_canary_seed():
    """Execute the canary slot seeding with observability."""
    
    database_url = os.environ.get('DATABASE_URL')
    if not database_url:
        print("ERROR: DATABASE_URL not set")
        return
    
    conn = psycopg2.connect(database_url)
    conn.autocommit = False
    
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            print("═" * 65)
            print("  PEOPLE SLOT CANARY SEED — PASS 0")
            print("═" * 65)
            
            # PHASE 1: Select canary outreach_ids from existing slots
            # Use outreach_ids that already have at least one slot (with valid company_unique_id)
            # This ensures FK constraint is satisfied
            cur.execute("""
                SELECT DISTINCT cs.outreach_id, cs.company_unique_id
                FROM people.company_slot cs
                WHERE cs.outreach_id IS NOT NULL
                  AND cs.company_unique_id IS NOT NULL
                ORDER BY cs.outreach_id
                LIMIT 100
            """)
            canary_records = cur.fetchall()
            print(f"  CANARY SIZE: {len(canary_records)} outreach_ids selected")
            print(f"  SLOT TYPES: CEO, CFO, HR")
            print(f"  MODE: INSERT IF MISSING ONLY")
            print("═" * 65)
            
            if len(canary_records) == 0:
                print("  ERROR: No outreach_ids with company_unique_id found. Aborting.")
                conn.rollback()
                return
            
            # Track metrics
            slots_created = {'CEO': 0, 'CFO': 0, 'HR': 0}
            slots_skipped = {'CEO': 0, 'CFO': 0, 'HR': 0}
            
            # PHASE 2-4: Seed slots for each type
            for slot_type in ['CEO', 'CFO', 'HR']:
                for record in canary_records:
                    outreach_id = record['outreach_id']
                    company_unique_id = record['company_unique_id']
                    
                    # Check if slot exists
                    cur.execute("""
                        SELECT 1 FROM people.company_slot
                        WHERE outreach_id = %s AND slot_type = %s
                    """, (outreach_id, slot_type))
                    
                    if cur.fetchone():
                        slots_skipped[slot_type] += 1
                    else:
                        # Generate unique ID for slot
                        slot_unique_id = str(uuid.uuid4())
                        
                        # Insert new slot with all required fields
                        cur.execute("""
                            INSERT INTO people.company_slot (
                                company_slot_unique_id,
                                company_unique_id,
                                outreach_id, 
                                slot_type, 
                                slot_status,
                                status,
                                is_filled,
                                canonical_flag, 
                                creation_reason, 
                                created_at
                            )
                            VALUES (%s, %s, %s, %s, 'open', 'open', FALSE, TRUE, 'bootstrap', NOW())
                            ON CONFLICT (outreach_id, slot_type) DO NOTHING
                        """, (slot_unique_id, company_unique_id, outreach_id, slot_type))
                        
                        if cur.rowcount > 0:
                            slots_created[slot_type] += 1
                        else:
                            slots_skipped[slot_type] += 1
            
            # Calculate totals
            total_inserted = sum(slots_created.values())
            total_skipped = sum(slots_skipped.values())
            
            # OBSERVABILITY REPORT
            print()
            print("═" * 65)
            print("  PEOPLE SLOT CANARY SEED — OBSERVABILITY REPORT")
            print("═" * 65)
            print()
            print("  CANARY SCOPE:")
            print(f"    outreach_ids processed: {len(canary_records)}")
            print()
            print("  SLOTS CREATED (by type):")
            print(f"    CEO slots created:  {slots_created['CEO']}")
            print(f"    CFO slots created:  {slots_created['CFO']}")
            print(f"    HR  slots created:  {slots_created['HR']}")
            print("    " + "─" * 21)
            print(f"    TOTAL INSERTED:     {total_inserted}")
            print()
            print("  SLOTS SKIPPED (already existed):")
            print(f"    CEO slots skipped:  {slots_skipped['CEO']}")
            print(f"    CFO slots skipped:  {slots_skipped['CFO']}")
            print(f"    HR  slots skipped:  {slots_skipped['HR']}")
            print("    " + "─" * 21)
            print(f"    TOTAL SKIPPED:      {total_skipped}")
            print()
            print("  SAFETY CONFIRMATION:")
            print("    people.people_master touched: 0 (ZERO)")
            print("    people.people_candidate touched: 0 (ZERO)")
            print("    slot_ingress_control modified: NO")
            print("    Enrichment calls made: 0")
            print("    Resolution logic triggered: NO")
            print()
            print("  CANARY SAMPLE (first 10 outreach_ids):")
            sample = [str(r['outreach_id']) for r in canary_records[:10]]
            print(f"    {', '.join(sample)}")
            print()
            
            # Commit transaction
            conn.commit()
            print("  STATUS: CANARY SEED COMPLETE")
            print("  INGRESS: REMAINS DISABLED (no switch change)")
            print("═" * 65)
            
    except Exception as e:
        conn.rollback()
        print(f"  ERROR: {e}")
        print("  STATUS: ROLLED BACK — NO CHANGES PERSISTED")
        raise
    finally:
        conn.close()


if __name__ == '__main__':
    execute_canary_seed()
