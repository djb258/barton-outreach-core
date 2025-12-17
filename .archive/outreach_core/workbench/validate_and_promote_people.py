#!/usr/bin/env python3
"""
People Intake Validation & Promotion Pipeline (v2.0)
====================================================

Complete workflow with Barton Outreach Doctrine validation:
1. Pull all records from intake.people_raw_intake
2. Validate using people_validator.py (strict doctrine rules)
3. For VALID records:
   - Generate Barton ID
   - Promote to marketing.people_master (UPSERT by unique_id)
   - DELETE from intake (goal: keep intake empty)
4. For INVALID records:
   - Upload to B2 grouped by state (bay_a.json or bay_b.json)
   - Log to garage_runs + agent_routing_log
   - Increment enrichment_attempt counter
   - Mark chronic_bad if enrichment_attempt >= 2
   - KEEP in intake for agent enrichment

CLI Modes:
- --validate-only: Only validate, don't promote or delete
- --validate-and-promote: Full pipeline (validate, promote, delete)

Exit Codes:
- 0: Success (intake is empty after run)
- 1: Incomplete (records remain in intake)

Author: Claude Code
Created: 2025-11-18
Barton ID: 04.04.02.04.50000.###
"""

import os
import sys
import json
import argparse
from datetime import datetime
from collections import defaultdict
import psycopg2
from dotenv import load_dotenv
import boto3
from botocore.client import Config

# Add parent directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from validation import validate_person

# Load environment variables
load_dotenv()

# ============================================================================
# CONFIGURATION
# ============================================================================

SNAPSHOT_VERSION = datetime.now().isoformat(timespec='seconds').replace(':', '').replace('-', '').replace('T', '')
VALIDATED_BY = "validate_and_promote_people.py v2.0"

# B2 Configuration
B2_ENDPOINT = os.getenv('B2_ENDPOINT')
B2_KEY_ID = os.getenv('B2_KEY_ID')
B2_APPLICATION_KEY = os.getenv('B2_APPLICATION_KEY')
B2_BUCKET = os.getenv('B2_BUCKET')

# Barton ID Configuration (must match DB constraints)
BARTON_SUBHIVE = "04"      # Outreach
BARTON_APP = "04"          # Outreach core
BARTON_LAYER = "02"        # People layer
# Format: 04.04.02.XX.XXXXX.XXX

# Statistics tracking
stats = {
    'total_scanned': 0,
    'promoted': 0,
    'failed_bay_a': 0,
    'failed_bay_b': 0,
    'chronic_bad': 0,
    'deleted_from_intake': 0,
    'uploaded_to_b2': 0,
    'logged_to_garage': 0,
}

# ============================================================================
# BARTON ID GENERATION
# ============================================================================

def generate_barton_id(sequence_num):
    r"""
    Generate Barton ID matching constraint: ^04\.04\.02\.[0-9]{2}\.[0-9]{5}\.[0-9]{3}$
    Example: 04.04.02.24.00024.024 or 04.04.02.00.00400.400

    Pattern:
    - 04.04.02 = Subhive.App.Layer (people)
    - XX = Last 2 digits of sequence (sequence % 100)
    - XXXXX = 5-digit sequence (zero-padded)
    - XXX = 3-digit sequence (zero-padded)
    """
    two_digit = sequence_num % 100
    return f"{BARTON_SUBHIVE}.{BARTON_APP}.{BARTON_LAYER}.{two_digit:02d}.{sequence_num:05d}.{sequence_num:03d}"

def get_next_people_sequence(cursor):
    """Get next sequence number for people_master"""
    cursor.execute("""
        SELECT unique_id FROM marketing.people_master
        WHERE unique_id LIKE %s
        ORDER BY unique_id DESC
        LIMIT 1;
    """, (f"{BARTON_SUBHIVE}.{BARTON_APP}.{BARTON_LAYER}.%",))

    result = cursor.fetchone()
    if result:
        last_id = result[0]
        last_seq = int(last_id.split('.')[-1])
        return last_seq + 1
    else:
        return 1

# ============================================================================
# B2 UPLOAD (GROUPED BY STATE)
# ============================================================================

def upload_to_b2_grouped(failed_people_by_state):
    """
    Upload failed people to B2, grouped by state and bay.

    Args:
        failed_people_by_state: Dict[state, Dict[bay, List[person]]]

    Returns:
        Number of files uploaded
    """
    try:
        s3 = boto3.client(
            's3',
            endpoint_url=B2_ENDPOINT,
            aws_access_key_id=B2_KEY_ID,
            aws_secret_access_key=B2_APPLICATION_KEY,
            config=Config(signature_version='s3v4')
        )

        uploaded_count = 0
        date_prefix = datetime.now().strftime("%Y-%m-%d")

        for state, bays in failed_people_by_state.items():
            for bay, people in bays.items():
                if not people:
                    continue

                # File path: people_bad/STATE/DATE/bay_a.json
                state_clean = state.replace(' ', '_').replace(',', '').upper() if state else 'UNKNOWN'
                file_name = f"people_bad/{state_clean}/{date_prefix}/{bay}.json"

                # Prepare payload
                payload = {
                    'snapshot_version': SNAPSHOT_VERSION,
                    'state': state,
                    'bay': bay,
                    'total_people': len(people),
                    'validated_at': datetime.now().isoformat(),
                    'validated_by': VALIDATED_BY,
                    'people': people
                }

                # Convert datetime objects to strings
                for person in payload['people']:
                    for key, value in person.items():
                        if isinstance(value, datetime):
                            person[key] = value.isoformat()

                # Upload to B2
                s3.put_object(
                    Bucket=B2_BUCKET,
                    Key=file_name,
                    Body=json.dumps(payload, indent=2),
                    ContentType='application/json'
                )

                print(f"  [B2] Uploaded {len(people)} people to {file_name}")
                uploaded_count += 1

        return uploaded_count

    except Exception as e:
        print(f"  [ERROR] B2 upload failed: {e}")
        return 0

# ============================================================================
# GARAGE LOGGING
# ============================================================================

def create_garage_run(cursor, snapshot_version):
    """Create a garage_run record and return the run_id."""
    try:
        cursor.execute("""
            INSERT INTO public.garage_runs (
                run_started_at,
                run_status,
                snapshot_version,
                total_records_processed,
                bay_a_count,
                bay_b_count
            ) VALUES (%s, %s, %s, %s, %s, %s)
            RETURNING run_id;
        """, (
            datetime.now(),
            'running',
            snapshot_version,
            0,
            0,
            0
        ))
        run_id = cursor.fetchone()[0]
        return run_id
    except Exception as e:
        print(f"  [WARNING] Failed to create garage_run: {e}")
        return None

def update_garage_run(cursor, run_id, total_records, bay_a_count, bay_b_count):
    """Update garage_run with final counts."""
    try:
        cursor.execute("""
            UPDATE public.garage_runs
            SET run_ended_at = %s,
                run_status = %s,
                total_records_processed = %s,
                bay_a_count = %s,
                bay_b_count = %s
            WHERE run_id = %s;
        """, (
            datetime.now(),
            'completed',
            total_records,
            bay_a_count,
            bay_b_count,
            run_id
        ))
    except Exception as e:
        print(f"  [WARNING] Failed to update garage_run: {e}")

def log_to_agent_routing(cursor, garage_run_id, person, validation_result):
    """Log failed person to agent_routing_log for agent assignment."""
    try:
        garage_bay = validation_result['garage_bay']
        reasons = ', '.join(validation_result['reasons'])

        # Determine agent based on bay
        if garage_bay == 'bay_a':
            agent_name = 'apify'  # LinkedIn scraping
        else:
            agent_name = 'claude'  # Complex reasoning

        cursor.execute("""
            INSERT INTO public.agent_routing_log (
                garage_run_id,
                record_type,
                record_id,
                garage_bay,
                agent_name,
                routing_reason,
                routed_at,
                status
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s);
        """, (
            garage_run_id,
            'person',
            str(person.get('id')),
            garage_bay,
            agent_name,
            reasons,
            datetime.now(),
            'pending'
        ))
    except Exception as e:
        print(f"  [WARNING] Failed to log to agent_routing_log: {e}")

# ============================================================================
# PROMOTION TO MASTER
# ============================================================================

def promote_to_master(cursor, person, barton_id):
    """
    Promote validated person to marketing.people_master.
    Uses UPSERT (INSERT ... ON CONFLICT UPDATE) to handle duplicates.
    """
    try:
        cursor.execute("""
            INSERT INTO marketing.people_master (
                unique_id,
                company_unique_id,
                first_name,
                last_name,
                full_name,
                title,
                seniority,
                department,
                email,
                work_phone_e164,
                personal_phone_e164,
                linkedin_url,
                twitter_url,
                facebook_url,
                bio,
                skills,
                education,
                certifications,
                source_system,
                source_record_id,
                created_at,
                updated_at
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (unique_id) DO UPDATE SET
                company_unique_id = EXCLUDED.company_unique_id,
                first_name = EXCLUDED.first_name,
                last_name = EXCLUDED.last_name,
                full_name = EXCLUDED.full_name,
                title = EXCLUDED.title,
                seniority = EXCLUDED.seniority,
                department = EXCLUDED.department,
                email = EXCLUDED.email,
                work_phone_e164 = EXCLUDED.work_phone_e164,
                personal_phone_e164 = EXCLUDED.personal_phone_e164,
                linkedin_url = EXCLUDED.linkedin_url,
                twitter_url = EXCLUDED.twitter_url,
                facebook_url = EXCLUDED.facebook_url,
                bio = EXCLUDED.bio,
                skills = EXCLUDED.skills,
                education = EXCLUDED.education,
                certifications = EXCLUDED.certifications,
                updated_at = EXCLUDED.updated_at;
        """, (
            barton_id,
            person.get('company_unique_id'),
            person.get('first_name'),
            person.get('last_name'),
            person.get('full_name'),
            person.get('title'),
            person.get('seniority'),
            person.get('department'),
            person.get('email'),
            person.get('work_phone'),
            person.get('personal_phone'),
            person.get('linkedin_url'),
            person.get('twitter_url'),
            person.get('facebook_url'),
            person.get('bio'),
            person.get('skills'),
            person.get('education'),
            person.get('certifications'),
            person.get('source_system', 'intake_csv'),
            str(person.get('id')),
            datetime.now(),
            datetime.now()
        ))
        return True
    except Exception as e:
        print(f"  [ERROR] Failed to promote person {person.get('id')}: {e}")
        return False

# ============================================================================
# MAIN PIPELINE
# ============================================================================

def main():
    parser = argparse.ArgumentParser(description='People Validation & Promotion Pipeline')
    parser.add_argument('--validate-only', action='store_true',
                        help='Only validate, do not promote or delete')
    parser.add_argument('--validate-and-promote', action='store_true',
                        help='Full pipeline: validate, promote, delete (default)')
    args = parser.parse_args()

    # Default to validate-and-promote if neither flag specified
    if not args.validate_only and not args.validate_and_promote:
        args.validate_and_promote = True

    mode = "VALIDATE ONLY" if args.validate_only else "VALIDATE & PROMOTE"

    print("=" * 80)
    print("PEOPLE INTAKE VALIDATION & PROMOTION PIPELINE v2.0")
    print("=" * 80)
    print()
    print(f"Mode: {mode}")
    print(f"Snapshot Version: {SNAPSHOT_VERSION}")
    print(f"B2 Bucket: {B2_BUCKET}")
    print()

    # ========================================================================
    # STEP 1: Connect to Neon PostgreSQL
    # ========================================================================
    print("STEP 1: Connecting to Neon PostgreSQL")
    print("-" * 80)

    try:
        neon_conn = psycopg2.connect(
            host=os.getenv('NEON_HOST'),
            database=os.getenv('NEON_DATABASE'),
            user=os.getenv('NEON_USER'),
            password=os.getenv('NEON_PASSWORD'),
            sslmode='require'
        )
        neon_cursor = neon_conn.cursor()
        print("[OK] Connected to Neon PostgreSQL")
        print()
    except Exception as e:
        print(f"[ERROR] Failed to connect to Neon PostgreSQL: {e}")
        sys.exit(1)

    # ========================================================================
    # STEP 2: Create Garage Run
    # ========================================================================
    garage_run_id = create_garage_run(neon_cursor, SNAPSHOT_VERSION)
    if garage_run_id:
        print(f"[OK] Created garage_run ID: {garage_run_id}")
        print()
    else:
        print("[WARNING] Could not create garage_run (will skip logging)")
        print()

    # ========================================================================
    # STEP 3: Pull ALL people from intake.people_raw_intake
    # ========================================================================
    print("STEP 2: Pulling ALL People from intake.people_raw_intake")
    print("-" * 80)

    try:
        neon_cursor.execute("""
            SELECT
                id, first_name, last_name, full_name, email, work_phone,
                personal_phone, title, seniority, department, company_name,
                company_unique_id, linkedin_url, twitter_url, facebook_url,
                bio, skills, education, certifications, city, state, state_abbrev,
                country, source_system, source_record_id, import_batch_id,
                validated, validation_notes, validated_at, validated_by,
                enrichment_attempt, chronic_bad, last_enriched_at, enriched_by,
                b2_file_path, b2_uploaded_at, created_at, updated_at
            FROM intake.people_raw_intake
            ORDER BY id;
        """)

        column_names = [desc[0] for desc in neon_cursor.description]
        people = []
        for row in neon_cursor.fetchall():
            person = dict(zip(column_names, row))
            people.append(person)

        print(f"[OK] Pulled {len(people)} people from intake")
        print()
    except Exception as e:
        print(f"[ERROR] Failed to pull people: {e}")
        neon_cursor.close()
        neon_conn.close()
        sys.exit(1)

    # ========================================================================
    # STEP 4: Validate, Promote, or Upload to B2
    # ========================================================================
    print("STEP 3: Validating People (Barton Doctrine)")
    print("-" * 80)
    print()

    people_to_delete = []
    failed_people_by_state = defaultdict(lambda: defaultdict(list))

    for idx, person in enumerate(people, start=1):
        stats['total_scanned'] += 1
        person_id = person['id']
        person_name = str(person.get('full_name', 'Unknown')).encode('ascii', 'ignore').decode('ascii')
        state = person.get('state') or person.get('state_abbrev') or 'UNKNOWN'

        # Prepare person dict for validator
        validator_input = {
            'full_name': person.get('full_name'),
            'email': person.get('email'),
            'linkedin_url': person.get('linkedin_url'),
            'title': person.get('title'),
            'company_unique_id': person.get('company_unique_id'),
            'seniority': person.get('seniority'),
            'department': person.get('department'),
            'company_domain': None,  # Would need to join with company_master
            'enrichment_attempt': person.get('enrichment_attempt', 0),
        }

        # Validate the person record
        validation_result = validate_person(validator_input)

        if validation_result['validation_status'] == 'passed':
            # ============================================================
            # VALID: Promote to master and DELETE from intake
            # ============================================================

            if args.validate_and_promote:
                # Generate Barton ID
                next_seq = get_next_people_sequence(neon_cursor)
                barton_id = generate_barton_id(next_seq)

                # Promote to marketing.people_master (UPSERT)
                if promote_to_master(neon_cursor, person, barton_id):
                    stats['promoted'] += 1
                    people_to_delete.append(person_id)

                    # Update intake with validation success
                    neon_cursor.execute("""
                        UPDATE intake.people_raw_intake
                        SET validated = TRUE,
                            validation_notes = %s,
                            validated_at = %s,
                            validated_by = %s
                        WHERE id = %s;
                    """, (
                        'All validations passed',
                        datetime.now(),
                        VALIDATED_BY,
                        person_id
                    ))

                    print(f"  [{idx}/{len(people)}] PROMOTED: {person_name} -> {barton_id}")
                else:
                    # Rollback failed transaction
                    neon_conn.rollback()
                    print(f"  [{idx}/{len(people)}] FAILED PROMOTION: {person_name}")
            else:
                # Validate-only mode
                print(f"  [{idx}/{len(people)}] VALID (not promoted): {person_name}")

        else:
            # ============================================================
            # INVALID: Upload to B2, increment enrichment_attempt
            # ============================================================

            garage_bay = validation_result['garage_bay']
            reasons = validation_result['reasons']
            current_attempt = person.get('enrichment_attempt', 0)
            new_attempt = current_attempt + 1
            is_chronic = new_attempt >= 2

            if garage_bay == 'bay_a':
                stats['failed_bay_a'] += 1
            else:
                stats['failed_bay_b'] += 1

            if is_chronic:
                stats['chronic_bad'] += 1

            # Add to B2 upload queue (grouped by state)
            person_for_b2 = {
                **person,
                'validation_errors': reasons,
                'validation_notes': ', '.join(reasons),
                'validation_timestamp': datetime.now().isoformat()
            }
            failed_people_by_state[state][garage_bay].append(person_for_b2)

            # Update enrichment tracking in intake
            try:
                neon_cursor.execute("""
                    UPDATE intake.people_raw_intake
                    SET validated = FALSE,
                        validation_notes = %s,
                        validated_at = %s,
                        validated_by = %s,
                        enrichment_attempt = %s,
                        chronic_bad = %s
                    WHERE id = %s;
                """, (
                    ', '.join(reasons),
                    datetime.now(),
                    VALIDATED_BY,
                    new_attempt,
                    is_chronic,
                    person_id
                ))

                # Log to agent_routing_log
                if garage_run_id and args.validate_and_promote:
                    log_to_agent_routing(neon_cursor, garage_run_id, person, validation_result)
                    stats['logged_to_garage'] += 1

            except Exception as e:
                print(f"  [ERROR] Failed to update enrichment tracking: {e}")

            chronic_flag = " [CHRONIC_BAD]" if is_chronic else ""
            print(f"  [{idx}/{len(people)}] FAILED ({garage_bay}, attempt {new_attempt}){chronic_flag}: {person_name}")

        # Progress indicator
        if idx % 50 == 0:
            print()

    print()
    print(f"[OK] Validation Complete")
    print()

    # ========================================================================
    # STEP 5: Upload to B2 (grouped by state)
    # ========================================================================
    if args.validate_and_promote and failed_people_by_state:
        print("STEP 4: Uploading Failed People to B2 (Grouped by State)")
        print("-" * 80)

        uploaded_files = upload_to_b2_grouped(failed_people_by_state)
        stats['uploaded_to_b2'] = uploaded_files
        print(f"[OK] Uploaded {uploaded_files} B2 files")
        print()

    # ========================================================================
    # STEP 6: DELETE promoted people from intake
    # ========================================================================
    if args.validate_and_promote:
        print("STEP 5: Deleting Promoted People from Intake")
        print("-" * 80)

        if people_to_delete:
            try:
                neon_cursor.execute("""
                    DELETE FROM intake.people_raw_intake
                    WHERE id = ANY(%s);
                """, (people_to_delete,))
                stats['deleted_from_intake'] = len(people_to_delete)
                print(f"[OK] Deleted {len(people_to_delete)} promoted people from intake")
            except Exception as e:
                print(f"[ERROR] Failed to delete from intake: {e}")
        else:
            print("[OK] No people to delete (none were promoted)")

        print()

    # ========================================================================
    # STEP 7: Update Garage Run
    # ========================================================================
    if garage_run_id and args.validate_and_promote:
        update_garage_run(
            neon_cursor,
            garage_run_id,
            stats['total_scanned'],
            stats['failed_bay_a'],
            stats['failed_bay_b']
        )

    # Commit all changes
    neon_conn.commit()

    # Check if intake is empty
    neon_cursor.execute("SELECT COUNT(*) FROM intake.people_raw_intake;")
    remaining_count = neon_cursor.fetchone()[0]

    neon_cursor.close()
    neon_conn.close()

    # ========================================================================
    # FINAL SUMMARY
    # ========================================================================
    print("=" * 80)
    print("PEOPLE VALIDATION & PROMOTION SUMMARY")
    print("=" * 80)
    print()
    print(f"Snapshot Version: {SNAPSHOT_VERSION}")
    print(f"Mode: {mode}")
    print()
    print("PROCESSING RESULTS:")
    print(f"  Total People Scanned: {stats['total_scanned']}")
    if stats['total_scanned'] > 0:
        print(f"  Promoted to Master: {stats['promoted']} ({stats['promoted']/stats['total_scanned']*100:.1f}%)")
        print(f"  Failed - Bay A (missing): {stats['failed_bay_a']} ({stats['failed_bay_a']/stats['total_scanned']*100:.1f}%)")
        print(f"  Failed - Bay B (contradictions): {stats['failed_bay_b']} ({stats['failed_bay_b']/stats['total_scanned']*100:.1f}%)")
    print(f"  Chronic Bad (2+ attempts): {stats['chronic_bad']}")
    print()
    print("DATABASE OPERATIONS:")
    print(f"  Deleted from intake: {stats['deleted_from_intake']} records")
    print(f"  Remaining in intake: {remaining_count} records")
    print()
    print("GARAGE 2.0 LOGGING:")
    print(f"  Garage Run ID: {garage_run_id or 'N/A'}")
    print(f"  Agent routing logs: {stats['logged_to_garage']} records")
    print()
    print("B2 STORAGE:")
    print(f"  Uploaded files: {stats['uploaded_to_b2']} (grouped by state)")
    print(f"  B2 Bucket: {B2_BUCKET}")
    print()
    print("NEXT STEPS:")
    if remaining_count > 0:
        print(f"  1. {remaining_count} people remain in intake (awaiting enrichment)")
        print("  2. Run Garage 2.0 enrichment agents:")
        print("     python enrichment_garage_2_0.py --record-type person --snapshot " + SNAPSHOT_VERSION)
        print("  3. After enrichment, re-run this validation pipeline")
    else:
        print("  [OK] Intake table is EMPTY - all people validated!")
    print()
    print("=" * 80)

    # Exit code based on intake status
    if remaining_count == 0:
        print("[OK] PIPELINE COMPLETE - INTAKE EMPTY")
        print("=" * 80)
        sys.exit(0)
    else:
        print("[INCOMPLETE] PIPELINE COMPLETE - RECORDS REMAIN IN INTAKE")
        print("=" * 80)
        sys.exit(1)

if __name__ == '__main__':
    main()
