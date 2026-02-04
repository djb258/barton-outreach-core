"""
Sync appointments with outreach table.

Run this after importing new appointments to:
1. Link appointments to outreach records (set outreach_id)
2. Flag outreach records as warm leads (has_appointment = TRUE)

Usage:
    python scripts/sync_appointments.py
"""

import psycopg2
import os
from dotenv import load_dotenv

load_dotenv()


def sync_appointments():
    """Sync appointments table with outreach table."""
    conn = psycopg2.connect(os.environ['DATABASE_URL'])
    cur = conn.cursor()
    
    print("=== SYNCING APPOINTMENTS WITH OUTREACH ===\n")
    
    # 1. Link appointments to outreach records where domain matches
    cur.execute("""
        UPDATE outreach.appointments a
        SET outreach_id = o.outreach_id,
            updated_at = NOW()
        FROM outreach.outreach o
        WHERE LOWER(a.domain) = LOWER(o.domain)
        AND a.outreach_id IS NULL
    """)
    linked = cur.rowcount
    print(f"✓ Linked {linked} appointments to outreach records")
    
    # 2. Flag outreach records as warm (has_appointment = TRUE)
    cur.execute("""
        UPDATE outreach.outreach o
        SET has_appointment = TRUE
        FROM outreach.appointments a
        WHERE LOWER(o.domain) = LOWER(a.domain)
        AND (o.has_appointment = FALSE OR o.has_appointment IS NULL)
    """)
    flagged = cur.rowcount
    print(f"✓ Flagged {flagged} outreach records as warm leads")
    
    conn.commit()
    
    # Summary stats
    print("\n=== CURRENT STATUS ===")
    
    cur.execute("SELECT COUNT(*) FROM outreach.appointments")
    total_appts = cur.fetchone()[0]
    
    cur.execute("SELECT COUNT(*) FROM outreach.appointments WHERE outreach_id IS NOT NULL")
    linked_appts = cur.fetchone()[0]
    
    cur.execute("SELECT COUNT(*) FROM outreach.outreach WHERE has_appointment = TRUE")
    warm_leads = cur.fetchone()[0]
    
    cur.execute("SELECT COUNT(*) FROM outreach.outreach WHERE has_appointment = FALSE OR has_appointment IS NULL")
    cold_leads = cur.fetchone()[0]
    
    print(f"Total appointments: {total_appts}")
    print(f"  - Linked to outreach: {linked_appts}")
    print(f"  - Not in outreach yet: {total_appts - linked_appts}")
    print(f"")
    print(f"Outreach records:")
    print(f"  - WARM (has_appointment=TRUE): {warm_leads}")
    print(f"  - COLD (has_appointment=FALSE): {cold_leads}")
    
    conn.close()
    print("\n✓ Sync complete!")


if __name__ == "__main__":
    sync_appointments()
