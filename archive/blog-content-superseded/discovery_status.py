#!/usr/bin/env python3
"""
URL Discovery Status Monitor
=============================
Quick status check for the company URL discovery process.

Usage:
    doppler run -- python discovery_status.py
"""

import psycopg2
from psycopg2.extras import RealDictCursor
import sys
import os

NEON_CONFIG = {
    'host': os.environ.get('NEON_HOST', 'ep-ancient-waterfall-a42vy0du-pooler.us-east-1.aws.neon.tech'),
    'port': 5432,
    'database': 'Marketing DB',
    'user': 'Marketing DB_owner',
    'password': os.environ.get('NEON_PASSWORD', 'npg_OsE4Z2oPCpiT'),
    'sslmode': 'require'
}

def check_status():
    if sys.platform == 'win32':
        sys.stdout.reconfigure(encoding='utf-8')

    conn = psycopg2.connect(**NEON_CONFIG)
    cur = conn.cursor(cursor_factory=RealDictCursor)

    print('=' * 60)
    print('URL DISCOVERY STATUS')
    print('=' * 60)
    print()

    # Total companies with websites
    cur.execute('''
        SELECT COUNT(*) as total
        FROM company.company_master
        WHERE website_url IS NOT NULL
    ''')
    total_with_website = cur.fetchone()['total']

    # Companies processed (have URLs discovered)
    cur.execute('''
        SELECT COUNT(DISTINCT company_unique_id) as processed
        FROM company.company_source_urls
    ''')
    processed = cur.fetchone()['processed']

    # Total URLs discovered
    cur.execute('SELECT COUNT(*) as total FROM company.company_source_urls')
    total_urls = cur.fetchone()['total']

    # By state
    cur.execute('''
        SELECT
            cm.address_state,
            COUNT(DISTINCT cm.company_unique_id) as total_companies,
            COUNT(DISTINCT csu.company_unique_id) as processed_companies
        FROM company.company_master cm
        LEFT JOIN company.company_source_urls csu
            ON cm.company_unique_id = csu.company_unique_id
        WHERE cm.website_url IS NOT NULL
        GROUP BY cm.address_state
        ORDER BY total_companies DESC
    ''')
    by_state = cur.fetchall()

    # By source type
    cur.execute('''
        SELECT source_type, COUNT(*) as count
        FROM company.company_source_urls
        GROUP BY source_type
        ORDER BY count DESC
    ''')
    by_type = cur.fetchall()

    # Recent discoveries
    cur.execute('''
        SELECT
            cm.company_name,
            csu.source_type,
            csu.discovered_at
        FROM company.company_source_urls csu
        JOIN company.company_master cm
            ON csu.company_unique_id = cm.company_unique_id
        ORDER BY csu.discovered_at DESC
        LIMIT 5
    ''')
    recent = cur.fetchall()

    # Print results
    pct = 100 * processed / total_with_website if total_with_website > 0 else 0
    print(f"PROGRESS:")
    print(f"  Companies with websites: {total_with_website:,}")
    print(f"  Companies processed:     {processed:,}")
    print(f"  Progress:                {pct:.1f}%")
    print(f"  Total URLs discovered:   {total_urls:,}")
    print(f"  Avg URLs per company:    {total_urls/processed:.1f}" if processed > 0 else "")
    print()

    print("BY STATE:")
    print("-" * 40)
    for row in by_state:
        state_pct = 100 * row['processed_companies'] / row['total_companies'] if row['total_companies'] > 0 else 0
        bar = '█' * int(state_pct / 5) + '░' * (20 - int(state_pct / 5))
        print(f"  {row['address_state']}: {row['processed_companies']:,}/{row['total_companies']:,} [{bar}] {state_pct:.0f}%")
    print()

    print("BY SOURCE TYPE:")
    print("-" * 40)
    for row in by_type:
        print(f"  {row['source_type']}: {row['count']:,}")
    print()

    print("RECENT DISCOVERIES:")
    print("-" * 40)
    for row in recent:
        print(f"  {row['company_name'][:35]}")
        print(f"    → {row['source_type']} at {row['discovered_at'].strftime('%H:%M:%S')}")

    cur.close()
    conn.close()


if __name__ == '__main__':
    check_status()
