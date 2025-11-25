"""
WV Data Audit - Comprehensive Database State Report
Generates complete audit of failed validation queue + validated companies + slot completion

Output: ctb/analytics/wv_data_audit.json

Usage:
    python create_audit_report.py
"""

import os
import sys
import json
from pathlib import Path
from datetime import datetime

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

try:
    import psycopg2
    from psycopg2.extras import RealDictCursor
except ImportError:
    print("ERROR: psycopg2 not installed. Run: pip install psycopg2-binary")
    sys.exit(1)

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    print("WARNING: python-dotenv not installed. Using system environment variables only.")


def get_db_connection():
    """Get database connection using environment variables"""
    connection_string = os.getenv("DATABASE_URL") or os.getenv("NEON_CONNECTION_STRING")

    if not connection_string:
        print("ERROR: DATABASE_URL not found in environment")
        sys.exit(1)

    try:
        conn = psycopg2.connect(connection_string)
        return conn
    except Exception as e:
        print(f"ERROR: Failed to connect to database: {e}")
        sys.exit(1)


def audit_failed_validation_queue(cursor):
    """Audit the failed validation queue"""
    print("\n" + "="*80)
    print("AUDITING FAILED VALIDATION QUEUE")
    print("="*80)

    audit = {
        "table_name": "marketing.company_invalid",
        "row_count": 0,
        "failure_reasons": {},
        "by_state": {},
        "reviewed_status": {},
        "examples": []
    }

    # 1. Total count
    cursor.execute("SELECT COUNT(*) as total FROM marketing.company_invalid;")
    audit["row_count"] = cursor.fetchone()['total']
    print(f"\nTotal records in queue: {audit['row_count']}")

    if audit["row_count"] == 0:
        print("Queue is empty!")
        return audit

    # 2. Count by reason_code
    cursor.execute("""
        SELECT reason_code, COUNT(*) as count
        FROM marketing.company_invalid
        GROUP BY reason_code
        ORDER BY count DESC;
    """)

    print("\nFailure Reasons Breakdown:")
    for row in cursor.fetchall():
        reason = row['reason_code'] or 'NULL'
        count = row['count']
        audit["failure_reasons"][reason] = count
        print(f"  {reason}: {count} companies")

    # 3. Count by state
    cursor.execute("""
        SELECT state, COUNT(*) as count
        FROM marketing.company_invalid
        GROUP BY state
        ORDER BY count DESC;
    """)

    print("\nBy State:")
    for row in cursor.fetchall():
        state = row['state'] or 'NULL'
        count = row['count']
        audit["by_state"][state] = count
        print(f"  {state}: {count} companies")

    # 4. Reviewed status
    cursor.execute("""
        SELECT reviewed, COUNT(*) as count
        FROM marketing.company_invalid
        GROUP BY reviewed;
    """)

    print("\nReview Status:")
    for row in cursor.fetchall():
        status = "Reviewed" if row['reviewed'] else "Not Reviewed"
        count = row['count']
        audit["reviewed_status"][status] = count
        print(f"  {status}: {count} companies")

    # 5. Sample 5 records
    cursor.execute("""
        SELECT
            id,
            company_unique_id,
            company_name,
            website,
            employee_count,
            reason_code,
            validation_errors,
            failed_at,
            reviewed
        FROM marketing.company_invalid
        ORDER BY failed_at DESC
        LIMIT 5;
    """)

    print("\nSample 5 Records:")
    records = cursor.fetchall()

    for i, row in enumerate(records, 1):
        example = {
            "id": row['id'],
            "company_unique_id": row['company_unique_id'],
            "company_name": row['company_name'],
            "website": row['website'],
            "employee_count": row['employee_count'],
            "reason_code": row['reason_code'],
            "failed_at": row['failed_at'].isoformat() if row['failed_at'] else None,
            "reviewed": row['reviewed'],
            "validation_errors": row['validation_errors']
        }
        audit["examples"].append(example)

        print(f"\n  {i}. {row['company_name']}")
        print(f"     ID: {row['company_unique_id']}")
        print(f"     Reason: {row['reason_code']}")
        print(f"     Employee Count: {row['employee_count'] or 'N/A'}")

    return audit


def audit_validated_companies(cursor):
    """Audit validated companies in company_master"""
    print("\n" + "="*80)
    print("AUDITING VALIDATED COMPANIES")
    print("="*80)

    audit = {
        "total_count": 0,
        "by_state": {},
        "slot_stats": {
            "complete_slots_3of3": 0,
            "incomplete_slots": 0,
            "missing_ceo": 0,
            "missing_cfo": 0,
            "missing_hr": 0,
            "no_slots": 0
        }
    }

    # 1. Total count in company_master
    cursor.execute("SELECT COUNT(*) as total FROM marketing.company_master;")
    audit["total_count"] = cursor.fetchone()['total']
    print(f"\nTotal validated companies: {audit['total_count']}")

    if audit["total_count"] == 0:
        print("No validated companies!")
        return audit

    # 2. Count by state
    cursor.execute("""
        SELECT address_state, COUNT(*) as count
        FROM marketing.company_master
        GROUP BY address_state
        ORDER BY count DESC
        LIMIT 10;
    """)

    print("\nTop 10 States:")
    for row in cursor.fetchall():
        state = row['address_state'] or 'NULL'
        count = row['count']
        audit["by_state"][state] = count
        print(f"  {state}: {count} companies")

    # 3. Slot completion stats
    # Check if company_slot table exists
    cursor.execute("""
        SELECT EXISTS (
            SELECT 1 FROM information_schema.tables
            WHERE table_schema = 'marketing'
            AND table_name = 'company_slot'
        );
    """)

    result = cursor.fetchone()
    if not result['exists']:
        print("\nWARNING: company_slot table does not exist")
        return audit

    # Count companies by slot completion
    cursor.execute("""
        WITH slot_counts AS (
            SELECT
                company_unique_id,
                COUNT(*) FILTER (WHERE is_filled = true) as filled_count,
                COUNT(*) as total_slots
            FROM marketing.company_slot
            GROUP BY company_unique_id
        )
        SELECT
            CASE
                WHEN filled_count = 3 THEN 'complete_3of3'
                WHEN filled_count > 0 THEN 'incomplete'
                ELSE 'no_slots'
            END as slot_status,
            COUNT(*) as count
        FROM slot_counts
        GROUP BY slot_status;
    """)

    print("\nSlot Completion:")
    for row in cursor.fetchall():
        status = row['slot_status']
        count = row['count']

        if status == 'complete_3of3':
            audit["slot_stats"]["complete_slots_3of3"] = count
            print(f"  Complete (3/3 filled): {count} companies")
        elif status == 'incomplete':
            audit["slot_stats"]["incomplete_slots"] = count
            print(f"  Incomplete (<3 filled): {count} companies")
        elif status == 'no_slots':
            audit["slot_stats"]["no_slots"] = count
            print(f"  No slots filled: {count} companies")

    # Count missing slots by type
    cursor.execute("""
        SELECT
            slot_type,
            COUNT(*) FILTER (WHERE is_filled = false) as unfilled_count
        FROM marketing.company_slot
        GROUP BY slot_type
        ORDER BY slot_type;
    """)

    print("\nMissing Slots by Type:")
    for row in cursor.fetchall():
        slot_type = row['slot_type']
        unfilled = row['unfilled_count']

        if slot_type == 'CEO':
            audit["slot_stats"]["missing_ceo"] = unfilled
        elif slot_type == 'CFO':
            audit["slot_stats"]["missing_cfo"] = unfilled
        elif slot_type == 'HR':
            audit["slot_stats"]["missing_hr"] = unfilled

        print(f"  Missing {slot_type}: {unfilled} companies")

    return audit


def create_full_audit_report():
    """Create comprehensive audit report"""
    conn = get_db_connection()
    cursor = conn.cursor(cursor_factory=RealDictCursor)

    print("\n" + "="*80)
    print("WV DATA AUDIT - COMPREHENSIVE REPORT")
    print("="*80)
    print(f"Timestamp: {datetime.now().isoformat()}")

    # Build report
    report = {
        "audit_timestamp": datetime.now().isoformat(),
        "failed_validation_queue": audit_failed_validation_queue(cursor),
        "validated_companies": audit_validated_companies(cursor)
    }

    # Add summary
    queue_count = report["failed_validation_queue"]["row_count"]
    validated_count = report["validated_companies"]["total_count"]
    total_companies = queue_count + validated_count

    complete_slots = report["validated_companies"]["slot_stats"]["complete_slots_3of3"]
    incomplete_slots = report["validated_companies"]["slot_stats"]["incomplete_slots"]

    report["summary"] = {
        "total_companies_loaded": total_companies,
        "validation_pass_count": validated_count,
        "validation_fail_count": queue_count,
        "validation_pass_rate": round(validated_count / max(total_companies, 1) * 100, 2),
        "slot_completion_rate": round(complete_slots / max(validated_count, 1) * 100, 2)
    }

    print("\n" + "="*80)
    print("SUMMARY")
    print("="*80)
    print(f"Total companies loaded: {total_companies}")
    print(f"  Passed validation: {validated_count} ({report['summary']['validation_pass_rate']}%)")
    print(f"  Failed validation: {queue_count}")
    print(f"\nSlot completion (of validated companies):")
    print(f"  Complete (3/3): {complete_slots} ({report['summary']['slot_completion_rate']}%)")
    print(f"  Incomplete: {incomplete_slots}")

    # Save report
    output_dir = Path(__file__).parent.parent.parent / "analytics"
    output_dir.mkdir(parents=True, exist_ok=True)
    output_file = output_dir / "wv_data_audit.json"

    with open(output_file, 'w') as f:
        json.dump(report, f, indent=2)

    print("\n" + "="*80)
    print(f"Report saved to: {output_file}")
    print("="*80)

    cursor.close()
    conn.close()

    return report


if __name__ == "__main__":
    create_full_audit_report()
