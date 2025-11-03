#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Check status of message sending from n8n workflows.
Shows what's scheduled, what's been sent, and any signals tracked.
"""

import os
import sys
import psycopg2
from psycopg2.extras import RealDictCursor

# Set UTF-8 encoding for Windows console
if sys.platform == 'win32':
    import codecs
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')

def check_status():
    """Check message sending status."""
    
    database_url = os.getenv('NEON_DATABASE_URL')
    
    if not database_url:
        print("[ERROR] NEON_DATABASE_URL not set")
        return
    
    try:
        conn = psycopg2.connect(database_url)
        cur = conn.cursor(cursor_factory=RealDictCursor)
        
        print("\n" + "="*100)
        print("MESSAGE SENDING STATUS")
        print("="*100 + "\n")
        
        # Scheduled messages
        print("[1/4] Messages Scheduled (pending send):")
        print("-"*100)
        
        cur.execute("""
            SELECT 
                cs.slot_type,
                COUNT(*) as count
            FROM marketing.people_master pm
            JOIN marketing.company_slots cs ON pm.company_slot_unique_id = cs.company_slot_unique_id
            WHERE pm.message_key_scheduled IS NOT NULL
            GROUP BY cs.slot_type
            ORDER BY cs.slot_type
        """)
        
        scheduled = cur.fetchall()
        total_scheduled = 0
        
        if scheduled:
            for s in scheduled:
                print(f"  {s['slot_type']}: {s['count']} contacts waiting to send")
                total_scheduled += s['count']
            print(f"\nTotal scheduled: {total_scheduled}")
        else:
            print("  No messages currently scheduled")
        
        print()
        
        # Sent messages
        print("[2/4] Messages Sent (from pipeline events):")
        print("-"*100)
        
        cur.execute("""
            SELECT 
                payload->>'channel' as channel,
                COUNT(*) as count,
                MAX(created_at) as last_sent
            FROM marketing.pipeline_events
            WHERE event_type = 'message_sent'
            GROUP BY payload->>'channel'
            ORDER BY COUNT(*) DESC
        """)
        
        sent = cur.fetchall()
        total_sent = 0
        
        if sent:
            for s in sent:
                print(f"  {s['channel']}: {s['count']} sent (last: {s['last_sent']})")
                total_sent += s['count']
            print(f"\nTotal sent: {total_sent}")
        else:
            print("  No messages sent yet (n8n workflows not running or just started)")
        
        print()
        
        # BIT signals
        print("[3/4] Engagement Signals (BIT tracking):")
        print("-"*100)
        
        cur.execute("""
            SELECT 
                signal_type,
                source,
                COUNT(*) as count,
                MAX(captured_at) as last_signal
            FROM bit.bit_signal
            GROUP BY signal_type, source
            ORDER BY COUNT(*) DESC
        """)
        
        signals = cur.fetchall()
        total_signals = 0
        
        if signals:
            for sig in signals:
                print(f"  {sig['signal_type']} ({sig['source']}): {sig['count']} signals")
                total_signals += sig['count']
            print(f"\nTotal signals: {total_signals}")
        else:
            print("  No signals tracked yet")
        
        print()
        
        # Recent activity
        print("[4/4] Recent Activity (last 10 events):")
        print("-"*100)
        
        cur.execute("""
            SELECT 
                event_type,
                payload->>'contact_id' as contact_id,
                payload->>'message_key' as message_key,
                payload->>'channel' as channel,
                created_at
            FROM marketing.pipeline_events
            WHERE event_type IN ('message_sent', 'message_failed')
            ORDER BY created_at DESC
            LIMIT 10
        """)
        
        recent = cur.fetchall()
        
        if recent:
            for r in recent:
                print(f"  [{r['created_at']}] {r['event_type']}")
                print(f"    Contact: {r['contact_id']}")
                print(f"    Message: {r['message_key']} via {r['channel']}")
        else:
            print("  No message activity yet")
        
        print()
        print("="*100)
        print("SUMMARY")
        print("="*100)
        print(f"  Scheduled (waiting): {total_scheduled}")
        print(f"  Sent (completed): {total_sent}")
        print(f"  Signals tracked: {total_signals}")
        print(f"  Status: {'ACTIVE' if total_sent > 0 or total_scheduled > 0 else 'IDLE'}")
        print("="*100 + "\n")
        
        cur.close()
        conn.close()
        
    except Exception as e:
        print(f"\n[ERROR] {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    check_status()

