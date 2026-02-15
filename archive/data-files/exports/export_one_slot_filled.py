#!/usr/bin/env python3
"""
Export companies with exactly 1 slot filled and generate breakdown statistics.
"""

import os
import sys
import csv
import psycopg2
from psycopg2.extras import RealDictCursor

# Set UTF-8 encoding for Windows console output
if sys.platform == 'win32':
    import codecs
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')

def get_db_connection():
    """Create database connection using environment variables."""
    return psycopg2.connect(
        host=os.environ['NEON_HOST'],
        database=os.environ['NEON_DATABASE'],
        user=os.environ['NEON_USER'],
        password=os.environ['NEON_PASSWORD'],
        sslmode='require'
    )

def export_companies_one_slot_filled():
    """Export companies with exactly 1 slot filled to CSV."""

    query = """
    SELECT
        o.outreach_id,
        o.domain,
        ci.company_name,
        cs.filled_count,
        cs.ceo_filled,
        cs.cfo_filled,
        cs.hr_filled
    FROM outreach.outreach o
    LEFT JOIN cl.company_identity ci ON o.sovereign_id = ci.company_unique_id
    JOIN (
        SELECT
            outreach_id,
            COUNT(*) FILTER (WHERE is_filled) AS filled_count,
            MAX(CASE WHEN slot_type = 'CEO' AND is_filled THEN 1 ELSE 0 END) AS ceo_filled,
            MAX(CASE WHEN slot_type = 'CFO' AND is_filled THEN 1 ELSE 0 END) AS cfo_filled,
            MAX(CASE WHEN slot_type = 'HR' AND is_filled THEN 1 ELSE 0 END) AS hr_filled
        FROM people.company_slot
        GROUP BY outreach_id
        HAVING COUNT(*) FILTER (WHERE is_filled) = 1
    ) cs ON o.outreach_id = cs.outreach_id
    ORDER BY o.domain;
    """

    conn = get_db_connection()
    cursor = conn.cursor(cursor_factory=RealDictCursor)

    try:
        cursor.execute(query)
        rows = cursor.fetchall()

        # Write to CSV
        csv_path = r'C:\Users\CUSTOM PC\Desktop\Cursor Builds\barton-outreach-core\exports\companies_one_slot_filled.csv'
        with open(csv_path, 'w', newline='', encoding='utf-8') as csvfile:
            if rows:
                fieldnames = rows[0].keys()
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(rows)

        print(f"\n[OK] Exported {len(rows)} companies to: {csv_path}")
        return len(rows)

    finally:
        cursor.close()
        conn.close()

def get_slot_breakdown():
    """Get count and breakdown of which slot is typically filled."""

    query = """
    SELECT
        'Total Companies with 1 Slot Filled' AS metric,
        COUNT(*) AS count
    FROM (
        SELECT outreach_id
        FROM people.company_slot
        GROUP BY outreach_id
        HAVING COUNT(*) FILTER (WHERE is_filled) = 1
    ) subq

    UNION ALL

    SELECT
        'CEO Only Filled' AS metric,
        COUNT(*) AS count
    FROM (
        SELECT outreach_id
        FROM people.company_slot
        GROUP BY outreach_id
        HAVING COUNT(*) FILTER (WHERE is_filled) = 1
           AND MAX(CASE WHEN slot_type = 'CEO' AND is_filled THEN 1 ELSE 0 END) = 1
    ) subq

    UNION ALL

    SELECT
        'CFO Only Filled' AS metric,
        COUNT(*) AS count
    FROM (
        SELECT outreach_id
        FROM people.company_slot
        GROUP BY outreach_id
        HAVING COUNT(*) FILTER (WHERE is_filled) = 1
           AND MAX(CASE WHEN slot_type = 'CFO' AND is_filled THEN 1 ELSE 0 END) = 1
    ) subq

    UNION ALL

    SELECT
        'HR Only Filled' AS metric,
        COUNT(*) AS count
    FROM (
        SELECT outreach_id
        FROM people.company_slot
        GROUP BY outreach_id
        HAVING COUNT(*) FILTER (WHERE is_filled) = 1
           AND MAX(CASE WHEN slot_type = 'HR' AND is_filled THEN 1 ELSE 0 END) = 1
    ) subq;
    """

    conn = get_db_connection()
    cursor = conn.cursor(cursor_factory=RealDictCursor)

    try:
        cursor.execute(query)
        rows = cursor.fetchall()

        print("\n" + "="*60)
        print("SLOT FILL BREAKDOWN - Companies with Exactly 1 Slot Filled")
        print("="*60)

        total = 0
        breakdown = {}

        for row in rows:
            metric = row['metric']
            count = row['count']

            if metric == 'Total Companies with 1 Slot Filled':
                total = count
                print(f"\n{metric}: {count:,}")
            else:
                breakdown[metric] = count

        if total > 0:
            print("\nBreakdown by Slot Type:")
            print("-" * 60)
            for metric, count in breakdown.items():
                pct = (count / total * 100) if total > 0 else 0
                print(f"  {metric}: {count:,} ({pct:.1f}%)")

        print("="*60 + "\n")

    finally:
        cursor.close()
        conn.close()

if __name__ == '__main__':
    print("\nExecuting Companies with 1 Slot Filled Export...")
    print("-" * 60)

    # Export to CSV
    total_exported = export_companies_one_slot_filled()

    # Get breakdown statistics
    get_slot_breakdown()

    print(f"[OK] Complete! {total_exported:,} companies exported.")
