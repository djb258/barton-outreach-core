#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Assign message keys to all verified contacts based on their role.
This schedules them for sending via n8n → Instantly/HeyReach.

CTB Classification Metadata:
CTB Branch: sys/tools
Barton ID: 08.04.01
Unique ID: CTB-ASSIGNMSG
Enforcement: ORBT
"""

import os
import sys
import psycopg2
from psycopg2.extras import RealDictCursor

# Set UTF-8 encoding for Windows console
if sys.platform == 'win32':
    import codecs
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')

def assign_messages():
    """Assign message keys to all verified contacts."""
    
    database_url = os.getenv('NEON_DATABASE_URL')
    
    if not database_url:
        print("[ERROR] NEON_DATABASE_URL not set")
        return
    
    print("\n" + "="*100)
    print("ASSIGN MESSAGES TO CONTACTS")
    print("="*100 + "\n")
    
    try:
        conn = psycopg2.connect(database_url)
        cur = conn.cursor(cursor_factory=RealDictCursor)
        
        # Check current status
        print("[1/4] Checking current message assignments...")
        
        cur.execute("""
            SELECT 
                cs.slot_type,
                COUNT(*) as total,
                COUNT(pm.message_key_scheduled) as already_assigned
            FROM marketing.people_master pm
            JOIN marketing.company_slots cs ON pm.company_slot_unique_id = cs.company_slot_unique_id
            GROUP BY cs.slot_type
            ORDER BY cs.slot_type
        """)
        
        status = cur.fetchall()
        
        print("\nCurrent Status:")
        for s in status:
            print(f"  {s['slot_type']}: {s['already_assigned']}/{s['total']} have messages assigned")
        print()
        
        # Assign messages
        print("[2/4] Assigning message keys by role...")
        
        cur.execute("""
            UPDATE marketing.people_master pm
            SET message_key_scheduled = CASE cs.slot_type
                WHEN 'CEO' THEN 'MSG.CEO.001.A'
                WHEN 'CFO' THEN 'MSG.CFO.005.A'
                WHEN 'HR' THEN 'MSG.HR.001.B'
                ELSE NULL
            END
            FROM marketing.company_slots cs
            WHERE pm.company_slot_unique_id = cs.company_slot_unique_id
              AND pm.email_verified = TRUE
              AND pm.message_key_scheduled IS NULL
        """)
        
        assigned = cur.rowcount
        conn.commit()
        
        print(f"[OK] Assigned messages to {assigned} contacts")
        print()
        
        # Show assignments
        print("[3/4] Verifying assignments...")
        
        cur.execute("""
            SELECT 
                cs.slot_type,
                pm.message_key_scheduled,
                COUNT(*) as count
            FROM marketing.people_master pm
            JOIN marketing.company_slots cs ON pm.company_slot_unique_id = cs.company_slot_unique_id
            WHERE pm.message_key_scheduled IS NOT NULL
            GROUP BY cs.slot_type, pm.message_key_scheduled
            ORDER BY cs.slot_type
        """)
        
        assignments = cur.fetchall()
        
        print("\nMessage Assignments:")
        total_assigned = 0
        for a in assignments:
            print(f"  {a['slot_type']}: {a['count']} contacts → {a['message_key_scheduled']}")
            total_assigned += a['count']
        
        print(f"\nTotal ready to send: {total_assigned}")
        print()
        
        # Show sample contacts
        print("[4/4] Sample contacts ready to send...")
        
        cur.execute("""
            SELECT 
                pm.full_name,
                pm.email,
                cm.company_name,
                cs.slot_type,
                pm.message_key_scheduled,
                mkr.subject_line,
                mkr.message_channel
            FROM marketing.people_master pm
            JOIN marketing.company_master cm ON pm.company_unique_id = cm.company_unique_id
            JOIN marketing.company_slots cs ON pm.company_slot_unique_id = cs.company_slot_unique_id
            JOIN marketing.message_key_reference mkr ON pm.message_key_scheduled = mkr.message_key
            LIMIT 5
        """)
        
        samples = cur.fetchall()
        
        print("\nFirst 5 contacts queued:")
        print("-"*100)
        for s in samples:
            print(f"{s['full_name']} ({s['slot_type']}) - {s['company_name']}")
            print(f"  Email: {s['email']}")
            print(f"  Channel: {s['message_channel']}")
            print(f"  Subject: {s['subject_line']}")
            print()
        
        print("="*100)
        print("MESSAGES ASSIGNED AND READY!")
        print("="*100)
        print(f"  Total contacts scheduled: {total_assigned}")
        print(f"  Status: READY FOR n8n TO SEND")
        print()
        print("Next steps:")
        print("  1. Make sure n8n workflows are ACTIVE in your hosted account")
        print("  2. n8n will automatically send within 15-20 minutes")
        print("  3. Monitor sends in n8n Executions tab")
        print("  4. Check Instantly and HeyReach for campaign activity")
        print("="*100 + "\n")
        
        cur.close()
        conn.close()
        
    except Exception as e:
        print(f"\n[ERROR] {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    assign_messages()

