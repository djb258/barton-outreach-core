#!/usr/bin/env python3
"""
Clay People CSV Loader

Loads all CEO/CFO/HR CSVs from state folders into intake.people_raw_intake.

Usage:
    doppler run -- python scripts/load_clay_people_intake.py

CSV Source: Clay Tables folder on Desktop
"""

import os
import sys
import csv
import psycopg2
from datetime import datetime
from pathlib import Path

# Windows encoding fix
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')


# State folders to process
STATES = {
    'DE': 'DE Lists',
    'KY': 'KY Lists',
    'MD': 'MD Lists',
    'NC': 'NC Lists',
    'OH': 'OH Lists',
    'PA': 'PA Lists',
    'VA': 'VA Lists',
    'WV': 'WV Lists',
}

BASE_PATH = Path(r"C:\Users\CUSTOM PC\Desktop\Clay Tables")


def get_connection():
    """Get database connection."""
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        print("[FAIL] DATABASE_URL not set")
        sys.exit(1)
    return psycopg2.connect(database_url)


def parse_location(location: str) -> dict:
    """Parse location string into city, state, country."""
    # Format: "Charleston, West Virginia, United States"
    parts = [p.strip() for p in location.split(',') if p.strip()]

    result = {'city': None, 'state': None, 'country': None}

    if len(parts) >= 1:
        result['city'] = parts[0]
    if len(parts) >= 2:
        result['state'] = parts[1]
    if len(parts) >= 3:
        result['country'] = parts[2]

    return result


def detect_slot_type(filename: str) -> str:
    """Detect slot type from filename."""
    filename_lower = filename.lower()
    if 'ceo' in filename_lower:
        return 'CEO'
    elif 'cfo' in filename_lower:
        return 'CFO'
    elif 'hr' in filename_lower:
        return 'HR'
    return 'UNKNOWN'


def find_csv_files(state_abbrev: str, folder_name: str) -> list:
    """Find CEO/CFO/HR CSVs in a state folder."""
    folder_path = BASE_PATH / folder_name
    if not folder_path.exists():
        return []

    csv_files = []
    for f in folder_path.glob("*.csv"):
        filename = f.name.lower()
        # Skip company files
        if 'compan' in filename:
            continue
        # Only include CEO/CFO/HR files
        if 'ceo' in filename or 'cfo' in filename or 'hr' in filename:
            csv_files.append({
                'path': f,
                'state': state_abbrev,
                'slot_type': detect_slot_type(f.name),
                'filename': f.name
            })

    return csv_files


def load_csv_to_intake(conn, csv_info: dict, batch_id: str) -> dict:
    """Load a single CSV into intake.people_raw_intake."""
    cur = conn.cursor()

    stats = {
        'file': csv_info['filename'],
        'state': csv_info['state'],
        'slot_type': csv_info['slot_type'],
        'total': 0,
        'inserted': 0,
        'errors': 0
    }

    try:
        with open(csv_info['path'], 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)

            for row in reader:
                stats['total'] += 1

                # Parse location
                location = row.get('Location', '')
                loc_parts = parse_location(location)

                # Map CSV columns to intake columns
                try:
                    cur.execute("""
                        INSERT INTO intake.people_raw_intake (
                            first_name, last_name, full_name, title,
                            company_name, linkedin_url,
                            city, state, state_abbrev, country,
                            slot_type, source_system, source_record_id,
                            import_batch_id, backfill_source,
                            validated, created_at
                        ) VALUES (
                            %s, %s, %s, %s,
                            %s, %s,
                            %s, %s, %s, %s,
                            %s, %s, %s,
                            %s, %s,
                            FALSE, NOW()
                        )
                    """, (
                        row.get('First Name', '').strip() or None,
                        row.get('Last Name', '').strip() or None,
                        row.get('Full Name', '').strip() or None,
                        row.get('Job Title', '').strip() or None,
                        row.get('Company Name', '').strip() or None,
                        row.get('LinkedIn Profile', '').strip() or None,
                        loc_parts['city'],
                        loc_parts['state'],
                        csv_info['state'],  # state_abbrev from folder
                        loc_parts['country'],
                        csv_info['slot_type'],
                        'clay_csv',
                        row.get('Company Domain', '').strip() or None,  # Store domain in source_record_id for joining
                        batch_id,
                        csv_info['filename'],
                        ))
                    stats['inserted'] += 1

                except Exception as e:
                    stats['errors'] += 1
                    if stats['errors'] <= 3:
                        print(f"    Error: {str(e)[:80]}")
                    conn.rollback()
                    continue

            conn.commit()

    except Exception as e:
        print(f"  [ERROR] Failed to process {csv_info['filename']}: {e}")
        stats['errors'] = stats['total']

    cur.close()
    return stats


def main():
    print("=" * 70)
    print("CLAY PEOPLE CSV LOADER")
    print("=" * 70)
    print(f"Base path: {BASE_PATH}")
    print(f"States: {', '.join(STATES.keys())}")

    # Generate batch ID
    batch_id = datetime.now().strftime("%Y%m%d_%H%M%S")
    print(f"Batch ID: {batch_id}")

    # Find all CSV files
    all_csvs = []
    print("\nScanning for CSV files...")
    for state_abbrev, folder_name in STATES.items():
        csvs = find_csv_files(state_abbrev, folder_name)
        all_csvs.extend(csvs)
        if csvs:
            print(f"  {state_abbrev}: {len(csvs)} files")
            for c in csvs:
                print(f"    - {c['slot_type']}: {c['filename']}")

    print(f"\nTotal CSV files found: {len(all_csvs)}")

    if not all_csvs:
        print("[WARN] No CSV files found")
        return

    # Connect and load
    conn = get_connection()

    # Check current intake count
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) FROM intake.people_raw_intake")
    before_count = cur.fetchone()[0]
    print(f"\nCurrent intake.people_raw_intake count: {before_count}")
    cur.close()

    # Load each CSV
    print("\nLoading CSVs...")
    all_stats = []

    for csv_info in all_csvs:
        print(f"\n  Processing: {csv_info['state']}/{csv_info['slot_type']} - {csv_info['filename']}")
        stats = load_csv_to_intake(conn, csv_info, batch_id)
        all_stats.append(stats)
        print(f"    Loaded: {stats['inserted']}/{stats['total']} (errors: {stats['errors']})")

    # Final count
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) FROM intake.people_raw_intake")
    after_count = cur.fetchone()[0]
    cur.close()

    conn.close()

    # Summary
    print("\n" + "=" * 70)
    print("LOAD SUMMARY")
    print("=" * 70)

    total_loaded = sum(s['inserted'] for s in all_stats)
    total_errors = sum(s['errors'] for s in all_stats)

    print(f"\nBy State/Slot:")
    for state in STATES.keys():
        state_stats = [s for s in all_stats if s['state'] == state]
        if state_stats:
            state_total = sum(s['inserted'] for s in state_stats)
            print(f"  {state}:")
            for s in state_stats:
                print(f"    {s['slot_type']}: {s['inserted']}")

    print(f"\nTotal records loaded: {total_loaded}")
    print(f"Total errors: {total_errors}")
    print(f"intake.people_raw_intake: {before_count} -> {after_count}")
    print(f"Batch ID: {batch_id}")


if __name__ == "__main__":
    main()
