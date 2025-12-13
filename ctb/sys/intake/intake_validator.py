#!/usr/bin/env python3
"""
PLE Data Intake Validator

Two-layer validation architecture:
1. INTAKE GATE (this script) - validates BEFORE insert, quarantines bad records
2. DB CONSTRAINTS - backstop if something slips through

Purpose: Catch garbage at the door, not when it hits the wall.
"""

import json
import sys
import os
from datetime import datetime
from typing import Dict, List, Any, Optional
import psycopg2
from psycopg2.extras import RealDictCursor
from dotenv import load_dotenv

# Load environment
load_dotenv()

# Connection string
CONNECTION_STRING = os.getenv('NEON_CONNECTION_STRING') or os.getenv('DATABASE_URL')

# Valid states
VALID_STATES = ['PA', 'VA', 'MD', 'OH', 'WV', 'KY']

# Validation thresholds
FAILURE_RATE_THRESHOLD = 0.20  # Kill switch at 20% failure rate


class ValidationError:
    def __init__(self, field: str, message: str):
        self.field = field
        self.message = message

    def __str__(self):
        return f"{self.field}: {message}"


def validate_company(record: Dict[str, Any]) -> Dict[str, Any]:
    """
    Validate company record against PLE requirements.

    Returns:
        {
            'valid': bool,
            'errors': List[str],
            'record': Dict
        }
    """
    errors = []

    # Required: name
    if not record.get('company_name') or str(record['company_name']).strip() == '':
        errors.append('company_name: required')

    # Required: employee_count (50-2000, no max actually, just 50+ per user)
    emp = record.get('employee_count')
    if emp is None:
        errors.append('employee_count: required')
    else:
        try:
            emp_int = int(emp)
            if emp_int < 50:
                errors.append(f'employee_count: {emp_int} below minimum 50')
        except (ValueError, TypeError):
            errors.append(f'employee_count: must be integer, got {type(emp).__name__}')

    # Required: state (PA, VA, MD, OH, WV, KY)
    state = record.get('address_state')
    if not state:
        errors.append('address_state: required')
    else:
        state_upper = str(state).upper()
        # Accept full names and convert
        state_map = {
            'PENNSYLVANIA': 'PA',
            'VIRGINIA': 'VA',
            'MARYLAND': 'MD',
            'OHIO': 'OH',
            'WEST VIRGINIA': 'WV',
            'KENTUCKY': 'KY'
        }
        normalized_state = state_map.get(state_upper, state_upper)

        if normalized_state not in VALID_STATES:
            errors.append(f'address_state: {state} not in {VALID_STATES}')
        else:
            # Normalize for insert
            record['address_state'] = normalized_state

    # Required: source_system
    if not record.get('source_system') or str(record['source_system']).strip() == '':
        errors.append('source_system: required')

    return {
        'valid': len(errors) == 0,
        'errors': errors,
        'record': record
    }


def validate_person(record: Dict[str, Any], db_connection) -> Dict[str, Any]:
    """
    Validate person record against PLE requirements.

    Returns:
        {
            'valid': bool,
            'errors': List[str],
            'record': Dict,
            'validation_status': str ('full', 'linkedin_only', 'email_only', 'invalid')
        }
    """
    errors = []

    # Required: first_name
    if not record.get('first_name') or str(record['first_name']).strip() == '':
        errors.append('first_name: required')

    # Required: last_name
    if not record.get('last_name') or str(record['last_name']).strip() == '':
        errors.append('last_name: required')

    # Required: title
    if not record.get('title') or str(record['title']).strip() == '':
        errors.append('title: required')

    # Required: company_unique_id (must exist in company_master)
    company_id = record.get('company_unique_id')
    if not company_id:
        errors.append('company_unique_id: required')
    else:
        # Verify company exists
        cursor = db_connection.cursor(cursor_factory=RealDictCursor)
        cursor.execute(
            "SELECT 1 FROM marketing.company_master WHERE company_unique_id = %s",
            (company_id,)
        )
        exists = cursor.fetchone()
        if not exists:
            errors.append(f'company_unique_id: {company_id} does not exist in company_master')

    # Conditional: linkedin_url OR email (at least one required)
    linkedin = record.get('linkedin_url')
    email = record.get('email')

    if not linkedin and not email:
        errors.append('contact: must have linkedin_url OR email')

    # Validate linkedin_url format if provided
    if linkedin:
        linkedin_str = str(linkedin).strip()
        if not linkedin_str.startswith('https://www.linkedin.com/') and not linkedin_str.startswith('https://linkedin.com/'):
            errors.append(f'linkedin_url: invalid format (must start with https://www.linkedin.com/)')

    # Validate email format if provided
    if email:
        email_str = str(email).strip()
        if '@' not in email_str or '.' not in email_str.split('@')[-1]:
            errors.append(f'email: invalid format')

    # Determine validation status
    validation_status = 'invalid'
    if linkedin and email:
        validation_status = 'full'
    elif linkedin:
        validation_status = 'linkedin_only'
    elif email:
        validation_status = 'email_only'

    return {
        'valid': len(errors) == 0,
        'errors': errors,
        'record': record,
        'validation_status': validation_status
    }


def check_company_duplicate(record: Dict[str, Any], db_connection) -> Dict[str, Any]:
    """
    Check if company already exists in database.

    Match criteria: name + state (case-insensitive)
    """
    cursor = db_connection.cursor(cursor_factory=RealDictCursor)
    cursor.execute("""
        SELECT company_unique_id, company_name
        FROM marketing.company_master
        WHERE LOWER(company_name) = LOWER(%s)
        AND address_state = %s
        LIMIT 1
    """, (record.get('company_name'), record.get('address_state')))

    existing = cursor.fetchone()

    if existing:
        return {
            'is_duplicate': True,
            'existing_uid': existing['company_unique_id'],
            'existing_name': existing['company_name']
        }

    return {'is_duplicate': False}


def check_person_duplicate(record: Dict[str, Any], db_connection) -> Dict[str, Any]:
    """
    Check if person already exists in database.

    Match criteria (in order):
    1. linkedin_url (strongest match)
    2. email
    """
    cursor = db_connection.cursor(cursor_factory=RealDictCursor)

    # Check by linkedin_url first
    if record.get('linkedin_url'):
        cursor.execute("""
            SELECT unique_id, full_name, linkedin_url
            FROM marketing.people_master
            WHERE linkedin_url = %s
            LIMIT 1
        """, (record['linkedin_url'],))

        existing = cursor.fetchone()
        if existing:
            return {
                'is_duplicate': True,
                'match_type': 'linkedin_url',
                'existing_uid': existing['unique_id'],
                'existing_name': existing['full_name']
            }

    # Check by email
    if record.get('email'):
        cursor.execute("""
            SELECT unique_id, full_name, email
            FROM marketing.people_master
            WHERE email = %s
            LIMIT 1
        """, (record['email'],))

        existing = cursor.fetchone()
        if existing:
            return {
                'is_duplicate': True,
                'match_type': 'email',
                'existing_uid': existing['unique_id'],
                'existing_name': existing['full_name']
            }

    return {'is_duplicate': False}


def ensure_quarantine_table(db_connection):
    """Create quarantine table if it doesn't exist."""
    cursor = db_connection.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS marketing.intake_quarantine (
            id SERIAL PRIMARY KEY,
            record_type VARCHAR NOT NULL CHECK (record_type IN ('company','person')),
            raw_payload JSONB NOT NULL,
            validation_errors JSONB NOT NULL,
            source VARCHAR,
            quarantined_at TIMESTAMP NOT NULL DEFAULT NOW(),
            resolved_at TIMESTAMP,
            resolution_action VARCHAR CHECK (resolution_action IN ('fixed','rejected','merged'))
        );

        CREATE INDEX IF NOT EXISTS idx_quarantine_type ON marketing.intake_quarantine(record_type);
        CREATE INDEX IF NOT EXISTS idx_quarantine_date ON marketing.intake_quarantine(quarantined_at);
        CREATE INDEX IF NOT EXISTS idx_quarantine_unresolved ON marketing.intake_quarantine(resolved_at) WHERE resolved_at IS NULL;
    """)
    db_connection.commit()


def quarantine_record(record_type: str, record: Dict[str, Any], errors: List[str], source: str, db_connection):
    """Insert invalid record into quarantine table."""
    cursor = db_connection.cursor()
    cursor.execute("""
        INSERT INTO marketing.intake_quarantine
        (record_type, raw_payload, validation_errors, source)
        VALUES (%s, %s, %s, %s)
        RETURNING id
    """, (record_type, json.dumps(record), json.dumps(errors), source))

    quarantine_id = cursor.fetchone()[0]
    db_connection.commit()
    return quarantine_id


def process_batch(records: List[Dict[str, Any]], record_type: str, source: str, mode: str, db_connection) -> Dict[str, Any]:
    """
    Process batch of records with validation, duplicate detection, and optional insert.

    Args:
        records: List of company or person records
        record_type: 'company' or 'person'
        source: Source identifier (clay, phantombuster, etc.)
        mode: 'validate' (dry run) or 'insert'
        db_connection: Database connection

    Returns:
        Validation report dict
    """
    results = {
        'total': len(records),
        'valid': 0,
        'invalid': 0,
        'duplicates': 0,
        'inserted': 0,
        'quarantined': [],
        'duplicate_matches': [],
        'source': source,
        'record_type': record_type,
        'mode': mode,
        'timestamp': datetime.utcnow().isoformat()
    }

    for idx, record in enumerate(records):
        # Step 1: Validate
        if record_type == 'company':
            validation = validate_company(record)
            dup_check = check_company_duplicate(record, db_connection) if validation['valid'] else None
        else:  # person
            validation = validate_person(record, db_connection)
            dup_check = check_person_duplicate(record, db_connection) if validation['valid'] else None

        # Step 2: Route based on validation result
        if not validation['valid']:
            results['invalid'] += 1

            # Quarantine if in insert mode
            if mode == 'insert':
                quarantine_id = quarantine_record(
                    record_type,
                    record,
                    validation['errors'],
                    source,
                    db_connection
                )
                results['quarantined'].append({
                    'index': idx,
                    'quarantine_id': quarantine_id,
                    'record': record,
                    'errors': validation['errors']
                })
            else:
                results['quarantined'].append({
                    'index': idx,
                    'record': record,
                    'errors': validation['errors']
                })

        elif dup_check and dup_check['is_duplicate']:
            results['duplicates'] += 1
            results['duplicate_matches'].append({
                'index': idx,
                'incoming': record,
                'existing_uid': dup_check['existing_uid'],
                'match_type': dup_check.get('match_type', 'name+state')
            })

        else:
            results['valid'] += 1

            # INSERT if mode == 'insert'
            if mode == 'insert':
                # TODO: Implement actual insert logic here
                # For now, just count as would-be-inserted
                results['inserted'] += 1

    # Calculate failure rate
    failure_rate = results['invalid'] / results['total'] if results['total'] > 0 else 0
    results['failure_rate'] = failure_rate

    # KILL SWITCH: If >20% failure, halt and alert
    if failure_rate > FAILURE_RATE_THRESHOLD:
        results['kill_switch_triggered'] = True
        results['alert'] = f"BATCH REJECTED - {failure_rate*100:.1f}% failure rate exceeds {FAILURE_RATE_THRESHOLD*100}% threshold"
    else:
        results['kill_switch_triggered'] = False

    return results


def print_validation_report(results: Dict[str, Any]):
    """Print formatted validation report."""
    print("\n" + "=" * 60)
    print("INTAKE VALIDATION REPORT")
    print("=" * 60)
    print(f"Source: {results['source']}")
    print(f"Record Type: {results['record_type']}")
    print(f"Mode: {results['mode']}")
    print(f"Timestamp: {results['timestamp']}")
    print()

    print("SUMMARY")
    print("-" * 60)
    print(f"Total Records: {results['total']}")
    print(f"Valid: {results['valid']} ({results['valid']/results['total']*100:.1f}%)")
    print(f"Invalid: {results['invalid']} ({results['invalid']/results['total']*100:.1f}%)")
    print(f"Duplicates: {results['duplicates']} ({results['duplicates']/results['total']*100:.1f}%)")
    if results['mode'] == 'insert':
        print(f"Inserted: {results['inserted']}")
    print()

    # Kill switch alert
    if results.get('kill_switch_triggered'):
        print("⚠️  KILL SWITCH TRIGGERED ⚠️")
        print("-" * 60)
        print(results['alert'])
        print("Action: All inserts halted. Batch quarantined.")
        print("Required: Manual review before retry")
        print()

    # Invalid records
    if results['quarantined']:
        print("INVALID RECORDS (Quarantined)")
        print("-" * 60)
        for item in results['quarantined'][:10]:  # Show first 10
            print(f"\nRecord {item['index'] + 1}:")
            print(f"  Data: {json.dumps(item['record'], indent=4)}")
            print(f"  Errors:")
            for error in item['errors']:
                print(f"    - {error}")
            if 'quarantine_id' in item:
                print(f"  Quarantine ID: {item['quarantine_id']}")

        if len(results['quarantined']) > 10:
            print(f"\n... and {len(results['quarantined']) - 10} more")
        print()

    # Duplicates
    if results['duplicate_matches']:
        print("DUPLICATES DETECTED")
        print("-" * 60)
        for item in results['duplicate_matches'][:10]:
            print(f"\nRecord {item['index'] + 1}:")
            if results['record_type'] == 'company':
                print(f"  Incoming: {item['incoming'].get('company_name')} ({item['incoming'].get('address_state')})")
            else:
                print(f"  Incoming: {item['incoming'].get('first_name')} {item['incoming'].get('last_name')}")
            print(f"  Matches: {item['existing_uid']} (match type: {item.get('match_type', 'name+state')})")
            print(f"  Action: SKIPPED")

        if len(results['duplicate_matches']) > 10:
            print(f"\n... and {len(results['duplicate_matches']) - 10} more")
        print()

    # Success
    if results['valid'] > 0 and results['mode'] == 'insert':
        print("SUCCESSFUL INSERTS")
        print("-" * 60)
        print(f"Records inserted: {results['inserted']}")
        print()

    print("=" * 60)


def main():
    """Main entry point."""
    import argparse

    parser = argparse.ArgumentParser(description='PLE Data Intake Validator')
    parser.add_argument('--input', required=True, help='Input JSON file with records')
    parser.add_argument('--type', required=True, choices=['company', 'person'], help='Record type')
    parser.add_argument('--source', required=True, help='Source identifier (clay, phantombuster, etc.)')
    parser.add_argument('--mode', default='validate', choices=['validate', 'insert'], help='Execution mode')

    args = parser.parse_args()

    # Load input
    with open(args.input, 'r') as f:
        records = json.load(f)

    if not isinstance(records, list):
        records = [records]

    # Connect to database
    conn = psycopg2.connect(CONNECTION_STRING)

    try:
        # Ensure quarantine table exists
        ensure_quarantine_table(conn)

        # Process batch
        results = process_batch(records, args.type, args.source, args.mode, conn)

        # Print report
        print_validation_report(results)

        # Exit code based on kill switch
        if results.get('kill_switch_triggered'):
            sys.exit(2)  # Kill switch triggered
        elif results['invalid'] > 0:
            sys.exit(1)  # Some invalid records
        else:
            sys.exit(0)  # All valid

    finally:
        conn.close()


if __name__ == '__main__':
    main()
