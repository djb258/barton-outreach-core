#!/usr/bin/env python3
"""
Migration: Create people.people_errors table
Doctrine: People Intelligence Error & Recovery System
Version: 1.0.0
Date: 2026-01-08

This table is the canonical error capture for all People Intelligence failures.
Rules:
  - Append-only (no deletes)
  - Status-driven lifecycle only
  - No nullable outreach_id
  - Errors are first-class citizens, not dead ends
"""

import os
import psycopg2
from datetime import datetime

def get_connection():
    """Get database connection from environment."""
    return psycopg2.connect(os.environ['DATABASE_URL'])

def run_migration():
    """Create the people.people_errors table with all doctrine requirements."""
    
    conn = get_connection()
    cur = conn.cursor()
    
    print("=" * 70)
    print("MIGRATION: people.people_errors")
    print(f"Timestamp: {datetime.now().isoformat()}")
    print("=" * 70)
    
    # Create table
    print("\n[1/4] Creating people.people_errors table...")
    cur.execute("""
        CREATE TABLE IF NOT EXISTS people.people_errors (
            error_id                UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            outreach_id             UUID NOT NULL,
            slot_id                 UUID NULL,
            person_id               UUID NULL,
            error_stage             TEXT NOT NULL,
            error_type              TEXT NOT NULL,
            error_code              TEXT NOT NULL,
            error_message           TEXT NOT NULL,
            source_hints_used       JSONB,
            raw_payload             JSONB NOT NULL,
            retry_strategy          TEXT NOT NULL,
            retry_after             TIMESTAMPTZ NULL,
            status                  TEXT NOT NULL DEFAULT 'open',
            created_at              TIMESTAMPTZ NOT NULL DEFAULT now(),
            last_updated_at         TIMESTAMPTZ NOT NULL DEFAULT now(),
            
            CONSTRAINT chk_error_stage CHECK (error_stage IN (
                'slot_creation', 'slot_fill', 'movement_detect', 'enrichment', 'promotion'
            )),
            CONSTRAINT chk_error_type CHECK (error_type IN (
                'validation', 'ambiguity', 'conflict', 'missing_data', 'stale_data', 'external_fail'
            )),
            CONSTRAINT chk_retry_strategy CHECK (retry_strategy IN (
                'manual_fix', 'auto_retry', 'discard'
            )),
            CONSTRAINT chk_status CHECK (status IN (
                'open', 'fixed', 'replayed', 'abandoned'
            ))
        );
    """)
    print("  ✓ Table created")
    
    # Create indexes
    print("\n[2/4] Creating indexes...")
    indexes = [
        ("idx_people_errors_outreach_id", "CREATE INDEX IF NOT EXISTS idx_people_errors_outreach_id ON people.people_errors (outreach_id);"),
        ("idx_people_errors_status", "CREATE INDEX IF NOT EXISTS idx_people_errors_status ON people.people_errors (status);"),
        ("idx_people_errors_error_stage", "CREATE INDEX IF NOT EXISTS idx_people_errors_error_stage ON people.people_errors (error_stage);"),
        ("idx_people_errors_raw_payload", "CREATE INDEX IF NOT EXISTS idx_people_errors_raw_payload ON people.people_errors USING GIN (raw_payload);"),
        ("idx_people_errors_error_code", "CREATE INDEX IF NOT EXISTS idx_people_errors_error_code ON people.people_errors (error_code);"),
        ("idx_people_errors_created_at", "CREATE INDEX IF NOT EXISTS idx_people_errors_created_at ON people.people_errors (created_at DESC);"),
    ]
    for name, sql in indexes:
        cur.execute(sql)
        print(f"  ✓ {name}")
    
    # Add comments
    print("\n[3/4] Adding doctrine comments...")
    comments = [
        ("TABLE people.people_errors", "Canonical error table for People Intelligence. Append-only, no deletes. Status-driven lifecycle."),
        ("COLUMN people.people_errors.outreach_id", "Spine anchor - NEVER NULL. All errors tie back to outreach."),
        ("COLUMN people.people_errors.slot_id", "If error is slot-related, reference the slot."),
        ("COLUMN people.people_errors.person_id", "If error is person-bound, reference the person."),
        ("COLUMN people.people_errors.error_stage", "Pipeline stage: slot_creation | slot_fill | movement_detect | enrichment | promotion"),
        ("COLUMN people.people_errors.error_type", "Error category: validation | ambiguity | conflict | missing_data | stale_data | external_fail"),
        ("COLUMN people.people_errors.error_code", "Stable machine key for programmatic handling (e.g., PI-E001)"),
        ("COLUMN people.people_errors.error_message", "Human-readable description for operator review"),
        ("COLUMN people.people_errors.source_hints_used", "Blog/DOL/CL inputs at time of failure - audit trail"),
        ("COLUMN people.people_errors.raw_payload", "Full failure context - must capture everything needed for replay"),
        ("COLUMN people.people_errors.retry_strategy", "Recovery path: manual_fix | auto_retry | discard"),
        ("COLUMN people.people_errors.retry_after", "For auto_retry: earliest retry time"),
        ("COLUMN people.people_errors.status", "Lifecycle: open | fixed | replayed | abandoned"),
    ]
    for target, comment in comments:
        cur.execute(f"COMMENT ON {target} IS %s;", (comment,))
    print("  ✓ All comments added")
    
    # Verify creation
    print("\n[4/4] Verifying table structure...")
    cur.execute("""
        SELECT column_name, data_type, is_nullable
        FROM information_schema.columns
        WHERE table_schema = 'people' AND table_name = 'people_errors'
        ORDER BY ordinal_position;
    """)
    columns = cur.fetchall()
    print(f"  ✓ Table has {len(columns)} columns:")
    for col_name, data_type, nullable in columns:
        null_str = "NULL" if nullable == 'YES' else "NOT NULL"
        print(f"      • {col_name}: {data_type} {null_str}")
    
    conn.commit()
    cur.close()
    conn.close()
    
    print("\n" + "=" * 70)
    print("MIGRATION COMPLETE")
    print("=" * 70)
    
    return True

if __name__ == "__main__":
    run_migration()
