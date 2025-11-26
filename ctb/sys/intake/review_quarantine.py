#!/usr/bin/env python3
"""
PLE Quarantine Review & Cleanup

Manage quarantined records from intake validation.
"""

import json
import os
from datetime import datetime, timedelta
from typing import Dict, List, Any
import psycopg2
from psycopg2.extras import RealDictCursor
from dotenv import load_dotenv

load_dotenv()

CONNECTION_STRING = os.getenv('NEON_CONNECTION_STRING') or os.getenv('DATABASE_URL')


def get_quarantine_stats(db_connection) -> Dict[str, Any]:
    """Get summary statistics of quarantined records."""
    cursor = db_connection.cursor(cursor_factory=RealDictCursor)

    # Total unresolved
    cursor.execute("""
        SELECT
            record_type,
            COUNT(*) as count,
            MIN(quarantined_at) as oldest,
            MAX(quarantined_at) as newest
        FROM marketing.intake_quarantine
        WHERE resolved_at IS NULL
        GROUP BY record_type
    """)
    unresolved = cursor.fetchall()

    # Total resolved
    cursor.execute("""
        SELECT
            record_type,
            resolution_action,
            COUNT(*) as count
        FROM marketing.intake_quarantine
        WHERE resolved_at IS NOT NULL
        GROUP BY record_type, resolution_action
    """)
    resolved = cursor.fetchall()

    # Most common errors
    cursor.execute("""
        SELECT
            jsonb_array_elements_text(validation_errors) as error,
            COUNT(*) as count
        FROM marketing.intake_quarantine
        WHERE resolved_at IS NULL
        GROUP BY error
        ORDER BY count DESC
        LIMIT 10
    """)
    common_errors = cursor.fetchall()

    return {
        'unresolved': unresolved,
        'resolved': resolved,
        'common_errors': common_errors
    }


def list_quarantined_records(db_connection, record_type: str = None, limit: int = 50) -> List[Dict[str, Any]]:
    """List quarantined records."""
    cursor = db_connection.cursor(cursor_factory=RealDictCursor)

    query = """
        SELECT
            id,
            record_type,
            raw_payload,
            validation_errors,
            source,
            quarantined_at
        FROM marketing.intake_quarantine
        WHERE resolved_at IS NULL
    """

    params = []
    if record_type:
        query += " AND record_type = %s"
        params.append(record_type)

    query += " ORDER BY quarantined_at DESC LIMIT %s"
    params.append(limit)

    cursor.execute(query, params)
    return cursor.fetchall()


def resolve_quarantined_record(db_connection, quarantine_id: int, action: str, notes: str = None):
    """
    Mark a quarantined record as resolved.

    Args:
        quarantine_id: ID from intake_quarantine table
        action: 'fixed' (manually fixed and inserted), 'rejected' (permanently rejected), 'merged' (duplicate merged)
        notes: Optional resolution notes
    """
    cursor = db_connection.cursor()
    cursor.execute("""
        UPDATE marketing.intake_quarantine
        SET
            resolved_at = NOW(),
            resolution_action = %s
        WHERE id = %s
    """, (action, quarantine_id))
    db_connection.commit()


def cleanup_old_resolved(db_connection, days: int = 90):
    """Delete resolved records older than X days."""
    cursor = db_connection.cursor()
    cursor.execute("""
        DELETE FROM marketing.intake_quarantine
        WHERE resolved_at IS NOT NULL
        AND resolved_at < NOW() - INTERVAL '%s days'
        RETURNING id
    """, (days,))

    deleted = cursor.rowcount
    db_connection.commit()
    return deleted


def export_quarantine_to_json(db_connection, output_file: str, record_type: str = None):
    """Export quarantined records to JSON for manual review."""
    records = list_quarantined_records(db_connection, record_type, limit=10000)

    # Convert to JSON-serializable format
    export_data = []
    for record in records:
        export_data.append({
            'quarantine_id': record['id'],
            'record_type': record['record_type'],
            'source': record['source'],
            'quarantined_at': record['quarantined_at'].isoformat(),
            'errors': record['validation_errors'],
            'data': record['raw_payload']
        })

    with open(output_file, 'w') as f:
        json.dump(export_data, f, indent=2)

    return len(export_data)


def print_quarantine_stats(stats: Dict[str, Any]):
    """Print formatted quarantine statistics."""
    print("\n" + "=" * 60)
    print("QUARANTINE STATISTICS")
    print("=" * 60)

    print("\nUNRESOLVED RECORDS")
    print("-" * 60)
    if stats['unresolved']:
        for row in stats['unresolved']:
            print(f"{row['record_type'].upper()}: {row['count']} records")
            print(f"  Oldest: {row['oldest']}")
            print(f"  Newest: {row['newest']}")
    else:
        print("No unresolved records ✓")

    print("\nRESOLVED RECORDS")
    print("-" * 60)
    if stats['resolved']:
        for row in stats['resolved']:
            print(f"{row['record_type'].upper()} - {row['resolution_action']}: {row['count']}")
    else:
        print("No resolved records yet")

    print("\nMOST COMMON ERRORS")
    print("-" * 60)
    if stats['common_errors']:
        for row in stats['common_errors']:
            print(f"  {row['error']}: {row['count']} occurrences")
    else:
        print("No errors to report")

    print("\n" + "=" * 60)


def print_quarantined_records(records: List[Dict[str, Any]]):
    """Print formatted list of quarantined records."""
    print("\n" + "=" * 60)
    print(f"QUARANTINED RECORDS ({len(records)} total)")
    print("=" * 60)

    for record in records:
        print(f"\nID: {record['id']}")
        print(f"Type: {record['record_type']}")
        print(f"Source: {record['source']}")
        print(f"Quarantined: {record['quarantined_at']}")
        print(f"Errors:")
        for error in record['validation_errors']:
            print(f"  - {error}")
        print(f"Data: {json.dumps(record['raw_payload'], indent=2)}")
        print("-" * 60)


def main():
    """Main entry point."""
    import argparse

    parser = argparse.ArgumentParser(description='PLE Quarantine Review & Cleanup')
    parser.add_argument('--action', required=True,
                        choices=['stats', 'list', 'export', 'resolve', 'cleanup'],
                        help='Action to perform')
    parser.add_argument('--type', choices=['company', 'person'], help='Filter by record type')
    parser.add_argument('--limit', type=int, default=50, help='Limit for list action')
    parser.add_argument('--output', help='Output file for export action')
    parser.add_argument('--id', type=int, help='Quarantine ID for resolve action')
    parser.add_argument('--resolution', choices=['fixed', 'rejected', 'merged'],
                        help='Resolution action for resolve')
    parser.add_argument('--days', type=int, default=90, help='Days for cleanup action')

    args = parser.parse_args()

    # Connect to database
    conn = psycopg2.connect(CONNECTION_STRING)

    try:
        if args.action == 'stats':
            stats = get_quarantine_stats(conn)
            print_quarantine_stats(stats)

        elif args.action == 'list':
            records = list_quarantined_records(conn, args.type, args.limit)
            print_quarantined_records(records)

        elif args.action == 'export':
            if not args.output:
                print("ERROR: --output required for export action")
                return 1

            count = export_quarantine_to_json(conn, args.output, args.type)
            print(f"✓ Exported {count} records to {args.output}")

        elif args.action == 'resolve':
            if not args.id or not args.resolution:
                print("ERROR: --id and --resolution required for resolve action")
                return 1

            resolve_quarantined_record(conn, args.id, args.resolution)
            print(f"✓ Resolved quarantine ID {args.id} as '{args.resolution}'")

        elif args.action == 'cleanup':
            deleted = cleanup_old_resolved(conn, args.days)
            print(f"✓ Deleted {deleted} resolved records older than {args.days} days")

    finally:
        conn.close()


if __name__ == '__main__':
    main()
