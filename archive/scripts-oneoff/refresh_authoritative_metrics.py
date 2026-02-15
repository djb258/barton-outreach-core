#!/usr/bin/env python3
"""
Refresh Authoritative Table Metrics

Updates the AUTHORITATIVE_TABLE_REFERENCE.md with current database counts.
Run this periodically to keep documentation in sync with actual data.

Usage:
    doppler run -- python scripts/refresh_authoritative_metrics.py
"""

import os
import psycopg2
from datetime import datetime

def get_metrics():
    """Query database for current metrics."""
    conn = psycopg2.connect(os.environ['DATABASE_URL'])
    cur = conn.cursor()
    
    metrics = {}
    
    # Total companies (authoritative)
    cur.execute('SELECT COUNT(*) FROM outreach.company_target')
    metrics['total_companies'] = cur.fetchone()[0]
    
    # Companies with filled slots
    cur.execute('''
        SELECT COUNT(DISTINCT ct.outreach_id)
        FROM outreach.company_target ct
        JOIN people.company_slot cs ON ct.outreach_id = cs.outreach_id
        WHERE cs.is_filled = true
    ''')
    metrics['companies_with_slots'] = cur.fetchone()[0]
    
    # Companies with email
    cur.execute('''
        SELECT COUNT(DISTINCT ct.outreach_id)
        FROM outreach.company_target ct
        JOIN people.company_slot cs ON ct.outreach_id = cs.outreach_id
        JOIN people.people_master pm ON cs.person_unique_id = pm.unique_id
        WHERE cs.is_filled = true AND pm.email IS NOT NULL
    ''')
    metrics['companies_with_email'] = cur.fetchone()[0]
    
    # Slot coverage by type
    for slot_type in ['CEO', 'CFO', 'HR']:
        cur.execute('''
            SELECT 
                COUNT(*) FILTER (WHERE cs.is_filled) as filled,
                COUNT(DISTINCT pm.unique_id) FILTER (WHERE pm.email IS NOT NULL) as has_email,
                COUNT(*) FILTER (WHERE NOT cs.is_filled OR cs.is_filled IS NULL) as empty
            FROM people.company_slot cs
            JOIN outreach.company_target ct ON cs.outreach_id = ct.outreach_id
            LEFT JOIN people.people_master pm ON cs.person_unique_id = pm.unique_id
            WHERE cs.slot_type = %s
        ''', (slot_type,))
        row = cur.fetchone()
        metrics[f'{slot_type.lower()}_filled'] = row[0]
        metrics[f'{slot_type.lower()}_email'] = row[1]
        metrics[f'{slot_type.lower()}_empty'] = row[2]
    
    # People needing email
    cur.execute('''
        SELECT COUNT(DISTINCT pm.unique_id)
        FROM people.people_master pm
        JOIN people.company_slot cs ON pm.unique_id = cs.person_unique_id
        JOIN outreach.company_target ct ON cs.outreach_id = ct.outreach_id
        WHERE cs.is_filled = true AND pm.email IS NULL
    ''')
    metrics['people_need_email'] = cur.fetchone()[0]
    
    # Source breakdown
    cur.execute('''
        SELECT 
            COALESCE(cs.source_system, 'unknown') as source,
            COUNT(*) as filled_slots
        FROM people.company_slot cs
        JOIN outreach.company_target ct ON cs.outreach_id = ct.outreach_id
        WHERE cs.is_filled = true
        GROUP BY cs.source_system
        ORDER BY filled_slots DESC
        LIMIT 7
    ''')
    metrics['sources'] = cur.fetchall()
    
    conn.close()
    return metrics

def print_report(metrics):
    """Print metrics report."""
    total = metrics['total_companies']
    
    print(f"\n{'='*60}")
    print(f"AUTHORITATIVE TABLE METRICS - {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print(f"{'='*60}")
    print(f"\nSource: outreach.company_target")
    print(f"Total Companies: {total:,}")
    
    print(f"\n--- Company Coverage ---")
    print(f"Companies with ≥1 filled slot: {metrics['companies_with_slots']:,} ({100*metrics['companies_with_slots']/total:.1f}%)")
    print(f"Companies with ≥1 email: {metrics['companies_with_email']:,} ({100*metrics['companies_with_email']/total:.1f}%)")
    print(f"Companies needing people: {total - metrics['companies_with_slots']:,} ({100*(total - metrics['companies_with_slots'])/total:.1f}%)")
    
    print(f"\n--- Slot Coverage ---")
    print(f"{'Slot':<6} {'Filled':>10} {'Has Email':>12} {'Empty':>10} {'% Filled':>10}")
    for slot in ['CEO', 'CFO', 'HR']:
        filled = metrics[f'{slot.lower()}_filled']
        email = metrics[f'{slot.lower()}_email']
        empty = metrics[f'{slot.lower()}_empty']
        pct = 100 * filled / total if total > 0 else 0
        print(f"{slot:<6} {filled:>10,} {email:>12,} {empty:>10,} {pct:>9.1f}%")
    
    print(f"\n--- Enrichment Needed ---")
    print(f"People needing email: {metrics['people_need_email']:,}")
    
    print(f"\n--- Sources ---")
    for source, count in metrics['sources']:
        print(f"  {source}: {count:,}")
    
    print(f"\n{'='*60}")

if __name__ == '__main__':
    metrics = get_metrics()
    print_report(metrics)
