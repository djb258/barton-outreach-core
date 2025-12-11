#!/usr/bin/env python3
"""
Create Stage-Specific Failure Tables in Neon
=============================================
Each pipeline stage has its own failure table so issues can be worked separately.

Tables:
  - marketing.failed_company_match     (Phase 1: company not in hub)
  - marketing.failed_slot_assignment   (Phase 1: matched but lost slot)
  - marketing.failed_low_confidence    (Phase 1: 70-79% fuzzy match)
  - marketing.failed_no_pattern        (Phase 2: company has no email pattern)
  - marketing.failed_email_verification (Phase 3: email didn't verify)

Created: 2024-12-11
"""

import os
from dotenv import load_dotenv
import psycopg2

load_dotenv()

DATABASE_URL = os.getenv('DATABASE_URL') or os.getenv('NEON_DATABASE_URL')


def create_failure_tables():
    """Create all stage-specific failure tables"""
    conn = psycopg2.connect(DATABASE_URL)
    cur = conn.cursor()

    print("Creating stage-specific failure tables...")
    print("=" * 60)

    # Phase 1: Company not found in hub
    cur.execute("""
        CREATE TABLE IF NOT EXISTS marketing.failed_company_match (
            id SERIAL PRIMARY KEY,
            person_id VARCHAR(50) NOT NULL,
            full_name VARCHAR(500) NOT NULL,
            job_title VARCHAR(500),
            title_seniority VARCHAR(50),
            company_name_raw VARCHAR(500) NOT NULL,
            linkedin_url VARCHAR(500),

            -- Match attempt details
            best_match_company VARCHAR(500),
            best_match_score DECIMAL(5,2),
            best_match_notes TEXT,

            -- Resolution tracking
            resolution_status VARCHAR(50) DEFAULT 'pending',
            resolution VARCHAR(50),
            resolution_notes TEXT,
            resolved_by VARCHAR(255),
            resolved_at TIMESTAMP,

            -- If resolved by adding to company hub
            resolved_company_id VARCHAR(50),

            -- Metadata
            source VARCHAR(100),
            source_file VARCHAR(255),
            created_at TIMESTAMP DEFAULT NOW(),
            updated_at TIMESTAMP DEFAULT NOW(),

            UNIQUE(person_id, source_file)
        )
    """)
    print("  ✅ marketing.failed_company_match")

    # Phase 1: Matched company but lost slot to higher seniority
    cur.execute("""
        CREATE TABLE IF NOT EXISTS marketing.failed_slot_assignment (
            id SERIAL PRIMARY KEY,
            person_id VARCHAR(50) NOT NULL,
            full_name VARCHAR(500) NOT NULL,
            job_title VARCHAR(500),
            title_seniority VARCHAR(50),
            company_name_raw VARCHAR(500),
            linkedin_url VARCHAR(500),

            -- Match details (they DID match)
            matched_company_id VARCHAR(50),
            matched_company_name VARCHAR(500),
            matched_company_domain VARCHAR(255),
            fuzzy_score DECIMAL(5,2),

            -- Slot competition details
            slot_type VARCHAR(50),
            lost_to_person_id VARCHAR(50),
            lost_to_person_name VARCHAR(500),
            lost_to_seniority VARCHAR(50),

            -- Resolution tracking (could be promoted to backup contact)
            resolution_status VARCHAR(50) DEFAULT 'pending',
            resolution VARCHAR(50),
            resolution_notes TEXT,
            resolved_by VARCHAR(255),
            resolved_at TIMESTAMP,

            -- Metadata
            source VARCHAR(100),
            source_file VARCHAR(255),
            created_at TIMESTAMP DEFAULT NOW(),
            updated_at TIMESTAMP DEFAULT NOW(),

            UNIQUE(person_id, source_file)
        )
    """)
    print("  ✅ marketing.failed_slot_assignment")

    # Phase 1: Low confidence match (70-79%)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS marketing.failed_low_confidence (
            id SERIAL PRIMARY KEY,
            person_id VARCHAR(50) NOT NULL,
            full_name VARCHAR(500) NOT NULL,
            job_title VARCHAR(500),
            title_seniority VARCHAR(50),
            company_name_raw VARCHAR(500) NOT NULL,
            linkedin_url VARCHAR(500),

            -- Match details
            matched_company_id VARCHAR(50),
            matched_company_name VARCHAR(500),
            matched_company_domain VARCHAR(255),
            fuzzy_score DECIMAL(5,2),
            match_notes TEXT,

            -- Resolution tracking
            resolution_status VARCHAR(50) DEFAULT 'pending',
            resolution VARCHAR(50),  -- 'confirmed', 'rejected', 'remapped'
            resolution_notes TEXT,
            resolved_by VARCHAR(255),
            resolved_at TIMESTAMP,

            -- If confirmed, they can proceed to slot assignment
            confirmed_company_id VARCHAR(50),

            -- Metadata
            source VARCHAR(100),
            source_file VARCHAR(255),
            created_at TIMESTAMP DEFAULT NOW(),
            updated_at TIMESTAMP DEFAULT NOW(),

            UNIQUE(person_id, source_file)
        )
    """)
    print("  ✅ marketing.failed_low_confidence")

    # Phase 2: Company has no email pattern
    cur.execute("""
        CREATE TABLE IF NOT EXISTS marketing.failed_no_pattern (
            id SERIAL PRIMARY KEY,
            person_id VARCHAR(50) NOT NULL,
            full_name VARCHAR(500) NOT NULL,
            job_title VARCHAR(500),
            title_seniority VARCHAR(50),
            company_name_raw VARCHAR(500),
            linkedin_url VARCHAR(500),

            -- Company details (they matched, but company has no pattern)
            company_id VARCHAR(50),
            company_name VARCHAR(500),
            company_domain VARCHAR(255),
            slot_type VARCHAR(50),

            -- Why no pattern
            failure_reason VARCHAR(100),  -- 'no_domain', 'pattern_lookup_failed', etc.
            failure_notes TEXT,

            -- Resolution tracking
            resolution_status VARCHAR(50) DEFAULT 'pending',
            resolution VARCHAR(50),  -- 'pattern_added', 'manual_email', 'skipped'
            resolution_notes TEXT,
            resolved_by VARCHAR(255),
            resolved_at TIMESTAMP,

            -- If resolved with manual email
            manual_email VARCHAR(255),
            manual_email_source VARCHAR(100),

            -- Metadata
            source VARCHAR(100),
            source_file VARCHAR(255),
            created_at TIMESTAMP DEFAULT NOW(),
            updated_at TIMESTAMP DEFAULT NOW(),

            UNIQUE(person_id, source_file)
        )
    """)
    print("  ✅ marketing.failed_no_pattern")

    # Phase 3: Email verification failed
    cur.execute("""
        CREATE TABLE IF NOT EXISTS marketing.failed_email_verification (
            id SERIAL PRIMARY KEY,
            person_id VARCHAR(50) NOT NULL,
            full_name VARCHAR(500) NOT NULL,
            job_title VARCHAR(500),
            title_seniority VARCHAR(50),
            company_name_raw VARCHAR(500),
            linkedin_url VARCHAR(500),

            -- Company details
            company_id VARCHAR(50),
            company_name VARCHAR(500),
            company_domain VARCHAR(255),
            email_pattern VARCHAR(50),
            slot_type VARCHAR(50),

            -- Failed email details
            generated_email VARCHAR(255),
            verification_error VARCHAR(255),
            verification_notes TEXT,

            -- Alternative emails tried
            email_variants TEXT,  -- JSON array of variants tried

            -- Resolution tracking
            resolution_status VARCHAR(50) DEFAULT 'pending',
            resolution VARCHAR(50),  -- 'alt_email_found', 'manual_verified', 'skipped'
            resolution_notes TEXT,
            resolved_by VARCHAR(255),
            resolved_at TIMESTAMP,

            -- If resolved with alternative email
            verified_email VARCHAR(255),
            verified_email_source VARCHAR(100),

            -- Metadata
            source VARCHAR(100),
            source_file VARCHAR(255),
            created_at TIMESTAMP DEFAULT NOW(),
            updated_at TIMESTAMP DEFAULT NOW(),

            UNIQUE(person_id, source_file)
        )
    """)
    print("  ✅ marketing.failed_email_verification")

    # Create indexes for common queries
    print("\nCreating indexes...")

    tables = [
        'failed_company_match',
        'failed_slot_assignment',
        'failed_low_confidence',
        'failed_no_pattern',
        'failed_email_verification'
    ]

    for table in tables:
        cur.execute(f"""
            CREATE INDEX IF NOT EXISTS idx_{table}_status
            ON marketing.{table}(resolution_status)
        """)
        cur.execute(f"""
            CREATE INDEX IF NOT EXISTS idx_{table}_source
            ON marketing.{table}(source_file)
        """)

    print("  ✅ Indexes created")

    conn.commit()
    conn.close()

    print("\n" + "=" * 60)
    print("All failure tables created successfully!")
    print("\nTable Summary:")
    print("  Phase 1 Failures:")
    print("    - failed_company_match    : Company not in hub")
    print("    - failed_slot_assignment  : Lost slot to higher seniority")
    print("    - failed_low_confidence   : 70-79% fuzzy match")
    print("  Phase 2 Failures:")
    print("    - failed_no_pattern       : Company has no email pattern")
    print("  Phase 3 Failures:")
    print("    - failed_email_verification : Email didn't verify")


def migrate_from_review_queue():
    """Migrate existing review_queue data to new tables"""
    conn = psycopg2.connect(DATABASE_URL)
    cur = conn.cursor()

    print("\nMigrating existing review_queue data...")
    print("=" * 60)

    # Migrate no_match -> failed_company_match
    cur.execute("""
        INSERT INTO marketing.failed_company_match (
            person_id, full_name, job_title, company_name_raw, linkedin_url,
            best_match_company, best_match_score, best_match_notes,
            resolution_status, source, source_file, created_at
        )
        SELECT
            person_id, full_name, job_title, company_name_raw, linkedin_url,
            fuzzy_matched_company, fuzzy_score, review_notes,
            'pending', source, source_file, created_at
        FROM marketing.review_queue
        WHERE review_reason = 'no_match'
        ON CONFLICT (person_id, source_file) DO NOTHING
    """)
    no_match_count = cur.rowcount
    print(f"  ✅ Migrated {no_match_count} no_match -> failed_company_match")

    # Migrate lost_slot -> failed_slot_assignment
    cur.execute("""
        INSERT INTO marketing.failed_slot_assignment (
            person_id, full_name, job_title, company_name_raw, linkedin_url,
            matched_company_id, matched_company_name, fuzzy_score,
            slot_type, lost_to_person_name,
            resolution_status, source, source_file, created_at
        )
        SELECT
            person_id, full_name, job_title, company_name_raw, linkedin_url,
            matched_company_id, fuzzy_matched_company, fuzzy_score,
            'hr', review_notes,  -- Extract from review_notes
            'pending', source, source_file, created_at
        FROM marketing.review_queue
        WHERE review_reason = 'lost_slot'
        ON CONFLICT (person_id, source_file) DO NOTHING
    """)
    lost_slot_count = cur.rowcount
    print(f"  ✅ Migrated {lost_slot_count} lost_slot -> failed_slot_assignment")

    # Migrate low_confidence -> failed_low_confidence
    cur.execute("""
        INSERT INTO marketing.failed_low_confidence (
            person_id, full_name, job_title, company_name_raw, linkedin_url,
            matched_company_id, matched_company_name, fuzzy_score, match_notes,
            resolution_status, source, source_file, created_at
        )
        SELECT
            person_id, full_name, job_title, company_name_raw, linkedin_url,
            matched_company_id, fuzzy_matched_company, fuzzy_score, review_notes,
            'pending', source, source_file, created_at
        FROM marketing.review_queue
        WHERE review_reason = 'low_confidence'
        ON CONFLICT (person_id, source_file) DO NOTHING
    """)
    low_conf_count = cur.rowcount
    print(f"  ✅ Migrated {low_conf_count} low_confidence -> failed_low_confidence")

    conn.commit()
    conn.close()

    print(f"\nTotal migrated: {no_match_count + lost_slot_count + low_conf_count}")


def show_stats():
    """Show current stats for all failure tables"""
    conn = psycopg2.connect(DATABASE_URL)
    cur = conn.cursor()

    print("\nFailure Table Stats:")
    print("=" * 60)

    tables = [
        ('failed_company_match', 'Phase 1: No company match'),
        ('failed_slot_assignment', 'Phase 1: Lost slot'),
        ('failed_low_confidence', 'Phase 1: Low confidence'),
        ('failed_no_pattern', 'Phase 2: No pattern'),
        ('failed_email_verification', 'Phase 3: Email failed'),
    ]

    for table, desc in tables:
        cur.execute(f"SELECT COUNT(*) FROM marketing.{table}")
        total = cur.fetchone()[0]

        cur.execute(f"""
            SELECT resolution_status, COUNT(*)
            FROM marketing.{table}
            GROUP BY resolution_status
        """)
        by_status = dict(cur.fetchall())

        pending = by_status.get('pending', 0)
        resolved = total - pending

        print(f"\n{desc}:")
        print(f"  Table: marketing.{table}")
        print(f"  Total: {total} | Pending: {pending} | Resolved: {resolved}")

    conn.close()


if __name__ == "__main__":
    create_failure_tables()
    migrate_from_review_queue()
    show_stats()
