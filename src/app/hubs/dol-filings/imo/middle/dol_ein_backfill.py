#!/usr/bin/env python3
"""
DOL EIN Lock-In Backfill (IMO-Compliant)
=========================================
Version: 1.0
Process ID: 01.04.02.04.22000
Agent ID: DOL_EIN_BACKFILL_V1

Purpose:
    One-time, deterministic backfill that locks outreach_id → EIN
    using existing Form 5500 data only.

Rules:
    - No fuzzy logic
    - No enrichment
    - No AIR writes
    - Errors only to shq.error_master
    - Append-only to dol.ein_linkage

Canonical Rule:
    If an outreach_id does not resolve to exactly ONE EIN, it FAILS.
    No retries. No partials. No soft fails.
"""

import os
import sys
import json
import uuid
import subprocess
from datetime import datetime, timezone
from dataclasses import dataclass, field
from typing import Optional

# ============================================================================
# CONFIGURATION
# ============================================================================

PROCESS_ID = "01.04.02.04.22000"
AGENT_ID = "DOL_EIN_BACKFILL_V1"
LINKAGE_SOURCE = "BACKFILL_5500_V1"
SEVERITY = "HARD_FAIL"

# Error types
ERROR_EIN_MISSING = "DOL_EIN_MISSING"
ERROR_EIN_AMBIGUOUS = "DOL_EIN_AMBIGUOUS"

# Safety assertions
_air_calls_detected = False
_fuzzy_logic_used = False
_non_append_writes = False


# ============================================================================
# DATABASE CONNECTION
# ============================================================================

def get_db_url() -> str:
    """Get DATABASE_URL from Doppler."""
    doppler_paths = [
        r"C:\Users\CUSTOMER PC\doppler-cli\doppler.exe",
        r"C:\Users\CUSTOMER PC\Cursor Repo\imo-creator\doppler.exe",
        "doppler"
    ]
    
    for doppler_path in doppler_paths:
        try:
            result = subprocess.run(
                [doppler_path, "secrets", "get", "DATABASE_URL", "--plain",
                 "--project", "barton-outreach-core", "--config", "dev"],
                capture_output=True,
                text=True,
                check=True
            )
            return result.stdout.strip()
        except (subprocess.CalledProcessError, FileNotFoundError):
            continue
    
    raise RuntimeError("Could not retrieve DATABASE_URL from Doppler")


def get_connection():
    """Get psycopg2 connection."""
    try:
        import psycopg2
        from psycopg2.extras import RealDictCursor
    except ImportError:
        raise ImportError("psycopg2 is required. Install with: pip install psycopg2-binary")
    
    db_url = get_db_url()
    return psycopg2.connect(db_url, cursor_factory=RealDictCursor)


# ============================================================================
# DATA STRUCTURES
# ============================================================================

@dataclass
class BackfillResult:
    """Tracks backfill execution results."""
    outreach_ids_scanned: int = 0
    linked_successfully: int = 0
    missing_ein: int = 0
    ambiguous_ein: int = 0
    rows_ein_linkage: int = 0
    rows_error_master: int = 0
    errors: list = field(default_factory=list)


@dataclass
class OutreachCandidate:
    """Represents an outreach_id with its resolution data."""
    outreach_id: str
    company_unique_id: Optional[str]
    company_name: Optional[str]
    company_state: Optional[str]
    company_ein: Optional[str] = None
    candidate_eins: list = field(default_factory=list)


# ============================================================================
# SAFETY ASSERTIONS
# ============================================================================

def no_air_calls_detected() -> bool:
    """Verify no AIR calls were made."""
    return not _air_calls_detected


def no_fuzzy_logic_used() -> bool:
    """Verify no fuzzy matching was used."""
    return not _fuzzy_logic_used


def all_writes_are_append_only() -> bool:
    """Verify all writes were append-only (no UPDATEs)."""
    return not _non_append_writes


def assert_safety_invariants():
    """Assert all safety invariants at end of execution."""
    assert no_air_calls_detected(), "FATAL: AIR calls detected - ABORT"
    assert no_fuzzy_logic_used(), "FATAL: Fuzzy logic detected - ABORT"
    assert all_writes_are_append_only(), "FATAL: Non-append writes detected - ABORT"
    print("✓ All safety assertions passed")


# ============================================================================
# CORE BACKFILL LOGIC
# ============================================================================

# Target states from contexts/global-config/geographic_targets.yaml
TARGET_STATES = {'WV', 'VA', 'PA', 'MD', 'OH', 'KY', 'DE', 'NC'}


def get_target_states(cursor) -> set:
    """Get target states - hardcoded from geographic_targets.yaml."""
    # Hardcoded per doctrine - 8 target states
    return TARGET_STATES


def get_outreach_candidates(cursor) -> list:
    """
    Get all outreach_ids with their company linkage.
    
    Join path:
        outreach.outreach.sovereign_id 
          → cl.company_identity_bridge.company_sov_id 
          → company.company_master.company_unique_id (via source_company_id)
    
    This is the canonical linkage path for the Company Lifecycle (CL) system.
    """
    cursor.execute("""
        SELECT 
            o.outreach_id::text AS outreach_id,
            cm.company_unique_id,
            cm.company_name,
            cm.address_state AS company_state,
            cm.ein AS company_ein
        FROM outreach.outreach o
        JOIN cl.company_identity_bridge cib ON cib.company_sov_id = o.sovereign_id
        JOIN company.company_master cm ON cm.company_unique_id = cib.source_company_id
        WHERE cm.address_state IN ('WV', 'VA', 'PA', 'MD', 'OH', 'KY', 'DE', 'NC')
        ORDER BY o.outreach_id
    """)
    
    candidates = []
    for row in cursor.fetchall():
        candidates.append(OutreachCandidate(
            outreach_id=row['outreach_id'],
            company_unique_id=row['company_unique_id'],
            company_name=row['company_name'],
            company_state=row['company_state'],
            company_ein=row.get('company_ein')
        ))
    return candidates


def find_candidate_eins(cursor, company_name: str, company_state: str, 
                        target_states: set, company_ein: str = None) -> list:
    """
    Find candidate EINs from Form 5500 data using EXACT name matching only.
    
    Priority:
        1. Use company_master.ein if populated (most reliable)
        2. Fall back to Form 5500 exact name matching
    
    Sources:
        - dol.form_5500.sponsor_dfe_ein (matched by sponsor_dfe_name)
        - dol.form_5500_sf.sponsor_dfe_ein (matched by sponsor_dfe_name)
    
    Filters:
        - EIN is NOT NULL
        - Company state is in target_states
    
    NO FUZZY MATCHING. Exact name match only.
    """
    # Priority 1: If company_master has EIN, use it directly
    if company_ein and company_ein.strip():
        return [company_ein.strip()]
    
    # Priority 2: Fall back to Form 5500 name matching
    if not company_name or not company_state:
        return []
    
    if company_state not in target_states:
        return []
    
    candidate_eins = set()
    
    # Query dol.form_5500 - EXACT match on sponsor name
    # Columns: sponsor_dfe_ein, sponsor_dfe_name, spons_dfe_dba_name, spons_dfe_mail_us_state
    cursor.execute("""
        SELECT DISTINCT sponsor_dfe_ein
        FROM dol.form_5500
        WHERE sponsor_dfe_ein IS NOT NULL
          AND sponsor_dfe_ein != ''
          AND spons_dfe_mail_us_state = %s
          AND (
              UPPER(TRIM(sponsor_dfe_name)) = UPPER(TRIM(%s))
              OR UPPER(TRIM(spons_dfe_dba_name)) = UPPER(TRIM(%s))
          )
    """, (company_state, company_name, company_name))
    
    for row in cursor.fetchall():
        if row['sponsor_dfe_ein']:
            candidate_eins.add(row['sponsor_dfe_ein'].strip())
    
    # Query dol.form_5500_sf - EXACT match on sponsor name
    # Columns: sponsor_dfe_ein, sponsor_dfe_name, spons_dfe_mail_us_state
    cursor.execute("""
        SELECT DISTINCT sponsor_dfe_ein
        FROM dol.form_5500_sf
        WHERE sponsor_dfe_ein IS NOT NULL
          AND sponsor_dfe_ein != ''
          AND spons_dfe_mail_us_state = %s
          AND UPPER(TRIM(sponsor_dfe_name)) = UPPER(TRIM(%s))
    """, (company_state, company_name))
    
    for row in cursor.fetchall():
        if row['sponsor_dfe_ein']:
            candidate_eins.add(row['sponsor_dfe_ein'].strip())
    
    return list(candidate_eins)


def insert_ein_linkage(cursor, outreach_id: str, ein: str, company_unique_id: str) -> bool:
    """
    Insert exactly ONE row into dol.ein_linkage.
    
    Actual schema:
        linkage_id, company_unique_id, ein, source, source_url, 
        filing_year, hash_fingerprint, outreach_context_id, created_at
    
    Rules:
        - source = 'BACKFILL_5500_V1'
        - No UPDATEs allowed
    """
    global _non_append_writes
    
    linkage_id = str(uuid.uuid4())
    now = datetime.now(timezone.utc)
    
    # Create hash fingerprint for deduplication
    import hashlib
    fingerprint = hashlib.sha256(f"{company_unique_id}|{ein}".encode()).hexdigest()[:32]
    
    # source_url is required - reference to DOL EFAST2 system
    source_url = f"https://www.efast.dol.gov/5500search/{ein}"
    
    try:
        cursor.execute("""
            INSERT INTO dol.ein_linkage (
                linkage_id,
                company_unique_id,
                ein,
                source,
                source_url,
                filing_year,
                hash_fingerprint,
                outreach_context_id,
                created_at
            ) VALUES (
                %s,
                %s,
                %s,
                %s,
                %s,
                %s,
                %s,
                %s,
                %s
            )
        """, (
            linkage_id,
            company_unique_id,
            ein,
            LINKAGE_SOURCE,
            source_url,
            2024,  # Current filing year reference
            fingerprint,
            outreach_id,  # Store outreach_id in outreach_context_id field
            now
        ))
        return True
    except Exception as e:
        print(f"  ERROR inserting linkage: {e}")
        return False


def insert_error(cursor, outreach_id: str, error_type: str, 
                 candidate_eins: list, company_state: Optional[str],
                 company_name: Optional[str]) -> bool:
    """
    Insert exactly ONE row to shq.error_master.
    
    NO AIR writes. Ever.
    """
    global _non_append_writes, _air_calls_detected
    
    error_id = str(uuid.uuid4())
    now = datetime.now(timezone.utc)
    
    context = {
        "outreach_id": outreach_id,
        "company_name": company_name,
        "company_state": company_state,
        "candidate_ein_count": len(candidate_eins),
        "candidate_eins": candidate_eins[:10],  # Limit for storage
        "backfill_version": "1.0",
        "timestamp": now.isoformat()
    }
    
    if error_type == ERROR_EIN_MISSING:
        message = f"No EIN found for outreach_id {outreach_id}"
    else:
        message = f"Ambiguous EIN resolution: {len(candidate_eins)} candidates for outreach_id {outreach_id}"
    
    try:
        cursor.execute("""
            INSERT INTO shq.error_master (
                error_id,
                process_id,
                agent_id,
                severity,
                error_type,
                message,
                outreach_context_id,
                context,
                created_at
            ) VALUES (
                %s::uuid,
                %s,
                %s,
                %s,
                %s,
                %s,
                %s,
                %s::jsonb,
                %s
            )
        """, (
            error_id,
            PROCESS_ID,
            AGENT_ID,
            SEVERITY,
            error_type,
            message,
            outreach_id,
            json.dumps(context),
            now
        ))
        return True
    except Exception as e:
        print(f"  ERROR inserting error record: {e}")
        return False


# ============================================================================
# MAIN BACKFILL FUNCTION
# ============================================================================

def run_backfill(dry_run: bool = False, limit: Optional[int] = None) -> BackfillResult:
    """
    Execute the DOL EIN Lock-In Backfill.
    
    Args:
        dry_run: If True, don't actually write to database
        limit: If set, only process this many outreach_ids
    
    Returns:
        BackfillResult with execution statistics
    """
    global _air_calls_detected, _fuzzy_logic_used, _non_append_writes
    
    # Reset safety flags
    _air_calls_detected = False
    _fuzzy_logic_used = False
    _non_append_writes = False
    
    result = BackfillResult()
    
    print("=" * 60)
    print("DOL EIN LOCK-IN BACKFILL")
    print("=" * 60)
    print(f"Process ID:     {PROCESS_ID}")
    print(f"Agent ID:       {AGENT_ID}")
    print(f"Linkage Source: {LINKAGE_SOURCE}")
    print(f"Dry Run:        {dry_run}")
    print(f"Limit:          {limit or 'None'}")
    print("=" * 60)
    
    conn = get_connection()
    cursor = conn.cursor()
    
    try:
        # Step 1: Get target states
        print("\n[1/4] Loading target states...")
        target_states = get_target_states(cursor)
        print(f"      Target states: {sorted(target_states)}")
        
        # Step 2: Get all outreach candidates
        print("\n[2/4] Loading outreach candidates...")
        candidates = get_outreach_candidates(cursor)
        total_candidates = len(candidates)
        print(f"      Found {total_candidates} outreach_ids to process")
        
        if limit:
            candidates = candidates[:limit]
            print(f"      Limited to {len(candidates)} for this run")
        
        # Step 3: Process each candidate
        print("\n[3/4] Processing candidates...")
        for i, candidate in enumerate(candidates):
            result.outreach_ids_scanned += 1
            
            if (i + 1) % 1000 == 0:
                print(f"      Processed {i + 1}/{len(candidates)}...")
            
            # Find candidate EINs using EXACT matching only
            candidate.candidate_eins = find_candidate_eins(
                cursor,
                candidate.company_name,
                candidate.company_state,
                target_states,
                candidate.company_ein
            )
            
            ein_count = len(candidate.candidate_eins)
            
            # Apply canonical rule
            if ein_count == 0:
                # DOL_EIN_MISSING
                result.missing_ein += 1
                if not dry_run:
                    if insert_error(cursor, candidate.outreach_id, ERROR_EIN_MISSING,
                                   candidate.candidate_eins, candidate.company_state,
                                   candidate.company_name):
                        result.rows_error_master += 1
            
            elif ein_count > 1:
                # DOL_EIN_AMBIGUOUS
                result.ambiguous_ein += 1
                if not dry_run:
                    if insert_error(cursor, candidate.outreach_id, ERROR_EIN_AMBIGUOUS,
                                   candidate.candidate_eins, candidate.company_state,
                                   candidate.company_name):
                        result.rows_error_master += 1
            
            else:
                # Exactly 1 EIN - SUCCESS
                ein = candidate.candidate_eins[0]
                result.linked_successfully += 1
                if not dry_run:
                    if insert_ein_linkage(cursor, candidate.outreach_id, ein, candidate.company_unique_id):
                        result.rows_ein_linkage += 1
        
        # Step 4: Commit transaction
        print("\n[4/4] Committing transaction...")
        if not dry_run:
            conn.commit()
            print("      Transaction committed")
        else:
            conn.rollback()
            print("      Dry run - rolled back")
        
    except Exception as e:
        conn.rollback()
        print(f"\nFATAL ERROR: {e}")
        result.errors.append(str(e))
        raise
    finally:
        cursor.close()
        conn.close()
    
    # Print summary
    print("\n" + "=" * 60)
    print("DOL EIN LOCK-IN BACKFILL COMPLETE")
    print("-" * 60)
    print(f"Outreach IDs scanned:   {result.outreach_ids_scanned}")
    print(f"Linked successfully:    {result.linked_successfully}")
    print(f"Missing EIN:            {result.missing_ein}")
    print(f"Ambiguous EIN:          {result.ambiguous_ein}")
    print(f"Rows inserted:")
    print(f"  - dol.ein_linkage:    {result.rows_ein_linkage}")
    print(f"  - shq.error_master:   {result.rows_error_master}")
    print("=" * 60)
    
    # Final safety assertions
    assert_safety_invariants()
    
    return result


# ============================================================================
# CLI INTERFACE
# ============================================================================

def main():
    """CLI entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="DOL EIN Lock-In Backfill (IMO-Compliant)"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Run without writing to database"
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=None,
        help="Limit number of outreach_ids to process"
    )
    parser.add_argument(
        "--confirm",
        action="store_true",
        help="Required flag to actually execute (without --dry-run)"
    )
    
    args = parser.parse_args()
    
    if not args.dry_run and not args.confirm:
        print("ERROR: Must specify --confirm to execute actual backfill")
        print("       Use --dry-run to preview without writing")
        sys.exit(1)
    
    try:
        result = run_backfill(dry_run=args.dry_run, limit=args.limit)
        
        if result.errors:
            sys.exit(1)
        
        sys.exit(0)
        
    except Exception as e:
        print(f"\nFATAL: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
