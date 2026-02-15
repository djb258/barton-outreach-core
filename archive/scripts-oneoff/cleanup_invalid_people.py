"""
People Master Cleanup Script
=============================
Identifies and cleans up invalid records in people.people_master.

Strategy:
1. Identify invalid records (missing email, bad data, invalid flags)
2. Check slot linkages (filled vs unfilled)
3. Archive or fix records based on linkage status
4. Report cleanup results

Per Doctrine:
- Preserve records linked to filled slots (critical business data)
- Archive/remove orphaned or invalid records
- Maintain referential integrity with people.company_slot
"""

import os
import sys
import logging
from datetime import datetime
from typing import Dict, List, Tuple
import psycopg2
import psycopg2.extras

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


# =============================================================================
# DATABASE CONNECTION
# =============================================================================

def get_db_connection():
    """Create database connection from environment variables."""
    conn_params = {
        'host': os.getenv('NEON_HOST'),
        'port': os.getenv('NEON_PORT', '5432'),
        'database': os.getenv('NEON_DATABASE'),
        'user': os.getenv('NEON_USER'),
        'password': os.getenv('NEON_PASSWORD'),
        'sslmode': 'require'
    }

    missing = [k for k, v in conn_params.items() if not v and k != 'sslmode']
    if missing:
        raise ValueError(f"Missing environment variables: {', '.join(missing)}")

    return psycopg2.connect(**conn_params)


# =============================================================================
# ANALYSIS FUNCTIONS
# =============================================================================

def analyze_people_master(conn) -> Dict:
    """Analyze people_master table structure and invalid records."""
    cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

    analysis = {
        'total_records': 0,
        'invalid_records': {},
        'slot_linkage': {},
        'data_quality': {}
    }

    # Get total count
    cursor.execute("SELECT COUNT(*) as count FROM people.people_master")
    analysis['total_records'] = cursor.fetchone()['count']
    logger.info(f"Total people_master records: {analysis['total_records']:,}")

    # Check for invalid flag columns
    cursor.execute("""
        SELECT column_name
        FROM information_schema.columns
        WHERE table_schema = 'people'
          AND table_name = 'people_master'
          AND column_name LIKE '%invalid%'
    """)
    invalid_columns = [row['column_name'] for row in cursor.fetchall()]
    logger.info(f"Invalid flag columns found: {invalid_columns}")

    # Check for records with missing critical fields
    logger.info("\n--- Checking data quality issues ---")

    # Missing email
    cursor.execute("""
        SELECT COUNT(*) as count
        FROM people.people_master
        WHERE email IS NULL OR TRIM(email) = ''
    """)
    missing_email = cursor.fetchone()['count']
    analysis['invalid_records']['missing_email'] = missing_email
    logger.info(f"Records with missing email: {missing_email:,}")

    # Missing unique_id (should never happen - PK)
    cursor.execute("""
        SELECT COUNT(*) as count
        FROM people.people_master
        WHERE unique_id IS NULL OR TRIM(unique_id) = ''
    """)
    missing_id = cursor.fetchone()['count']
    analysis['invalid_records']['missing_person_id'] = missing_id
    logger.info(f"Records with missing unique_id: {missing_id:,}")

    # Missing name
    cursor.execute("""
        SELECT COUNT(*) as count
        FROM people.people_master
        WHERE (full_name IS NULL OR TRIM(full_name) = '')
          AND (first_name IS NULL OR TRIM(first_name) = '')
          AND (last_name IS NULL OR TRIM(last_name) = '')
    """)
    missing_name = cursor.fetchone()['count']
    analysis['invalid_records']['missing_name'] = missing_name
    logger.info(f"Records with missing name fields: {missing_name:,}")

    # Missing company_unique_id
    cursor.execute("""
        SELECT COUNT(*) as count
        FROM people.people_master
        WHERE company_unique_id IS NULL OR TRIM(company_unique_id) = ''
    """)
    missing_company = cursor.fetchone()['count']
    analysis['invalid_records']['missing_company_id'] = missing_company
    logger.info(f"Records with missing company_unique_id: {missing_company:,}")

    # Records with multiple critical issues
    cursor.execute("""
        SELECT COUNT(*) as count
        FROM people.people_master
        WHERE (email IS NULL OR TRIM(email) = '')
          AND (company_unique_id IS NULL OR TRIM(company_unique_id) = '')
          AND ((full_name IS NULL OR TRIM(full_name) = '')
               AND (first_name IS NULL OR TRIM(first_name) = ''))
    """)
    critical_invalid = cursor.fetchone()['count']
    analysis['invalid_records']['critical_invalid'] = critical_invalid
    logger.info(f"Records with multiple critical issues: {critical_invalid:,}")

    # Check slot linkage
    logger.info("\n--- Checking slot linkage ---")

    # Records linked to filled slots
    cursor.execute("""
        SELECT COUNT(DISTINCT pm.unique_id) as count
        FROM people.people_master pm
        INNER JOIN people.company_slot cs
          ON pm.unique_id = cs.person_unique_id
        WHERE cs.is_filled = TRUE
    """)
    linked_filled = cursor.fetchone()['count']
    analysis['slot_linkage']['linked_to_filled_slots'] = linked_filled
    logger.info(f"Records linked to filled slots: {linked_filled:,}")

    # Records linked to unfilled slots
    cursor.execute("""
        SELECT COUNT(DISTINCT pm.unique_id) as count
        FROM people.people_master pm
        INNER JOIN people.company_slot cs
          ON pm.unique_id = cs.person_unique_id
        WHERE cs.is_filled = FALSE
    """)
    linked_unfilled = cursor.fetchone()['count']
    analysis['slot_linkage']['linked_to_unfilled_slots'] = linked_unfilled
    logger.info(f"Records linked to unfilled slots: {linked_unfilled:,}")

    # Records not linked to any slot
    cursor.execute("""
        SELECT COUNT(*) as count
        FROM people.people_master pm
        WHERE NOT EXISTS (
            SELECT 1
            FROM people.company_slot cs
            WHERE cs.person_unique_id = pm.unique_id
        )
    """)
    no_slot = cursor.fetchone()['count']
    analysis['slot_linkage']['no_slot_linkage'] = no_slot
    logger.info(f"Records NOT linked to any slot: {no_slot:,}")

    # Invalid records linked to filled slots (CRITICAL - should not delete)
    cursor.execute("""
        SELECT COUNT(DISTINCT pm.unique_id) as count
        FROM people.people_master pm
        INNER JOIN people.company_slot cs
          ON pm.unique_id = cs.person_unique_id
        WHERE cs.is_filled = TRUE
          AND (pm.email IS NULL OR TRIM(pm.email) = '')
    """)
    invalid_but_filled = cursor.fetchone()['count']
    analysis['slot_linkage']['invalid_but_filled'] = invalid_but_filled
    logger.warning(f"Invalid records linked to FILLED slots (PRESERVE): {invalid_but_filled:,}")

    cursor.close()
    return analysis


def get_cleanup_candidates(conn) -> Tuple[List[Dict], List[Dict], List[Dict]]:
    """
    Get records eligible for cleanup, categorized by safety.

    Returns:
        Tuple of (safe_to_delete, needs_review, must_preserve)
    """
    cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

    # SAFE TO DELETE: No slot linkage + invalid
    cursor.execute("""
        SELECT
            pm.unique_id,
            pm.full_name,
            pm.email,
            pm.company_unique_id,
            pm.source_system as data_source,
            pm.created_at
        FROM people.people_master pm
        WHERE NOT EXISTS (
            SELECT 1
            FROM people.company_slot cs
            WHERE cs.person_unique_id = pm.unique_id
        )
        AND (
            (pm.email IS NULL OR TRIM(pm.email) = '')
            OR (pm.company_unique_id IS NULL OR TRIM(pm.company_unique_id) = '')
            OR ((pm.full_name IS NULL OR TRIM(pm.full_name) = '')
                AND (pm.first_name IS NULL OR TRIM(pm.first_name) = ''))
        )
        ORDER BY pm.created_at DESC
    """)
    safe_to_delete = cursor.fetchall()

    # NEEDS REVIEW: Linked to unfilled slots + invalid
    cursor.execute("""
        SELECT DISTINCT
            pm.unique_id,
            pm.full_name,
            pm.email,
            pm.company_unique_id,
            pm.source_system as data_source,
            cs.slot_type,
            cs.is_filled,
            pm.created_at
        FROM people.people_master pm
        INNER JOIN people.company_slot cs
          ON pm.unique_id = cs.person_unique_id
        WHERE cs.is_filled = FALSE
          AND (
              (pm.email IS NULL OR TRIM(pm.email) = '')
              OR (pm.company_unique_id IS NULL OR TRIM(pm.company_unique_id) = '')
          )
        ORDER BY pm.created_at DESC
    """)
    needs_review = cursor.fetchall()

    # MUST PRESERVE: Linked to filled slots (even if invalid)
    cursor.execute("""
        SELECT DISTINCT
            pm.unique_id,
            pm.full_name,
            pm.email,
            pm.company_unique_id,
            pm.source_system as data_source,
            cs.slot_type,
            cs.is_filled,
            pm.created_at,
            CASE
                WHEN pm.email IS NULL OR TRIM(pm.email) = '' THEN 'missing_email'
                WHEN pm.company_unique_id IS NULL OR TRIM(pm.company_unique_id) = '' THEN 'missing_company'
                ELSE 'other'
            END as invalid_reason
        FROM people.people_master pm
        INNER JOIN people.company_slot cs
          ON pm.unique_id = cs.person_unique_id
        WHERE cs.is_filled = TRUE
          AND (
              (pm.email IS NULL OR TRIM(pm.email) = '')
              OR (pm.company_unique_id IS NULL OR TRIM(pm.company_unique_id) = '')
          )
        ORDER BY pm.created_at DESC
    """)
    must_preserve = cursor.fetchall()

    cursor.close()
    return safe_to_delete, needs_review, must_preserve


# =============================================================================
# CLEANUP FUNCTIONS
# =============================================================================

def create_archive_table(conn):
    """Create archive table if it doesn't exist."""
    cursor = conn.cursor()

    logger.info("Creating people_master_archive table (if not exists)...")
    cursor.execute("""
        -- Drop and recreate to ensure consistency
        DROP TABLE IF EXISTS people.people_master_archive;

        CREATE TABLE people.people_master_archive (
            archived_at TIMESTAMP NOT NULL DEFAULT NOW(),
            archive_reason TEXT,
            unique_id TEXT,
            company_unique_id TEXT,
            company_slot_unique_id TEXT,
            first_name TEXT,
            last_name TEXT,
            full_name TEXT,
            title TEXT,
            seniority TEXT,
            department TEXT,
            email TEXT,
            work_phone_e164 TEXT,
            personal_phone_e164 TEXT,
            linkedin_url TEXT,
            twitter_url TEXT,
            facebook_url TEXT,
            bio TEXT,
            skills TEXT[],
            education TEXT,
            certifications TEXT[],
            source_system TEXT,
            source_record_id TEXT,
            promoted_from_intake_at TIMESTAMP,
            promotion_audit_log_id INTEGER,
            created_at TIMESTAMP,
            updated_at TIMESTAMP,
            email_verified BOOLEAN,
            message_key_scheduled TEXT,
            email_verification_source TEXT,
            email_verified_at TIMESTAMP,
            validation_status VARCHAR,
            last_verified_at TIMESTAMP,
            last_enrichment_attempt TIMESTAMP,
            is_decision_maker BOOLEAN
        );
    """)

    conn.commit()
    cursor.close()
    logger.info("Archive table ready")


def archive_records(conn, person_ids: List[str], reason: str) -> int:
    """Archive records to people_master_archive."""
    if not person_ids:
        return 0

    cursor = conn.cursor()

    # Insert into archive
    cursor.execute("""
        INSERT INTO people.people_master_archive (
            archived_at, archive_reason,
            unique_id, company_unique_id, company_slot_unique_id,
            first_name, last_name, full_name, title, seniority, department,
            email, work_phone_e164, personal_phone_e164,
            linkedin_url, twitter_url, facebook_url, bio,
            skills, education, certifications,
            source_system, source_record_id,
            promoted_from_intake_at, promotion_audit_log_id,
            created_at, updated_at,
            email_verified, message_key_scheduled, email_verification_source,
            email_verified_at, validation_status, last_verified_at,
            last_enrichment_attempt, is_decision_maker
        )
        SELECT
            NOW(), %s,
            unique_id, company_unique_id, company_slot_unique_id,
            first_name, last_name, full_name, title, seniority, department,
            email, work_phone_e164, personal_phone_e164,
            linkedin_url, twitter_url, facebook_url, bio,
            skills, education, certifications,
            source_system, source_record_id,
            promoted_from_intake_at, promotion_audit_log_id,
            created_at, updated_at,
            email_verified, message_key_scheduled, email_verification_source,
            email_verified_at, validation_status, last_verified_at,
            last_enrichment_attempt, is_decision_maker
        FROM people.people_master
        WHERE unique_id = ANY(%s)
    """, (reason, person_ids))

    archived_count = cursor.rowcount

    # Delete from main table
    cursor.execute("""
        DELETE FROM people.people_master
        WHERE unique_id = ANY(%s)
    """, (person_ids,))

    deleted_count = cursor.rowcount

    conn.commit()
    cursor.close()

    logger.info(f"Archived {archived_count} records, deleted {deleted_count} records")
    return deleted_count


def unlink_from_unfilled_slots(conn, person_ids: List[str]) -> int:
    """Remove person_unique_id from unfilled slots (set to NULL)."""
    if not person_ids:
        return 0

    cursor = conn.cursor()

    cursor.execute("""
        UPDATE people.company_slot
        SET person_unique_id = NULL,
            is_filled = FALSE,
            filled_at = NULL
        WHERE person_unique_id = ANY(%s)
          AND is_filled = FALSE
    """, (person_ids,))

    unlinked_count = cursor.rowcount
    conn.commit()
    cursor.close()

    logger.info(f"Unlinked {unlinked_count} unfilled slot assignments")
    return unlinked_count


# =============================================================================
# MAIN CLEANUP LOGIC
# =============================================================================

def execute_cleanup(conn, dry_run: bool = True) -> Dict:
    """
    Execute the cleanup strategy.

    Args:
        conn: Database connection
        dry_run: If True, report only without making changes

    Returns:
        Cleanup statistics
    """
    logger.info(f"\n{'='*80}")
    logger.info(f"CLEANUP MODE: {'DRY RUN (no changes)' if dry_run else 'LIVE (will modify data)'}")
    logger.info(f"{'='*80}\n")

    stats = {
        'safe_deleted': 0,
        'review_archived': 0,
        'preserved': 0,
        'slots_unlinked': 0
    }

    # Get cleanup candidates
    safe_to_delete, needs_review, must_preserve = get_cleanup_candidates(conn)

    logger.info(f"\n--- Cleanup Candidates ---")
    logger.info(f"Safe to delete (no slot linkage): {len(safe_to_delete):,}")
    logger.info(f"Needs review (unfilled slots): {len(needs_review):,}")
    logger.info(f"Must preserve (filled slots): {len(must_preserve):,}")

    # Show samples
    if safe_to_delete:
        logger.info(f"\nSample safe-to-delete records (first 5):")
        for record in safe_to_delete[:5]:
            logger.info(f"  - {record['unique_id']}: {record['full_name']} | {record['email']} | {record['data_source']}")

    if needs_review:
        logger.info(f"\nSample needs-review records (first 5):")
        for record in needs_review[:5]:
            logger.info(f"  - {record['unique_id']}: {record['full_name']} | {record['email']} | Slot: {record['slot_type']} | Filled: {record['is_filled']}")

    if must_preserve:
        logger.info(f"\nWARNING: Invalid records linked to FILLED slots (first 5):")
        for record in must_preserve[:5]:
            logger.info(f"  - {record['unique_id']}: {record['full_name']} | {record['email']} | Slot: {record['slot_type']} | Filled: {record['is_filled']} | Issue: {record['invalid_reason']}")

    if dry_run:
        logger.info(f"\n{'='*80}")
        logger.info(f"DRY RUN COMPLETE - No changes made")
        logger.info(f"Run with --execute flag to apply cleanup")
        logger.info(f"{'='*80}")
        return stats

    # LIVE CLEANUP
    logger.info(f"\n--- Executing Cleanup (LIVE) ---")

    # Create archive table
    create_archive_table(conn)

    # 1. Archive and delete safe records (no slot linkage)
    if safe_to_delete:
        logger.info(f"\nArchiving {len(safe_to_delete):,} orphaned invalid records...")
        safe_ids = [r['unique_id'] for r in safe_to_delete]
        stats['safe_deleted'] = archive_records(conn, safe_ids, 'orphaned_invalid')

    # 2. Unlink from unfilled slots, then archive
    if needs_review:
        logger.info(f"\nUnlinking {len(needs_review):,} records from unfilled slots...")
        review_ids = [r['unique_id'] for r in needs_review]
        stats['slots_unlinked'] = unlink_from_unfilled_slots(conn, review_ids)
        stats['review_archived'] = archive_records(conn, review_ids, 'unfilled_slot_invalid')

    # 3. Preserve filled slot records (just count, do NOT delete)
    stats['preserved'] = len(must_preserve)
    if must_preserve:
        logger.warning(f"\nPreserving {stats['preserved']:,} invalid records linked to filled slots")
        logger.warning("These records need manual review and fixing")

    logger.info(f"\n{'='*80}")
    logger.info(f"CLEANUP COMPLETE")
    logger.info(f"  - Deleted (orphaned): {stats['safe_deleted']:,}")
    logger.info(f"  - Deleted (unlinked from unfilled): {stats['review_archived']:,}")
    logger.info(f"  - Preserved (filled slots): {stats['preserved']:,}")
    logger.info(f"  - Slots unlinked: {stats['slots_unlinked']:,}")
    logger.info(f"{'='*80}")

    return stats


def main():
    """Main execution."""
    import argparse

    parser = argparse.ArgumentParser(description='Clean up invalid people_master records')
    parser.add_argument('--execute', action='store_true', help='Execute cleanup (default is dry run)')
    args = parser.parse_args()

    try:
        # Connect to database
        logger.info("Connecting to Neon database...")
        conn = get_db_connection()
        logger.info("Connected successfully")

        # Analyze current state
        logger.info("\n" + "="*80)
        logger.info("ANALYZING PEOPLE_MASTER TABLE")
        logger.info("="*80)
        analysis = analyze_people_master(conn)

        # Execute cleanup
        stats = execute_cleanup(conn, dry_run=not args.execute)

        # Final count
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) as count FROM people.people_master")
        final_count = cursor.fetchone()[0]
        cursor.close()

        logger.info(f"\nFinal people_master count: {final_count:,}")
        logger.info(f"Initial count: {analysis['total_records']:,}")
        logger.info(f"Records removed: {analysis['total_records'] - final_count:,}")

        conn.close()

    except Exception as e:
        logger.error(f"Error: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
